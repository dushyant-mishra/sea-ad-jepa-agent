# V5 LOCAL PARAMETER DERIVABILITY AUDIT — 2026-09-14

## Purpose

This audit records which V5 design parameters can be derived or narrowed from assets already available in the lightweight environment, before using the 4.55M-cell heavy FULL104 substrate. It exists to prevent another sequencing error where a long heavy-machine run is launched before exhausting the frozen discovery/calibration evidence.

This document is mechanics/discovery evidence only. It does not authorize D_shared, training, protected/pathology access, TD60, or relational activation.

## Local assets actually available

- `FOUNDATION_CALIBRATION_BUNDLE_20260824.zip`
- `FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip` (50,000 frozen discovery cells, 41,238-address sparse log1p10k expression)
- `expression.zip` (frozen sample manifest + 42 operator metadata shards)
- `checkpoints.zip`
- `t1_checkpoint_u0200.zip`
- 84-cell truth table covering all 42 operators
- support/address/operator/source contracts and historical geometry/calibration reports

## Historical discovery work that must be reused

`FOUNDATION_GEOMETRY_REVIEW.md` already prospectively separated four geometry concepts:

1. raw/common geometry on addresses scalar-measurable in every included operator;
2. full operator-aware geometry with explicit measurement/support state;
3. within-source geometry for HVS, NPH52 and SEA-AD separately;
4. optional integrated sensitivity only after 1–3 are frozen.

It also prospectively required:

- donor-block resampling;
- support-only geometry as a falsification control;
- source/operator/support/depth fingerprints for every discovered structure;
- fixed neighborhood scales `k={15,30,60,120}`;
- fixed graph resolutions `{0.25,0.5,1.0,2.0}`;
- no biological interpretation for structure confined to one donor, explained by support/detection, or disappearing within source.

The historical review explicitly warned that source, donor population, operator, support, depth and biology are partly aliased.

## Historical shortcut evidence

`FOUNDATION_TEACHER_SHORTCUT_ATLAS.csv` shows that technical structure was already strongly readable before training:

- source balanced accuracy at u0: `1.0` in rich_H, partial_H and rich_CELL; `0.952381` in partial_CELL;
- support-measured-count R2 at u0: `0.969797` to `0.999805` across representations;
- rich_H operator balanced accuracy at u0: `0.755113`, rising slightly to `0.763206` at u205;
- these signals changed little with training.

This means source/support leakage is a substrate property, not merely a learned shortcut.

## Locally derivable parameter families

### 1. Common-core molecular universe — DERIVABLE HERE

From the support recurrence table:

- total molecular addresses: 41,238
- addresses measured scalar in all 42 operators: 17,186

This can be recomputed locally exactly. Heavy FULL104 expression is not required.

### 2. Candidate number of genuinely disjoint molecular views K — NARROWABLE HERE BEFORE HEAVY REBUILD

A deterministic identity-only screening partition was used locally for mechanics:

`view = uint64(SHA256(namespace | K | molecular_address_id)[:8]) mod K`

This screening namespace is not final authority and is distinct from Claude's current K=2 production candidate. No expression, annotation, variance or D_shared result determines membership.

#### 84-cell/all-42-operator truth-table screen

Candidate K values 2,3,4,5,6,8,10,12,16 were evaluated on the 17,186-address common core.

Key result: K=2 through K=6 preserve common-core cell-cell cosine-distance ordering very strongly. Degradation becomes more heterogeneous from about K=8 onward.

Examples:

- K=2: minimum view-vs-full Spearman about 0.996; ~8.6k addresses/view
- K=4: minimum about 0.988; ~4.2–4.4k addresses/view
- K=6: minimum about 0.978; ~2.8–2.9k addresses/view
- K=8: minimum about 0.952 on the 84-cell screen; ~2.1–2.25k addresses/view

#### 50K frozen discovery-expression refinement

A deterministic 500-cell subset (250 from each frozen discovery sample A/B) was selected only for computational tractability; it covered all three sources and 36/42 operators.

On the 17,186 common core:

| K | min/max addresses per view | min view-vs-full distance Spearman | minimum P05 nonzeros/cell/view | minimum median nonzeros/cell/view |
|---:|---:|---:|---:|---:|
| 2 | 8593 / 8593 | 0.9968 | 503.9 | 1399.5 |
| 3 | 5655 / 5839 | 0.9942 | 331.0 | 933.5 |
| 4 | 4252 / 4385 | 0.9904 | 244.0 | 688.0 |
| 5 | 3324 / 3527 | 0.9883 | 196.8 | 545.0 |
| 6 | 2792 / 2921 | 0.9865 | 162.0 | 457.0 |
| 8 | 2097 / 2218 | 0.9787 | 121.0 | 329.5 |
| 10 | 1656 / 1760 | 0.9745 | 96.0 | 271.5 |
| 12 | 1367 / 1516 | 0.9695 | 75.9 | 221.5 |

