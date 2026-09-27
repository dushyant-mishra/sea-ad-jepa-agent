# JEPA R16 — original-data forbidden-compartment and query-swap intervention

**September 26–27, 2026. Development-only original historical evidence. Not FULL104 raw-Level4 execution, neural V5 training, independent biological validation or production normalization authority.**

## What was physically run

The exact **410,278,055-byte** original `FOUNDATION_CALIBRATION_BUNDLE_20260824.zip` was authenticated by SHA-256 `07748d5bd21fe0857ccad3002fba3946d1791d25898b841d41056a3707117444`. The historical 84-cell, 41,238-address truth table in that ZIP and 42 matched original operator metadata files from the supplied `expression.zip` were loaded and joined by stable cell key; **84/84 cells matched**, two per operator. Exact ZIP and truth-member roots are recorded in `R16_RESULTS.json`.

The truth table stores genuine originally observed log1p10K expression in `float32`, not original raw count blocks. Original full-source integer `source_library` metadata allowed physical inversion via `round(expm1(log_value) * source_library/10000)`; among **379,170 nonzero entries**, the largest fractional distance from an integer was **0.000563 UMI**. Reapplying the logged normalization to the recovered integers agreed with all original nonzero values within **3e−7**. Replaying all four physically stored historical masks for all 84 cells (336 views) reproduced their stored encoder inputs to **2.39e−7** per query. Original raw Level4 files were **not opened**, so this evidence remains an authenticated historical logged-count reconstruction with a verified inverse, not an independently executed current FULL104 raw-count reader.

Inherited the **exact R8 four-partner/eight-reference measured-anchor constructor** rather than inventing a new target. This target object is a same-cell RNA measurement, not an independently validated biological latent state. Tested three exploratory programs: APOE, P2RY12 and HLA-DRA. For each query, in each of 84 cells, a raw-count change was made separately to q, to one measured partner and to one measured reference, with the full-source library adjusted by the exact count change. In every original historical masking view, the student input included only measured, visible complementary genes and excluded forbidden genes. Derived student-visible QC totals, detections and expression summaries were tested alongside the tokens and denominator.

## Original-data results

| Query | Original q-positive cells / 84 | Q mutation max full-source token shift | Q-only denominator: max forbidden-partner/reference shift | All 13 forbidden excluded: max shift | Measured-anchor statuses (positive / measured zero / zero reference / structurally unmeasured) |
|---|---:|---:|---:|---:|---|
| APOE | 10 | 0.003353 | 0.003454 | **0** | 59 / 13 / 12 / 0 |
| P2RY12 | 17 | 0.003687 | 0.003454 | **0** | 48 / 24 / 12 / 0 |
| HLA-DRA | 9 | 0.001033 | 0.003454 | **0** | 3 / 9 / 2 / 70 |

Per program: **84 q**, **84 partner**, **84 reference** count interventions, crossing all **42 original operators**, plus **336 original historical masked-view replays**. The genuine R8 target constructor returned an unchanged measured target under every q-only mutation. A q-excluded denominator did remove the q-specific scalar channel—but retained a second channel through forbidden partner and reference genes. Removing all **13** prospective forbidden genes eliminated both channels in the tested original-data numerical surface. A case with measured zero is not structurally unmeasured; zero-reference cases abstain. HLA-DRA's 70 structurally unmeasured target rows reflect this deliberately broad historical 42-operator sample, **not** an estimate of HLA-DRA assay support in the actual microglia cohort.

### Additional discovery: query-swap normalization shortcut

For a query swap, the comparison must distinguish biological target changes from changes to the *student inputs*. Even after forbidding each individual q/partner/reference group, different queries subtract different 13-gene sets from the full-source library. Thus two otherwise identical cells can acquire different normalized complementary RNA **solely because the query label changed**.

To test this, I held the **same original raw RNA**, the **same 23-gene common complementary feature basis** (3 query genes + 12 partners + 8 shared references excluded), the same cell, and the same physically recorded masking view. The *only* difference in the first comparator was the choice of the query-specific 13-gene denominator; the fixed-union comparator used a single, common 23-gene denominator.

