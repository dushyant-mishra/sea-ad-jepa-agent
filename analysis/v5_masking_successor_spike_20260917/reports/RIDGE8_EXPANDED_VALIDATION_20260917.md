# JEPA RIDGE8 expanded discovery validation — 2026-09-17

**Status: EXPLORATORY SUCCESSOR EVIDENCE ONLY. NO MASKING AUTHORITY. TRAINING OFF.**

This package extends the prior RIDGE8 handoff with independent local validation performed from the frozen 50,000-cell discovery substrate. Protected/D_shared/pathology outcomes were not opened.

## Unified 32-target ridge-scored comparison at 6,000 addresses

All arms use the same outer donor folds, common random base masks, matched 15% burden, and the same freshly fit ridge attacker.

- RIDGE8: mean drop 0.007979; relative drop 6.42%; positive target mean on 30/32 targets.
- TOP8: mean drop 0.004734; relative drop 3.81%; positive target mean on 29/32 targets.
- PREFIX3: mean drop 0.000184 overall; acts on 10/32 targets.

This resolves the earlier invalid cross-attacker comparison: under one scorer and one n, RIDGE8 remains stronger overall than TOP8 and PREFIX3.

## Outside-original-800 target challenge

A separate deterministic challenge set was selected from the other 5,200 addresses, using only support/variance eligibility and hash ordering before RIDGE8 outcomes were inspected.

At 32 targets x 4 folds, 6,000-address universe:

- RIDGE8: mean drop 0.010597; relative drop 10.55%; target win 31/32; target-clustered 95% CI [0.006861, 0.014994].
- TOP8: mean drop 0.006433; relative drop 6.40%; target win 29/32; target-clustered 95% CI [0.003450, 0.010235].
- RIDGE8 minus TOP8: mean paired advantage 0.004164; target-clustered 95% CI [0.001527, 0.007009].
- PREFIX3: mean drop 0.002215 overall; acts on 6/32 targets; acted-row mean drop 0.016676.

This materially reduces the concern that the RIDGE8 signal is confined to targets selected from the original nested 800-address subset.

## STABLE10 / STABLE15 diagnosis

- STABLE15 is vacuous at the tested threshold: zero action rows.
- STABLE10 is not primarily a mask-construction bug. In nearly every action row, the selected address is genuinely swapped into the mask; the simple correlation attacker nevertheless keeps choosing the same strongest remaining predictor, producing zero score change.
- Therefore STABLE10 is best interpreted as ineffective for this threat model, not evidence that burden-preserving masking is broken.

## Nonlinear attacker check

HistGradientBoosting was used as a deliberately different held-donor attacker class.

Original 8 targets:
- RIDGE8 relative reduction 4.29%; positive target mean 8/8; CI [0.002324, 0.007219].
- TOP8 relative reduction 2.51%; positive target mean 7/8.
- RIDGE8 minus TOP8 paired advantage 0.001906; CI [0.000663, 0.003215].

Outside-original-800 8 targets:
- RIDGE8 relative reduction 3.93%; positive target mean 8/8; CI [0.003965, 0.008873].
- TOP8 relative reduction 2.14%; positive target mean 6/8.
- RIDGE8 minus TOP8 mean advantage 0.002895; CI [-0.000483, 0.006227].

The nonlinear direction is supportive, but the outside-800 RIDGE8-vs-TOP8 superiority claim is not closed at n=8 because its paired CI crosses zero.

## Current interpretation

RIDGE8 is the strongest **broad exploratory candidate** tested here. PREFIX3 remains scientifically interesting as a sparse/selective strategy because its acted effects can be large even when its overall mean is diluted by low trigger rate. Do not describe PREFIX3 as disproven.

Nothing here freezes cap 8, 15% mask burden, RIDGE8, PREFIX3, or any production threshold.

## Next prospective step

Before any FULL104 successor outcome is inspected, freeze a successor masking qualification contract that includes:

1. common random masks and burden-preserving swaps;
2. bounded paired scoring;
3. target-clustered uncertainty;
4. RIDGE8, TOP8 and selective PREFIX3 comparators;
5. positive and shuffled-negative controls;
6. address-universe ladder;
7. evidence-budget authority kept separate from masking-policy authority;
8. a nonlinear/objective-aligned attacker-class robustness check;
9. explicit no-training and protected-outcome seals.

The broader project-design additions remain prospective: observation-process conditioning, evidence-response curves, separate biological-vs-measurement uncertainty, basis/subspace stability, and pathology-blind confirmation.
