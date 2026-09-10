# Matched-QC held-out validation: step 4

**Diagnostic only.** `RARE_TAIL_UNDERDETERMINED_MEASUREMENT` is unchanged,
`training_authorized: false`. No balance threshold, caliper, alternative
matching method, donor subset or holdout feature subset is chosen from these
results. Implements `configs/v4/t0_tail_matched_qc_contract_v1.json`, frozen by
the owner in `bc60a921` before the probe was written.

Records in `outputs/t0_tail_matched_qc_20260910/`.

## Headline

**The matching worked. The test it enabled has no power. No inference about
confounding is available from it.**

That last sentence is the finding, and only a control the contract did not
prescribe makes it visible.

## The matching succeeded

Every one of the 18 donors is eligible: all 513 common-support tail cells were
matched 1:1 without replacement against rest cells in pooled-rank QC space, and
all 18 clear the frozen minimum of five matched pairs, so the diagnostic is
decision-capable at 18 donors against a minimum of 10.

Balance, measured against a **fixed pre-match denominator** (see corrections):

| metric | mean abs SMD before | after | max before | after | reduction |
| --- | ---: | ---: | ---: | ---: | ---: |
| Q_DEPTH | 0.2437 | **0.0138** | 0.5343 | 0.0580 | 94% |
| Q_DETECT | 0.2947 | **0.0249** | 0.7911 | 0.0910 | 92% |

The observed QC imbalance is essentially gone. Per-donor extremes fall from
0.7911 to 0.0910 on Q_DETECT. This is the equalisation the whole step existed to
achieve, and the common-support precursor could not achieve it.

## And the held-out coherence collapses

| comparison | rest group | mean pairwise cosine | exact p |
| --- | ---: | ---: | ---: |
| unmatched (committed T0) | all rest, median 290/donor | **0.104216** | 7.63e-06 |
| matched 1:1 | matched, median 22/donor | **−0.000961** | 0.696 |

Leave-one-donor-out after matching: mean cosine −0.0040, positive fraction
0.444 — chance. The donor vectors have become mutually uninformative.

Read alone, that looks like a clean answer: the held-out program was the QC
confound, and removing the confound removed the program.

## The control says otherwise

The contract did not require one; it was added as a correction, with the
replicate count and seed rule fixed before it ran. It uses **the same matched
tail cells** against an equal number of rest cells drawn **at random from common
support instead of matched on QC**. That design keeps the confound — a random
common-support rest sample retains the tail/rest QC difference — and differs
from the matched analysis only in how the rest cells were chosen.

| | mean pairwise cosine | exact p |
| --- | ---: | ---: |
| size-matched random control, 20 replicates | mean **−0.001466**, sd 0.001296, range −0.003959 to +0.000934 | median 0.788 |
| matched 1:1 (observed) | **−0.000961** | 0.696 |

**The matched value sits inside the control range.** A comparison that retains
the confound produces the same roughly-zero coherence at the same sample size.

So the collapse from 0.104216 to zero is attributable to the reduction in
comparison-group size — median rest per donor falling from 290 to 22 — and not
to the removal of the QC imbalance. Each donor's holdout vector is a difference
of means over 6,146 genes; halving the effective sample size on the rest side
pushes those vectors to noise, and a cross-donor cosine of noise is zero.

**Without this control the honest-looking conclusion would have been wrong.** The
matched result would have read as evidence that the independent program was the
confound all along, which the data does not support.

## What step 4 establishes

- **1:1 matching on Q_DEPTH and Q_DETECT removes the observed imbalance**, by
  92–94% on the corrected balance measure. The method works.
- **At the resulting sample size the held-out coherence statistic has no
  power.** A design retaining the confound scores the same as one removing it.
- **Therefore the matched comparison is uninformative about confounding.** It
  neither supports nor undermines the held-out program.
- The frozen terminal is untouched and remains correct.

## What would be needed

Preserve the comparison-group size while balancing QC. That means k:1 matching
with several rest cells per tail cell, or a weighting estimator that keeps all
rest cells and reweights them to the tail's QC distribution. Either would retain
the power the 1:1 design destroys.

Both are explicitly out of scope here: the contract forbids choosing an
alternative matching method after seeing this result, and rightly so. A method
selected because it restores significance would be worthless. Any successor
design needs prospective freezing and owner authorisation, and it should be
**power-calibrated before it is run** — the size-matched control used here is
the natural calibration instrument.

## The two corrections applied

Both under the owner's standing authority to correct major scientific mistakes
in the contracts. Both are additive: every quantity the contract prescribes is
still computed and published, and both are recorded in the artifact under
`contract_corrections_applied`.

**`FIXED_DENOMINATOR_BALANCE`.** The contract asked for pre-match and post-match
standardized mean differences as the balance evidence. The frozen `_donor_delta`
divides by the standard deviation of whatever subset it is handed, so a
pre-match value over all of a donor's cells and a post-match value over its
matched pairs sit on **different scales** and their difference says nothing about
balance. This was not hypothetical — the common-support precursor had just shown
the frozen contrast *rising* from 0.2947 to 0.3228 purely because restriction
shrank the standardiser. Holding the denominator at the donor's pre-match spread
makes the pair comparable, which is the matching literature's convention for
exactly this reason, and it is what produces the 92–94% figures above. A test
asserts the fixed-denominator pre-match value equals the frozen pre-match value,
since the fixed denominator *is* the pre-match spread.

**`SIZE_MATCHED_UNMATCHED_CONTROL`.** As above. Without it a null result is
indistinguishable from a dead statistic.

## For the V5 QC framework

This is the sharpest lesson of the arc, and it generalises well beyond the tail.

**A gate that successfully removes a confound can simultaneously destroy the
power to detect the signal it was meant to validate — and the result looks like
a clean pass of the confound test.** An anti-cheat or QC gate must therefore
ship with a power calibration: a control that retains the artefact and shows the
gate can still see a real effect at the sample size the gate creates. Otherwise
"the representation no longer correlates with the technical variable" and "the
gate can no longer see anything" are the same number.

Combined with the earlier findings, the framework needs three properties: don't
demand independence from observed QC across cells; prefer same-cell
intervention for qualification authority; and calibrate every gate's power on a
confound-retaining control before granting it rejection authority.

## Stopping here

No successor tail estimator, matching method, weighting scheme, QC gate or
threshold is proposed. The next design decision is the owner's.
