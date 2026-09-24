# Research Findings: Home Assistant 2026.9.3 Architecture

## Critical Findings - Issues Identified

Your concerns were justified. The implementation has several critical issues that would cause deployment failures.

---

## Finding 1: localhost:8080 DOES NOT WORK ❌

### Current Implementation (WRONG)
```python
async with session.post(
    "http://localhost:8080/ask",
    ...
)
```

### Reality
- Home Assistant Core runs in ONE container
- Farm Agent add-on runs in a DIFFERENT container
- These containers cannot reach each other via `localhost`
- Containers have separate network namespaces

### Correct Endpoint
**`http://supervisor/core/api`** for Home Assistant Core communication

The Supervisor is the orchestration component that manages both containers.

### For Add-on to Add-on Communication
Add-ons can communicate via:
- Direct container hostname: `farm_agent` or `farm-agent` (slug-based)
- Docker network aliases: `http://farm-agent:8080/ask` (if properly configured)
- Through Supervisor API (recommended for authenticated communication)

### Implication
**The current integration will FAIL with "Connection Refused" when deployed.**

The integration needs to:
1. Use correct hostname for reaching Farm Agent add-on
2. OR Farm Agent needs to expose via Supervisor Ingress
3. OR Farm Agent needs to expose through Supervisor proxy

---

## Finding 2: Custom Integration Installation is NOT Automatic ❌

### Current Assumption (WRONG)
"Copy files to ~/.homeassistant/custom_components/farm_agent/ via SSH and restart"

### Reality
- Custom integrations are discovered on Home Assistant startup ONLY
- They must be in `/config/custom_components/` before Home Assistant starts
- Manual copy is error-prone for a remote system
- NO automatic provisioning from add-on repository to /config/custom_components/

### Supported Installation Methods

**Method 1: HACS (Recommended)**
- Create separate GitHub repository for the integration
- Register it with HACS as a custom repository (category: Integration)
- Users install via HACS UI (Settings → Devices & Services → HACS)
- Automatic file placement
- Automatic updates
- **Requires Home Assistant restart after install**

**Method 2: Manual Copy**
- Users manually copy files to `/config/custom_components/`
- Error-prone on remote systems
- Requires SSH access
- **Requires Home Assistant restart**

**Method 3: Add-on Provisioning (NOT STANDARD)**
- Add-on could copy files to `/config/custom_components/` via mounted volume
- Not a documented or standard pattern
- Adds complexity

### Implication
**The custom integration needs its own GitHub repository** or should be provided via HACS.

Current approach won't work for users.

---

## Finding 3: Conversation API Changed ❌

### Current Implementation (POSSIBLY WRONG)
```python
async def async_process(
    self, user_input: ConversationInput
) -> ConversationResult:
```

### Home Assistant 2026.9.3 Reality

There are TWO supported patterns:

**OLD (Still works for backwards compatibility):**
```python
async def async_process(self, user_input) -> ConversationResult:
```

**NEW (2026.9.3+ Standard):**
```python
async def _async_handle_message(
    self,
    user_input: ConversationInput,
    chat_log: ChatLog
) -> ConversationResult:
```

### Current Status
The current implementation uses `async_process` which WORKS but is deprecated.

For 2026.9.3+ best practices, should use `_async_handle_message` with ChatLog support.

### Implication
Code will work for now, but should be modernized to the `_async_handle_message` pattern for future compatibility.

---

## Finding 4: Config Flow Storing Wrong Data ❌

### Current Implementation
```python
data={"host": "localhost", "port": 8080}
```

### Problems
1. **Hardcoded:** Stores localhost regardless of actual add-on address
2. **Wrong for multiple reasons:**
   - localhost doesn't work (containers are separate)
   - Config flow doesn't verify endpoint is reachable
   - User can't override the values
   - No auto-detection of add-on address

