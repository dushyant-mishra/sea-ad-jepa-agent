# S174 downstream re-score

Old and corrected numbers side by side for the V77 synthetic-lane records judged against the real targets. Recorded synthetic statistics are re-scored under each record's own rule; nothing is generated, tuned or selected. JSON record: `results/v77/s174_replay/S174_DOWNSTREAM_RESCORE_V1.json`.

## S159 (open)

- `V77_REAL_CALIBRATION_ENVELOPE_V1.json::corrected`: point outside its own p05-p95 band on median_abs_corr
- `V77_REAL_DETECTION_ENVELOPE_V1.json::corrected`: point outside its own p05-p95 band on transitivity

Resampling: {'unit': 'donor', 'n_bootstrap': 20}. under the recorded rule a candidate identical to the corrected real point would fail on these targets; a count of targets inside the band is therefore capped below the number of targets and is read beside the ratio to the point.

## Background search rounds

Recorded rule: a candidate must land inside the donor-resampled 5th-to-95th percentile envelope on EVERY target individually; improvement alone is not acceptance.

Re-scorer faithful to every recorded count: **True**. 18 recorded entries, 16 distinct candidates (the two candidate-search files duplicate rounds 1 and 2 and are counted once). Accepted under the old envelope: 0; under the corrected: 0. Most targets inside: 5/11 old, 2/11 corrected.

| round | candidate | recorded | old (recomputed) | corrected | median abs corr / corrected point |
|---|---|---|---|---|---|
| ROUND1 | C0_baseline_independent | 0/11 | 0/11 | 0/11 | 0.2392 |
| ROUND1 | C1_coherent_balanced | 0/11 | 0/11 | 0/11 | 0.2574 |
| ROUND1 | C2_coherent_more_factors | 0/11 | 0/11 | 0/11 | 0.3147 |
| ROUND2 | C6_few_dominant_global | 1/11 | 1/11 | 0/11 | 1.8733 |
| ROUND2 | C7_dominant_tuned_noise | 1/11 | 1/11 | 0/11 | 2.3263 |
| ROUND2 | C8_dominant_plus_midband | 0/11 | 0/11 | 2/11 | 1.2733 |
| ROUND3 | E2_two_dominant_calibrated | 0/11 | 0/11 | 0/11 | 2.4833 |
| ROUND4 | E2_two_dominant_calibrated | 4/11 | 4/11 | 1/11 | 6.0585 |
| ROUND4 | C6_few_dominant_global | 0/11 | 0/11 | 0/11 | 3.8343 |
| ROUND5 | F1_two_dom_more_mid | 0/11 | 0/11 | 0/11 | 4.1526 |
| ROUND5 | F2_two_dom_strong_mid | 0/11 | 0/11 | 1/11 | 2.0716 |
| ROUND5 | F3_three_dom_rich_mid | 0/11 | 0/11 | 0/11 | 1.4955 |
| ROUND6 | G1_interp_60mid | 4/11 | 4/11 | 0/11 | 6.0644 |
| ROUND6 | G2_interp_90mid | 0/11 | 0/11 | 0/11 | 5.3867 |
| ROUND6 | G3_interp_120mid | 1/11 | 1/11 | 0/11 | 4.7117 |
| ROUND7 | H1_dom_cover82 | 5/11 | 5/11 | 0/11 | 6.2769 |
| ROUND7 | H2_dom_cover70 | 4/11 | 4/11 | 0/11 | 6.2309 |
| ROUND7 | H3_dom_cover82_richmid | 0/11 | 0/11 | 0/11 | 5.1247 |

Where the recorded entries sit (finite values only):

| statistic | old point | corrected point | recorded range | below old | above old | below corrected | above corrected |
|---|---|---|---|---|---|---|---|
| median_abs_corr | 0.3291 | 0.0562 | 0.0134 to 0.3528 | 14 | 4 | 3 | 15 |
| frac_abs_gt_0p3 | 0.5621 | 0.0242 | 0.0 to 0.5875 | 16 | 2 | 5 | 13 |
| var_top10_pc | 0.5089 | 0.262 | 0.0283 to 0.6885 | 9 | 9 | 4 | 14 |
| mean_degree | 1685.8173 | 72.7047 | 0.0 to 1761.9713 | 16 | 2 | 5 | 13 |
| transitivity | 0.8605 | 0.5127 | 0.2834 to 0.9527 | 10 | 7 | 4 | 13 |

