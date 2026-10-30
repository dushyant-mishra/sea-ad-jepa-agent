# Downstream Qualification Program V1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Status:** `ANALYSIS_ONLY__PROSPECTIVE_PLAN_CANDIDATE__NOT_YET_CONTROLLING_IMPLEMENTATION_AUTHORITY`

**Goal:** Qualify the exact merged `TARGET_QUALIFICATION_BUNDLE_V1 → teacher → student → predictor → optimizer/EMA → checkpoint/runtime → downstream certification → runtime eligibility` chain without repeating historical audits or inheriting stale training authority.

**Architecture:** This is a reuse-first qualification program layered after unified Task 7 emits an exact verified Target Qualification Bundle. Historical V4/V5 tests and audit artifacts are inherited as regression/attack evidence, but every claim whose scientific input or authority context changes under the merged TQB/current runtime is requalified through exact receipts. No package may promote the next package merely because its historical analogue was green.

**Tech Stack:** Python, PyTorch, pytest, JSON/JSON Schema-style canonical receipts, existing `sea_ad_jepa.v4/v5` modules as historical evidence/adapters, unified `scripts/v5/td_unified` authority/receipt primitives.

**Spec:**
- `docs/agent/DOWNSTREAM_QUALIFICATION_DELTA_FROM_HISTORICAL_AUDITS_V1_20261014.md`
- `results/target_discovery/unified_qualification_v1/DOWNSTREAM_QUALIFICATION_EVIDENCE_REUSE_MATRIX_V1.json`
- `docs/superpowers/specs/2026-10-14-unified-td-qualification-downstream-custody-architecture-v1.md`
- `docs/superpowers/specs/2026-10-14-unified-td-qualification-downstream-custody-architecture-v1-1-hostile-review-amendment.md`

## Global Constraints

- This plan is not executable until Task 0 receives exact-head independent acceptance and the downstream amendment is prospectively adopted into the controlling implementation plan.
- `TARGET_QUALIFICATION_BUNDLE_V1` is the only lawful TD→downstream scientific handoff.
- Recompute the exact TQB digest; never trust a caller-supplied digest string.
- No support, estimability, source, endpoint, target, relation, observation or evidence-right widening downstream.
- Historical V4/V5 PASS/GREEN states are evidence inputs, not current authority.
- Before new tests, classify the claim as `ALREADY_AUDITED`, `SUPERSEDED`, `OPEN`, or `CHANGED_INPUT_REQUIRES_REQUALIFICATION`.
- Reuse/port historical tests when equivalent; do not repeat historical archaeology.
- `reader_validation` and `reader_oracle` remain protected unless a later explicit authority transition permits access.
- `SUBSPACE_ONLY` is the current representation interpretation ceiling where axes are not qualified.
- Technology invariance is not currently qualified.
- Same-nucleus and separate-nucleus evidence are distinct operators; independently measured ATAC is distinct from RNA-derived regulatory hypotheses.
- Stored and unmaterialized library mass remain distinct where decision-bearing; no zero-fill of unsupported/non-estimable targets.
- Optimizer completion must be proved before EMA; rejected/incomplete updates cannot advance teacher.
- `DOWNSTREAM_CERTIFIED` cannot promote directly to `TRAINING_ELIGIBLE`; `RUNTIME_ELIGIBILITY_RECEIPT_V1` is mandatory.
- `TRAINING_ELIGIBLE` does not imply `TRAINING_AUTHORIZED`; project-scope owner authorization is separate.
- Global authority remains `TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED` until explicit later authority changes it.

## Review Focus

1. **Historical-test substitution:** current code must actually run inherited attacks against exact TQB/current-runtime bytes, not merely cite old PASS artifacts.
2. **Identity/query shortcuts:** target address/query identity must not supply an unqualified shortcut through predictor/online/EMA pathways.
3. **Information-channel leakage:** normalization totals, support, source, visibility, missingness and evidence availability must be attacked explicitly.
4. **Authority inflation:** component mechanics, downstream certification and runtime eligibility must remain distinct authority stages/scopes.
5. **Changed-input drift:** any model/config/masking/EMA/proposal/checkpoint change creates a new authority identity and cannot inherit the old stage automatically.

---

### Task A: Exact TQB Consumption and Target Semantics

**Files:**
- Create: `scripts/v5/downstream_qualification/tqb_consumption_v1.py`
- Create: `schemas/target_discovery/unified_v1/downstream_target_binding_v1.json`
- Test: `tests/v5/downstream_qualification/test_tqb_consumption_v1.py`

