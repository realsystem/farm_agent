# Next Steps - After Hostname Verification

**This document becomes active once hostname research completes.**

---

## Step 1: Record the Verified Hostname

Once research completes, the exact hostname will be determined. Record it here:

```
VERIFIED HOSTNAME: ______________________
SOURCE: ______________________
EVIDENCE: ______________________
CONFIRMATION: YES / NO
```

### What Counts As Verification
- ✅ Home Assistant 2026.9.3 source code reference
- ✅ Official Home Assistant documentation
- ✅ Supervisor source code showing hostname assignment
- ✅ Working example from another add-on integration

### What Does NOT Count
- ❌ Assumptions or guesses
- ❌ "Probably works" statements
- ❌ Older HA version documentation
- ❌ Community discussions without official backing

---

## Step 2: Update Integration Code

### File 1: `farm_agent/hass_integration/conversation.py`

Find line ~50:
```python
async with session.post(
    "http://localhost:8080/ask",  # ← CHANGE THIS
    json={"question": question},
    timeout=30,
) as resp:
```

Replace with:
```python
async with session.post(
    "http://[VERIFIED_HOSTNAME]:8080/ask",  # ← NEW HOSTNAME
    json={"question": question},
    timeout=30,
) as resp:
```

**Options Based on Hostname Type:**

**If Direct Docker Hostname (e.g., `farm_agent` or `farm-agent`):**
```python
# Simple direct connection
async with session.post(
    "http://farm_agent:8080/ask",  # or farm-agent:8080
    json={"question": question},
    timeout=30,
) as resp:
```

**If Supervisor Proxy (e.g., `supervisor/addons/farm_agent/proxy`):**
```python
# Use Supervisor proxy with authentication
import os

supervisor_token = os.environ.get("SUPERVISOR_TOKEN", "")

async with session.post(
    "http://supervisor/addons/farm_agent/proxy/ask",
    headers={
        "X-Supervisor-Token": supervisor_token,
    },
    json={"question": question},
    timeout=30,
) as resp:
```

### File 2: `farm_agent/hass_integration/config_flow.py`

Update endpoint detection:

```python
async def _detect_farm_agent_endpoint(self) -> str | None:
    """Detect Farm Agent add-on endpoint."""
    POSSIBLE_ENDPOINTS = [
        "http://farm_agent:8080",
        "http://farm-agent:8080",
        "http://supervisor/addons/farm_agent/proxy",
    ]
    
    session = async_get_clientsession(self.hass)
    
    for endpoint in POSSIBLE_ENDPOINTS:
        try:
            async with session.post(
                f"{endpoint}/ask",
                json={"question": "ping"},
                timeout=5,
                headers={"X-Supervisor-Token": os.environ.get("SUPERVISOR_TOKEN", "")}
            ) as resp:
                if resp.status in (200, 400, 500):
                    return endpoint
        except:
            continue
    
    return None
```

---

## Step 3: Update Port Binding

### File: `farm_agent/config.yaml`

Find:
```yaml
ports:
  8080/tcp: 8080
```

Change to:
```yaml
ports:
  "127.0.0.1:8080:8080"
```

**Why:** Binds port to localhost only, not accessible from LAN.

---

## Step 4: Add Tests

### Create: `farm_agent/test_hostname_endpoint.py`

```python
"""Tests for the verified hostname endpoint."""
import unittest
from unittest.mock import AsyncMock, patch

class TestEndpointConnectivity(unittest.TestCase):
    
    def test_verified_hostname_is_in_code(self):
        """Verify conversation.py uses the correct hostname."""
        conv_file = Path(__file__).parent / "hass_integration" / "conversation.py"
        content = conv_file.read_text()
        
        # Check for verified hostname
        expected_hostname = "[VERIFIED_HOSTNAME_HERE]"
        self.assertIn(expected_hostname, content,
                     "Verified hostname not found in conversation.py")
    
    def test_localhost_is_removed(self):
        """Verify old localhost reference is removed."""
        conv_file = Path(__file__).parent / "hass_integration" / "conversation.py"
        content = conv_file.read_text()
        
        # localhost:8080 should NOT be in the code anymore
        self.assertNotIn("localhost:8080", content,
                        "Old localhost:8080 still in code!")
```

---

## Step 5: Documentation Updates

### File: `README.md`

Update architecture section:
```markdown
## Network Architecture

Home Assistant Core and Farm Agent add-on communicate via:

**Endpoint:** `http://[VERIFIED_HOSTNAME]:8080/ask`

This is [EXPLAIN: direct Docker communication / Supervisor proxy / other]

**Why:** [EXPLAIN: simplest / most secure / official recommendation]
```

### File: New `HOSTNAME_VERIFIED.md`

Document the verification result:
```markdown
# Hostname Verification Result

**Verified Hostname:** [HOSTNAME]

**Source:** [OFFICIAL SOURCE]

**Evidence:** [CITATION OR LINK]

**Why This Works:**
- [Explanation of mechanism]

