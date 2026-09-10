# Common-support restriction alone: the step-4 precursor

*Superseded as "step 4" by the owner-frozen matched-QC contract
(`configs/v4/t0_tail_matched_qc_contract_v1.json`, commit `bc60a921`). Retained
because it establishes why restriction alone is not enough and why matching is
required — which is the finding that motivates that contract's matching stage.*


Declared outcome: **`QC_ASSOCIATION_STILL_FIRES__RESTRICTION_INSUFFICIENT`** —
the third of the four outcomes frozen in advance.

**Diagnostic only.** `RARE_TAIL_UNDERDETERMINED_MEASUREMENT` is unchanged,
`training_authorized: false`, no successor estimator, QC gate, threshold or
training authority is designed or chosen. Implements
`configs/v4/t0_tail_common_support_contract_v1.json`, frozen in `974ba90d`
before the probe was written. Records in
`outputs/t0_tail_common_support_20260910/`.

## The result

The unrestricted control reproduces both committed objects exactly — the frozen
coherence field by field and the frozen QC veto on contrast, p, replicates,
donors and veto — before any restricted number is quoted.

| | cells (tail / rest) | holdout coherence | exact p | QC max contrast | QC p | veto |
| --- | ---: | ---: | ---: | ---: | ---: | :---: |
| unrestricted | 516 / 6,521 | 0.104216 | 7.63e-06 | 0.294686 | 0.018 | **fires** |
| common support | 513 / 5,736 | 0.103714 | 7.63e-06 | **0.322805** | **0.011** | **fires** |

Restricting to the region where each donor's tail and rest cells overlap in
Q_DEPTH and Q_DETECT **did not reduce the confound. It increased it** — the
frozen statistic rose from 0.2947 to 0.3228 and became more significant, 0.018 to
0.011. The veto still fires.

Holdout coherence is essentially unchanged, 0.104216 to 0.103714, with LOO mean
cosine 0.2660 to 0.2652 and per-donor holdout direction cosine 0.9898 to the
unrestricted vectors. But that carries almost no information here, for a reason
given below.

## Why the confound got worse, mechanically

Two facts explain it, and both are measured rather than inferred.

**The restriction was mild.** Only 785 of 6,521 rest cells were removed — 12% —
and 3 of 516 tail cells. The tail already occupies a narrow band within its
donor, so the common-support box is close to the tail's own range and most rest
cells were already inside it.

**The frozen statistic standardises by a quantity the restriction shrinks.** The
frozen `_donor_delta` computes

```
(mean over tail  -  mean over rest) / std over ALL retained cells
```

Removing rest cells at the extremes of the QC range reduces that denominator.
The numerator falls too, but not as fast, so the ratio rises. The effect is
concentrated exactly where the geometry predicts — the donors with the fewest
tail cells, whose common-support box is narrowest and whose rest group loses the
most:

| donor | tail before → after | rest before → after | abs Q_DETECT contrast before → after |
| --- | ---: | ---: | ---: |
| H20.33.024 | 6 → 5 | 111 → 60 | 0.4949 → **1.0530** |
| H21.33.012 | 6 → 5 | 203 → 184 | 0.1590 → **0.6133** |
| H20.33.027 | 10 → 10 | 204 → 168 | 0.0080 → 0.2279 |
| H21.33.039 | 8 → 8 | 192 → 137 | 0.1585 → 0.2431 |

Only 6 of 18 donors show an increase, but those increases are large enough to
lift the cohort mean.

## What this means, stated exactly

**The coherence result is not interpretable as confound-free.** That was frozen
in advance as the consequence of this outcome, and it holds: the confound is
still detectable among the retained cells, so a surviving held-out coherence
cannot be attributed to biology rather than to the residual QC difference. And
because the restriction removed so little, the coherence number is close to
unchanged for the trivial reason that the data barely changed.

**Common-support restriction is the wrong instrument for this confound.** When
one group occupies a narrow sub-range of the other, restricting to the overlap
mostly trims the wider group's tails, which shrinks the standardiser rather than
balancing the comparison.

**And this is a defect in the statistic as a production gate, separate from
anything about T0.** The frozen QC statistic is **not monotone under support
restriction**: applying the standard remedy for confounding makes the measured
confound look worse, through the denominator rather than through the data. A gate
with that property cannot be used to certify that a confound has been addressed,
because the natural corrective action moves it the wrong way.

**Balancing beyond restriction was not available under this contract's
inherited minima.** 1:1 matching sets each donor's rest count equal to its tail
count, and with a median of 22 tail cells that pushes most donors below the
frozen `MIN_REST_CELLS` of 20 when the adjudicator is used. This contract
recorded that in advance so the absence of a balancing variant would be a
consequence of the frozen minima rather than a choice made here.

The owner's matched-QC contract resolves this properly rather than by relaxing a
threshold: eligibility is stated as a minimum of **five matched pairs** and ten
decision donors — the same frozen numbers, applied to the matched design where
the rest group is the same size as the tail group by construction — and the
exact common-direction test is applied directly to the eligible donor vectors
rather than through the adjudicator that enforces the rest minimum. That is the
step that actually equalises the comparison.

## Where the four steps leave the tail

| step | question | answer |
| --- | --- | --- |
| 1 | which QC axis carries the frozen contrast | Q_DETECT attains it, but the axes substitute in the null 476/523 and correlate at 0.92, so this discriminates weakly |
| 2 | does depth alone move the tail label | yes, strongly — 9–11% label churn at 10% depth loss, 39% at half depth, and the upper tail is the most depth-sensitive region |
| 3 | does an independent held-out program survive depth reduction | yes — coherent at the exact-test floor down to quarter depth, while the labels are fragile |
| 4 | does the confound survive removing the tail/rest QC difference | the difference was not removable by restriction, and the statistic got worse |

**The rare tail is not resolvable with this estimand on this data.** Not because
the evidence is absent — step 3 found a donor-consistent held-out program that
survives a fourfold depth reduction on genes that did not select the cells — but
because the confound cannot be separated from it by any diagnostic available
here. `RARE_TAIL_UNDERDETERMINED_MEASUREMENT` is the correct terminal, and after
four steps it is better supported than when it was adjudicated.

That is a decision-relevant answer rather than a null one. A successor design
should treat the tail as requiring either a different estimand — one whose
scoring is detection-invariant by construction rather than by adjustment — or
deeper and more uniform data. It should not treat it as a thing to be recovered
by a correction applied to the current estimator.

## For the V5 QC framework

The transferable findings, which is why this arc was worth running:

1. **Do not gate on a max over collinear technical axes.** They substitute for
   each other in the statistic and the winner is a weak discriminator.
2. **Do not gate on a standardised cross-cell contrast whose denominator is
   estimated on the cells being restricted.** It is not monotone under the very
   remedy the gate would prompt.
3. **A score that sums over detected entries and subtracts a fixedall-gene offset
   is not detection-invariant.** Characterise that sensitivity before freezing an
   estimator, not after.
4. **Support restriction is not balance.** Verify with a recomputed statistic
   rather than assuming the restriction worked.
5. **Association gates and intervention gates answer different questions.** Step
   3 is the shape a qualification gate should take: hold the grouping fixed,
   change only the measurement, and ask whether the conclusion moves.

## Stopping here

No successor tail estimator, weighting scheme, QC gate or threshold is proposed
in this document. The matched-QC analysis proper is the owner-frozen contract,
reported separately.
