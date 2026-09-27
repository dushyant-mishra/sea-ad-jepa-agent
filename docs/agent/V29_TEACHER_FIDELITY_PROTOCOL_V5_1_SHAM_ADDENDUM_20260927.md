# Protocol v5.1 — addendum fixing the sham comparison

**Addendum to v5 (`48cd89c0`, sha256
`fe429ede1aa9c1960f8c60a379d17b98ab5882ae07a9063681219ea857c2e362`). v5 stands;
this pins down one criterion it left underspecified.**

**Dated 2026-09-27, before any real outcome exists.** The synthetic gate has been
run; no control gene has been extracted and no real expression has been read.

## Why this is needed now

The gate's NEG-2 arm — independent programs, shared per-nucleus capture
efficiency, sparse counts — produced a **qualifying association where there is
none**: median increment +0.0230, 73% of evaluation donors positive, permutation
p = 0.02.

The diagnosis matters more than the number. **The permutation null is the wrong
instrument for this artifact.** Permuting the program state within stratum
destroys the capture link along with everything else, so the null shows no
association and the observed dependence looks significant. But the observed
dependence is real; it is simply not biological. A permutation test asks whether
there is *any* dependence. The question here is whether there is dependence
*beyond capture efficiency*, and the pseudocounted CLR carries capture at these
counts however the null is constructed.

v5 already names the right instrument — criterion 3, the abundance-matched sham,
which carries the identical capture leak and no biology. The gate implementation
omitted it. Adding it implements the freeze; it does not relax it.

## The criterion, stated exactly

For each directed test, a **sham predictor** is built: four genes matched to
*P*'s partner abundance distribution, sharing the same nuclei and therefore the
same capture efficiency, with no biological relation to *Q*. The sham is carried
through the identical pipeline — same offset, same controls, same centering,
same split, same statistic.

> **Criterion 3.** The real program's per-donor increment must exceed the sham's
> **in at least two thirds of evaluation donors**, compared **paired within
> donor**.

A bare "real median > sham median" is a coin flip when both carry only the leak,
which is precisely the NEG-2 case this must catch. The paired two-thirds rule
matches criterion 2's form and is not coin-flippy.

Criteria 1 and 2 are unchanged. A directed pair passes only if **all three**
hold. A program qualifies only if both its directed tests pass.

## What this changes in the expected behaviour

| arm | real carries | sham carries | criterion 3 | arm verdict |
|---|---|---|---|---|
| NEG-1 | nothing | nothing | not met | no association — correct |
| NEG-2 | capture leak | capture leak | **not met** | no association — correct |
| POS-1 | signal | nothing | met | association — correct |
| POS-2 | signal + leak | leak | met | association — correct |

The sham is what separates "dependence" from "dependence beyond the technical
factor the sham shares". The gate must be re-run with it, and all four arms must
return their required verdict before any real data is read.
