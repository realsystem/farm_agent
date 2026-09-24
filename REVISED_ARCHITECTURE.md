# Farm Agent Assist Integration - Revised Architecture

## Based on Home Assistant 2026.9.3 Reality

---

## Corrected Endpoints

### ❌ WRONG (Current)
```python
"http://localhost:8080/ask"
```

### ✅ CORRECT (Revised)

For add-on-to-add-on communication in Home Assistant:

**Option A: Direct Docker Network (Recommended for simplicity)**
```python
"http://farm_agent:8080/ask"  # Using Docker hostname from add-on slug
```

How it works:
- Docker containers can reach each other using hostname
- Slug "farm_agent" becomes hostname "farm_agent" on Docker network
- No authentication needed (internal docker network)
- Simpler than Supervisor proxy

**Option B: Supervisor API Proxy (Most Secure)**
```
http://supervisor/addons/farm_agent/proxy/ask
```

How it works:
- Supervisor proxies requests to the add-on
- Authenticated with SUPERVISOR_TOKEN (from environment)
- Works through supervisor's network isolation
- Most compliant with Home Assistant architecture

**Option C: Ingress (If Farm Agent Becomes Web App)**
```
http://localhost:8099  # (Supervisor ingress endpoint)
```

How it works:
- Use Supervisor Ingress instead of direct port exposure
- Authentication handled by Home Assistant
- No port exposed to network

### RECOMMENDATION
**Option A (Docker hostname)** for MVP:
- Simplest to implement
- Farm Agent add-on listens on 8080 internally (no LAN exposure)
- Conversation integration uses `http://farm_agent:8080/ask`
- Both containers on same Docker network (guaranteed by Supervisor)

**Migrate to Option B (Supervisor proxy)** later if needed for:
- Better security isolation
- Explicit authentication logging
- Future multi-add-on deployments

---

## Network Architecture (CORRECTED)

```
┌─────────────────────────────────────┐
│ Home Assistant Host (Raspberry Pi)  │
├─────────────────────────────────────┤
│                                     │
│  ┌──────────────────────────────┐   │
│  │ Home Assistant Core          │   │
│  │ (Container)                  │   │
│  │                              │   │
│  │ Custom Integration:          │   │
│  │ POST http://farm_agent:8080  │   │
│  └──────────────────────────────┘   │
│            │                         │
│            │ Docker Network          │
│            │ (Internal, isolated)    │
│            ↓                         │
│  ┌──────────────────────────────┐   │
│  │ Farm Agent Add-on            │   │
│  │ (Container)                  │   │
│  │                              │   │
│  │ Port 8080                    │   │
│  │ (Bound to localhost only ✓)  │   │
│  │                              │   │
│  │ HTTP Server:                 │   │
│  │ GET  /ask?q=...              │   │
│  │ POST /ask {question}         │   │
│  └──────────────────────────────┘   │
│                                     │
│  NOT ACCESSIBLE FROM LAN ✓          │
│  (Only Home Assistant can reach)    │
│                                     │
└─────────────────────────────────────┘

Pixel Phone
(connected to farm network)
  ↓
Home Assistant Assist App
  ↓
Home Assistant Core (already authenticated)
  ↓
Conversation Integration (local to HA)
  ↓
Docker Network (internal)
  ↓
Farm Agent (listening internally only)
```

---

## Implementation Changes Required

### 1. Fix conversation.py

**Change Line 50:**
```python
# FROM:
async with session.post(
    "http://localhost:8080/ask",
    ...

# TO:
async with session.post(
    "http://farm_agent:8080/ask",
    ...
```

**Alternative (Supervisor proxy method):**
```python
# More secure but more complex:
supervisor_token = os.environ.get("SUPERVISOR_TOKEN", "")
async with session.post(
    "http://supervisor/addons/farm_agent/proxy/ask",
    headers={
        "X-Supervisor-Token": supervisor_token
    },
    json={"question": question},
    timeout=30,
) as resp:
    ...
```

### 2. Fix config_flow.py

**Change from hardcoded values:**
```python
# FROM (WRONG):
data={"host": "localhost", "port": 8080}

# TO (BETTER):
# Auto-detect or verify endpoint
endpoint_url = self._detect_farm_agent_endpoint()
if not endpoint_url:
    return self.async_abort(reason="farm_agent_not_found")

data={"endpoint": endpoint_url}
```

**Detect Farm Agent function:**
```python
async def _detect_farm_agent_endpoint(self) -> str | None:
    """Detect Farm Agent add-on endpoint."""
    # Try Docker hostname first (simplest)
    try:
        session = async_get_clientsession(self.hass)
        async with session.post(
            "http://farm_agent:8080/ask",
            json={"question": "ping"},
            timeout=5,
        ) as resp:
            if resp.status in (200, 400, 500):  # Any response = reachable
                return "http://farm_agent:8080"
    except:
        pass
    
    return None
```

### 3. Fix Port Binding

**Update config.yaml:**

