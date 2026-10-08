# V5 base-training estimand reconciliation — 2026-09-15

Status: `OPEN_RECONCILIATION_RESOLVED_TO_EXISTING_SCIENTIFIC_TARGET__NO_TRAINING_AUTHORITY`

Classification: `OPEN_RECONCILIATION__NOT_NEW_ESTIMAND_DISCOVERY`.

## Recovered authority

The project already contains `TEACHER_STUDENT_V5_SCIENTIFIC_TARGET_AUTHORITY_V2`, which repaired an earlier operator-balanced target and reaffirmed the base JEPA scientific population target as `DONOR_UNIFORM__CELL_UNIFORM_WITHIN_DONOR_V1` over `reader_fit`. Raw cell count does not set donor mass; operator does not set base scientific mass; source is a domain/robustness stratum rather than automatic objective mass.

The full-reader proposal/weight/restart closure later executed the same target over 4,553,407 reader-fit cells and 104 donors using `p_i = 1/(D*n_d)` with exact `p/q` correction when proposal mass differs.

No explicit later supersession of that scientific-target authority was recovered. The later September-15 handoff statement that the base-training estimand was open is therefore treated here as a governance/scope inconsistency, not as permission to rediscover the population target from later representation metrics.

## Current-V5 binding

Current V5 recovers the existing scientific target through two immutable artifacts:

- `V5_RECOVERED_BASE_TRAINING_SCIENTIFIC_WEIGHT_LAW_20260915.json`
- `V5_BASE_TRAINING_ESTIMAND_AUTHORITY_20260915.json`

The recovery binds exact historical scientific-target and full-reader replay content hashes, the authenticated reader-fit population root, the current support-estimability root, and the measurement-support eligibility root.

## Anti-carryover boundary

This reconciliation does **not** inherit or freeze historical proposal coefficients, source-mixture coefficients, operator-coverage coefficients, presentation horizon, affine order, physical packing sizes, optimizer settings, model/rank geometry, masking geometry, seeds, or EMA timescale. Proposal `q`, schedule, packing, geometry, masking, optimizer mechanics and EMA remain separate authorities.

The dimension-qualification equal-donor estimand is **not** used as the source of this decision. The recovered source is the pre-existing base scientific-target authority itself. Layer-2 empirical/source-uniform/donor-primary comparisons remain diagnostics and cannot replace the scientific population target based on representation performance.

`TRAINING_OFF`

`NO_D_SHARED_OUTCOME_EXECUTION_OR_INSPECTION`
