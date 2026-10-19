"""Coordinator streaming Envertech inverter data over local TCP."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .panels import panel_indices
from .stream import run_with_reconnect, stream_inverter
from .const import CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL

_LOGGER = logging.getLogger(__name__)

# A panel value that is missing from this many consecutive packets is dropped
# from the cache so removed modules do not show stale values forever.
STALE_PACKET_LIMIT = 3


class InverterSocketCoordinator(DataUpdateCoordinator[dict]):
    """Keep a TCP stream to the inverter alive and push updates to entities."""

    def __init__(self, hass: HomeAssistant, ip: str, port: int, sn: str) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"envertech_local_{sn}",
            update_interval=timedelta(seconds=30),
        )
        self.ip = ip
        self.port = port
        self.sn = sn
        self.data: dict = {}
        self.number_of_panels = 0
        self.connected = False
        self.last_error: str | None = None
        self.last_loss: datetime | None = None
        self.reconnect_count = 0
        self.poll_interval = DEFAULT_POLL_INTERVAL
        self._entry: ConfigEntry | None = None
        self._stream_task: asyncio.Task | None = None
        self._stale_counters: dict[str, int] = {}

    async def _async_update_data(self) -> dict:
        """Return latest cached stream data for coordinator consumers."""
        return self.data

    @callback
    def async_start(self, entry: ConfigEntry) -> None:
        """Start the (self-reconnecting) stream as an entry background task.

        Using the entry's background task ensures Home Assistant cancels it on
        unload and on shutdown.
        """
        self._entry = entry
        self.poll_interval = int(
            entry.options.get(CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL)
        )
        if self._stream_task and not self._stream_task.done():
            return
        self._stream_task = entry.async_create_background_task(
            self.hass,
            self._async_run(),
            f"envertech_local_stream_{self.sn}",
        )

    @callback
    def async_set_poll_interval(self, interval: int) -> None:
        """Apply a new poll interval and restart the stream with it.

        Called from the options flow. Cancels the running stream task and
        starts a fresh one so the new interval takes effect immediately.
        """
        self.poll_interval = int(interval)
        entry = self._entry
        task, self._stream_task = self._stream_task, None
        if task and not task.done():
            task.cancel()
        if entry is not None:
            self._stream_task = entry.async_create_background_task(
                self.hass,
                self._async_run(),
                f"envertech_local_stream_{self.sn}",
            )

    async def async_shutdown(self) -> None:
        """Stop the background stream."""
        task, self._stream_task = self._stream_task, None
        if task and not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        self.connected = False
        parent_shutdown = getattr(super(), "async_shutdown", None)
        if parent_shutdown is not None:
            await parent_shutdown()

    def _open_stream(self):
        # Imported lazily: the library pulls in netifaces for discovery.
        from envertech_local import (
            InverterClient,
            build_inverter_break_command,
            build_inverter_request,
        )

        parser = InverterClient(self.ip, self.port, self.sn)
        return stream_inverter(
            self.ip,
            self.port,
            self.sn,
            build_request=build_inverter_request,
            build_break=build_inverter_break_command,
            parse=parser.parse_data,
            interval=self.poll_interval,
        )

    async def _async_run(self) -> None:
        await run_with_reconnect(
            self._open_stream,
            on_data=self._handle_data,
            on_disconnect=self._handle_disconnect,
            name=f"Envertech inverter {self.sn} ({self.ip}:{self.port})",
        )

    @callback
    def _handle_data(self, update: dict) -> None:
        for key, val in update.items():
            self.data[key] = round(val, 2) if isinstance(val, float) else val
            self._stale_counters[key] = 0
        # Drop cached values that stopped arriving (removed modules).
        for key in [k for k, n in self._stale_counters.items() if k not in update]:
            self._stale_counters[key] += 1
            if self._stale_counters[key] >= STALE_PACKET_LIMIT:
                del self._stale_counters[key]
                self.data.pop(key, None)
        self.number_of_panels = len(panel_indices(self.data))
        self.connected = True
        self.last_error = None
        self.async_set_updated_data(self.data)

    @callback
    def _handle_disconnect(self, error: BaseException | None) -> None:
        self.last_error = f"{type(error).__name__}: {error}" if error else None
        if self.connected:
            self.connected = False
            self.last_loss = dt_util.utcnow()
            self.reconnect_count += 1
            # Mark entities unavailable instead of showing stale values.
            self.async_update_listeners()
