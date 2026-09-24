# Farm Agent Custom Integration for Home Assistant

This directory contains a custom Home Assistant integration that allows Home Assistant Assist to communicate with the Farm Agent add-on.

## Architecture

```
Pixel Phone
  ↓
Home Assistant Assist
  ↓
Farm Agent Conversation Integration (in Home Assistant)
  ↓
Farm Agent Add-on HTTP API (localhost:8080/ask)
  ↓
OpenAI Agents SDK + Home Assistant API
  ↓
Answer
```

## Installation

### Step 1: Copy Integration to Home Assistant

The custom integration is located in `farm_agent/hass_integration/`.

Copy this directory to your Home Assistant custom integrations folder:

```bash
# On your Home Assistant instance:
mkdir -p /home/homeassistant/.homeassistant/custom_components/farm_agent

# Copy the integration files
cp -r farm_agent/hass_integration/* /home/homeassistant/.homeassistant/custom_components/farm_agent/
```

**Or via SSH to your Home Assistant:**

```bash
scp -r farm_agent/hass_integration/ homeassistant@<HA_IP>:/home/homeassistant/.homeassistant/custom_components/farm_agent/
```

### Step 2: Restart Home Assistant

The custom integration will be discovered automatically on restart.

Go to Settings → Devices & Services → Create Automation → Farm Agent and set it up.

Or if you want to use the UI:
1. Settings → Devices & Services
2. Create Integration → Farm Agent
3. Click Configure

### Step 3: Add Farm Agent to Your Assist Pipeline

1. Go to Settings → Voice Assistants
2. Select your Assist pipeline
3. Under "Conversation Agent", select "Farm Agent"
4. Save

## How It Works

1. User speaks/types a question in Assist
2. Assist sends the text to the Farm Agent Conversation agent
3. The integration makes an HTTP POST request to `http://localhost:8080/ask`
4. Farm Agent (the add-on) receives the question and uses OpenAI Agents SDK
5. The agent uses its tools to query Home Assistant API
6. The answer is returned to the integration
7. The integration returns the answer to Assist
8. Assist speaks/displays the answer

## Communication Details

- **Endpoint:** `http://localhost:8080/ask` (POST)
- **Request:** `{"question": "What is the battery voltage?"}`
- **Response:** `{"answer": "The battery voltage is 48.2V"}`
- **Errors:** Returns response with error message and HTTP error code

## No Configuration Required

The integration does NOT require changes to `configuration.yaml`.

It discovers the Farm Agent add-on automatically at `localhost:8080`.

## Hot Reload

After updating the integration files, you can reload it without restarting Home Assistant:

Settings → Devices & Services → Farm Agent → (three dots) → Reload

## Troubleshooting

### Integration not appearing in Settings

- Verify the integration folder exists at: `/home/homeassistant/.homeassistant/custom_components/farm_agent/`
- Check that `manifest.json` is present
- Restart Home Assistant
- Check the Home Assistant logs for errors

### "Farm Agent is not responding"

- Verify the Farm Agent add-on is running
- Check that the add-on is listening on port 8080
- Verify that `OPENAI_API_KEY` is configured in the add-on settings
- Check the add-on logs for errors

### Timeouts

- The integration waits 30 seconds for Farm Agent to respond
- If the LLM takes too long, increase the timeout in `conversation.py`

## Files

- `__init__.py` — Integration setup
- `config_flow.py` — Configuration flow (minimal, auto-setup)
- `conversation.py` — Conversation entity implementation
- `manifest.json` — Integration metadata
- `strings.json` — UI strings
- `INTEGRATION_SETUP.md` — This file

## Security Notes

- The integration communicates with Farm Agent via `localhost:8080`
- The integration does NOT send OpenAI API keys to Home Assistant
- The integration does NOT expose the Supervisor token to clients
- The Farm Agent add-on remains responsible for authentication with OpenAI and Home Assistant
