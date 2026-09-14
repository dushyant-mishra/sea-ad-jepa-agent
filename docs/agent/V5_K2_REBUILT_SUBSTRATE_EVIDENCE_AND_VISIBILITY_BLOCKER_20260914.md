# V5 K=2 REBUILT SUBSTRATE EVIDENCE + VISIBILITY BLOCKER — 2026-09-14

## Scope

This record incorporates the completed heavy-machine K=2 rebuild report returned by Claude. No D_shared outcome was executed or inspected. Training, protected/pathology access, TD60 and relational activation remained OFF.

The K=2 rebuild is a full-scale reference substrate and not automatically final view-count authority.

## Deterministic disjoint molecular partition

Namespace: `JEPA_V5_COMMON_CORE_DISJOINT_VIEW_PARTITION_V1`

Rule: `view = sha256(namespace | address_id).digest()[0] & 1`

Ordering: ascending molecular_address_id, identity-only.

Parent registry/observation-state binding: `7d61ed7bb649d129496c45cdf49adbb8b85faf7330803803287a2ec93631e4fd`

Results:

- common core: 17,186 addresses
- V0: 8,568
- V1: 8,618
- intersection: 0
- union: exactly 17,186
- deterministic replay identical
- V0 address-list SHA-256: `0cda9e8ed75f23d244bf1b4e67b881df43c6c3749f21d13a0491bfd2b1884b37`
- V1 address-list SHA-256: `76432f120a154ba78f1534f9e1b1ee018007fdda26cbbe4d435cc1c5bb5b4669`
- core address-list SHA-256: `f23342ac67dde64a53d86b2e271b473a01c8bd97a490cb3497e1f39feee91bb8`
- partition artifact SHA-256: `129631f95c9ef90bd5a4af2a70cbc2adbbf907ed6357b9c13c4aa370cafc1575`

A cheap typicality check over 40 alternative namespaces found the frozen split's cardinality gap 50 at the 32.5th percentile (median 82, max 230). This supports that the frozen split was not selected for unusually balanced cardinality. It is not a feature-level typicality distribution.

Terminal: `PASS_GENUINELY_DISJOINT_COMMON_CORE_VIEWS`

## Rebuilt full-population feature substrate

- `V0_full.npy`: shape `(4553407, 512)`, float32, SHA-256 `3b3f102c6767727ca4ab56832f8e70baf203676d6b65973c42903b22b6d56ada`
- `V1_full.npy`: shape `(4553407, 512)`, float32, SHA-256 `c41df46d842d643f04566b8523a8aa711fa54bec1c836e0b394c0146017f231c`
- `ASSEMBLY_SEEN_V5.npy`: SHA-256 `0339d2e79599419f369d78cddf14448019f89476eb674000437b72a1b4fb640e`

Built from 8,915 authenticated blocks under manifest `66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29` in 86.2 minutes wall time.

Normalization: `log1p(raw * 10000 / source_library)` exactly once.

Per view: 256 value + 256 visibility channels. New projections are namespace-derived. Historical 4-view geometry and 0.60 visible masking were not inherited. No sampling, clipping, capping, winsorization, imputation or PCA.

The exactly-once assembly receipt is lineage corroboration only because row population/order were already closed historically; its byte identity to the old all-ones receipt is not a new scientific result.

Terminal: `PASS_V5_REBUILT_FEATURE_SUBSTRATE_MECHANICS_AND_LINEAGE`

## Structural characterization of current 512-channel rebuild

| quantity | V0 | V1 |
|---|---:|---:|
| numerical rank | 512 | 512 |
| min eigenvalue | 0.538 | 0.470 |
| condition number | 411 | 445 |
| participation ratio | 35.6 | 37.3 |
| spectral-entropy effective rank | 201 | 204 |
| cumulative rank 50% | 76 | 76 |
| cumulative rank 75% | 242 | 240 |
| cumulative rank 90% | 379 | 377 |
| cumulative rank 95% | 437 | 435 |
| cumulative rank 99% | 493 | 492 |
| rank above frozen spectral noise floor | 480 | 480 |
| total variance | 1574.3 | 1526.5 |

The historical A/B substrate was singular/rank-deficient, with condition approximately `1.2e303`, participation ratio 8.3/9.5 and spectral-entropy rank 46/53. The rebuilt 512-channel covariance is numerically full rank and far better conditioned.

This is structural characterization only. Rank authority remains unfrozen.

## Nuisance structure after current rebuild

Approximate common-core rebuilt 512-channel fractions:

- donor variance fraction ~0.152
- operator variance fraction ~0.179
- source variance fraction ~0.137

Historical operator-native comparator:

- donor ~0.452
- operator ~0.479

