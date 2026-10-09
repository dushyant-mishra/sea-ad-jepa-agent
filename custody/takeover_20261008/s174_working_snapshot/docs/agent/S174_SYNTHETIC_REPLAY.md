# S174 synthetic replay

V77 synthetic results whose statistics were computed on the cache-derived evaluation universe, rerun on the corrected universe with nothing else changed. JSON record: `results/v77/s174_replay/S174_SYNTHETIC_REPLAY_V1.json`.

Rule: each replay reran the committed runner with the receipt's original arguments; only the universe (and --out) changed; a rerun on the old universe reproduced each committed receipt first; no seed, arm, preprocessing or scoring rule changed and no arm was tuned after the corrected target was seen.

## Statistical ruling

- pooled envelopes: not qualification targets until S159 is resolved
- real point estimates: descriptive reference values
- donor resampled distributions: uncertainty diagnostics
- binary inside every envelope decision: not made
- recentring: not done; an interval is never moved to make the point fit
- why: S159: the corrected real point lies outside its own donor-bootstrap p05-p95 interval for some statistics, so a candidate identical to the real point could fail a gate built on these intervals

Every cell below is a description: the ratio to the real point, and in brackets the position relative to the donor-bootstrap interval (`point only` where the reference has no interval). Nothing passes, fails or is selected.

S159: the corrected real point lies outside its own interval for expression.median_abs_corr, detection.transitivity.

Universe label: the runners write TRAIN_PREVALENCE05_19569, the builder's fixed name for the frozen universe; in s174_replay it denotes the corrected 14,417-address universe. S130: abundance max/median on the frozen universe divides by the median of nonzero gene means and so also penalises detection coverage; read it that way.

## Reproduction on the old universe

| receipt | exact | numeric leaves |
|---|---|---|
| V77_REALIZATION_ISOLATION_RECEIPT_V2.json | True | 106 |
| V77_DYNAMIC_RANGE_TOURNAMENT_V2.json | True | 253 |
| V77_DYNAMIC_RANGE_TOURNAMENT_V2__WITHIN_HVS_EXPLORATORY.json | True | 253 |
| V77_DYNAMIC_RANGE_TOURNAMENT_V2__WITHIN_SEA_AD_EXPLORATORY.json | True | 253 |

Superseded before S174, not replayed:

- `V77_REALIZATION_ISOLATION_RECEIPT_V1.json`: superseded by V2 (S139/S140 scorer mismatch); not replayed
- `V77_DYNAMIC_RANGE_TOURNAMENT_V1.json`: superseded by V2 (S129/S138 DR5, S139/S140 scorer mismatch); not replayed

## Reference values

| invariant | old point | corrected point | corrected interval | corrected point inside its own interval |
|---|---|---|---|---|
| expression.median_abs_corr | 0.3291 | 0.0562 | [0.0569, 0.0591] | False |
| expression.frac_abs_gt_0p3 | 0.5621 | 0.0242 | [0.0233, 0.026] | True |
| expression.var_top10_pc | 0.5089 | 0.262 | [0.2613, 0.2679] | True |
| detection.median_abs_corr | 0.377 | 0.1946 | [0.1889, 0.1965] | True |
| detection.frac_abs_gt_0p3 | 0.6148 | 0.1348 | [0.1242, 0.1513] | True |
| detection.mean_degree | 1843.804 | 404.3647 | [372.4921, 453.687] | True |
| detection.transitivity | 0.8871 | 0.6672 | [0.6454, 0.667] | False |
| detection.largest_community_frac | 0.763 | 0.1367 | [0.127, 0.2128] | True |
| class_separation.t5_within_over_pooled | 1.0118 | 0.7435 | - | - |
| abundance.abundance_max_over_median_nonzero | 1976.6481 | 2273.2075 | [2183.824, 2382.7249] | True |
| abundance.top1pct_count_share | 0.2457 | 0.2741 | [0.2716, 0.2767] | True |
| depth.median_detected_per_cell | 4467.0 | 4495.5 | - | - |

## Per-arm description against the corrected real values (corrected universe)