| Query swap | Original cell×view comparisons | Query-specific denominators changed, and tokens changed | Max spurious query-specific token difference | Common-union token difference | Comparisons in which both measured targets evaluable |
|---|---:|---:|---:|---:|---:|
| APOE ↔ P2RY12 | 336 | **300** | 0.005189 | **0** | 288 |
| APOE ↔ HLA-DRA | 336 | **288** | 0.004153 | **0** | 48 |
| P2RY12 ↔ HLA-DRA | 336 | **216** | 0.004943 | **0** | 48 |

These are exact numerical input comparisons, not trained model query-swap outcomes. The fixed union is only a **three-query developmental comparator**. An all-41K-query production union might leave too little usable RNA; a scalable common-basis protocol must be preregistered and qualified for actual intended query panels before implementation. Query-specific masks may be biologically needed, but a raw q-swap model comparison must not treat mask/denominator differences as evidence of learning a query-specific state.

## What this changes

1. Versioned normalization research should distinguish `FULL_SOURCE`, `Q_ONLY_EXCLUDED`, `QUERY_TARGET_COMPARTMENT_EXCLUDED`, and `FIXED_COMMON_QUERY_COMPARISON` as different experimental estimands. A q-only normalization successor is *not sufficient* for the R8 measured target because partner/reference genes remain forbidden yet can enter the denominator.
2. **Freeze all student-visible ancestors**, not only masked tokens: source libraries, QC, summary features, and derived readouts. `ALL_FORBIDDEN_EXCLUDED` passes this local numerical surface, but all other current V5 consumers require tracing and independent verification before source succession.
3. For query identity tests, compare models in a common lawful student coordinate system and fixed common input normalization or explicitly measure/adjust the differing input information. Supply q identity as the query condition, not as a hidden denominator change.
4. Respect assay support: for HLA-DRA, 70 of the 84 broadly sampled historical cells lack the full measured target. Abstain; don't zero-fill and don't infer target quality from unqualified cells.
5. Move the **original-data q intervention** to the current authenticated Level4 reader on the separate GPU laptop after a versioned successor design; this package cannot establish that the historic 84-cell inverse is identical to every FULL104 runtime source/library consumer. Neither a synthetic result nor this historical original-data result authorizes current training.

## Tests and honest failure record

**28/28 unit and physical-fixture tests passed, zero skipped.** Tests cover archived source authentication, two cells across each of 42 operators, stable-key library join, float-to-integer recovery, actual four-view replay, actual inherited R8 target, missing/zero abstention, three denominator versions, q/partner/reference mutations, q-swap on a common feature basis, false-positive mutation controls and protection statuses. Initially **one test failed** because its planted unsafe q-leak fixture had *no nonzero permitted input gene*: an unsafe denominator cannot change all-zero logged values. Corrected the fixture by adding one positive permitted gene; reran **28/28 green** without weakening the assertion. The initial failure was a fixture defect, not a negative result about leakage.

**No production changes or remote commits.** This is a portable, complete developmental research package with code, the inherited R8 constructor, executed result JSON, row-level (hashed-key only) audit, tests, run logs and SHA manifest. Original human RNA archives are *not* copied into the portable ZIP. To replay, supply the exact authentic local archives and run:

```bash
python r16_original84_forbidden_compartment.py \
  --calibration /path/to/FOUNDATION_CALIBRATION_BUNDLE_20260824.zip \
  --expression-metadata /path/to/expression.zip \
  --out-dir /path/to/clean-output
python -m unittest -v test_r16_original84_forbidden_compartment
```

A real V5 `Full104ManifestStreamV1` normalization source trace was separately authenticated by Claude at `6db6020c` (streaming executor SHA-256 `143645becff6f6142d99224bfe188702b2400228b4af121738341ed4e3ebb86d`; geometry SHA-256 `44d6f7c490b83585e4003e8f711ea6331d9b54b2e7b4873eb7a90eed48f33cc4`). This round uses the mathematically equivalent recorded log1p10K mapping for original historical cells; it does **not** claim to have executed the production iterator on source Level4 blocks or the neural V5 encoder/EMA.

`TRAINING=OFF | AUDIT_B_N1=UNOPENED | D_SHARED_G5=UNOPENED | FULL104_PROTECTED=UNOPENED | BIOLOGICAL_TARGET_NOT_QUALIFIED`.
