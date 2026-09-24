# Farm Agent Testing Guide

## Test Overview

These tests verify:
1. Farm Agent add-on HTTP API works
2. Custom integration can communicate with the add-on
3. Home Assistant can discover and load the integration
4. Assist can route questions to Farm Agent
5. Questions get answered correctly
6. Error cases are handled gracefully

## Prerequisites

- Farm Agent add-on is installed and running
- Custom integration is installed
- Home Assistant is running and accessible
- You have a way to test Home Assistant APIs (curl, Developer Tools, etc.)

## Test Suite 1: Farm Agent Add-on HTTP API

### Test 1.1: GET /ask endpoint works

**What to test:** The simple GET endpoint accepts questions

```bash
curl "http://localhost:8080/ask?q=What%20is%20the%20battery%20voltage"
```

**Expected result:**
```json
{"answer": "The battery voltage is 48.2V"}
```

**Success criteria:**
- HTTP 200 response
- JSON response with "answer" key
- Answer is a non-empty string

### Test 1.2: POST /ask endpoint works

**What to test:** The JSON POST endpoint accepts questions

```bash
curl -X POST http://localhost:8080/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the battery voltage?"}'
```

**Expected result:**
```json
{"answer": "The battery voltage is 48.2V"}
```

**Success criteria:**
- HTTP 200 response
- JSON response with "answer" key
- Same answer format as GET

### Test 1.3: Missing question parameter returns error

**What to test:** API rejects requests without a question

```bash
# GET without q parameter
curl "http://localhost:8080/ask"

# POST with empty question
curl -X POST http://localhost:8080/ask \
  -H "Content-Type: application/json" \
  -d '{"question": ""}'
```

**Expected result:**
```json
{"error": "..."}
```

or HTTP 400

**Success criteria:**
- HTTP 400 response
- Clear error message

### Test 1.4: Invalid JSON returns error

**What to test:** API handles malformed JSON

```bash
curl -X POST http://localhost:8080/ask \
  -H "Content-Type: application/json" \
  -d 'not valid json'
```

**Expected result:**
- HTTP 400 response
- Error message

## Test Suite 2: Farm Agent ↔ Home Assistant API

### Test 2.1: Agent can discover entities

**What to test:** The agent's discover_entities() tool works

**How to verify:**
1. SSH to Home Assistant machine
2. Use Python to test:

```python
import urllib.request
import json
import os

token = os.environ['SUPERVISOR_TOKEN']
url = "http://supervisor/core/api/states"

request = urllib.request.Request(
    url,
    headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    },
)

with urllib.request.urlopen(request, timeout=5) as response:
    states = json.loads(response.read())

# Filter for farm entities
farm_entities = [
    s for s in states
    if "eco_worthy" in s["entity_id"] or "smartshunt" in s["entity_id"]
]

print(f"Found {len(farm_entities)} farm entities")
for entity in farm_entities:
    print(f"  - {entity['entity_id']}: {entity['state']}")
```

**Expected result:**
- Lists at least one eco_worthy or smartshunt sensor
- Shows current state/value
- No authentication errors

**Success criteria:**
- Entity list is non-empty
- All entities have entity_id, state, attributes
- HTTP 200 response

### Test 2.2: Agent can read entity state

**What to test:** The agent can fetch current values

Ask Farm Agent: "What is the battery voltage?"

**Expected result:**
Agent uses get_entity_state() to fetch:
- sensor.eco_worthy_0b_89a2_voltage
- Returns actual voltage value
- Agent formats answer: "The battery voltage is 48.2V"

**Success criteria:**
- Answer includes numeric value
- Answer includes unit (V)
- Value matches what you see in Home Assistant states

### Test 2.3: Agent reads multiple entities

**What to test:** Agent can correlate multiple readings

Ask Farm Agent: "Is the farm battery charging?"

**Expected result:**
Agent reads:
- Battery current (positive = charging, negative = discharging)
- Voltage
- State of charge
Answers: "Yes, the battery is charging at 15A" or "No, the battery is discharging"

**Success criteria:**
- Agent checks multiple entities
- Answer reflects actual battery state
- Response is natural language

## Test Suite 3: Custom Integration Discovery & Loading

### Test 3.1: Integration appears in Settings

**What to test:** Home Assistant discovers the custom integration

**Steps:**
1. Go to Home Assistant Settings → Devices & Services
2. Search for "Farm Agent"

**Expected result:**
- "Farm Agent" integration appears
- Can click to create entry

