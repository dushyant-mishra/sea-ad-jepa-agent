# JEPA lane audit + takeover refresh implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refresh the canonical JEPA audit and handoff branches so a successor can take over without repeating historical archaeology, while preserving all authority boundaries and exact provenance.

**Architecture:** Keep PR #322 as the audit/provenance surface and PR #323 as the stacked custody/handoff surface. Copy the already-green post-TD harness byte-for-byte from frozen implementation head `97dd73f49e1554053bbfab6c5369377a23a72ceb`; do not reconstruct code. Add append-only current-state docs and machine-readable manifests. Keep large/private biological/checkpoint artifacts external and hash-bound rather than publicly uploaded.

**Tech Stack:** Git/GitHub objects, Python 3.12 unittest/py_compile, JSON/CSV/Markdown custody manifests.

**Spec:** `docs/agent/JEPA_LANE_TAKEOVER_HANDOFF_20261013.md`

## Global Constraints

- Binding authority remains `TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`.
- PR #314 is immutable/spent; do not rerun or reinterpret it.
- PR #313 remains a separate real-tournament lane.
- Synthetic lane remains read-only from this lane; controller truth remains separated unless separately authorized.
- Phase-1 receipt `e67aace8dfa8b9823cf8635155a48f5a78faed0a45bf9edb6f7adcba07737684` is structurally audited but does not grant phase-2, real-data, target-selection, TD60, Stage4 or training authority.
- Post-TD harness implementation head is `97dd73f49e1554053bbfab6c5369377a23a72ceb`; copy exact blobs only.
- Large/private expression/checkpoint/controller artifacts remain external custody and are referenced by exact size/hash.

## Review Focus

- No historical closed/superseded result is silently promoted to active authority.
- No controller truth or semantic mapping enters phase-1 custody.
- Handoff branch remains stacked on the current audit branch after the audit branch advances.
- Copied harness files match the source implementation blob identities exactly.
- All downstream authority flags remain false.

---

### Task 1: Preserve the current execution record

**Files:**
- Create: `docs/superpowers/plans/2026-10-13-jepa-lane-audit-takeover-refresh.md`

- [ ] Commit this plan to the audit branch before the refresh.

### Task 2: Consolidate exact post-TD runnable artifacts into audit custody

**Files:**
- Copy exact source blobs for 4 scripts, 4 tests, the harness workflow, and `docs/agent/JEPA_POST_TD_HARNESS_PREFREEZE_20261013.md` from `97dd73f49e1554053bbfab6c5369377a23a72ceb`.
- Create current-state audit manifest and append-only audit update document.

- [ ] Verify the source implementation workflow run `38448458550` is green on the exact source head.
- [ ] Preserve source commit/run/blob identities in the audit manifest.
- [ ] Commit exact blobs and audit update without granting new authority.

### Task 3: Refresh the stacked takeover/handoff branch

**Files:**
- Update: `docs/agent/JEPA_LANE_TAKEOVER_HANDOFF_20261013.md`
- Update: `docs/agent/JEPA_LATEST_HANDOFF_POINTER_20261013.json`
- Create: `docs/agent/JEPA_LANE_SUCCESSOR_HANDOFF_20261013.md`
- Create: `results/target_discovery/JEPA_LANE_SUCCESSOR_STATE_20261013.json`

- [ ] Merge the refreshed audit branch ancestry into the handoff branch.
- [ ] Record phase-1 receipt audit, post-TD harness status, custody hashes, current open work, and exact next actions.
- [ ] Keep all authority flags false.

### Task 4: Verify branch/PR custody

- [ ] Confirm PR #322 points to the refreshed audit head.
- [ ] Confirm PR #323 points to the refreshed stacked handoff head and includes the refreshed audit head as ancestry.
- [ ] Confirm the 10 harness paths on both custody surfaces resolve to the exact source blobs.
- [ ] Confirm GitHub Actions status for the new heads; if the handoff/audit validators run, record their exact outcomes.
- [ ] Add PR comments with frozen successor checkpoints and no-authority statement.
