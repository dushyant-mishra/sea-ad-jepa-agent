# GSE178317 — recovered, qualified, and externally validated

Date: 2026-09-24
Supersedes: `GSE178317_GUIDE_JOIN_STOP_20260923.md` and
`GSE178317_RECOVERY_RESULT_20260924.md` (the v1 failure record, retained).

```
guide reads recovered from SRA      PASS
cell-to-guide assignment (v2)       PASS   11,775 of 58,302 cells, 39/39 targets
target engagement                   PASS   39/39 knocked down, median log2FC -0.715
external validation vs CRISPRbrain  PASS   35/35 direction, Spearman 0.720
```

The 2026-09-23 STOP held that the guide-to-cell join could not be completed. It
was right about the processed GEO deposit and wrong about the experiment.

## Provenance

Count stage executed from committed head `662639f6`, clean worktree, 47m35s,
2026-09-24T16:07:53Z to 16:55:28Z. Call stage and downstream from `49c64d77`.

```
recover_gse178317_guide_assignments_v2.py     3aa48c6ed33445e5...
build_gse178317_intervention_effects_v1.py    286e6c1fdfd268d2...
sgRNA library (Suppl. Table 5)                8de1e7e737c8c42e...
```

Heavy artifacts, referenced not committed:

```
gse178317_cell_guide_umi_counts_v2.npz    3,121,266 B  170a16797d681124...
gse178317_cell_guide_assignments_v2.csv     965,167 B  3719a109f18ce9f5...
gse178317_top_effects_v1.csv                 77,129 B  a022e4709d9a18bd...
```

## Read layer

```
spots read                  221,434,278
reads on called cells       190,036,621
reads carrying a guide      174,012,015   (91.6%)
guide UMIs after dedup       18,006,495
cells with >=1 guide UMI         54,950   of 58,302
distinct guides                   81/81   in every lane
```

`gex_called_cells` sums to **58,302**, the published figure exactly, so lane
wiring and cell sets agree with the depositors independently. The deduplicated
UMI total reproduced v1's **18,006,495** exactly, so the read layer is
deterministic across the v1 and v2 implementations.

## Assignment

v1 assigned 10 cells. Its rule required the top guide to hold 70% of a cell's
guide UMIs, which is the wrong question for an sgRNA **enrichment** library:
hemi-nested PCR amplifies ambient guide transcripts, so the median cell carries
167 guide UMIs spread across the whole 81-guide library and nothing approaches a
70% share. That rule came from GSE311359, where direct guide capture makes it
appropriate. **The threshold was not retuned.** The method was replaced.

v2 requires agreement of two differently motivated statistics, mirroring the
published use of demuxEM with the Tian et al. 2019 z-score cutoff:

* a per-guide robust z-score of the cell fraction against a median/MAD
  background — because any one guide is carried by a small minority of cells,
  that guide's across-cell distribution estimates the ambient background;
* a Poisson tail test of the observed count against an ambient expectation of
  cell depth times the guide's share of all guide UMIs.

Exactly one guide must pass both, so multiplets and ambiguous cells are reported
unassigned rather than resolved by a tie-break.

```
cells_total          58,302        targets_represented        39
cells_judged         47,318        ntc_cells                 800
cells_assigned       11,775        cells per target  min 33 | median 277 | max 800
cells_multiplet          44        usable targets (>=40 cells)  38 of 30 required
```

Sensitivity over the declared grid, showing the answer is not an artifact of the
cut:

```
z>=3.0  13,180     z>=5.0  11,775  (operating point)     z>=8.0   4,976
z>=4.0  12,654     z>=6.0  10,228                        z>=10.0  1,897
```

v1's equivalent grid ran 10 to 0.

This assignment is **more conservative than the depositors'**, who report about
28,905 singly assigned cells. That is the expected direction for a rule
requiring two tests to agree, and no adjustment was made toward their number.

## Target engagement

Computed from our own assignments, per (lane, target) pseudobulk against that
lane's own non-targeting cells, averaged across lanes:

```
targets analyzed              39
engagement measured           39
knocked down (log2FC < 0)     39     <- all of them
estimable uncertainty         37     (>=3 lanes at >=10 cells)
median engagement log2FC  -0.7146
```

## External validation

CRISPRbrain hosts the depositors' own processed differential expression for this
experiment. The two paths share no intermediate: ours runs from archived SRA
reads through our guide calling, pseudobulk and normalisation; theirs is their
pipeline's output.

```
targets comparable            35
direction agreement        35/35
Spearman rho               0.720
Pearson r                  0.598
median ours / reference   -0.715 / -0.233
magnitude ratio            3.07x
```

Two aspects matter more than the headline number.

**Agreement on their own nulls.** Of the 35, eighteen carry FDR >= 0.05 in the
reference analysis. On those, median |log2FC| is 0.399 for us against 0.168 for
them — a ratio of 2.37x, *below* the 3.07x overall scaling. A pipeline
manufacturing signal would inflate nulls more than hits, not less.

**Magnitude was declared in advance as not expected to match.** A stricter guide
caller admits fewer cells and therefore carries fewer misassigned cells diluting
each estimate toward zero, so larger effects are the predicted consequence of
the stricter rule rather than a discrepancy.

Restricted to the 17 targets called at FDR < 0.05 in the reference, all 17 agree
in direction and Spearman is 0.306 — lower than the overall 0.720 because
restricting to hits truncates the range. Recorded rather than omitted.

The single visible outlier is **AARS**: -1.56 from 18 cells for us against
-0.225 with FDR 1 for them. Eighteen cells is the one target below the declared
40-cell usability floor, so the floor identified it without being asked to.

## What this study now contributes

39 perturbed genes in iPSC-derived microglia with transcriptome-wide responses
and cell-level data under our own control. All 39 targets are present in the
FULL104 address space, 35 in the common core, none unobserved, median detected
in 104 of 104 donors.

```
TRAINING=OFF · AUDIT_B_N1=UNOPENED · PROTECTED_OUTCOMES=UNOPENED · THERAPEUTIC_RANKING=OFF
```
