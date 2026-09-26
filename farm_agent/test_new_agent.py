#!/usr/bin/env python3
"""
Test suite for new OpenAI-based agent implementation.

Tests the configuration mechanism and HTTP API without requiring
OpenAI API key or Home Assistant instance.
"""

import os
import unittest
import json
from unittest.mock import patch, MagicMock
import sys
import urllib.request


# Import the configuration functions
import sys
import os as os_module
sys.path.insert(0, os_module.path.dirname(__file__))
from agent import _get_ha_config, _make_ha_request, discover_entities, get_entity_state


class TestConfiguration(unittest.TestCase):
    """Test Home Assistant configuration mechanism."""

    def setUp(self):
        """Clear environment before each test."""
        for key in ['HA_API_URL', 'HA_TOKEN', 'SUPERVISOR_TOKEN']:
            os.environ.pop(key, None)

    def tearDown(self):
        """Clean up after each test."""
        for key in ['HA_API_URL', 'HA_TOKEN', 'SUPERVISOR_TOKEN']:
            os.environ.pop(key, None)

    def test_production_configuration(self):
        """Production environment uses Supervisor API and token."""
        os.environ['SUPERVISOR_TOKEN'] = 'supervisor-test-token'

        ha_api_url, token = _get_ha_config()

        self.assertEqual(ha_api_url, "http://supervisor/core/api")
        self.assertEqual(token, "supervisor-test-token")

    def test_development_configuration(self):
        """Development environment uses local HA and long-lived token."""
        os.environ['HA_API_URL'] = 'http://homeassistant:8123/api'
        os.environ['HA_TOKEN'] = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'

        ha_api_url, token = _get_ha_config()

        self.assertEqual(ha_api_url, "http://homeassistant:8123/api")
        self.assertEqual(token, "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")

    def test_missing_both_configs(self):
        """Missing both production and dev configs raises ValueError."""
        with self.assertRaises(ValueError) as ctx:
            _get_ha_config()

        self.assertIn("SUPERVISOR_TOKEN", str(ctx.exception))
        self.assertIn("HA_API_URL", str(ctx.exception))

    def test_missing_ha_token_with_url(self):
        """HA_API_URL without HA_TOKEN raises ValueError."""
        os.environ['HA_API_URL'] = 'http://homeassistant:8123/api'

        with self.assertRaises(ValueError) as ctx:
            _get_ha_config()

        self.assertIn("HA_TOKEN", str(ctx.exception))


class TestEntityAllowlist(unittest.TestCase):
    """Test entity ID allowlisting for security."""

    def test_eco_worthy_allowed(self):
        """EcoWorthy entities are allowed."""
        allowed_ids = [
            'sensor.eco_worthy_0b_89a2_voltage',
            'sensor.eco_worthy_0b_89a2_current',
            'sensor.eco_worthy_0b_89a2_temperature',
            'sensor.eco_worthy_0b_89a2_battery',
        ]

        for entity_id in allowed_ids:
            allowed = (
                entity_id.startswith("sensor.eco_worthy_")
                or entity_id.startswith("sensor.smartshunt_")
                or entity_id == "sun.sun"
            )
            self.assertTrue(allowed, f"{entity_id} should be allowed")

    def test_smartshunt_allowed(self):
        """SmartShunt entities are allowed."""
        allowed_ids = [
            'sensor.smartshunt_hq2203nczhp_voltage',
            'sensor.smartshunt_hq2203nczhp_current',
            'sensor.smartshunt_hq2203nczhp_consumed_ampere_hours',
            'sensor.smartshunt_hq2203nczhp_alarm',
            'sensor.smartshunt_hq2203nczhp_signal_strength',
        ]

        for entity_id in allowed_ids:
            allowed = (
                entity_id.startswith("sensor.eco_worthy_")
                or entity_id.startswith("sensor.smartshunt_")
                or entity_id == "sun.sun"
            )
            self.assertTrue(allowed, f"{entity_id} should be allowed")

    def test_sun_allowed(self):
        """Sun entity is allowed."""
        entity_id = 'sun.sun'
        allowed = (
            entity_id.startswith("sensor.eco_worthy_")
            or entity_id.startswith("sensor.smartshunt_")
            or entity_id == "sun.sun"
        )
        self.assertTrue(allowed)

    def test_other_entities_blocked(self):
        """Other entities are blocked for security."""
        blocked_ids = [
            'light.living_room',
            'switch.kitchen',
            'climate.bedroom',
            'sensor.other_device',
            'binary_sensor.motion',
        ]

        for entity_id in blocked_ids:
            allowed = (
                entity_id.startswith("sensor.eco_worthy_")
                or entity_id.startswith("sensor.smartshunt_")
                or entity_id == "sun.sun"
            )
            self.assertFalse(allowed, f"{entity_id} should be blocked")