**Interfaces:**
- Consumes: `VerifiedTargetBundle` from unified Task 7.
- Produces: `DownstreamTargetBinding`; `bind_downstream_target(bundle, resolver) -> DownstreamTargetBinding`.

- [ ] **Step 1: Port historical scientific-target invariants into RED tests**

Reuse assertions from `tests/test_teacher_student_v5_scientific_target_v2.py` where compatible. Add:

```python
def test_downstream_target_recomputes_exact_tqb_digest(): ...
def test_target_none_remains_lawful_terminal_and_cannot_spawn_training_target(): ...
def test_target_or_portfolio_semantics_addresses_relations_and_limitations_match_tqb_exactly(): ...
def test_support_or_estimability_widening_fails_closed(): ...
```

- [ ] **Step 2: Run focused RED**

Run: `python -m pytest -q tests/v5/downstream_qualification/test_tqb_consumption_v1.py`
Expected: FAIL because implementation is absent.

- [ ] **Step 3: Implement exact binding without training code**

- [ ] **Step 4: Run GREEN plus inherited target tests**

Run: `python -m pytest -q tests/v5/downstream_qualification/test_tqb_consumption_v1.py tests/test_teacher_student_v5_scientific_target_v2.py`
Expected: PASS.

- [ ] **Step 5: Freeze exact review head and receipt; no authority beyond target binding**

---

### Task B: Teacher Evidence and Target-Construction Contract

**Files:**
- Create: `scripts/v5/downstream_qualification/teacher_contract_v1.py`
- Create: `schemas/target_discovery/unified_v1/teacher_construction_receipt_v1.json`
- Test: `tests/v5/downstream_qualification/test_teacher_contract_v1.py`

**Interfaces:**
- Consumes: `DownstreamTargetBinding`, TQB evidence-right/provenance fields.
- Produces: `TeacherConstructionReceipt`.

- [ ] **Step 1: Reuse historical teacher mechanics as fixtures, not authority**

Read/port relevant assertions from `tests/test_teacher_student_unified_runtime_v1.py` and V5 data-first tests.

- [ ] **Step 2: Add RED tests for changed evidence context**

```python
def test_teacher_reads_only_tqb_allowed_evidence(): ...
def test_teacher_private_information_is_explicit_and_not_student_target_by_default(): ...
def test_independent_atac_and_rna_derived_regulatory_hypotheses_remain_distinct(): ...
def test_same_nucleus_and_separate_nucleus_evidence_cannot_be_substituted(): ...
def test_query_or_hidden_total_leakage_in_teacher_target_fails(): ...
```

- [ ] **Step 3: Run RED; implement minimal construction validator; run GREEN**

- [ ] **Step 4: Freeze receipt bound to exact TQB and evidence provenance**

---

### Task C: Student Restriction, Recoverability and Uncertainty

**Files:**
- Create: `scripts/v5/downstream_qualification/student_contract_v1.py`
- Create: `schemas/target_discovery/unified_v1/student_restriction_receipt_v1.json`
- Test: `tests/v5/downstream_qualification/test_student_contract_v1.py`

**Interfaces:**
- Consumes: Teacher receipt + TQB support/evidence/estimability scope.
- Produces: `StudentRestrictionReceipt`.

- [ ] **Step 1: RED-test exact evidence restriction and no protected partition rescue**
- [ ] **Step 2: RED-test four recoverability classes: point, stochastic, teacher-private, NOT_ESTIMABLE**
- [ ] **Step 3: RED-test uncertainty requirement for stochastic-identifiable targets**
- [ ] **Step 4: RED-test no zero-fill/no fake target for NOT_ESTIMABLE**
- [ ] **Step 5: Implement minimal contract and run GREEN with `test_population_access_registry_v1.py`**

---

### Task D: Target-Address / Query-Identity Shortcut Firewall

**Files:**
- Create: `scripts/v5/downstream_qualification/target_query_firewall_v1.py`
- Test: `tests/v5/downstream_qualification/test_target_query_firewall_v1.py`

**Historical evidence to reuse:**
- Sept. 15 target-identity shortcut finding in `JEPA_HISTORICAL_AUDITS_INDEX_20260915.md`
- branch `planning/v5-teacher-target-redteam-20260915 @ e342455ae841050282ef1932824e1aec971f1375`
- V4 predictor/F1-B attacks.

- [ ] **Step 1: Do not rediscover the path; encode it as the RED threat model**
- [ ] **Step 2: RED-test identity-only baseline, shuffled target identities and fixed/separate target-address codes**
- [ ] **Step 3: RED-test gradient path from target identity to online identity table/EMA teacher**
- [ ] **Step 4: Implement the minimum qualified target-address/query representation**
- [ ] **Step 5: Run inherited predictor/F1-B regressions plus new attacks GREEN**

