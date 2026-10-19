"""Diagnostics support for Envertech Local."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.util import dt as dt_util
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import InverterSocketCoordinator


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict:
    """Return diagnostics for a config entry."""
    coordinator: InverterSocketCoordinator = hass.data[DOMAIN][entry.entry_id]
    return {
        "serial_number": coordinator.sn,
        "ip": coordinator.ip,
        "port": coordinator.port,
        "connected": coordinator.connected,
        "last_error": coordinator.last_error,
        "last_loss": dt_util.as_local(coordinator.last_loss).isoformat()
        if coordinator.last_loss
        else None,
        "reconnect_count": coordinator.reconnect_count,
        "number_of_panels": coordinator.number_of_panels,
        "latest_values": coordinator.data,
    }
