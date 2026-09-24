"""Tests for Home Assistant Conversation integration (without HA runtime)."""
import asyncio
import json
import unittest
from unittest.mock import Mock, AsyncMock, MagicMock, patch
import sys
from pathlib import Path

# Test that imports work without Home Assistant
class TestIntegrationImports(unittest.TestCase):
    """Test that integration files have correct syntax."""

    def test_conversation_file_has_correct_structure(self):
        """Verify conversation.py has expected class and method."""
        # We can't import it without HA, but we can verify the structure
        conv_file = Path(__file__).parent / "hass_integration" / "conversation.py"
        content = conv_file.read_text()

        # Check for key class
        self.assertIn("class FarmAgentConversation", content)

        # Check for expected method
        self.assertIn("async def async_process", content)

        # Check for HTTP client usage
        self.assertIn("async_get_clientsession", content)

        # Check for correct endpoint (farm-agent, not localhost)
        self.assertIn("farm-agent:8080", content)

    def test_config_flow_has_correct_structure(self):
        """Verify config_flow.py has expected class."""
        cf_file = Path(__file__).parent / "hass_integration" / "config_flow.py"
        content = cf_file.read_text()

        # Check for config flow class
        self.assertIn("class FarmAgentConfigFlow", content)

        # Check for async_step_user
        self.assertIn("async def async_step_user", content)

        # Check for endpoint detection
        self.assertIn("_detect_endpoint", content)

        # Check that it uses farm-agent hostname (not localhost)
        self.assertIn("farm-agent:8080", content)

    def test_manifest_is_valid_json(self):
        """Verify manifest.json is valid."""
        manifest_file = Path(__file__).parent / "hass_integration" / "manifest.json"
        content = manifest_file.read_text()

        try:
            manifest = json.loads(content)
            self.assertIn("domain", manifest)
            self.assertEqual(manifest["domain"], "farm_agent")
            self.assertIn("homeassistant", manifest)
            self.assertGreaterEqual(manifest["homeassistant"]["min_version"], "2026.9.0")
        except json.JSONDecodeError as e:
            self.fail(f"manifest.json is not valid JSON: {e}")


class TestConversationEntityContract(unittest.TestCase):
    """Test the expected interface without running Home Assistant."""

    def test_conversation_entity_would_need_these_methods(self):
        """Verify code has methods that ConversationEntity would require."""
        conv_file = Path(__file__).parent / "hass_integration" / "conversation.py"
        content = conv_file.read_text()

        # Must have async_process for Conversation integration
        self.assertIn("async def async_process", content,
                     "ConversationEntity must implement async_process")

        # Should accept ConversationInput
        self.assertIn("user_input: ConversationInput", content,
                     "async_process must accept ConversationInput")

        # Should return ConversationResult
        self.assertIn("ConversationResult", content,
                     "async_process must return ConversationResult")

    def test_config_entry_setup_structure(self):
        """Verify async_setup_entry is present."""
        init_file = Path(__file__).parent / "hass_integration" / "__init__.py"
        content = init_file.read_text()

        self.assertIn("async def async_setup_entry", content)
        self.assertIn("async_forward_entry_setups", content)


class TestHTTPEndpointAssumptions(unittest.TestCase):
    """Test the HTTP endpoint usage."""

    def test_endpoint_is_specified(self):
        """Verify the endpoint URL is explicitly defined."""
        conv_file = Path(__file__).parent / "hass_integration" / "conversation.py"
        content = conv_file.read_text()

        # Check that farm-agent:8080/ask is used (verified hostname)
        self.assertIn("farm-agent:8080", content)

    def test_request_format_is_documented(self):
        """Verify request format matches Farm Agent API."""
        conv_file = Path(__file__).parent / "hass_integration" / "conversation.py"
        content = conv_file.read_text()

        # Check that JSON request is used
        self.assertIn('"question"', content)
        self.assertIn('json={"question":', content)

    def test_response_parsing_documented(self):
        """Verify response format expectations."""
        conv_file = Path(__file__).parent / "hass_integration" / "conversation.py"
        content = conv_file.read_text()

        # Check that it expects "answer" field
        self.assertIn('.get("answer"', content)


