"""Options flow for Envertech Local (poll interval)."""

from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

from .const import CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL, POLL_INTERVAL_CHOICES


class InverterMonitorOptionsFlow(config_entries.OptionsFlow):
    """Options flow for the Envertech Local integration."""

    async def async_step_init(
        self, user_input: dict | None = None
    ) -> FlowResult:
        """Handle the options flow."""
        if user_input is not None:
            # Validate the interval even though the schema already restricts it,
            # so a stored/legacy value can never produce an out-of-range poll.
            interval = int(user_input[CONF_POLL_INTERVAL])
            if interval not in POLL_INTERVAL_CHOICES:
                interval = DEFAULT_POLL_INTERVAL
            user_input[CONF_POLL_INTERVAL] = interval
            return self.async_create_entry(title="", data=user_input)

        current = self.config_entry.options.get(
            CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL
        )
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_POLL_INTERVAL, default=current): vol.In(
                        POLL_INTERVAL_CHOICES
                    ),
                }
            ),
        )
