# Target-discovery historical quantitative design calibration — 2026-10-11

Status: `HISTORICAL_METADATA_CALIBRATION_COMPLETE__OUTCOME_BLIND_FUTURE_DESIGN_CONSTRAINTS_ONLY__NO_TARGET_AUTHORITY`

Authenticated historical calibration bundle SHA-256:
`07748d5bd21fe0857ccad3002fba3946d1791d25898b841d41056a3707117444`

This audit reads only compact historical calibration/metadata/support/sampler tables from that authenticated bundle. It does not open corrected target-discovery values, G6/G7 outputs, pathology, or protected confirmation outcomes.

## 1. Corpus/source imbalance is extreme

Reader-fit population:

| source | cells | donors | operators | fraction of fit104 cells |
|---|---:|---:|---:|---:|
| HVS | 198,718 | 41 | 24 | 4.36% |
| NPH52 | 236,476 | 17 | 7 | 5.19% |
| SEA_AD | 4,118,213 | 46 | 11 | 90.44% |

Historical original T1 rows instead contained:

| source | original T1 rows | fraction of historical T1 |
|---|---:|---:|
| HVS | 2,059 | 62.55% |
| NPH52 | 218 | 6.62% |
| SEA_AD | 1,015 | 30.83% |

This is a major sampling inversion. A pooled cell-weighted metric on the full reader-fit population would be overwhelmingly SEA-AD-weighted, while the historical T1 optimization population was HVS-heavy.

**Binding future-design consequence:** target qualification is donor-primary and source-explicit. Pooled cell performance can be descriptive but cannot substitute for per-source donor-level gates.

## 2. Donor and operator sizes are also highly unequal

The authenticated metadata atlas reports:

- 104 reader-fit donors;
- donor cell-count range 81 to 174,111;
- donor median 14,749 cells;
- donor-size Gini 0.61249;
- operator cell-count range 179 to 732,360;
- operator-size Gini 0.76473.

Historical T1 schedule exposure per donor ranged from 16 to 555 slots; median 268. The waterfill quotas were capacity-bound for 38/41 HVS donors, all 17 NPH52 donors and all 46 SEA-AD donors.

**Consequence:** neither cell-uniform nor inherited historical schedule weighting is a neutral scientific estimator. Discovery metrics must aggregate at donor level before source-level adjudication; eventual training sampling remains a separate prospectively frozen problem.

## 3. Molecular support differs sharply by source

Of 41,238 historical molecular addresses:

- 289 were measured in zero source families;
- 10,334 in one source family;
- 13,269 in two source families;
- 17,346 in all three source families.

Cell-weighted measured-scalar fractions were:

- HVS: 0.454338;
- NPH52: 0.807054;
- SEA_AD: 0.850575.

Collision-unresolved fractions were:

- HVS: 0;
- NPH52: 0.013212;
- SEA_AD: 0.017217.

**Consequence:** a target component may only be scored where its physical/support contract is satisfied. Unsupported or unresolved components abstain. Missing support cannot be converted into a biological zero or forced cross-source completion.

## 4. Held-out transfer partitions are not source-symmetric

The 45 held-out donors are split:

### reader_validation
- HVS: 10 donors / 53,933 cells;
- SEA_AD: 12 donors / 893,098 cells;
- NPH52: **0 donors**.

### reader_oracle
- HVS: 11 donors / 55,848 cells;
- SEA_AD: 10 donors / 766,542 cells;
- NPH52: **2 donors** / 28,925 cells.

Therefore source-specific held-out transfer is structurally absent for NPH52 in validation and extremely donor-sparse in oracle.

**Consequence:** future reporting must distinguish `NOT_ESTIMABLE` from FAIL. A three-source transfer terminal cannot silently require a source/partition combination that has no lawful donor population.

## 5. Objective donor-resolution rule instead of an invented donor cutoff

The new synthetic-only precision helper derives estimability from the predeclared effective alpha rather than choosing `minimum_donors` by taste.

For a two-sided exact donor sign gate under null donor win probability 0.5:

`minimum attainable p with n non-tied donors = 2 * 0.5^n`.

At `alpha_eff = 0.05`, at least **6 non-tied donors** are required before the gate can possibly pass. Thus two NPH52 oracle donors may support a descriptive statistic but cannot qualify donor-generalized recurrence under this gate even if both improve in the expected direction.

If multiplicity makes `alpha_eff` smaller, the required donor count rises automatically. Alpha itself must be frozen from the future decision family before outcomes; this helper does not choose alpha.

