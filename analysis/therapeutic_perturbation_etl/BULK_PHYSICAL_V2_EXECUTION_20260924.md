# Corrected physical bulk ETL — GSE254205, GSE240609, GSE241858

Date: 2026-09-24
Executed on the GPU laptop against the physically authenticated source store.
The V2 producers originate in parallel draft PRs **#86** (GSE254205) and **#94**
(GSE240609 identity freeze and corrected bulk producer); they were reviewed and
executed here, not merged.

```
GSE254205  PASS_DEVELOPMENT_ETL   9 bulk samples, V1/V2 effect parity EXACT
GSE240609  PASS_DEVELOPMENT_ETL   4 samples, 2x2 complete, NOT_ESTIMABLE
GSE241858  PASS_DEVELOPMENT_ETL   clone-level, 2 clones per genotype
```

## GSE240609 — identity freeze verified against physical bytes

PR #94 freezes four GSMs by public GEO title, genotype pair, filename and
SHA-256. Every digest was recomputed from the extracted archive and matches:

```
GSM7703564  APOE3CH-WT      neuron WT    x microglia APOE3ch   105,792 B  OK
GSM7703567  APOE3CH-PSEN1   neuron PSEN  x microglia APOE3ch   107,793 B  OK
GSM7703569  APOE3-WT        neuron WT    x microglia APOE3     106,848 B  OK
GSM7703571  APOE3-PSEN1     neuron PSEN  x microglia APOE3     106,590 B  OK
```

Four files, four design cells, **no extra files and no missing cell**. The V2
producer fails closed on design-cell collision and on a missing genotype cell,
so an incomplete 2x2 cannot be silently analysed.

```
samples 4 | genes 27,154 | detected 19,045 | contrast rows 38,090
replicates per design cell 1  ->  uncertainty_estimable = FALSE
```

The corrected material semantics are carried in the output rather than left in a
commit message: the RNA is **CD11b-purified microglia recovered AFTER neuron
coculture**, not unfractionated coculture. Response may therefore depend on
neuron context, and one sample per genotype cross forbids a biological standard
error. No cell-autonomous claim follows.

## GSE241858 — clone is the biological unit

```
baseline  12 samples | 28,395 genes | 20,509 detected |  4 clone-treatment units
cytokine  23 samples | 28,395 genes | 24,157 detected | 12 clone-treatment units
clones per genotype: 2 (both arms)
```

Two independent clones per genotype, with within-clone replicates grouped
beneath the clone. The unbalanced `CTRL_A:LPS` cell carries one replicate where
the others carry two, and is recorded rather than padded. This is a bulk
genotype-by-context design and is **not** a CRISPR perturbation study.

## GSE254205 — assayed-undetected is not structurally missing

The correction PR #86 exists for, executed on the physical nine-sample assay:

```
genes in annotation                      58,395
genes assayed                            58,395
genes detected anywhere across 9 samples 36,117
genes assayed but undetected             22,278
genes structurally unmeasured            0
detection filter  DETECTED_ANYWHERE_ACROSS_NINE_SAMPLES
```

All three treatment contrasts preserved, replicates preserved before
aggregation:

```
AB_vs_NT       36,117 scored | median log2FC -0.0404 | |log2FC|>1: 2,253 | >2: 109
AB_GNE_vs_AB   36,117 scored | median log2FC  0.0499 | |log2FC|>1: 3,840 | >2: 481
AB_GNE_vs_NT   36,117 scored | median log2FC  0.0037 | |log2FC|>1: 2,030 | >2: 300
```

### V1 to V2 effect-field parity: EXACT

The point of V2 is to correct a **label**, not a number, and that is provable:

```
rows            V1 108,351   V2 108,351
keys            common 108,351 | V1-only 0 | V2-only 0
log2fc          max |delta| = 0.000e+00  over 108,351 comparisons
se              max |delta| = 0.000e+00  over 108,351 comparisons
n_numerator     max |delta| = 0.000e+00
n_denominator   max |delta| = 0.000e+00
all shared string fields              identical
```

V2 adds exactly three columns — `assayed`, `detected_anywhere`,
`effect_inclusion_rule` — and changes no effect value. The 22,278 genes formerly
implied to be structurally missing are now correctly recorded as assayed and
undetected, which is a different biological statement: the assay looked and saw
nothing, rather than never having looked.

**Drug-induced change is not evidence of disease rescue.** No rescue or reversal
claim is computed, and the receipt records that explicitly.

## What remains open for GSE254205

Three authenticated assay assets are still unprocessed and require metadata-first
handling with an exposure declaration before any previously unread effect is
inspected:

```
GSE254205_ad_raw.h5ad.gz                        734,059,992 B   snRNA-seq
GSE254205_iMG_LD_sort_RNA_seq.tar.gz              2,114,725 B   LD-sort
GSE254205_human_APOE3_IPSCmicroglia_ATAC.tar.gz   1,701,960 B   ATAC
```

All three are physically verified in the WP-A inventory. None has been opened.

## Scope

Development ETL on one cell model and one timepoint per study. No predictor
fitted, no therapy ranked, no reserved outcome opened.

```
TRAINING=OFF · AUDIT_B_N1=UNOPENED · PROTECTED_FULL104_OUTCOMES=UNOPENED
D_SHARED_G5=UNOPENED · THERAPEUTIC_RANKING=OFF
```
