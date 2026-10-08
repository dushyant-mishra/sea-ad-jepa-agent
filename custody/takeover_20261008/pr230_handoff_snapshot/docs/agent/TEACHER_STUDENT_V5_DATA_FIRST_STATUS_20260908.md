# Teacher/Student V5 data-first planning status — 2026-09-08

Status: `V5_DATA_FIRST_MECHANICS_PROTOTYPE_PASS__SCIENTIFIC_TARGET_REPAIRED_V2__PROPOSAL_SCHEDULE_EXECUTION_UNFROZEN`

## Current decision boundary

V4 remains the immutable audited baseline. V5 is a prospective successor design/proof lane only. No V5 execution, training, successor-u0 materialization, TD60 execution, or protected-population access is authorized.

The V5 **scientific target** is now frozen separately from proposal and compute:
- base JEPA: `DONOR_UNIFORM__CELL_UNIFORM_WITHIN_DONOR_V1`;
- relational: `DONOR_UNIFORM__ELIGIBLE_ANCHOR_CELL_UNIFORM__SAME_OPERATOR_COMPARATOR_PAIR_UNIFORM_V2`;
- V1 equal-operator-group relational weighting is superseded: operator is now an admissibility boundary, with group mass proportional to eligible anchor-cell prevalence inside donor;
- source remains a domain/robustness stratum rather than automatic equal objective mass;
- base proposal `q`, finite triplet budget, evidence dose, token budget, update size, horizon, EMA half-life, and production GPU kernel remain numerically unfrozen.

## Exact data-first findings

Reader-fit support was profiled directly from frozen calibration authorities, reader-fit only:
- 4,553,407 cells, 104 donors, 42 operators;
- HVS 198,718 cells / 41 donors / 24 operators;
- NPH52 236,476 / 17 / 7;
- SEA_AD 4,118,213 / 46 / 11;
- 1,400 donor×operator groups, median size 228, maximum 42,209;
- 1,361/1,400 groups have >=3 cells and contain 99.9987% of reader-fit cells;
- the 3,292-cell mechanics inventory spans the same 1,400 groups but samples only 1–5 cells/group, so mechanics group size is explicitly non-production geometry;
- 17,186 canonical addresses are MEASURED_SCALAR in all 42 operators;
- historical 40%-hidden masking exposes 11,242 HVS addresses versus 21,046 SEA_AD addresses, so evidence is reported both within-support and relative to the 41,238-address universe.
- operator semantics are source-dependent: HVS/NPH52 operators are native-class-pure while SEA_AD operators are multi-class; equal operator-group scientific mass can upweight tiny groups by up to ~141.07x versus eligible-anchor prevalence, so that V1 relational weighting was rejected.

All current descriptive artifacts replay byte-identically from their frozen inputs:
- reader-fit geometry;
- relational support/capacity;
- scientific estimands V1 and V2;
- donor-proposal Pareto profile;
- support-overlap profile;
- support-overlap profile and deterministically generated 17,186-address common-core CSV (derived CSV hash-bound, not duplicated in the repository).

## Mechanics/proof closure

Current V5 prospective suite: **66/66 PASS** across the exact active selection.

Closed proof items:
- support-aware evidence telemetry and ragged relational estimability;
- singleton matched-null strata become explicit NOT_ESTIMABLE without inventing a cross-stratum match;
- finite anchored-triplet sampling by exact rank/unrank with explicit no-default budget and no exhaustive enumeration;
- scientific target `p`, proposal `q`, and compute packing are separate authorities with explicit `p/q` correction when needed;
- operator-support-aware microbatch packing has no default token budget and cannot alter the frozen cell set;
- weighted accumulation uses scientific/target mass rather than equal microbatch averaging;
- dense-vs-packed eval-mode teacher/student/predictor/block-loss equivalence is demonstrated on synthetic attacks;
- Philox4x32-10 V2 reference uses an injective address over run seed, update, stable 64-bit cell key, canonical token, feature, domain, view, layer, and site; tensor position/packing are absent from the address;
- the obsolete hash-based keyed-dropout proof helper was removed, leaving a single prospective RNG contract;
- train-mode dense-vs-packed state and gradient attacks pass closely under keyed dropout;
- ordinary positional dropout is retained as a negative control and is not packing invariant;
- an inactive CPU mechanics harness proves frozen-cell-set preservation, scientific weight-mass preservation, teacher-no-grad, one AdamW step, deterministic replay, and exact in-place EMA chronology;
- reference checkpoint/resume continuation now binds online/teacher/predictor/optimizer state plus next-update and presentation cursors; uninterrupted two-update execution and save/restore continuation are exact in the reference harness;
- exposure-based EMA semantics are defined as a half-life in presentations, with no production half-life selected;
- numerical-boundary attacks show tiny floating reduction-order differences can be amplified by AdamW near zero, so packed V5 is explicitly **not** a bitwise/statewise continuation of V4 and must receive its own mechanical qualification.

