# V77 Qualified ZERO_UPDATE Join Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Join the current V77 synthetic adapter to shared qualification V2 and the canonical V5 runtime in ZERO_UPDATE mode, with executed q-safety and physical row/value provenance proven before any bounded mutation.

**Architecture:** Start from validated shared-interface SHA `e83bb8d90bbabefdfe6bfa7c5dfff994d7a41005`. Import/adapt only the V77 adapter/bridge logic needed from `51b7e2e4f91b53da6353dbff3bf944bbc5916006`; do not import V77 runtime machinery or change canonical V5 mechanics. The joined executor must bind the exact batch, executed q-safe transformations, source row/value provenance, and ZERO_UPDATE runtime result.

**Tech Stack:** Python 3.12, pytest, PyTorch, existing `sea_ad_jepa.qualification` and V5 runtime modules.

**Spec:** `docs/agent/JEPA_NEW_AGENT_FULL_TAKEOVER_HANDOFF_20261007.md` at custody commit `2708c8870cd32bdf0cd607829c5572af0ee32d46`.

## Global Constraints

- `TRAINING=OFF`; first joined execution is `ZERO_UPDATE` only.
- No TEST, Morabito, real-RNA mutation, 500K, Stage 4, or multimodal training.
- V1 runtime proof is diagnostic only; it cannot promote mutation authority.
- Rich-teacher loss remains a mechanics fixture, not target authority.
- Raw source/operator identity may support provenance diagnostics but must not enter learnable model inputs.
- Coordinates, logical identity, payload provenance, and consumed expression values must be one proof chain.

## Review Focus

- Correct row metadata paired with values from a different physical row must fail closed.
- Global/local/reset-index substitutions must fail closed.
- q-sensitive information must be transformed by the executed path, not merely declared safe.
- Raw source/operator or equivalent identity proxies must not reach encoder/predictor tensors or unrestricted context.
- ZERO_UPDATE must leave optimizer, online parameters, and EMA teacher unchanged.

---

### Task 1: Establish the joined adapter boundary

**Files:**
- Create: `src/sea_ad_jepa/qualification/v77_join.py`
- Test: `tests/integration/test_v77_joined_zero_update.py`

**Interfaces:**
- Consumes: `QualificationBatchV1`, current q-safety types, canonical V5 runtime binding.
- Produces: a narrow V77-to-qualification adapter and joined ZERO_UPDATE result with bound provenance.

- [ ] Write a failing test proving the current policy-only V77 handoff cannot count as executed joined proof.
- [ ] Run the focused test and record the isolated RED result.
- [ ] Implement the minimum typed join surface needed to construct/validate the batch without mutation.
- [ ] Re-run focused tests.
- [ ] Commit the bounded change.

### Task 2: Physical row/value provenance red-team

**Files:**
- Modify: `src/sea_ad_jepa/qualification/v77_join.py`
- Modify: `tests/integration/test_v77_joined_zero_update.py`

**Interfaces:**
- Consumes: authenticated logical row identity plus physical payload/value binding.
- Produces: fail-closed validation before qualification output or model input.

- [ ] Add RED tests for global/local row swap, reset-index substitution, correct digest/wrong row, correct metadata/wrong values, and correct logical row/wrong physical payload.
- [ ] Run tests and verify each attack reaches the intended boundary and fails for the missing protection.
- [ ] Add the minimum physical coupling checks.
- [ ] Re-run focused tests and existing qualification tests.
- [ ] Commit.

### Task 3: Executed q-safety proof

**Files:**
- Modify: `src/sea_ad_jepa/qualification/v77_join.py`
- Modify: `tests/integration/test_v77_joined_zero_update.py`

**Interfaces:**
- Consumes: exact batch identity, challenge partition, visibility classes, q-sensitive channels, exact adapter/interface/runtime identities.
- Produces: proof derived from transformations actually executed for that batch.

- [ ] Add RED tests showing declarations/callback registration alone cannot mint q-safety.
- [ ] Add q-leak attacks across all required q-sensitive channels.
- [ ] Implement execution-bound transformation evidence and digest binding.
- [ ] Verify stale or mismatched proof cannot be reused on another batch/run.
- [ ] Commit.

### Task 4: Model-input shortcut firewall

**Files:**
- Modify: `src/sea_ad_jepa/qualification/v77_join.py`
- Modify: `tests/integration/test_v77_joined_zero_update.py`

**Interfaces:**
- Consumes: lawful measurement/support context.
- Produces: model-facing inputs with raw source/operator identity and unapproved identity proxies excluded.

- [ ] Add RED tests that plant source/operator identity and proxy substitutions.
- [ ] Inspect the exact objects crossing into encoder/predictor calls.
- [ ] Implement the narrow allowlist/sanitization needed for model-facing context.
- [ ] Verify provenance remains available outside learnable inputs.
- [ ] Commit.

### Task 5: Canonical ZERO_UPDATE runtime proof

**Files:**
- Modify: `src/sea_ad_jepa/qualification/v77_join.py`
- Modify: `tests/integration/test_v77_joined_zero_update.py`

**Interfaces:**
- Consumes: validated joined batch and current canonical runtime binding.
- Produces: ZERO_UPDATE receipt proving no online/optimizer/EMA mutation.

- [ ] Add pre/post state assertions for online parameters, optimizer state, teacher parameters/age, and mutation authority.
- [ ] Execute canonical ZERO_UPDATE path.
- [ ] Verify V1 cannot promote mutation authority and only typed V2 remains the eventual promotion route.
- [ ] Run existing runtime-binding integration tests.
- [ ] Commit.

### Task 6: Spillover audit and CI

**Files:**
- Create: `.github/workflows/v77-qualified-zero-update-join.yml`
- Create: `docs/agent/JEPA_V77_QUALIFIED_ZERO_UPDATE_JOIN_20261007.md`

**Interfaces:**
- Produces: GitHub-verifiable joined gate and exact SHA/result record.

- [ ] Add a focused workflow covering the joined path plus relevant qualification/runtime regression tests.
- [ ] Search the joined tree for alternate optimizer/EMA/checkpoint paths, weaker V1 promotion, fixed `.996`, unbound row coordinates, and raw identity model inputs.
- [ ] Check all 42 observation operators remain represented at the rehearsal smoke scale.
- [ ] Run the focused and broader suites.
- [ ] Record exact runtime/interface/V77/join SHAs and evidence classification.
- [ ] Open a draft PR against `reconcile/shared-qualification-v2-on-canonical-runtime-20261007` and require GREEN CI before any bounded mutation rehearsal.
