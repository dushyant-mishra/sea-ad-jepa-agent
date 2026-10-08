# S174 corrected replay: old and corrected numbers side by side

**schema:** S174_REPLAY_SUMMARY_V1

**status:** CORRECTED_REPLAY_COMPLETE for the nine affected V77 real-data results. Old results stay in results/v77 unchanged; corrected ones are in results/v77/s174_replay under the same names

## cache

**old:** data/cache/stage81a3r_corrected_real_train (S174: scrambled gene axis for HVS and SEA-AD)

**corrected:** data/cache/s174_rebuilt_real_train_v1 (fresh gene-ID join; authorized by G1b)

**same_cells:** True

## S149

**question:** how much of the frozen pooled real detection topology does cohort coverage alone produce?

### pooled_vs_coverage_only_null

| statistic | pooled_old | pooled_corrected | null_old | null_corrected | null_share_old | null_share_corrected |
|---|---|---|---|---|---|---|
| frac_abs_gt_0p3 | 0.6148 | 0.1348 | 0.5463 | 0.0042 | 0.8885 | 0.0314 |
| median_abs_corr | 0.377 | 0.1946 | 0.3273 | 0.013 | 0.8682 | 0.0667 |
| mean_degree | 1843.804 | 404.3647 | 1638.2193 | 12.6873 | 0.8885 | 0.0314 |
| largest_community_frac | 0.763 | 0.1367 | 0.6777 | 0.0567 | 0.8882 | 0.4146 |
| transitivity | 0.8871 | 0.6672 | 0.8967 | 0.8652 | 1.0108 | 1.2967 |

### within_single_stratum_frac_abs_gt_0p3

| stratum | old | corrected |
|---|---|---|
| HVS | 0.0768 | 0.1083 |
| NPH52 | 0.0312 | 0.2078 |
| SEA_AD | 0.0602 | 0.2319 |

### coverage_strata

**agreement_old:** 1.0

**agreement_corrected:** 1.0

#### cells_per_stratum_old

**HVS:** 3072

**NPH52:** 246

**SEA_AD:** 1408

**NONE:** 0

#### cells_per_stratum_corrected

**HVS:** 3072

**NPH52:** 246

**SEA_AD:** 1408

**NONE:** 0

**answer:** Under the corrected input, cohort coverage alone reproduces about 3% of the pooled fraction of strong correlations (0.0042 of 0.1348), not about 89% (0.546 of 0.615). The pooled value itself falls from 0.615 to 0.135 and now lies within the range of the single-cohort values (0.108 to 0.232) rather than far above them

### what_survives

- cohort coverage still identifies the study perfectly (agreement 1.0 before and after)

### what_does_not

- pooled real dependence dominated by cohort composition: 3% of it, not 89%, is produced by coverage alone
- 'within one study the dependence is several times weaker': within-study values are now at or above the pooled one

**interpretation_rule:** per the owner: S149 was not assumed false; its input was corrupted, and this corrected replay decides. The pooled-composition headline does not survive; the strata finding does

**status:** S149_CORRECTED: the old numbers are history of a corrupted input; the corrected numbers are the evidence

## detection_envelope_points

| statistic | old | corrected |
|---|---|---|
| frac_abs_gt_0p3 | 0.6148 | 0.1348 |
| median_abs_corr | 0.377 | 0.1946 |
| var_top10_pc | 0.5602 | 0.3349 |
| mean_degree | 1843.804 | 404.3647 |
| transitivity | 0.8871 | 0.6672 |
| pos_over_neg_ratio | 1.6686 | 59.0185 |

## expression_envelope_points

| statistic | old | corrected |
|---|---|---|
| frac_abs_gt_0p3 | 0.5621 | 0.0242 |
| median_abs_corr | 0.3291 | 0.0562 |
| var_top10_pc | 0.5089 | 0.262 |
| mean_degree | 1685.8173 | 72.7047 |
| transitivity | 0.8605 | 0.5127 |
| substitute_frac | 0.1983 | 0.0167 |

## topology

| statistic | old | corrected |
|---|---|---|
| T5 mean within-class median /corr/ | 0.3329 | 0.0418 |
| T3 global transitivity | 0.8605 | 0.5127 |
| T1 mean degree | 1685.8173 | 72.7047 |

## abundance_envelope_points

| statistic | old | corrected |
|---|---|---|
| abundance_max_over_median_nonzero | 1976.6481 | 2273.2075 |
| top1pct_count_share | 0.2457 | 0.2741 |

## evaluation_universe

**old:** 19569

**corrected:** 14417

**shared:** 11230

**jaccard:** 0.4935

## within_cohort_v2

### points

| statistic | old | corrected |
|---|---|---|
| HVS.detection.frac_abs_gt_0p3 | 0.1146 | 0.1146 |
| HVS.detection.median_abs_corr | 0.1944 | 0.1944 |
| HVS.expression.frac_abs_gt_0p3 | 0.0169 | 0.0169 |
| HVS.expression.median_abs_corr | 0.0545 | 0.0545 |
| HVS.expression.var_top10_pc | 0.2336 | 0.2336 |
| SEA_AD.detection.frac_abs_gt_0p3 | 0.2394 | 0.2427 |
| SEA_AD.detection.median_abs_corr | 0.2273 | 0.2285 |
| SEA_AD.expression.frac_abs_gt_0p3 | 0.0375 | 0.0382 |
| SEA_AD.expression.median_abs_corr | 0.0665 | 0.0667 |
| SEA_AD.expression.var_top10_pc | 0.2793 | 0.2811 |

**reading:** HVS is bit-identical: inside one family the scramble was only a relabelling, so label-free within-cohort statistics were never affected. SEA-AD moves slightly because collision exclusion now removes the right genes and recovers others. NPH52 is below the eligibility floor in both

**consequences_for_the_synthetic_lane:** the corrected real expression geometry (median |corr| among highly variable genes 0.056, 2.4% of pairs above 0.3, 26% of variance in the top 10 components) is close to the original synthetic generator's (0.0675 and 2.3%), whereas the old targets (0.329, 56%, 51%) were produced by the scramble. The V77 Step 3 background search, the factor-family falsification and the Observer-V2 decision were judged against the old targets and are re-scored in the next phase; nothing is tuned on these outcomes

**identity_note:** the 353 historical-Ensembl-ID-to-different-symbol mappings were followed as frozen and remain flagged for the identity lane

## side_by_side

**path:** results/v77/s174_replay/S174_REPLAY_SIDE_BY_SIDE_V1.json

**sha256:** ffc2cd36d6463aede69e63f0dd1c068f21fc837ca1436831105bbc0fe263fbcc

**note:** every numeric leaf of the nine results, old beside corrected

**recorded_utc:** 2026-10-07T20:35:42Z

**head_when_recorded:** 4ab8e2101f2e595d9a97df05517d6e672768ecec