## Step 3 background calibration

Recorded verdict: `STEP_3_NOT_CLOSED__LATENT_MECHANISM_SOLVED__OBSERVATION_MODEL_IS_THE_BINDING_CONSTRAINT`.

**Premise 1, latent mechanism matched real geometry** (C6_few_dominant_global). Recorded: the latent layer reproduces real dependence geometry closely on five of six targets. Corrected: the 5 statistics the record called close are 6.134 to 47.5315 times the corrected points; transitivity, the one it missed, is 1.071 times.

| statistic | latent | old real | corrected real | latent / old | latent / corrected |
|---|---|---|---|---|---|
| median_abs_corr | 0.3447 | 0.3291 | 0.0562 | 1.0476 | 6.134 |
| frac_abs_gt_0p3 | 0.5563 | 0.5621 | 0.0242 | 0.9896 | 22.945 |
| frac_pos_gt_0p3 | 0.2781 | 0.2964 | 0.0184 | 0.9383 | 15.1229 |
| frac_neg_lt_m0p3 | 0.2781 | 0.2657 | 0.0059 | 1.0467 | 47.5315 |
| mean_degree | 1668.2107 | 1685.8173 | 72.7047 | 0.9896 | 22.945 |
| transitivity | 0.5491 | 0.8605 | 0.5127 | 0.6382 | 1.071 |

**Premise 2, observation attenuates correlation.** Recorded: after observation the best candidates reach median |corr| about 0.22 against a target of 0.33, mean degree about 950 against 1686, transitivity about 0.55 against 0.86, while var_top10_pc runs HIGH at 0.68 against 0.509. Corrected: the recorded figures fell short of the old target on median_abs_corr, mean_degree, transitivity; 3 of those 3 are above the corrected point (median_abs_corr, mean_degree, transitivity), so there the shortfall the record attributed to the observation model exists only against the old target; the figure it recorded as running high stays high against the corrected point: var_top10_pc (2.5953 times).

| statistic | recorded after observation | recorded target | corrected point | recorded / corrected |
|---|---|---|---|---|
| median_abs_corr | 0.22 | 0.33 | 0.0562 | 3.9145 |
| mean_degree | 950.0 | 1686.0 | 72.7047 | 13.0666 |
| transitivity | 0.55 | 0.86 | 0.5127 | 1.0727 |
| var_top10_pc | 0.68 | 0.509 | 0.262 | 2.5953 |

**Premise 3, correlation and rank cannot both be met.** Recorded: fewer dominant factors raise correlation but push the rank too low; more factors lower correlation. Within this model family the two cannot be satisfied together after observation. Corrected: the trap was stated for raising correlation toward the old target without pushing the rank too low; against the corrected targets the recorded figures are above the real value on both, so meeting them would need lower correlation and a less dominant top-10 rank together, which is not the trade-off recorded.

## Factor-family falsification

Recorded verdict: `FACTOR_MODEL_FAMILY_FALSIFIED__INCLUDING_THE_TWO_LAYER_HURDLE_EXTENSION`.

- Invariant: global transitivity, recorded real 0.8871 (band [0.8752, 0.8928]), family range [0.515, 0.775] over 11 recorded configurations.
- Corrected detection 0.6672 (band [0.6454, 0.667], point inside own band: False); corrected expression 0.5127 (band [0.5019, 0.5184]).
- Recorded configurations inside the corrected detection band: 0; inside the corrected expression band: 1.
- Edge density at the real point (mean degree over 2999): old 0.6148, corrected 0.1348.
- Corrected: the record's invariant is on the detection layer (its recorded real 0.8871 is the old detection point) and falsified the family because transitivity never approached it at an edge density of 0.6148. The corrected detection value 0.6672 is inside the range the family produced [0.515, 0.775], at an edge density of 0.1348, so the stated reason no longer holds. The corrected expression value 0.5127 is below the lowest recorded value 0.515. This does not show that the family fits the corrected targets: that was never scored.

Second structural tension, recorded: the correlation targets and the rank/community targets move in opposite directions under every lever tested. Corrected points: {"median_abs_corr": 0.0562, "var_top10_pc": 0.262, "largest_community_frac": 0.2377}.

