"""Unit tests for the coordinator cache/reconnect bookkeeping.

Home Assistant is stubbed so the coordinator module can run standalone,
matching the approach of the other tests in this package.
"""

from __future__ import annotations

import importlib.util
import sys
import types
from datetime import datetime, timezone
from pathlib import Path

from tests._loader import load

_PKG = Path(__file__).resolve().parents[1] / "custom_components" / "envertech_local"


def _install_ha_stubs() -> None:
    if "homeassistant.config_entries" in sys.modules:
        return

    def mod(name: str, **attrs) -> types.ModuleType:
        m = types.ModuleType(name)
        for key, val in attrs.items():
            setattr(m, key, val)
        sys.modules[name] = m
        return m

    class _Anything:
        def __init__(self, *args, **kwargs) -> None:
            pass

    class DataUpdateCoordinator:  # minimal stand-in for the base class
        def __class_getitem__(cls, item):
            return cls

        def __init__(self, hass, logger, *, name, update_interval) -> None:
            self.hass = hass

    def callback(fn):
        return fn

    def _utcnow() -> datetime:
        return datetime.now(timezone.utc)

    mod("homeassistant")
    mod("homeassistant.config_entries", ConfigEntry=_Anything)
    mod("homeassistant.core", HomeAssistant=_Anything, callback=callback)
    mod(
        "homeassistant.helpers.update_coordinator",
        DataUpdateCoordinator=DataUpdateCoordinator,
    )
    dt = mod("homeassistant.util.dt", utcnow=_utcnow, now=_utcnow)
    mod("homeassistant.util", dt=dt)


def _make_coordinator() -> object:
    _install_ha_stubs()

    # Make relative imports (``from .panels import ...``) resolvable.
    if "envertech_local" not in sys.modules:
        pkg = types.ModuleType("envertech_local")
        pkg.__path__ = [str(_PKG)]  # mark as package
        sys.modules["envertech_local"] = pkg
    panels = load("panels")
    sys.modules.setdefault("envertech_local.panels", panels)

    name = "envertech_local.coordinator"
    cached = sys.modules.get(name)
    if cached is None or not hasattr(cached, "InverterSocketCoordinator"):
        # (Re)load the module so it is fully initialised.
        sys.modules.pop(name, None)
        spec = importlib.util.spec_from_file_location(name, _PKG / "coordinator.py")
        assert spec and spec.loader
        coordinator_mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = coordinator_mod
        spec.loader.exec_module(coordinator_mod)
    else:
        coordinator_mod = cached

    cls = coordinator_mod.InverterSocketCoordinator
    coord = object.__new__(cls)
    # Attributes normally set in __init__:
    coord.hass = object()
    coord.ip = "127.0.0.1"
    coord.port = 14889
    coord.sn = "12345678"
    coord.data = {}
    coord._stale_counters = {}
    coord.number_of_panels = 0
    coord.connected = False
    coord.last_error = None
    coord.last_loss = None
    coord.reconnect_count = 0
    coord.poll_interval = 5
    coord._entry = None
    coord._stream_task = None

    coord.async_set_updated_data = lambda data: data
    coord.async_update_listeners = lambda: None
    return coord


def test_stale_panel_values_are_dropped_after_missing_packets() -> None:
    coord = _make_coordinator()

    # Packet 1: two panels report.
    coord._handle_data({"0_power": 10.0, "1_power": 20.0, "total_power": 30.0})
    assert coord.data.get("0_power") == 10.0
    assert coord.data.get("1_power") == 20.0

    # Panel 0 stops reporting; counter must reach the limit first.
    coord._handle_data({"1_power": 20.0, "total_power": 20.0})
    assert "0_power" in coord.data
    coord._handle_data({"1_power": 20.0, "total_power": 20.0})
    assert "0_power" in coord.data
    coord._handle_data({"1_power": 20.0, "total_power": 20.0})
    assert "0_power" not in coord.data
    assert coord.number_of_panels == 1

    # Panel comes back and is tracked again.
    coord._handle_data({"0_power": 15.0, "1_power": 20.0, "total_power": 35.0})
    assert coord.data.get("0_power") == 15.0
    assert coord.number_of_panels == 2


def test_disconnect_updates_reconnect_bookkeeping() -> None:
    coord = _make_coordinator()
    coord.connected = True

    assert coord.last_loss is None
    assert coord.reconnect_count == 0

    coord._handle_disconnect(TimeoutError("nope"))
    assert coord.connected is False
    assert coord.last_loss is not None
    assert coord.reconnect_count == 1
    assert "TimeoutError" in coord.last_error

    coord._handle_data({"total_power": 1.0})
    coord._handle_disconnect(None)
    assert coord.reconnect_count == 2
