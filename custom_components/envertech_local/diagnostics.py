"""Diagnostics support for Envertech API."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
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
        "number_of_panels": coordinator.number_of_panels,
        "latest_values": coordinator.data,
    }
