# Audit C — target source-specific estimability

Date: 2026-09-20
Status: **`NEW_FINDING` / `OPEN`. The 17,053-target eligibility set is NOT
altered.**

Produced by `scripts/audit_c_target_source_estimability_20260920.py` from the
shared core sufficient statistics over all 8,915 blocks and all 4,553,407 cells.
Evidence: `evidence/audit_c/`.

---

## 1. The mismatch being tested

Eligibility is **global and donor-based**: ≥30 nonzero cells per donor, ≥20
supported training donors, ≥5 supported validation donors. That yields 17,053
all-fold eligible targets.

But the masking estimand is **source-balanced**: the primary score averages
within source and then across sources, so HVS, NPH52 and SEA_AD each contribute
**one third of the verdict** regardless of how many donors or cells they hold for
that target.

Global eligibility does not imply per-source estimability. This audit measures
the gap.

## 2. C1 — per-source support

| source | donors | cells | mean supported donors per target | targets with **zero** supported donors | targets with <5 | mean detection rate |
|---|---|---|---|---|---|---|
| HVS | 41 | 198,718 | 36.96 | 274 | 810 | 0.2378 |
| NPH52 | **17** | 236,476 | **14.84** | 258 | 608 | 0.2079 |
| SEA_AD | 46 | 4,118,213 | 40.15 | **923** | 1,189 | 0.1626 |

NPH52 has only 17 donors in total, so its guardrail — one third of the verdict —
rests on at most 17 units and on average fewer than 15.

## 3. All-donor descriptive support benchmark

| | targets | share |
|---|---|---|
| **estimable in all three sources** | **14,526** | **85.18%** |
| one weak source | 2,447 | 14.35% |
| two weak sources | 80 | 0.47% |
| three weak sources | 0 | 0% |

**2,527 of 17,053 targets (14.8%) have fewer than five globally supported donors
in at least one source under this all-donor descriptive benchmark.** This is not a
new per-source eligibility rule and is not yet fold-specific estimability.

Weakness by source — the criterion is fewer than 5 supported donors:

| source | targets weak here | of which **zero** supported donors |
|---|---|---|
| HVS | 810 | 274 |
| NPH52 | 608 | 258 |
| SEA_AD | 1,189 | 923 |

## 4. C3 — the sharp part: scorer-relevant target non-variability

This is why §3 matters rather than being a bookkeeping note.

From `_source_balanced_prediction_score`, verbatim:

```python
den = float(np.sqrt(max(rss_y, 0.0) * max(pred_ss, 0.0)))
r = 0.0 if den <= _EPS else cov / den
```

`rss_y` is the within-donor centred sum of squares of the target. **If the target
does not vary within a donor, `rss_y = 0`, so `r = 0`, and that donor contributes
`r² = 0` to its source's mean.**

Zero is the *best possible* score. A donor where the target never varies therefore
contributes a **perfect "no shortcut detected" verdict** — not a missing value,
not an abstention.

| source | donor×target pairs | **all-zero** pairs | fraction | targets with **any** all-zero donor | targets where **every** donor is all-zero |
|---|---|---|---|---|---|
| HVS | 699,173 | 887 | 0.127% | 380 | 0 |
| NPH52 | 289,901 | 6,220 | **2.146%** | **4,976** | 0 |
| SEA_AD | 784,438 | 23,344 | **2.976%** | 2,031 | **75** |

Two things stand out.

**4,976 targets (29.2%)** have at least one NPH52 donor that is all-zero for the
target and therefore contributes a free zero under the current score. NPH52 has only 17 donors, so one silent donor is ~6% of that
source's entire guardrail.

**75 targets** have *every* SEA_AD donor all-zero. For those targets, every SEA_AD
donor has undefined target correlation and the current implementation maps those
terms to zero.
It cannot fail. It reports "clean" because there is nothing there to be dirty.

## 5. Method note

The exact route proves a sufficient condition: a target detected in **no** cell of
a donor is identically zero across that donor, so its within-donor variance is
exactly zero. It does **not** exhaust all mathematically constant targets; a
constant-positive target would also have zero variance. The scorer-epsilon route
is therefore retained as the scorer-relevant comparison.

The scorer-epsilon route (`rss ≤ 1e-12`, using the scorer's own constant) is
reported beside it, not instead of it, because `sumsq/n − mean²` suffers
catastrophic cancellation precisely at near-zero variance — exactly where this
audit looks. On the real data the two routes agree exactly in every source, which
is reassuring but was not assumed.

## 5b. C2 fold-aware estimability is now required before promotion

The reviewed V1 script accepted `--fold-by-donor` but did not use it. That is now
treated as an instrument defect, not as missing prose.

The successor instrument is bound to the authenticated FULL104 split receipt by
SHA, donor order and source codes. It reports, for every source × outer fold:

- available training and held-out donors;
- supported training/held-out donors per target;
- scorer-variable training/held-out donors (`rss_y > EPS`);
- the number of donor score terms the current scorer would include;
- how many targets therefore contain one or more undefined-target terms mapped to zero.

No new threshold is chosen from those counts.

The already-committed all-donor numbers above remain
`CURRENT_FULL104_RECONNAISSANCE`, but they **must not be promoted to the
fold-specific terminal estimability result** until the updated instrument is run
against the content-addressed FULL104 sufficient-statistics artifact.

## 6. Classification

```
GLOBAL_ELIGIBILITY_AND_SOURCE_BALANCED_GUARDRAILS_MEASURE_DIFFERENT_POPULATIONS
```

An `OPEN` design issue. A source guardrail can pass because the target was
unvarying there, which is the opposite of evidence that masking worked. That is
the clearest identified path by which a terminal verdict could come out right for
the wrong reason.

## 7. What is NOT done

**The target set is not shrunk.** Removing targets after seeing which ones are
weak is precisely the move that must not be made casually — it would select the
evaluation population using the evaluation itself.

```
PROPOSED_REPAIR_REQUIRED
```

Options, none selected:

1. **Require per-source estimability** in the eligibility rule, prospectively,
   and accept the smaller target universe that follows.
2. **Let a source abstain** rather than contribute `r² = 0` when its target is
   unvarying, and re-weight the remaining sources — which changes the estimand.
3. **Keep the rule and report** the per-source estimable count alongside every
   verdict, making the conditionality explicit rather than removing it.

Option 2 is the most faithful to the intent but changes what the score means.
Option 1 shrinks the universe. Option 3 changes nothing but stops the verdict
being read as stronger than it is. The choice must not be made by observing which
option produces a preferred outcome.

## 8. Verification

Positive control: targets made undetected in a known donor set are counted
exactly — nine constructed pairs recovered as nine. Negative control: when every
target varies, zero flags are raised. Weak-source accounting is pinned to
partition every target exactly once, and the eligibility set is asserted
unaltered. 9 tests, 0 skipped.

```
ELIGIBILITY_SET_ALTERED = false
TERMINAL_MASKING_OUTCOMES = UNOPENED
TRAINING_OFF
```
