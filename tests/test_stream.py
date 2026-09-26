"""Unit tests for the reconnecting inverter stream (no Home Assistant needed).

Uses real local TCP servers to reproduce the failure modes seen after a
Home Assistant restart (peer closes socket, silent peer, refused connect).
"""

from __future__ import annotations

import asyncio
import contextlib

import pytest

from tests._loader import load

stream = load("stream")

SN = "12345678"
REQUEST = b"REQ"
BREAK = b"BRK"


def build_request(sn: str) -> bytes:
    return REQUEST


def build_break(sn: str) -> bytes:
    return BREAK


def parse(raw: list[int]):
    """Fake parser: b"D<n>" -> data dict, anything else -> no data."""
    if raw and raw[0] == ord("D"):
        return {"0_power": float(raw[1] - ord("0")), "total_power": 1.0}, 1, 4177
    return {}, None, 4102


def _stream(port: int, **kwargs):
    return stream.stream_inverter(
        "127.0.0.1",
        port,
        SN,
        build_request=build_request,
        build_break=build_break,
        parse=parse,
        **kwargs,
    )


async def _server(handler):
    async def wrapped(reader, writer):
        try:
            result = handler(reader, writer)
            if asyncio.iscoroutine(result):
                await result
        finally:
            # Python 3.12's Server.wait_closed() waits for server-side
            # connections, so always close them when the handler returns.
            writer.close()

    server = await asyncio.start_server(wrapped, "127.0.0.1", 0)
    return server, server.sockets[0].getsockname()[1]


def test_next_backoff_doubles_and_caps() -> None:
    delays = [5.0]
    for _ in range(6):
        delays.append(stream.next_backoff(delays[-1], 60))
    assert delays == [5.0, 10.0, 20.0, 40.0, 60.0, 60.0, 60.0]


def test_yields_only_real_data_and_polls() -> None:
    requests: list[bytes] = []

    async def handler(reader, writer):
        for payload in (b"X", b"D1", b"D2"):
            requests.append(await reader.readexactly(len(REQUEST)))
            writer.write(payload)
            await writer.drain()
        while await reader.read(100):  # until the client disconnects
            pass

    async def main():
        server, port = await _server(handler)
        async with server:
            got = []
            async with contextlib.aclosing(_stream(port, interval=0.05)) as gen:
                async for data in gen:
                    got.append(data["0_power"])
                    if len(got) == 2:
                        break
            return got

    assert asyncio.run(asyncio.wait_for(main(), 5)) == [1.0, 2.0]
    assert requests == [REQUEST] * 3


def test_peer_close_raises_instead_of_freezing_event_loop() -> None:
    ticks = 0

    async def handler(reader, writer):
        await reader.read(10)
        writer.close()

    async def ticker():
        nonlocal ticks
        while True:
            ticks += 1
            await asyncio.sleep(0.01)

    async def main():
        server, port = await _server(handler)
        async with server:
            tick_task = asyncio.create_task(ticker())
            with pytest.raises(stream.InverterConnectionLost):
                async for _ in _stream(port, interval=0.05):
                    pass
            await asyncio.sleep(0.05)
            tick_task.cancel()

    asyncio.run(asyncio.wait_for(main(), 5))
    assert ticks > 1


def test_silent_peer_raises_idle_timeout() -> None:
    async def handler(reader, writer):
        while await reader.read(100):  # read requests, never answer
            pass

    async def main():
        server, port = await _server(handler)
        async with server:
            with pytest.raises(stream.InverterIdleTimeout):
                async for _ in _stream(port, interval=0.05, idle_timeout=0.3):
                    pass

    asyncio.run(asyncio.wait_for(main(), 5))


def test_refused_connection_raises_oserror() -> None:
    async def main():
        server, port = await _server(lambda r, w: None)
        server.close()
        await server.wait_closed()
        with pytest.raises(OSError):
            async for _ in _stream(port):
                pass

    asyncio.run(asyncio.wait_for(main(), 5))


def test_connect_timeout() -> None:
    async def never_connects(ip, port):
        await asyncio.sleep(10)

    async def main():
        with pytest.raises(TimeoutError):
            async for _ in _stream(
                1, connect_timeout=0.1, open_connection=never_connects
            ):
                pass

    asyncio.run(asyncio.wait_for(main(), 5))


def test_break_command_sent_on_close() -> None:
    received = bytearray()
    closed = asyncio.Event

    async def main():
        done = closed()

        async def handler(reader, writer):
            await reader.readexactly(len(REQUEST))
            writer.write(b"D5")
            await writer.drain()
            while chunk := await reader.read(100):
                received.extend(chunk)
            done.set()

        server, port = await _server(handler)
        async with server:
            async with contextlib.aclosing(_stream(port, interval=10)) as gen:
                async for _ in gen:
                    break
            await asyncio.wait_for(done.wait(), 2)

    asyncio.run(asyncio.wait_for(main(), 5))
    assert received.endswith(BREAK)


def test_supervisor_reconnects_with_backoff_until_data_arrives() -> None:
    attempts = 0
    sleeps: list[float] = []
    events: list[object] = []

    async def open_stream():
        nonlocal attempts
        attempts += 1
        if attempts <= 3 or attempts == 5:  # inverter not reachable
            raise OSError("Host unreachable")
        yield {"0_power": 1.0}
        yield {"0_power": 2.0}
        raise stream.InverterConnectionLost("closed")

    async def fake_sleep(delay: float) -> None:
        sleeps.append(delay)
        if len(sleeps) >= 5:
            raise asyncio.CancelledError

    async def main():
        with pytest.raises(asyncio.CancelledError):
            await stream.run_with_reconnect(
                open_stream,
                on_data=lambda d: events.append(d["0_power"]),
                on_disconnect=lambda e: events.append(type(e).__name__),
                initial_backoff=5,
                max_backoff=30,
                sleep=fake_sleep,
            )

    asyncio.run(main())
    # 3 failed connects with growing backoff, then data resets the backoff,
    # a further failed connect doubles it again.
    assert sleeps == [5, 10, 20, 5, 10]
    assert events[:6] == [
        "OSError",
        "OSError",
        "OSError",
        1.0,
        2.0,
        "InverterConnectionLost",
    ]


def test_supervisor_propagates_cancellation() -> None:
    async def open_stream():
        await asyncio.sleep(10)
        yield {}

    async def main():
        task = asyncio.create_task(
            stream.run_with_reconnect(
                open_stream, on_data=lambda d: None, on_disconnect=lambda e: None
            )
        )
        await asyncio.sleep(0.05)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    asyncio.run(asyncio.wait_for(main(), 5))
