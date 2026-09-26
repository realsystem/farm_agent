# Local Development Environment

This guide explains how to set up and run the Farm Agent locally with a real Home Assistant Docker container for development and testing.

## Architecture

```
┌─────────────────────────────────────┐
│ Docker Compose                      │
│                                     │
│  Home Assistant (port 8123)         │
│  http://homeassistant:8123/api      │
│       │                             │
│       │ (real REST API)             │
│       ↓                             │
│  Farm Agent (port 8080)             │
│  http://localhost:8080/ask          │
│       │                             │
│       ↓                             │
│  OpenAI API                         │
│                                     │
└─────────────────────────────────────┘
```

## Prerequisites

- Docker & Docker Compose
- OpenAI API key: https://platform.openai.com/api-keys
- 1-2 GB free disk space (for Home Assistant config)

## Quick Start

### 1. Create .env file

```bash
cp .env.example .env
```

Edit `.env` and add your credentials:

```
OPENAI_API_KEY=sk-proj-...
HA_TOKEN=           # (leave blank for now, create after HA starts)
```

### 2. Start the local environment

```bash
docker-compose -f docker-compose.dev.yml up -d
```

This starts two services:
- **Home Assistant**: http://localhost:8123 (takes 60+ seconds to start)
- **Farm Agent**: http://localhost:8080

### 3. Wait for Home Assistant to fully start

```bash
docker-compose -f docker-compose.dev.yml logs homeassistant
```

Look for:
```
Home Assistant has started
```

(This takes 1-2 minutes on first run as it initializes the database.)

### 4. Complete Home Assistant onboarding

1. Open http://localhost:8123 in your browser
2. Follow the onboarding flow (location, language, etc.)
3. Create a user account

This is a **one-time setup** for your local development environment.

### 5. Create a long-lived access token

1. In Home Assistant, click your **user profile icon** in the **bottom left corner** (shows your name/avatar)
2. This opens your **profile page**
3. Scroll down to **"Long-lived access tokens"** section
4. Click **"Create Token"**
5. Name it "Farm Agent Local Dev"
6. Copy the token that appears
7. Paste it into your `.env` file as `HA_TOKEN`

```bash
# .env
OPENAI_API_KEY=sk-proj-...
HA_TOKEN=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### 6. Restart the Farm Agent

```bash
docker-compose -f docker-compose.dev.yml restart farm-agent
```

Wait for it to be healthy (check logs):

```bash
docker-compose -f docker-compose.dev.yml logs farm-agent
```

### 7. Create simulated farm entities

You need to add Home Assistant entities that represent your farm sensors. The easiest way is to use **Template Sensors** or **Input Helpers**.

#### Option A: Quick setup with template sensors (recommended)

Create a file `farm_entities.yaml` in your Home Assistant config directory:

```bash
docker exec homeassistant mkdir -p /config/includes
```

Create `/config/includes/farm_entities.yaml` with:

```yaml
template:
  - sensor:
      - name: "Battery Voltage"
        unique_id: eco_worthy_0b_89a2_voltage
        unit_of_measurement: "V"
        device_class: voltage
        state: "13.28"
        attributes:
          friendly_name: "EcoWorthy Battery Voltage"

      - name: "Battery Current"
        unique_id: eco_worthy_0b_89a2_current
        unit_of_measurement: "A"
        device_class: current
        state: "-4.2"
        attributes:
          friendly_name: "EcoWorthy Battery Current"

      - name: "Battery Temperature"
        unique_id: eco_worthy_0b_89a2_temperature
        unit_of_measurement: "°F"
        device_class: temperature
        state: "82"
        attributes:
          friendly_name: "EcoWorthy Battery Temperature"

      - name: "Battery SOC"
        unique_id: eco_worthy_0b_89a2_battery
        unit_of_measurement: "%"
        device_class: battery
        state: "88"
        attributes:
          friendly_name: "EcoWorthy Battery State of Charge"

      - name: "SmartShunt Voltage"
        unique_id: smartshunt_hq2203nczhp_voltage
        unit_of_measurement: "V"
        device_class: voltage
        state: "13.28"
        attributes:
          friendly_name: "SmartShunt Voltage"

      - name: "SmartShunt Current"
        unique_id: smartshunt_hq2203nczhp_current
        unit_of_measurement: "A"
        device_class: current
        state: "-4.2"
        attributes:
          friendly_name: "SmartShunt Current"

      - name: "SmartShunt Consumed Ah"
        unique_id: smartshunt_hq2203nczhp_consumed_ampere_hours
        unit_of_measurement: "Ah"
        state: "2450"
        attributes:
          friendly_name: "SmartShunt Consumed Ampere Hours"

      - name: "SmartShunt Alarm"
        unique_id: smartshunt_hq2203nczhp_alarm
        state: "ok"
        attributes:
          friendly_name: "SmartShunt Alarm Status"

      - name: "SmartShunt Signal Strength"
        unique_id: smartshunt_hq2203nczhp_signal_strength
        unit_of_measurement: "%"
        state: "100"
        attributes:
          friendly_name: "SmartShunt Signal Strength"