**Success criteria:**
- Integration is discoverable
- No errors in Settings
- manifest.json is valid

### Test 3.2: Integration loads and creates entity

**What to test:** The integration sets up properly

**Steps:**
1. Settings → Devices & Services → Farm Agent
2. Check the entity list

**Expected result:**
- Shows "farm_agent_conversation" entity
- Status is "enabled"
- Type is "Conversation"

**Success criteria:**
- Entity is created successfully
- No error messages
- Entity is available in automations/services

### Test 3.3: Integration survives reload

**What to test:** Can reload without restarting Home Assistant

**Steps:**
1. Settings → Devices & Services → Farm Agent
2. Click three dots → Reload
3. Wait for reload to complete

**Expected result:**
- Reload completes successfully
- No error messages
- Entity is still available

**Success criteria:**
- Reload works in <5 seconds
- No restart required
- Entity remains functional

## Test Suite 4: Assist Integration

### Test 4.1: Farm Agent appears in Voice Assistant settings

**What to test:** Farm Agent is available as a conversation agent

**Steps:**
1. Go to Settings → Voice Assistants
2. Click on the active pipeline (or create one)
3. Under "Conversation Agent", look for options

**Expected result:**
- "Farm Agent" appears in the dropdown

**Success criteria:**
- Can select Farm Agent
- Setting persists after save

### Test 4.2: Question via conversation.process service

**What to test:** Can send questions via Home Assistant service

**Steps:**
1. Go to Developer Tools → Services
2. Select service: `conversation.process`
3. Fill in JSON:

```json
{
  "agent_id": "farm_agent_conversation",
  "text": "What is the battery voltage?"
}
```

4. Call service

**Expected result:**
```
Response:
The battery voltage is 48.2V
```

**Success criteria:**
- Service returns successful response
- Answer is natural language
- Response time <30 seconds

### Test 4.3: Question via Assist (Phone)

**What to test:** Assist on a Pixel phone routes to Farm Agent

**Steps:**
1. Open Home Assistant app on your Pixel phone
2. Press microphone button or open Assist
3. Say: "What is the battery voltage?"

**Expected result:**
- Assist listens and processes
- Returns: "The battery voltage is 48.2V"
- Optionally speaks the answer back

**Success criteria:**
- Question is understood
- Answer is correct
- Response time is acceptable (<10 seconds typical)

### Test 4.4: Different question formats

**What to test:** Agent handles varied question phrasing

Test these questions (via phone Assist or conversation.process):

1. "What is the current battery voltage?"
2. "How much battery voltage do we have?"
3. "Is the battery charging?"
4. "Tell me about the battery status"
5. "What is the temperature?"

**Expected result:**
- Agent understands all variations
- Provides relevant answer
- Falls back gracefully if question is ambiguous

**Success criteria:**
- All questions get reasonable answers
- Agent doesn't crash
- Errors are logged, not shown as crashes

## Test Suite 5: Error Handling

### Test 5.1: Farm Agent unavailable

**What to test:** Graceful error when add-on is down

**Steps:**
1. Stop the Farm Agent add-on (or block port 8080)
2. Ask via Assist: "What is the battery voltage?"

**Expected result:**
```
Farm Agent is not responding
```

**Success criteria:**
- Clean error message
- No timeout/hang
- Home Assistant doesn't crash
- Error is logged

### Test 5.2: OpenAI API error

**What to test:** Graceful error when OpenAI is unavailable

**Steps:**
1. Temporarily set OPENAI_API_KEY to an invalid value
2. Ask a question via Assist

**Expected result:**
- Error message from OpenAI
- Gracefully returned to user
- Home Assistant doesn't crash

**Success criteria:**
- Error is handled
- Doesn't cascade to Home Assistant
- Error is logged

### Test 5.3: Entity not found

**What to test:** Agent handles missing entities gracefully

**Steps:**
1. Ask: "What is the status of sensor.nonexistent?"

**Expected result:**
Agent tries to call Home Assistant API, gets 404, returns:
```
Entity is not available through this tool
```

or similar error message

**Success criteria:**
- Agent doesn't crash
- Returns clear error
- User understands the entity doesn't exist

### Test 5.4: Timeout

**What to test:** Request timeout is handled

**Steps:**
1. Introduce a network delay (use Linux tc command or proxy)
2. Ask a question that takes >30 seconds

**Expected result:**
```
Farm Agent is not responding
```

