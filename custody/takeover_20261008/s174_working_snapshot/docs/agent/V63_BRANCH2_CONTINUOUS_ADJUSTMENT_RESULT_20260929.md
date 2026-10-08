# Branch 2 — the continuous-adjustment estimator: classification **A**

Contract `results/v63/V63_CONTINUOUS_ADJUSTMENT_ESTIMATOR_CONTRACT_V1.json`,
committed at `4f774e0b` **before** the estimator was written or run.
donors=18, seeds=24. Arms, worlds, seeds, `M_MIN` and the LCB construction are
inherited from tournament v2.1 unmodified; **only the estimator changed**.
`TRAINING=OFF`, `TD60=BLOCKED`, synthetic only.

---

## Every represented family clears

| family | margin | LCB95 | |
|---|---|---|---|
| NULL | +0.03228 | +0.03206 | PASS |
| **TECH** | **+0.01996** | **+0.01948** | **PASS** |
| GEO | +0.02556 | +0.02517 | PASS |
| ACC | +0.03166 | +0.03031 | PASS |
| ANCHOR | +0.03700 | +0.03578 | PASS |
| DONOR | +0.03202 | +0.03161 | PASS |
| held-out ambient | +0.03233 | +0.03174 | generalises |

TECH clears `M_MIN` by roughly a factor of two, having failed at **every**
granularity on the frontier where the population stayed representative.

## Support is genuinely broad, not concentrated

| | |
|---|---|
| linked pairs scored | **960 / 960 = 100%**, no trimming |
| Kish effective sample size | **935 (97.4%)** |
| contribution share, top 1 / 5 / 10% | 0.013 / 0.066 / **0.128** |
| residual corr. on LINKED pairs | log-dist +0.0024, degree +0.0014, accessibility −0.0066, anchor −0.0062 |
| linked-vs-control SMD **before** adjustment | **1.964** |

The residual correlations are measured on **linked** pairs, which are
out-of-sample for the nuisance model. |r| ≤ 0.0066 against a pre-adjustment
imbalance of ~2 SMD is the substantive check, not a tautology.

This beats the frontier baseline **on both axes at once**: representative
population *and* TECH rejected.

## The ablation is what makes this believable

Out-of-fold R² for the nuisance model is **−0.0049** — essentially zero, which
initially looked like the adjustment was inert. It is not. Replacing the fitted
surface with the training-fold mean and changing nothing else:

| | frozen estimator | adjustment disabled |
|---|---|---|
| NEG_TECH_2 median | +0.01185 | **+0.16990** |
| TECH | +0.01996 PASS | **−0.13856 FAIL** |
| GEO | +0.02556 PASS | **−0.10086 FAIL** |
| ANCHOR | +0.03700 PASS | **−0.03579 FAIL** |
| classification | A | **D_ANOTHER_FAMILY_BROKE__STOP** |

Support is *identical* across the two (ESS 935 vs 936), so only the adjustment
differs — a clean controlled comparison.

**R² was the wrong diagnostic.** Per-pair correspondence over 40 metacells is
noise-dominated (SE ≈ 0.16) while the systematic geometry component is ≈ 0.02, so
R² ≈ 1.5% at best and reads as zero out-of-fold. Averaged over 960 pairs that
component is exactly what matters — removing it moves NEG_TECH_2 by a factor of
fourteen. The ablation is retained as a permanent diagnostic so the next reader
does not misread R² the way I nearly did.

## Why the adjustment does not eat the biology

POS_BIO_1 **+0.22825** and POS_BIO_2 **+0.03140**, against v2.1's +0.22976 and
+0.03223 — essentially unchanged. The nuisance model is fitted on **unlinked
pairs only** and cross-fitted **by promoter**, so it never sees the linked pairs
where the planted signal lives and cannot learn to predict it away. Contract
points 4 and 5 are doing precisely the work they were specified for.

## The caveat that must travel with reading A

**The nuisance model's functional form is well matched to the simulated nuisance
mechanism.** `NEG_TECH_2`'s latent is scaled by `(degree/10) × (1e5/distance)` —
a product of degree and inverse distance — and the frozen feature set contains
log-distance, degree and their interaction. In log space the model can represent
that surface closely. This is therefore close to a **well-specified** adjustment,
and real data will not be.

Two things partially offset it, neither decisive:

- the **held-out ambient family**, not used in design, still generalises at
  +0.03174;
- the surface is **extrapolated** from controls into the linked region across a
  ~2 SMD gap rather than interpolated, which is the harder direction.

So reading A's scope is: *the problem was coarse support adjustment* **for a
nuisance whose geometry dependence lies within the frozen model's span**. Whether
that holds for a real capture-quality latent is **not** established here and must
not be assumed.

## Classification against the predeclared readings

- **A — TECH clears + broad coverage + others green.** Top-10% share 0.128 < 0.50
  and ESS 97.4% > 30%, so the broad-coverage test passes on its own predeclared
  rule.
- **Not B** — the result is not carried by a small subset.
- **Not C** — TECH did not still fail.
- **Not D** — no other family broke; the ablation shows what D looks like.

> **Strong evidence that the failure was COARSE SUPPORT ADJUSTMENT, not intrinsic
> non-identifiability — within the span of the frozen adjustment model.**

## What this does and does not change

The **frontier result stands unchanged and unretracted**: it correctly ruled out
solving this by moving matching granularity, and that remains true. The
continuous estimator does not contradict it — it sidesteps the trade by not
trimming at all.

`NEG_TECH_2` is no longer `EMPIRICALLY_UNRESOLVED` **under this estimator class**.

The **semantic twin is untouched**: identical to POS_BIO_1 to zero tolerance,
`NON_IDENTIFIABLE_BY_DESIGN`. Nothing here moves that boundary, and nothing here
licenses treating it as moveable.

## Self-audit

**S-V63-6 — I nearly rejected a working estimator on a misleading statistic.** I
saw R² ≈ 0 and prepared to report that the adjustment was inert and that the
apparent fix came from changing the control set. That would have been wrong, and
the only reason it did not become the reported conclusion is that I ran the
ablation before writing it up. The lesson is narrow and worth keeping: for a
noise-dominated per-pair statistic, out-of-fold R² is not a measure of whether an
adjustment is doing useful work; the ablation is.

**What remains open.** The specification-match caveat above is the main one. A
harder test would be a geometry-keyed nuisance whose functional form is
deliberately *outside* the frozen feature span — but constructing one now, after
seeing reading A, would be a post-hoc negative and would need the same
prospective freeze the rest of this work has had.
