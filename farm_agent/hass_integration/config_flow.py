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
            # Detect Farm Agent endpoint
            endpoint = await self._detect_endpoint()
            if not endpoint:
                return self.async_abort(reason="farm_agent_not_found")

            return self.async_create_entry(
                title="Farm Agent",
                data={"endpoint": endpoint}
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({}),
            description_placeholders={},
        )

    async def _detect_endpoint(self) -> str | None:
        """Detect Farm Agent add-on endpoint."""
        session = async_get_clientsession(self.hass)

        # Try the verified hostname (underscore converts to hyphen in Supervisor)
        endpoint = "http://farm-agent:8080"

        try:
            async with session.post(
                f"{endpoint}/ask",
                json={"question": "ping"},
                timeout=5,
            ) as resp:
                if resp.status in (200, 400, 500):  # Any response = reachable
                    _LOGGER.info(f"Farm Agent detected at {endpoint}")
                    return endpoint
        except Exception as e:
            _LOGGER.debug(f"Farm Agent detection failed: {e}")

        return None

    async def async_step_import(self, import_data):
        """Import a config entry."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        return self.async_create_entry(
            title="Farm Agent",
            data=import_data
        )