---

### Task E: Masking and Evidence-Acquisition Shortcut Firewall

**Files:**
- Create: `scripts/v5/downstream_qualification/masking_qualification_v1.py`
- Test: `tests/v5/downstream_qualification/test_masking_qualification_v1.py`

**Historical evidence to reuse:** V5 support schedule, finite triplets, Sept. 15 cross-view shortcut audit and historical CorrMask review.

- [ ] **Step 1: RED-test uniform masking against correlated-neighbor/local-interpolation shortcut**
- [ ] **Step 2: RED-test historical graph masking against pooled FULL104/source-confounded covariance**
- [ ] **Step 3: RED-test donor/source-recurrent or cross-source-consensus candidate masking**
- [ ] **Step 4: Freeze outcome-blind coverage/exposure criteria before model outcomes**
- [ ] **Step 5: Implement selected policy only after prospective review; run all alternatives as falsifiers**

---

### Task F: Scientific Weighting, Proposal and Exposure Schedule

**Files:**
- Create: `scripts/v5/downstream_qualification/scientific_weight_schedule_v1.py`
- Test: `tests/v5/downstream_qualification/test_scientific_weight_schedule_v1.py`

**Historical tests:** `test_teacher_student_v5_objective_schedule_v2.py`, `test_teacher_student_v5_proposal_policy_v1.py`, `test_teacher_student_v5_support_schedule_v1.py`.

- [ ] **Step 1: Rebind donor-primary p to exact current manifest/TQB**
- [ ] **Step 2: RED-test that q cannot redefine p and exact p/q correction is mandatory**
- [ ] **Step 3: Freeze repeat/exposure and donor×operator coverage constraints prospectively**
- [ ] **Step 4: Derive q under frozen constraints without outcome tuning**
- [ ] **Step 5: Run historical proposal/schedule tests plus current binding tests GREEN**

---

### Task G: Representation, Subspace and Transfer Scope

**Files:**
- Create: `scripts/v5/downstream_qualification/representation_scope_v1.py`
- Test: `tests/v5/downstream_qualification/test_representation_scope_v1.py`

- [ ] **Step 1: RED-test `SUBSPACE_ONLY` propagation and axis-semantics prohibition**
- [ ] **Step 2: RED-test technology-invariance claim remains false unless separately qualified**
- [ ] **Step 3: Add principal-angle/canonical-correlation/Procrustes/eigengap receipt interfaces**
- [ ] **Step 4: Preserve HVS/NPH52 non-demonstration as non-absence and forbid forced invariance**
- [ ] **Step 5: Run GREEN; cap interpretation scope in downstream receipt**

---

### Task H: Normalization, Library, Support and Information Channels

**Files:**
- Create: `scripts/v5/downstream_qualification/information_channel_v1.py`
- Test: `tests/v5/downstream_qualification/test_information_channel_v1.py`

- [ ] **Step 1: RED-test stored vs unmaterialized/full library mass provenance**
- [ ] **Step 2: RED-test denominator/source shortcut**
- [ ] **Step 3: RED-test address parity cannot stand in for evidence parity**
- [ ] **Step 4: RED-test source-explicit estimability and no zero-fill**
- [ ] **Step 5: RED-test a within-donor metric cannot certify absence of a channel it is invariant to**
- [ ] **Step 6: Run GREEN with Sept. 15 cross-view/FULL104 fixtures**

---

### Task I: Multimodal / Regulatory Provenance

**Files:**
- Create: `scripts/v5/downstream_qualification/multimodal_provenance_v1.py`
- Test: `tests/v5/downstream_qualification/test_multimodal_provenance_v1.py`

- [ ] **Step 1: RED-test RNA-derived hypotheses cannot become independent regulatory truth**
- [ ] **Step 2: RED-test same-nucleus vs separate-nucleus operator identity**
- [ ] **Step 3: RED-test nearest-gene/proximity cannot become causal target**
- [ ] **Step 4: RED-test incomplete SCENIC work cannot promote**
- [ ] **Step 5: Bind exact evidence provenance into teacher and downstream receipts**

---

### Task J: Joined Optimizer / Gradient / Moment / EMA Runtime

**Files:**
- Create: `scripts/v5/downstream_qualification/runtime_update_v1.py`
- Test: `tests/v5/downstream_qualification/test_runtime_update_v1.py`

