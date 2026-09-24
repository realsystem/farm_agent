"""Conversation agent for Farm Agent."""
import logging
import asyncio

from homeassistant.components.conversation import ConversationEntity, ConversationInput, ConversationResult
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

_LOGGER = logging.getLogger(__name__)

DOMAIN = "farm_agent"


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up conversation entities from a config entry."""
    async_add_entities([FarmAgentConversation(hass, config_entry)])


class FarmAgentConversation(ConversationEntity):
    """Farm Agent conversation entity."""

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Initialize the conversation entity."""
        self.hass = hass
        self.config_entry = config_entry
        self._attr_name = "Farm Agent"
        self._attr_unique_id = "farm_agent_conversation"

    @property
    def supported_languages(self) -> list[str]:
        """Return a list of supported languages."""
        return ["en"]

    async def async_process(
        self, user_input: ConversationInput
    ) -> ConversationResult:
        """Process a conversation turn. Supports 2026.9.x."""
        question = user_input.text

        try:
            session = async_get_clientsession(self.hass)

            async with session.post(
                "http://localhost:8080/ask",
                json={"question": question},
                timeout=30,
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    answer = data.get("answer", "No answer received")

                    return ConversationResult(
                        response=answer,
                        conversation_id=user_input.conversation_id,
                    )
                else:
                    error_text = await resp.text()
                    _LOGGER.error(f"Farm Agent error: {error_text}")
                    return ConversationResult(
                        response=f"Farm Agent error: {error_text}",
                        conversation_id=user_input.conversation_id,
                    )

        except asyncio.TimeoutError:
            _LOGGER.error("Farm Agent request timed out")
            return ConversationResult(
                response="Farm Agent is not responding",
                conversation_id=user_input.conversation_id,
            )
        except Exception as e:
            _LOGGER.error(f"Farm Agent request failed: {e}")
            return ConversationResult(
                response=f"Farm Agent error: {str(e)}",
                conversation_id=user_input.conversation_id,
            )