## Scientific weighting/proposal status

Raw cell-uniform sampling would give SEA_AD ~90.44% of base objective mass. The frozen donor-primary target instead treats the donor as the biological replicate.

Proposal remains a compute/statistical-efficiency decision rather than scientific mass. The frozen Pareto profile shows:
- raw cell-uniform proposal for donor-uniform target: ESS ~9.68%, importance-weight ratio ~2,149.5×;
- source-uniform/cell-uniform-within-source proposal for donor target: ESS ~40.58%, ratio ~296×;
- mixture proposals can improve ESS further but increase repeated exposure of cells from the smallest donors.

No mixture alpha is selected. Proposal must be frozen only after the intended presentation horizon/exposure limits are known.


Additional proposal closure:
- relational proposal is frozen separately as `DIRECT_DONOR_ANCHOR_CELL_TRIPLET_TARGET_PROPOSAL_V2`; it samples donor -> eligible group proportional to eligible cell count -> uniform anchored triplet, exactly matching relational V2 without importance correction or O(n^3) capacity weighting;
- base proposal remains numerically and derivationally unfrozen. The earlier `EXPOSURE_CONSTRAINED_DONOR_TARGET_MIXTURE_V1` remains an admissible source/exposure subfamily, but is no longer treated as the complete final derivation rule;
- a new descriptive coverage profile compares direct donor-target, source-uniform, and donor/operator-coverage proposals without selecting any of them; source-uniform strongly lowers worst repeated exposure, while operator-coverage dramatically improves minimum donor×operator coverage but can oversample tiny groups;
- final base `q` may only be derived after total presentations, repeated-exposure limit, importance-weight/proposal conditioning, and minimum donor×operator coverage requirements are frozen prospectively; exact `p/q` correction remains mandatory whenever `q != p`;
- the existing source-mixture algebra still independently round-trips all 104-donor Pareto points and remains available as a tested candidate subfamily.

## Common-core view status

The exact 17,186-address all-operator common measured core is an admissible `COMMON_CORE_ANCHOR` view family and is aligned with the support basis used in TD59. It does **not** replace native-support information. A prospective student schedule may combine:
- `COMMON_CORE_ANCHOR` for equal-availability molecular evidence;
- `NATIVE_SUPPORT_COVERAGE` for operator-specific measured information.

Visible gene count, target count, view-family weights, views/family, and block geometry remain unfrozen.

## Remaining gates before a V5 external-review candidate

1. Freeze proposal `q` only after an explicit training-presentation horizon and repeat/exposure limits are prospectively chosen; do not choose alpha from post-training outcomes.
2. Implement/review an optimized GPU Philox keyed-dropout kernel against the exact V2 CPU reference and deterministic test vectors.
3. Integrate the inactive packed/weighted mechanics into a bounded V5 mechanical-qualification runtime and re-run mandatory gradient/optimizer/EMA/checkpoint attacks as V5 authority.
4. GPU-calibrate explicit token/memory budget on target hardware; compute packing remains downstream of science.
5. Freeze evidence/view/block numerical schedule from the full reader-fit support profile, not the mechanics sample or 50k locality experiments.
6. Freeze finite relational triplet budget/presentation policy as a variance/compute quantity; group capacity must never become scientific weight.
7. Freeze training presentation horizon and EMA half-life in exposure units.
8. Build a self-contained V5 package, clean-room replay it, run V4 regression + V5 prospective suites in CI, and only then request independent external review.

Current authority remains fail-closed:

`training_authorized = false`

`execution_authorized = false`

`successor_u0_materialization_authorized = false`

`td60_execution_authorized = false`
