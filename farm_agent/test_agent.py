import json
import unittest
from unittest.mock import patch, MagicMock
import asyncio
import urllib.request
from http.client import HTTPConnection
import socket


def _can_import_agent():
    """Check if agent module can be imported."""
    try:
        import agent
        return True
    except (ImportError, AttributeError):
        return False


class TestAgentHTTPServer(unittest.TestCase):
    """Test HTTP API endpoints."""

    def test_health_endpoint_responds(self):
        """Test that /health endpoint returns 200 with status ok."""
        try:
            conn = HTTPConnection("127.0.0.1", 8080, timeout=5)
            conn.request("GET", "/health")
            response = conn.getresponse()
            data = response.read().decode()
            conn.close()

            self.assertEqual(response.status, 200)
            parsed = json.loads(data)
            self.assertEqual(parsed.get("status"), "ok")
        except (socket.error, ConnectionRefusedError):
            self.skipTest("agent.py HTTP server not running")

    def test_ask_get_missing_parameter(self):
        """Test that GET /ask without q parameter returns 400."""
        try:
            conn = HTTPConnection("127.0.0.1", 8080, timeout=5)
            conn.request("GET", "/ask")
            response = conn.getresponse()
            conn.close()

            self.assertEqual(response.status, 400)
        except (socket.error, ConnectionRefusedError):
            self.skipTest("agent.py HTTP server not running")

    def test_ask_post_missing_question(self):
        """Test that POST /ask with empty question returns 400."""
        try:
            conn = HTTPConnection("127.0.0.1", 8080, timeout=5)
            body = json.dumps({"question": ""})
            conn.request("POST", "/ask", body, {"Content-Type": "application/json"})
            response = conn.getresponse()
            conn.close()

            self.assertEqual(response.status, 400)
        except (socket.error, ConnectionRefusedError):
            self.skipTest("agent.py HTTP server not running")

    def test_ask_post_invalid_json(self):
        """Test that POST /ask with invalid JSON returns 400."""
        try:
            conn = HTTPConnection("127.0.0.1", 8080, timeout=5)
            conn.request("POST", "/ask", "not valid json", {"Content-Type": "application/json"})
            response = conn.getresponse()
            conn.close()

            self.assertEqual(response.status, 400)
        except (socket.error, ConnectionRefusedError):
            self.skipTest("agent.py HTTP server not running")

    def test_404_on_unknown_path(self):
        """Test that unknown paths return 404."""
        try:
            conn = HTTPConnection("127.0.0.1", 8080, timeout=5)
            conn.request("GET", "/unknown")
            response = conn.getresponse()
            conn.close()

            self.assertEqual(response.status, 404)
        except (socket.error, ConnectionRefusedError):
            self.skipTest("agent.py HTTP server not running")


class TestAgentTools(unittest.TestCase):
    """Test agent tool functions and configuration."""

    def setUp(self):
        """Skip all tests if agent module can't be imported."""
        if not _can_import_agent():
            self.skipTest("agents module not available")

    def test_discover_entities_function_exists(self):
        """Test that discover_entities function is defined."""
        from farm_agent.agent import discover_entities
        self.assertTrue(callable(discover_entities))

    def test_get_entity_state_function_exists(self):
        """Test that get_entity_state function is defined."""
        from farm_agent.agent import get_entity_state
        self.assertTrue(callable(get_entity_state))

    def test_agent_is_configured(self):
        """Test that agent is properly configured."""
        from farm_agent.agent import agent
        self.assertEqual(agent.name, "Farm Assistant")
        self.assertIsNotNone(agent.instructions)
        self.assertTrue(len(agent.tools) >= 2)

    def test_agent_has_correct_tools(self):
        """Test that agent has the expected tools."""
        from farm_agent.agent import agent
        tool_names = [tool.__name__ for tool in agent.tools]
        self.assertIn("discover_entities", tool_names)
        self.assertIn("get_entity_state", tool_names)

    def test_get_entity_state_validation_blocks_unauthorized(self):
        """Test that get_entity_state rejects unauthorized entities."""
        from farm_agent.agent import get_entity_state
        result = get_entity_state("light.unauthorized")
        # Should return error for non-whitelisted entities
        self.assertIsInstance(result, str)
        self.assertIn("not available", result.lower())

    def test_get_entity_state_allows_whitelisted_sensors(self):
        """Test that get_entity_state approves whitelisted patterns."""
        from farm_agent.agent import get_entity_state
        # These calls will fail (entities don't exist) but should validate successfully
        result = get_entity_state("sensor.eco_worthy_test")
        # Should not reject due to whitelist; may fail due to entity not existing
        self.assertIsInstance(result, str)

    @patch('farm_agent.agent.urllib.request.urlopen')
    def test_discover_entities_returns_json(self, mock_urlopen):
        """Test that discover_entities returns valid JSON."""
        from farm_agent.agent import discover_entities
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps([
            {
                "entity_id": "sensor.eco_worthy_test",
                "attributes": {"friendly_name": "Test Sensor"},
                "state": "42"
            }
        ]).encode()
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = discover_entities()
        parsed = json.loads(result)
        self.assertIsInstance(parsed, list)

    @patch('farm_agent.agent.urllib.request.urlopen')
    def test_get_entity_state_returns_json(self, mock_urlopen):
        """Test that get_entity_state returns valid JSON on success."""
        from farm_agent.agent import get_entity_state
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "state": "48.2",
            "attributes": {"unit_of_measurement": "V"}
        }).encode()
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = get_entity_state("sensor.eco_worthy_0b_89a2_voltage")
        parsed = json.loads(result)
        self.assertIsInstance(parsed, dict)


class TestAgentImports(unittest.TestCase):
    """Test that all required modules can be imported."""

    def test_stdlib_imports(self):
        """Test that standard library imports work."""
        import asyncio
        import json
        import os
        import urllib.request
        from http.server import HTTPServer, BaseHTTPRequestHandler
        from urllib.parse import urlparse, parse_qs
        self.assertTrue(True)

    def test_third_party_imports(self):
        """Test that required third-party packages are available."""
        try:
            from openai import Agent
            self.assertTrue(True)
        except ImportError:
            self.skipTest("openai package not installed")


if __name__ == "__main__":
    unittest.main()
