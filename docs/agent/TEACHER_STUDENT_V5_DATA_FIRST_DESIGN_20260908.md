# Teacher/Student V5 — data-first successor design

Date: 2026-09-08

Status: `PROSPECTIVE_DESIGN_ONLY__NO_TRAINING_AUTHORITY`

## Governing principle

The dataset defines support and estimability. The pipeline may select, pack, mask, weight, or decline to estimate, but it may not require unsupported observations or mechanics-sample geometry to exist.

V5 preserves V4 as an immutable audited baseline. V5 is a successor data-interface/schedule design, not a mutation of V4 review bytes.

## Exact data authority used for this design

- reader metadata SQLite SHA-256: `a771f08be31a840b5472448c438a153fbca7de93ba2ed31fe692eaeda02e6913`
- operator support CSV SHA-256: `1814a22c8ae01ee94a6fe132546a029af01a7d762384d53c152f37cb545787c1`
- historical 3,292-cell mechanics inventory SHA-256: `7ac13973162a46cafa5baa24c5bea14beb64bd5859e8f58900801eee07083a30`
- derived profile: `READER_FIT_DATA_GEOMETRY_PROFILE_V1.json`

No pathology, oracle, reader-validation, DEV, or SEALED outcome is opened by the profile.

## What the full reader-fit data actually says

Reader-fit population:
- 4,553,407 cells
- 104 donors
- 42 operators
- HVS: 198,718 cells / 41 donors / 24 operators
- NPH52: 236,476 cells / 17 donors / 7 operators
- SEA_AD: 4,118,213 cells / 46 donors / 11 operators

Raw cell proportions are therefore ~4.36% HVS, 5.19% NPH52, and 90.44% SEA_AD, whereas donor proportions are ~39.42%, 16.35%, and 44.23%. Cell-uniform and donor-primary objectives are not interchangeable.

### Donor×operator support

There are exactly 1,400 reader-fit donor×operator combinations.

Full reader-fit group size:
- min 1
- p5 4
- p25 46
- median 228
- p75 3,169
- p95 ~16,498
- max 42,209

1,361/1,400 groups (97.21%) have at least 3 cells and contain 99.9987% of reader-fit cells.

The historical 3,292-cell mechanics inventory also spans 1,400 donor×operator combinations, but intentionally contains only 1–5 cells per combination (median 2); 72.93% of those sampled groups have fewer than 3 cells. **That mechanics distribution is a subsampling artifact and cannot define production relational geometry.**

### Measurement support

Measured scalar support differs strongly by source/operator:
- HVS: exactly 18,736 measured scalar addresses/operator
- NPH52: 30,294–34,405, median 32,445
- SEA_AD: exactly 35,076

Under the historical 40% within-support mask, exact visible counts are:
- HVS 11,242 = 27.26% of the 41,238-address universe
- NPH52 18,177–20,643 = 44.08–50.06%
- SEA_AD 21,046 = 51.04%

Thus “60% evidence” is only a within-operator statement. V5 must always report both within-support and universe-relative evidence.

## V5 architecture boundary

### Preserve as model/scientific invariants

- canonical 41,238-address identity namespace
- continuous measured scalar value semantics
- structurally unmeasured != measured zero
- IPB width 160 / 6 blocks / 4 heads unless separately re-qualified
- EMA teacher has no gradients and moves only after a proved optimizer step
- scale-free anchored triplet ordering as the prospective relational target object
- direct 160-D cell_state for learned-geometry qualification
- no learned locality selector
- no nearest-third hard-local objective
- no production nearest-half fraction inherited from TD59
- no protected-population access

### Reclassify as qualification mechanics, not production data geometry

The historical values below may remain exact for a bounded u0→u40 mechanical qualification if that lane is separately authorized, but V5 does not permit them to become full-reader production constants by inheritance:

- effective batch 128
- microbatch 8
- 4 masked views/cell
- 40% within-support hidden fraction
- 16 target blocks
- 205-update historical horizon / 40-update qualification horizon
- mechanics replay cap 8

The current source name `PRODUCTION_CONFIG` is therefore semantically too strong for these recovered mechanics values. A V5 implementation should separate `QualificationConfig` from a full-reader `ProductionScheduleAuthority`.

## Data-first schedule decomposition

V5 splits one “batch” into two independent authorities.

### 1. Scientific cell-selection authority

Defines which reader-fit cells contribute to an optimizer update and their scientific weights. It must explicitly state whether the intended training estimand is cell-weighted, donor-weighted, source×donor-weighted, or another prospectively justified estimand.

The 90.44% SEA_AD raw-cell share makes this explicit choice mandatory; accidental cell-uniform training is itself a weighting decision.

No compute constraint may silently change the selected scientific cell set or its weights.

### 2. Compute-packing authority