**Must reuse:**
- `test_c2_mandatory_gradient_gate_v1.py`
- `test_f1b_successor_attack_suite_v1.py`
- `test_healthy_teacher_training_contract_v1.py`
- `test_teacher_student_unified_runtime_v1.py`
- `test_teacher_student_v5_inactive_update_reference.py`

- [ ] **Step 1: Port the historical causal update-chain attacks verbatim where semantics match**
- [ ] **Step 2: RED-test current protected registry and scientific-weight input**
- [ ] **Step 3: RED-test rejected/incomplete update cannot advance EMA/cursor/checkpoint**
- [ ] **Step 4: Implement current joined update path; do not call legacy V4 `production_update` as authority**
- [ ] **Step 5: Run inherited attacks + current tests GREEN**

---

### Task K: EMA Timescale Authority

**Files:**
- Create: `scripts/v5/downstream_qualification/ema_schedule_v1.py`
- Test: `tests/v5/downstream_qualification/test_ema_schedule_v1.py`

- [ ] **Step 1: RED-test historical `.996` cannot be accepted as current authority**
- [ ] **Step 2: Implement presentation-normalized schedule `m_u = exp(log(0.5) * p_u / H)`**
- [ ] **Step 3: Prospectively freeze the presentation unit and H before outcomes**
- [ ] **Step 4: Attack lag, collapse, resume and variable-presentation invariance**
- [ ] **Step 5: Freeze EMA schedule receipt only after independent review**

---

### Task L: Checkpoint, Resume, Source and Runtime Provenance

**Files:**
- Create: `scripts/v5/downstream_qualification/checkpoint_v1.py`
- Create: `schemas/target_discovery/unified_v1/downstream_checkpoint_receipt_v1.json`
- Test: `tests/v5/downstream_qualification/test_checkpoint_v1.py`

- [ ] **Step 1: Port V4 checkpoint/source tamper tests**
- [ ] **Step 2: Bind exact TQB + downstream-certification + config/source/model identities**
- [ ] **Step 3: Bind optimizer/teacher/predictor/scaler/RNG/cursors/EMA counters/environment**
- [ ] **Step 4: Exact uninterrupted-vs-resume continuation attack**
- [ ] **Step 5: Fail closed on any moved source/runtime identity**

---

### Task M: Model / Protected Registry / Geometry Authority

**Files:**
- Create: `scripts/v5/downstream_qualification/model_geometry_v1.py`
- Test: `tests/v5/downstream_qualification/test_model_geometry_v1.py`

- [ ] **Step 1: RED-test hard-coded historical six-block/48-tensor/128×8 constants**
- [ ] **Step 2: Derive protected registry from exact final model**
- [ ] **Step 3: Freeze model depth/width/heads independently from D_shared rank ceiling**
- [ ] **Step 4: Bind registry digest to update/checkpoint/runtime receipts**
- [ ] **Step 5: Run current-registry anti-carryover regressions GREEN**

---

### Task N: Packing, RNG and Hardware Equivalence

**Files:**
- Create: `scripts/v5/downstream_qualification/packing_rng_v1.py`
- Test: `tests/v5/downstream_qualification/test_packing_rng_v1.py`

**Reuse:** V5 packed-equivalence, RNG-contract, dense-packed and numerical-boundary tests.

- [ ] **Step 1: RED-test identity-keyed RNG independent of tensor position/packing**
- [ ] **Step 2: RED-test packing preserves cell set, masks and scientific weight mass**
- [ ] **Step 3: Qualify optimized GPU kernel against frozen reference vectors**
- [ ] **Step 4: Calibrate token/memory budget on target hardware without changing science**
- [ ] **Step 5: Run dense/packed output+gradient equivalence at current configuration**

---

### Task O: Collapse, Movement and Stability Qualification

**Files:**
- Create: `scripts/v5/downstream_qualification/stability_v1.py`
- Test: `tests/v5/downstream_qualification/test_stability_v1.py`

- [ ] **Step 1: Port exact decay-only movement tests; reject fixed 2× historical margin**
- [ ] **Step 2: RED-test mandatory tensor noncompensation**
- [ ] **Step 3: RED-test collapse/stability at representation/subspace level**
- [ ] **Step 4: Refuse axis interpretation when only subspace stability passes**
- [ ] **Step 5: Freeze prospective thresholds/reference law before training outcomes**

---

### Task P: Historical Leakage / Falsifier Regression Battery

**Files:**
- Create: `scripts/v5/downstream_qualification/regression_battery_v1.py`
- Test: `tests/v5/downstream_qualification/test_regression_battery_v1.py`

