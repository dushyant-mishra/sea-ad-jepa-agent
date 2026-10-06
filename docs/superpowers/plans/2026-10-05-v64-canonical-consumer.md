# V64 Canonical Consumer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close the V64 downstream seam so the existing V5 teacher/student mechanics can only perform an optimizer update through `CurrentTrainingAuthorityV2` + `CurrentOptimizerStepGuardV4`, then bind resumable checkpoint state to the same current authority lineage.

**Architecture:** Do not build a new JEPA trainer. Add a thin canonical consumer around the existing qualified mechanics and current V64 authority objects. Keep optimizer authorization, model mechanics, EMA ordering, and checkpoint authority as separate responsibilities so each can be red-teamed independently.

**Tech Stack:** Python, PyTorch, pytest, GitHub Actions.

**Spec:** `docs/agent/JEPA_DOWNSTREAM_PIPELINE_AUDIT_START_20261005.md` on draft PR #218, plus `results/v64/V64_DOWNSTREAM_SETUP_IMPLEMENTATION_STATUS_V1.json` on the V64 lineage.

## Global Constraints

- `TRAINING = OFF` at project authority level; this work creates mechanical code/tests only and does not authorize a scientific run.
- Do not change target-selection thresholds, scientific target definitions, V77 oracle bands, TEST, Morabito, 500K, Stage 4, or representation authority.
- Preserve existing encoder/predictor/teacher/dropout/weighting mechanics; compose rather than reimplement.
- No direct optimizer step is lawful from the canonical consumer without `CurrentTrainingAuthorityV2` and `CurrentOptimizerStepGuardV4`.
- EMA must occur only after the guarded optimizer step has completed and been acknowledged.
- Historical V1/V2/V3 guard/authority paths remain provenance and may not satisfy the new canonical consumer.
- Known synthetic truth remains evaluation-only and must never enter optimizer inputs or teacher target construction.

## Review Focus

1. A caller attempts an optimizer step without arming the V4 guard: fail closed before parameter mutation.
2. A stale/nonsequential schedule cursor is supplied: reject and do not perform EMA.
3. A guarded optimizer step succeeds but completion acknowledgement fails: do not advance EMA/checkpoint state.
4. Historical/untyped training authority is supplied: reject before model update.
5. Resume/checkpoint authority or registry identity drifts: reject load/resume rather than silently continuing.

---

### Task 1: Canonical guarded update consumer

**Files:**
- Create: `src/sea_ad_jepa/v5/current_canonical_update_consumer_v1.py`
- Create: `tests/test_v5_current_canonical_update_consumer_v1.py`
- Modify only if needed for CI discovery: existing V5 audit workflow, without changing scientific authority.

**Interfaces:**
- Consumes: existing V5 online encoder / EMA teacher / predictor / optimizer objects; `CurrentTrainingAuthorityV2`; V4 teacher-target receipt; expected target-package/root graph; integer schedule cursor.
- Produces: `run_current_guarded_optimizer_step_v1(...) -> CurrentGuardedStepReceiptV1`, a small mechanical receipt proving guard arm, one optimizer step, guard completion, and EMA-after-step ordering.

- [ ] **Step 1: Write the failing tests**
  - importing `run_current_guarded_optimizer_step_v1` must initially fail because the canonical consumer does not exist;
  - valid V4 authority + arm performs exactly one step and then EMA;
  - unarmed/direct bypass is rejected by the installed guard;
  - wrong authority type is rejected;
  - repeated/nonsequential cursor is rejected;
  - if optimizer step raises or completion cannot be acknowledged, EMA callback is not invoked.

- [ ] **Step 2: Run the focused test in GitHub Actions and verify RED**

Run: `pytest -q tests/test_v5_current_canonical_update_consumer_v1.py`
Expected: FAIL because `current_canonical_update_consumer_v1` / its public API does not exist.