Takes the already-frozen update cell set and partitions it into deterministic microbatches according to actual operator support/token cost. Packing may reorder execution only through a frozen deterministic rule and may not change scientific weights.

No default token budget is supplied by V5. It must be calibrated on the actual GPU/runtime and then frozen before execution.

## Canonical packed-token path

The existing encoder has no positional encoding. Invalid genes are masked from key/value contribution, and valid gene/cell outputs are permutation-equivariant. Therefore structurally unmeasured teacher tokens and hidden/unmeasured student tokens are computational baggage rather than scientific observations.

Prospective V5 packed execution:
- teacher: process only MEASURED_SCALAR canonical IDs for the operator
- student: process only visible MEASURED_SCALAR canonical IDs for the exact frozen mask view
- gene IDs remain canonical 0..41,237 IDs; there is no remapping of biological identity
- target block query identities remain canonical IDs
- teacher block gather uses an explicit canonical-ID -> packed-position map

A local architectural equivalence probe across HVS/SEA_AD support showed valid cell/gene states agree with dense execution to ~1e-6 in eval mode, and the complete block-JEPA loss agrees to <=2.4e-7 in the tested cases. This is evidence for the algebraic path, not execution authority. Training-mode dropout/RNG invariance must still be solved and attacked before packed execution can become active.

At reader-fit cell weighting, teacher + four historical-60%-visible student views would process about 56.5% of the dense token positions if packed, a theoretical ~1.77x token-volume reduction before overhead. Do not freeze this estimate as a speed claim; measure it on the target GPU.

## Loss accumulation under variable microbatches

The current formula gives each microbatch equal weight by dividing each local mean loss by `views * microbatch_count`. That is correct only when all microbatches have equal target-element counts.

V5 requires exact global-mean accumulation:

`weight_mb = target_elements_mb / total_target_elements_in_update`

and the local mean loss is multiplied by that weight. If block count/size later varies, normalization follows actual decision-bearing target elements rather than microbatch count.

This prevents support-aware packing from silently changing the scientific loss weighting.

## Relational support and triplets

V5 treats donor×operator groups as ragged.

A group with <3 selected cells is `RELATIONAL_NOT_ESTIMABLE` for anchored triplets in that update; it may still contribute to base JEPA. It does not invalidate the whole update.

Full-group exhaustive triplet enumeration is forbidden for production-sized groups. At the full reader-fit median group size 228, exhaustive anchored triplets would be 5,848,428; at the max group size 42,209 it would exceed 37 trillion.

Therefore relational training, if later authorized, must use an externally frozen finite triplet budget/sampling authority or exact pre-frozen triplets. Group size alone may not determine objective weight.

Qualification semantics remain distinct: TD57B/TD59/TD60 use their exact frozen triplets/nulls and are not replaced by this training sampler.

## Null estimability

A fine matched-null stratum with <2 cells cannot be deranged. V5 converts that condition from a global exception into an explicit per-stratum estimability state.

Any allowed fallback/coarsening hierarchy must be frozen prospectively and outcome-blind. If no authorized fallback exists, those cells are `NULL_NOT_ESTIMABLE`; they do not make unsupported matches appear.

## Exposure-aware optimizer/EMA semantics

Per-update parameters become data-dependent if update size changes. V5 therefore forbids silently carrying a per-step training horizon or EMA timescale from the mechanics corpus into full-reader training.

For reference only:
- u40 at 128 cells/update = 5,120 presentations = 0.112% of one reader-fit cell pass
- u205 = 26,240 presentations = 0.576% of one reader-fit cell pass
- EMA momentum 0.996 has a half-life ~172.94 updates, or ~22,136 cell presentations at batch 128

These are mechanics-scale quantities, not a full-reader training schedule. A future production authority must specify schedule/EMA semantics in exposure units as well as update units.

## Required V5 gates before any external review candidate

1. Freeze and independently replay `READER_FIT_DATA_GEOMETRY_PROFILE_V1`.
2. Implement the qualification-vs-production configuration split without weakening V4 historical replay.
3. Implement packed canonical-token execution behind an inactive flag/module.
4. Prove dense-vs-packed valid-output equivalence with dropout disabled and design a deterministic training-mode RNG policy.
5. Implement exact target-element-weighted accumulation for variable microbatches and attack it against equal-size and unequal-size partitions.
6. Replace equal-size relational batch validation with ragged estimability + externally frozen finite triplet authority.
7. Define/freeze full-reader scientific sampling estimand and schedule from reader-fit capacities; do not infer it from mechanics sample counts.
8. GPU-measure token budget and memory; freeze compute-packing limits independently of the scientific sampler.
9. Build a V5 self-contained package and repeat source/test/package/CI/clean-room attacks.
10. Only then request new external review.

## Current authority

This document and the V5 prototype code are design/proof artifacts only.

`training_authorized = false`

`successor_u0_materialization_authorized = false`

`td60_execution_authorized = false`
