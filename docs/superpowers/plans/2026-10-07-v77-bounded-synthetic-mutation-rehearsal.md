# V77 Bounded Synthetic Mutation Rehearsal Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement exactly one fail-closed synthetic optimizer update on the already-qualified V77 → shared interface → canonical V5 runtime path, followed by guarded EMA, typed persistence and deterministic reload.

**Architecture:** Add one narrow qualification-layer rehearsal wrapper; do not duplicate optimizer, EMA or checkpoint logic. Reuse `PhysicalRowValueBindingV2`, bound q-safety, canonical V5 guarded-update/EMA/checkpoint APIs and the existing joined ZERO_UPDATE fixture/configuration.

**Tech Stack:** Python 3.12, PyTorch, pytest, existing `sea_ad_jepa.v5` canonical runtime and `sea_ad_jepa.qualification` interfaces.

**Spec:** `docs/agent/V77_BOUNDED_SYNTHETIC_MUTATION_REHEARSAL_CONTRACT_20261007.md`

## Global Constraints

- Synthetic fixture only: 2 cells × 4 genes.
- Exactly one optimizer update attempt.
- Test-only EMA half-life = 1000 successful base-cell presentations.
- No second optimizer step.
- No corrected real-data statistic may enter the rehearsal.
- No new optimizer, EMA or checkpoint implementation.
- `training_authorized=False` and `production_promotable=False` in every receipt.

## Review Focus

- A failure path that mutates online/predictor parameters before rejecting.
- EMA advancing after a skipped/rejected optimizer step.
- A second update being possible through the same rehearsal object/call.
- A V1/weak proof being accepted instead of typed physical V2 continuation.
- Persistence/reload accepting EMA configuration drift.

---

### Task 1: Add RED joined-mutation contract tests

**Files:**
- Create: `tests/integration/test_v77_bounded_synthetic_mutation.py`
- Modify: `.github/workflows/v77-qualified-zero-update-join.yml`

**Interfaces:**
- Consumes: the existing `_batch`, `_bindings`, `_proof` semantics from joined ZERO_UPDATE tests and the prospective contract.
- Produces: failing tests defining the exact one-step rehearsal receipt and fail-closed attacks.

- [ ] **Step 1: Write the successful one-step test**

Require one call to the prospective rehearsal function to change online/predictor state, advance teacher age from 0 to 2 only after completed optimizer proof, create typed continuation, reload deterministically, and return the exact non-production verdict.

- [ ] **Step 2: Write adversarial tests**

Cover missing/wrong physical binding, wrong adapter/runtime digest, replayed q-safety proof, nonfinite/step-skip, EMA-before-completion, second-step attempt, V1 promotion, EMA config drift and non-authorizing flags.

- [ ] **Step 3: Wire the new test file into CI**

Run it in `v77-qualified-zero-update-join.yml` with the existing focused suites.

- [ ] **Step 4: Verify RED**

Expected: tests fail because the bounded-mutation rehearsal module/function does not yet exist.

### Task 2: Implement the smallest canonical rehearsal wrapper

**Files:**
- Create: `src/sea_ad_jepa/qualification/v77_bounded_mutation.py`
- Modify only if required for public export: `src/sea_ad_jepa/qualification/__init__.py`

**Interfaces:**
- Consumes: `QualificationBatchV1`, tuple of `PhysicalRowValueBindingV2`, `BoundAdapterQSafetyProofV1`, canonical runtime-source digest, init seed.
- Produces: `run_bounded_synthetic_mutation(...) -> dict[str, object]`.

- [ ] **Step 1: Reuse ZERO_UPDATE preflight**

Apply the same synthetic-only, runtime-source, q-safety, model-visible and V2 physical-binding checks before constructing runtime state.

- [ ] **Step 2: Reuse canonical runtime construction**

Build the same width/head/block/optimizer configuration as ZERO_UPDATE; capture parent typed checkpoint at update 0 / presentations 0.

- [ ] **Step 3: Issue test-only presentation EMA authority**

Use half-life 1000 and `SUCCESSFUL_BASE_CELL_PRESENTATIONS`; mark it mechanically test-only/non-production in the receipt.

- [ ] **Step 4: Execute exactly one canonical guarded update**

Use existing canonical guarded update APIs; do not call `optimizer.step()` or mutate teacher directly in the qualification wrapper.

- [ ] **Step 5: Persist typed continuation and reload**

Create the canonical child continuation after successful guard+EMA proof and verify deterministic reload.

- [ ] **Step 6: Return a non-authorizing receipt**

Include all contract-required pre/post digests, exactly two presentations on success, one optimizer step, continuation/reload evidence and the exact success verdict.

- [ ] **Step 7: Run focused tests**

Expected: new mutation suite GREEN and all existing ZERO_UPDATE/provenance/shared-interface tests remain GREEN.

### Task 3: Mutation-proof the fail-closed boundary

**Files:**
- Modify: `tests/integration/test_v77_bounded_synthetic_mutation.py`

**Interfaces:**
- Consumes: Task 2 rehearsal wrapper.
- Produces: evidence that mutation cannot occur through rejected paths.

- [ ] **Step 1: Verify every preflight attack leaves state unadvanced**

Assert no teacher age/EMA completion/child continuation on rejected calls.

- [ ] **Step 2: Verify nonfinite step cannot mint completion**

Use the canonical scaler/guard skip path and assert EMA is impossible.

- [ ] **Step 3: Verify second-step refusal**

Attempt to reuse the completed rehearsal continuation under the bounded API and require rejection before another update.

- [ ] **Step 4: Run the complete focused workflow suite**

Expected: zero skips, all tests GREEN.

### Task 4: Record exact execution evidence

**Files:**
- Create: `docs/agent/V77_BOUNDED_SYNTHETIC_MUTATION_REHEARSAL_RESULT_20261007.md` only after GREEN.

**Interfaces:**
- Consumes: exact branch head and GitHub Actions run.
- Produces: non-authorizing execution receipt/handoff.

- [ ] **Step 1: Record RED→GREEN commits and exact CI run**
- [ ] **Step 2: Record observed pre/post digests and proof identities**
- [ ] **Step 3: Restate that biological qualification and real training remain off**
