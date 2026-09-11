"""The Envertech Local integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_IP_ADDRESS, CONF_PORT, CONF_UNIQUE_ID, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN
from .sensor import InverterSocketCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Envertech Local component."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Envertech Local from a config entry."""
    _LOGGER.debug("Setting up envertech_local entry %s", entry.entry_id)

    ip = entry.data[CONF_IP_ADDRESS]
    sn = entry.data[CONF_UNIQUE_ID]
    port = entry.data[CONF_PORT]

    coordinator = InverterSocketCoordinator(hass, ip, port, sn)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        coordinator: InverterSocketCoordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await coordinator.async_shutdown()
    return unload_ok


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
        "number_of_panels": coordinator.number_of_panels,
        "latest_values": coordinator.data,
    }