| arm | expr med|r| | expr |r|>0.3 | expr top10 var | det med|r| | det |r|>0.3 | det degree | det transitivity | det community | T5 | max/median | top1% | detected/cell |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A_deterministic | 2.922 (above) | 8.3527 (above) | 1.6294 (above) | 0.8116 (below) | 2.0903 (above) | 2.0903 (above) | 1.1145 (above) | 5.6415 (above) | 1.3673 (point only) | 2.7039 (above) | 1.7641 (above) | 0.4794 (point only) |
| B_poisson | 0.9367 (below) | 0.3483 (below) | 0.6369 (below) | 0.5113 (below) | 0.0182 (below) | 0.0182 (below) | 0.5061 (below) | 0.0024 (below) | 1.6258 (point only) | 8.8631 (above) | 1.7725 (above) | 0.3966 (point only) |
| DR1_scale_1p20_baseline | 0.9367 (below) | 0.3483 (below) | 0.6369 (below) | 0.5113 (below) | 0.0182 (below) | 0.0182 (below) | 0.5061 (below) | 0.0024 (below) | 1.6258 (point only) | 8.8631 (above) | 1.7725 (above) | 0.3966 (point only) |
| DR2_scale_2p50 | 1.9039 (above) | 3.7222 (above) | 1.1174 (above) | 0.4467 (below) | 0.9921 (in) | 0.9921 (in) | 1.1669 (above) | 0.9195 (below) | 1.4086 (point only) | 10.3872 (above) | 1.808 (above) | 0.3537 (point only) |
| DR3_scale_4p00 | 2.4151 (above) | 6.6747 (above) | 1.4041 (above) | 0.3258 (below) | 1.7279 (above) | 1.7279 (above) | 1.3139 (above) | 4.1829 (above) | 1.3788 (point only) | 11.0413 (above) | 1.822 (above) | 0.3268 (point only) |
| DR4_scale_5p50 | 2.5353 (above) | 7.3375 (above) | 1.4979 (above) | 0.3098 (below) | 1.8468 (above) | 1.8468 (above) | 1.3283 (above) | 4.5073 (above) | 1.375 (point only) | 11.225 (above) | 1.8251 (above) | 0.3141 (point only) |
| DR5_true_on_off | 2.5671 (above) | 7.422 (above) | 1.5186 (above) | 0.3105 (below) | 1.8616 (above) | 1.8616 (above) | 1.3329 (above) | 2.8366 (above) | 1.3729 (point only) | 11.1246 (above) | 1.8254 (above) | 0.3108 (point only) |

## The same arms against the old real values (old universe), for comparison

| arm | expr med|r| | expr |r|>0.3 | expr top10 var | det med|r| | det |r|>0.3 | det degree | det transitivity | det community | T5 | max/median | top1% | detected/cell |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A_deterministic | 0.5419 (below) | 0.3978 (below) | 0.8606 (below) | 0.3715 (below) | 0.4296 (below) | 0.4296 (below) | 0.8307 (below) | 0.9996 (in) | 0.9991 (point only) | 3.8579 (above) | 2.1098 (above) | 0.5544 (point only) |
| B_poisson | 0.1811 (below) | 0.0198 (below) | 0.354 (below) | 0.2711 (below) | 0.0049 (below) | 0.0049 (below) | 0.392 (below) | 0.0004 (below) | 1.1503 (point only) | 13.5347 (above) | 2.1147 (above) | 0.4662 (point only) |
| DR1_scale_1p20_baseline | 0.1811 (below) | 0.0198 (below) | 0.354 (below) | 0.2711 (below) | 0.0049 (below) | 0.0049 (below) | 0.392 (below) | 0.0004 (below) | 1.1503 (point only) | 13.5347 (above) | 2.1147 (above) | 0.4662 (point only) |
| DR2_scale_2p50 | 0.3669 (below) | 0.2011 (below) | 0.616 (below) | 0.2239 (below) | 0.2496 (below) | 0.2496 (below) | 0.9179 (below) | 0.1708 (below) | 1.0227 (point only) | 15.6064 (above) | 2.1455 (above) | 0.4214 (point only) |
| DR3_scale_4p00 | 0.4615 (below) | 0.3378 (below) | 0.771 (below) | 0.1629 (below) | 0.399 (below) | 0.399 (below) | 1.0193 (above) | 0.8156 (below) | 1.0081 (point only) | 16.5892 (above) | 2.1585 (above) | 0.3899 (point only) |
| DR4_scale_5p50 | 0.4818 (below) | 0.3625 (below) | 0.8216 (below) | 0.159 (below) | 0.4151 (below) | 0.4151 (below) | 1.026 (above) | 0.8602 (below) | 1.0057 (point only) | 16.5975 (above) | 2.1622 (above) | 0.3774 (point only) |
| DR5_true_on_off | 0.4877 (below) | 0.3656 (below) | 0.8339 (below) | 0.1613 (below) | 0.418 (below) | 0.418 (below) | 1.0287 (above) | 0.5011 (below) | 1.0041 (point only) | 16.9206 (above) | 2.1623 (above) | 0.3747 (point only) |