Interpretation: the serious K candidates can already be narrowed locally to approximately `{2,3,4,6}`. K>=8 is still possible but begins paying a clear per-view information/sparsity cost. This is a screening result, not a final K freeze.

A final K requires the rebuilt FULL104 per-view spectrum, conditioning, nuisance predictability, positive-control recovery and null calibration, but it was unnecessary to treat K=2 as the only option before the heavy run.

### 3. Source-conditioned exchangeability constraints — DERIVABLE HERE

Historical metadata/sampler files give 104 fit donors distributed as:

- HVS: 41 donors
- NPH52: 17 donors
- SEA_AD: 46 donors

The historical geometry review already states donors are disjoint across sources. Current heavy reconnaissance independently confirms donors/operators/support-patterns are nested within source.

Therefore whole-donor permutation across source is not lawful. Candidate donor exchangeability must be conditioned on source unless a separately justified conditional-randomization model is used.

### 4. Measurement-depth intervention range — DERIVABLE/NARROWABLE HERE

The frozen 50K discovery sample contains `source_library` for every sampled cell.

Global source-library quantiles:

- p01 1,224
- p05 2,647
- p10 3,881
- p25 7,560
- p50 16,127
- p75 32,520
- p90 54,224
- p95 71,246
- p99 115,969

By source, medians are approximately:

- HVS 14,149
- NPH52 8,151
- SEA_AD 19,243

This is enough to prospectively define candidate same-cell thinning ladders from real measurement geometry before representation-level qualification. The exact final ladder should be source-aware and must be frozen before applying it to decision-bearing representations.

### 5. Support-pattern geometry — DERIVABLE HERE

The calibration/support assets reproduce:

- 42 operators;
- 9 distinct support patterns;
- 17,186-address universal common core;
- HVS scalar support ~45.4%;
- NPH52 source-weighted scalar support ~80.7%;
- SEA_AD ~85.1%.

This is sufficient to design support-only falsification controls and common-core/operator-native comparator contracts locally.

### 6. Neighborhood/grid scales — ALREADY HISTORICALLY PROSPECTIVE

The historical discovery geometry contract already froze exploratory geometry scales:

- cosine kNN `k={15,30,60,120}`;
- community resolutions `{0.25,0.5,1.0,2.0}`;
- 50 SVD components or maximum supported rank.

These are historical discovery settings, not automatically current V5 D_shared authority, but they should be reused as sensitivity/reference scales rather than re-invented.

### 7. Nuisance variables that must be challenged — DERIVABLE HERE

Historical shortcut evidence and metadata establish source, operator/support state and depth as major nuisance channels. The current V5 nuisance challenge should therefore at least consider:

- source/technology;
- operator nested within source;
- measurement support pattern;
- source-library/depth;
- detection/support quantities;
- donor identity for generalization/leverage.

Because source and operator are nested, separate causal interpretation of source and operator is not identifiable internally.

### 8. Donor-disjoint evaluation requirement — DERIVABLE/HISTORICALLY SUPPORTED HERE

Historical discovery explicitly required donor-block resampling. Existing reader splits and donor metadata permit donor-disjoint mechanics checks locally. Random cell-level CV should not be treated as generalization evidence.

## Parameters that can be narrowed here but should NOT be finally frozen here

- final K (local evidence narrows serious range roughly to 2/3/4/6);
- exact deterministic canonical K-way partition namespace;
- final rank envelope;
- exact nuisance model family/ridge strength;
- exact within-source donor-vs-within-operator null choice;
- exact positive-control amplitudes;
- exact measurement-thinning acceptance thresholds.

These need rebuilt FULL104 feature geometry or complete-procedure calibration.

## Parameters that genuinely require the heavy rebuilt FULL104 substrate

- per-view production-scale covariance/eigen-spectrum and supported rank;
- per-view source/operator/QC predictability after the new common-core rebuild;
- full-population null mobility under candidate exchangeability units;
- production-scale positive/negative control recovery;
- final comparison of K candidates if local screening does not separate 2/3/4/6;
- final V3 null qualification and final rank-support authority.

## Corrected sequencing rule

Before any future heavy rebuild or long GPU/CPU run:

1. inventory local historical discovery/calibration assets;
2. derive every structural parameter possible from support/metadata/frozen discovery samples;
3. narrow candidate families locally;
4. freeze the heavy-run question and outputs;
5. only then launch full-population execution.

For the present run, Claude's K=2 rebuild should finish because it remains a valuable full-scale reference substrate. But K=2 must not be promoted merely because it was computed first.

## Hard boundary

`LOCAL_PARAMETER_SCREENING_ONLY__NO_D_SHARED_OUTCOME_ACCESS__NO_TRAINING_AUTHORITY`
