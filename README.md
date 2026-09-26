# Farm Agent: AI Assistant for Remote Farm Monitoring

An AI-powered assistant for monitoring a remote farm using Home Assistant Assist and OpenAI Agents SDK.

## What It Does

Farm Agent answers questions about your remote farm in natural language:

- **"What is the current battery voltage?"** → Returns live sensor data
- **"Is the farm battery charging?"** → Analyzes current flow and state
- **"What is the temperature?"** → Fetches latest environmental data

The agent connects to your Home Assistant instance, queries real sensors, and uses OpenAI's language model to provide intelligent answers.

## Architecture

```
Pixel Phone → Home Assistant Assist → Farm Agent Conversation Integration → Farm Agent Add-on → OpenAI Agents SDK → Home Assistant API → Sensors → Answer
```

## Components

### 1. Farm Agent Add-on (`farm_agent/`)

A Home Assistant add-on that runs the AI agent:
- Receives OpenAI API key from configuration
- Exposes HTTP API on port 8080
- Runs OpenAI Agents SDK
- Queries Home Assistant via REST API (through Supervisor token)
- Answers questions about farm sensors

**Files:**
- `agent.py` — Main agent with tools for entity discovery and state retrieval
- `config.yaml` — Add-on configuration and schema
- `run.sh` — Startup script
- `Dockerfile` — Container image definition

### 2. Custom Integration (`farm_agent/hass_integration/`)

A Home Assistant custom integration that bridges Assist to Farm Agent:
- Implements ConversationEntity
- Routes Assist questions to Farm Agent add-on via HTTP
- Returns answers to Assist
- Handles errors gracefully

**Files:**
- `__init__.py` — Integration setup and config entries
- `config_flow.py` — Configuration flow (minimal, auto-setup)
- `conversation.py` — Conversation agent implementation
- `manifest.json` — Integration metadata
- `strings.json` — UI strings

### 3. Documentation

- `INSTALLATION.md` — Step-by-step setup guide
- `INTEGRATION_SETUP.md` — Details about the custom integration
- `TESTING.md` — Comprehensive test plan with 23 test cases
- `HA_DASHBOARD_SETUP.md` — Dashboard UI setup and usage guide
- `README.md` — This file

### 4. Dashboard UI (Optional)

- `ha-dashboard-config.yaml` — Home Assistant helpers and script configuration
- `ha-dashboard-card.yaml` — Dashboard card YAML for the UI

## Quick Start

### 1. Install Farm Agent Add-on

1. Add repository: `https://github.com/realsystem/farm_agent`
2. Install "Farm Agent"
3. Set `openai_api_key` in add-on settings
4. Start the add-on

### 2. Install Custom Integration

Copy `farm_agent/hass_integration/` to `~/.homeassistant/custom_components/farm_agent/`

```bash
# Via SSH:
ssh homeassistant@<HA_IP>
mkdir -p ~/.homeassistant/custom_components/farm_agent
# Copy files from repository...
```

### 3. Restart Home Assistant

**Required for first-time setup.** After restart:

Settings → Devices & Services → Create integration → Farm Agent

### 4. Add to Assist Pipeline

Settings → Voice Assistants → Conversation Agent → Select "Farm Agent"

### 5. Test

Ask on your Pixel phone: "What is the battery voltage?"

**Full details:** See [INSTALLATION.md](INSTALLATION.md)

### 6. (Optional) Add Dashboard UI

For a simple text-based interface to ask arbitrary questions:

1. Copy configuration from `ha-dashboard-config.yaml` into Home Assistant
2. Create a dashboard card using `ha-dashboard-card.yaml`
3. Type questions and click "Ask" from the dashboard

**Full details:** See [HA_DASHBOARD_SETUP.md](HA_DASHBOARD_SETUP.md)

## Key Features