- [ ] **Step 3: Implement the minimal canonical consumer**

Public API must install/reuse `CurrentOptimizerStepGuardV4`, arm exactly one cursor, invoke the optimizer with `v5_current_guard_schedule_cursor=<cursor>`, assert guarded completion, then and only then invoke the supplied EMA update callback. Do not duplicate model forward/backward logic in this file.

- [ ] **Step 4: Verify focused tests GREEN, then run the relevant V5/V64 authority suites**

Expected: new tests PASS; existing current-authority/optimizer-guard tests remain PASS.

- [ ] **Step 5: Commit**

Commit message: `feat: add V64 canonical guarded update consumer`

### Task 2: Current-authority resumable checkpoint binding

**Files:**
- First search the V64/later history for an existing current-authority checkpoint successor and reuse it if complete.
- If absent, Create: `src/sea_ad_jepa/v5/current_runtime_checkpoint_v1.py`
- Create: `tests/test_v5_current_runtime_checkpoint_v1.py`

**Interfaces:**
- Consumes: `CurrentTrainingAuthorityV2`; canonical guarded-step receipt; online/EMA/predictor state; optimizer/scaler state if resumable; schedule cursor; RNG states; registry/tokenizer digest; masking/view contract; model config; data/split identity; source-code provenance.
- Produces: sealed checkpoint payload plus `validate_current_runtime_checkpoint_v1(...)` and restore metadata that refuses authority/identity drift.

- [ ] **Step 1: Search later V64/Macha branches for an already-complete checkpoint successor**

If a later implementation binds the same current authority and required reproducibility fields, adopt it rather than duplicate it and write tests against it.

- [ ] **Step 2: Write failing tests for any missing behavior**
  - checkpoint refuses training-authority digest drift;
  - refuses registry/tokenizer digest drift;
  - refuses missing RNG/update-cursor state for resumable checkpoints;
  - distinguishes online encoder and EMA teacher state;
  - save/load preserves all declared metadata;
  - resume cursor must equal the next lawful guarded-step cursor.

- [ ] **Step 3: Verify RED in GitHub Actions**

Expected: tests fail only for the missing current checkpoint behavior.

- [ ] **Step 4: Implement the minimal missing checkpoint binding**

No model/scientific logic belongs in checkpoint code; it only seals and validates reproducibility/authority state.

- [ ] **Step 5: Verify focused tests and relevant V5/V64 suite GREEN**

Then run repository-wide tests available in CI and report every pre-existing or new failure by name.

- [ ] **Step 6: Commit**

Commit message: `feat: bind V64 runtime checkpoints to current authority`

### Task 3: Bypass/red-team closure and audit handback

**Files:**
- Create: `tests/test_v5_current_consumer_bypass_redteam_v1.py`
- Update: `docs/agent/JEPA_DOWNSTREAM_PIPELINE_AUDIT_START_20261005.md` on the PR #218 coordination branch only after results are known.

**Interfaces:**
- Consumes: Task 1 canonical consumer and Task 2 current checkpoint surface.
- Produces: evidence that old/unarmed stepping paths are unreachable from the canonical entrypoint and that resume cannot escape current authority binding.

- [ ] **Step 1: Add adversarial tests**
  - monkey-patched/historical authority object rejected;
  - direct `optimizer.step()` while V4 guard installed rejected;
  - cursor replay and cursor skipping rejected;
  - authority mutation after guard installation rejected;
  - EMA callback is not reached on any rejected step;
  - checkpoint from mismatched authority/root/registry rejected.

- [ ] **Step 2: Run focused red-team and relevant V5 suites**

Expected: all adversarial controls are actively rejected, not skipped.

- [ ] **Step 3: Update audit ledger with exact commit/test evidence**

Do not label the whole downstream pipeline qualified unless 41K reader/view/model/checkpoint composition has also been positively exercised. This task closes only the optimizer/checkpoint consumer seam.
