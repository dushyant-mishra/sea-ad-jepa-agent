# GSE178317 — guide identity recovered from SRA; cell assignment **FAILED**

Date: 2026-09-24
Producer: `scripts/recover_gse178317_guide_assignments_v1.py`
Executed from committed head `ab0b5dae`, clean worktree, script sha256
`69bc14ed510d0847c436e28787ac9460400d8e8632d27ccaf5b14dd5d37ab943`
Runtime 47m02s, 2026-09-24T15:13:15Z to 2026-09-24T16:00:17Z

```
guide reads recovered from SRA   PASS
cell-to-guide assignment         FAIL   10 of 58,302 cells
intervention effects             NOT_EXECUTED
```

The 2026-09-23 STOP said the guide-to-cell join could not be completed from the
deposited assets. That was correct about the deposit and wrong about the
experiment: the read-level recovery works. The failure here is in the calling
rule, and it is mine.

## What worked

| quantity | measured |
|---|---|
| spots read across 4 lanes | 221,434,278 |
| reads on Cell Ranger called cells | 190,036,621 |
| reads carrying a library guide | **174,012,015 (91.6%)** |
| guide UMIs after deduplication | 18,006,495 |
| cells with at least one guide UMI | **54,950 of 58,302 (94.3%)** |
| distinct guides observed | **81 of 81, in every lane** |

`gex_called_cells` sums to **58,302**, which is exactly the figure the authors
report in Supplementary Table 6 and in the GEO processing text. The lane wiring
and cell sets therefore agree with theirs independently.

## What failed, and why

```
cells_assigned                   10
assignment_rate                  0.0002
guide UMIs per cell (L1)         354, spread across 81 guides
```

The pre-declared sensitivity grid, fixed in the producer before the run:

```
umi>=3,  dom>=0.70   ->    10
umi>=5,  dom>=0.70   ->     0        <- the declared operating point
umi>=5,  dom>=0.80   ->     0
umi>=10, dom>=0.70   ->     0
umi>=10, dom>=0.90   ->     0
```

The rule required the top guide to hold at least 70% of a cell's guide UMIs.
That is the wrong question for this assay. These are **sgRNA enrichment
libraries** built by hemi-nested PCR, which amplifies every guide transcript in
the droplet including ambient ones, so a typical cell carries 354 guide UMIs
distributed across the whole library and no guide reaches a 70% share.

The rule was imported from GSE311359, where it is appropriate because that study
uses direct guide capture with far lower per-cell guide depth. It was applied
here without checking that the assay matched. The defect is the transfer, not
the threshold value.

## What is deliberately not being done

The threshold is **not** being lowered until the cell count looks reasonable.
The authors recovered about 28,905 singly assigned cells, and a dominance cutoff
could be slid until it reproduces that number, but a frozen acceptance threshold
retuned against a known answer carries no evidential weight, and the resulting
assignments would be an artifact of the tuning.

## The principled repair

Replace the *method*, not the constant. The GEO record states what the authors
used:

> sgRNA unique molecular identifier (UMI) counts for each cell barcode were
> obtained using a previously described mapping workflow (Hill et al., 2018).
> To facilitate sgRNA identity assignment, a combination of demuxEM (Gaublomme
> et al., 2019) and a z-score cut-off method we previously described (Tian et
> al., 2019) were used.

The distinction that matters: a z-score cutoff asks whether a guide's count in a
cell is an outlier **across cells for that guide**, which is robust to a uniform
ambient background. A dominance fraction asks whether a guide leads **within a
cell**, which is not. Adopting a published method is a different act from
sliding one's own constant, and only the former is available here.

Required changes to the producer:

1. persist the per-cell by per-guide UMI matrix, so calling rules can be
   evaluated without re-streaming 221M spots for 47 minutes;
2. implement the per-guide across-cell z-score assignment, with its parameters
   declared before it is run;
3. report the assignment rate unconditionally, as now.

## This does not block the study

CRISPRbrain hosts `iTF Microglia-Day-8-CROP-seq-CRISPRi`, the processed
differential expression for this same experiment: 343,707 rows over exactly the
same 39 target genes, with target engagement measurable directly (35 of 35
targets with a self row are knocked down, median log2FC -0.233, 17 at FDR<0.05).
GSE178317's scientific content is therefore already available to this project.

The cell-level recovery remains worth completing, because it gives control over
normalisation, cell filtering and pseudobulk construction that consuming a
processed table does not. But it is a question of control, not of access.

```
TRAINING=OFF · AUDIT_B_N1=UNOPENED · PROTECTED_OUTCOMES=UNOPENED · THERAPEUTIC_RANKING=OFF
```