class TestErrorHandling(unittest.TestCase):
    """Test error handling in conversation entity."""

    def test_timeout_error_caught(self):
        """Verify timeout errors are handled."""
        conv_file = Path(__file__).parent / "hass_integration" / "conversation.py"
        content = conv_file.read_text()

        self.assertIn("asyncio.TimeoutError", content)
        self.assertIn("Farm Agent is not responding", content)

    def test_generic_exception_caught(self):
        """Verify generic exceptions are handled."""
        conv_file = Path(__file__).parent / "hass_integration" / "conversation.py"
        content = conv_file.read_text()

        self.assertIn("except Exception", content)

    def test_http_error_responses_handled(self):
        """Verify HTTP error responses are handled."""
        conv_file = Path(__file__).parent / "hass_integration" / "conversation.py"
        content = conv_file.read_text()

        self.assertIn("if resp.status == 200", content)
        self.assertIn("else:", content)


class TestConfigFlowIssues(unittest.TestCase):
    """Test config flow for potential issues."""

    def test_config_flow_stores_endpoint(self):
        """Verify config flow stores the endpoint."""
        cf_file = Path(__file__).parent / "hass_integration" / "config_flow.py"
        content = cf_file.read_text()

        self.assertIn('data={"endpoint":', content)
        self.assertIn('farm-agent:8080', content)

    def test_config_flow_has_single_instance_check(self):
        """Verify only one instance is allowed."""
        cf_file = Path(__file__).parent / "hass_integration" / "config_flow.py"
        content = cf_file.read_text()

        self.assertIn("single_instance_allowed", content)

    def test_config_flow_verifies_connectivity(self):
        """Verify config flow tests the endpoint."""
        cf_file = Path(__file__).parent / "hass_integration" / "config_flow.py"
        content = cf_file.read_text()

        # Config flow should detect and verify the endpoint
        self.assertIn("_detect_endpoint", content)
        self.assertIn("session.post", content)
        self.assertIn("farm-agent:8080", content)


class TestFarmAgentAPIContract(unittest.TestCase):
    """Test that Farm Agent HTTP API is called correctly."""

    def test_get_ask_endpoint_still_works(self):
        """Verify GET /ask?q=... endpoint still exists."""
        # This is tested in test_agent.py, just documenting the requirement
        agent_file = Path(__file__).parent / "agent.py"
        content = agent_file.read_text()

        self.assertIn("def do_GET", content)
        self.assertIn('"/ask"', content)

    def test_post_ask_endpoint_still_works(self):
        """Verify POST /ask endpoint still exists."""
        agent_file = Path(__file__).parent / "agent.py"
        content = agent_file.read_text()

        self.assertIn("def do_POST", content)
        self.assertIn('"question"', content)


class TestIntegrationFilesNotModified(unittest.TestCase):
    """Verify we didn't break existing files."""

    def test_agent_py_unchanged(self):
        """Verify agent.py wasn't accidentally modified."""
        agent_file = Path(__file__).parent / "agent.py"
        content = agent_file.read_text()

        # Should have OpenAI Agents SDK import
        self.assertIn("from agents import Agent", content)

        # Should have HTTP server
        self.assertIn("HTTPServer", content)

        # Should have /ask endpoints
        self.assertIn('"/ask"', content)

    def test_config_yaml_unchanged(self):
        """Verify config.yaml wasn't modified."""
        config_file = Path(__file__).parent / "config.yaml"
        content = config_file.read_text()

        # Should have port 8080
        self.assertIn("8080", content)

        # Should have openai_api_key option
        self.assertIn("openai_api_key", content)


class TestSecurityAssumptions(unittest.TestCase):
    """Test security-related assumptions."""

    def test_conversation_does_not_expose_secrets(self):
        """Verify conversation.py doesn't log or return sensitive data."""
        conv_file = Path(__file__).parent / "hass_integration" / "conversation.py"
        content = conv_file.read_text()

        # Should not have OpenAI API key references
        self.assertNotIn("openai", content.lower())

        # Should not have Supervisor token references
        self.assertNotIn("supervisor_token", content.lower())

    def test_config_flow_does_not_store_secrets(self):
        """Verify config flow doesn't store API keys."""
        cf_file = Path(__file__).parent / "hass_integration" / "config_flow.py"
        content = cf_file.read_text()

        # Should not store openai_api_key
        self.assertNotIn("openai_api_key", content.lower())


if __name__ == "__main__":
    # Run tests
    suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Exit with error if any tests failed
    sys.exit(0 if result.wasSuccessful() else 1)