Although absolute operator variance fell about 2.7x, donor variance also fell. Historical operator/donor ratio was ~1.06; new full-512 ratio is ~1.18. Therefore the 2.7x operator reduction must not be interpreted by itself as technical-confounding resolution.

Per-view balance is strong:

- donor fraction relative difference ~0.44%
- operator fraction ~0.43%
- source fraction ~0.62%
- Q_DEPTH max-|corr| ~4.38%
- Q_DETECT max-|corr| ~3.54%
- participation ratio ~4.45%
- total variance ~3.04%

The near-identical source/operator fractions are expected because the same cells/operators/sources underlie both molecular halves. Molecular disjointness cannot remove cell-level technical effects.

## Critical blocker: visibility-channel QC coupling

The current 512-channel rebuild materially worsened QC dependence:

- historical Q_DEPTH max |corr| ~0.371 -> rebuilt ~0.672
- historical Q_DETECT max |corr| ~0.417 -> rebuilt ~0.773

Claude identified a plausible construction-level cause: the 256 visibility channels are signed sums over detected addresses and therefore can directly encode detection count in a common-core/no-mask design.

This is a measurement-design regression. Do not freeze rank or V3 null against the current full 512-channel substrate until the value/visibility decomposition is characterized.

Required next heavy-machine action uses the existing arrays only; no new expression rebuild is justified yet:

1. verify exact column layout from producer code;
2. characterize `VALUE_ONLY` 256 channels, `VISIBILITY_ONLY` 256 channels, and `FULL` 512 channels separately for V0 and V1;
3. recompute spectrum/effective rank/conditioning;
4. recompute donor/operator/source fractions;
5. recompute Q_DEPTH/Q_DETECT correlations and donor-disjoint nuisance predictability;
6. compare VALUE_ONLY geometry against FULL using frozen pair/structure-preservation machinery;
7. recompute rank-support candidate rules on VALUE_ONLY;
8. if visibility is the dominant QC encoder and value-only preserves geometry/conditioning, recommend but do not yet freeze: `PRIMARY_MOLECULAR_REPRESENTATION = VALUE_ONLY`, `VISIBILITY_DETECTION = OBSERVATION_STATE_NUISANCE_CONTROL_ONLY`.

Do not restore the old 60% mask merely to decorrelate Q_DETECT.

## Exchangeability implications

Heavy reconnaissance reconfirmed all donors/operators/support-patterns are nested within source and all 42 operators have multiple donors. Mobility does not imply valid exchangeability.

Local stress tests already reject:

- unrestricted cross-source donor permutation;
- naive source-only donor permutation under operator-exposure confounding;
- cell-level within-operator permutation under donor random effects;
- aggressive residualization without geometry-preservation checks;
- pooled operator-exposure nuisance slopes across sources.

Strongest remaining unfrozen family:

`DONOR_LEVEL_INFERENCE + SOURCE_BLOCKING + SOURCE_CONDITIONAL_OPERATOR_EXPOSURE_NUISANCE_MODEL + WHOLE_PROCEDURE_RESIDUAL/CONDITIONAL_RANDOMIZATION_CALIBRATION + STRUCTURE_PRESERVATION_GATE + SAME_CELL_MEASUREMENT_INTERVENTION_GATE`

## Rank-support status

Current full-512 candidate rule results:

- positive numerical support: 512 / 512
- spectral noise floor: 480 / 480
- cumulative 99%: 493 / 492
- participation ratio: 36 / 37

These are not authority because the visibility block may inflate effective/numerical support while carrying technical signal. Recompute after value-only ablation.

Terminal: `RANK_SUPPORT_CHARACTERIZED__AUTHORITY_NOT_YET_FROZEN`

## Environment / provenance

Heavy-machine HEAD reported by Claude: `d9938dd782443b5310919ecf6c14099c0b4c23ec`, clean.

Substrate path on heavy machine: `D:/jepa_v5_substrate_20260914/`

Characterization artifact: `substrate_characterization.json`

Characterization runtime approximately 10.2 min/view; 16 logical CPUs; chunk 262,144 rows (~1.07 GB working set).

## Current terminals

`PASS_GENUINELY_DISJOINT_COMMON_CORE_VIEWS`

`PASS_V5_REBUILT_FEATURE_SUBSTRATE_MECHANICS_AND_LINEAGE`

`VALUE_VISIBILITY_ABLATION_REQUIRED_BEFORE_PRIMARY_REPRESENTATION_AUTHORITY`

`PRIMARY_REPRESENTATION_AUTHORITY_NOT_YET_FROZEN`

`RANK_SUPPORT_AUTHORITY_NOT_YET_FROZEN`

`V3_NULL_NOT_YET_DESIGNED_OR_EXECUTED`

`NO_D_SHARED_OUTCOME_EXECUTION_OR_INSPECTION`

`TRAINING_OFF`