```

Then add this to your Home Assistant `configuration.yaml`:

```yaml
homeassistant:
  packages:
    farm_entities: !include includes/farm_entities.yaml
```

Restart Home Assistant:

```bash
docker exec homeassistant supervisorctl restart homeassistant
```

Alternatively, use the Web UI:
1. Settings → System → Restart Home Assistant

#### Option B: Manual setup via Home Assistant UI

1. Settings → Devices & Services → Helpers
2. Create **Numeric Input** helpers:
   - Name: "Battery Voltage", Entity ID: `input_number.battery_voltage`, Min: 0, Max: 20, Unit: V
   - Name: "Battery Current", Entity ID: `input_number.battery_current`, Min: -50, Max: 50, Unit: A
   - Name: "Battery Temp", Entity ID: `input_number.battery_temp`, Min: 0, Max: 150, Unit: °F
   - etc.

This is more manual but requires no file editing.

#### Creating Template Sensors (Option C)

If you prefer the UI approach for template sensors:

1. Settings → Devices & Services → Helpers → Create Helper → Template
2. Create a template sensor with entity ID `sensor.eco_worthy_0b_89a2_voltage`

### 8. Test the agent

Once entities are created, test the Farm Agent:

#### GET request (query parameter)

```bash
curl "http://localhost:8080/ask?q=What%20is%20the%20current%20battery%20voltage?"
```

#### POST request (JSON body)

```bash
curl -X POST http://localhost:8080/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the current battery voltage?"
  }'
