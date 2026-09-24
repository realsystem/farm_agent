# Hostname Verification - Critical Before Implementation

## Question Being Researched

**What is the correct internal hostname for Home Assistant Core (2026.9.3) to reach the Farm Agent add-on?**

### Context
- Add-on repository: https://github.com/realsystem/farm_agent
- Add-on slug: `farm_agent`
- Home Assistant version: 2026.9.3
- Communication direction: HA Core → Farm Agent Add-on
- Port: 8080 (where Farm Agent listens)

---

## Candidates Being Verified

1. **`http://farm_agent:8080`**
   - Slug used directly as hostname
   - Pros: Simple, Docker-native
   - Cons: Underscore might not resolve

2. **`http://farm-agent:8080`**
   - Slug with underscore converted to hyphen
   - Pros: Follows DNS naming conventions
   - Cons: Requires confirmation this conversion happens

3. **`http://localhost:8080`**
   - Direct localhost
   - Pros: Simple
   - Cons: Different containers, should NOT work

4. **`http://supervisor/addons/farm_agent`**
   - Through Supervisor proxy
   - Pros: More secure, authenticated
   - Cons: More complex, requires Supervisor token

5. **Other mechanism**
   - Some other internal addressing scheme
   - Will be identified during research

---

## What We're Verifying

### Primary
- [ ] Exact internal hostname for add-on communication
- [ ] Whether hostname is based on slug or something else
- [ ] Whether underscores in slug are converted (to hyphens or not)
- [ ] Port exposure on internal Docker network

### Secondary
- [ ] Authentication requirements between add-ons
- [ ] DNS resolution configuration inside containers
- [ ] Example implementations from other add-ons
- [ ] Supervisor source code confirmation

### Tertiary
- [ ] Whether Supervisor proxy is recommended
- [ ] Performance implications of different approaches
- [ ] Security implications of direct vs. proxied communication

---

## Sources Being Checked

1. **Home Assistant Supervisor Repository**
   - github.com/home-assistant/supervisor
   - Docker compose configuration
   - Add-on spawning code
   - DNS/networking setup

2. **Home Assistant Core Repository**
   - github.com/home-assistant/core
   - Add-on integration examples
   - Conversation component (if it communicates with add-ons)
   - Test fixtures showing add-on communication

3. **Home Assistant Official Documentation**
   - developers.home-assistant.io
   - Add-on communication docs
   - Supervisor networking docs
   - Official examples

4. **Working Add-on Examples**
   - Add-ons that expose HTTP services
   - Add-ons that communicate with other add-ons
   - Real-world implementations

---

## What This Determines

Once verified, the hostname will be used in:

1. **conversation.py**
   ```python
   async with session.post(
       f"http://{HOSTNAME}:8080/ask",
       ...
   )
   ```

2. **config_flow.py**
   ```python
   async with session.post(
       f"http://{HOSTNAME}:8080/ask",
       ...
   )
   ```

3. **Documentation**
   - Installation instructions
   - Troubleshooting guide
   - Architecture diagram

---

## Risk if Wrong

If hostname is incorrect:
- ❌ Integration will fail with "Connection Refused"
- ❌ Deployment to remote HA will be broken
- ❌ No clear error message (network timeout looks like HA down)
- ❌ Difficult to debug without physical access

---

## Risk Mitigation

This is why we're verifying BEFORE:
1. Implementing the integration
2. Installing on local HA
3. Deploying to remote HA

Once verified, we can be confident the integration will work.

---

## Research Status

**In Progress:** Agent researching Home Assistant 2026.9.3 source and documentation

**Waiting for:** Definitive answer with evidence from official sources

**No assumptions:** We will not proceed until we have VERIFIED the correct hostname

---

## Next Action

Once research completes:

1. Document exact hostname with evidence
2. Update conversation.py with correct hostname
3. Update config_flow.py to detect and verify
4. Test on local Home Assistant
5. Deploy with confidence

**Timeline:** Research should complete in ~5-10 minutes

---

## DO NOT DEPLOY until this is verified

The entire integration hinges on reaching the add-on correctly. This must be right.