**Success criteria:**
- Timeout is caught
- Error message is clear
- Home Assistant doesn't hang

## Test Suite 6: Advanced Scenarios

### Test 6.1: Conversation history context

**What to test:** Agent can handle multi-turn conversations

**Steps:**
1. Ask: "What is the battery voltage?"
2. Follow up: "How much is that in percentage?"

**Expected result:**
Agent understands "that" refers to battery voltage from previous question

**Success criteria:**
- Agent understands context
- Answers make sense in conversation flow

### Test 6.2: Unauthorized entity rejection

**What to test:** Agent won't return data for unauthorized entities

**Steps:**
1. Ask: "What is the state of light.bedroom?"

**Expected result:**
Agent returns:
```
Entity is not available through this tool
```

(Because light.bedroom is not in the whitelist)

**Success criteria:**
- Unauthorized entities are blocked
- Returns clear message
- Security is maintained

### Test 6.3: Multiple concurrent requests

**What to test:** Integration handles multiple questions at once

**Steps:**
1. Open multiple conversations or send parallel requests:

```bash
for i in {1..5}; do
  curl -X POST http://localhost:8080/ask \
    -H "Content-Type: application/json" \
    -d '{"question": "What is the battery voltage?"}' &
done
wait
```

**Expected result:**
- All requests complete successfully
- Answers are correct for each
- No crashes or hangs

**Success criteria:**
- Handles concurrency
- All responses are correct
- No race conditions

## Running the Tests

### Automated Tests

Run the test suite:

```bash
cd farm_agent
python -m unittest test_integration.py -v
```

### Manual Test Script

Save as `test_farm_agent.sh`:

```bash
#!/bin/bash

echo "=== Farm Agent Test Suite ==="

echo "1. Testing GET /ask"
curl -s "http://localhost:8080/ask?q=What%20is%20the%20battery%20voltage" | jq .

echo "2. Testing POST /ask"
curl -s -X POST http://localhost:8080/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Is the battery charging?"}' | jq .

echo "3. Testing missing parameter"
curl -s "http://localhost:8080/ask" | jq .

echo "4. Testing conversation.process service"
echo "Go to Developer Tools → Services and test conversation.process"

echo "5. Testing Assist on phone"
echo "Ask your Pixel phone: What is the battery voltage?"

echo "=== Tests complete ==="
```

Run it:
```bash
chmod +x test_farm_agent.sh
./test_farm_agent.sh
```

## Test Results Template

Use this to track test results:

```markdown
# Test Results - [DATE]

## Test Suite 1: HTTP API
- [ ] Test 1.1: GET /ask - PASS / FAIL
- [ ] Test 1.2: POST /ask - PASS / FAIL
- [ ] Test 1.3: Missing parameter - PASS / FAIL
- [ ] Test 1.4: Invalid JSON - PASS / FAIL

## Test Suite 2: HA API
- [ ] Test 2.1: Entity discovery - PASS / FAIL
- [ ] Test 2.2: Entity state - PASS / FAIL
- [ ] Test 2.3: Multiple entities - PASS / FAIL

## Test Suite 3: Integration
- [ ] Test 3.1: Integration appears - PASS / FAIL
- [ ] Test 3.2: Entity created - PASS / FAIL
- [ ] Test 3.3: Reload works - PASS / FAIL

## Test Suite 4: Assist
- [ ] Test 4.1: Farm Agent in settings - PASS / FAIL
- [ ] Test 4.2: conversation.process service - PASS / FAIL
- [ ] Test 4.3: Phone Assist - PASS / FAIL
- [ ] Test 4.4: Different phrasing - PASS / FAIL

## Test Suite 5: Errors
- [ ] Test 5.1: Farm Agent unavailable - PASS / FAIL
- [ ] Test 5.2: OpenAI error - PASS / FAIL
- [ ] Test 5.3: Entity not found - PASS / FAIL
- [ ] Test 5.4: Timeout - PASS / FAIL

## Test Suite 6: Advanced
- [ ] Test 6.1: Conversation history - PASS / FAIL
- [ ] Test 6.2: Entity whitelisting - PASS / FAIL
- [ ] Test 6.3: Concurrent requests - PASS / FAIL

## Summary
Total: 23 tests
Passed: ?
Failed: ?

## Notes
[Any issues or observations]
```

## When Tests Are Complete

Once all tests pass:
1. Update the GitHub repository with the integration
2. Update INSTALLATION.md with any issues found
3. Document any configuration changes
4. Update CHANGELOG with version notes
