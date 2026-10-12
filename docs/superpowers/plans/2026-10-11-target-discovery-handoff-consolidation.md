# Target Discovery Handoff Consolidation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Leave one complete, auditable takeover package for the target-discovery lane that preserves history, current authority, code/data identities, qualification evidence, Macha instructions, and downstream decision boundaries.

**Architecture:** Keep executable code on PR #282, synthetic/metadata-only tournament governance on PR #275, and documentation/state/authority on PR #284. Add one master handoff as the primary new-agent entrypoint, then make START_HERE/current handoff/evidence index/Macha runbook/canonical machine state and PR #284 all point to the same current facts.

**Tech Stack:** GitHub markdown/JSON state, Python V5 target-discovery scripts, GitHub Actions qualification evidence.

**Spec:** `docs/agent/TARGET_DISCOVERY_CANONICAL_TAKEOVER_20261011.md` plus `docs/superpowers/specs/2026-10-11-td-corrected-replay-interpretation-prefreeze.md` and `docs/superpowers/specs/2026-10-11-td-multitarget-tournament-prefreeze-v2.md`.

## Global Constraints

- Preserve historical failures and superseded qualifications; never rewrite them as success.
- Do not merge any PR.
- Do not authorize G7, corrected TD56/57B/57C/59, TD60, target selection, representation selection, Stage4, or training.
- Keep PR #282 executable identity distinct from PR #284 audit-branch identity.
- Keep PR #275 synthetic/metadata-only governance distinct from real-data authority.
- Treat G4/G5 and G6/G7 custody PASS as technical/data-integrity evidence, not biological validation.
- TD57C historical FAIL is immutable; TD60 was never qualifyingly executed and must never be called failed.
- Donor remains the biological replication unit.
- Public research-data safety-tool blocks are tooling constraints, not evidence that the datasets are private/confidential.

## Review Focus

1. Stale PR #282 status accidentally claiming execution or G7 authority.
2. Stale PR #275 110/167/187-green references instead of the current 197-green authenticated-registry chain.
3. Missing historical 50K row-binding/global-row rule and failed first G6 namespace.
4. Missing distinction between historical relational biology and current corrected-replay authority.
5. Cross-lane leakage from V79 or representation work into real target-discovery claims.

---

### Task 1: Create master new-agent handoff

**Files:**
- Create: `docs/agent/TARGET_DISCOVERY_MASTER_HANDOFF_20261011.md`

**Interfaces:**
- Consumes: current PR #282 qualification/authority, PR #275 qualification, canonical history, evidence/data hashes.
- Produces: single primary new-agent handoff.

- [ ] Capture hard terminal, lane map, scientific objective, historical evidence, corrected-substrate reason, exact G4/G5/G6/G7 lineage, data/code identities, current authority, Macha execution instructions, and downstream decision tree.
- [ ] Include explicit claim boundaries and immutable historical failures.
- [ ] Include the current PR #275 197-green governance chain but no real-tournament authority.
- [ ] Commit.

### Task 2: Synchronize navigation and current-state files

**Files:**
- Modify: `docs/agent/TARGET_DISCOVERY_START_HERE_20261011.md`
- Modify: `docs/agent/TARGET_DISCOVERY_CURRENT_HANDOFF_20261011.md`
- Modify: `docs/agent/TARGET_DISCOVERY_EVIDENCE_CODE_DATA_INDEX_20261011.md`
- Modify: `docs/agent/MACHA_TARGET_DISCOVERY_AND_PARALLEL_LANE_RUNBOOK_20261011.md`

**Interfaces:**
- Consumes: Task 1 master handoff.
- Produces: consistent entrypoint, evidence index, and Macha operating instructions.

- [ ] Make master handoff the first read.
- [ ] Replace stale PR #282 and PR #275 states with exact current heads/results.
- [ ] Preserve all important hashes and canonical storage/evidence paths.
- [ ] Keep Macha STOP boundaries explicit.
- [ ] Commit.

### Task 3: Synchronize canonical machine state and PR #284

**Files:**
- Modify: `docs/agent/TARGET_DISCOVERY_CANONICAL_STATE_20261011.json`
- Modify: PR #284 body.

**Interfaces:**
- Consumes: Tasks 1-2.
- Produces: machine-readable current state and human-facing audit PR summary.

- [ ] Point canonical state at PR #282 exact qualified head `ff4a21f9e470f26e34a935b6a4c7c61b03a6dfb0` and PR #275 exact qualified head `0cbe6244756df3d1b7ed1ef4e1643aae0f94e875`.
- [ ] Keep replacement G6 authorized exactly once; G7 blocked pending external G6 audit.
- [ ] Add master handoff to PR #284 package list and update audit-branch head.
- [ ] Commit.

### Task 4: Final audit

**Files:** no new files required.

**Interfaces:**
- Consumes: all previous tasks.
- Produces: verified takeover plateau.

- [ ] Re-fetch all updated files from audit branch and check exact heads/hashes/status claims.
- [ ] Confirm PR #284 remains open/draft/unmerged and based on PR #282 qualified executable head.
- [ ] Confirm no claim authorizes G7, corrected replay, target selection, TD60, Stage4, or training.
- [ ] Record final handoff summary to the user.