# GSE178317 — guide identity recovered; DEVELOPMENT-scope result, corrected

Date: 2026-09-24, corrected same day after independent review (PRs #101, #102).
Supersedes: `GSE178317_GUIDE_JOIN_STOP_20260923.md`.
Retains: `GSE178317_RECOVERY_RESULT_20260924.md` (the v1 failure record).

```
guide reads recovered from SRA      PASS
cell-to-guide assignment (v2)       PASS_LANE_SUPPORT_ONLY
                                    11,775 of 58,302 cells, 39/39 targets
target engagement                   39/39 knocked down, median log2FC -0.7146
biological uncertainty              NOT ESTIMABLE
comparison vs CRISPRbrain           35/35 direction, Spearman 0.720
                                    reference comparison, NOT replication
scope                               DEVELOPMENT, not prospective confirmation
```

The 2026-09-23 STOP held that the guide-to-cell join could not be completed. It
was right about the processed GEO deposit and wrong about the experiment.

## Corrections to the first version of this document

The first version of this file, pushed earlier today, made three claims that
independent review correctly rejected. They are listed first because the rest of
the document should be read in their light.

1. **It reported "estimable uncertainty: 37".** The four 10x lanes are capture
   wells loaded from one pool of day-eight iTF-Microglia. They are not
   independent differentiations, donors or cell lines. Spread across them is
   technical and process variation. Presenting it as biological uncertainty was
   wrong. The corrected producer reports `technical_well_spread` and fixes
   `biological_uncertainty_estimable` to FALSE.
2. **It described the CRISPRbrain comparison as "external validation" whose two
   paths "share no intermediate".** The reads are the shared intermediate. It is
   the same experiment analysed twice, so it tests whether our pipeline recovers
   what theirs did. It is reference data, **not independent replication**, and
   cannot support a claim about the biology reproducing.
3. **Its usability gate could pass an unusable design.** It checked global
   per-target counts only, so 30 targets confined to L1 with all controls in L2
   would have passed while producing zero within-lane comparisons. The repaired
   gate requires >=40 cells in total AND >=3 lanes holding >=10 target cells and
   >=10 same-lane NTC cells.

A fourth point stands on the record: the thresholds `z=5`,
`min_usable_targets=30` and `min_cells=40` were declared after an inspected
0.27% smoke run. That is development calibration, not prospective held-out
confirmation, and the receipts now say so.

## Provenance

Count stage from committed `662639f6`, clean worktree, 47m35s,
2026-09-24T16:07:53Z to 16:55:28Z. Call stage re-run through the repaired
lane-support gate; effects from `build_gse178317_intervention_effects_v2.py`.
`build_gse178317_intervention_effects_v1.py` is fail-closed and retained for
provenance only.

Heavy artifacts, referenced not committed:

```
gse178317_cell_guide_umi_counts_v2.npz    3,121,266 B  170a16797d681124...
gse178317_cell_guide_assignments_v2.csv     965,167 B  (lanegate re-run)
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

`gex_called_cells` sums to **58,302**, the published figure exactly. The
deduplicated UMI total reproduced v1's **18,006,495** exactly, so the read layer
is deterministic across two independent implementations. Both facts concern the
read layer only and say nothing about the assignment.

## Assignment

v1 assigned 10 cells. Its rule required the top guide to hold 70% of a cell's
guide UMIs, the wrong question for an sgRNA **enrichment** library: hemi-nested
PCR amplifies ambient guide transcripts, so the median cell carries 167 guide
UMIs spread across the whole 81-guide library and nothing approaches a 70%
share. That rule came from GSE311359, where direct guide capture makes it
appropriate. **The threshold was not retuned.** The method was replaced.

v2 requires agreement of two statistics: a per-guide robust z-score of the cell
fraction against a median/MAD background, and a Poisson tail test against an
ambient expectation of cell depth times the guide's share of all guide UMIs.
Exactly one guide must pass both.

This is an **approximation in the same spirit** as demuxEM and the Tian et al.
2019 z-score cutoff, not a reimplementation of either. No claim of guaranteed
false-discovery control is made; the Bonferroni correction is applied to the
Poisson component under an independence assumption the data need not satisfy.

```
cells_total          58,302        targets_represented        39
cells_judged         47,318        ntc_cells                 800
cells_assigned       11,775        cells per target  min 33 | median 277 | max 800
cells_multiplet          44        lane-supported targets    37 of 30 required
```

Sensitivity over the declared grid:

```
z>=3.0  13,180     z>=5.0  11,775  (operating point)     z>=8.0   4,976
z>=4.0  12,654     z>=6.0  10,228                        z>=10.0  1,897
```

v1's equivalent grid ran 10 to 0, so the answer is no longer an artifact of the
cut. This assignment is more conservative than the roughly 28,905 cells reported
by the depositors, the expected direction for a rule requiring two tests to
agree; no adjustment was made toward their number.

## Target engagement

Per (lane, target) pseudobulk against that lane's own non-targeting cells:

```
targets analyzed              39
engagement measured           39
knocked down (log2FC < 0)     39
technical well spread         37     <- capture-well variation, 4 wells
biological uncertainty        NOT ESTIMABLE
median engagement log2FC  -0.7146
```

Every CRISPRi target moves down. There is no biological error bar on any of
them, and none can be produced from this experiment as deposited.

## Comparison against CRISPRbrain — reference, not replication

CRISPRbrain hosts the depositors' own processed differential expression for this
same experiment. Our path runs from archived SRA reads through our guide
calling, pseudobulk and normalisation; theirs is their pipeline on the same
reads. Agreement therefore tests **our pipeline**, not whether the biology
reproduces.

```
targets comparable            35
direction agreement        35/35
Spearman rho               0.720
Pearson r                  0.598
median ours / reference   -0.715 / -0.233
magnitude ratio            3.07x
```

The informative part is the behaviour on their own nulls. Of the 35, eighteen
carry FDR >= 0.05 in the reference. On those, median |log2FC| is 0.399 for us
against 0.168 for them, a ratio of 2.37x, *below* the 3.07x overall scaling. A
pipeline manufacturing signal would inflate nulls more than hits, not less.

Magnitude was declared in advance as not expected to match: a stricter caller
admits fewer cells and so carries fewer misassigned cells diluting each estimate
toward zero.

Restricted to the 17 targets called at FDR < 0.05 in the reference, all 17 agree
in direction and Spearman falls to 0.306, because restricting to hits truncates
the range. Recorded rather than omitted.

The one visible outlier is **AARS**: -1.56 from 18 cells for us against -0.225 at
FDR 1 for them. Eighteen cells is below the declared 40-cell floor, so the gate
identified it without being asked to.

## What this study contributes, and what it does not

**Contributes:** 39 perturbed genes in iPSC-derived microglia with
transcriptome-wide response estimates and cell-level data under our own control.
All 39 targets are present in the FULL104 address space, 35 in the common core,
none unobserved, median detected in 104 of 104 donors.

**Does not contribute:** any biological error bar, any held-out confirmation, and
any evidence that the biology replicates. The scope is DEVELOPMENT. Promotion to
a confirmation role requires a validation design frozen before new outcomes are
viewed, and independent guide-identity evidence rather than a comparison against
the same experiment's own published analysis.

```
TRAINING=OFF · AUDIT_B_N1=UNOPENED · PROTECTED_OUTCOMES=UNOPENED · THERAPEUTIC_RANKING=OFF
```
