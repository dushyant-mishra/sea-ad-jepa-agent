# V5 D_shared Authority V2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a prospectively frozen D_shared-only V2 authority that supersedes the V1 scalar-max execution semantics, freezes the matched-null/effect/rank/multiplicity rules, and emits an exact FULL104 pre-outcome binding before any D_shared outcome can run.

**Architecture:** Preserve all V1 artifacts unchanged. Add a new V2 authority artifact and validator/plan/binding module, a D_shared-specific V2 execution firewall, and a V2 rank adjudicator with a terminal 512-rank boundary. The V2 cross-binding authorizes D_shared metric execution only and explicitly denies D_private, D_obs, training, protected data, TD60, and relational activation.

**Tech Stack:** Python 3, pytest, canonical JSON + SHA-256, existing `artifact_binding_v1` and `full104_dimension_interface_v1` validation patterns.

**Spec:** `docs/superpowers/specs/2026-09-14-v5-dshared-authority-v2-design.md`

## Global Constraints

- V1 precision SHA `cc4ac4d5116fa81990f1c3bd0497fc578eda86bb2d7d3cd2747abcf7ffcf9428` remains immutable.
- V1 cross-binding receipt SHA `eccc30f9f5d01f7905a0740982d678d0ce45532a08cd5a61c51f5448b63b3d3a` remains immutable provenance only.
- No current-V5 D_shared outcome may be generated or inspected during this implementation.
- Rank envelope is exactly 1..512.
- Familywise precision risk is 0.05 across 10 quantity families × 512 ranks.
- `alpha_per_quantity_rank = 9.765625e-6`.
- Frozen Hoeffding counts are 9,784 for range-2/epsilon-.05 or range-1/epsilon-.025, and 2,446 for range-1/epsilon-.05.
- D_shared V2 effect criterion is `SIMULTANEOUS_LOWER_BOUND_STRICTLY_GT_ZERO_V1`.
- Matched-null generator is `DETERMINISTIC_WITHIN_MATCHING_STRATUM_INDEPENDENT_VIEW_PERMUTATION_FULL_POPULATION_V1`.
- Matching tuple is exactly donor, operator, Q_DEPTH, Q_DETECT, support_measurability.
- Training/protected data/TD60/relational activation remain unauthorized.

---

### Task 1: Freeze and validate the V2 authority artifact

**Files:**
- Create: `docs/agent/V5_PROSPECTIVE_D_SHARED_AUTHORITY_V2.json`
- Create: `src/sea_ad_jepa/v5/d_shared_authority_v2.py`
- Create: `tests/test_d_shared_authority_v2.py`

**Interfaces:**
- Consumes: exact FULL104 parent hashes, V1 precision SHA, V1 cross-binding receipt SHA, dimension interface SHA.
- Produces: `validate_d_shared_authority_v2(authority)`, `canonical_d_shared_authority_bytes(authority)`, `bind_d_shared_execution_plan_v2(authority, authority_sha256=...)`.

- [ ] Write RED tests proving V2 rejects V1 schema, scalar-only replicate plans, rank envelopes other than 1..512, wrong multiplicity alpha, wrong Hoeffding counts, wrong generator/matching tuple, nonzero outcome-access flags, and authority-byte SHA substitution.
- [ ] Run only the new test file and record the expected import/function failures.
- [ ] Add canonical V2 JSON with all five D_shared quantities carrying explicit `replicates_by_rank` semantics and 9,784 declared replicates per rank.
- [ ] Implement minimal validator and plan builder. Plan output must carry a per-quantity map and may expose maxima only as informational fields.
- [ ] Re-run new tests to GREEN.

### Task 2: Bind V2 exactly to FULL104 and superseded V1 provenance

**Files:**
- Modify: `src/sea_ad_jepa/v5/d_shared_authority_v2.py`
- Extend: `tests/test_d_shared_authority_v2.py`

**Interfaces:**
- Produces: `bind_full104_d_shared_preoutcome_v2(...) -> dict[str, object]` with schema `JEPA_V5_FULL104_D_SHARED_PREOUTCOME_BINDING_V2`.

