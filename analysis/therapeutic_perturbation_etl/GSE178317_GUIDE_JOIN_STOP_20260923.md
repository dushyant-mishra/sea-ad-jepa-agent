# GSE178317 — guide-to-cell join: **STOP**, guide identities were not deposited

Date: 2026-09-23
Branch: `analysis/perturbation-etl-gse301119-claude-20260923`

```
file authentication        PASS   (2 assets, 16 archive members, unchanged)
lane pairing               PASS   established empirically, not from filenames
guide-to-cell join         STOP   no guide features exist in the deposited assets
raw-count qualification    NOT_EXECUTED
statistical analysis       NOT_EXECUTED
```

This study is the **Kampmann CRISPRi/a iPSC-microglia platform** — the same lineage
as the project's historical failure benchmark. Its CROP-seq arm is exactly the
direct microglial counterpart to the already-qualified primary-macrophage
experiments, which is why it was prioritized. It cannot be qualified as a
perturbation dataset from what was deposited.

---

## What the assets contain

Two acquired assets, 16 archive members, all previously authenticated:

| lane | gene expression | sgRNA enrichment |
|---|---|---|
| 1 | GSM5387652 | GSM5387656 |
| 2 | GSM5387653 | GSM5387657 |
| 3 | GSM5387654 | GSM5387658 |
| 4 | GSM5387655 | GSM5387659 |

each as `filtered` and `raw` `feature_bc_matrix.h5`.

## The lane pairing was established from the data, not the filenames

The acquired SOFT record is **series-level only** — 61 lines, listing sample IDs
with no per-sample titles or characteristics. It therefore does not independently
establish which sgRNA lane belongs to which expression lane, and the lane number
appears only in the supplementary filename. Inferring the join from that would be
exactly the filename inference this work forbids.

So the pairing was derived from barcode containment instead. For each expression
lane × sgRNA lane pair, the fraction of sgRNA-lane barcodes also called in the
expression lane:

```
           sg L1   sg L2   sg L3   sg L4
 gex L1    0.051   0.004   0.004   0.004
 gex L2    0.004   0.091   0.003   0.003
 gex L3    0.004   0.004   0.091   0.003
 gex L4    0.004   0.004   0.004   0.100
```

The diagonal is 12–25× the off-diagonal. The pairing is 1↔1, 2↔2, 3↔3, 4↔4, and it
**agrees** with the filename numbering — but it is now supported by the data
rather than by the naming.

## Why the join still cannot be completed

The sgRNA-enrichment matrices contain **no guide features at all**:

```
GSM5387656..659, filtered AND raw, all four lanes
  33,538 features   feature types: {'Gene Expression': 33538}
  CRISPR Guide Capture features: 0
```

They carry the standard 33,538-gene transcriptome reference — `MIR1302-2HG`,
`FAM138A`, `OR4F5`, … — and are almost empty: 100,129 nonzeros over 6,794,880 raw
barcodes in Lane 1, and less in the others.

A name search for guide-like features returns only genes whose symbols happen to
contain the substring: `ISG15`, `SGIP1`, `ISG20L2`, `MSGN1`, `RASGRP3`, `TSGA10`.
Those are genes, not guides.

**Conclusion:** the sgRNA enrichment libraries were processed against the
transcriptome reference rather than against a guide reference, so guide identity
is absent from the deposited processed assets. Which of the 38 targeted genes was
perturbed in any given cell is not recoverable from these files.

No assignment was inferred. Doing so would mean inventing the perturbation
identity, which is the one thing a perturbation dataset must not contain.

## What the bulk asset does and does not support

`GSE178317_iTF_Microglia_RNAseq_abundance.csv.gz` — 60,232 genes × 18 samples,
Ensembl IDs with symbols:

```
iTF-iPSCs Day0            x3
iTF-Microglia Day9 PBS    x3     Day9 LPS  x3     Day15  x3
BrownJohn-Microglia Day9 PBS x3  Day9 LPS  x3
```

The series description mentions Day-8 non-targeting and PFN1 CRISPRa samples.
**Those samples are not in this file.** So the bulk asset supports a
differentiation and LPS-stimulation design across two microglial models — a
legitimate *context* dataset — but it is **not** a genetic perturbation dataset
and must not be presented as one.

## Required to lift the STOP

Any one of these, none of which can be manufactured locally:

1. the CRISPR Guide Capture matrices, or a per-cell protospacer-call table, as
   GSE293118 deposited and GSE311359 embeds directly;
2. an authenticated author-supplied cell-to-guide assignment table;
3. the Day-8 CRISPRa bulk arms, for a much narrower NT-vs-PFN1 contrast.

Until one exists, GSE178317 contributes an LPS-context bulk dataset and no
perturbation effects.

## Comparison across the three CRISPR studies

| study | where guide identity lives | join risk |
|---|---|---|
| GSE301119 | in the Seurat object metadata | none; already qualified |
| GSE293118 | separate file, **different GSM** | verified: 83,564 called barcodes, zero orphans |
| **GSE311359** | **same matrix as the genes** | none by construction |
| **GSE178317** | **nowhere in the deposited assets** | **STOP** |

```
TRAINING=OFF · AUDIT_B_N1=UNOPENED · PROTECTED_OUTCOMES=UNOPENED · THERAPEUTIC_RANKING=OFF
```