- H1 single-layer: recorded inside 5 of 11; over the corrected point {"median_abs_corr": 6.2775, "var_top10_pc": 2.4949, "largest_community_frac": 4.1373}
- independent fraction 0.40: recorded inside 1 of 11; over the corrected point {"median_abs_corr": 2.6957, "var_top10_pc": 2.1636, "largest_community_frac": 3.0198}

Two-layer findings, corrected: detection still carries more dependence than expression (corrected 0.1946 against 0.0562) and is still more positively skewed, so the direction of the two-layer findings survives; their magnitudes, and every synthetic value the record placed inside an old envelope, were measured against the inflated targets.

| statistic | detection old | detection corrected | expression old | expression corrected |
|---|---|---|---|---|
| median_abs_corr | 0.377 | 0.1946 | 0.3291 | 0.0562 |
| pos_over_neg_ratio | 1.6686 | 59.0185 | 1.1156 | 3.1432 |
| mean_signed_corr | 0.1016 | 0.1774 | 0.0322 | 0.0257 |
| largest_community_frac | 0.763 | 0.1367 | 0.8243 | 0.2377 |
| var_top10_pc | 0.5602 | 0.3349 | 0.5089 | 0.262 |

## Observer-V2 decision

Recorded decision: `OBSERVER_V2_SUPPORTED_FOR_NEXT_STAGE`. Recorded answer: YES for the coupling. Decoupling removes the trade-off: at FULL abundance scale the topology is nearly restored, with the fraction above 0.3 at 0.6154 against a real 0.6148 and mean degree at 1846 against a real 1844. The abundance marginal is retained rather than collapsed. The residual gap is a DIFFERENT mechanism.

Corrected: the decision cited the deterministic-threshold variant reproducing the real fraction above 0.3 and mean degree essentially exactly; those real values are the old detection points. Against the corrected points, on the four topology statistics, the deterministic variant is 1.2346 to 4.5652 times the real value and the Poisson variant, recorded as destroying detection correlation, 0.0438 to 0.7011 times.

| variant | frac abs corr > 0.3 (/ corrected) | mean degree (/ corrected) | transitivity (/ corrected) | median abs corr (/ corrected) |
|---|---|---|---|---|
| decoupled + DETERMINISTIC threshold | 0.6154 (4.5642) | 1846 (4.5652) | 0.8238 (1.2346) | 0.3486 (1.7917) |
| decoupled + POISSON realization | 0.0059 (0.0438) | 18 (0.0445) | 0.3558 (0.5332) | 0.1364 (0.7011) |
| REAL | 0.6148 (4.5597) | 1843.8 (4.5597) | 0.8871 (1.3295) | 0.377 (1.9377) |

Roster, recorded: every candidate failed on topology = True; best O6_wide_capture_plus_cell_state, transitivity 0.6650 and degree 328.

| candidate | topology inside old | inside corrected | median abs corr | frac > 0.3 | transitivity | mean degree | largest community | max/median | top1% |
|---|---|---|---|---|---|---|---|---|---|
| O1_null_capture_constant | 0/5 | 0/5 | 0.7509 | 0.0796 | 0.5855 | 0.0796 | 0.0024 | 0.2467 | 0.8819 |
| O2_capture_independent_moderate | 0/5 | 0/5 | 0.7342 | 0.0641 | 0.5574 | 0.0641 | 0.0024 | 0.5276 | 1.048 |
| O3_capture_independent_wide | 0/5 | 0/5 | 0.7082 | 0.0479 | 0.5754 | 0.0479 | 0.0024 | 1.5448 | 1.4182 |
| O4_capture_anticorrelated | 0/5 | 0/5 | 0.7525 | 0.0762 | 0.5593 | 0.0762 | 0.0024 | 0.3791 | 0.8941 |
| O5_poorly_captured_subpopulation | 0/5 | 0/5 | 0.7289 | 0.0611 | 0.5858 | 0.0611 | 0.0024 | 0.5468 | 1.1006 |
| O6_wide_capture_plus_cell_state | 0/5 | 1/5 | 1.1413 | 0.8121 | 0.9967 | 0.8121 | 0.0024 | 1.7691 | 1.4586 |

Roster columns after the counts are ratios to the corrected real point.