```yaml
# FROM (WRONG - exposes to LAN):
ports:
  8080/tcp: 8080

# TO (CORRECT - localhost only):
ports:
  "127.0.0.1:8080:8080"

# OR switch to Ingress:
ingress: true
```

**Explanation:**
- `"127.0.0.1:8080:8080"` binds port 8080 to localhost ONLY
- Not accessible from network
- Only Home Assistant Core can reach it
- More secure by default

### 4. Update __init__.py

Store the detected endpoint:

```python
async def async_setup_entry(hass, entry):
    """Set up Farm Agent from config entry."""
    hass.data.setdefault(DOMAIN, {})
    
    # Store endpoint URL from config
    endpoint = entry.data.get("endpoint", "http://farm_agent:8080")
    hass.data[DOMAIN][entry.entry_id] = {
        "endpoint": endpoint,
        "entry": entry
    }

    await hass.config_entries.async_forward_entry_setups(entry, ["conversation"])
    return True
```

Then use it in conversation.py:

```python
async def async_process(self, user_input):
    endpoint = self.hass.data[DOMAIN][self.config_entry.entry_id]["endpoint"]
    
    async with session.post(
        f"{endpoint}/ask",
        json={"question": user_input.text},
        ...
    )
```

---

## Installation Architecture (CORRECTED)

### NOT: Manual file copy (error-prone)
### YES: HACS-based installation (automated, safe)

```
User's Home Assistant
        ↓
Settings → Devices & Services → HACS (↓ Browse)
        ↓
Search: "Farm Agent"
        ↓
Repository: realsystem/farm_agent
        ↓
Install Integration
        ↓
HACS copies to: /config/custom_components/farm_agent/
        ↓
Home Assistant discovers integration
        ↓
Restart Home Assistant (unavoidable first time)
        ↓
Settings → Devices & Services → Farm Agent
        ↓
Create Integration Entry
```

### Required: Separate GitHub Repository

The integration needs its own repository:

```
https://github.com/realsystem/farm-agent-integration/

├── custom_components/
│   └── farm_agent/
│       ├── __init__.py
│       ├── config_flow.py
│       ├── conversation.py
│       ├── manifest.json
│       └── strings.json
├── tests/
├── README.md
├── hacs.json
└── LICENSE
```

HACS integration repository structure:

```json
// hacs.json
{
  "name": "Farm Agent Conversation Integration",
  "homeassistant": "2026.9.0",
  "domains": ["conversation"],
  "requirements": [],
  "codeowners": ["@realsystem"]
}
```

---

## Conversation API: Use Modern Pattern

### Current (Works, but deprecated)
```python
async def async_process(self, user_input: ConversationInput) -> ConversationResult:
    ...
```

### Recommended (2026.9.3+ standard)
```python
async def _async_handle_message(
    self,
    user_input: ConversationInput,
    chat_log: ChatLog
) -> ConversationResult:
    """Handle a message with conversation history context."""
    # Can access chat_log.messages for conversation history
    # Can add messages/tools to chat_log
    # Returns ConversationResult
    ...
```

### Upgrade Steps
1. Keep `async_process` for compatibility
2. Add `_async_handle_message` implementation
3. Use ChatLog for better context
4. Test with Home Assistant 2026.9.3

---

## Deployment Procedure (SAFE)

### Phase 0: Before Any Changes
- [ ] Farm Agent add-on is already installed and working
- [ ] Testing on a LOCAL Home Assistant instance (not remote yet)

### Phase 1: Prepare Integration Repository
- [ ] Create separate GitHub repo for integration
- [ ] Structure files as /custom_components/farm_agent/
- [ ] Update conversation.py to use `http://farm_agent:8080`
- [ ] Update config_flow.py to auto-detect endpoint
- [ ] Add comprehensive tests
- [ ] Create HACS structure (hacs.json, readme)

### Phase 2: Register with HACS
- [ ] Add repository to HACS (settings)
- [ ] Test installation on local Home Assistant
- [ ] Verify Assist pipeline works
- [ ] Verify rollback works (remove integration, restart)

### Phase 3: Update Farm Agent Add-on
- [ ] Update config.yaml port binding: `"127.0.0.1:8080:8080"`
- [ ] Rebuild add-on image
- [ ] Test on local Home Assistant

### Phase 4: Deploy to Remote
- [ ] User adds HACS repository
- [ ] User installs "Farm Agent Integration" via HACS
- [ ] HACS automatically places files in /config/custom_components/
- [ ] User restarts Home Assistant (unavoidable first install)
- [ ] User configures Assist pipeline
- [ ] Test question to Farm Agent

### Phase 5: If Anything Fails
- [ ] Remove /config/custom_components/farm_agent/
- [ ] Restart Home Assistant
- [ ] System recovers to previous state
- [ ] No physical intervention needed

---

## Testing Required (Before Deployment)

### Unit Tests
- [ ] Config flow endpoint detection
- [ ] Conversation entity message handling
- [ ] Error handling (timeout, connection refused, malformed response)
- [ ] No credentials leaked in logs

