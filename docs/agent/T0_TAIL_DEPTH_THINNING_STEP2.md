# Same-cell depth intervention on the rare tail: step 2

**Diagnostic only.** `RARE_TAIL_UNDERDETERMINED_MEASUREMENT` stands untouched,
`training_authorized: false`, no remediation designed or tested, the tail rule
and threshold unmodified. Pathology-blind: no AT8 value is read.

Contract frozen before execution:
`configs/v4/t0_tail_depth_thinning_contract_v1.json`, committed in `7df39de6`
ahead of the implementation and the run, so no level, seed or check could be
chosen for the answer it produced.

Records: `outputs/t0_tail_depth_thinning_20260910/` — the report, a per-level CSV
(15 rows) and a per-cell CSV (35,185 rows across 5 levels).

## The question this asks that step 1 could not

The cross-cell QC test asks whether tail-labelled cells differ from their
donor's other cells in Q_DEPTH or Q_DETECT. That is association, and a genuine
biological state may also differ on those axes. The counterfactual question is
different: **holding cell identity fixed, does changing only the measurement
process move the biological conclusion?**

So: thin molecules from the exact confirmation cells to fixed lower depths,
recompute the score with the frozen scorer and the frozen fit, re-centre per
donor as the frozen builder does, re-apply the frozen threshold, and see what
happens to the label.

## Harness validation before any result

Two STOP-guarded checks, both passed:

- The recomputed unthinned baseline reproduces the **frozen tail mask for all 18
  donors**, so displacement is measured against a baseline built by the same
  code path.
- The control level, retention 1.0, displaced **no score** (mean, median and p95
  absolute displacement all exactly 0.0), flipped **no label**, held the tail at
  516 cells and returned within-donor Spearman 1.0 — on all three draws.

The intervention also demonstrably did what it claims: mean Q_DETECT fell
0.07673 → 0.07208 → 0.06446 → 0.04949 → 0.03006 and mean Q_DEPTH 8.6258 →
8.5205 → 8.3382 → 7.9326 → 7.2397 across the ladder.

## Result

Three draws per level; draw-to-draw variation is small throughout, so these are
level effects rather than sampling noise. Tail starts at 516 of 7,037 cells.

| retention | mean abs displacement | in donor SD | within-donor Spearman | tail cells | tail→rest | rest→tail |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1.00 *(control)* | 0.00000 | 0.000 | 1.000 | 516 → 516 | 0 | 0 |
| 0.90 | 0.00151 | 0.143 | 0.969 | 516 → 496–516 | 45–57 | 37–46 |
| 0.75 | 0.00269 | 0.254 | 0.916 | 516 → 492–502 | 101–104 | 80–87 |
| 0.50 | 0.00434 | 0.408 | 0.808 | 516 → 426–432 | 194–203 | 104–118 |
| 0.25 | 0.00600 | 0.562 | 0.649 | 516 → 325–341 | 296–314 | 120–123 |

**The tail label is highly fragile to measurement depth.** A 10% depth
reduction — retention 0.9, the mildest rung — already churns roughly 9–11% of
the tail label in each direction. Halving depth removes about 39% of the
original tail cells. At quarter depth, 57–61% of them are gone.

**Depth does not merely shift scores, it reorders them.** Within-donor Spearman
falls 0.969 → 0.916 → 0.808 → 0.649. A uniform shift would be absorbed entirely
by the per-donor centering and would flip nothing; the rank decay says the
displacement is heterogeneous across cells within a donor.

**And the compression is systematic toward the mean.** The correlation between a
cell's baseline centered score and its signed displacement is −0.150 at
retention 0.9, −0.383 at 0.5 and −0.557 at 0.25: the higher a cell scores, the
more its score falls. Split by label at retention 0.25, mean signed displacement
is **−0.00997 for tail cells against +0.00079 for the rest**, with mean absolute
displacement about 2.2 times larger for tail cells. The overall mean is exactly
zero because centering forces it, so this is redistribution, not drift.

That explains the monotone shrinkage in the table: lowering depth compresses the
upper tail toward the donor mean, and cells fall back across a threshold that
has not moved.

## Why the frozen estimator behaves this way

Worth stating because it is a property of the frozen design rather than of this
probe. `score_raw_counts` computes

```
score = sum over NONZERO entries of log1p(10000 * count / library) * w
        - (mu . w) over ALL genes
```

A gene dropping to zero loses its contribution while the offset is unchanged.
The frozen score is therefore **not detection-invariant by construction**, and
cells whose high score rests on many detected genes have the most to lose. This
probe measures that consequence; it does not introduce it.

## What this establishes, and what it does not

**Establishes.** Changing measurement depth alone, with cell identity held
fixed, substantially moves the frozen tail label — mildly at 10% depth loss,
severely at half depth. The extreme scores that define the tail are the most
depth-sensitive part of the distribution. So the tail label as currently
constructed cannot be treated as a depth-stable property of a cell.

**Does not establish that the tail is artefactual.** This is the inference to
resist, and the contract froze the caution in advance. A genuine rare
biological state is also measured worse at lower depth: losing it under thinning
is exactly what one would expect of real signal observed with fewer molecules.
Fragility to depth is a statement about the estimator's robustness, not about
whether the underlying state exists.

**Does not separate depth from detection.** Thinning moves both together, by
construction. Step 1 already showed the two axes substitute for each other in
the frozen statistic (null argmax 476 / 523), and nothing here improves that.

**What it does do for the identifiability question** is show that the direction
of causation the veto worried about is real and operative: reduced detection
lowers the score and removes tail membership. The association the frozen QC test
found is therefore exactly the kind measurement variation can generate. The
frozen decision to refuse the tail claim looks well founded on this evidence,
and the underdetermination is not resolved in either direction.

## Next

3. **Test the held-out genes rather than the scoring genes.** The coherence and
   holdout gene sets are already separated from the SCORING set the tail score
   is built on. If tail cells still show coherent held-out gene geometry after
   the measurement conditions are equalised, that is much stronger evidence of
   biology than anything computable from the scoring genes, because it breaks
   the near-circularity between the label and the metric.
4. **Matched-QC tail analysis** within each donor, restricted to overlapping
   Q_DEPTH/Q_DETECT support, with no extrapolation beyond common support.
5. **Only then** a successor estimator, frozen before it touches confirmation.

Step 2 sharpens the requirement on step 3: because the frozen score is not
detection-invariant and its upper tail is the most depth-sensitive region, any
evidence that survives on **held-out** genes after equalising measurement is
worth considerably more than evidence drawn from the genes that defined the
label.
