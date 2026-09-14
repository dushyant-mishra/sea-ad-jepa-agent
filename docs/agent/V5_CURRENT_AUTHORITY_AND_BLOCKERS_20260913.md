# V5 current authority and blockers — 2026-09-13

Status: `FULL104_AND_PRECISION_CROSS_BINDING_PASS__D_SHARED_PRODUCTION_EXECUTOR_NEXT__NO_TRAINING_AUTHORITY`

This is the current successor ledger. It supersedes the *status* portions of older blocker documents while preserving them as historical provenance.

## Closed current-V5 prerequisites

1. Historical FULL104 physical bytes were relocated and authenticated.
2. Hardened FULL104 binder replay passed physical/identity closure over 4,553,407 cells, 104 donors, 42 operators, 42 matrices, 8,915 blocks, and 41,238 molecular addresses.
3. `V5_FULL104_DIMENSION_INPUT_ARTIFACT_V1` was sealed.
4. Prospective dimension precision authority was frozen before current-V5 dimension outcomes.
5. Frozen precision authority SHA-256:
   `cc4ac4d5116fa81990f1c3bd0497fc578eda86bb2d7d3cd2747abcf7ffcf9428`.
6. Sealed FULL104 dimension-input artifact SHA-256:
   `eb1264489306413fb57316abe7f70205a771248881302d8c867c70b69273f1ad`.
7. FULL104 ↔ precision pre-outcome bridge passed with all six FULL104 parents matching independently.
8. Cross-binding receipt SHA-256:
   `eccc30f9f5d01f7905a0740982d678d0ce45532a08cd5a61c51f5448b63b3d3a`.
9. `.gitattributes` protects `docs/history/full104_v014_20260826/**` from EOL translation.
10. No D_shared, D_private, or D_obs current-V5 outcomes were inspected before this freeze/binding chain closed.

Repository verification at repair head `3e1164aa055d956dad09f44b05c1b05a9b14cf3a`:

- 223 tests passed;
- 17/17 frozen critical tests executed and passed;
- authority-source compilation passed.

## Immediate scientific blocker

`D_SHARED_PRODUCTION_METRIC_EXECUTOR_NOT_YET_AUTHORITY_BEARING`

The existing dimension-family script adjudicates supplied metric rows. Production authority requires a real executor that itself computes the D_shared evidence from authenticated FULL104 under the frozen precision plan.

Required decision-bearing D_shared quantities:

1. `shared_matched_null_exceedance`
2. `shared_subspace_stability`
3. `shared_held_donor_cross_view_predictability`
4. `shared_independent_view_agreement`
5. `shared_measurement_shortcut_increment`

The producer must internally enforce:

- exact FULL104/cross-binding/precision parents;
- full-reader-fit execution where required;
- full-refit null geometry;
- precision-authority per-quantity replicate counts;
- deterministic `SHA256_PARENT_QUANTITY_REPLICATE_INDEX_V1` replay;
- unconditional decision populations;
- estimator failure = nonqualifying + separately reported;
- no survivor-only intervals;
- no pathology/protected/checkpoint-outcome adaptation;
- no historical V4 executor promoted as final authority;
- raw evidence sealed before rank adjudication.

## Still-open downstream blockers

### D_private and D_obs authority

Their rules were frozen prospectively as candidates, but they still require explicit independent review/finalization before current-V5 numeric execution. D_private remains closed until exact D_shared is frozen.

### Dataset-derived runtime geometry

After dimensions freeze, derive proposal weights, schedule, packing/restart, model width/depth, microbatch/effective batch and related runtime geometry from authenticated data and predeclared constraints. Historical V4 constants are not inherited authority.

### Executable anti-cheat evidence

The rejection-gate calibration layer cannot rely only on caller-shaped reports. Each canonical gate requires executable minimally-valid/minimally-invalid control producers with raw outputs hashed before summary adjudication.

### Production-geometry CUDA runner

A validator exists, but a real runner must execute the exact derived geometry on real FULL104 data and prove protected gradients, movement beyond decay, both Adam moments, EMA, and atomic checkpoint/telemetry commit.

### Environment authority

Heavy-machine V5 suites require the documented `sea-ad-jepa-v3` environment because the package import path includes torch. Add an executable environment preflight so inability to collect tests cannot be mistaken for a green result.

### External/confirmation cohort governance

Freeze cohort roles before any outcome access. Validation/transport outcomes may not flow backward into dimension, architecture, threshold, locality, masking, schedule, or training choices. See `V5_EXTERNAL_COHORT_ROLE_REGISTRY_20260913.json`.

### Artifact lineage downstream

Continue exact-byte parent binding through proposal weights, packing/restart, production-GPU receipts, raw gate evidence, base-learning qualification, teacher checkpoint authority, TD60, and relational qualification.

### Branch governance

A branch-to-unique-content/ancestry matrix is still needed before historical branch cleanup. This is operational governance, not a blocker for D_shared implementation.

## Hard boundaries

`training_authorized = false`

`protected_data_authorized = false`

`numeric_dimensions_authorized = false`

`td60_authorized = false`

`relational_target_activation_authorized = false`

`external_validation_outcomes_authorized_for_design = false`

## Current sequence

`D_shared executor -> real D_shared -> freeze D_shared -> finalize/review D_private -> D_private -> finalize/review D_obs -> D_obs -> schedule/proposal/packing/model geometry -> executable anti-cheat controls -> production CUDA qualification -> bounded base learning -> lawful EMA teacher -> TD60 -> relational student qualification -> internal biology validation -> matched-context controls -> external transport -> integrated review -> possible later training authority`
