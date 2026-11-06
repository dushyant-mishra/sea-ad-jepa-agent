# Downstream qualification evidence-reuse guide V1 — 2026-10-14

Status: `READ_FIRST_BEFORE_DOWNSTREAM_QUALIFICATION__NO_TRAINING_AUTHORITY`

Machine source:
`results/target_discovery/unified_qualification_v1/DOWNSTREAM_QUALIFICATION_EVIDENCE_REUSE_MATRIX_V1.json`

## Why this exists

The downstream JEPA lane already contains years-worth of project-history-equivalent audit work in the current repository: causal training-mechanics failures, EMA chronology, source/protected-population firewalls, target/query semantic defects, masking review, V4 attack suites, V5 data-first weighting/proposal work, FULL104 geometry, measurement-shortcut analysis, and checkpoint/replay controls.

The merged lane must **reuse and rebind** that evidence, not recreate it.

The rule before every new downstream analysis is:

1. classify the proposed claim as `ALREADY_AUDITED`, `SUPERSEDED`, `OPEN`, or `CHANGED_INPUT_REQUIRES_REQUALIFICATION`;
2. identify the exact historical test/doc/branch that covers the old claim;
3. if inputs/authority did not change, inherit it with exact custody rather than recompute;
4. if TQB/current runtime changes the claim, port the historical attack to the exact new object and add only the delta assertion;
5. write a genuinely new test only where no historical equivalent exists.

## Primary historical test suites to reuse

### V4 mechanics/authority attacks

Exact active-test selection historically included:

- `tests/test_c2_mandatory_gradient_gate_v1.py`
- `tests/test_f1b_successor_attack_suite_v1.py`
- `tests/test_population_access_registry_v1.py`
- `tests/test_healthy_teacher_training_contract_v1.py`
- `tests/test_teacher_student_unified_runtime_v1.py`
- `tests/test_teacher_student_relational_v2.py`
- `tests/test_teacher_student_integration_freeze_v4.py`

These cover large parts of optimizer/gradient/moment guards, EMA ordering, checkpoint/source/runtime binding, population firewall, architecture/source freeze and relational mechanics. They are historical evidence, not current merged authority.

### V5 prospective/data-first suite

Historical active selection:

- `tests/test_teacher_student_data_first_v1.py`
- `tests/test_teacher_student_packed_equivalence_v1.py`
- `tests/test_teacher_student_v5_finite_triplets_v1.py`
- `tests/test_teacher_student_v5_inactive_update_reference.py`
- `tests/test_teacher_student_v5_numerical_boundary_v1.py`
- `tests/test_teacher_student_v5_objective_schedule_v2.py`
- `tests/test_teacher_student_v5_proposal_policy_v1.py`
- `tests/test_teacher_student_v5_rng_contract_v2.py`
- `tests/test_teacher_student_v5_rng_dense_packed_v2.py`
- `tests/test_teacher_student_v5_scientific_target_v2.py`
- `tests/test_teacher_student_v5_support_schedule_v1.py`

These cover support-aware data contracts, scientific target/proposal separation, packing invariance, finite triplets, objective weighting, identity-keyed RNG and inactive reference runtime mechanics. They do not authorize production execution.

### Sept. 15 target/shortcut lane

Branch:
`planning/v5-teacher-target-redteam-20260915`

Exact observed head:
`e342455ae841050282ef1932824e1aec971f1375`

Important inherited artifacts include:

- `analysis/v5_layer2_cross_view_shortcut_20260915/V5_LAYER2_CROSS_VIEW_SHORTCUT_CLOSEOUT.json`
- `analysis/v5_layer2_cross_view_shortcut_20260915/X_CROSS_VIEW_SHORTCUT_AUDIT_SPEC.json`
- `analysis/v5_layer2_cross_view_shortcut_20260915/Z_RESIDUAL_OVER_CONTEXT_SPECIFICATION.md`
- source/donor/QC/within-donor/LODO analyses and fixture validation under the same directory.

The corrected closeout demonstrated recurrent within-donor molecular-view signal beyond measured QC across all three sources but explicitly did **not** claim that the signal was biological or nontechnical. It also corrected the earlier pooled-context interpretation. Preserve those exact limits.

The historical audit index separately records the still-open target-address identity path through the predictor query; do not repeat discovery of that path. The new work is to close/qualify it under the exact TQB-bound target.

## Package-level reuse priorities

### A–C: target, teacher, student

Start from V5 target/proposal/data contracts and the corrected recoverability/teacher-private doctrine. New work is exact TQB binding, evidence rights, uncertainty and NOT_ESTIMABLE behavior.

### D–E: target identity and masking shortcuts

Do not rediscover that target identity can flow through the predictor query or that random masking can leave correlated partners visible. Port those historical attack concepts to the exact final target/masking policy and require prospective, outcome-blind controls.

### F: weighting/proposal/exposure

Reuse donor-primary target, p/q correction, proposal/horizon derivation and support schedule tests. Rebind to the exact current manifest/TQB and freeze exposure limits prospectively.

### G–I: representation, information channels, multimodal

Reuse F6–F9 custody and historical representation/visibility/context evidence. New work is exact downstream propagation and failure tests, not another broad representation archaeology pass.

### J–L: optimizer/EMA/checkpoint runtime

Reuse the V4 causal mechanics and V5 inactive-runtime/reference attacks. Run them against the new joined configuration and current protected registry. Do not claim success from historical V4 test results alone.

### M–O: model geometry, hardware/RNG, collapse/stability

Reuse current-registry derivation pattern, V5 RNG/packing tests, exact decay-only movement logic and relational noncompensation. New work is current architecture binding and prospective thresholds/authority.

### P: regression battery

Historical falsifiers are permanent. The regression battery should mostly be adapters that run existing attacks on the exact new TQB/runtime, plus genuinely new F7/F9/target-identity/masking attacks.

### Q–T: certification/eligibility/authorization

These are genuinely new authority objects. Historical mechanics are prerequisites and test inputs, not substitutes:

`DOWNSTREAM_CERTIFICATION_RECEIPT → RUNTIME_ELIGIBILITY_RECEIPT → TRAINING_ELIGIBILITY independent review → explicit owner TRAINING_AUTHORIZED`.

No earlier GREEN/PASS can skip this chain.

## No-repeat examples

Do not redo:
- zero-gradient causal archaeology;
- whether EMA can advance after skipped optimizer steps;
- whether V4 teacher/student/EMA code exists;
- the historical QID matched-null semantic defect;
- the defective x4-within estimator investigation;
- FULL104 cell/donor/operator/address census;
- visibility-only QC predictiveness;
- historical common-core rebuild;
- context-estimand sensitivity;
- discovery of the target-identity shortcut path;
- discovery that `.996` EMA was historical mechanics rather than current authority.

Re-run/requalify only when the exact current object changes the question, for example:
- new TQB target addresses;
- new teacher evidence rights;
- new student evidence dose;
- new masking policy;
- new model depth/protected registry;
- new EMA half-life;
- new GPU kernel/packing implementation;
- new checkpoint schema/source root;
- new downstream certification semantics.

## Current scientific status

There is a substantial historically audited teacher/student/EMA architecture, but there is no single current merged receipt that qualifies the exact final teacher target, student restriction, masking, predictor query, current architecture, EMA timescale, runtime, TQB consumption and leakage suite together.

Therefore:

`CURRENT_JOINED_TEACHER_STUDENT_EMA_FULLY_QUALIFIED = false`

`DOWNSTREAM_CERTIFIED = false`

`TRAINING_ELIGIBLE = false`

`TRAINING_AUTHORIZED = false`
