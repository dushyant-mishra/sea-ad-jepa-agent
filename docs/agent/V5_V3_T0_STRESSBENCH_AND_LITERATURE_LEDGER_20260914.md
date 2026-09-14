# V5 V3 / T0 STRESS-BENCH + LITERATURE LEDGER — 2026-09-14

## Purpose

This file is the current record for substrate-independent V3/T0 mechanics built while Claude/heavy-machine work rebuilds the FULL104 feature substrate. It is intended for new chats and other agents so they do not restart from stale V2 assumptions.

Repository: `dushyant-mishra/sea-ad-jepa-agent`

Working branch: `repair/v5-v3-null-t0-stressbench-20260914`

Verified head before this ledger commit: `0e770cdd708228c3628ef0e2d29bd5fee1757547`

Exact-head GitHub Actions run: `34885448123`

Verification result:

- `305 passed`
- `0 failed`
- critical execution guard: `45/45 passed`
- authority-source compilation: PASS

The final ledger commit itself must be re-fetched before any later current-state claim.

## Governing scientific rule

`DATA -> SUPPORT/ESTIMABILITY -> SCIENTIFIC ESTIMAND -> PRODUCTION GEOMETRY -> MODEL`

Current refinement:

`UNDERSTAND_FULL104_DEEPLY__KEEP_FINAL_D_SHARED_HYPOTHESIS_TEST_SEALED`

Hard boundaries remain:

- training OFF
- protected/pathology confirmation OFF
- D_shared real outcome OFF
- D_private OFF
- D_obs OFF
- TD60 OFF
- relational target activation OFF
- external validation outcomes must not feed design

No mechanics PASS in this ledger grants biological authority.

## Critical upstream FULL104 finding from Claude

All 14 outcome-blind FULL104 reconnaissance diagnostics were completed without D_shared outcome access.

Evidence root:

`629e860ac1b6bae2ef80512b9c9f9e0bf93b75b8d9077305cb5717320cdf26be`

Artifact:

`V5_FULL104_RECON_EVIDENCE_V1.json`

Artifact SHA-256:

`552b220edcc0e05591cb3876b3ab0be58277c0c5fd8a111cdfe8d4b5ad6200da`

Key findings:

1. Q_DEPTH and Q_DETECT are losslessly recoverable to discrete counts across all 4,553,407 rows.
2. Support-measurability is exactly redundant with operator.
3. Exact V2 key `(donor, operator, Q_DEPTH_COUNT, Q_DETECT_COUNT)` is operationally degenerate: 99.911% of cells are singleton strata; maximum stratum size is 3.
4. Therefore the V2 matched-null is nearly an identity map and is not a meaningful negative reference.
5. Between-operator feature variance exceeds between-donor variance on the historical substrate.
6. Historical A/B are independent hash projections of the same 41,238-address molecular content, not genuinely disjoint molecular views.
7. Historical pooled covariance is singular; effective dimensionality is far below nominal 512.
8. Q_DEPTH and Q_DETECT are materially correlated with feature coordinates.

Interpretation:

`V2_MATCHED_NULL_TECHNICALLY_DEFINED__OPERATIONALLY_DEGENERATE`

This is not evidence that biology is absent. It is evidence that the control assay is invalid at exact matching resolution.

## Sequencing change now adopted

Do not design/freeze final V3 null against the historical A/B substrate.

Current order:

`authenticated FULL104 -> genuinely disjoint molecular views -> rebuilt V5 feature substrate -> outcome-blind structural characterization -> supported rank envelope -> operator/QC nuisance characterization -> V3 null design -> T0 falsification -> FULL104 measurement qualification -> only then D_shared`

Claude/heavy-machine lane was instructed to:

- derive a deterministic disjoint split of the 17,186-address common measured core;
- preserve operator-native information as a separate comparator channel;
- rebuild features from authenticated FULL104 blocks rather than relabel historical A/B;
- rerun structural spectrum/effective-rank/operator/QC diagnostics on the new substrate;
- characterize donor/operator/support-pattern exchangeability ingredients;
- characterize same-cell intervention feasibility;
- return hash-bound evidence only;
- NOT execute or inspect D_shared.