### Integration Tests (on local Home Assistant)
- [ ] Integration appears in Settings
- [ ] Config entry created successfully
- [ ] Endpoint verified and stored correctly
- [ ] Conversation service can process requests

### End-to-End Tests
- [ ] Farm Agent add-on listening
- [ ] Integration can reach endpoint
- [ ] Question → Answer flow works
- [ ] Assist pipeline routes correctly
- [ ] Rollback removes all files

---

## Rollback Procedure

**If integration installation fails:**

1. SSH to Home Assistant (if possible):
   ```bash
   rm -rf /config/custom_components/farm_agent/
   ```

2. Restart Home Assistant via UI or command

3. Integration is completely removed

4. Farm Agent add-on continues working

5. Can retry after fixing the issue

**If config entry can't be removed:**
1. Edit `/config/.storage/core.config_entries`
2. Remove the farm_agent entry
3. Restart

**If still broken:**
1. Create backup snapshot in HA UI
2. Remove custom_components/farm_agent/ directory
3. Restart
4. Should recover

---

## Security Model (CORRECTED)

### Port Binding
- Port 8080 is bound to `127.0.0.1` ONLY
- NOT accessible from network
- Only Home Assistant Core can reach it
- Safe by default

### Authentication
- Farm Agent and Integration on same Docker network
- Internal communication only
- No need for API key between them
- OpenAI key stays in Farm Agent only
- Supervisor token stays in Farm Agent only

### Attack Vectors Mitigated
- ✅ LAN doesn't have access to /ask endpoint
- ✅ Credentials don't leave Farm Agent
- ✅ Home Assistant can't access OpenAI API directly
- ✅ Integration can't access Supervisor token

---

## Startup Sequence (CORRECTED)

```
1. Supervisor starts Docker containers
   
2. Home Assistant Core container starts
   ├─ Loads built-in components
   ├─ Scans /config/custom_components/
   ├─ Loads farm_agent custom component
   └─ Creates conversation entity

3. Farm Agent add-on container starts
   ├─ Loads OPENAI_API_KEY from config
   ├─ Loads SUPERVISOR_TOKEN from environment
   └─ Starts HTTP server on localhost:8080

4. Integration initialization
   ├─ Config flow runs (or loads existing entry)
   ├─ Detects Farm Agent endpoint
   ├─ Conversation entity is registered
   └─ Assist can now use it

5. User asks question in Assist
   ├─ Assist calls conversation.process()
   ├─ Integration makes POST to http://farm_agent:8080/ask
   ├─ Farm Agent receives and processes question
   ├─ Returns answer via JSON
   ├─ Integration returns to Assist
   └─ Assist displays/speaks answer
```

---

## Comparison: Current vs. Corrected

| Aspect | Current ❌ | Corrected ✅ |
|--------|----------|------------|
| Endpoint | localhost:8080 | farm_agent:8080 (Docker hostname) |
| Connection | Won't work | Works reliably |
| Config | Hardcoded values | Auto-detected & verified |
| Port security | LAN-accessible | Localhost only |
| Installation | Manual copy | HACS automated |
| Rollback | Complex | Simple (delete folder, restart) |
| Testing | Basic | Comprehensive |
| Documentation | Misleading | Accurate |
| First restart | Required, not mentioned | Required, documented |

---

## Timeline for Fixes

### Immediate (Blocking deployment)
1. Change endpoint from localhost to farm_agent (1 hour)
2. Fix config_flow to auto-detect (2 hours)
3. Update port binding to localhost only (30 mins)
4. Create tests for new endpoint (2 hours)

**Subtotal: ~5.5 hours**

### Short-term (Before remote deployment)
5. Create separate HACS repository (2 hours)
6. Test on local Home Assistant (2 hours)
7. Document HACS installation (1 hour)
8. Update all documentation (2 hours)

**Subtotal: ~7 hours**

### Medium-term (Nice to have)
9. Modernize to `_async_handle_message` pattern (3 hours)
10. Add config entry migration if needed (2 hours)
11. Add comprehensive error recovery (2 hours)

**Subtotal: ~7 hours**

---

## Commitment Before Any Remote Deployment

✅ All CRITICAL fixes complete
✅ Tested on local Home Assistant
✅ HACS repository functional
✅ Rollback procedure documented
✅ Security model verified
✅ No localhost assumptions
✅ Endpoints tested and working
✅ Documentation accurate (no false claims about restarts)

**ONLY THEN:** Safe to deploy to remote farm system

---

## NEXT STEPS (DO NOT DEPLOY YET)

1. [ ] Acknowledge this revised architecture
2. [ ] Approve Docker hostname approach (or choose alternative)
3. [ ] Begin implementation of fixes
4. [ ] Create HACS repository structure
5. [ ] Test on local Home Assistant
6. [ ] Verify all fixes work
7. [ ] Get approval before remote deployment

**Keep the remote farm system safe. Every step must be reversible.**
