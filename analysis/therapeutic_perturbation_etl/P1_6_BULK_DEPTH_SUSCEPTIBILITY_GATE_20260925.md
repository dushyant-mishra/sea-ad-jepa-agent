# P1-6 susceptibility gate: are the bulk studies exposed to the depth artifact?

**Verdict: no. Both bulk studies clear the gate by a wide margin, and the P1-6
independent recompute can proceed safely and independently.**

## Why this gate exists

The GSE301119 negative control showed that a log2(CPM+1) contrast between groups
of very different sequencing depth produces a large systematic bias. Before
spending the next stretch of work on the remaining P1-6 recomputes, the cheap
question is whether GSE241858 and GSE240609 are susceptible to the same thing. If
they were, recomputing them faithfully would reproduce a biased quantity
precisely — which is the self-audit **S4** failure just demonstrated, not a second
independent instance of verification.

Both studies are **bulk** RNA-seq, so the dominant GSE301119 term — cell-state
under-sampling, worth roughly 95 % of the measured bias — does not apply at all:
there are no cells to sample. Only the depth term is in play. The reference point
is that at a 5x depth gap the simulated bias is about **-0.003** across all genes
and essentially zero for well-expressed ones, against the **19.8x** median gap
that produced GSE301119's failure.

## Measurement

Only the **within-contrast** ratio matters — the depth ratio between the two
groups actually being compared. Ratios across groups that are never contrasted
cannot produce a directional artifact.

### GSE241858 — 35 samples, depths from the `total_counts` column of `GSE241858_sample_identity.csv`

| contrast | numerator mean | denominator mean | ratio | abs(log2) |
|---|---|---|---|---|
| R47H_vs_CTRL_baseline | 11,716,943 | 8,549,522 | 1.370 | 0.455 |
| IFN_vs_UNTR_in_CTRL | 29,656,365 | 39,156,890 | 0.757 | 0.401 |
| IFN_vs_UNTR_in_R47H | 32,585,811 | 37,071,359 | 0.879 | 0.186 |
| LPS_vs_UNTR_in_CTRL | 37,571,112 | 39,156,890 | 0.960 | 0.060 |
| LPS_vs_UNTR_in_R47H | 35,796,526 | 37,071,359 | 0.966 | 0.050 |
| R47H_vs_CTRL_untreated | 37,071,359 | 39,156,890 | 0.947 | 0.079 |

**Worst within-contrast ratio: 1.370x.**

The max/min across all 35 samples is **16.6x**, which looks alarming in
isolation. It is not the susceptible quantity: it spans the baseline arm (mean
~8.5-11.7 M) against the cytokine arm (mean ~29.7-39.2 M), and no declared
contrast crosses those arms. Every contrast is within-arm.

### GSE240609 — 4 samples, depths computed from the deposited count files

The deposited `*_gene_counts.txt.gz` files carry **no header row**; a first pass
consumed `A1BG` as one. Corrected totals over all 27,154 genes:

| sample | genes | total counts |
|---|---|---|
| APOE3ch / WT (GSM7703564) | 27,154 | 17,235,291 |
| APOE3ch / PSEN (GSM7703567) | 27,154 | 21,558,869 |
| APOE3 / WT (GSM7703569) | 27,154 | 19,855,132 |
| APOE3 / PSEN (GSM7703571) | 27,154 | 18,832,128 |

| contrast (2x2 design) | ratio | abs(log2) |
|---|---|---|
| APOE3ch vs APOE3 in WT | 0.8681 | 0.2041 |
| APOE3ch vs APOE3 in PSEN | 1.1448 | 0.1951 |
| PSEN vs WT in APOE3ch | 1.2509 | 0.3229 |
| PSEN vs WT in APOE3 | 0.9485 | 0.0763 |

**Worst within-contrast ratio: 1.2509x**, which is also the max/min across all
four samples.

## Conclusion

| study | worst within-contrast ratio | gate reference (5x) | GSE301119 (failed) |
|---|---|---|---|
| GSE241858 | **1.370x** | 5x | 19.8x |
| GSE240609 | **1.251x** | 5x | 19.8x |

Both sit far below the level at which the depth artifact becomes material, and
neither is exposed to the cell-composition term at all. **P1-6 may proceed.**

## One thing recorded, not resolved

Within-group sample spread is modest everywhere except one group: cytokine /
CTRL / UNTR has an internal max/min of **6.02x** across its 4 samples (the next
widest is 2.08x). This does not create a directional bias between groups the way
a systematic gap does — it is heterogeneity, and it enters as noise rather than
as a shift — but it is worth knowing before that group is used as a denominator
in three of the six contrasts. It is recorded here, not adjusted for.

```
TRAINING=OFF · AUDIT_B_N1=UNOPENED · PROTECTED_FULL104_OUTCOMES=UNOPENED
D_SHARED_G5=UNOPENED · RARE_TAIL_MOLECULAR=UNOPENED · THERAPEUTIC_RANKING=OFF
```
