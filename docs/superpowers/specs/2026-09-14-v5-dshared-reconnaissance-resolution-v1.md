# V5 D_shared reconnaissance resolution V1

Status: `PROSPECTIVE_RESOLUTION_AFTER_OUTCOME_BLIND_RECONNAISSANCE__NO_D_SHARED_OUTCOME_ACCESSED`

Date: 2026-09-14

Branch: `repair/v5-dshared-authority-v2-20260914`

## Scope

This document resolves the authority consequences of the outcome-blind FULL104 feature-lineage and matching-state reconnaissance. It does **not** authorize D_shared execution, D_private, D_obs, training, protected-data access, TD60, or relational activation.

The frozen D_shared Authority V2 remains immutable statistical provenance. Findings below may require a successor execution/null authority, but V2 is not edited in place.

## Recovered feature lineage

The recovered derivation chain is:

`authenticated expression block manifest -> multiview feature builder + sketch projections + multiview feature contract -> 8,915 multiview blocks -> full feature-matrix assembler -> validation/publisher -> A_full/B_full/A_views/B_views`

The historical feature package remains content-addressed by:

- feature package root `c9a6ede6f33a4a9d4ce22cde0f1a8c0fb5e7e039bac3df364325c778487329ef`
- multiview root `d6f70ee1bca777f3d2cbd89dd560395cc46ec25f6a648ae4ba0fd6e77c1c2cf1`
- authenticated expression block manifest `66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29`

The heavy-machine report states that all published feature artifacts were re-hashed byte-identically to their manifests, row coverage/order closed over 4,553,407 rows, and no pathology/protected/checkpoint/training outcome was used.

## Ruling F1 — unresolved original writer hash

The historical manifest's original writer-code SHA cannot currently be resolved to a surviving file. This is a provenance-record gap, not evidence that the published 93 GB arrays changed.

It MUST NOT be represented as `deterministic_reproduction_passed=true` for the original writer.

A mechanics-repair certification may instead state all of the following explicitly:

- original writer hash unresolved;
- current/recovered producer and validation scripts are hash-bound;
- the validation-only patch is hash-bound and shown to alter validation memory mechanics only;
- every published feature artifact is byte-verified against its frozen manifest;
- semantic transform equivalence is independently evidenced;
- exact original-writer byte replay is **not** claimed.

This permits provenance certification only. It does not by itself authorize the feature geometry for D_shared.

## Ruling F2 — historical views/mask constants

The historical feature construction uses four subviews and visible fraction 0.60 (equivalently mask fraction 0.40).

These values directly determine the D_shared measurement representation. Therefore they are **not** silently promoted from historical V4 mechanics into current-V5 biological measurement authority.

The existing matrices may be certified as historical/provenance/mechanics artifacts, but final D_shared use requires a separate outcome-blind measurement-geometry qualification that either:

1. prospectively qualifies this exact four-view / 0.60-visible construction at real FULL104 geometry using the frozen negative/positive-control framework; or
2. replaces it with a prospectively selected/rebuilt current-V5 feature geometry before any D_shared outcome is opened.

No D_shared result may be used to choose between those paths.

## Ruling F3 — stale absolute paths

Absolute historical Windows staging paths are non-authoritative. Artifact resolution is by logical artifact name plus exact frozen content hash/root. Relocation to a current directory is lawful only when every resolved file re-hashes to the frozen manifest.

Frozen policy identifier:

`CONTENT_HASH_AND_LOGICAL_NAME_AUTHORITATIVE__ABSOLUTE_PATH_INFORMATIONAL_ONLY_V1`

## Reconnaissance evidence binding

A reconnaissance receipt MUST bind actual evidence, not only assert that diagnostics ran.

For every allowed diagnostic it MUST contain a SHA-256 evidence digest, plus a deterministic root digest over the complete diagnostic-evidence map. Missing evidence for any declared diagnostic is a STOP.

Reconnaissance remains outcome-blind and cannot carry D_shared rank/effect/pass fields.

## Matching-state finding

Frozen V2 requires exact discrete states for:

`(donor, operator, Q_DEPTH, Q_DETECT, support_measurability)`

The heavy-machine report found:

- donor: discrete;
- operator: discrete;
- `Q_DEPTH=log1p(source_library)`: stored as continuous float32 per cell;
- `Q_DETECT=nonzero/max(scalar,1)`: stored as continuous float32 per cell;
- support measurability: deterministic function of operator and therefore redundant in the matching key.

Under V2 as written, execution therefore stops with `STOP_D_SHARED_MATCHED_NULL_STRATIFICATION_UNSPECIFIED`.

## First successor resolution path — lossless discrete preimages

Before inventing bins or replacing the null, test whether the continuous stored descriptors have exact discrete generating states.

### Q_DEPTH

Candidate discrete state:

`Q_DEPTH_COUNT = round(expm1(Q_DEPTH))`

This is admissible only if reconstruction using the frozen writer's numeric semantics reproduces every stored Q_DEPTH value exactly under a prospectively specified byte/tolerance rule and the recovered counts are valid nonnegative integers.

### Q_DETECT

If operator-level scalar support count is frozen and integral, candidate discrete state:

`Q_DETECT_COUNT = round(Q_DETECT * max(SCALAR_SUPPORT_COUNT, 1))`

This is admissible only if reconstruction reproduces every stored Q_DETECT value exactly under the same prospective numeric rule and recovered counts are valid integers in the lawful support range.

### Required occupancy report

Without inspecting D_shared outcomes, report the complete stratum-size distribution for:

`(donor, operator, Q_DEPTH_COUNT, Q_DETECT_COUNT)`

including cells and strata at sizes 1, 2-3, 4-7, and >=8, plus min/median/p95/max size and the unconditional fraction of cells in singleton/nonpermutable strata.

`support_measurability` is retained as a redundancy-audit field but is not duplicated in the key if exact identity with operator is proven.

### Consequence

If both preimages are lossless, they may be frozen in a successor matching-state representation contract. This is recovery of generating discrete states, not post-hoc binning.

If either preimage is not lossless, or if subsequent real-geometry measurement qualification shows that this exact matching construction cannot discriminate signal from technical dependence, V2 matched-null execution remains closed and a new V3 continuous-nuisance null must be designed prospectively.

## Forbidden shortcuts

The following are forbidden before D_shared outcome access:

- arbitrary quantile/equal-width bins introduced without a successor authority;
- treating support measurability as an independent matching variable after operator redundancy is proven;
- declaring original-writer deterministic replay when the original writer hash is unresolved;
- treating four views / mask 0.40 as current-V5 authority merely because the historical arrays are byte-valid;
- using stale absolute paths as provenance authority;
- opening any D_shared rank, effect, null distribution, held-donor score, or pass/fail result to choose a repair.

## Current terminal

`STOP_REAL_D_SHARED_PENDING_FEATURE_GEOMETRY_QUALIFICATION_AND_MATCHING_STATE_RESOLUTION`

Hard boundaries remain:

- `d_shared_real_outcome_access_authorized=false`
- `d_private_execution_authorized=false`
- `d_obs_execution_authorized=false`
- `training_authorized=false`
- `protected_data_authorized=false`
- `td60_authorized=false`
- `relational_target_activation_authorized=false`
