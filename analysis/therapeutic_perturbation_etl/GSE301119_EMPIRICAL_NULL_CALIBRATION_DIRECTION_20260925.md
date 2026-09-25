# Direction for repairing the GSE301119 estimand — a design note, not a qualified method

**Status: DESIGN DIRECTION ONLY. Nothing here is implemented, tested or
authorised to run.** No estimator in this document may be used to produce a
number until it has a producer, an adversarial suite and a qualification
contract, in that order. A specification is not in force until an executor
enforces it.

## What the repair has to clear

The matched-NT negative control decomposed the bias into two terms of very
different size:

| term | isolated by | median bias | share of total |
|---|---|---|---|
| read depth, zeros, pseudocount | depth-only binomial thinning (composition held fixed) | -0.046 measured, -0.074 simulated under pure Poisson at 19.8x | about **5 %** |
| between-cell state composition | cell-sampling arm minus the above | — | about **95 %** |

Any candidate repair must be judged against the **dominant** term. Two obvious
ones are not:

* **Expression-stratification** cleans the depth term convincingly — genes at
  50 CPM or above carry -0.001 at 19.8x and -0.007 even at 50x, while the bottom
  deciles carry -0.1 to -0.47 — and would therefore pass its own diagnostic while
  leaving 95 % of the problem intact. Genes whose abundance is concentrated in a
  subpopulation (CLU, CXCL10, MT1G) carry large composition variance *regardless*
  of overall abundance, so matching on abundance does not match on the thing that
  actually varies.
* **A negative-binomial GLM with library-size offsets** correctly handles depth
  and zeros, but contains no term for between-cell state variance, so it also
  addresses only the 5 %.

## The direction that does address the dominant term

Use the instrument the negative control already built. For each gene, at each
unit size, the repeated size-matched non-targeting draws **are** the null
distribution. Express a real effect as its position in that distribution — a
quantile, or a standardized deviation against its own null — rather than as a raw
log2 fold-change.

This works on the dominant term for a structural reason rather than a modelling
one: the null draws carry the depth gap **and** the composition variance, because
they are drawn the same way the real unit was. Both terms are absorbed at once,
and no new distributional assumption is introduced.

The practical consequence is that the negative control stops being a one-off
verdict and becomes a reusable calibration layer.

## The assumption it carries, stated plainly

**Non-targeting cells span the same state heterogeneity as perturbed cells.** If
perturbation itself shifts which states are present, the NT-derived null is not
the right reference for a perturbed unit, and effects would be miscalibrated in a
direction that depends on the perturbation. This assumption is testable and must
be tested before the layer is trusted; it is not assumed away here.

## Why CRISPRa is the part to run first

The bias is negative in both modalities (CRISPRi -1.41, CRISPRa -1.75). An
observed **up**-call therefore has to overcome the bias, which means the true
effect is bounded below by the observed one. That is the conservative direction,
and it makes CRISPRa engagement the part of this dataset the artifact cannot
manufacture.

That is currently an argument, not a measurement. The gene-specific empirical
null is what converts it: if a CRISPRa target's observed effect sits in the
extreme upper tail of its own size-matched null, it survives. The five shared
direct targets (CSF1R, CSF2RA, CSF2RB, TGFBR1, TGFBR2) should be run through the
null before anything further is claimed about them — the current receipt covers
the seven sentinels and tail recurrence only, not those rows.

## What is explicitly not licensed

No causal claim, no p-value, no therapeutic ranking, no benchmark promotion. The
null draws share NT units and are Monte Carlo references, not independent
biological replicates. GSE301119 remains n=2 donors.

```
TRAINING=OFF · AUDIT_B_N1=UNOPENED · PROTECTED_FULL104_OUTCOMES=UNOPENED
D_SHARED_G5=UNOPENED · RARE_TAIL_MOLECULAR=UNOPENED · THERAPEUTIC_RANKING=OFF
```
