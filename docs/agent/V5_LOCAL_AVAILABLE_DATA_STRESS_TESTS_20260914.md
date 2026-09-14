# V5 LOCAL AVAILABLE-DATA STRESS TESTS — 2026-09-14

## Scope

This record captures substrate-independent/local calibration evidence produced in the ChatGPT environment while the heavy-machine FULL104 disjoint-view rebuild is still running.

These results are **NOT** FULL104 production authority, **NOT** D_shared evidence, and **NOT** permission to freeze V3. They are falsification/calibration evidence from the locally available project assets:

- `FOUNDATION_CALIBRATION_BUNDLE_20260824.zip`
- `FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip` (50,000 rows × 41,238 addresses sparse CSR)
- `expression.zip` sample metadata

Hard boundaries remained OFF: D_shared real outcome, D_private, D_obs, training, pathology/protected confirmation, TD60, relational activation.

## 1. Independent reproduction of Claude's deterministic disjoint partition

Using the calibration address registry and observation-state NPZ, the common core is exactly 17,186 addresses.

Replayed rule:

`view = sha256("JEPA_V5_COMMON_CORE_DISJOINT_VIEW_PARTITION_V1" + "|" + molecular_address_id).digest()[0] & 1`

Result:

- common core = 17,186
- view 0 = 8,568
- view 1 = 8,618
- intersection = 0
- union = 17,186

Canonical newline-separated ascending-ID hashes independently reproduced exactly:

- core: `f23342ac67dde64a53d86b2e271b473a01c8bd97a490cb3497e1f39feee91bb8`
- view 0: `0cda9e8ed75f23d244bf1b4e67b881df43c6c3749f21d13a0491bfd2b1884b37`
- view 1: `76432f120a154ba78f1534f9e1b1ee018007fdda26cbbe4d435cc1c5bb5b4669`

This exactly matches Claude's heavy-machine interim report.

## 2. Independent calibration geometry under the exact disjoint partition

On the real 84-cell/all-42-operator calibration truth table:

- cosine-distance Spearman(view0, view1) = `0.9836454535`
- Euclidean-distance Spearman(view0, view1) = `0.9812240945`
- median relative cosine-distance difference between disjoint views = `0.0146524`
- view0 vs full-common-core cosine-distance Spearman = `0.9954478972`
- view1 vs full-common-core cosine-distance Spearman = `0.9961404699`
- median relative distance change versus full common core ~`0.7%` per view

Interpretation: genuine molecular disjointness is mechanically viable on the independent calibration fixture without collapsing cell-cell geometry. This is not biological qualification.

## 3. Local 50K sample reproduces source nesting

The 50K discovery sample contains:

- 104 donors
- 42 operators
- 3 sources

Independently reproduced:

- donors spanning >1 source = 0 / 104
- operators spanning >1 source = 0 / 42
- donors/source = HVS 41, NPH52 17, SEA_AD 46

Therefore source is a hard exchangeability boundary in this local sample, matching the FULL104 reconnaissance finding.

## 4. Whole-donor source preservation does NOT imply operator-exposure preservation

In the 50K sample:

- median operators per donor = 11
- range = 1..21
- only 1/104 donors appears in exactly one operator

If exact donor operator-set profile is required, only 67/104 donors have another donor with an identical operator set. Coverage is highly source-dependent:

- HVS: 6/41 donors eligible; 14.5% of HVS sample rows
- NPH52: 16/17 donors eligible; 98.5% of NPH52 rows
- SEA_AD: 45/46 donors eligible; 98.1% of SEA_AD rows

No two donors in any source have an exactly identical operator **count/proportion vector** in the 50K sample.

A deterministic minimum-cost source-preserving donor derangement based on operator-composition total-variation distance can improve similarity but remains approximate:

- overall median best-match TV distance ~0.118
- overall p95 ~0.234
- HVS median ~0.167
- NPH52 median ~0.088 with a severe unmatched tail (~0.977)
- SEA_AD median ~0.085

Therefore `within_source_donor_permutation` alone does not establish exact exchangeability with respect to operator exposure.

## 5. Unrestricted donor permutation catastrophically fails under source confounding

Synthetic conditional-null outcomes were generated over the real 104-donor/source geometry with source effects but no direct conditional relationship to the real donor-level common-core summary predictor.

Across 200 replicates with 399 permutations/replicate:

- unrestricted whole-donor permutation rejection at nominal 0.05 = **1.00**
- within-source donor permutation rejection = **0.02**
- median p unrestricted = 0.0025
- median p within-source = 0.505

Interpretation: permuting donors across sources is empirically invalid on this geometry, not merely theoretically questionable.

## 6. Source-preserving donor permutation can still fail under operator-composition confounding

A synthetic within-source operator-exposure nuisance score was constructed from the first PC of each donor's operator-composition vector. The score is outcome-blind and was oriented only relative to the representation summary for worst-case stress testing.

Within-source correlations between the real common-core donor predictor and operator-exposure nuisance score:

- HVS ~0.544
- NPH52 ~0.469
- SEA_AD ~0.145

After source-centering the statistic, source-preserving donor permutation was anti-conservative when both predictor and synthetic outcome depended on this operator-exposure nuisance:

- nuisance beta 0.5: rejection ~0.555
- beta 1.0: rejection ~0.97
- beta 2.0: rejection ~1.00

A Freedman-Lane-style nuisance adjustment including the operator-exposure score, with residual permutation inside source, returned rejection near nominal in the related stress test (~0.08, 0.055, 0.05 over beta 0.5,1,2).

Interpretation: source blocking is necessary but may not be sufficient; operator-exposure nuisance must be handled explicitly and whole-procedure calibration is required.

## 7. Cell-level within-operator permutation is pseudoreplication-prone

Synthetic outcomes with independent donor random effects were placed on the real 10K-cell subset and operator-centered. A cell-level within-operator permutation null was then used, incorrectly treating cells as exchangeable units.

Across 40 replicates with 79 permutations/replicate:

- rejection at nominal 0.05 = **0.525**
- median p = 0.0375

Interpretation: within-operator cell permutation is highly mobile but statistically unsafe when donor clustering exists. Donor coherence cannot be discarded.

## 8. Common-core restriction does not neutralize source/operator structure

A deterministic 10K-cell sample (every fifth discovery row) was processed with memory-mapped sparse arrays. For all addresses, common core, and each disjoint half, three simple outcome-blind summaries were computed: fixed-universe mean expression, RMS expression, and detected fraction.

On common-core summaries, donor-disjoint cross-fitted operator-only ridge achieved high predictive power for some aggregate coordinates:

- core mean R2 ~0.801
- core RMS R2 ~0.967
- core detected fraction R2 ~0.397
- view0 mean/RMS/detect ~0.780 / 0.959 / 0.379
- view1 mean/RMS/detect ~0.817 / 0.963 / 0.415

This is descriptive mechanics only; because source/operator/biology are confounded, these values are not pure technical variance estimates.

Even after broad-cell-class mean removal, common-core summaries remained strongly source-associated. Thus common-core restriction removes operator-specific **measurement support availability** but does not make source/operator expression structure disappear.

## 9. Aggressive operator residualization can destroy geometry

Using the same donor-disjoint cross-fitted operator-only ridge:

- median source between-group variance fraction across summary features fell from ~0.420 to ~0.000078
- median operator between-group variance fraction fell from ~0.607 to ~0.000831

However, on a deterministic same-broad-class pair set:

- pair-distance Spearman before vs residualized geometry = **0.5573**
- median relative distance change = **0.2107**
- p95 relative distance change = **0.8317**

Interpretation: a method can appear to remove batch/source structure extremely well while badly distorting real-data geometry. V5 requires a two-sided qualification: nuisance reduction **and** structure preservation.

## 10. Injected-signal identifiability challenge

Two synthetic signals of equal amplitude were injected on top of a real common-core summary and the same donor-disjoint operator adjustment was applied.

Signal A was explicitly centered within source (nuisance-orthogonal). Signal B was aligned with source.

Retained slope relative to injected amplitude:

- nuisance-orthogonal signal: ~1.00 at amplitudes 0.25, 0.5, 1.0
- source-aligned signal: ~0.00 at amplitudes 0.25, 0.5, 1.0

Interpretation: source-aligned biology is not identifiable from source-linked technical structure inside this dataset. An adjustment can preserve orthogonal signal yet erase equally real source-aligned signal. Future positive-control qualification must include both nuisance-orthogonal and nuisance-aligned challenges; the latter cannot be used to demand impossible recovery, but it must expose the identifiability boundary rather than hiding it.

## Current methodological implications

The local evidence rejects the following simplistic V3 candidates:

1. unrestricted donor permutation across source;
2. source-preserving donor permutation with no operator-exposure adjustment;
3. cell-level within-operator permutation that discards donor clustering;
4. aggressive operator/source residualization judged only by nuisance removal;
5. claiming common-core restriction alone solves operator/source confounding.

The strongest remaining family to evaluate prospectively after Claude's rebuilt substrate arrives is:

`DONOR_LEVEL_INFERENCE + SOURCE_BLOCKING + EXPLICIT_OPERATOR_EXPOSURE_NUISANCE_MODEL + WHOLE_PROCEDURE_RESIDUAL/CONDITIONAL_RANDOMIZATION_CALIBRATION + STRUCTURE_PRESERVATION_GATE + SAME_CELL_MEASUREMENT_INTERVENTION_GATE`

This is a candidate family only. Exact nuisance design, statistic, permutation/randomization mechanism, rank support, thresholds and multiplicity remain unfrozen.

## Authority boundary

`LOCAL_CALIBRATION_AND_FALSIFICATION_EVIDENCE_ONLY__NOT_V3_AUTHORITY`

`V3_NULL_NOT_YET_DESIGNED_OR_EXECUTED_ON_FULL104`

`NO_D_SHARED_OUTCOME_EXECUTION_OR_INSPECTION`
