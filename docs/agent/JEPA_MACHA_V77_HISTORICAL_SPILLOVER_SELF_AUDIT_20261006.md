# JEPA Macha/V77 — historical spillover self-audit

Date: 2026-10-06
Branch: `handoff/jepa-20261006-macha-audit-successor`
Parent observed before write: `796396169d07c9b1fc67fdc24325b1631d17dcb4`
Status: `DOCUMENTATION_ONLY__TRAINING_OFF`

## Purpose

Iterative self-audit after the independent S149 reconstruction. Question: can any current V77 executable still make the old pooled real topology look like current biological decision authority?

## What is clean

Two active search executors now fail closed unless the operator explicitly acknowledges S149:

- `scripts/v77/run_v77_background_search.py`
- `scripts/v77/run_v77_substate_search.py`

Both mark pooled-envelope outputs as composition-confounded and not for decisions.

This is a real improvement over the historical state.

## Finding M-SPILLOVER-1 — P1

`run_v77_dynamic_range_tournament.py` does not have the S149 acknowledgement/refusal guard.

It still:

- describes comparison to unchanged `real-data envelopes`;
- runs `v77_matched_scoring.score_matched()`;
- stores output under `matched_to_real_envelopes`;
- carries rejection rules phrased as if the real envelope is a valid target;
- can be executed without any explicit acknowledgement that the pooled target is S149-confounded.

The committed `V77_DYNAMIC_RANGE_TOURNAMENT_V2.json` receipt likewise contains no S149 status field and records `matched_to_real_envelopes` under the old pooled comparison semantics.

Biological meaning: this route can still encourage a reader to tune synthetic biology toward a pattern that is partly created by study/measurement composition rather than biology.

### Current classification

`HISTORICAL_SPILLOVER_PATH_REMAINS_OPEN__INTERPRETATION_AUTHORITY_RISK`

This does **not** invalidate the directional mechanical observation that changing latent dynamic range changes synthetic topology under Poisson observation. It invalidates using closeness to the old pooled real envelope as biological calibration evidence.

## Finding M-SPILLOVER-2 — P2

`run_v77_substate_search.py` now requires S149 acknowledgement, but its receipt still embeds the historical headline:

- real transitivity `0.8871`
- old pooled envelope `[0.8752, 0.8928]`
- factor-family range `[0.515, 0.775]`

and console output still labels pooled points as `real`.

The guard makes this non-decision authority, but the presentation is still semantically stale and easy to quote out of context.

Classification:

`GUARDED_BUT_STALE_PRESENTATION`

## Self-audit against overcalling

I checked whether this was merely a harmless scoring helper. It is not fully harmless because the dynamic-range tournament itself contains rejection language and a committed receipt that presents synthetic-vs-real matched scores without an S149 warning. Therefore the P1 classification is retained.

I also checked whether the underlying synthetic dynamic-range mechanism must be discarded. It does not: within-synthetic comparisons remain mechanically informative if separated from biological target matching.

## Required repair before further use

For every executor that consumes pooled V77 real envelopes:

1. default refusal unless an explicit S149 historical-reference acknowledgement is supplied;
2. receipt field marking pooled references `COMPOSITION_CONFOUNDED__NON_DECISION_AUTHORITY`;
3. no `ACCEPT`, `REJECT`, `matched_to_real`, or equivalent biological-target wording unless the comparison is to an externally approved S149-safe target;
4. preserve old receipts as historical, not delete them;
5. do not rerun synthetic tuning against the replacement within-cohort envelope until its donor estimand and S159 interval defects are repaired.

## Boundaries unchanged

`TRAINING=OFF`

`STAGE4=NOT_AUTHORIZED`

`TEST=SEALED`

`MORABITO=PROTECTED`

`TARGET_WINNER=NONE_QUALIFIED`

`REPRESENTATION_WINNER=NONE_QUALIFIED`

`SELECTED_ESTIMAND=UNSET_REQUIRES_APPROVAL`
