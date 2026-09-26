# Farm Agent Dashboard UI Setup

This guide explains how to set up a simple Home Assistant dashboard UI for asking arbitrary questions to the Farm Agent.

## What This Does

Provides a dashboard card in Home Assistant where you can:

1. Type a question (e.g., "What is the current battery voltage?")
2. Click "Ask Farm Agent"
3. See the answer displayed in the dashboard

The request originates from Home Assistant itself (not your browser), so the Farm Agent endpoint does not need to be publicly accessible.

## Architecture

```
┌─────────────────────────┐
│ Home Assistant          │
│                         │
│ input_text              │
│  farm_agent_question    │
│  farm_agent_answer      │
│                         │
│ script.farm_agent_ask   │
└────────────┬────────────┘
             │ POST /ask
             │ (originates from HA)
             ↓
┌─────────────────────────┐
│ Farm Agent Add-on       │
│ (http://farm-agent:8080)│
└─────────────────────────┘
```

The dashboard calls the existing Farm Agent `/ask` endpoint internally within the Home Assistant network.

## Installation

### Step 1: Add Home Assistant Configuration

You have two options:

**Option A: Add to configuration.yaml**

1. SSH into Home Assistant or connect via SMB to `~/.homeassistant/`
2. Edit `configuration.yaml`
3. Add the contents of `ha-dashboard-config.yaml` to the appropriate sections:
   - `input_text:` entries
   - `script:` entries
   - `rest_command:` entries

**Option B: Use configuration.yaml includes (recommended)**

1. Copy `ha-dashboard-config.yaml` to `~/.homeassistant/farm_agent/config.yaml`
2. In your main `configuration.yaml`, add:

```yaml
# Include Farm Agent configuration
input_text: !include farm_agent/config.yaml?section=input_text
script: !include farm_agent/config.yaml?section=script
rest_command: !include farm_agent/config.yaml?section=rest_command
```

### Step 2: Restart Home Assistant (or use hot reload)

Option 1: Full restart
- Settings → System → Restart Home Assistant

Option 2: Reload helpers (no restart needed)
- Developer Tools → YAML → Reload Input Text Helpers

### Step 3: Create the Dashboard Card

1. Open Home Assistant
2. Go to Settings → Dashboards
3. Select your dashboard (or create a new one)
4. Click the three-dot menu and select "Edit dashboard"
5. Click the "+" button to add a new card
6. Select "Manual card" (or "By YAML")
7. Copy the YAML from `ha-dashboard-card.yaml` into the editor
8. Click Save

Alternatively, if your dashboard is in edit mode, you can use the UI to add:
- An Entities card showing:
  - `input_text.farm_agent_question`
  - `input_text.farm_agent_answer`
- A Button card that calls `script.farm_agent_ask`

## Usage

1. Open Home Assistant app
2. Navigate to your Farm Agent dashboard
3. Type a question in the "Question" field:
   - "What is the current battery voltage?"
   - "Is the battery charging?"
   - "What is the temperature?"
   - "Which sensors are available?"
4. Click "Ask Farm Agent" button
5. Wait 3-5 seconds for the answer to appear

## What Gets Created

### Helpers (Input Text)

- **input_text.farm_agent_question**
  - Stores the user's question
  - Max 500 characters
  - Used as input to the script

- **input_text.farm_agent_answer**
  - Displays the answer from Farm Agent
  - Max 1000 characters
  - Updated after each request

### Script

- **script.farm_agent_ask**
  - Takes the question from `input_text.farm_agent_question`
  - Calls `rest_command.farm_agent_ask`
  - Stores the response in `input_text.farm_agent_answer`
  - Shows "Asking Farm Agent..." while waiting
  - Shows error message if Farm Agent is unavailable

### REST Command

- **rest_command.farm_agent_ask**
  - Endpoint: `http://farm-agent:8080/ask` (internal Docker hostname)
  - Method: POST
  - Payload: `{"question": "..."}`
  - Timeout: 35 seconds

## Networking Details

### Why "farm-agent:8080"?

The hostname `farm-agent:8080` is the internal Docker service name used within the Home Assistant network. This hostname is NOT publicly accessible from the internet.

When the script runs on Home Assistant, it uses this internal hostname to reach the Farm Agent add-on container.

### Security

- The request originates from Home Assistant itself, not from your browser
- The endpoint is not exposed to the LAN or internet
- OpenAI API key remains in the add-on only
- Supervisor token remains in the add-on only
- No credentials are sent in the dashboard

## Error Handling

The dashboard handles common errors:

- **"Please enter a question first."** — You left the question field empty
- **"Asking Farm Agent..."** — Request is in progress (give it 3-5 seconds)
- **"Farm Agent is unavailable. Please check the add-on status."** — The add-on is stopped or not responding
- Any other response — Direct answer from Farm Agent

## Limitations

- Maximum question length: 500 characters
- Maximum answer length: 1000 characters (long answers will be truncated)
- Only plain text questions (no images)
- Requests must complete within 35 seconds
- Only accessible from Home Assistant (not externally)

## Troubleshooting

### Dashboard card doesn't appear

- Verify the YAML syntax is correct
- Restart the browser/app
- Check Settings → Devices & Services for any Farm Agent errors

### "Farm Agent is unavailable" error

1. Check that the Farm Agent add-on is running:
   - Settings → Add-ons → Farm Agent
   - Status should show "Running"

2. Check add-on logs:
   - Settings → Add-ons → Farm Agent → Logs
   - Should show no errors

3. Verify the question has the OPENAI_API_KEY set:
   - Settings → Add-ons → Farm Agent → Configuration
   - openai_api_key should be filled

### Answer is empty or truncated

- Very long answers (>1000 chars) are truncated
- If answer is legitimately empty, check the add-on logs
- Ask a more specific question to get a shorter answer

### Timeout (takes >35 seconds)

- OpenAI API might be slow
- Try a simpler question
- Increase the timeout in `rest_command.farm_agent_ask` if needed

## Customization

### Change the endpoint

If for some reason the endpoint is different, edit `ha-dashboard-config.yaml`:

```yaml
rest_command:
  farm_agent_ask:
    url: "http://your-custom-endpoint:8080/ask"  # Change this line
```

### Change the appearance

The card YAML can be customized:

- Change title
- Change icons (search for mdi: icon names at materialdesignicons.com)
- Add styling
- Rearrange layout

### Use automations instead of script

Instead of a button that calls the script, you could create an automation triggered by:
- A button press
- A voice command
- A specific time
- Any other Home Assistant trigger

## Testing Without a Real Home Assistant

You can validate the YAML syntax locally:

```bash
# Check if YAML is valid
python3 -c "import yaml; yaml.safe_load(open('ha-dashboard-config.yaml'))"

# No errors = valid YAML
```

For full end-to-end testing, a real Home Assistant instance is required.

## Related Files

- `ha-dashboard-config.yaml` — Configuration (helpers, script, REST command)
- `ha-dashboard-card.yaml` — Dashboard card (UI)
- `../farm_agent/hass_integration/` — The Farm Agent integration (not modified)
- `../farm_agent/agent.py` — The Farm Agent Python code (not modified)

## Next Steps

1. Copy the configuration to your Home Assistant instance
2. Restart (or reload helpers)
3. Create the dashboard card
4. Test by asking a question

That's it! You now have a simple, working UI for the Farm Agent.