## Which corrected invariants the replayed arms span

Distinct arms: A_deterministic, B_poisson, DR2_scale_2p50, DR3_scale_4p00, DR4_scale_5p50, DR5_true_on_off (DR1 is the same arm as B_poisson and is counted once). A bracketed invariant is one whose real value lies between the lowest and highest arm; this describes what the family spans and ranks nothing.

| invariant | lowest arm / point | highest arm / point | real value bracketed |
|---|---|---|---|
| expression.median_abs_corr | 0.9367 | 2.922 | True |
| expression.frac_abs_gt_0p3 | 0.3483 | 8.3527 | True |
| expression.var_top10_pc | 0.6369 | 1.6294 | True |
| detection.median_abs_corr | 0.3098 | 0.8116 | False |
| detection.frac_abs_gt_0p3 | 0.0182 | 2.0903 | True |
| detection.mean_degree | 0.0182 | 2.0903 | True |
| detection.transitivity | 0.5061 | 1.3329 | True |
| detection.largest_community_frac | 0.0024 | 5.6415 | True |
| class_separation.t5_within_over_pooled | 1.3673 | 1.6258 | False |
| abundance.abundance_max_over_median_nonzero | 2.7039 | 11.225 | False |
| abundance.top1pct_count_share | 1.7641 | 1.8254 | False |
| depth.median_detected_per_cell | 0.3108 | 0.4794 | False |

Class separation: every replayed arm has a within-class over pooled ratio of 1.0166 to 1.2087, against a corrected real 0.7435: none reproduces the part of the real pooled dependence that comes from broad cell-class separation. The substate decision records that its sub-states are drawn independently of annotated cell class by construction, which is consistent with this. Recorded as a constraint on the next design; it does not change this replay.


## Realization isolation (V2)

Reading: between arms identical except realization, Poisson counting lowers detection transitivity from 0.7436 to 0.3377 and mean degree from 845.2427 to 7.342 on the corrected universe (old universe: 0.7369 to 0.3477, 792.14 to 9.0133); the collapse persists. Relative to the corrected real points the deterministic arm is 1.1145 and 2.0903 times, the Poisson arm 0.5061 and 0.0182 times.

The audit correction's headline figures came from topology_v1_binary_hvg__NOT_COMPARABLE_TO_REAL (S139/S140), old universe: {"A_deterministic": {"frac_abs_gt_0p3": 0.5208, "transitivity": 0.7645, "mean_degree": 1561.7587}, "B_poisson": {"frac_abs_gt_0p3": 0.0028, "transitivity": 0.3555, "mean_degree": 8.3647}}.

## Dynamic-range tournament (V2)

Recorded verdict: `HYPOTHESIS_CONFIRMED__ALL_ARMS_REJECTED_BY_PREDECLARED_RULES` (cites `results/v77/V77_DYNAMIC_RANGE_TOURNAMENT_V1.json`). the verdict was written on tournament V1, whose DR5 values the register withdrew (S129) and whose scorer was not comparable to the real envelopes (S139/S140); its claims are restated here with the V2 matched numbers.

Transitivity rises monotonically over the graded arms: {'old_universe': True, 'corrected_universe': True}; mean degree: {'old_universe': True, 'corrected_universe': True}.

