# Frozen protocol v6 — the sham generates the null

**Prospectively dated successor to v5 / v5.1. v1–v5.1 preserved unedited as
historical record; v6 is the sole execution authority.**

**Dated 2026-09-27. The synthetic gate has run and FAILED its NEG-2 arm. No
control gene has been extracted and no real expression has been read.** Every
change below is a response to that failure and to a false-positive-rate
argument, not to any real outcome.

## Why v5.1's sham criterion was not enough

v5.1 required the real program to beat the sham in at least two thirds of
evaluation donors. With nine evaluation donors and real and sham exchangeable
under the null, six or more favouring the real program happens with probability
130/512 ≈ **25%**. In the NEG-2 arm criteria 1 and 2 both fired, so criterion 3
was carrying the entire load — at a 25% false-positive rate. That is not
control.

## The change: the sham is the null model

A sham matched on abundance, sparsity and sensitivity to capture efficiency, and
carrying no biology, **is** the null. So it generates the null distribution
rather than serving as one comparison.

> **Primary test.** Draw `B_sham = 199` independent sham programs, each carried
> through the identical pipeline — same offset, same controls, same centering,
> same split, same statistic. The null distribution is their median-per-donor
> increments. The p-value for the real program is
> `p = (1 + #{sham ≥ real}) / (1 + B_sham)`.

This also explains why the within-stratum permutation null failed and could not
have succeeded. Permuting the state destroys the capture link along with the
biological one, so it tests *"is there any dependence"*. The question is *"is
there dependence beyond the technical factor"*, and only a null that **keeps**
the technical factor while removing the biology can ask it. The matched sham
does exactly that; a permutation does the opposite.

The within-stratum permutation is retained as a **reported diagnostic**, never
as a qualifying criterion.

## Sham construction, specified

Each sham is four genes drawn to match *P*'s partners on all three properties
that matter, not just the first:

1. **mean abundance** — matched per partner, not only in aggregate;
2. **sparsity** — matched zero fraction, because the pseudocount pathology is a
   low-count phenomenon and an abundance-matched but denser sham would not
   reproduce it;
3. **capture sensitivity** — the sham is drawn on the *same nuclei* and so
   inherits the same per-nucleus capture factor, which is what makes it carry
   the artifact.

A sham matched only on mean would be a weaker null than the artifact it must
represent.

## Decision rule

A directed pair passes if **both**:

1. the **sham-null** p-value survives Benjamini–Hochberg at q = 0.05 across the
   six directed tests; and
2. the increment is positive in at least two thirds of evaluation donors.

A **program qualifies** only if both its directed tests pass. Primary reporting
unit is the directed pair. The permutation p-value and the raw sham comparison
are reported alongside, as diagnostics.

## The gate, extended

All four arms must return their required verdict — NEG-1 and NEG-2 must **not**
qualify, POS-1 and POS-2 must qualify — and, additionally:

> **Calibration.** The gate is repeated across **40 independently generated
> datasets**. The observed false-qualification rate of NEG-2 must not exceed the
> nominal level materially. One favourable seed establishes nothing; a test that
> passes on one seed and fires on a fifth of others is worse than no test,
> because it looks like evidence.

The sham null, the donor criterion and the permutation diagnostic are all
evaluated **together in a single pass**, exactly as they will be on real data.

**If NEG-2 still qualifies after this, the sham criterion has not solved the
underlying problem and v6 is replaced prospectively rather than argued around.**

## Everything else

Unchanged from v5: the NB GLM on raw nonnegative counts with the frozen `log D`
offset; predictors leave-one-out centered within `donor × operator` stratum and
the readout never centered; minimum stratum 20; held-out donors by hash; the
frozen denominator including structural-missingness handling; the six directed
tests; reserved genes SALL1, CTSD, CTSS, LPL, CSF1R, HLA-DMB frozen; HVS
excluded from anything requiring observed LPL; `TRAINING=OFF`; scope limited to
the audited addresses in candidate myeloid nuclei.

The biological question is unchanged and is the point of all of this: does the
four-partner state carry information beyond both the queried gene and the
technical dependence the sham reproduces?
