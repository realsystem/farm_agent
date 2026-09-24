# Farm Agent Installation Guide

## Prerequisites

- Home Assistant 2026.9.3 (or later)
- Farm Agent add-on already installed and working
- SSH access to your Home Assistant instance, OR
- Access to the config directory via Samba/SMB

## Step 1: Install the Farm Agent Add-on

If not already installed, add the repository to Home Assistant:

1. Go to Settings → Add-ons → Repositories
2. Add: `https://github.com/realsystem/farm_agent`
3. Install "Farm Agent"
4. Set `openai_api_key` in the add-on settings
5. Start the add-on
6. Verify it's running: Check add-on logs for "Listening on port 8080"

## Step 2: Install the Custom Integration

### Method A: Via SSH (Recommended)

On your Home Assistant machine:

```bash
# Log in via SSH
ssh homeassistant@<YOUR_HA_IP>

# Create the custom components directory if it doesn't exist
mkdir -p ~/.homeassistant/custom_components/farm_agent

# Copy the integration files from the repository
# You can either clone/download the repo or copy the files directly
cd ~/farm_agent  # Or wherever you downloaded the repo

cp -r farm_agent/hass_integration/* ~/.homeassistant/custom_components/farm_agent/

# Verify files are there
ls -la ~/.homeassistant/custom_components/farm_agent/
```

Expected files:
```
__init__.py
config_flow.py
conversation.py
manifest.json
strings.json
```

### Method B: Via Samba/Network Share

1. Connect to your Home Assistant Samba share
2. Navigate to: `homeassistant/.homeassistant/custom_components/`
3. Create folder: `farm_agent`
4. Copy these files from the repository into `farm_agent/`:
   - `__init__.py`
   - `config_flow.py`
   - `conversation.py`
   - `manifest.json`
   - `strings.json`

### Method C: Via SCP

```bash
# From your local machine where you have the repository
cd farm_agent
scp -r farm_agent/hass_integration/* homeassistant@<YOUR_HA_IP>:~/.homeassistant/custom_components/farm_agent/
```

## Step 3: Restart Home Assistant

**Important:** A restart is required for Home Assistant to discover the new custom integration.

Go to:
1. Settings → System → Restart Home Assistant
2. OR SSH: `ssh homeassistant@<YOUR_HA_IP>` then `sudo systemctl restart homeassistant`

The restart takes ~2-5 minutes.

## Step 4: Configure the Integration

After Home Assistant restarts:

1. Go to Settings → Devices & Services
2. Look for "Farm Agent" in the integrations list
3. Click "Create Integration" → Search for "Farm Agent"
4. Click "Farm Agent" and then "Create entry"
5. The default settings are fine (communicates with localhost:8080)

## Step 5: Add Farm Agent to Assist Pipeline

1. Go to Settings → Voice Assistants
2. Under "Assist", find your active pipeline (or create one)
3. In "Conversation Agent", select "Farm Agent"
4. Click "Save"

## Step 6: Test It

### Via Assist on Your Phone

Ask your Pixel phone (in the HA app or via Google Assistant):
- "What is the current battery voltage?"
- "Is the farm battery charging?"
- "What is the temperature?"

### Via Home Assistant Web UI

1. Settings → Devices & Services → Farm Agent
2. Click the entity "Farm Agent"
3. Look for a "Test" or "Ask" action (if available)
4. Or use the Developer Tools → Services and call `conversation.process`:

```yaml
service: conversation.process
data:
  agent_id: farm_agent_conversation
  text: "What is the battery voltage?"
```

## Verification

### Check Integration Status

Settings → Devices & Services → Farm Agent

Should show:
- Status: ✓ Loaded
- Platform: Conversation

### Check Logs

If something doesn't work:

1. Settings → System → Logs
2. Search for "farm_agent"
3. Should see:
   - `Setting up Farm Agent integration`
   - `Setting up Farm Agent conversation entity`

### Test Farm Agent Directly

```bash
# SSH into Home Assistant
ssh homeassistant@<YOUR_HA_IP>

# Test the add-on directly
curl -X POST http://localhost:8080/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the battery voltage?"}'

# Expected response:
# {"answer": "The battery voltage is 48.2V"}
```

If this works but Assist doesn't, the integration setup may have an issue. Check Settings → System → Logs.

## No Restart Required for Updates

After the initial setup, you can update the integration files without restarting:

1. Update the files in `~/.homeassistant/custom_components/farm_agent/`
2. Go to Settings → Devices & Services → Farm Agent
3. Click the three dots → Reload
4. Changes are applied immediately

## Troubleshooting

### "Farm Agent integration not found in Settings"

- Verify files are in: `~/.homeassistant/custom_components/farm_agent/`
- Check that `manifest.json` exists and is valid JSON
- Restart Home Assistant (Settings → System → Restart Home Assistant)
- Check Settings → System → Logs for errors

### "Farm Agent is not responding"

- SSH and check Farm Agent add-on is running: `ps aux | grep agent.py`
- Check add-on logs in Home Assistant UI
- Verify port 8080 is accessible: `curl http://localhost:8080/ask` should return 400 (because no question)
- Check that OPENAI_API_KEY is set in add-on settings

### "Entity not available" when asking questions

- Farm Agent may not be discovering entities
- Check Home Assistant is working and states are available: Go to Developer Tools → States
- Verify sensor.eco_worthy_* and sensor.smartshunt_* entities exist
- Check Farm Agent add-on logs for API errors

### Assist doesn't respond

- Verify Farm Agent appears in Settings → Voice Assistants
- Verify it's selected in the pipeline's "Conversation Agent"
- Test via `conversation.process` service first (see Verification section)
- Check Settings → System → Logs for "conversation" errors

### Timeout errors

The integration waits 30 seconds for Farm Agent to respond. If you see timeouts:

1. Check if the OpenAI API is slow
2. Try asking a simpler question
3. If Farm Agent is consistently slow, increase timeout in `conversation.py` (line with `timeout=30`)

## Uninstallation

To remove the integration:

1. Settings → Devices & Services → Farm Agent
2. Click the three dots → Delete
3. Delete the folder: `~/.homeassistant/custom_components/farm_agent/`
4. Restart Home Assistant (optional, but recommended)

## Architecture Overview

```
Pixel Phone with HA App
        ↓
Home Assistant Assist
        ↓
Conversation Integration (farm_agent)
        ↓
HTTP POST to localhost:8080/ask
        ↓
Farm Agent Add-on
        ↓
OpenAI Agents SDK
        ↓
Home Assistant REST API (via Supervisor)
        ↓
Battery sensors / other entities
        ↓
Answer returned through the chain
        ↓
Displayed/spoken in Assist
```

## Security Notes

- The integration only communicates locally (localhost:8080)
- OpenAI API key remains in the add-on only
- Supervisor token remains in the add-on only
- No credentials are exposed to Home Assistant
- The integration cannot access Home Assistant API directly (by design)
- Only the Farm Agent add-on communicates with Home Assistant API

## Support

For issues:
1. Check the logs (Settings → System → Logs)
2. Verify the Farm Agent add-on is running
3. Test the add-on directly with curl (see Troubleshooting)
4. Report issues at: https://github.com/realsystem/farm_agent/issues
