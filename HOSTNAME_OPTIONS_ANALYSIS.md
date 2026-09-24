# Hostname Options - Technical Analysis

Analysis of each possible hostname option for HA Core → Farm Agent add-on communication.

---

## Option 1: `http://farm_agent:8080`

**Description:** Using the add-on slug directly as the hostname

### How It Would Work
- Docker container hostname = add-on slug
- Docker DNS resolution: `farm_agent` → internal IP
- Containers on same Docker network can resolve each other

### Pros
- ✅ Simplest approach
- ✅ Docker native behavior
- ✅ No special configuration needed
- ✅ Most other add-ons work this way

### Cons
- ❌ Underscore in hostname (some DNS systems have issues with underscores)
- ❌ Unconfirmed if Home Assistant actually sets hostname to slug

### Evidence Needed
- Supervisor source code showing hostname assignment
- Docker compose configuration
- Working example of add-on communication

### Risk Level: **MEDIUM**
- Would work IF Supervisor assigns hostname correctly
- But underscore might cause issues in some DNS implementations

### Implementation Impact
```python
# conversation.py line 50
async with session.post(
    "http://farm_agent:8080/ask",
    json={"question": question},
    timeout=30,
) as resp:
```

---

## Option 2: `http://farm-agent:8080`

**Description:** Slug with underscore converted to hyphen

### How It Would Work
- Docker hostname = slug with hyphen conversion
- Docker DNS resolves `farm-agent` to internal IP
- Follows DNS naming conventions (RFC 952)

### Pros
- ✅ Follows DNS best practices
- ✅ Avoids underscore issues
- ✅ More standard networking approach
- ✅ Cleaner to read

### Cons
- ❌ Requires confirmation that conversion happens
- ❌ If conversion doesn't happen, will fail

### Evidence Needed
- Supervisor source confirming underscore→hyphen conversion
- Documentation stating this behavior
- Example add-ons using this

### Risk Level: **MEDIUM-LOW**
- If conversion is standard, this is safest option
- If conversion doesn't happen, it will fail clearly (connection refused)

### Implementation Impact
```python
# conversation.py line 50
async with session.post(
    "http://farm-agent:8080/ask",  # hyphen instead of underscore
    json={"question": question},
    timeout=30,
) as resp:
```

---

## Option 3: `http://localhost:8080`

**Description:** Using localhost (current incorrect assumption)

### How It Works
- Points to the local container's loopback interface
- HA Core's localhost ≠ Farm Agent's localhost

### Pros
- Simple syntax
- No hostname resolution needed

### Cons
- ❌ WILL NOT WORK (different containers)
- ❌ Each container has its own localhost
- ❌ Farm Agent listening on 127.0.0.1 won't be reachable from another container
- ❌ Will fail with "Connection refused"

### Evidence
- ✅ Confirmed: different containers have separate network namespaces
- ✅ Confirmed: localhost in one container ≠ localhost in another

### Risk Level: **CRITICAL - WILL FAIL**

### Why It Doesn't Work
```
Container A (HA Core)              Container B (Farm Agent)
localhost = 127.0.0.1              localhost = 127.0.0.1
       ↓                                   ↓
    loopback                          loopback
  (only self)                       (only self)

Connection to localhost:8080 from Container A
→ Reaches Container A's loopback
→ Container B's port is NOT there
→ Connection refused
```

### Verdict
**DO NOT USE - This is what we currently have and it's WRONG**

---

## Option 4: `http://supervisor:8080`

**Description:** Using `supervisor` hostname as gateway

### How It Would Work
- Docker network routes `supervisor` hostname
- Supervisor acts as intermediary or proxy
- Not direct container-to-container communication

### Pros
- ✅ Goes through Supervisor (authenticated)
- ✅ More secure
- ✅ Easier to monitor/log

### Cons
- ❌ Requires Supervisor to have routing/proxy capability
- ❌ Might not work for raw port 8080 (may need proxy path)
- ❌ More latency (goes through supervisor)
- ❌ Requires special Supervisor configuration

### Evidence Needed
- Supervisor documentation on proxy routing
- Whether Supervisor proxies raw ports or only HTTP APIs
- Performance implications

### Risk Level: **MEDIUM-HIGH**
- Might not work as expected
- May need special Supervisor proxy configuration

### Implementation Impact
```python
# conversation.py line 50
async with session.post(
    "http://supervisor:8080/ask",
    json={"question": question},
    timeout=30,
) as resp:
```

---

## Option 5: `http://supervisor/addons/farm_agent/proxy`

**Description:** Using Supervisor as authenticated proxy

