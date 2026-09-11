"""Config flow for Envertech Local."""

from __future__ import annotations

import logging

import voluptuous as vol
from envertech_local import discover_devices_async
from homeassistant import config_entries
from homeassistant.const import CONF_IP_ADDRESS, CONF_PORT, CONF_UNIQUE_ID
from homeassistant.data_entry_flow import FlowResult

from .const import DEFAULT_PORT, DEVICE_NAME, DOMAIN

_LOGGER = logging.getLogger(__name__)


class InverterMonitorConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Envertech Local."""

    VERSION = 1

    def __init__(self) -> None:
        self.discovered_devices: list[dict] = []

    async def async_step_user(self, user_input: dict | None = None) -> FlowResult:
        """Handle the initial step with discovery."""
        errors: dict[str, str] = {}

        try:
            self.discovered_devices = await discover_devices_async(timeout=5)
        except Exception:
            _LOGGER.exception("Device discovery failed")
            self.discovered_devices = []

        existing_entries = self.hass.config_entries.async_entries(DOMAIN)
        existing_ids = {
            entry.data[CONF_UNIQUE_ID]
            for entry in existing_entries
            if CONF_UNIQUE_ID in entry.data
        }

        filtered_devices = [
            device
            for device in self.discovered_devices
            if device.get("serial_number") not in existing_ids
        ]
        ip_to_sn = {d["ip"]: d["serial_number"] for d in filtered_devices}

        if user_input is not None:
            selected_ip = user_input[CONF_IP_ADDRESS]

            if selected_ip == "manual":
                return await self.async_step_manual()

            sn = ip_to_sn.get(selected_ip)
            if not sn:
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(sn)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"{DEVICE_NAME} {sn}",
                    data={
                        CONF_IP_ADDRESS: selected_ip,
                        CONF_UNIQUE_ID: sn,
                        CONF_PORT: user_input[CONF_PORT],
                    },
                )

        device_choices = {
            d["ip"]: f"{d['ip']} — {d['serial_number']}" for d in filtered_devices
        }
        device_choices["manual"] = "Manual entry"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_IP_ADDRESS): vol.In(device_choices),
                    vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
                }
            ),
            errors=errors,
            description_placeholders={
                "discovered_devices": ", ".join(
                    f"{d['ip']} — {d['serial_number']}"
                    for d in self.discovered_devices
                )
                or "none"
            },
        )

    async def async_step_manual(self, user_input: dict | None = None) -> FlowResult:
        """Handle manual entry of device details."""
        errors: dict[str, str] = {}

        if user_input is not None:
            sn = user_input[CONF_UNIQUE_ID].strip()
            await self.async_set_unique_id(sn)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=f"{DEVICE_NAME} {sn}",
                data={
                    CONF_IP_ADDRESS: user_input[CONF_IP_ADDRESS].strip(),
                    CONF_UNIQUE_ID: sn,
                    CONF_PORT: user_input[CONF_PORT],
                },
            )

        return self.async_show_form(
            step_id="manual",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_IP_ADDRESS): str,
                    vol.Required(CONF_UNIQUE_ID): str,
                    vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
                }
            ),
            errors=errors,
        )
