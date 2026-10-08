# H3 target-vs-donor precision decomposition

Date: 2026-09-20
Status: **PROSPECTIVE DESIGN / OUTCOME-BLIND**
Scope class: `CURRENT_FULL104_RECONNAISSANCE`

This design is derived from the authenticated FULL104 donor/source/fold geometry.
It does not select a G5 margin and does not inspect terminal evidence.

## Current geometry

Donors:
- HVS 41
- NPH52 17
- SEA_AD 46

Held-out donors by fold:
- fold 0: HVS 11, NPH52 5, SEA_AD 12
- fold 1: HVS 10, NPH52 4, SEA_AD 12
- fold 2: HVS 10, NPH52 4, SEA_AD 11
- fold 3: HVS 10, NPH52 4, SEA_AD 11

Under the current equal-source score, a single held-out NPH52 donor contributes
1/(3*5)=6.67% of the total score in fold 0 and 1/(3*4)=8.33% in folds 1-3.

This does not imply source balancing is wrong. It means finite-donor precision,
especially for NPH52, may set a floor that increasing target count cannot remove.

## Three bootstrap contrasts

At each prospectively frozen target-count rung, use the same source-balanced
estimand and compare:

1. `TARGET_ONLY`
   - resample target indices;
   - donors fixed.

2. `DONOR_ONLY_WITHIN_SOURCE`
   - targets fixed;
   - resample donors independently within HVS/NPH52/SEA_AD preserving source
     counts.

3. `PAIRED_TARGET_AND_DONOR_WITHIN_SOURCE`
   - current combined structure;
   - resample targets plus donors within source.

Use the same replicate count and prospectively derived seed namespace.

Report bootstrap mean, SD, interval width, and source-specific donor-only widths.
Do not claim additive variance decomposition; these are diagnostic contrasts.

## Interpretation

If TARGET_ONLY width shrinks with more targets while DONOR_ONLY stays nearly
constant and PAIRED approaches DONOR_ONLY, H3 is donor-limited. More target
addresses cannot create additional independent NPH52 donors.

If TARGET_ONLY remains dominant, a larger target panel may materially improve
precision.

## Hard prerequisite

Do not run this on an evidence matrix where target non-estimability has already
been converted to literal scientific zero.

Audit C2 and the terminal evidence schema must preserve the distinction between:

- target correlation undefined because `rss_y <= EPS`; and
- an estimable target with correlation equal to zero.

No per-source `train>=20 / heldout>=5` threshold is introduced here; those global
eligibility constants cannot be transplanted into NPH52 folds after the fact.

```
G5_MARGIN_SELECTED = NO
TERMINAL_MASKING_OUTCOMES = UNOPENED
TRAINING_OFF
```
