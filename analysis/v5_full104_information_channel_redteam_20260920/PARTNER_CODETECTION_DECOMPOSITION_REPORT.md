# Audit E — co-detection versus quantitative co-expression

Date: 2026-09-20
Status: **`PARTIALLY_AUDITED` / `OPEN`. No categorical threshold frozen. No
biological claim.**

Produced by `scripts/audit_e_codetection_decomposition_20260920.py` from the
shared core sufficient statistics, over all 4,553,407 cells.
Evidence: `evidence/audit_e/`.

---

## 1. The question

At 83.3% measured zeros, correlation screening on normalized expression may be
selecting partners that are merely **detected together** rather than partners
whose **levels covary when both are detected**. Those are different biological
claims, and masking one removes different evidence than masking the other.

## 2. Decomposition

Per (target, partner) pair:

- **E1** — binary detection association: the phi coefficient of `I(x>0)` with `I(y>0)`
- **E2** — quantitative association among cells where **both** are detected
- **E3** — the current production screening score shape: source-balanced mean of
  `|within-donor r|` on normalized expression

512 pairs (64 targets × 8 partners), all 4,553,407 cells. Every pair had ≥30
both-detected cells, so `e2_non_estimable_pairs = 0` — no pair needed the
`NON_ESTIMABLE_CONDITIONAL_ON_DETECTION` label.

| | mean | p05 | median | p95 | min | max |
|---|---|---|---|---|---|---|
| **E1** detection association | 0.1424 | −0.0953 | 0.1149 | 0.4880 | −0.4589 | 0.7628 |
| **E2** conditional quantitative | **0.2600** | −0.2798 | **0.2621** | 0.6757 | −0.4251 | 0.8569 |
| **E3** production screening score | 0.0760 | 0.0238 | 0.0678 | 0.1593 | 0.0141 | 0.2085 |

## 3. The result

```
correlation of E3 with E1 (co-detection)            = +0.1774
correlation of E3 with E2 (quantitative covariation) = −0.0721
```

The production screening score tracks **neither** component strongly. It leans
weakly toward co-detection, and if anything leans *away* from quantitative
covariation among cells where both genes are on.

Two readings follow, and both matter:

**The screening score is not "quantitative co-expression".** Its correlation with
conditional quantitative association is slightly negative. Whatever TOP8 and
RIDGE8 are selecting, it is not primarily "genes whose levels move together".

**But it is not simply co-detection either.** At +0.18, co-detection explains
little of it. The score is dominated by something neither component captures —
most plausibly the overall variance and scale structure of the normalized values,
which both components deliberately factor out.

There is also a genuinely reassuring sub-result: **E2 (mean 0.26) exceeds E1
(mean 0.14)**. Among cells where both genes are detected, real quantitative
covariation is present and is *stronger* than the detection-level association. So
the underlying biology is not merely co-detection — even though the screening
score is not selecting on it.

## 4. No threshold is frozen

```
classification = UNFROZEN__CONTINUOUS_ONLY
categories_frozen = false
```

Partners are **not** labelled "predominantly co-detection" or "predominantly
quantitative". Choosing a cut after seeing these values is how an arbitrary
constant gets laundered into a finding. The continuous decomposition is reported;
the categories stay open until a threshold has a justification of its own.

The single structural exception is `NON_ESTIMABLE_CONDITIONAL_ON_DETECTION`,
applied when too few both-detected cells exist for E2 to be defined at all. That
is a statement about missing evidence, not a threshold on an effect size — and on
the real data it applied to no pair.

## 5. Scope, stated plainly

The real planner scores each target against all 17,186 addresses, at one
streaming pass over the training donors **per target per fold**. That is not
feasible to enumerate.

So this audit uses a **deterministic 512-address pool**, selected by a hash rule
declared before any result was seen, and picks partners **within that pool** using
the same screening shape. The cross-products were accumulated in the same
traversal that feeds Audits B and C, so all three read one pass over the
substrate rather than three.

This is a reduced-scale mirror of the mechanism. **It is not a claim about which
partners production would select**, and the pool rule cannot have been chosen to
favour an outcome because it depends on nothing about the data.

## 6. Why it stays `PARTIALLY_AUDITED`

A real number exists, but it does not answer the whole question. The pool is 512
of 17,186 addresses, and partner choice within a small pool is not the same
problem as partner choice across the full universe — the best available partner
in a pool of 512 may be a poor one in absolute terms, which could itself depress
the observed relationships.

What the audit does establish is narrower and still useful: **on the real
substrate, the production screening shape does not preferentially select
quantitatively co-varying partners.** Whether that holds at full scale needs the
full-universe computation.

## 7. Relation to Audit F

Audit F decomposes the *target representation* along the same seam — identity and
context versus detection versus quantitative state. E and F are the same question
at two points in the pipeline, and a consistent answer across both would be
considerably stronger evidence than either alone. F cannot run until a lawful
teacher exists.

```
CATEGORIES_FROZEN = false
BIOLOGICAL_CLAIM = NONE
TERMINAL_MASKING_OUTCOMES = UNOPENED
TRAINING_OFF
```
