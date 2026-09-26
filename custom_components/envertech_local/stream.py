"""Robust TCP stream to an Envertech inverter/gateway (Home Assistant free).

The ``stream_inverter_data`` helper of ``envertech-local==0.0.2`` has several
problems that break the integration after a Home Assistant restart:

* when the peer closes the socket, its receiver loops on ``reader.read()``
  returning ``b""`` without ever yielding to the event loop (busy loop),
* a silent / half-open connection never ends; it just yields ``{}`` every
  10 seconds, so no reconnect ever happens,
* ``open_connection`` has no timeout.

This module re-implements the stream using the library's command builders and
parser (injected as callables so it can be unit tested without the library or
Home Assistant) and adds a supervisor with exponential reconnect backoff.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
import socket
from collections.abc import AsyncIterator, Awaitable, Callable
from typing import Any

_LOGGER = logging.getLogger(__name__)

DEFAULT_INTERVAL = 5.0
DEFAULT_CONNECT_TIMEOUT = 10.0
DEFAULT_IDLE_TIMEOUT = 60.0
DEFAULT_WRITE_TIMEOUT = 10.0
DEFAULT_CLOSE_TIMEOUT = 2.0
INITIAL_BACKOFF = 5.0
MAX_BACKOFF = 120.0
READ_CHUNK = 4096


class InverterConnectionLost(ConnectionError):
    """The inverter closed the connection."""


class InverterIdleTimeout(TimeoutError):
    """No bytes were received from the inverter for too long."""


def next_backoff(current: float, maximum: float = MAX_BACKOFF) -> float:
    """Return the next reconnect delay (doubling, capped at ``maximum``)."""
    return min(maximum, max(current, 1.0) * 2)


def _enable_keepalive(writer: asyncio.StreamWriter) -> None:
    """Enable TCP keepalive so dead peers are eventually detected by the OS."""
    sock = writer.get_extra_info("socket")
    if sock is None:
        return
    with contextlib.suppress(OSError, AttributeError):
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        if hasattr(socket, "TCP_KEEPIDLE"):
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 30)
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 10)
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 3)


async def stream_inverter(
    ip: str,
    port: int,
    sn: str,
    *,
    build_request: Callable[[str], bytes],
    build_break: Callable[[str], bytes] | None,
    parse: Callable[[list[int]], Any],
    interval: float = DEFAULT_INTERVAL,
    connect_timeout: float = DEFAULT_CONNECT_TIMEOUT,
    idle_timeout: float = DEFAULT_IDLE_TIMEOUT,
    write_timeout: float = DEFAULT_WRITE_TIMEOUT,
    open_connection: Callable[..., Awaitable[Any]] = asyncio.open_connection,
) -> AsyncIterator[dict]:
    """Connect, poll every ``interval`` seconds and yield parsed data dicts.

    Only non-empty data dicts are yielded. The generator never ends normally:
    it raises ``OSError``/``TimeoutError`` when connecting fails,
    ``InverterConnectionLost`` when the peer closes the socket and
    ``InverterIdleTimeout`` when nothing is received for ``idle_timeout``.
    """
    reader, writer = await asyncio.wait_for(
        open_connection(ip, port), timeout=connect_timeout
    )
    _enable_keepalive(writer)
    _LOGGER.debug("Connected to inverter %s at %s:%s", sn, ip, port)
    loop = asyncio.get_running_loop()
    request = build_request(sn)
    try:
        last_rx = loop.time()
        next_send = loop.time()
        while True:
            now = loop.time()
            if now >= next_send:
                writer.write(request)
                await asyncio.wait_for(writer.drain(), timeout=write_timeout)
                next_send = now + interval
            if now - last_rx >= idle_timeout:
                raise InverterIdleTimeout(
                    f"No response from inverter {sn} for {idle_timeout:.0f}s"
                )
            wait = max(0.01, min(next_send, last_rx + idle_timeout) - loop.time())
            try:
                chunk = await asyncio.wait_for(reader.read(READ_CHUNK), timeout=wait)
            except TimeoutError:
                continue
            if not chunk:
                raise InverterConnectionLost(f"Inverter {sn} closed the connection")
            last_rx = loop.time()
            result = parse(list(chunk))
            data = result[0] if isinstance(result, tuple) else result
            if data:
                yield data
    finally:
        if build_break is not None:
            with contextlib.suppress(Exception):
                writer.write(build_break(sn))
                await asyncio.wait_for(writer.drain(), timeout=DEFAULT_CLOSE_TIMEOUT)
        with contextlib.suppress(Exception):
            writer.close()
            await asyncio.wait_for(writer.wait_closed(), timeout=DEFAULT_CLOSE_TIMEOUT)


async def run_with_reconnect(
    open_stream: Callable[[], AsyncIterator[dict]],
    *,
    on_data: Callable[[dict], None],
    on_disconnect: Callable[[BaseException | None], None],
    name: str = "inverter",
    initial_backoff: float = INITIAL_BACKOFF,
    max_backoff: float = MAX_BACKOFF,
    sleep: Callable[[float], Awaitable[Any]] = asyncio.sleep,
) -> None:
    """Run ``open_stream`` forever, reconnecting with exponential backoff.

    Only returns when cancelled. The backoff is reset after a data packet.
    """
    backoff = initial_backoff
    failures = 0
    while True:
        error: BaseException | None = None
        try:
            async with contextlib.aclosing(open_stream()) as stream:
                async for data in stream:
                    if failures:
                        _LOGGER.info(
                            "Connection to %s re-established after %s failed attempt(s)",
                            name,
                            failures,
                        )
                    failures = 0
                    backoff = initial_backoff
                    on_data(data)
        except asyncio.CancelledError:
            raise
        except Exception as err:  # noqa: BLE001 - keep the stream alive
            error = err
        failures += 1
        on_disconnect(error)
        log = _LOGGER.warning if failures == 1 else _LOGGER.debug
        log(
            "Connection to %s lost or not possible (%s); retrying in %.0fs",
            name,
            f"{type(error).__name__}: {error}" if error else "stream ended",
            backoff,
        )
        await sleep(backoff)
        backoff = next_backoff(backoff, max_backoff)
