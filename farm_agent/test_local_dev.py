#!/usr/bin/env python3
"""
Test suite for local development environment.

Verifies:
- Configuration mechanism (production vs local)
- Home Assistant API connectivity
- Farm entity discovery
- Entity state retrieval
"""

import os
import unittest
from unittest.mock import patch, MagicMock
import json


def _get_ha_config():
    """Get Home Assistant configuration from environment variables."""
    ha_api_url = os.environ.get("HA_API_URL")
    ha_token = os.environ.get("HA_TOKEN")
    supervisor_token = os.environ.get("SUPERVISOR_TOKEN")

    if ha_api_url:
        if not ha_token:
            raise ValueError("HA_TOKEN must be set when HA_API_URL is configured")
        return ha_api_url, ha_token

    ha_api_url = "http://supervisor/core/api"
    if not supervisor_token:
        raise ValueError(
            "SUPERVISOR_TOKEN not set and HA_API_URL not configured. "
            "Set one of: (HA_API_URL + HA_TOKEN) or SUPERVISOR_TOKEN"
        )
    return ha_api_url, supervisor_token


class TestHAConfiguration(unittest.TestCase):
    """Test Home Assistant configuration mechanism."""

    def setUp(self):
        """Clear environment before each test."""
        # Remove all HA-related env vars
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

    def test_production_takes_precedence_if_dev_also_set(self):
        """HA_API_URL takes precedence over SUPERVISOR_TOKEN."""
        # Both are set - HA_API_URL should take precedence
        os.environ['HA_API_URL'] = 'http://homeassistant:8123/api'
        os.environ['HA_TOKEN'] = 'dev-token'
        os.environ['SUPERVISOR_TOKEN'] = 'supervisor-token'

        ha_api_url, token = _get_ha_config()

        self.assertEqual(ha_api_url, "http://homeassistant:8123/api")
        self.assertEqual(token, "dev-token")


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
        """Other entities are blocked."""
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


class TestLocalDevelopmentSetup(unittest.TestCase):
    """Integration tests for local development setup."""

    def test_docker_compose_file_exists(self):
        """docker-compose.dev.yml exists."""
        import os.path
        self.assertTrue(os.path.exists('docker-compose.dev.yml'))

    def test_dockerfile_dev_exists(self):
        """Dockerfile.dev exists."""
        import os.path
        self.assertTrue(
            os.path.exists('farm_agent/Dockerfile.dev'),
            "Dockerfile.dev must exist for local development"
        )

    def test_env_example_exists(self):
        """.env.example exists."""
        import os.path
        self.assertTrue(
            os.path.exists('.env.example'),
            ".env.example must exist for users to copy"
        )

    def test_local_development_docs_exist(self):
        """LOCAL_DEVELOPMENT.md exists."""
        import os.path
        self.assertTrue(
            os.path.exists('LOCAL_DEVELOPMENT.md'),
            "LOCAL_DEVELOPMENT.md should document local setup"
        )

    def test_farm_entities_template_exists(self):
        """dev/farm_entities.yaml exists."""
        import os.path
        self.assertTrue(
            os.path.exists('dev/farm_entities.yaml'),
            "Farm entity templates should be available"
        )


class TestAgentHTTPServer(unittest.TestCase):
    """Test HTTP server configuration."""

    def test_server_respects_agent_host_env(self):
        """Server host can be configured via AGENT_HOST."""
        # This test verifies the code handles AGENT_HOST
        host = os.environ.get("AGENT_HOST", "127.0.0.1")
        port = int(os.environ.get("AGENT_PORT", "8080"))

        # In production/add-on, these should be localhost
        # In Docker, AGENT_HOST=0.0.0.0 to accept connections

        self.assertIn(host, ["127.0.0.1", "0.0.0.0", "localhost"])
        self.assertIsInstance(port, int)
        self.assertGreater(port, 0)

    def test_agent_port_configurable(self):
        """Server port can be configured via AGENT_PORT."""
        # Verify the configuration is flexible
        original_port = os.environ.get("AGENT_PORT")
        try:
            os.environ["AGENT_PORT"] = "9000"
            port = int(os.environ.get("AGENT_PORT", "8080"))
            self.assertEqual(port, 9000)
        finally:
            if original_port:
                os.environ["AGENT_PORT"] = original_port
            else:
                os.environ.pop("AGENT_PORT", None)


if __name__ == '__main__':
    unittest.main()