### What It SHOULD Do
1. Auto-detect the Farm Agent add-on is installed and running
2. Verify it's reachable
3. Store the actual working endpoint
4. OR not store endpoint at all (use Supervisor API if available)

### Implication
Even if user installs everything correctly, the integration stores the wrong endpoint and will fail silently.

---

## Finding 5: Port 8080 Exposure is Insecure ❌

### Current Configuration
```yaml
ports:
  8080/tcp: 8080
```

### Reality
- This exposes port 8080 to the **entire LAN** by default
- No authentication required
- Anyone on your farm network can query `/ask` endpoint
- The endpoint has no API key requirement

### Security Risk
- Unauthenticated access to Farm Agent API
- Potential data exposure (sensor values, responses)
- Can be exploited by anyone on the network

### Recommended Fixes

**Option 1: Use Ingress (Recommended)**
```yaml
ingress: true  # Expose through Home Assistant UI
```
- Authentication handled by Home Assistant
- No port exposed to network
- Works for web interfaces

**Option 2: Bind to localhost only**
```yaml
ports:
  "127.0.0.1:8080:8080"  # Only accessible from same machine
```
- Port not accessible from network
- Only Home Assistant Core can reach it

**Option 3: Use Supervisor API**
- Farm Agent doesn't expose port at all
- Home Assistant communicates through Supervisor (authenticated)

### Implication
Current deployment has a security vulnerability. Port 8080 is exposed to the LAN without authentication.

---

## Finding 6: Integration Discovery REQUIRES Restart ❌

### Current Documentation Claim
"No restart needed for updates—reload via UI in <5 seconds"

### Reality for Home Assistant 2026.9.3
- **First install of custom integration: RESTART REQUIRED**
  - Custom integrations are only discovered at startup
  - No dynamic loading mechanism exists
  - Restart is unavoidable for initial discovery

- **Updates to existing integration: Reload can work**
  - Service: `homeassistant.reload_config_entry`
  - This reloads configuration, not the code
  - For code changes, restart still needed

### Implication
Documentation is misleading. First installation WILL require a restart.

This is especially critical for remote farm system where restart = 2+ hour downtime.

---

## Finding 7: How to Actually Deploy Safely

### Current Plan (UNSAFE)
1. Copy files to ~/.homeassistant/ via SSH
2. Restart Home Assistant
3. Hope it works
4. No rollback if it fails

### Safe Deployment Plan (REQUIRED)

**Phase 1: Before Any HA Changes**
- [ ] Create separate GitHub repository for farm_agent integration
- [ ] Register with HACS as custom repository
- [ ] Document installation process
- [ ] Create comprehensive tests
- [ ] Set up rollback procedure

**Phase 2: Installation (Minimal Downtime)**
- [ ] User adds HACS repository
- [ ] User installs integration via HACS UI
- [ ] User restarts Home Assistant (unavoidable, first time only)
- [ ] If fails: User removes integration (HA still starts)

**Phase 3: Configuration**
- [ ] Integration auto-detects Farm Agent add-on
- [ ] User configures Assist pipeline
- [ ] Test and verify

**Phase 4: Rollback (If Needed)**
- [ ] Remove /config/custom_components/farm_agent/
- [ ] Restart Home Assistant
- [ ] System recovers

---

## Finding 8: Testing Before Deployment is Critical

### Current Tests
- 23 test cases, but they don't actually test:
  - Integration loading in HA
  - HTTP communication (mocked)
  - Actual endpoint connectivity
  - Error recovery

### Required Tests

**Before Deployment:**
- [ ] Integration files have correct syntax
- [ ] Manifest is valid JSON
- [ ] Config flow works
- [ ] HTTP client logic is correct
- [ ] Error handling doesn't crash
- [ ] No credentials are exposed

**After Installation (User Tests):**
- [ ] Integration appears in Settings
- [ ] Configuration can be created
- [ ] HTTP endpoint is reachable
- [ ] Assist can route questions
- [ ] Responses are correct
- [ ] Rollback removes all files