## 6. Permutation/null replicate counts must come from alpha resolution, not history

For an exact permutation p-value of the form:

`p = (1 + # null >= observed) / (B + 1)`,

the minimum attainable p-value is `1/(B+1)`.

Therefore the minimum number of null draws needed merely to resolve a predeclared `alpha_eff` is:

`B_min = ceil(1 / alpha_eff) - 1`.

Examples:

- alpha 0.05 -> at least 19 draws;
- alpha 0.01 -> at least 99 draws.

These are **resolution floors**, not claims that 19 or 99 draws provide high-precision quantile estimation. The final Monte-Carlo budget must be frozen from the actual multiplicity/precision contract before real execution. Historical 64/256/999/1000 replicate counts are not inherited merely because earlier code used them.

## 7. Historical shortcut atlas makes technology/support control mandatory

At u205, fixed-capacity held-out-donor probes report:

| representation | source BA | operator BA | support-count R2 |
|---|---:|---:|---:|
| rich_H | 1.0000 | 0.7632 | 0.9998 |
| partial_H | 1.0000 | 0.5214 | 0.9909 |
| rich_CELL | 1.0000 | 0.4839 | 0.9995 |
| partial_CELL | 0.9048 | 0.1916 | 0.9697 |

This does not prove the representation is purely technical because source/operator/support are aliased with donor and biology. It does prove that unconditional technology invariance is not established.

**Consequence:** learned-state candidates C3 and C4 require an explicit conditional-technology-imprint gate after accounting for comparable biology/support. Simply making source prediction difficult is not the scientific objective; the test is unnecessary residual technology information conditional on lawful biological comparability.

## 8. Partial-evidence ceilings vary strongly by endpoint

On the combined 45 held-out donors, the lawful RNA predictive baseline achieved approximately:

- broad_common R2 0.979;
- local R2 0.994;
- local_halo R2 0.999;
- core_halo R2 0.9996;
- weak_distributed R2 0.953;
- local_core R2 0.976;
- sparse_marker_like R2 0.934;
- innovation_tail R2 0.575.

For rare recurrence endpoints:

- recurrent_5pct: 22 positives across 12 positive donors, AP 0.341, AUROC 0.937;
- recurrent_1pct: only 5 positives across 5 positive donors, AP 0.031, AUROC 0.867.

**Consequence:** a single universal success metric is invalid. Common continuous state, innovation-tail state and rare-event state require different estimands and estimability reporting. Rare-event claims must report positive donor counts; cell-level AUROC alone cannot establish donor-generalized recurrence.

## 9. The 84-cell truth-table set is a falsification set, not training evidence

The historical truth-table metadata contain:

- 84 cells;
- all 42 operators;
- 54 donors;
- HVS 48, NPH52 14, SEA_AD 22 cells;
- all 84 marked `in_original_t1 = 0`;
- `expression_read_before_freeze = false` for the frozen metadata selection.

This makes it useful for compact cross-operator structural/support and leakage falsification. It is not large enough to replace donor-level full-population qualification, and it does not become corrected-data authority.

## 10. Prospectively binding design consequences

For the future target tournament, before real outcome execution:

1. Freeze the decision family and derive `alpha_eff`; do not inherit historical null counts.
2. Compute donor-sign resolution and permutation-resolution floors from `alpha_eff`.
3. Mark source/partition combinations `NOT_ESTIMABLE` where the predeclared donor/statistical gate cannot mathematically resolve.
4. Keep source-specific donor adjudication separate from pooled descriptive metrics.
5. Require candidate-specific shortcut controls, especially conditional technology imprint for learned states.
6. Use support-aware eligibility/abstention; never force common coverage across source families.
7. Use endpoint-specific estimands: continuous state, innovation-tail behavior and rare-event recurrence are not interchangeable.
8. For rare endpoints, report positive cells **and positive donors** and reject cell-only inference.
9. Keep the 84-cell table for structural/leakage/operator falsification rather than promotion by itself.
10. Do not use any number in this historical audit as a target performance cutoff merely because historical models attained it.

## Authority boundary

This calibration does not authorize G6/G7, corrected replay, real target-tournament execution, target selection, representation selection, TD60, Stage4, pathology or training.

Terminal:

`HISTORICAL_QUANTITATIVE_DESIGN_CALIBRATED__SOURCE_DONOR_SUPPORT_ASYMMETRIES_BOUND__PRECISION_DERIVATION_RULES_FROZEN__NO_TARGET_AUTHORITY`
