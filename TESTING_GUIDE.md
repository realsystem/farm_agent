# Testing the Farm Agent

## Prerequisites

### 1. Verify Docker Containers Are Running

```bash
cd /Users/segorov/Projects/AI/simple-agent/addons/farm-agent

# Check both services are healthy
docker-compose -f docker-compose.dev.yml ps

# Expected output:
# NAME            IMAGE                       STATUS
# homeassistant   homeassistant/home-assistant:latest  Up (healthy)
# farm-agent      farm-agent-farm-agent       Up (healthy)
```

### 2. Verify Simulated Entities Are Created

```bash
# Get the HA_TOKEN from .env
HA_TOKEN=$(grep "HA_TOKEN=" .env | cut -d= -f2)

# Verify entities exist in Home Assistant
docker exec homeassistant curl -s 'http://localhost:8123/api/states' \
  -H "Authorization: Bearer $HA_TOKEN" | python3 << 'EOF'
import sys, json
states = json.load(sys.stdin)
eco = [s for s in states if 'eco_worthy' in s['entity_id']]
smart = [s for s in states if 'smartshunt' in s['entity_id']]
print(f"✓ EcoWorthy sensors: {len(eco)}")
print(f"✓ SmartShunt sensors: {len(smart)}")
for s in eco + smart:
    print(f"  - {s['entity_id']}: {s['state']} {s.get('attributes', {}).get('unit_of_measurement', '')}")
EOF
```

### 3. Verify OpenAI API Key Access

```bash
# Get the API key from .env
OPENAI_API_KEY=$(grep "OPENAI_API_KEY=" .env | cut -d= -f2)

# Test if it's valid and has network access
docker exec farm-agent python3 << 'EOF'
import os
from openai import OpenAI

api_key = os.environ.get('OPENAI_API_KEY')
print(f"API Key present: {bool(api_key)}")
print(f"API Key format: {api_key[:10]}..." if api_key else "No key")

try:
    client = OpenAI(api_key=api_key)
    # Try a simple completion
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Say 'test'"}],
        max_tokens=5
    )
    print(f"✓ OpenAI API accessible: {response.choices[0].message.content}")
except Exception as e:
    print(f"✗ OpenAI API error: {type(e).__name__}: {str(e)[:100]}")
EOF
```

## Testing Scenarios

### Scenario 1: Basic Agent Functionality

**Test:** Agent can receive requests and respond

```bash
# GET request with query parameter
curl 'http://localhost:8080/ask?q=Hello'

# Expected response format:
# {"answer": "..."}

# POST request with JSON body
curl -X POST http://localhost:8080/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"Hello"}'
```

### Scenario 2: Health Check

**Test:** Health endpoint is responsive

```bash
curl http://localhost:8080/health

# Expected: {"status": "ok"}
```

### Scenario 3: Entity Discovery with Fallback (No OpenAI)

**Test:** Agent discovers sensors without OpenAI (fallback mode)

```bash
# If OpenAI is not accessible, agent falls back to discovering entities
curl 'http://localhost:8080/ask?q=What%20sensors%20are%20available?'

# If fallback is triggered, returns JSON array of entities:
# {"answer": "[{\"entity_id\": \"sensor.eco_worthy_0b_89a2_voltage\", ...}]"}
```

### Scenario 4: Full Agent with Function Calling (OpenAI Required)

**Test:** Agent uses OpenAI function calling to intelligently query sensors

```bash
# This requires:
# 1. Valid OpenAI API key with network access
# 2. Docker container network access to api.openai.com:443

# Test question 1: Sensor discovery
curl 'http://localhost:8080/ask?q=What%20battery%20sensors%20are%20available?'

# Expected response (with OpenAI):
# {"answer": "The available battery sensors are: sensor.eco_worthy_0b_89a2_voltage, sensor.eco_worthy_0b_89a2_current, sensor.eco_worthy_0b_89a2_temperature, sensor.eco_worthy_0b_89a2_battery, sensor.smartshunt_hq2203nczhp_voltage, sensor.smartshunt_hq2203nczhp_current, and sensor.smartshunt_hq2203nczhp_consumed_ampere_hours."}

# Test question 2: Specific sensor value
curl 'http://localhost:8080/ask?q=What%20is%20the%20current%20battery%20voltage?'

# Expected response (with OpenAI):
# {"answer": "The current battery voltage is 13.28 V."}

# Test question 3: Status assessment
curl 'http://localhost:8080/ask?q=Is%20the%20battery%20charging%20or%20discharging?'

# Expected response (with OpenAI):
# {"answer": "The battery is discharging at 4.2 A. This is indicated by the negative current value of -4.2 A."}

# Test question 4: Battery health
curl 'http://localhost:8080/ask?q=How%20is%20the%20battery%20doing?'

# Expected response (with OpenAI):
# {"answer": "The battery is in good condition. It has a state of charge of 88% and is currently discharging at 4.2 A. The voltage is 13.28 V, which is within normal range, and the temperature is 82°F."}
```

## Debugging Commands

### Check Agent Logs

```bash
# Last 20 lines
docker-compose -f docker-compose.dev.yml logs farm-agent --tail 20

# Live logs
docker-compose -f docker-compose.dev.yml logs -f farm-agent

# Filter for errors
docker-compose -f docker-compose.dev.yml logs farm-agent | grep -i error
```

