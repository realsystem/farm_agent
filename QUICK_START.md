# Quick Start: 5 Minutes to Farm Agent on Assist

## Prerequisites

- ✓ Home Assistant 2026.9.3 (or later)
- ✓ Farm Agent add-on already installed and running
- ✓ SSH access to your Home Assistant machine
- ✓ `openai_api_key` configured in Farm Agent add-on settings

## Installation

### Step 1: Copy Integration Files (1 minute)

SSH into your Home Assistant machine:

```bash
ssh homeassistant@<YOUR_HA_IP>
mkdir -p ~/.homeassistant/custom_components/farm_agent
```

Download/clone the repository, then copy the 5 integration files:

```bash
cd farm_agent
cp -r farm_agent/hass_integration/* ~/.homeassistant/custom_components/farm_agent/
```

Verify:
```bash
ls -la ~/.homeassistant/custom_components/farm_agent/
```

Should show: `__init__.py`, `config_flow.py`, `conversation.py`, `manifest.json`, `strings.json`

### Step 2: Restart Home Assistant (5 minutes)

Go to Home Assistant Settings → System → Restart Home Assistant

*The restart is required one time only to discover the integration.*

### Step 3: Create Integration (1 minute)

After Home Assistant restarts:

1. Settings → Devices & Services
2. Look for "Farm Agent" in the list
3. Click "Create Integration"
4. Follow the wizard (just click next, default settings work)

### Step 4: Configure Assist (1 minute)

1. Settings → Voice Assistants
2. Find the pipeline you use (or create one)
3. Under "Conversation Agent", select "Farm Agent"
4. Save

### Step 5: Test (1 minute)

Ask your Pixel phone (in the HA app):

> *"What is the battery voltage?"*

Expected response:

> *"The battery voltage is currently 48.2 volts"*

---

## Done! 🎉

You can now ask Assist questions about your farm.

---

## Test Variations

Try these questions:

- "What is the battery voltage?"
- "Is the farm battery charging?"
- "What is the current?"
- "Tell me about the battery status"
- "How much power is being generated?"

---

## If Something Doesn't Work

### Check 1: Is the add-on running?

Home Assistant UI → Settings → Add-ons → Farm Agent → Check status

Look for: "Listening on port 8080"

### Check 2: Is the integration installed?

Settings → Devices & Services → Search for "Farm Agent"

Should appear in the list.

### Check 3: Test the add-on directly

SSH into Home Assistant:

```bash
curl -X POST http://farm-agent:8080/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the battery voltage?"}'
```

Should return:
```json
{"answer": "The battery voltage is 48.2V"}
```

If this fails, the add-on has an issue. Check:
- Add-on logs (Settings → Add-ons → Farm Agent → Logs)
- Is `openai_api_key` set?
- Can Home Assistant reach the sensors?

### Check 3: Check Home Assistant logs

Settings → System → Logs

Search for "farm_agent"

Should see messages like:
- `Setting up Farm Agent integration`
- `Setting up Farm Agent conversation entity`

If you see errors, post them to: https://github.com/realsystem/farm_agent/issues

---

## Detailed Documentation

- [Full Installation Guide](INSTALLATION.md) — 3 installation methods, troubleshooting
- [Test Plan](TESTING.md) — 23 test cases to verify everything works
- [Architecture](IMPLEMENTATION_SUMMARY.md) — How everything fits together
- [README](README.md) — Overview and features

---

## What You Just Installed

- **Farm Agent add-on:** Already running, queries OpenAI and Home Assistant
- **Custom Integration:** Routes Assist questions to Farm Agent
- **5 files:** ~160 lines of production-ready code
- **No configuration:** Works with default settings
- **No restart needed after first time:** Future updates reload without restart

---

## Performance

Typical question-to-answer time: **3-5 seconds**

Breakdown:
- 0.2s — HTTP to Farm Agent
- 0.1s — Query Home Assistant sensors  
- 2-4s — OpenAI API call (language model thinking)
- 0.1s — Format and return answer

---

## Next Steps

### Now That It's Working:

1. Ask it various farm-related questions
2. Check the logs if you want to see what's happening
3. Adjust sensor whitelist if you want (see INSTALLATION.md)

### Coming Soon (Optional):

- Set up Home Assistant automations based on Farm Agent responses
- Create custom Assist voices
- Expand sensor monitoring beyond farm sensors

---

## Support

**Docs:** Start with [INSTALLATION.md](INSTALLATION.md)

**Issues:** https://github.com/realsystem/farm_agent/issues

**Questions:**
1. Check the logs (Settings → System → Logs)
2. Test the add-on directly (curl command above)
3. Verify Farm Agent is in Assist settings

---

## Summary

| Step | Time | Action |
|------|------|--------|
| 1 | 1m | Copy 5 integration files |
| 2 | 5m | Restart Home Assistant |
| 3 | 1m | Create integration in Settings |
| 4 | 1m | Select Farm Agent in Assist |
| 5 | 1m | Test on your phone |
| **Total** | **~9m** | Done! |

That's it. You now have AI-powered Assist for your farm! 🚜🤖

---

For detailed guides, see the other documentation files in this directory.
