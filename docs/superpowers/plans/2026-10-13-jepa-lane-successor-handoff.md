# JEPA Lane Successor Handoff Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Preserve the historical JEPA/Target Discovery audit, phase-1 custody evidence, downstream post-TD harness, local artifact identities, and a read-first takeover path without granting new scientific authority.

**Architecture:** Keep historical PR #322/#323 snapshots immutable; build append-only successor audit and handoff branches. Reuse the exact green post-TD harness tree, add machine-readable/current custody manifests, and stack a detailed successor-agent handoff on the audit successor.

**Tech Stack:** Git/GitHub, Python 3.12 contract tests, JSON/CSV/Markdown provenance.

**Spec:** `docs/agent/JEPA_LANE_SUCCESSOR_AUDIT_20261013.md`

## Global Constraints

- No target or representation selection.
- No phase-2 controller opening without separate authority.
- No phase-1 rerun.
- No Stage4, TD60, multimodal training, or real JEPA training authority.
- Preserve #313 separation and #314 immutability.
- Large/private biological binaries remain byte-bound by custody manifest rather than copied into public GitHub.

## Review Focus

- Gene-identity provenance must not silently upgrade pre-repair NPH semantic evidence.
- Historical rejected experiments must remain closed/negative priors unless explicitly replay-required.
- Downstream harness code must preserve all authority flags false.
- Phase-1 receipt identity/custody must remain exact and controller unopened.
- Handoff must distinguish implementation readiness from scientific authorization.

---

### Task 1: Cleanly consolidate post-TD harness

**Files:** Existing harness modules/tests/workflow from source commit `97dd73f49e1554053bbfab6c5369377a23a72ceb`.

- [x] Confirm source tree and green CI provenance.
- [x] Squash exact tree onto audited handoff base `87cd356d...` without carrying temporary marker history.
- [x] Preserve no-authority contracts.

### Task 2: Freeze successor audit state

**Files:**
- Create: `docs/agent/JEPA_LANE_SUCCESSOR_AUDIT_20261013.md`
- Create: `results/target_discovery/JEPA_LANE_SUCCESSOR_STATE_20261013.json`
- Create: `docs/agent/JEPA_LOCAL_ARTIFACT_CUSTODY_20261013.csv`
- Create: `docs/agent/JEPA_SUCCESSOR_BRANCH_MAP_20261013.md`

- [x] Record phase-1 exact identities and audit status.
- [x] Record historical no-repeat and gene-ID rules.
- [x] Bind local project artifacts by byte size and SHA-256.
- [x] Index active/frozen branches and separate lanes.

### Task 3: Freeze successor handoff

**Files:**
- Create: `docs/agent/JEPA_LANE_SUCCESSOR_HANDOFF_20261013.md`
- Create: `docs/agent/JEPA_LATEST_SUCCESSOR_POINTER_20261013.json`

- [x] Provide read-first sequence and takeover checklist.
- [x] State next lawful actions and hard stops.
- [x] Preserve architecture/teacher/student/EMA history without reopening closed ideas.

### Task 4: Publish and verify

- [ ] Open audit successor PR stacked on PR #323 branch.
- [ ] Open handoff successor PR stacked on audit successor.
- [ ] Link historical PR #322/#323 to successor pair.
- [ ] Run/inspect CI on exact successor heads and report any limitations.
