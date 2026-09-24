# Architectural Audit - Farm Agent Assist Integration

**Status: UNDER REVIEW - DO NOT DEPLOY**

Critical concerns identified that must be resolved before deployment to remote Home Assistant.

---

## Concern 1: Add-on to Home Assistant Core Communication

### Current Implementation
```python
# conversation.py, line 50
async with session.post(
    "http://localhost:8080/ask",
    ...
)
```

### Problem
**UNVERIFIED ASSUMPTION:** The integration assumes `localhost:8080` works to reach the Farm Agent add-on.

**Reality Check:**
- Home Assistant Core runs in one container
- Farm Agent add-on runs in a separate container
- These containers may NOT have `localhost` refer to the same address
- Home Assistant has a specific internal service discovery mechanism for add-ons
- We don't know if it's:
  - `http://farm_agent:8080`
  - `http://supervisor/addons/farm_agent`
  - Some other mechanism
  - Or if `localhost:8080` actually works (depends on Docker network config)

### Research Needed
- [ ] Home Assistant 2026.9.3 official documentation for add-on-to-core communication
- [ ] Home Assistant Core source code for service discovery
- [ ] How other add-ons communicate with Home Assistant Core
- [ ] Whether there's a supported hostname for add-on containers
- [ ] Docker compose/network setup for Home Assistant

### Implication
If localhost doesn't work, the integration will fail with connection refused. This is a **silent failure** that could leave remote Home Assistant partially broken on first deployment.

---

## Concern 2: Custom Integration Installation Mechanism

### Current Implementation
Integration files exist in the repository at:
```
farm_agent/hass_integration/
  ├── __init__.py
  ├── config_flow.py
  ├── conversation.py
  ├── manifest.json
  └── strings.json
```

### Problem
**HOW DO THESE FILES GET TO HOME ASSISTANT?**

The repository contains the source, but Home Assistant loads integrations from:
```
/config/custom_components/farm_agent/
```

The gap is unspecified:
- Manual copy via SSH? (Not automated, error-prone)
- Add-on copies files at startup? (Would need to be coded in run.sh)
- Some automated installation mechanism?
- Are these files even meant to be in the add-on repository?

### Research Needed
- [ ] Can a Home Assistant add-on repository provide custom integrations?
- [ ] How do users typically install custom integrations?
- [ ] Is there a standard package format (HACS, etc.)?
- [ ] Should this be a separate repository?
- [ ] Should the add-on copy these files to /config at startup?

### Implication
Users won't know how to install the integration. Documentation may be wrong. Integration might need to be distributed separately.

---

## Concern 3: Conversation API for Home Assistant 2026.9.3

### Current Implementation
```python
class FarmAgentConversation(ConversationEntity):
    async def async_process(
        self, user_input: ConversationInput
    ) -> ConversationResult:
```

### Problem
**UNVERIFIED AGAINST 2026.9.3 EXACTLY:**

- Current implementation uses `async_process` method
- Home Assistant may have changed this in 2026.9.3
- The method might be:
  - `async_process` (current guess)
  - `_async_handle_message` (alternative)
  - `async_process_conversation_turn` (old pattern)
  - Something else entirely
- ConversationInput and ConversationResult structure unverified
- Config entry setup pattern may be different

### Research Needed
- [ ] Home Assistant Core 2026.9.3 tag/source code
- [ ] Exact ConversationEntity class definition
- [ ] Exact ConversationInput dataclass
- [ ] Exact ConversationResult dataclass  
- [ ] Correct method signature for 2026.9.3
- [ ] Working examples for 2026.9.3

### Implication
Integration will fail at import time if the API is wrong. This will prevent Home Assistant from starting if the integration is malformed.

---

## Concern 4: Config Flow Naive Storage

### Current Implementation
```python
# config_flow.py, line 25
return self.async_create_entry(
    title="Farm Agent",
    data={"host": "localhost", "port": 8080}
)
```

### Problem
**INCORRECT FOR MULTIPLE REASONS:**

1. **Hardcoded values:** Stores localhost:8080 regardless of actual endpoint
2. **No verification:** Never tests whether the endpoint is reachable
3. **No user input:** User can't override the hostname/port
4. **No auto-discovery:** Doesn't detect the actual add-on address

### Research Needed
- [ ] Can config flow auto-discover the Farm Agent add-on?
- [ ] Should there be a user-selectable endpoint?
- [ ] Should config flow verify connectivity?
- [ ] What does a proper config flow look like for add-on communication?

### Implication
If the endpoint is wrong, the integration stores the wrong address and users can't fix it without recreating the entry.

---

## Concern 5: Port 8080 Exposure

### Current Add-on Configuration
```yaml
# config.yaml
ports:
  8080/tcp: 8080
```

### Problem
**SECURITY UNCLEAR:**

1. **Network exposure:** Does exposing the port make it accessible on:
   - Localhost only? (Safe)
   - Docker bridge network only? (Safe)
   - Host network? (Dangerous)
   - LAN network? (Dangerous)

2. **No authentication:** The /ask endpoint has no authentication

3. **Unverified access control:** We don't know how Home Assistant restricts access to exposed ports

### Research Needed
- [ ] Home Assistant 2026.9.3 port exposure documentation
- [ ] Are exposed ports accessible from the LAN?
- [ ] How to restrict to localhost only?
- [ ] Home Assistant network architecture