Diagnosed residual, recorded: real detection reaches a correlation of 0.377 at comparable depth, so real biological rate swings must carry genes from effectively absent to clearly present, not from 1.5 counts to 5. Corrected: real detection median abs corr 0.377 becomes 0.1946 (roster range [0.1378, 0.2221]); the median the residual was quantified on now lies inside the roster's own range; the corrected real fraction above 0.3 (0.1348) lies above the roster's range [0.0065, 0.1095], which is 0.0479 to 0.8121 times the real value.

Abundance retained, recorded: O2 at 1199 and O5 at 1243 against a real 1977, versus a collapse to about 10 under the old abundance-shrinking workaround. Corrected: real max/median 1976.6481 becomes 2273.2075.

Caveat: roster and isolation statistics were computed with each arm's own prevalence filter, which the audit correction showed to be material; the audit correction's canonical-universe numbers were computed on the old cache-derived universe and are pending a synthetic replay.

## Substate family

Search rounds: re-scorer faithful to every recorded count: **True**.

| round | candidate | expression inside (recorded / corrected) | detection inside (recorded / corrected) | which (corrected detection) |
|---|---|---|---|---|
| ROUND1 | S1_coarse | 0 / 0 | 0 / 0 | - |
| ROUND1 | S2_medium | 0 / 1 | 0 / 0 | - |
| ROUND1 | S3_fine | 0 / 0 | 0 / 0 | - |
| ROUND1 | S4_coarse_lownoise | 0 / 0 | 0 / 0 | - |
| ROUND2 | L1_two_giant | 0 / 0 | 0 / 0 | - |
| ROUND2 | L2_three_giant | 0 / 0 | 0 / 0 | - |
| ROUND2 | L3_four_giant_lownoise | 1 / 0 | 0 / 0 | - |
| ROUND2 | L4_two_giant_morestates | 0 / 0 | 0 / 0 | - |

Recorded decision: `SUPPORTED_FOR_NEXT_STAGE__WITH_TWO_NAMED_UNRESOLVED_ISSUES`. Recorded headline: the transitivity envelope was entered for the first time. Transitivity is the single invariant that falsified the factor/hurdle family, where it never left 0.515 to 0.775 across 37 candidates. The discrete sub-state family reaches 0.8844, inside the envelope of 0.8752 to 0.8928, while mean degree and the fraction above 0.3 land essentially on target.

Headline setting (L1_two_giant: two giant near-disjoint modules switched by 40 hidden sub-states; abundance prior x0.3): inside the old band on 4 of 5, inside the corrected band on 0.

| statistic | measured | recorded real (old) | corrected point | measured / corrected |
|---|---|---|---|---|
| median_abs_corr | 0.3549 | 0.377 | 0.1946 | 1.8241 |
| frac_abs_gt_0p3 | 0.6188 | 0.6148 | 0.1348 | 4.5894 |
| transitivity | 0.8844 | 0.8871 | 0.6672 | 1.3255 |
| mean_degree | 1855.9 | 1843.8 | 404.3647 | 4.5897 |
| largest_community_frac | 0.921 | 0.763 | 0.1367 | 6.739 |

The change the decision credits, recorded: the exact per-cell detected-count constraint. Every prior variant forced each cell to detect exactly k features. In real data that count is an OUTCOME of the cell's state, not a constraint on it. Corrected: against the corrected points the free-threshold model the record moved to (C) is further from the real value than the exact top-k default it replaced (A) on 4 of 5 statistics (median_abs_corr, frac_abs_gt_0p3, transitivity, mean_degree).

| model | median_abs_corr | frac_abs_gt_0p3 | transitivity | mean_degree | largest_community_frac |
|---|---|---|---|---|---|
| A exact per-cell top-k, the previous default | 0.735 | 0.4621 | 1.0319 | 0.4622 | 0.0073 |
| B free global threshold, count is an outcome, with selection noise | 1.3759 | 3.0705 | 1.1375 | 3.0707 | 5.6539 |
| C free global threshold, no selection noise | 1.6668 | 4.0821 | 1.1975 | 4.082 | 7.0295 |
| REAL binarised | 1.9377 | 4.5597 | 1.3295 | 4.5597 | 5.5829 |

Model columns are ratios to the corrected real point.