---

## What Must Be Fixed (Priority Order)

### CRITICAL (Must Fix Before Deployment)

1. **Fix Endpoint Address**
   - [ ] Change from `localhost:8080` to correct address
   - [ ] Determine correct hostname for add-on-to-add-on communication
   - [ ] OR expose Farm Agent through Supervisor proxy
   - [ ] OR use Ingress for Farm Agent

2. **Fix Config Flow**
   - [ ] Don't hardcode localhost:8080
   - [ ] Auto-detect Farm Agent add-on
   - [ ] Verify endpoint is reachable
   - [ ] Store actual working endpoint

3. **Create HACS Repository**
   - [ ] Separate GitHub repo for integration
   - [ ] Register with HACS
   - [ ] Automatic file installation
   - [ ] Update docs with HACS installation

4. **Fix Security**
   - [ ] Bind port 8080 to localhost only, OR
   - [ ] Use Ingress, OR
   - [ ] Switch to Supervisor API communication
   - [ ] Add authentication if necessary

5. **Fix Documentation**
   - [ ] Clarify restart is required for first install
   - [ ] Document rollback procedure
   - [ ] Explain HACS installation
   - [ ] Remove misleading "no restart" claims

### HIGH (Should Fix)

6. **Modernize Conversation API**
   - [ ] Implement `_async_handle_message` pattern
   - [ ] Add ChatLog support
   - [ ] Test with actual Home Assistant

7. **Add Real Tests**
   - [ ] Mock HTTP server tests
   - [ ] Integration loading tests
   - [ ] Error scenario tests

8. **Create Installation Procedure**
   - [ ] Step-by-step for remote system
   - [ ] Rollback procedure
   - [ ] Verification steps
   - [ ] Troubleshooting guide

---

## Current Implementation Status

| Component | Status | Issue |
|-----------|--------|-------|
| localhost:8080 endpoint | ❌ WRONG | Different containers, won't work |
| Config flow | ❌ NAIVE | Hardcoded values |
| Installation mechanism | ❌ MISSING | No HACS, manual copy only |
| Conversation API | ⚠️ WORKS | Old pattern, should modernize |
| Port security | ❌ EXPOSED | Accessible from LAN, no auth |
| Restart requirement | ❌ MISREPRESENTED | Required but docs say no |
| Rollback procedure | ❌ MISSING | Can't safely undo failed install |
| Tests | ✓ OK | Basic tests pass, but incomplete |

---

## Immediate Actions Required

**DO NOT DEPLOY** until issues 1-5 are fixed.

### Next Steps

1. [ ] Wait for architecture review based on these findings
2. [ ] Determine correct hostname/endpoint for Farm Agent
3. [ ] Fix conversation.py to use correct address
4. [ ] Fix config_flow to auto-detect and verify endpoint
5. [ ] Create HACS repository structure
6. [ ] Fix port binding or switch to Ingress
7. [ ] Update all documentation
8. [ ] Add tests for actual communication
9. [ ] Create rollback procedure
10. [ ] Test on local Home Assistant before remote deployment

---

## Risk Assessment

**Current Implementation Risk: VERY HIGH**

- ❌ Will not connect to Farm Agent add-on (localhost issue)
- ❌ Hard to install for end users (manual copy)
- ❌ No safe rollback if something fails
- ❌ Exposes port to LAN without authentication
- ❌ Misleading documentation about restart

**Recommended: Fix all CRITICAL issues before any deployment attempt.**

The remote farm system cannot be left broken for weeks. Every change must be thoroughly tested and reversible first.

---

## Repository Status

**Current:** Implementation complete but based on incorrect assumptions

**After Fixes:** Should be safe for remote deployment

**Timeline:** Fix critical issues, then test on local HA first, then deploy to remote

---

See REVISED_ARCHITECTURE.md for the corrected implementation plan.