- [ ] Add RED tests for wrong FULL104 artifact SHA, wrong dimension-interface SHA, wrong parent, wrong V1 provenance SHA, and stage-authority escalation.
- [ ] Implement binding via `validate_full104_dimension_input` and exact six-parent comparison.
- [ ] Require output booleans: D_shared true; D_private false; D_obs false; training false; protected false; TD60 false; relational false.
- [ ] Re-run tests to GREEN.

### Task 3: Replace scalar-max firewall semantics with D_shared V2 semantics

**Files:**
- Create: `src/sea_ad_jepa/v5/d_shared_execution_firewall_v2.py`
- Create: `tests/test_d_shared_execution_firewall_v2.py`

**Interfaces:**
- Consumes: a raw D_shared execution receipt plus expected V2 pre-outcome binding SHA.
- Produces: `DSharedExecutionFirewallV2.validate(receipt)`.

- [ ] Add RED tests showing V1 scalar `donor_resamples=4794` is insufficient, missing per-quantity counts fail, any count substitution fails, ranks outside 1..512 fail, V1 cross-binding authority fails, caps fail, wrong null generator fails, matching tuple changes fail, survivor-only aggregation fails, silent failure dropping fails, forbidden data access fails, and D_private/D_obs flags fail.
- [ ] Implement exact per-quantity/rank plan validation and D_shared-only authorization checks.
- [ ] Re-run tests to GREEN.

### Task 4: Add terminal-boundary V2 rank adjudication

**Files:**
- Create: `src/sea_ad_jepa/v5/d_shared_rank_adjudication_v2.py`
- Create: `tests/test_d_shared_rank_adjudication_v2.py`

**Interfaces:**
- Produces: `select_shared_dimension_v2(rows)`.

- [ ] Add RED tests for standard one-SE prefix selection, lawful zero, interior tested-boundary expansion rejection, exact 512-row fully-supported terminal behavior, and rejection of >512/nonconsecutive rows.
- [ ] Implement selection without importing historical rank-32 envelopes.
- [ ] At 512 supported ranks, return `PASS_D_SHARED_FULL_RANK_ENVELOPE_EXHAUSTED` and the frozen one-SE-selected rank.
- [ ] Re-run tests to GREEN.

### Task 5: Freeze critical tests and CI coverage

**Files:**
- Modify: `tests/v5_critical_test_manifest_v1.json`
- Modify: `.github/workflows/v5_dataset_first_production_closure.yml`

**Interfaces:**
- Consumes: the new V2 test modules.
- Produces: CI coverage that cannot silently skip V2 authority/firewall/adjudication tests.

- [ ] Add V2 authority, binding, firewall, and rank-boundary tests to the critical manifest.
- [ ] Add new test files to the V5 workflow invocation.
- [ ] Verify manifest paths/test names exactly match pytest collection.

### Task 6: Supersession/governance receipt

**Files:**
- Create: `docs/agent/V5_D_SHARED_AUTHORITY_V2_SUPERSESSION_20260914.md`
- Update: `docs/agent/V5_CURRENT_AUTHORITY_AND_BLOCKERS_20260913.md`
- Update: `docs/agent/V5_MASTER_OPEN_ITEMS_20260913.md`

**Interfaces:**
- Produces: explicit statement that V1 precision/cross-binding remain provenance but cannot authorize D_shared execution; D_shared remains NOT RUN until a V2 heavy-machine binding receipt passes.

- [ ] Record exact V2 authority SHA and implementation head.
- [ ] Record that no D_shared outcome was inspected before V2 freeze.
- [ ] Keep training/protected/TD60/relational authority false.

### Task 7: Verification

**Files:** no new files unless verification exposes a defect.

- [ ] Run all new V2 tests.
- [ ] Run existing precision/binding/firewall/dimension tests for regressions.
- [ ] Run the repository V5 suite and critical execution guard.
- [ ] Compile authority-source modules.
- [ ] Compare branch against base `f78eb520...` and confirm only intended V2 code/tests/docs/workflow changes.
- [ ] Do not claim completion unless exact-head CI is green and critical tests are all executed, not skipped.
