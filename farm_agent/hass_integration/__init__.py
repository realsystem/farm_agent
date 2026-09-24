"""Farm Agent Conversation integration for Home Assistant."""
import logging

_LOGGER = logging.getLogger(__name__)

DOMAIN = "farm_agent"

async def async_setup(hass, config):
    """Set up the Farm Agent integration."""
    _LOGGER.debug("Setting up Farm Agent integration")
    return True


async def async_setup_entry(hass, entry):
    """Set up Farm Agent from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Store the endpoint URL from config
    endpoint = entry.data.get("endpoint", "http://farm-agent:8080")
    hass.data[DOMAIN][entry.entry_id] = {
        "endpoint": endpoint,
        "entry": entry,
    }

    _LOGGER.info(f"Farm Agent configured with endpoint: {endpoint}")

    await hass.config_entries.async_forward_entry_setups(entry, ["conversation"])
    return True


async def async_unload_entry(hass, entry):
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, ["conversation"])
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
