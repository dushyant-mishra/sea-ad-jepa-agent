# Which QC metric drives the rare-tail veto: detection, not depth

Diagnostic only. The frozen rare-tail terminal remains
`RARE_TAIL_UNDERDETERMINED_MEASUREMENT` on the authority of the max statistic at
p = 0.018, and nothing here re-adjudicates it.

Record: `outputs/t0_tail_qc_decomposition_20260910/T0_TAIL_QC_METRIC_DECOMPOSITION.json`.
Pathology-blind: no AT8 value is read.

## Why this needed doing

The frozen veto statistic is a maximum across the two QC metrics, and the
committed record stores only that maximum — 0.2947, p = 0.018 — without saying
which metric attained it. Depth-matched tail calling and
detection-residualised tail calling are different designs, and the two metrics
are strongly associated (Pearson r = 0.9232 on discovery donors), so which one
carries the signal was not guessable from the correlation.

## Faithfulness first

The decomposition would describe nothing if it could not reproduce the statistic
it decomposes, so that is a precondition rather than an assumption. Using the
frozen per-donor contrast function and the frozen hash-seeded permutation keys
directly:

```
observed max statistic   0.2946862124155104   (recorded: 0.2946862124155104)
max-statistic p_upper    0.018  (ge = 17)     (recorded: 0.018)
```

Bit-exact on the statistic and exact on p. The module refuses to report a
decomposition otherwise.

## The answer

| metric | mean \|standardized contrast\| | attains max | null mean | null p95 | descriptive p |
| --- | ---: | :---: | ---: | ---: | ---: |
| Q_DEPTH | 0.243660 | no | 0.2058 | 0.2740 | 0.1710 |
| **Q_DETECT** | **0.294686** | **yes** | 0.2064 | 0.2728 | **0.0150** |

**Q_DETECT is the frozen statistic.** Its observed contrast exceeds the 95th
percentile of its own null; Q_DEPTH's does not — 0.2437 against a null p95 of
0.2740, sitting unremarkably inside its own null at a descriptive p of 0.171.

So the cells being called rare-tail differ from their donor's other cells in the
*fraction of the address space detected*, not in library size, beyond what a
within-donor reassignment of the same size produces.

The per-metric p-values are descriptive. The frozen test takes the maximum
across metrics precisely to control multiplicity, so a single metric's position
in its own null is not a test and cannot license a different terminal. They are
here to identify the driver, not to re-decide anything.

## Two things about the shape of it

**The direction is mixed, so this is a magnitude effect rather than a systematic
bias.** Signed Q_DETECT contrasts run from −0.3711 to +0.7911, positive in 10 of
18 donors, mean +0.1435. The statistic averages the *absolute* within-donor
contrast, and what it is detecting is that tail cells differ in detection in
either direction more than chance allows — not that tail cells uniformly detect
more. A remediation aimed at a single global detection offset would be aimed at
something that is not there.

**It is not a small-n artifact, which is what I first suspected.** Sorting
donors by contrast puts two donors with only 5 and 6 tail cells at the top, at
+0.79 and +0.49, and a standardized mean difference on 5 cells is unstable — so
the obvious hypothesis is that a few thin-tailed donors carry the whole
statistic. Tested, and it does not hold:

| | value |
| --- | ---: |
| correlation, tail-cell count vs \|Q_DETECT contrast\| | **+0.101** |
| correlation, 1/sqrt(tail count) vs \|contrast\| | +0.053 |
| 6 donors with ≤10 tail cells, mean \|contrast\| | 0.2993 |
| 12 donors with >10 tail cells, mean \|contrast\| | 0.2924 |
| tail cells per donor | min 5, median 22, max 129 |

The two groups are indistinguishable, and the correlation is negligible and if
anything slightly *positive* — the opposite direction from a noise-inflation
story. The detection contrast is distributed across the cohort rather than
concentrated in the donors where it would be least trustworthy. That makes the
veto more credible, not less: it is not an artifact of six thin tails.

For scale: a random within-donor split of the same size already yields a mean
absolute contrast of about 0.206, so the observed 0.295 is roughly 43% above the
null mean, and ranks 15th of 1,000 in detection's own null. A real effect, and a
modest one.

## What this implies for remediation

Stated as implications for design, not as conclusions about biology.

**Depth matching is the wrong instrument.** Q_DEPTH is not the driver and is
unremarkable in its own null, so matching or residualising on library size would
leave the confound the veto found essentially untouched.

**Detection breadth is the thing to address**, and because the effect is mixed in
direction and spread across donors, a per-donor or per-cell treatment is more
plausible than a global one — for instance residualising the per-cell tail score
on per-cell Q_DETECT before thresholding, or matching tail and comparison cells
on detection within each donor. Either is a change to the estimand and needs its
own prospective freeze.

**A mechanistic hypothesis, labelled as one.** Q_DETECT is the fraction of the
35,076 scalar-measured addresses observed nonzero in a cell. At a given library
size, detection breadth reflects how evenly expression is spread across the
transcriptome. A cell called rare-tail has an unusual expression profile by
construction, so the tail score may be partly reading detection breadth rather
than the biological program it is meant to capture. That is exactly the confound
the veto exists to catch. It is consistent with what is measured here and is not
established by it; distinguishing "the tail score partly reads detection" from
"tail biology genuinely co-occurs with broader detection" needs a design that can
separate them, which is new work.

## Scope

- The frozen decision is untouched and was not recomputed as an alternative.
  `RARE_TAIL_UNDERDETERMINED_MEASUREMENT` stands.
- No V20 estimator, target, threshold, nuisance model, donor role, feature role
  or adjudication rule changes. No training authority. No gate opened.
- Pathology-blind throughout: the QC metrics and the tail mask are properties of
  the expression data and the frozen target.
- 516 tail cells of 7,037 confirmation cells (7.33%), 18 tail-measurable donors,
  999 frozen replicates.
