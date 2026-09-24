# Pre-Deployment Checklist

**Status: AWAITING HOSTNAME VERIFICATION**

Once hostname research completes, use this checklist to ensure safe deployment.

---

## Phase 1: Research & Verification ⏳

- [ ] Hostname for add-on communication verified
  - Source: Home Assistant 2026.9.3 official docs/source
  - Hostname: `_______________` (to be filled in)
  - Evidence: `_______________` (to be filled in)

- [ ] Alternative hostnames ruled out
  - [ ] NOT localhost (different containers)
  - [ ] Verified correct format (underscore vs hyphen)
  - [ ] Verified no additional prefixes needed

- [ ] Port accessibility confirmed
  - [ ] Port 8080 internally accessible
  - [ ] Authentication requirements (if any) documented
  - [ ] Docker network configuration understood

---

## Phase 2: Implementation (Pending Hostname)

- [ ] Update conversation.py
  - [ ] Change endpoint from `localhost:8080` to correct hostname
  - [ ] Add error handling for connection failures
  - [ ] Test endpoint detection in config_flow

- [ ] Update config_flow.py
  - [ ] Auto-detect Farm Agent add-on
  - [ ] Verify endpoint is reachable
  - [ ] Store actual working endpoint
  - [ ] Handle detection failures gracefully

- [ ] Update config.yaml
  - [ ] Change port binding from `8080/tcp: 8080`
  - [ ] To: `"127.0.0.1:8080:8080"` (localhost only)
  - [ ] Rebuild add-on image

- [ ] Update conversation.py imports
  - [ ] Use correct method signature for HA 2026.9.3
  - [ ] Modern pattern: `_async_handle_message` (if applicable)
  - [ ] Or maintain `async_process` for compatibility

- [ ] Create comprehensive tests
  - [ ] Config flow endpoint detection
  - [ ] Conversation entity initialization
  - [ ] Mock HTTP server testing
  - [ ] Error handling (timeout, connection refused)

- [ ] Update documentation
  - [ ] Remove misleading "no restart" claims
  - [ ] Document exact hostname
  - [ ] Document why restart is required first time
  - [ ] Clear installation instructions

---

## Phase 3: Local Testing (First Local HA Instance)

**Prerequisites:**
- [ ] Farm Agent add-on already installed and running
- [ ] Farm Agent responding to `GET /ask?q=test`
- [ ] Farm Agent responding to `POST /ask` with JSON

**Integration Installation:**
- [ ] Files created in correct location
- [ ] Manifest.json is valid
- [ ] All imports are correct
- [ ] Conversation entity can be instantiated

**Integration Discovery:**
- [ ] Home Assistant finds the integration
- [ ] Settings → Devices & Services → Farm Agent appears
- [ ] Can create config entry without errors

**Configuration:**
- [ ] Config flow runs successfully
- [ ] Endpoint is auto-detected
- [ ] Endpoint detection shows correct hostname
- [ ] Config entry is stored correctly

**Restart & Boot:**
- [ ] Home Assistant restarts cleanly
- [ ] Integration loads at startup
- [ ] No errors in logs
- [ ] Conversation entity is available

**Assist Pipeline:**
- [ ] Farm Agent appears in Voice Assistants
- [ ] Can select as Conversation Agent
- [ ] Pipeline saves successfully

**Actual Conversation:**
- [ ] Can ask question via conversation.process service
- [ ] Question reaches Farm Agent add-on
- [ ] Farm Agent responds with answer
- [ ] Answer returns to Home Assistant
- [ ] Assist displays/speaks the answer

**Error Cases:**
- [ ] Timeout error handled gracefully
- [ ] Connection refused handled gracefully
- [ ] Malformed response handled gracefully
- [ ] Add-on unavailable shows useful error

**Rollback Test:**
- [ ] Remove custom_components/farm_agent/
- [ ] Restart Home Assistant
- [ ] Home Assistant starts cleanly
- [ ] No errors about missing integration
- [ ] Farm Agent add-on still works

---

## Phase 4: Local Documentation Verification

- [ ] Installation instructions are accurate
- [ ] Screenshots match actual UI
- [ ] Troubleshooting steps are correct
- [ ] Example questions work as documented
- [ ] Rollback procedure is clear and accurate

---

## Phase 5: Remote Deployment Planning

**Backup & Recovery:**
- [ ] Create Home Assistant backup snapshot
- [ ] Document backup restoration procedure
- [ ] Know how to SSH into remote HA if needed
- [ ] Have rollback procedure memorized

**Communication Plan:**
- [ ] Know how to contact help if needed
- [ ] Have documentation available offline
- [ ] Remote system has internet for GitHub/HACS

**Timing:**
- [ ] Schedule deployment at convenient time
- [ ] Account for ~5 minute downtime (restart)
- [ ] Remote system can be offline for that duration
- [ ] No critical farm operations during deployment