## T0 role

T0 remains closed as a biological result.

Terminal remains:

`T0_MEASUREMENT_PROCEDURE_NOT_QUALIFIED_AT_N28__BIOLOGY_UNRESOLVED`

T0 may now be used only as a retrospective method-development stress bench:

- it may reject a candidate V3 mechanism;
- it may not certify V5;
- it may not select V5 thresholds/ranks/nulls based on known T0 biology;
- it may not reopen protected/pathology confirmation;
- it may not convert permutation significance into a transportable effect-size claim.

## New substrate-independent mechanics implemented

### 1. Null mobility audit

Module:

`src/sea_ad_jepa/v5/null_mobility_audit_v1.py`

Purpose:

- validates caller-supplied blocked permutation as a full bijection;
- forbids cross-block moves;
- reports eligible/noneligible rows;
- reports actual changed/identity fractions;
- makes identity-null collapse visible;
- does not choose block definitions;
- cannot authorize D_shared/training.

Important red-team hardening:

- non-integral permutation indices rejected;
- NaN/out-of-range mobility thresholds rejected;
- singleton blocks remain in the population and are explicitly noneligible rather than silently dropped.

Authority:

`MECHANICS_ONLY__V3_NULL_NOT_FROZEN`

### 2. T0 -> V5 sandbox firewall

Module:

`src/sea_ad_jepa/v5/t0_v3_sandbox_firewall_v1.py`

Purpose:

- permits T0 falsification/mechanics evidence;
- prevents T0 from becoming V5 qualification or D_shared authority;
- preserves rare-tail refusal and T0 closeout semantics.

### 3. Same-cell technical intervention probe hardening

Module:

`src/sea_ad_jepa/v5/same_cell_technical_intervention_probe_v1.py`

The pre-existing numerical same-cell probe is now receipt-bound to:

- measurement parent SHA;
- intervention-plan SHA;
- explicit intervention strength;
- intervention frozen before execution;
- stable row identity;
- donor identity;
- operator identity;
- source identity;
- no D_shared/protected/pathology/training feedback.

Authority:

`MEASUREMENT_ROBUSTNESS_ONLY__NOT_D_SHARED_AUTHORITY`

This mechanism is currently treated as a measurement-robustness gate, not automatically the primary D_shared null.

### 4. Cross-fitted nuisance adjustment comparator

Module:

`src/sea_ad_jepa/v5/nuisance_adjustment_probe_v1.py`

Purpose:

- measures how much representation variance declared technical covariates predict under cross-fitting;
- supports explicit ridge strength supplied by caller;
- reports per-feature and aggregate cross-fit R2 plus residual variance ratios;
- remains a comparator only;
- does not authorize residualized expression/representation as production biology.

Authority:

`NUISANCE_COMPARATOR_MECHANICS_ONLY__NOT_PRODUCTION_REPRESENTATION`

### 5. Pair-sampled structure-preservation probe

Module:

`src/sea_ad_jepa/v5/structure_preservation_probe_v1.py`

Purpose:

- protects against overcorrection when reducing operator/source/QC dependence;
- compares a prospectively frozen set of row-pair distances before/after adjustment;
- avoids O(N^2) full-population pairwise cost;
- reports distance-rank preservation, median/P95 relative distance change and zero-distance collapse;
- applies no acceptance threshold yet.

Critical self-audit repair:

The first version bound a pair-plan hash but did not prove the actual supplied pair list was the frozen list and did not enforce unchanged row identity. That was recognized as a fail-open design risk and hardened before promotion. Any production use must bind the canonical pair list and exact row identity, not just an external plan filename/hash.

Authority:

`STRUCTURE_PRESERVATION_MECHANICS_ONLY__NOT_BIOLOGICAL_AUTHORITY`

### 6. Donor-disjoint split integrity guard

Module:

`src/sea_ad_jepa/v5/group_split_integrity_v1.py`

Purpose:

