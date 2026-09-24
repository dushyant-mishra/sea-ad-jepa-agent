# GSE175721 — guide-to-cell join: **STOP stands**, but the reason is now specific

Date: 2026-09-24
Branch: `analysis/perturbation-etl-gse301119-claude-20260923`
Supersedes: the GSE175721 determination recorded on 2026-09-23, which reached the
same verdict on partly wrong grounds.

```
file authentication        PASS   unchanged
guide reference            FOUND  deposited all along, 14 CROP-seq vectors
guide features in matrix   ABSENT stock 10x hg19, 32,738 genes, no vector contig
cell barcodes in BAM       PRESENT raw CR and UR tags on every unplaced read
guide reads in BAM         ~45 estimated in the whole file, far too few
author metadata file       DESCRIBED IN GEO BUT NEVER DEPOSITED
guide-to-cell join         STOP
statistical analysis       NOT_EXECUTED
```

---

## What the 2026-09-23 determination got wrong

The earlier note dismissed this study after searching the feature list for the
`CRISPR Guide Capture` feature type and finding none, then reporting that name
matches such as `C8orf44-SGK3` and `KNTC1` were false positives.

That search was wrong in principle. In CROP-seq the sgRNA is transcribed as a
polyadenylated Pol II transcript, so when it is captured at all it is added to
the *transcriptome* reference and appears as an ordinary `Gene Expression`
feature. `CRISPR Guide Capture` is the feature type for a different assay
(10x Feature Barcoding), and its absence says nothing either way.

The earlier note also did not mention `GSE175721_CRISPR_seq.fa.gz`, a 427-byte
supplementary file that was deposited with the series from the start.

## The guide reference was deposited

`GSE175721_CRISPR_seq.fa.gz`
(sha256 `45e8d92cd4cfebb7b53233931cbee20bf5abdd5e82216efa6b0c7646658a673f`)
holds 14 complete CROP-seq vector sequences, each about 380 bp. The protospacer
sits between the U6 terminus `GGAAAGGACGAAACACCG` and the scaffold
`GTTTTAGAGCTAGAAATAGCAAG`, and all 14 extract cleanly at exactly 20 nt:

| guide | protospacer | guide | protospacer |
|---|---|---|---|
| TREM2-sG1 | GAAAGACGAGATCTTGCACA | BIN1-SG1 | AAGGCAGCTTATTGTCCGGA |
| TREM2-SG2 | CGCCTTCATAATTCACCCCA | PLCG2-SG1 | GAAGCAGAAGTAGCGAGCGC |
| CD33-SG1 | GACAAGAACTCCCCAGTTCA | CASS4-SG1 | CAGGCATTGAGACGTGAGTG |
| SORL1-SG1 | CAGTAGCGTTCGCCCGAACA | PTK2B-SG1 | AGGTAGGTGTGCAACGGCTC |
| PICALM-SG1 | TTAGAATGGCAGCAACGTGT | APOE4-SG1 | AGGACGTCCTTCACCTCCGC |
| SHIP1-SG1 | GAGCCGGTCATTCCACCCAG | APOE4-SG2 | AGGGTCCCAGCTCTTTCTAG |
| CD2AP-SG1 | AGTGCTAAGGAAGAGGCGAG | RIN3-SG1 | ATCATGCCGCCGGCAGCTCC |

Thirteen AD risk genes. `SHIP1` is the informal name for `INPP5D` and must be
mapped to that symbol before any cross-study join.

The reference file has been staged at
`analysis/therapeutic_perturbation_etl/reference/GSE175721_CRISPR_seq.fa`.

## The deposited matrix cannot carry the guides

Both samples share one feature file
(sha256 `f4e843b9639e5aa41b1826c51360dc316dfef3d324239e583f8562e25d930377`):
32,738 features, every one typed `Gene Expression`, which is the stock Cell
Ranger hg19-1.2.0 reference unmodified. None of the 14 guide names appears. The
vector was never added to the reference, so no guide count could exist in the
matrix regardless of how well the guides were captured.

## The barcodes survive in the submitted BAM, but the guide reads do not

ENA holds the submitted Cell Ranger BAMs rather than FASTQ:
`BC03.bam.1` 30,538,916,109 bytes and `BC04.bam` 29,449,572,855 bytes, both
indexed. The header confirms the alignment reference and that barcodes are
recorded:

