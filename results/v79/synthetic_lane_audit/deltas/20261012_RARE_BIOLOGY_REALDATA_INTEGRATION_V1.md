# V79 delta — repaired benchmark success + rare-biology real-data integration

Date: 2026-10-12
Status: `MATERIAL_DELTA`

## 1. Repaired engineering benchmark

The single authorized repaired benchmark was consumed successfully at exact PR #308 head `559a1c104c8f1f56d2c05509eecf6b9dc05846a5`.

Authority/evidence:
- PR #308 authorization `6128881654`
- execution instructions `6129078915`
- result comment `6129569599`
- evidence branch commit `586e5ea5af73bbc28637a4cbab0eb7c108c67d42`
- prep receipt SHA-256 `ee89a67ba3919a6593b2f20e4cc4030904e4032ef78c28438fecdab0cfed8170`
- benchmark result receipt SHA-256 `3774cecbc10266ed9205fe3bd8f161faf119ab83c3625783b484c2412477316d`

Observed:
- 4/4 fits COMPLETE; PRIMARY stage only;
- 0 divergences;
- worst R-hat 1.01;
- worst bulk/tail ESS 1184 / 1343;
- mean fit wall 3.818 s;
- projected 1,056-fit runtime 1.520 h including frozen settle term;
- frozen ceiling 72 h;
- `stop_required=false`;
- no qualification fit, scoring, controller truth access or training.

Interpretation: engineering feasibility PASS. Qualification fitting still requires a separate controller authorization.

## 2. Recovered project requirement omitted from V79 Layer A

Project history establishes rare/private biology, donor recurrence, partial-evidence recovery and uncertainty as major qualification goals. Q00-Q11 do not implement this biological truth; they qualify the observation/statistical layer.

This is now explicitly governed as:
- Layer A: V79 Q00-Q11 observation/statistical qualification;
- Layer B: new donor-structured rare biological truth;
- Layer C: teacher/student rare-state recovery + uncertainty qualification.

Q00-Q11 remain immutable. No retroactive modification is allowed.

## 3. Existing ETL/caches assimilated; no new ETL

A capability matrix was created from existing audits/manifests:
`results/v79/rare_biology_integration/V79_RARE_BIOLOGY_DATASET_CAPABILITY_MATRIX_20261012.csv`.

Already available evidence includes FOUNDATION RNA, Morabito RNA/ATAC caches, GSE214979 paired multiome, GSE272082 candidate paired multiome, Stage75-79/cisTarget regulatory resources, spatial UCDQ assets, and GSE178317 perturbation data.

## 4. Exact local artifact re-verification

Read-only checks of artifacts already supplied to the project confirmed:
- frozen V6R5A program weights SHA-256 exactly matches `001375ec77c5b606ad0972073c1daa6ad14b0e517f05ea23c6c9b3110203ff70`;
- 41K expression archive parts match their sidecar;
- reassembled archive matches `63239898b9c93f29c20b62b84dc9b94c2c87e3e3f2b7958b7435847e3b9541f7`;
- inner 50K × 41,238 NPZ matches `4c50f1de2446b07bbf3199bba80ebc89749c8104cb7668664ed705dbfc579d92`.

No source file was modified.

## 5. Consequential rare-program finding

`innovation_tail`, `recurrent_5pct`, and `recurrent_1pct` have identical frozen molecular weight vectors. Rare5/rare1 are threshold roles, not separate molecular directions.

Applying the frozen innovation direction to the already-authenticated 50K TRAIN discovery sample showed strong source dependence:
- global upper 5%: NPH52 1,889 / HVS 347 / SEA-AD 264;
- global upper 1%: NPH52 499 / HVS 1 / SEA-AD 0.

Therefore the historical innovation score cannot serve as the new cross-source rare biological truth. The new rare state must be planted independently of source/operator/depth, with observation effects applied afterward.

A bounded microglia-only diagnostic contained 665 cells across 66 donors and all three sources. Upper-tail cells occurred across multiple donors/sources, showing feasibility of donor-recurrent rarity, but the sample is too small/uneven and the score too source-shifted to freeze prevalence thresholds from it.

## 6. New prospective spec

Created:
`docs/agent/V79_RARE_BIOLOGY_REALDATA_INTEGRATION_SPEC_20261012.md`.

Required rare-world families cover:
- recurrent RNA-recoverable biology;
- teacher-private regulatory biology;
- frequency-matched technical pseudo-rare twins;
- donor-restricted real biology;
- Morabito-matched separate-nucleus donor-level RNA/ATAC concordance;
- GSE214979-matched same-nucleus multiome;
- intrinsic versus context-conditioned spatial rarity;
- perturbation-response support.

Implementation plan:
`docs/superpowers/plans/2026-10-12-v79-rare-biology-realdata-integration.md`.

## 7. Current terminal

`ENGINEERING_BENCHMARK_PASS__Q00_Q11_FITS_REQUIRE_NEW_AUTHORITY__RARE_BIOLOGY_LAYER_REQUIRED__REALDATA_ASSIMILATION_COMPLETE__NO_NEW_ETL__NO_PATHOLOGY__NO_TRAINING`