Reading: detection transitivity above the real point: DR3_scale_4p00, DR4_scale_5p50, DR5_true_on_off on the old universe against the old point; DR2_scale_2p50, DR3_scale_4p00, DR4_scale_5p50, DR5_true_on_off on the corrected universe against the corrected point, so the verdict's 'the mechanism overshoots the real transitivity' was measured against the old point. The grounds the verdict recorded for rejecting every arm remain against the corrected references: abundance max/median lies outside the corrected interval for 5 of 5 arms, and the median detected per cell is 0.3108 to 0.3966 times the corrected real value.

### The 12-fold arm (DR2_scale_2p50): OBSERVATION; NOT A WINNER; NOT SELECTED

on the corrected universe the 12-fold arm lands close to the corrected real detection density (0.1338 against 0.1348, 0.9921 times, inside the interval) and mean degree (401.1713 against 404.3647, 0.9921 times, inside). Its transitivity overshoots (0.7786 against 0.6672, 1.1669 times); its abundance max/median is 10.3872 times the real point (above the interval) and its median detected per cell 0.3537 times the real value, so the abundance and depth objections the verdict recorded still apply. It is recorded as an observation, not as a winner or a selected model.

Objections the verdict recorded for this arm: abundance max/median 30848.3 outside frozen envelope [1804.8, 2187.7]; abundance WORSENS versus the baseline arm (30848.3 against 26753.4); depth marginal distorted: 1882 detected per cell against a real 4467.

## Exploratory within-cohort variants

EXPLORATORY; within-cohort references are not authorized for synthetic pass or fail, and none are applied.

`V77_DYNAMIC_RANGE_TOURNAMENT_V2__WITHIN_HVS_EXPLORATORY.json` (universe TRAIN_WITHIN_HVS_PREVALENCE05_13326 to TRAIN_WITHIN_HVS_PREVALENCE05_13326):

| arm | median abs corr | frac > 0.3 | transitivity | mean degree |
|---|---|---|---|---|
| DR1_scale_1p20_baseline | 0.0942 / 0.0982 | 0.0017 / 0.0022 | 0.3691 / 0.3834 | 5.024 / 6.484 |
| DR2_scale_2p50 | 0.0821 / 0.0857 | 0.1218 / 0.131 | 0.7743 / 0.7842 | 365.19 / 392.7507 |
| DR3_scale_4p00 | 0.0608 / 0.0637 | 0.2191 / 0.2295 | 0.8696 / 0.8695 | 657.0513 / 688.2093 |
| DR4_scale_5p50 | 0.0593 / 0.0614 | 0.2375 / 0.2468 | 0.8817 / 0.8806 | 712.2633 / 740.0113 |
| DR5_true_on_off | 0.0594 / 0.0618 | 0.2397 / 0.2492 | 0.8839 / 0.882 | 718.8407 / 747.3847 |

`V77_DYNAMIC_RANGE_TOURNAMENT_V2__WITHIN_SEA_AD_EXPLORATORY.json` (universe TRAIN_WITHIN_SEA_AD_PREVALENCE05_14948 to TRAIN_WITHIN_SEA_AD_PREVALENCE05_15158):

| arm | median abs corr | frac > 0.3 | transitivity | mean degree |
|---|---|---|---|---|
| DR1_scale_1p20_baseline | 0.0871 / 0.1018 | 0.0024 / 0.0051 | 0.3271 / 0.3407 | 7.2173 / 15.24 |
| DR2_scale_2p50 | 0.0829 / 0.0921 | 0.0985 / 0.1469 | 0.7461 / 0.7915 | 295.496 / 440.5207 |
| DR3_scale_4p00 | 0.0654 / 0.069 | 0.1917 / 0.2363 | 0.8261 / 0.8795 | 574.972 / 708.718 |
| DR4_scale_5p50 | 0.0616 / 0.0656 | 0.2123 / 0.2526 | 0.8419 / 0.8863 | 636.6413 / 757.5527 |
| DR5_true_on_off | 0.0609 / 0.0654 | 0.2152 / 0.2542 | 0.8465 / 0.8878 | 645.3507 / 762.4067 |

Exploratory cells give old universe / corrected universe.