```
STAR_2.5.1b  --genomeDir .../cellranger-2.1.0/refdata-cellranger-hg19-1.2.0
84 contigs: chr1-22, X, Y, MT and GL000* scaffolds; no vector contig
CO  10x_bam_to_fastq:R1(CR:CY,UR:UY)
```

Scanning the unplaced-unmapped region of `BC03.bam.1` over HTTP with a local
index, 400,000 reads examined out of 17,902,462 unplaced (2.2%):

```
raw cell barcode CR        400,000   present on every read
raw UMI UR                 400,000   present on every read
corrected barcode CB             0   Cell Ranger 2.1.0 writes none on unmapped reads
reads containing scaffold        4
reads containing a protospacer   1   (TREM2-SG2)
```

The single hit reads
`GACGAAACACCGCGCCTTCATAATTCACCCCAGTTTTAGAGCTAGAAATAGCAAGTTAAAATAAGG`,
which is the expected U6 terminus, protospacer and scaffold in order, so the
extraction logic is correct and the rate is real rather than a parsing failure.

Scaled to the whole unplaced region that is roughly **45 protospacer-bearing
reads and 179 vector-derived reads in the entire 30 GB file**. This is an
extrapolation from a 2.2% prefix and is reported as such; it is not a measured
total. No plausible correction to it reaches the scale needed to assign guides
across the roughly 10,000 cells in the sample.

## Why the yield is this low, and why GSE178317 differs

GSE175721 deposited **two samples, both plain 10x 3-prime gene expression**.
There is no sgRNA enrichment library anywhere in the series. Unenriched CROP-seq
guide capture in a 3-prime library is known to be poor, and four vector reads per
400,000 is what that looks like.

GSE178317 is recoverable precisely because that lab did the opposite: they
reserved cDNA and ran hemi-nested enrichment PCR into four separately indexed
sgRNA libraries, which are archived in SRA with the cell barcode read intact.
The difference between the two studies is the enrichment library, not the
archive and not the analysis.

## The specific thing that is missing

The GEO sample record for GSM5345023 states:

> Read count matrix was formated by mtx. Barcodes and genes were provided by tsv
> format. **Metadata file was provided as tab-separated format.** gRNA sequences
> used in this study are shown as fasta format.

Three of those four items are present. The tab-separated metadata file is not,
at any level of the deposit:

| location | contents |
|---|---|
| GSE175721 series suppl | `CRISPR_seq.fa.gz`, `RAW.tar`, `filelist.txt` |
| GSE175722 SuperSeries suppl | `RAW.tar`, `filelist.txt` |
| GSM5345023 sample suppl | barcodes, features, matrix |
| GSM5345024 sample suppl | barcodes, features, matrix |

Every `filelist.txt` was read directly; nothing was inferred from filenames.
The metadata file the submitters describe was never uploaded.

## Required to lift the STOP

One specific, answerable request, in order of preference:

1. **The tab-separated metadata file the GEO record already promises.** If it
   carries the per-cell guide assignment, the study qualifies immediately with no
   reprocessing, because the matrices and the guide reference are already in hand.
2. The sgRNA enrichment FASTQ files, if such a library was sequenced and not
   deposited.
3. Their Seurat object with the guide assignment in `meta.data`.

Contact of record: Bilal Cakir, In-Hyun Park laboratory, Yale University
(`bilal.cakir@yale.edu`), listed as submitter on the series.

This is a materially better position than the 2026-09-23 note left us in. That
note said the guide identities were simply not deposited and the study could not
be used. In fact the guide reference is in hand, the cell barcodes are in hand,
and exactly one named file is missing — one the depositors already stated they
had provided.

## What GSE175721 can contribute without the join

Nothing as a perturbation dataset. No assignment was inferred, and none should
be: with about 45 guide-bearing reads the only achievable assignment would be
invented, which is the one thing a perturbation dataset must not contain.

Separately, the sibling SubSeries **GSE175719** under the same SuperSeries is a
microglia-presence by amyloid 2x2 in organoids (`hCO`, `hCOAB`, `mhCO`,
`mhCOAB`, plus GFP-sorted fractions). It is a context dataset rather than a
genetic perturbation dataset, and like GSE240609 it has one sample per design
cell, so differences are computable and uncertainty is not estimable. It has not
been acquired or qualified and is noted here only so the option is on record.

```
TRAINING=OFF · AUDIT_B_N1=UNOPENED · PROTECTED_OUTCOMES=UNOPENED · THERAPEUTIC_RANKING=OFF
```