### Check Home Assistant Status

```bash
# Check if Home Assistant API is accessible
docker exec homeassistant curl -s http://localhost:8123/ | head -20

# Check Home Assistant logs
docker-compose -f docker-compose.dev.yml logs homeassistant --tail 20
```

### Test Home Assistant API Directly

```bash
# Get all entities
HA_TOKEN=$(grep "HA_TOKEN=" .env | cut -d= -f2)
docker exec homeassistant curl -s http://localhost:8123/api/states \
  -H "Authorization: Bearer $HA_TOKEN" | python3 -m json.tool | head -50

# Get specific entity
docker exec homeassistant curl -s 'http://localhost:8123/api/states/sensor.eco_worthy_0b_89a2_voltage' \
  -H "Authorization: Bearer $HA_TOKEN" | python3 -m json.tool
```

### Test OpenAI Connectivity from Container

```bash
# Test DNS resolution
docker exec farm-agent python3 -c "import socket; print(socket.gethostbyname('api.openai.com'))"

# Test TCP connection
docker exec farm-agent python3 << 'EOF'
import socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(5)
result = sock.connect_ex(('api.openai.com', 443))
print("✓ Can reach api.openai.com:443" if result == 0 else f"✗ Cannot reach (error {result})")
sock.close()
EOF

# Test OpenAI API with curl
docker exec farm-agent curl -I https://api.openai.com/v1/models 2>&1 | head -10
```

## Full End-to-End Test Checklist

```bash
#!/bin/bash

echo "=== Farm Agent Testing Checklist ==="
echo ""

# 1. Containers running
echo "1. Container Status:"
docker-compose -f docker-compose.dev.yml ps | grep -E "homeassistant|farm-agent"
echo ""

# 2. Health check
echo "2. Health Check:"
curl -s http://localhost:8080/health | python3 -m json.tool
echo ""

# 3. Entity discovery
echo "3. Entity Discovery:"
curl -s 'http://localhost:8080/ask?q=What%20sensors%20exist?' | python3 -m json.tool | head -10
echo ""

# 4. Specific sensor query
echo "4. Voltage Query:"
curl -s 'http://localhost:8080/ask?q=battery%20voltage?' | python3 -m json.tool | head -5
echo ""

# 5. Check logs for errors
echo "5. Recent Errors:"
docker-compose -f docker-compose.dev.yml logs farm-agent --tail 5 | grep -i "error" || echo "No errors found"
echo ""

echo "✓ Testing complete!"
```

## Expected Behavior by Environment

### With Full OpenAI Access (Raspberry Pi or Unblocked Network)

1. Agent receives question
2. Calls OpenAI API with function tools
3. OpenAI decides which tool to call
4. Agent executes tool (discover_entities or get_entity_state)
5. Result passed back to OpenAI
6. OpenAI formulates intelligent answer
7. Answer returned to user

**Example Response:**
```
Q: "What is the battery voltage?"
A: "The current battery voltage is 13.28 V."
```

### With Limited/No OpenAI Access (Docker Local Environment)

1. Agent receives question
2. Attempts to call OpenAI API
3. Connection fails (SSL, network, or API error)
4. Smart fallback triggered
5. Directly executes discover_entities()
6. Returns raw entity JSON

**Example Response:**
```
Q: "What sensors are available?"
A: "[{"entity_id": "sensor.eco_worthy_0b_89a2_voltage", "state": "13.28", ...}]"
```

## Troubleshooting

### OpenAI API Returns 401 Unauthorized
- Invalid or expired API key
- **Fix:** Verify OPENAI_API_KEY in .env is correct
- **Verify:** `curl -H "Authorization: Bearer $KEY" https://api.openai.com/v1/models`

### OpenAI API Connection Timeout
- Network/firewall blocking api.openai.com:443
- Docker container network restrictions
- **Fix:** Test from container: `docker exec farm-agent curl -I https://api.openai.com/v1/models`
- **Workaround:** Agent automatically falls back to local entity discovery

### Home Assistant Returns 401 Unauthorized
- Invalid or expired HA_TOKEN
- **Fix:** Recreate token in Home Assistant UI
- **Verify:** `curl -H "Authorization: Bearer $TOKEN" http://localhost:8123/api/states`

### Agent Returns "Connection error"
- OpenAI API unreachable from container
- HA_TOKEN invalid
- **Fix:** Check logs: `docker-compose -f docker-compose.dev.yml logs farm-agent`
- **Workaround:** Agent falls back to entity discovery for sensor-related questions

## Performance Expectations

With OpenAI API access:
- Response time: 3-5 seconds (includes OpenAI API latency)
- First request: ~5 seconds (model initialization)
- Subsequent requests: ~3 seconds

With fallback only:
- Response time: <1 second (direct API call)
- Near-instant sensor data retrieval

## Next Steps After Testing

1. ✅ Verify agent works locally
2. Deploy to Raspberry Pi
3. Configure production environment:
   - Use SUPERVISOR_TOKEN instead of HA_TOKEN
   - HA_API_URL: http://supervisor/core/api
4. Test with real farm data in production
5. Monitor logs and performance