✅ **Simple Setup** — Just add your OpenAI API key and go  
✅ **No Restart Required for Updates** — Reload via UI  
✅ **Secure** — Credentials stay in add-on only  
✅ **Fast** — Local communication, typical 3-5 second response  
✅ **Intelligent** — OpenAI language model understands context  
✅ **Monitored** — Entity whitelist prevents unauthorized access  
✅ **Error Handling** — Graceful failures with clear error messages  

## System Requirements

- **Home Assistant:** 2026.9.3 or later
- **Hardware:** Raspberry Pi 5 / aarch64 or amd64
- **OpenAI API Key:** https://platform.openai.com/api-keys
- **Python:** 3.9+ (runs in container)

## How It Works

1. **User speaks to Assist:** "What is the battery voltage?"
2. **Assist routes to Farm Agent** conversation agent
3. **Integration makes HTTP request** to add-on (farm-agent:8080/ask)
4. **Add-on receives question** via REST endpoint
5. **Agent initializes** with OpenAI Agents SDK
6. **Agent uses tools:**
   - `discover_entities()` — Find relevant sensors
   - `get_entity_state()` — Fetch current values
7. **OpenAI language model** processes sensor data and formulates answer
8. **Answer returned** to integration
9. **Integration returns** to Assist
10. **Assist speaks/displays** the answer

## Monitored Entities

The agent can query these Home Assistant entities:

- `sensor.eco_worthy_*` — Solar system sensors (voltage, current, battery, etc.)
- `sensor.smartshunt_*` — Battery management system sensors
- `sun.sun` — Solar position and sunrise/sunset

Other entities are blocked for security.

## Network Architecture

```
Home Assistant (localhost)
    ↓
Custom Integration (listens)
    ↓
HTTP POST http://farm-agent:8080/ask
    ↓
Farm Agent Add-on (listens on port 8080)
    ↓
Home Assistant REST API (http://supervisor/core/api/states)
    ↓
Sensor data returned to add-on
    ↓
OpenAI API (with agent tools)
    ↓
Answer returned through chain
```

- **Secure:** Supervisor token and OpenAI keys never leave the add-on
- **Fast:** All communication is local (localhost)
- **Simple:** No database, no authentication, minimal dependencies

## Troubleshooting

### Integration not appearing in Settings

1. Verify files: `~/.homeassistant/custom_components/farm_agent/`
2. Restart Home Assistant
3. Check Settings → System → Logs for errors

### "Farm Agent is not responding"

1. Verify add-on is running: Check add-on UI
2. Verify port 8080: `curl http://localhost:8080/ask` (should give 400)
3. Check add-on logs for OpenAI API errors
4. Verify `openai_api_key` is set in add-on settings

### Assist doesn't use Farm Agent

1. Verify integration is installed: Settings → Devices & Services
2. Verify it's selected: Settings → Voice Assistants → Conversation Agent
3. Test manually: Developer Tools → Services → conversation.process

**Full troubleshooting:** See [INSTALLATION.md](INSTALLATION.md)

## Testing

23 automated tests verify:
- HTTP API endpoints (GET/POST /ask)
- Home Assistant entity access
- Integration discovery and loading
- Assist integration
- Error handling
- Concurrent requests

Run tests:
```bash
cd farm_agent
python -m unittest test_integration.py -v
```

**Full test plan:** See [TESTING.md](TESTING.md)

## Files & Directory Structure

```
farm_agent/
├── README.md                          (this file)
├── INSTALLATION.md                    (setup guide)
├── INTEGRATION_SETUP.md               (integration details)
├── TESTING.md                         (test plan & results)
├── repository.yaml                    (repository metadata)
├── Dockerfile                         (container build)
│
└── farm_agent/                        (add-on application)
    ├── agent.py                       (main agent + HTTP server)
    ├── config.yaml                    (add-on config schema)
    ├── run.sh                         (startup script)
    ├── requirements.txt               (Python dependencies)
    ├── test_agent.py                  (smoke tests)
    ├── test_integration.py            (integration tests)
    │
    └── hass_integration/              (custom integration)
        ├── __init__.py                (setup & config entries)
        ├── config_flow.py             (configuration flow)
        ├── conversation.py            (conversation agent)
        ├── manifest.json              (integration metadata)
        └── strings.json               (UI strings)
```