### Implication
The Farm Agent /ask endpoint might be accessible to anyone on your LAN without authentication. This is a security risk.

---

## Concern 6: Integration Discovery Without Restart

### Current Documentation Claim
"No restart needed for updates—reload via UI in <5 seconds"

### Problem
**UNVERIFIED:**

1. **First installation:** Documentation says restart is needed
2. **But why?** We don't know if there's an alternative
3. **Reload mechanism:** Is this actually supported in 2026.9.3?
4. **Integration loading:** Can integrations be loaded post-startup?

### Research Needed
- [ ] Home Assistant 2026.9.3 integration loading mechanism
- [ ] Whether reload is actually supported
- [ ] Whether there's a way to load without restart on first install
- [ ] What "reload" actually does

### Implication
Restart might be required when it could be avoided. Or reload might not work and we're claiming it does.

---

## Concern 7: HTTP Endpoint Contract

### Current Implementation
The integration makes HTTP requests:
```python
async with session.post(
    "http://localhost:8080/ask",
    json={"question": question},
    timeout=30,
) as resp:
    if resp.status == 200:
        data = await resp.json()
        answer = data.get("answer", "No answer received")
```

### Requirement
**EXISTING FARM AGENT MUST CONTINUE WORKING:**
```
GET /ask?q=...
POST /ask with {"question": "..."}
```

### Problem
The current Farm Agent application provides both endpoints, so this should be fine. But:

1. **No tests verify** the integration can actually call the endpoint
2. **Error handling is basic** - just returns the error string
3. **Response format assumed** - no schema validation

### Research Needed
- [ ] Add tests that mock the HTTP server
- [ ] Verify conversation entity can call the endpoint
- [ ] Verify response parsing
- [ ] Verify error cases

### Implication
Integration could fail silently or handle responses incorrectly.

---

## Concern 8: Installation Procedure

### Current Documentation
"Copy files to ~/.homeassistant/custom_components/farm_agent/"

### Problem
**RISKY FOR REMOTE DEPLOYMENT:**

1. **Manual process:** Copy files via SSH manually
2. **No automation:** User could make mistakes
3. **No verification:** Can't verify files copied correctly
4. **No rollback:** Can't easily remove if broken
5. **Restart required:** Downtime on remote farm system

### Research Needed
- [ ] Better installation method (HACS? Package?)
- [ ] Automated installation
- [ ] Installation verification
- [ ] Rollback procedure
- [ ] Whether restart can be avoided

### Implication
Deployment to remote Home Assistant is risky. A single mistake could leave the system broken for weeks (until someone visits physically).

---

## Critical Issues Summary

| # | Issue | Severity | Status |
|---|-------|----------|--------|
| 1 | localhost:8080 validity | CRITICAL | Unverified |
| 2 | Integration installation mechanism | CRITICAL | Unspecified |
| 3 | Home Assistant 2026.9.3 API compatibility | CRITICAL | Unverified |
| 4 | Config flow endpoint configuration | HIGH | Naive implementation |
| 5 | Port 8080 security exposure | HIGH | Unclear |
| 6 | Integration reload without restart | HIGH | Unverified |
| 7 | HTTP endpoint testing | MEDIUM | No tests |
| 8 | Safe remote deployment procedure | CRITICAL | Missing |

---

## Required Fixes (In Priority Order)

### Phase 1: Research & Verification
- [ ] Determine correct add-on-to-core communication mechanism for 2026.9.3
- [ ] Verify Conversation API for 2026.9.3 exactly
- [ ] Determine how custom integrations are installed
- [ ] Understand port exposure security model

### Phase 2: Implementation Fixes
- [ ] Update conversation.py to use correct hostname/mechanism
- [ ] Fix config_flow to use detected/configured endpoint
- [ ] Update integration to verify connectivity
- [ ] Add proper tests with mocked HTTP server

### Phase 3: Installation & Deployment
- [ ] Determine proper installation mechanism (not manual copy)
- [ ] Create automated installation procedure
- [ ] Add installation verification steps
- [ ] Document rollback procedure
- [ ] Safe deployment plan (minimize restart, enable rollback)

### Phase 4: Security
- [ ] Verify port 8080 access control
- [ ] Document network security model
- [ ] Add authentication if needed
- [ ] Verify Assist can't accidentally expose credentials

### Phase 5: Testing
- [ ] Integration tests with mocked HTTP
- [ ] Integration tests with actual Farm Agent (local test)
- [ ] Config flow tests
- [ ] Assist pipeline tests
- [ ] Error scenario tests

---

## What We DO NOT Deploy Until

- ✗ All "CRITICAL" issues are resolved
- ✗ Research is complete and verified
- ✗ Implementation is tested
- ✗ Deployment procedure is documented
- ✗ Rollback procedure is documented
- ✗ Security model is verified
- ✗ No localhost assumptions without proof

---

## Next Steps

**DO NOT MODIFY HOME ASSISTANT YET.**

1. Wait for research agent to return findings on:
   - Add-on communication mechanism
   - Integration API for 2026.9.3
   - Installation procedure
   - Security model

2. Review findings and identify gaps

3. Fix implementation based on findings

4. Add proper tests

5. Create safe deployment plan

6. Get approval before any Home Assistant changes

---

## Deployment Hold

🚨 **DO NOT DEPLOY** until all critical issues are resolved and verified.

The remote farm system cannot be left broken for weeks. Every change must be reversible and thoroughly tested first.
