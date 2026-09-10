# Held-out tail coherence under depth thinning: step 3

**Diagnostic only.** `RARE_TAIL_UNDERDETERMINED_MEASUREMENT` is unchanged,
`training_authorized: false`, and no p-value threshold, rescue criterion, tail
rule, estimator or training gate is chosen from these results. No matched-QC
analysis is designed here.

Implements `configs/v4/t0_tail_holdout_thinning_contract_v1.json` exactly, as
frozen by the owner in `03372f16` before execution. Records in
`outputs/t0_tail_holdout_thinning_20260910/`.

## What was asked, and why the design matters

The frozen tail grouping is held **fixed** at every retention level. The
measurement changes; the labels do not. Re-deriving membership after thinning
would let the depth-sensitive SCORING estimator select the validation groups
again, which is the entanglement the diagnostic exists to avoid.

A consequence worth stating: with the grouping fixed, **the SCORING counts never
enter this step at all.** The report records `scoring_features_entering_validation: 0`.
Validation runs on the 7,015 COHERENCE_HOLDOUT addresses, 6,146 of them
decision-capable under the frozen discovery-fit scale — genes that played no
part in defining the grouping they are asked to validate.

Harness checks, all STOP-guarded and all passed: the unthinned baseline
reproduces the committed frozen coherence object field by field; retention 1.0
leaves counts, library, holdout vectors and pre-normalisation norms exactly
unchanged; the holdout decision-feature count reproduces the committed 6,146;
support counts are identical at every level, which is what a fixed grouping
requires; and the one derived function — the frozen vector builder — differs from
its frozen source by exactly one instrumented line.

## Result

| retention | mean pairwise cosine | exact p | null max | LOO mean cosine | LOO positive | mean donor cos to unthinned | min |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| baseline | **0.104216** | 7.63e-06 | 0.104216 | 0.2660 | 1.000 | — | — |
| 1.00 | 0.104216 | 7.63e-06 | 0.104216 | 0.2660 | 1.000 | 1.0000 | 1.0000 |
| 0.90 | 0.1001–0.1015 | 7.63e-06 | = observed | 0.259–0.261 | 1.000 | 0.966–0.970 | 0.901–0.922 |
| 0.75 | 0.0932–0.0965 | 7.63e-06 | = observed | 0.246–0.252 | 1.000 | 0.909–0.919 | 0.730–0.803 |
| 0.50 | 0.0833–0.0853 | 7.63e-06 | = observed | 0.228–0.231 | 1.000 | 0.782–0.811 | 0.517–0.598 |
| 0.25 | 0.0628–0.0712 | 7.63e-06 (2 draws), 2.29e-05 (1) | = observed except one draw | 0.185–0.203 | 1.000, 0.944 | 0.599–0.619 | 0.350–0.405 |

**The held-out program stays coherent at every level, including quarter depth.**
`coherence_ok` is true throughout.

Three details sharpen that.

`mean_pairwise_cosine` equals `null_max` at every level except one draw at
retention 0.25. The exact test enumerates all 131,072 donor sign
configurations, so this says the **all-positive configuration is the unique
maximiser** — the eighteen donors' held-out directions agree with each other
more than any of the 131,071 alternatives. That is the strongest available
outcome of that test, and `p = 7.63e-06` is its floor, 1/131,072.

Leave-one-donor-out positive fraction is **1.000** down to half depth: every
donor's held-out direction agrees with the consensus of the other seventeen. At
quarter depth it is 1.000 in two draws and 0.944, seventeen of eighteen, in the
third.

Individual donor directions nonetheless degrade substantially. Cosine to the
same donor's full-depth direction falls to a mean of 0.60 and a minimum of 0.35
at quarter depth. So each donor's estimate becomes noisy while the consensus
survives — the pattern expected of a genuine shared program observed with
increasing measurement noise, and the reason the cross-donor test still resolves
when the per-donor vectors no longer would.

Pre-normalisation vector magnitude is roughly stable — mean 28.30 at baseline
against 24.99–26.60 at quarter depth — so the scaled tail-versus-rest difference
does not collapse in size; what erodes is its direction.

## Comparison with step 2

At retention 0.25 the two steps disagree sharply about the same cells:

| | at quarter depth |
| --- | --- |
| SCORING-based tail label (step 2) | 57–61% of the 516 tail cells lose the label; within-donor rank Spearman 0.649 |
| COHERENCE_HOLDOUT program (step 3) | still coherent at the exact-test floor; every donor but one agrees with consensus |

That is the first of the two outcomes distinguished in advance: the held-out
program remains coherent while the scoring-based labels are depth-fragile.

## What this supports, and what it does not

**It supports the methodological conclusion.** A production rejection rule that
vetoes on the cross-cell QC association would reject this configuration — and
this configuration contains an independently measured, donor-consistent program
on genes that did not select the cells, significant at the exact test's floor
and still resolving after a fourfold reduction in depth. A rule that cannot
distinguish that case from an artefact is too coarse to carry production
rejection authority. This is exactly the calibration case it was hoped to be.

**It does not establish that the rare tail is real, and one limitation is
decisive.** Thinning removes the same expected fraction of molecules from every
cell, so it scales tail and rest depth together and **leaves the tail-versus-rest
depth and detection difference intact**. If the held-out contrast were itself
driven by that within-donor difference, it would survive thinning — which is
what was observed. So this step cannot separate "independent biology" from
"residual tail/rest depth contrast read out on independent genes". The contract
said so in advance, and it is why step 4 is not optional.

**Nor does it rescue anything in T0.** The frozen terminal stands. The frozen QC
veto was the correct conservative call on what it could distinguish; what has
changed is our understanding of what it *cannot* distinguish, which is a fact
about the method rather than about this result.

Two further limits carried from the contract: loss of coherence would not have
proven the tail artefactual either, since genuine signal becomes unmeasurable as
molecules are removed; and `support_ok` being true at every level carries no
information, because the grouping is fixed and the support counts cannot move.

## Next

Step 4, separately and prospectively frozen: the within-donor common-support and
matched-QC analysis, comparing tail and rest cells only where their Q_DEPTH and
Q_DETECT distributions overlap, with no extrapolation beyond common support.
That is the step that removes the difference this one deliberately preserved.

**Stopping here as instructed.** No matched-QC design is proposed in this
document.

## For V5

The transferable lesson, recorded because it is the reason this investigation
matters beyond T0. A cross-cell association gate would have rejected a case in
which an independent, prospectively separated readout carries a donor-consistent
program that survives fourfold depth reduction. A same-cell intervention gate
distinguishes the two situations that gate conflates: it separates "the
conclusion moves when only the measurement moves" from "the representation
correlates with a technical variable". The first is a defect; the second may be
biology. V5's anti-cheat framework should place rejection authority with the
former and treat the latter as a warning.