## Security Considerations

### What This Does NOT Expose

- ❌ OpenAI API key (stays in add-on)
- ❌ Supervisor token (stays in add-on)
- ❌ Home Assistant password/token
- ❌ Arbitrary Home Assistant entities (whitelist enforced)
- ❌ Raw sensor data without LLM filtering

### What This Does Protect

- ✅ Entity whitelist blocks unauthorized access
- ✅ Only farm-related sensors are visible to users
- ✅ Credentials are never transmitted to Home Assistant
- ✅ All communication is local (no external API except OpenAI)
- ✅ LLM can refuse harmful requests
- ✅ Errors don't expose internal details to users

### Assumptions

- Home Assistant and the add-on run on the same trusted network
- OpenAI API key is kept confidential in add-on settings
- Users are familiar with their farm equipment

## Performance

Typical response time: **3-5 seconds**

Breakdown:
- 0.2s - HTTP request to Farm Agent
- 0.1s - Discover entities
- 0.2s - Fetch entity states
- 2-4s - OpenAI API call
- 0.1s - Return response

**Factors affecting speed:**
- Network latency to Home Assistant
- OpenAI API load
- Number of entities to query
- Complexity of the question

## Compatibility

- **Home Assistant:** 2026.9.0+
- **OS:** Home Assistant OS 18.2+
- **Hardware:** aarch64 (Raspberry Pi 5) or amd64
- **Python:** 3.9, 3.10, 3.11, 3.12
- **SDK:** OpenAI Agents SDK 0.1.0+

## Local Development Environment

For iterating on the agent without deploying to the Raspberry Pi:

```bash
./dev-setup.sh
```

This starts:
- Real Home Assistant in Docker (http://localhost:8123)
- Farm Agent in Docker (http://localhost:8080)
- Both on a local Docker network

**Key features:**
- ✅ Real Home Assistant (not mocked)
- ✅ Simulated farm entities with realistic values
- ✅ Fast Python iteration (code is mounted in container)
- ✅ Isolated from production Raspberry Pi
- ✅ No credentials in Git (uses .env)

**Quick test after setup:**
```bash
curl "http://localhost:8080/ask?q=What%20is%20the%20battery%20voltage?"
```

**For full details:** [LOCAL_DEVELOPMENT.md](LOCAL_DEVELOPMENT.md)

## Development (Production Add-on)

To modify the agent running on the Raspberry Pi:

1. Edit `farm_agent/agent.py`
2. Test locally with Docker Compose (see above)
3. Rebuild container: `docker build -t farm-agent:latest farm_agent/`
4. Restart add-on in Home Assistant

To modify the integration:

1. Edit `farm_agent/hass_integration/*`
2. Reload integration: Settings → Devices & Services → Farm Agent → Reload
3. Test via conversation.process or Assist
4. No restart required!

## Contributing

Issues and PRs welcome at: https://github.com/realsystem/farm_agent

## License

Open source. Details in repository.

## What's Next

Possible future enhancements:
- Multiple conversation agents in a pipeline
- Persistent conversation history
- Custom entity whitelists
- Voice response synthesis
- Battery optimization alerts
- Power forecasting with weather integration

## Support

**Documentation:**
- [Installation Guide](INSTALLATION.md)
- [Test Plan](TESTING.md)
- [Integration Setup](INTEGRATION_SETUP.md)

**Troubleshooting:**
- Check Settings → System → Logs
- Test Farm Agent directly: `curl -X POST http://localhost:8080/ask ...` (from Home Assistant)
- Verify Home Assistant can reach sensors: Developer Tools → States

**Issues:**
https://github.com/realsystem/farm_agent/issues

---

**Last Updated:** 2026-09-24  
**Version:** 0.4.0  
**Status:** Production Ready
