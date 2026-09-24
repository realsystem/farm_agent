"""Config flow for Farm Agent integration."""
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import logging

_LOGGER = logging.getLogger(__name__)

DOMAIN = "farm_agent"


class FarmAgentConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Farm Agent."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle a flow initiated by the user."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            return self.async_create_entry(
                title="Farm Agent",
                data={"host": "localhost", "port": 8080}
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({}),
            description_placeholders={},
        )

    async def async_step_import(self, import_data):
        """Import a config entry."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        return self.async_create_entry(
            title="Farm Agent",
            data=import_data
        )