Abundance dial, recorded: a wide abundance spread gives each gene its own effective detection threshold, which breaks cliques apart under thresholding. Narrowing it lets genes in a switched module cross together. The dial brackets the target cleanly: transitivity 0.8220 at x0.5, 0.8844 at x0.3 and 0.9410 at x0.2. Corrected: the dial brackets the old target; none of the 3 recorded settings is inside the corrected band.

Issue 2, real detection positive-over-negative ratio: old 1.6686, corrected 59.0185; largest community: old 0.763, corrected 0.1367.

Issue 1: the abundance figures this issue quotes (6685, 0.322) were computed over all 41,238 addresses of the old cache and are not recomputed here; on the filtered universe the corrected abundance points are in the observer V2 section.

## T5 guard

Real within-class over pooled ratio: old 1.0118 (recorded 1.012), corrected 0.7435 (pooled 0.0562, mean within-class 0.0418).

- background rounds: recorded synthetic range [0.9982, 2.4089]
- factor family: recorded synthetic range [0.9982, 1.0632]
- observer V2 roster: recorded synthetic range [0.9794, 0.9906]
- substate search rounds: recorded synthetic range [0.9926, 1.1128]
- substate family: recorded synthetic range [0.9926, 1.1128]

Corrected: the guard fails a candidate whose ratio collapses toward zero, and no recorded candidate did (lowest 0.9794). But the real ratio is 0.7435, not 1.0118: within-class dependence is about 74% of pooled, so part of the real pooled dependence is class separation. Every recorded synthetic range lies above the corrected real ratio. The inferences built on a ratio of about 1, that real dependence carries essentially no class separation and that a successor's states cannot simply be the broad cell classes, rested on the old input.

## Pending a synthetic replay

- `V77_REALIZATION_ISOLATION_RECEIPT_V1.json`: scores synthetic counts on the cache-derived evaluation universe
- `V77_REALIZATION_ISOLATION_RECEIPT_V2.json`: scores synthetic counts on the cache-derived evaluation universe
- `V77_DYNAMIC_RANGE_TOURNAMENT_V1.json`: scores synthetic counts on the cache-derived evaluation universe
- `V77_DYNAMIC_RANGE_TOURNAMENT_V2.json`: scores synthetic counts on the cache-derived evaluation universe
- `V77_DYNAMIC_RANGE_TOURNAMENT_V2__WITHIN_HVS_EXPLORATORY.json`: exploratory; same universe dependence
- `V77_DYNAMIC_RANGE_TOURNAMENT_V2__WITHIN_SEA_AD_EXPLORATORY.json`: exploratory; same universe dependence
- `V77_OBSERVER_V2_AUDIT_CORRECTION_V1.json`: its canonical-universe numbers come from the realization isolation
- `V77_DYNAMIC_RANGE_VERDICT_V1.json`: the verdict on the dynamic-range tournament; it also quotes the old detection points

## Not replayed (not material)

- `V77_S157_PAIRED_CHALLENGE_SCORE_ARM1_V1.json / _ARMS_V1.json / _PREREGISTRATION_V1.json`: the universe is only the address set of synthetic twin worlds; the identifiability conclusions do not depend on which genes it holds (as recorded when S174 was registered)
- `V77_CONTEXT_SHORTCUT_AUDIT_V1.json`: DIAGNOSTIC_ONLY; study recoverability from support and depth does not depend on gene identity
- `REHEARSAL_* and V77_RUNTIME_HANDOFF_*`: plumbing and runtime lane (kept separate from this repair by the owner); the universe is an index set there; flagged, not replayed

## Classified before this re-score

- `V77_REPRODUCTION_ABUNDANCE_ENVELOPE_V1.json`: superseded by the replay itself (addendum 6)
- `V77_REPRODUCTION_REAL_TOPOLOGY_AFTER_T5_EXTRACTION_V1.json`: superseded by the replay itself (addendum 6)
- `V77_SUPERSEDED_REBUILD_CUSTODY_V1.json`: not material (addendum 6)
- `V77_WITHIN_COHORT_AUTHORITY_CORRECTION_V1.json`: not material (addendum 6)
- `V77_S157_LINEAGE_CROSSWALK_V1.json`: not material; its S149 row is superseded by the S149 update (addendum 6)
- `V77_S157_TERMINAL_RECEIPT_V1.json`: not material (addendum 6)
- `V77_REAL_WITHIN_COHORT_ENVELOPE_V1.json`: superseded by V2 before S174 (S159); V2 is replayed