**Remote System Status:**
- [ ] Farm Agent add-on currently running on remote HA
- [ ] Remote HA is responding correctly
- [ ] Sensors are being read correctly
- [ ] System is stable before any changes

---

## Phase 6: Actual Remote Deployment

**Pre-Installation:**
- [ ] Verify remote HA is accessible
- [ ] Verify Farm Agent add-on is running
- [ ] Create backup snapshot
- [ ] Log into remote HA

**HACS Installation:**
- [ ] Add HACS custom repository: `realsystem/farm-agent-integration`
- [ ] Wait for HACS to index repository
- [ ] Search for "Farm Agent" in HACS
- [ ] Click Install
- [ ] HACS shows files being downloaded/installed

**Integration Discovery:**
- [ ] Files appear in /config/custom_components/farm_agent/
- [ ] manifest.json exists and is valid
- [ ] All Python files are present

**First Restart:**
- [ ] Home Assistant restart initiated
- [ ] Monitor restart progress (should be ~3-5 minutes)
- [ ] HA comes back online
- [ ] Check Home Assistant is accessible

**Integration Appearance:**
- [ ] Settings → Devices & Services shows Farm Agent
- [ ] Can click to create entry
- [ ] No errors in startup logs

**Configuration:**
- [ ] Create integration entry
- [ ] Config flow detects endpoint correctly
- [ ] No errors during creation
- [ ] Entry shows as "Loaded"

**Assist Pipeline:**
- [ ] Settings → Voice Assistants
- [ ] Select the Assist pipeline
- [ ] Conversation Agent tab shows Farm Agent
- [ ] Pipeline saves successfully

**Testing on Remote:**
- [ ] Ask question via phone Assist
- [ ] Farm Agent responds
- [ ] Answer is correct
- [ ] No timeouts or errors

**Verification:**
- [ ] Check logs for any errors
- [ ] Verify Farm Agent add-on is still running
- [ ] Test both GET and POST endpoints still work
- [ ] Multiple questions work correctly

---

## Phase 7: Ongoing Monitoring

**First Week:**
- [ ] Monitor logs for any errors
- [ ] Test Farm Agent regularly
- [ ] Verify responses are correct
- [ ] Check for any integration crashes

**Long Term:**
- [ ] Monitor HA logs for integration issues
- [ ] Keep HA updated to latest version
- [ ] Keep add-on updated when new versions available
- [ ] Report any issues to repository

---

## Critical Decision Points

**At Each Checkpoint, Ask:**

1. **Before updating conversation.py:**
   - Is the hostname confirmed correct?
   - Do we have evidence from official sources?

2. **Before local testing:**
   - Are all changes committed?
   - Do we have a rollback plan?
   - Is Farm Agent add-on running?

3. **Before first local restart:**
   - Have we tested without restart?
   - Have we verified endpoint works?
   - Have we documented the current state?

4. **Before remote deployment:**
   - Did local testing succeed completely?
   - Do we have a backup snapshot?
   - Is the timing acceptable?
   - Can we recover if something goes wrong?

---

## What Breaks the Process

**Stop and fix immediately if:**

- ❌ Hostname is not confirmed from official sources
- ❌ Endpoint detection fails
- ❌ Farm Agent cannot be reached
- ❌ Restart takes >10 minutes (something wrong)
- ❌ Integration doesn't appear in Settings
- ❌ Assist can't reach integration
- ❌ Responses are garbled or wrong
- ❌ Logs show repeated errors
- ❌ Rollback doesn't recover system
- ❌ Any unexpected behavior

**In any of these cases:**
- Stop deployment immediately
- Do NOT proceed to next step
- Investigate and document the issue
- Test fix locally before remote retry

---

## Sign-Off Checklist

**Before declaring ready to deploy to remote:**

- [ ] All research complete and verified
- [ ] All code changes tested locally
- [ ] All documentation accurate and updated
- [ ] Rollback procedure tested and verified
- [ ] Local HA integration working perfectly
- [ ] No errors in any phase
- [ ] Remote system ready to receive update
- [ ] Backup snapshot created
- [ ] User is confident and ready

**Only after ALL items are checked:**
Proceed to remote deployment

---

## Final Verification

The three critical questions before ANY Home Assistant changes:

1. **Is the hostname correct?**
   - Evidence: _______________
   - Source: _______________

2. **Has everything been tested locally?**
   - Result: PASS / FAIL

3. **Do we have a safe rollback?**
   - Procedure: Delete /config/custom_components/farm_agent/, restart
   - Tested: YES / NO

**All three must be YES before proceeding.**

---

**Remember: The remote farm system cannot be down for weeks. Every step must be reversible and thoroughly tested first.**