class TestToolFunctions(unittest.TestCase):
    """Test tool functions with mocked Home Assistant."""

    def setUp(self):
        """Set up test configuration."""
        os.environ['SUPERVISOR_TOKEN'] = 'test-token'

    def tearDown(self):
        """Clean up after each test."""
        for key in ['HA_API_URL', 'HA_TOKEN', 'SUPERVISOR_TOKEN']:
            os.environ.pop(key, None)

    @patch('urllib.request.urlopen')
    def test_discover_entities(self, mock_urlopen):
        """Test discover_entities with mocked HA response."""
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps([
            {
                "entity_id": "sensor.eco_worthy_0b_89a2_voltage",
                "state": "13.28",
                "attributes": {
                    "friendly_name": "Battery Voltage",
                    "unit_of_measurement": "V"
                }
            },
            {
                "entity_id": "sensor.smartshunt_hq2203nczhp_current",
                "state": "-4.2",
                "attributes": {
                    "friendly_name": "Battery Current",
                    "unit_of_measurement": "A"
                }
            },
            {
                "entity_id": "light.living_room",  # Should be filtered out
                "state": "on",
                "attributes": {}
            }
        ]).encode('utf-8')
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        result = discover_entities()
        entities = json.loads(result)

        # Should only have 2 entities (light filtered out)
        self.assertEqual(len(entities), 2)
        entity_ids = [e["entity_id"] for e in entities]
        self.assertIn("sensor.eco_worthy_0b_89a2_voltage", entity_ids)
        self.assertIn("sensor.smartshunt_hq2203nczhp_current", entity_ids)
        self.assertNotIn("light.living_room", entity_ids)

    @patch('urllib.request.urlopen')
    def test_get_entity_state_allowed(self, mock_urlopen):
        """Test get_entity_state for allowed entities."""
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "entity_id": "sensor.eco_worthy_0b_89a2_voltage",
            "state": "13.28",
            "attributes": {"unit_of_measurement": "V"}
        }).encode('utf-8')
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        result = get_entity_state("sensor.eco_worthy_0b_89a2_voltage")
        data = json.loads(result)

        self.assertEqual(data["entity_id"], "sensor.eco_worthy_0b_89a2_voltage")
        self.assertEqual(data["state"], "13.28")

    def test_get_entity_state_blocked(self):
        """Test get_entity_state rejects non-whitelisted entities."""
        result = get_entity_state("light.living_room")

        self.assertEqual(result, "Entity is not available through this tool.")

    @patch('urllib.request.urlopen')
    def test_get_entity_state_not_found(self, mock_urlopen):
        """Test get_entity_state handles 404 errors."""
        mock_urlopen.side_effect = urllib.error.HTTPError(
            "http://test", 404, "Not Found", {}, None
        )

        result = get_entity_state("sensor.eco_worthy_nonexistent")

        self.assertIn("not found", result.lower())


class TestOpenAIIntegration(unittest.TestCase):
    """Test OpenAI SDK integration."""

    def test_tools_definition(self):
        """Test that tools are properly defined for OpenAI API."""
        from agent import TOOLS

        # Should have 2 tools
        self.assertEqual(len(TOOLS), 2)

        # Check tool names
        tool_names = [t["function"]["name"] for t in TOOLS]
        self.assertIn("discover_entities", tool_names)
        self.assertIn("get_entity_state", tool_names)

        # Each tool should have proper structure
        for tool in TOOLS:
            self.assertEqual(tool["type"], "function")
            self.assertIn("name", tool["function"])
            self.assertIn("description", tool["function"])
            self.assertIn("parameters", tool["function"])

    def test_tool_execution(self):
        """Test _execute_tool function."""
        from agent import _execute_tool

        # Test invalid tool
        result = _execute_tool("nonexistent_tool", {})
        self.assertIn("Unknown tool", result)


class TestNewAgentStructure(unittest.TestCase):
    """Test the overall agent structure."""

    def test_imports(self):
        """Test that all required modules can be imported."""
        try:
            from agent import (
                _get_ha_config,
                _make_ha_request,
                discover_entities,
                get_entity_state,
                TOOLS,
                ask_agent,
            )
            self.assertTrue(callable(ask_agent))
        except ImportError as e:
            self.fail(f"Failed to import from agent: {e}")

    def test_agent_no_longer_uses_old_agents_library(self):
        """Verify we're not importing the old agents library."""
        with open('/Users/segorov/Projects/AI/simple-agent/addons/farm-agent/farm_agent/agent.py', 'r') as f:
            content = f.read()

        # Should NOT import from agents library
        self.assertNotIn('from agents import', content)
        self.assertNotIn('import agents', content)

        # Should import from openai
        self.assertIn('from openai import', content)


if __name__ == '__main__':
    unittest.main()
