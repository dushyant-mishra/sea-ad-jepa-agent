# Teacher/Student Relational Extension V1 — Prospective Design

Date: 2026-09-08

Status:

`PROSPECTIVE_RELATIONAL_EXTENSION__NOT_IN_CURRENT_TRAINING_OBJECTIVE__EXTERNAL_REVIEW_REQUIRED`

This document is intentionally additive to the frozen healthy-teacher base. It does **not** modify the currently frozen u0→u40 training objective, population, schedule, masking geometry, optimizer, EMA, or execution authorization.

The purpose is to make the next teacher/student generation capable of learning and evaluating **relational biological geometry**, not only per-cell hidden-block targets.

## 1. Representation used by the relational objective

V1 uses the canonical 160-dimensional teacher and student **`cell_state` directly**.

No learned relational projection head is active in V1.

Reason:

- the teacher and student already inhabit the same 160-D encoder state space;
- adding a learned projection would create another trainable object and another route to apparent relational success;
- direct cell-state geometry is easier to audit, replay, and compare to D1 downstream estimation;
- a future learned projection requires a separate prospective contract and must not silently replace the direct-state V1 target.

Teacher state is detached/no-grad. Student state remains differentiable.

## 2. Exact relational loss

The differentiable relational loss is defined within frozen relational groups only.

For each donor×operator group:

1. subtract that group's cell-state mean from teacher and student states independently;
2. compute teacher pairwise Euclidean distances;
3. define one teacher distance scale as the median strictly-positive teacher pair distance over all eligible within-group pairs in the batch;
4. divide both teacher and student pairwise distances by that same teacher scale;
5. compute centered-state cosine-similarity matrices;
6. evaluate only upper-triangular within-group pairs;
7. compute:
   - Smooth-L1 loss on normalized pair distances;
   - Smooth-L1 loss on cosine similarities;
8. total relational loss is exactly:
   `0.5 * normalized_distance_loss + 0.5 * angle_loss`.

Neighborhood rank is **not** part of the differentiable loss. It is a non-differentiable qualification/reporting diagnostic using same-group k-nearest-neighbor overlap.

This prevents rank discontinuities from influencing gradients while still preserving a topology diagnostic.

Implementation:

`src/sea_ad_jepa/v4/teacher_student_relational.py`

## 3. Relational batch construction

Current frozen u0→u40 training continues to use its existing 128-cell schedule and is **not altered** by this document.

For a future relational-training promotion, V1 defines the candidate batch geometry:

- total batch: 128 cells;
- exactly 8 relational groups;
- exactly 16 cells per group;
- group key: `canonical_donor_id × operator_id`;
- no cross-group pair contributes to relational loss;
- groups smaller than the frozen minimum are ineligible rather than pooled.

The production schedule for this geometry has not yet been materialized from the full lawful population and therefore is not execution authority.

Before activation, a data-only schedule authority must show:

- exact eligible donor×operator groups;
- deterministic waterfill/cycling;
- exact cell identities and stable keys;
- replay cap;
- no same-update duplicates;
- donor/operator exposure balance;
- no reader-validation/oracle, DEV/SEALED, external holdout, or pathology access.

## 4. Fine-matched null

Relational qualification must prove more than preservation of coarse cell-type geometry.

The null is qualification-only and never used to select training examples.

Each real cell must be reassigned only within a **prospectively frozen fine stratum**. The final stratum authority must include at least:

- canonical donor;
- operator;
- frozen coarse cell-state/type identity;
- measurement-support bin.

Within each stratum, a deterministic no-fixed-point permutation is used.

The package currently freezes the permutation mechanic but **does not invent the coarse-cell-state or support-bin authority**. Those exact stratum bytes must be materialized and independently reviewed before real relational qualification.

Required comparison:

- real teacher↔student relational agreement;
- fine-matched-null teacher↔permuted-student agreement.

Coarse cell identity alone must not count as relational success.

## 5. Collapse prevention

Three exact geometry metrics are frozen:

1. within-group centered variance;
2. median within-group pairwise Euclidean spread;
3. entropy effective rank of centered cell-state singular-value power.

The active rule is fail-closed but has **no invented numerical threshold**.

Relational activation requires a separately frozen:

`RELATIONAL_COLLAPSE_CALIBRATION_V1`

containing teacher-relative lower ratios for:

- student/teacher variance;
- student/teacher spread;
- student/teacher effective rank.

The runtime then rejects if any value is:

- missing;
- nonfinite;
- nonpositive where positivity is required;
- below its prospectively frozen ratio.

No pooled rescue is allowed.

The calibration must be derived outcome-blind from lawful u0/reference geometry and reviewed before relational training is activated.

## 6. Evidence masking schedule

Evidence levels are exactly:

`20%, 40%, 60%, 80%, 100%`

with hidden fractions:

- 20% evidence → 80% hidden;
- 40% evidence → 60% hidden;
- 60% evidence → 40% hidden;
- 80% evidence → 20% hidden;
- 100% evidence → 0% hidden.

### Current frozen u0→u40 training

Training remains **60% evidence only**, matching the already-frozen 40% hidden target geometry.

This relational extension does not change that.

### Relational qualification

At u0 and reviewed checkpoints, relation-preservation diagnostics may be evaluated at all five evidence levels using no-grad/RNG-neutral evaluation.

100% is a mechanics/reference level only.

### Future multi-evidence training

A later reviewed continuation may use 20/40/60/80% as training conditions.

100% must never be treated as a hidden-target biological training dose because there is no hidden target at 100%.

No multi-evidence training is authorized by this V1 package.

## 7. Production population binding

Current healthy-teacher qualification remains bound to:

- 104 reader-fit donors;
- 3,292 frozen mechanics cells;
- 26,240 scheduled presentations;
- existing cap-8 schedule.

The project also has the lawful FULL104 reader-fit universe:

- 4,553,407 cells;
- 104 reader-fit donors;
- 42 operators;
- 41,238-address namespace;
- HVS, NPH52, SEA_AD.

Moving relational or block-JEPA training from the 3,292-cell mechanics corpus to the 4.553M-cell population is a **separate scale-up gate**.

Required before that move:

1. exact full-population membership/root;
2. exact production-loader source/root;
3. new deterministic dataset→donor→cell schedule generated from the full population;
4. relational donor×operator group eligibility audit;
5. replay/exposure caps derived for the full population rather than copied from the small mechanics corpus;
6. resource/memory qualification;
7. checkpoint/resume rehearsal;
8. independent review;
9. explicit execution authority.

No threshold, effective dimension, replay cap, or schedule statistic from the 3,292-cell corpus may be hard-coded into the 4.553M run without recomputation.

## 8. Relationship to existing F1 and D1

F1-A remains the frozen qualification framework. Its 20/40/60/80/100 evidence semantics are not changed.

D1 remains the estimation/ranking layer. Direct 160-D cell-state relational outputs are chosen in part so D1 can later estimate:

- program geometry;
- cell rankings;
- donor recurrence;
- source/operator heterogeneity;
- neighborhood structure;
- extreme relational tails.

Relational training success is not itself a biological claim.

## 9. Activation firewall

The following are explicitly false in this package:

- relational loss active in current production_update;
- relational loss weight added to current u0→u40 objective;
- relational batch schedule frozen;
- fine-matched real stratum authority frozen;
- collapse numerical calibration frozen;
- multi-evidence training authorized;
- 4.553M training authorized;
- real u1 authorized.

Promotion requires a successor source manifest, active tests, independent review, and execution binding.

## 10. Required external-review attacks

Before promotion, independently test:

1. changing only cross-group positions does not change relational loss;
2. changing within-group geometry does change loss;
3. teacher collapse is rejected;
4. student collapse below frozen calibration is rejected;
5. a singleton/undersized relation group cannot be silently pooled;
6. fine-matched null never crosses its frozen stratum;
7. fine-matched null has no fixed points;
8. coarse-type-only separation can be defeated by the fine null;
9. 100% evidence cannot enter hidden-target training;
10. current u0→u40 production_update remains byte-/behavior-equivalent with relational extension disabled;
11. 4.553M mode cannot run without a separately frozen full-population schedule/root.

Current terminal:

`RELATIONAL_EXTENSION_V1_MECHANICS_DEFINED__NOT_ACTIVATED__TRAINING_UNAUTHORIZED`
