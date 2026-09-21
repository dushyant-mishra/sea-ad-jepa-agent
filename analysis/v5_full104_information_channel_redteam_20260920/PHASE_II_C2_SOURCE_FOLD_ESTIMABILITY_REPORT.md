# Phase II — C2: authenticated source × fold estimability

Date: 2026-09-21
Scope class: **`CURRENT_FULL104_RECONNAISSANCE`**
Determination: **measured. The design issue is OPEN. The 17,053-target
eligibility set is NOT altered.**

```
BASE_SHA        : ae5dc5c624fff341b8ef30c5359c55528383920a
split receipt   : 5d616c9c509d8224d15d6e8c163ca38b4b5140a44fdab4c2fa00efad7a8f01e4
heavy artifact  : f77dff47df71e2b97895f6e850db4d2a2ebdab441d195dedf91f582b4d53b5ae
                  (qualified for reuse in Phase I)
```

---

## 1. Scientific question

> Where, and how often, does the current scorer treat an **undefined** target
> correlation as an **estimable correlation whose measured value is zero**?

## 2. What would falsify the intended interpretation

If undefined terms were vanishingly rare, or confined to targets that no fold
actually scores, the concern would be theoretical. If the row-level variance
recomputation disagreed with the sufficient-statistics classification, the
measurement itself would be void.

## 3. Authenticated inputs — geometry verified, not assumed

The split receipt's fold geometry was checked against the handoff expectation
**cell by cell** before anything was computed:

| fold | HVS train/held | NPH52 train/held | SEA_AD train/held |
|---|---|---|---|
| 0 | 30 / 11 | 12 / 5 | 34 / 12 |
| 1 | 31 / 10 | 13 / 4 | 34 / 12 |
| 2 | 31 / 10 | 13 / 4 | 35 / 11 |
| 3 | 31 / 10 | 13 / 4 | 35 / 11 |

All 12 fold × source cells match exactly; held-out totals [28, 26, 25, 25] equal
the receipt's own `fold_sizes`. No provenance investigation was required.

**No per-source `train>=20 / heldout>=5` criterion was introduced.** NPH52 has
only 17 donors and at most 5 held out per fold, so such a rule would be
unsatisfiable by construction.

## 4. Result — the mechanism, quantified

From the frozen scorer, verbatim:

```python
den = float(np.sqrt(max(rss_y, 0.0) * max(pred_ss, 0.0)))
r = 0.0 if den <= _EPS else cov / den
```

When a target does not vary within a held-out donor, `rss_y = 0`, so `r = 0` and
that donor contributes `r² = 0` — **the best attainable value** — to its source's
mean. Not a missing value, not an abstention: a free perfect score.

### Targets whose current score includes at least one undefined term

| fold | HVS | NPH52 | SEA_AD |
|---|---|---|---|
| 0 | 214 | **4,897** | 1,681 |
| 1 | 114 | 623 | 1,438 |
| 2 | 203 | 64 | 912 |
| 3 | 84 | 370 | 1,477 |

Fold 0 / NPH52 is the extreme: **4,897 targets (28.7%)**, in a source with only
**5 held-out donors**, so one silent donor is **20% of that source's entire
guardrail for that fold**.

### Union across all folds and sources

| quantity | value | share |
|---|---|---|
| targets with ≥1 undefined held-out term somewhere | **6,653** / 17,053 | **39.01%** |
| targets where some source's held-out guardrail is **wholly vacuous** | **202** / 17,053 | **1.18%** |
| undefined held-out score terms | **30,451** / 1,773,512 | **1.7170%** |

Wholly-vacuous cases by source: **SEA_AD 200**, HVS 1, NPH52 1.

For those 202 targets, an entire source contributes `0` with **no variable
held-out donor at all**. That third of the verdict is structurally incapable of
detecting anything, and reports the cleanest possible result.

## 5. Controls

All in `tests/test_v5_audit_bc_burden_estimability_v1.py`.

**Positive** — constructed zero-variance target/donor combinations are counted
exactly (nine constructed pairs recovered as nine).

**Negative** — when every target varies in every donor, zero flags are raised.

**Adversarial, added in this phase** —
`test_c2_adversarial_constant_positive_target_is_flagged_not_just_all_zero`.
A target detected in **every** cell of a donor at an identical normalized value
also has zero variance, so `r` is undefined there just as surely as for an
all-zero target — but its detection count is *maximal*, so a detector keyed on
`nnz == 0` would call it perfectly well-behaved.