**Why Alternatives Don't Work:**
- localhost: Different containers have separate namespaces
- [Other option]: [Why it doesn't work]

**Security Implications:**
- [Any security notes]

**Performance:**
- Typical latency: [measurement if applicable]
```

---

## Step 6: Local Testing Checklist

Once code is updated with verified hostname:

```bash
# 1. Verify syntax
cd farm_agent
python -m py_compile hass_integration/conversation.py
python -m py_compile hass_integration/config_flow.py

# 2. Run tests
python -m unittest test_hass_integration.py -v
python -m unittest test_hostname_endpoint.py -v

# 3. Build add-on
docker build -t farm-agent:local farm_agent/

# 4. Deploy to local Home Assistant
# [Manual steps]

# 5. Test integration
# - Can Home Assistant find the integration?
# - Does config flow work?
# - Can it detect the endpoint?
# - Does Assist work?
```

---

## Step 7: Implementation Decision

Based on verified hostname, decide implementation complexity:

### If Simple Docker Hostname (e.g., `farm_agent:8080`)

**Pros:**
- Simple code change (one line)
- No authentication complexity
- Direct communication

**Cons:**
- Less secure (no token validation)
- Less logging/audit trail

**Implementation Time:** 1 hour

### If Supervisor Proxy (e.g., `supervisor/addons/farm_agent/proxy`)

**Pros:**
- More secure (authenticated)
- Official approach
- Better for logging

**Cons:**
- More complex code
- Requires token handling
- Slightly slower

**Implementation Time:** 2-3 hours

---

## Step 8: Commit and Track Changes

```bash
# After updates are complete:
git add farm_agent/hass_integration/conversation.py
git add farm_agent/hass_integration/config_flow.py
git add farm_agent/config.yaml
git add farm_agent/test_hostname_endpoint.py
git add README.md
git add HOSTNAME_VERIFIED.md

git commit -m "Implement verified hostname for Farm Agent communication

Based on Home Assistant 2026.9.3 official source:
- Hostname: [VERIFIED]
- Source: [CITED]
- Reason: [EXPLAINED]

Changes:
- Updated conversation.py to use correct endpoint
- Updated config_flow.py to detect endpoint
- Updated port binding to localhost only
- Added endpoint connectivity tests
- Updated documentation with verified information

Tests passing: All integration tests
Local testing: Ready to proceed
Security: [Assessment]"

git push origin main
```

---

## Step 9: Local Home Assistant Testing

### Prerequisites
- [ ] Local Home Assistant 2026.9.3+ running
- [ ] Farm Agent add-on already installed and working
- [ ] Files updated with verified hostname

### Test Procedure
- [ ] Copy updated integration to local HA
- [ ] Restart Home Assistant
- [ ] Check Settings → Devices & Services for Farm Agent
- [ ] Create config entry
- [ ] Verify endpoint is detected correctly
- [ ] Ask question via Assist
- [ ] Verify answer is correct
- [ ] Test error cases (Farm Agent offline, timeout, etc.)

---

## Step 10: Ready for Remote Deployment

Once local testing passes completely:

- [ ] All code changes verified
- [ ] All tests passing
- [ ] Hostname confirmed and documented
- [ ] Local HA testing successful
- [ ] Documentation accurate
- [ ] Rollback procedure tested

**Then:** Safe to proceed to HACS installation on remote system

---

## Timeline After Hostname Verification

| Phase | Time | Task |
|-------|------|------|
| Update code | 1-2h | Implement verified hostname |
| Run tests | 30m | Verify everything passes |
| Local test | 2h | Test on local Home Assistant |
| Documentation | 1h | Update docs with findings |
| **Total** | **5h** | Ready for HACS/remote deployment |

---

## Critical Checkpoints

Before proceeding to next phase:

```
Update Code → ✅ Compiles without errors
            → ✅ Tests pass
            
Local Test  → ✅ Integration discovered
            → ✅ Endpoint detected correctly
            → ✅ Questions answered
            → ✅ Rollback works
            
Remote Prep → ✅ All documentation accurate
            → ✅ No false claims about restart
            → ✅ Clear installation steps
            → ✅ Rollback procedure documented
```

**Do not skip any checkpoint.**

---

## If Anything Fails

At any point, if something doesn't work:

1. **Stop** - Do not proceed further
2. **Document** - Record what failed and why
3. **Investigate** - Determine root cause
4. **Fix** - Address the underlying issue
5. **Test** - Verify fix locally
6. **Repeat** - Go back to previous checkpoint

**Do not force-deploy something broken.**

---

## Once Remote Deployment Is Complete

- [ ] Document any issues discovered
- [ ] Monitor logs for errors
- [ ] Test regularly for first week
- [ ] Keep documentation updated
- [ ] Plan for future updates

---

## Questions to Answer Before Proceeding

1. Is the hostname confirmed from official Home Assistant 2026.9.3 source?
2. Have we updated ALL references to the old hostname?
3. Does the code compile without errors?
4. Do all tests pass?
5. Did local Home Assistant testing succeed completely?
6. Is the documentation accurate and clear?
7. Have we tested the rollback procedure?
8. Are we confident about deploying to remote?

**All must be YES before remote deployment.**

---

## This Document Activates When...

Research on the correct hostname is complete and we have a definitive answer from official sources.

Until then, all changes are on hold.

**No guessing. No assumptions. Only facts from official Home Assistant 2026.9.3 documentation.**
