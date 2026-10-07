# JEPA Macha/V77 — within-cohort V2 scope audit

Date: 2026-10-06
Parent audit head before write: `172c705f2069e30ad0710047080cdd2b7c80e38d`
Macha head audited: `eb98ede1419adb48fec6b82bfdcbdaffa4ae54c1`
Status: `DOCUMENTATION_ONLY__TRAINING_OFF__NO_CALIBRATION_AUTHORITY`

## Finding

`V77_REAL_WITHIN_COHORT_ENVELOPE_V2.json` is a numerical S159 repair candidate, not a new biological/statistical estimand.

The V2 producer change at `df7f82a2...`:

- keeps the same within-cohort point estimates;
- keeps the same donor-resampling scheme;
- keeps 24 bootstrap replicates;
- keeps the point statistic cell-weighted inside each sampled donor set;
- keeps the same HVS / NPH52 / SEA_AD stratum assignment;
- keeps the same 200-cell class floor, so NPH52 remains ineligible;
- adds class-size metadata;
- recentres bootstrap spread around the observed point;
- requires synthetic comparisons at the same stratum-specific cell count.

The later authority correction at `f0f03d1c...` correctly withdraws V2's original `acceptance rule` language and states that neither V1 nor V2 is authorized for synthetic pass/fail decisions.

## Biological interpretation

V2 fixes a bad ruler, not the population question.

The old percentile ruler could exclude the real sample from its own interval because resampling donors with replacement reduces the number of distinct cells and inflates correlation magnitudes. V2 recentres that spread around the observed value.

That does **not** answer:

- whether donors should have equal biological weight;
- how HVS, NPH52 and SEA_AD should be combined;
- what source/study population the project intends to generalize to;
- whether class-associated structure is biological or technical;
- what calibration target should authorize a synthetic model.

## Remaining weighting defect

Although donors are the bootstrap clusters, the statistic within each bootstrap replicate is still calculated after concatenating all cells from selected donors. Donors with more cells therefore contribute more to the correlation/topology statistic.

Thus:

`DONOR_CLUSTERED_UNCERTAINTY != EQUAL_DONOR_ESTIMAND`

No equal-donor estimator has been introduced by V2.

## S159 status

S159 remains open methodologically.

The candidate re-centred range is reasonable diagnostic evidence that the inherited percentile interval had a location-bias problem. It is not yet a validated acceptance interval. With only 24 bootstrap replicates, tail-boundary precision is also weak for a future sealed gate.

## NPH52

NPH52 still has only 246 cells total and fails the inherited requirement that at least two broad classes each contain >=200 cells. V2 does not solve this; it simply preserves NPH52 as ineligible under that statistic.

## Correct current classification

`WITHIN_COHORT_V2 = CANDIDATE_NUMERICAL_INTERVAL_REPAIR__NOT_SELECTED_ESTIMAND__NOT_CALIBRATION_AUTHORITY`

## Authority unchanged

TRAINING=OFF; Stage A OFF; Stage 4 NOT AUTHORIZED; TEST sealed; Morabito protected; no target, representation, calibration target, evidence-object or estimand winner.