```

#### Expected response

```json
{
  "answer": "The current battery voltage is 13.28 V."
}
```

### 9. Simulate different conditions

You can change simulated values in Home Assistant to test the agent's responses:

**Normal operation:**
- Voltage: 13.28 V
- Current: -4.2 A (discharging)
- Temperature: 82°F
- SOC: 88%

**Charging:**
```bash
curl -X POST http://localhost:8080/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"Is the battery charging or discharging?"}'
```

Then change the Current value in Home Assistant to `+18` A.

**Low battery:**
```bash
# Change SOC to 20%, Voltage to 12.1 V
```

**Hot battery:**
```bash
# Change Temperature to 105°F
```

Use the Home Assistant UI to change `input_number.*` or template sensor values:
1. Developer Tools → States
2. Find the entity
3. Click to set a new state

## Development Workflow

### 1. Edit agent.py

```bash
nano farm_agent/agent.py
```

### 2. Rebuild and restart (if dependencies changed)

```bash
docker-compose -f docker-compose.dev.yml build farm-agent
docker-compose -f docker-compose.dev.yml up -d farm-agent
```

Or just restart if only Python code changed (volume is mounted):

```bash
docker-compose -f docker-compose.dev.yml restart farm-agent
```

### 3. Test immediately

```bash
curl "http://localhost:8080/ask?q=What%20is%20the%20battery%20voltage?"
```

### 4. Check logs

```bash
docker-compose -f docker-compose.dev.yml logs -f farm-agent
```

## Production vs Local Configuration

The agent automatically selects the correct environment:

### Production (Home Assistant add-on on Raspberry Pi)

```
HA_API_URL=http://supervisor/core/api
SUPERVISOR_TOKEN=<token from supervisor>
```

The agent uses the add-on's Supervisor token (provided by Home Assistant automatically).

### Local Development

```
HA_API_URL=http://homeassistant:8123/api
HA_TOKEN=<long-lived access token>
```

The agent uses a long-lived access token that you created manually.

**The same agent.py code runs in both environments.** The configuration is determined entirely by environment variables.

## Troubleshooting

### "Home Assistant unavailable"

1. Check if Home Assistant is running:
   ```bash
   docker-compose -f docker-compose.dev.yml logs homeassistant
   ```

2. Verify it's fully started (look for "Home Assistant has started")

3. Test direct connection:
   ```bash
   curl http://localhost:8123
   ```

### "Farm Agent is not responding"

1. Check if the Farm Agent is running:
   ```bash
   docker-compose -f docker-compose.dev.yml ps
   ```

2. Check logs:
   ```bash
   docker-compose -f docker-compose.dev.yml logs farm-agent
   ```

3. Check if HA_TOKEN is set:
   ```bash
   docker-compose -f docker-compose.dev.yml exec farm-agent env | grep HA
   ```

### "HA_TOKEN: invalid token" or 401 Unauthorized

1. Your token may have expired or been wrong. Create a new one:
   - Settings → Devices & Services → (Your Name) → Create Token
   - Copy the new token
   - Update `.env`
   - Restart: `docker-compose -f docker-compose.dev.yml restart farm-agent`

### "Entity not found"

1. Verify the entity exists in Home Assistant:
   - Developer Tools → States
   - Search for `sensor.eco_worthy_` or `sensor.smartshunt_`

2. Check the exact entity ID (case-sensitive)

3. Make sure you've created the farm entities (see step 7 above)

### Docker networking issues

If containers can't reach each other:

```bash
# Check the network
docker network ls
docker network inspect <farm_network_name>

# Verify DNS
docker exec farm-agent nslookup homeassistant
```

## Cleanup

To stop and remove the local environment:

```bash
docker-compose -f docker-compose.dev.yml down
```

To keep Home Assistant config (for next development session):

```bash
docker-compose -f docker-compose.dev.yml down
# (config is persisted in Docker volume)
```

To delete everything including Home Assistant data:

```bash
docker-compose -f docker-compose.dev.yml down -v
```

## Notes

- **Credentials are NOT logged**: The .env file is ignored by Git. Never commit .env.
- **Production is unaffected**: The production add-on on the Raspberry Pi is not affected by local development.
- **Real Home Assistant**: The local environment uses the real Home Assistant container (not mocked).
- **Real entity IDs**: Simulated entities use the same entity IDs as production so you can test the exact same agent code.
- **Fast iteration**: Python code changes take effect immediately (the source is mounted in the container).

## Next Steps

Once the environment is running:

1. ✅ Test basic agent functionality
2. 🔧 Edit `farm_agent/agent.py` and add new tools
3. 📊 Add more simulated entities to test additional features
4. 🧪 Run the existing tests with local HA: `python farm_agent/test_agent.py`
5. 🚀 Deploy changes to production when confident

## More Information

- Production setup: [INSTALLATION.md](INSTALLATION.md)
- Test plan: [TESTING.md](TESTING.md)
- Integration details: [INTEGRATION_SETUP.md](INTEGRATION_SETUP.md)
