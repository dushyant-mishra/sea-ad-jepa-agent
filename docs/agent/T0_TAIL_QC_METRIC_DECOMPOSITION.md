# Rare-tail QC veto, decomposed: step 1 of the QC methodology investigation

**Diagnostic only, and non-authoritative.** The frozen tail terminal remains
`RARE_TAIL_UNDERDETERMINED_MEASUREMENT`. Nothing here modifies T0 V20, the
frozen QC gate, `QC_ALPHA`, the tail definition, the terminal, or training
authority, and no remediation is designed or tested. `training_authorized:
false`.

Records:

- `outputs/t0_tail_qc_decomposition_20260910/T0_TAIL_QC_METRIC_DECOMPOSITION.json`
- `…/T0_TAIL_QC_DONOR_COMPONENTS.csv` — 18 decision donors x 2 metrics, signed and absolute
- `…/T0_TAIL_QC_REPLICATE_COMPONENTS.csv` — 999 replicates x `T_depth`, `T_detect`, `T_max`, argmax

Pathology-blind: no AT8 value is read. The already-materialised confirmation
cells, masks and decision donors are reused; the tail mask is not recalculated
under any different rule.

## Regression check first

A decomposition of a statistic it cannot reproduce would describe something
else, so reproduction is a precondition and any mismatch is a STOP. Using the
frozen per-donor contrast function, the frozen hash-seeded permutation key and
the frozen constants directly:

| quantity | reproduced | recorded |
| --- | --- | --- |
| observed max statistic | `0.2946862124155104` | `0.2946862124155104` |
| exceedance count `ge` | 17 | 17 |
| `p_upper` | 0.018 | 0.018 |
| `veto` | true | true |

Bit-exact on the statistic, exact on `ge` and `p_upper`. Fourteen tests
reconstruct all of this from the published CSVs rather than from anything the
report asserts about itself.

## The two components

| metric | observed mean absolute standardized contrast | share of max | percentile in own null | exceedances | descriptive p |
| --- | --- | ---: | ---: | ---: | ---: |
| Q_DEPTH | `0.24365980396814418` | 0.8268 | 82.98% | 170 | 0.1710 |
| **Q_DETECT** | `0.2946862124155104` | **1.0000** | 98.60% | 14 | 0.0150 |

`Q_DETECT` attains the frozen maximum; its value *is* the frozen statistic.
`Q_DEPTH` is smaller and sits unremarkably inside its own null.

The component p-values and percentiles are **diagnostic, non-authoritative
quantities, not new p-value gates**. The frozen test takes the maximum across
metrics precisely to control multiplicity, so a single component's position in
its own null cannot license a different tail terminal.

## The finding that most constrains interpretation

**Across the frozen null the two axes very nearly split the maximum: Q_DEPTH
wins 476 replicates, Q_DETECT 523, no exact ties.**

That is a 47.6 / 52.3 split. Under random within-donor label reassignment,
either axis attains the maximum about half the time. So the statistic does not
structurally favour one dimension; the two components largely **substitute for
each other** in it.

Read together with their correlation — Pearson r = 0.9232 across discovery
donors, each retaining roughly nine percent independent residual variance once
the other is included, and the nuisance design's condition number rising from
about 310.6 to 37,671 when both are appended — the honest reading is that the
gate is built around two highly redundant readouts of substantially the same
measurement process.

**So "Q_DETECT carries more of the contrast" is the whole claim available here.**
It is not evidence of a unique causal mechanism, and nothing in this
decomposition attributes the contrast to detection rather than depth as a
physical cause. With components that substitute in the null and correlate at
0.92 in the data, which one attains the observed maximum is a weak
discriminator.

## How donor-distributed and how stable

**Broad, not driven by a few donors.** Signed `Q_DETECT` contrasts run from
−0.3711 to +0.7911, positive in 10 of 18 donors, mean +0.1435. The statistic
averages the *absolute* contrast, so what it detects is that tail cells differ
in detection in either direction more than chance allows — not that tail cells
uniformly detect more.

**Not a thin-tail artifact.** Sorting donors by contrast puts two donors with
only 5 and 6 tail cells at the top, so the obvious suspicion is that a few
thinly-tailed donors carry the statistic. Tested, and it does not hold:

| | value |
| --- | ---: |
| correlation, tail-cell count vs abs Q_DETECT contrast | **+0.101** |
| correlation, 1/sqrt(tail count) vs abs contrast | +0.053 |
| 6 donors with ≤10 tail cells, mean abs contrast | 0.2993 |
| 12 donors with >10 tail cells, mean abs contrast | 0.2924 |
| tail cells per donor | min 5, median 22, max 129 |

The two groups are indistinguishable and the correlation is negligible and if
anything the opposite sign from a noise-inflation story.

**Stable to single-donor removal.** Leave-one-donor-out over all 18 donors: the
larger component remains `Q_DETECT` in every case. No donor's removal flips the
identity of the larger axis.

For scale, a random within-donor split of the same size already yields a mean
absolute contrast of about 0.206, so the observed 0.295 is roughly 43% above the
null mean.

## What step 1 establishes, and what it does not

Established: the frozen statistic is reproducible exactly; `Q_DETECT` attains
it; the effect is broad across donors, mixed in direction, and stable to
single-donor removal; and the two components substitute for each other under the
null, so the gate discriminates poorly between them.

Not established, and not addressable by this test at all: whether the
tail/QC dependence is **technical in origin**. The frozen test asks whether
tail-labelled cells differ from their donor's other cells in these metrics
against randomly reassigned labels. That is a valid association test, and
association is weaker than demonstrating a technical artifact. The test is
better understood as an **identifiability veto** than as a production QC design.

There is also a near-circularity worth stating plainly, because it bounds what
any cross-cell version of this test could ever show. Tail membership is derived
from an expression score computed from the raw counts, and `Q_DETECT` is the
fraction of nonzero genes in those same raw counts. The score normalizes for
library size first, which helps, but normalization cannot make detection and
dropout behaviour disappear: a score built from observed nonzero counts can
correlate with detection even when the underlying biological state is genuine.

The frozen T0 decision therefore stands as the correct conservative call —
technical and biologically induced dependence were not distinguishable, so the
tail claim was refused — and it remains untouched.

## Next, in order

This is step 1 of five. Steps 2 to 4 are the diagnostics that can address the
causal question this one cannot, and step 5 is deliberately last:

2. **Same-cell depth perturbation.** Thin molecules from the exact confirmation
   cells to prospectively fixed lower depths with fixed seeds, recompute the
   frozen target score and tail classification, and measure score displacement,
   rank stability and tail-label flip rates. This asks whether changing
   measurement depth *alone* manufactures or destroys the tail.
3. **Separate biology from the genes used to call the tail**, by testing the
   already-separated coherence/holdout genes rather than the scoring genes after
   perturbation or matching.
4. **Matched-QC tail analysis** within each donor, restricted to overlapping
   Q_DEPTH/Q_DETECT support, with no extrapolation beyond common support.
5. **Only then**, design a successor tail estimator, frozen before it touches
   confirmation. Not chosen because it rescues this tail.

Note on step 5, recorded now so it is not forgotten later: QC residualisation
should not be the first candidate. If biological state genuinely affects
transcript complexity, regressing QC out can subtract biology, which is the same
error as demanding independence from observed QC in the first place.