The control constructs exactly that case and requires it to be flagged. It also
requires the **exact `nnz == 0` route to NOT flag it**, which is what proves the
two routes measure genuinely different things rather than one being a restatement
of the other. Without this control, the entire 39.01% figure could have been an
artifact of only ever looking for absent targets.

Also pinned: C2 refuses a split receipt not bound by the eligibility authority,
and the eligibility set is asserted unaltered.

## 6. Independent cross-check — row level, different numerical route

`scripts/verify_c2_variance_from_rows_20260920.py`,
evidence `evidence/audit_c/C2_ROW_LEVEL_VARIANCE_VERIFICATION.json`.

The sufficient-statistics classification uses the one-pass form
`rss = n·(nsq/n − mean²)`, which cancels catastrophically exactly at near-zero
variance — precisely where this audit looks. So the check recomputes variance
**two-pass** (mean first, then summed squared deviations) directly from the
authenticated Level-4 rows. A different numerical route, not the same arithmetic
repeated.

| | |
|---|---|
| pairs checked | **384** (32 targets × 12 donors) |
| pairs in agreement | **384** |
| pairs disagreeing | **0** |
| **flagged non-variable pairs verified** | **8** |
| runtime | 66s, 8 workers |

Selection used two declared routes, reported separately: a **hash sample**
keyed on a salt joined to the target address and donor id — independent of the
data and of the classification — and a **flagged verification** covering every
sampled pair C2 called non-variable. The second is a targeted check of the
positive class and is labelled as such; its counts are not prevalence. Both are
needed: the hash sample alone would barely touch the class the audit is about,
and the flagged set alone could not detect false negatives.

```
verdict = C2_CLASSIFICATION_CONFIRMED_AT_ROW_LEVEL
```

## 7. Red-team

| question | answer |
|---|---|
| Held-out data used to choose the method? | No. The classification is a property of the target's within-donor variance; no score was computed and no policy chosen. |
| Reduced-pool or historical value promoted? | No. All 17,053 targets, all 104 donors, all 4 authenticated folds. |
| Estimand silently changed? | No. The frozen scorer is quoted, not modified. |
| Undefined turned into zero? | **That is the defect being measured**, and it is counted rather than propagated. This audit converts nothing. |
| Population weighting used where donor/source weighting intended? | No weighting is applied; these are counts over the authenticated fold geometry. |
| Cache with changed semantics reused? | No — Phase I qualified the artifact first. |
| Could the positive control pass with a wrong implementation? | No. The adversarial control specifically defeats an all-zero-only detector. |
| Does the negative control falsify? | Yes — all-varying targets must produce zero flags. |
| Threshold chosen after the result? | No. `_EPS = 1e-12` is the scorer's own constant, not a new one. |
| Sealed information used? | No. |
| Second computation reproduces the headline? | Yes — 384 pairs re-derived from rows by a two-pass route. |

## 8. What this establishes

On the authenticated FULL104 split, **1.717% of all held-out score terms are
mathematically undefined yet enter the score as a perfect zero**; 39.01% of
targets are affected at least once; and for 202 targets an entire source's
held-out guardrail is vacuous.

The global eligibility universe and the source-balanced guardrails are therefore
measuring different populations.

## 9. What this does NOT establish

- **No terminal masking outcome was computed or inspected.** This is the geometry
  of the score's *inputs*, not any score.
- It does not say how much the verdict would change — that depends on the
  representation chosen in Phase III, which is deliberately not chosen here.
- It does not imply the affected targets should be removed. Removing targets
  after seeing which are weak would select the evaluation population using the
  evaluation.
- 1.717% of terms is not 1.717% of anything scientifically meaningful until the
  evidence contract defines how undefined terms are handled.

## 10. Blockers

```
GLOBAL_ELIGIBILITY_VS_SOURCE_BALANCED_GUARDRAIL_MISMATCH = OPEN
PROPOSED_REPAIR_REQUIRED                                  = YES, none selected
ELIGIBILITY_SET_ALTERED                                   = NO
TERMINAL_MASKING_OUTCOMES                                 = UNOPENED
TRAINING_OFF
```

**Next dependent step:** Phase III — freeze the non-estimability evidence
contract, so that undefined, missing and measured-zero states remain
distinguishable through serialization and resampling. Phase III must be designed
from these counts **without** choosing whichever rule makes masking easiest to
pass.
