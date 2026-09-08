# Teacher/Student Relational Extension V2 — Prospective Design

Date: 2026-09-08

Status:

`PROSPECTIVE_RELATIONAL_EXTENSION_V2__NOT_IN_CURRENT_TRAINING_OBJECTIVE__EXTERNAL_REVIEW_REQUIRED`

V2 supersedes the prospective V1 adjunct only. It does **not** modify the active Teacher/Student V4 source root, current u0→u40 objective, population, schedule, masking, optimizer, EMA, or execution authorization.

## Why V1 was superseded

Adversarial review found two fail-open mechanics in V1:

1. `relational_batch_contract(..., group_size=32, groups_per_batch=4)` could accept a 4×32 batch even though the frozen design requires exactly 8×16.
2. collapse health was aggregated across all relational groups, so sufficiently rich groups could rescue a collapsed donor×operator group, contradicting the no-pooled-rescue rule.

V2 closes both and also fail-closes undefined centered-state angles, non-exact evidence-level inputs, malformed group IDs, and empty donor/operator identities.

## Frozen V2 mechanics

### Representation

Direct teacher/student 160-D `cell_state`; no learned projection. Teacher is detached/no-grad; student is differentiable.

### Relational loss

Within eligible donor×operator groups only:

1. center teacher and student separately by group;
2. reject any eligible centered state with zero norm because its cosine angle is undefined;
3. require every eligible teacher group to have positive pairwise spread;
4. compute within-group upper-triangular Euclidean distances and centered-state cosine similarities;
5. use one teacher-set scale equal to the median strictly-positive teacher pair distance across all eligible within-group pairs in the batch;
6. loss remains exactly:
   `0.5 × SmoothL1(normalized pair distances) + 0.5 × SmoothL1(cosines)`.

Cross-group pairs never enter the loss. kNN overlap remains diagnostic only.

### Exact relational batch

There is no geometry override parameter in V2:

- exactly 128 cells;
- exactly 8 donor×operator groups;
- exactly 16 cells per group;
- donor and operator identities must be non-empty strings.

The full-population scheduler, cell identities, replay caps, exposure balance, and no-duplicate proofs remain separate activation prerequisites.

### Fine-matched null

Unchanged in principle: deterministic no-fixed-point permutation within externally frozen fine strata. The real stratum authority remains unresolved and training remains inactive.

### Collapse prevention — per group, no pooled rescue

For every eligible relational group separately, compute:

- centered variance;
- median upper-triangular pairwise spread;
- entropy effective rank.

Teacher and student must have exactly the same health-group set. For every group and every metric, reject missing/nonfinite/nonpositive values and reject student/teacher ratios below the separately frozen `RELATIONAL_COLLAPSE_CALIBRATION_V1` threshold. One healthy group cannot rescue another collapsed group.

No numerical calibration thresholds are invented by V2.

### Evidence schedule

Exactly 20/40/60/80/100% evidence with hidden fractions 80/60/40/20/0%. Inputs must be exact integer levels; fractional values are not silently coerced. Current u0→u40 training remains 60% evidence / 40% hidden only. 100% remains reference/mechanics only and cannot become a hidden-target training dose.

### Population scale-up

The 4,553,407-cell FULL104 move remains a separate scale-up gate requiring its own full-population membership/root, scheduler, donor×operator eligibility audit, replay caps, resources, checkpoint rehearsal, review, and execution authority. No small-corpus threshold or schedule statistic may be copied without recomputation.

## Required external-review attacks

1. 4×32 cannot satisfy the 8×16 batch contract, including via keyword override.
2. one collapsed teacher group is rejected even when all other groups are rich.
3. one student group below calibration is rejected even when all others pass.
4. a centered zero-norm state is rejected rather than assigned an arbitrary cosine.
5. cross-group translations do not change relational loss.
6. within-group geometry changes do change loss.
7. fine-matched null stays within stratum and has no fixed points.
8. fractional evidence percentages do not coerce to a supported level.
9. malformed/non-integer group IDs and empty batch identities fail closed.
10. current V4 `production_update` remains unchanged and does not import/call V2.
11. 4.553M execution remains impossible without a separate reviewed full-population schedule/root and explicit authority.

Current terminal:

`RELATIONAL_EXTENSION_V2_MECHANICS_DEFINED__NOT_ACTIVATED__TRAINING_UNAUTHORIZED`