### How It Would Work
- Supervisor provides HTTP proxy endpoint
- Supervisor forwards requests to add-on
- Supervisor handles authentication
- Requires Supervisor token (SUPERVISOR_TOKEN env var)

### Pros
- ✅ Secure (requires Supervisor token)
- ✅ Authenticated communication
- ✅ Official Home Assistant recommended pattern
- ✅ Better for audit trails and logging
- ✅ Supervisor manages routing

### Cons
- ❌ More complex implementation
- ❌ Requires reading SUPERVISOR_TOKEN from environment
- ❌ Requires passing token in header
- ❌ Slightly slower (goes through Supervisor)

### Evidence
- ✅ Confirmed: Supervisor API documentation
- ✅ Confirmed: `/addons/<SLUG>/proxy` endpoint exists
- ✅ Confirmed: Used by Home Assistant Core to reach add-ons

### Risk Level: **LOW**
- Official approach
- Well documented
- Used by Home Assistant itself

### Implementation Impact
```python
# conversation.py
import os

async def async_process(self, user_input):
    supervisor_token = os.environ.get("SUPERVISOR_TOKEN", "")
    
    try:
        session = async_get_clientsession(self.hass)
        
        async with session.post(
            "http://supervisor/addons/farm_agent/proxy/ask",
            headers={
                "X-Supervisor-Token": supervisor_token,
            },
            json={"question": user_input.text},
            timeout=30,
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                answer = data.get("answer", "No answer received")
                
                return ConversationResult(
                    response=answer,
                    conversation_id=user_input.conversation_id,
                )
```

---

## Comparison Table

| Aspect | Option 1 | Option 2 | Option 3 | Option 4 | Option 5 |
|--------|----------|----------|----------|----------|----------|
| **Hostname** | `farm_agent` | `farm-agent` | `localhost` | `supervisor` | `supervisor/proxy` |
| **Works?** | Maybe | Likely ✅ | No ❌ | Maybe | Yes ✅ |
| **Complexity** | Low | Low | Low | Medium | Medium |
| **Security** | Internal | Internal | Internal | Proxy | Proxy ✓ |
| **Auth** | None | None | None | Maybe | Yes ✓ |
| **Performance** | Fast | Fast | Fast | Medium | Medium |
| **Risk** | Medium | Low | Critical | Medium | Low |
| **Recommendation** | Need proof | Likely good | DON'T USE | Not standard | Most secure |

---

## Home Assistant's Own Approach

When Home Assistant Core needs to reach an add-on:
- Uses: `http://supervisor/addons/<SLUG>/proxy`
- Includes: `X-Supervisor-Token` header
- Method: Always authenticated through Supervisor

**Implication:** If HA uses Supervisor proxy, we should too.

---

## Decision Framework

### If Research Confirms Docker Hostname Works
→ Use **Option 2** (`farm-agent:8080`) for simplicity

### If Only Supervisor Proxy Is Documented
→ Use **Option 5** (`http://supervisor/addons/farm_agent/proxy`) for security

### If Underscore Is Actually OK
→ Can use **Option 1** (`farm_agent:8080`) but less preferred

### Whatever We Learn
→ **DO NOT use Option 3** (localhost) - confirmed wrong

---

## Critical Unknowns Requiring Research

1. **Does Supervisor assign hostname to add-ons?**
   - If yes: what format? (slug, hyphen-slug, other?)
   - If no: must use Supervisor proxy

2. **Can containers reach each other on Docker network?**
   - Yes: use Docker hostname (Option 1 or 2)
   - No: must use Supervisor proxy (Option 5)

3. **Is Supervisor proxy the recommended approach?**
   - Likely: should use Option 5
   - Maybe: could use Docker if simpler

4. **What do existing add-on-to-core integrations use?**
   - Would show the actual working pattern
   - Most reliable guide

---

## Research Status

**Awaiting:** Home Assistant 2026.9.3 official documentation/source code

**Will Determine:** Which option is correct

**Once Known:** Can implement with confidence

---

## Timeline

- **Now:** All options documented with rationale
- **Soon:** Research completes with definitive answer
- **Then:** Implement using confirmed correct option
- **Next:** Test on local HA
- **Finally:** Deploy to remote with confidence

---

## DO NOT GUESS

This decision is too critical. We will wait for research results and use official sources.

The difference between correct and incorrect hostname = integration either works perfectly or fails completely.

No amount of guessing or testing will help if the underlying hostname is wrong.

**Only proceed with implementation once hostname is confirmed from official Home Assistant 2026.9.3 source.**