- [ ] **Step 1: Adapter-run all applicable historical attacks on exact new TQB/runtime**
- [ ] **Step 2: Include normalization/query/hidden-total/support/wrong-cell/donor/source/oracle/evidence-starvation/target-drift/support-widening attacks**
- [ ] **Step 3: Add target-identity, masking-dependency, F7 and F9 attacks**
- [ ] **Step 4: Require an immutable test receipt for every mandatory attack**
- [ ] **Step 5: No aggregate score may rescue a failed mandatory falsifier**

---

### Task Q: Downstream Certification Receipt

**Files:**
- Create/extend: `scripts/v5/td_unified/downstream_contract_v1.py`
- Create/extend: `schemas/target_discovery/unified_v1/downstream_certification_contract_v1.json`
- Test: `tests/v5/downstream_qualification/test_downstream_certification_v1.py`

- [ ] **Step 1: RED-test every inherited TQB obligation must have exercised receipt**
- [ ] **Step 2: RED-test exact teacher/student/representation/evaluation identities**
- [ ] **Step 3: RED-test missing Package A–P receipt blocks certification**
- [ ] **Step 4: Issue `DOWNSTREAM_CERTIFIED` at pipeline scope only**
- [ ] **Step 5: Confirm global training authority remains off**

---

### Task R: Runtime Eligibility Receipt

**Files:**
- Create: `scripts/v5/downstream_qualification/runtime_eligibility_v1.py`
- Create: `schemas/target_discovery/unified_v1/runtime_eligibility_receipt_v1.json`
- Test: `tests/v5/downstream_qualification/test_runtime_eligibility_v1.py`

- [ ] **Step 1: Require exact active downstream-certification parent**
- [ ] **Step 2: Require Packages J–P active current identities and joined q-safety**
- [ ] **Step 3: Fail on moved checkpoint/source/runtime/config identity**
- [ ] **Step 4: Emit runtime-eligibility receipt without project training authority**

---

### Task S: Independent Training-Eligibility Review

**Files:**
- Create: `scripts/v5/downstream_qualification/training_eligibility_v1.py`
- Test: `tests/v5/downstream_qualification/test_training_eligibility_v1.py`

- [ ] **Step 1: RED-test component PASS/GREEN cannot create project training eligibility**
- [ ] **Step 2: Require exact TQB, downstream certification, runtime eligibility and all active parents**
- [ ] **Step 3: Require distinct independent review identity**
- [ ] **Step 4: Issue `TRAINING_ELIGIBLE` at `PROJECT:TRAINING` scope only if all prerequisites pass**
- [ ] **Step 5: Assert `TRAINING_AUTHORIZED` still false**

---

### Task T: Explicit Owner Training Authorization

**Files:**
- Create only after Task S acceptance: `scripts/v5/downstream_qualification/training_authorization_v1.py`
- Test: `tests/v5/downstream_qualification/test_training_authorization_v1.py`

- [ ] **Step 1: RED-test automatic promotion from eligibility is impossible**
- [ ] **Step 2: Require explicit owner authorization bound to exact eligibility identity**
- [ ] **Step 3: Reject stale/moved/revoked prerequisite chain**
- [ ] **Step 4: Only this separate project-scope action may create `TRAINING_AUTHORIZED`**

---

## Self-Review

**Spec coverage:** Packages A–T cover exact TQB handoff, teacher/student semantics, known historical shortcuts, proposal/weighting, F6–F9 obligations, joined runtime, EMA schedule, checkpoint/source provenance, model geometry, RNG/packing/hardware, stability/collapse, inherited falsifiers, downstream certification, runtime eligibility, independent training eligibility and explicit owner authorization.

**No-repeat coverage:** V4 active tests and V5 active tests are named as inherited suites. Historical target-identity discovery, zero-gradient archaeology, QID defect, FULL104 census, context sensitivity and defective x4 estimator are not scheduled for rediscovery.

**Authority coverage:** Every package is receipt-bound; no historical PASS or component GREEN promotes downstream/training authority. `DOWNSTREAM_CERTIFIED`, runtime eligibility, `TRAINING_ELIGIBLE` and `TRAINING_AUTHORIZED` remain separate.

**Changed-input coverage:** The exact TQB/current runtime creates new identities for teacher target/evidence, student restriction, masking, query mechanism, scientific weighting, proposal, EMA schedule, model registry, checkpoint and regression battery; these are requalified rather than inherited wholesale.

**Current execution state:** Plan only. Do not implement before Task 0 independent acceptance and prospective adoption of this downstream plan/amendment.
