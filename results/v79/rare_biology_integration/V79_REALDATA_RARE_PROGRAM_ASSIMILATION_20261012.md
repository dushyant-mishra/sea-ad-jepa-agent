# V79 rare-biology real-data assimilation — 2026-10-12

Status: `READ_ONLY_ASSIMILATION_COMPLETE__NO_NEW_ETL__NO_PATHOLOGY`

## What was verified from already-built artifacts

No source dataset was reacquired and no historical ETL was rerun.

- Uploaded `66e64913-959f-4a7c-bbfe-6ff906fb281d.npz` SHA-256 = `001375ec77c5b606ad0972073c1daa6ad14b0e517f05ea23c6c9b3110203ff70`, exactly matching the frozen V6R5A/T1 `program_weights.npz` authority.
- The two uploaded 41K expression archive parts match the supplied sidecar exactly:
  - part001 `b8163f53a27f7cb1b526f8311d1b46b599502596c5d0be74fa588747a4e72b2e`
  - part002 `5bc2ec30fb374b15f1c5a4764e1856b0664c13513462ef2f7e224c4b6f856875`
- Reassembling those two parts read-only produced archive SHA-256 `63239898b9c93f29c20b62b84dc9b94c2c87e3e3f2b7958b7435847e3b9541f7`, exactly matching the sidecar.
- The inner `FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.npz` SHA-256 is `4c50f1de2446b07bbf3199bba80ebc89749c8104cb7668664ed705dbfc579d92`, matching the recorded discovery audit.
- Matrix shape is 50,000 cells × 41,238 molecular addresses with 246,702,069 nonzeros.
- The existing sample freeze contains 50,000 rows from 104 TRAIN donors: SEA-AD 33,821 cells, HVS 10,958, NPH52 5,221.

These checks establish byte identity of the already-created calibration assets. They do not create a new data authority.

## Important historical rare-endpoint finding

The frozen program-weight NPZ proves:

- `innovation_tail`, `recurrent_5pct`, and `recurrent_1pct` have identical molecular weight vectors.
- Therefore rare5 and rare1 are frequency/threshold roles on one historical innovation score; they are not distinct planted biological programs.

This confirms the old rare endpoints are useful historical comparators but cannot by themselves define the new rare-biological-state truth.

## Read-only empirical check on the existing 50K TRAIN discovery sample

The frozen `l2__innovation_tail` weights were applied to the already-built 50K 41K-address expression sample. This was a diagnostic only; no outcome/pathology fields were used.

### Whole 50K sample

Global upper 5% of the innovation score = 2,500 cells:
- NPH52: 1,889
- HVS: 347
- SEA-AD: 264

Global upper 1% = 500 cells:
- NPH52: 499
- HVS: 1
- SEA-AD: 0

Interpretation: the historical innovation/rare score has very strong source dependence in this heterogeneous real sample. It is therefore **not acceptable as the new cross-source rare-biological-state definition**. This is exactly the type of source shortcut the new rare-program contract must prevent.

### Bounded microglia check

Using only exact native microglia labels already present in the sample freeze:
- HVS `Microglia-PVM`: 128 cells / 23 donors
- NPH52 `MG`: 304 cells / 16 donors
- SEA-AD `Microglia-PVMSubclass`: 233 cells / 27 donors
- total: 665 cells / 66 donors

Within this bounded microglia set:
- top 5% innovation score: 34 cells; at least one positive cell in 16/66 donors; positives occurred in all three sources.
- top 1% innovation score: 7 cells; at least one positive cell in 6/66 donors; positives occurred in all three sources.

This is only a feasibility observation. The sample is small and uneven at the donor level, and the score itself remains source-shifted. These numbers must **not** become frozen prevalence thresholds.

## Consequence for the new synthetic rare biology

The new rare biological truth must be defined independently of source/operator/depth and then passed through the V79 observation process. It should not be created by thresholding the historical innovation score globally.

The real-data-matched design should use:

1. a donor-level latent propensity for a biological program;
2. within-donor cell-level program activity/prevalence;
3. coherent RNA program effects;
4. regulatory effects tied to frozen Stage75-79/SCENIC-style topology;
5. modality-specific observation operators;
6. matched technical pseudo-rare controls;
7. explicit donor/source/operator recurrence gates.

## Existing real-data validation mapping

- FOUNDATION TRAIN: calibrates donor recurrence, RNA program amplitude, evidence sufficiency and technical/source/operator geometry.
- Morabito GSE174367: separate-nucleus donor-level RNA/ATAC regulatory concordance; never same-cell validation.
- GSE214979: conditional same-nucleus RNA+ATAC validation after predeclared donor exclusions/target freeze.
- GSE272082: secondary paired-multiome route after only the missing authentication is completed.
- SCP2167 + eligible Fang STG MERFISH: already-identifiable real context route for intrinsic vs neighborhood-supported programs.
- Stage75-79 + cisTarget assets: coherent regulatory topology/annotation, not causal truth.
- GSE178317: perturbation calibration/support, not definition of the rare state.

## Governance

- Q00-Q11 remain immutable and are not modified by this work.
- The rare-biology layer is additive and prospective.
- Passing Q00-Q11 can qualify V2_CORE observation/statistical behavior only.
- Rare/multimodal teacher-student biology requires a separate contract and gates before JEPA training authority.
- No pathology, DEV, SEALED, TEST, Morabito outcome selection, or optimizer training was opened by this assimilation.