- forbids donor leakage across train/validation/test;
- requires every row exactly once and unique row identity;
- requires train, validation and test all present;
- reports source/operator overlaps without interpreting them as proof of generalization;
- does not choose the split or authorize training.

Authority:

`SPLIT_INTEGRITY_MECHANICS_ONLY__NOT_GENERALIZATION_PROOF`

## Pre-existing fail-open discovered and fixed during this lane

The matching-state validator previously checked cell-count partitions but did not enforce internal consistency between reported stratum-count buckets and cell-count buckets. A corrupted singleton-stratum count could be accepted.

CI exposed this as a real failure (`281 passed, 1 failed`) during the red-green cycle.

`d_shared_matching_state_resolution_v1.py` was hardened so singleton and size-band stratum counts must be arithmetically compatible with their cell counts and total strata.

This repair is part of the current green lineage.

## External-methodology inspiration incorporated

The waiting-time literature/practice scan reinforced four principles. These are design inspiration, not imported authority:

1. Batch removal must be evaluated together with biological/structural preservation; one-sided batch-invariance metrics can reward overcorrection.
2. Approximate binning of continuous nuisance covariates does not automatically restore exact exchangeability; therefore arbitrary Q_DEPTH/Q_DETECT bins remain disfavored.
3. Evaluation should be donor-disjoint when donor is the biological independence unit; random cell-level CV can overstate generalization.
4. Corrected/residualized expression should not automatically replace the original molecular substrate for biological inference; correction can itself create or erase apparent biology.

These principles motivated the structure-preservation and donor-split guards and support keeping nuisance residualization as a comparator until independently qualified.

## What is intentionally NOT frozen

Do not infer a decision from implementation availability.

Still unfrozen:

- final V3 null family;
- donor-level permutation as primary null;
- operator-block permutation as primary null;
- support-pattern blocking as primary null;
- conditional randomization model;
- nuisance regression family/degree;
- ridge value for production;
- common-core final view partition;
- final number of views;
- final rank envelope;
- rank cutoff rule;
- pair-preservation acceptance threshold;
- same-cell intervention acceptance threshold;
- V5 positive-control injection ladder;
- D_shared decision thresholds under a successor authority.

No arbitrary depth/detection bins have been introduced.

## Current decision logic after Claude returns

1. Authenticate Claude's rebuilt substrate and deterministic common-core partition.
2. Verify genuine molecular disjointness and complete row/address lineage.
3. Rerun/inspect outcome-blind spectrum, conditioning and nuisance dominance on the new substrate.
4. Apply nuisance comparator and structure-preservation mechanics together; do not optimize one without the other.
5. Characterize candidate exchangeability units and run the null-mobility audit before treating any permutation family as viable.
6. Derive a prospective structural rank-support rule from the rebuilt spectrum/numerical stability; do not inherit 1..512 or choose a convenient threshold retrospectively.
7. Freeze candidate V3 authority only after these inputs are reviewed.
8. Use T0 to falsify the frozen candidate mechanics; T0 cannot certify V5.
9. Run independent FULL104 measurement qualification at real geometry.
10. Only after qualification and exact pre-outcome binding may one real D_shared execution be contemplated.

## Current hard terminals

`V3_NULL_NOT_YET_DESIGNED_OR_EXECUTED`

`RANK_SUPPORT_AUTHORITY_NOT_YET_FROZEN`

`REBUILT_DISJOINT_FULL104_SUBSTRATE_PENDING_HEAVY_MACHINE_EVIDENCE`

`NO_D_SHARED_OUTCOME_EXECUTION_OR_INSPECTION`

`TRAINING_OFF`

## Verification record

Exact verified pre-ledger head:

`0e770cdd708228c3628ef0e2d29bd5fee1757547`

Workflow:

`V5 dataset-first production closure`

Run:

`34885448123`

Result:

`305 passed; 45/45 critical tests executed and passed; authority-source compilation PASS`

Do not claim the ledger-writing commit itself is verified by that run. Re-fetch the branch and its next workflow before making a newer green claim.
