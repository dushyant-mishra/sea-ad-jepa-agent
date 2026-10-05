# GSE301119 count-layer parity — Phase 1.1 qualification

Date: 2026-09-23
Branch: `analysis/perturbation-etl-gse301119-claude-20260923`

```
TERMINAL: PASS
  both modalities, two independent verification routes, zero discrepancies
```

## The blocker that was reported, and how it was removed

The previous report recorded that only **SeuratObject 4.1.0** was installed, that it
does not define `Assay5`, and that `dim()` returned *empty rather than raising* —
so the PR #81 checker could not run and was `NOT_EXECUTED`.

That is no longer the state. A current R and the matching SeuratObject were
installed into isolated locations, leaving the existing R 4.1.2 untouched:

```
R            4.6.1        D:/R-4.6.1                (new, isolated)
SeuratObject 5.4.0        D:/jepa_rlib46            (new, isolated library)
```

SeuratObject **5.4.0 is the exact version that wrote these objects**, so the
official accessor is now available rather than approximated.

## Route 1 — PR #81 checker, official accessor vs attribute-only reader

`crosscheck_seurat5_counts_v1.R`, taken verbatim from PR #81
(`sha256 7c2f9fd98e8cc40aaef1c9ca982a4a591b449e3fe6a820f1e1d5c7adaaffca4d`).

| check | CRISPRa | CRISPRi |
|---|---|---|
| `same_dim` | TRUE | TRUE |
| `same_features` | TRUE | TRUE |
| `same_cells` | TRUE | TRUE |
| `same_i` (CSC row indices) | TRUE | TRUE |
| `same_p` (CSC pointers) | TRUE | TRUE |
| `same_x` (nonzero values) | TRUE | TRUE |
| `same_colsum` | TRUE | TRUE |
| `same_rowsum` | TRUE | TRUE |
| **`exact_count_layer_parity`** | **TRUE** | **TRUE** |

```
CRISPRa   19,162 x 23,584    nnz 77,128,293
CRISPRi   36,601 x 28,466    nnz 89,015,982
```

The comparison is on the canonical CSC representation — indices, pointers and
values — not merely on totals, so a permutation that preserved sums would still
fail.

## Route 2 — the object's own metadata as an external oracle

Run before SeuratObject 5 was available, and kept because it is genuinely
independent: Seurat 5.4.0 computed `nCount_RNA` and `nFeature_RNA` when it **built**
the object and stored them in `meta.data`. Those values come from the producing
software, not from us.

| | CRISPRa | CRISPRi |
|---|---|---|
| colSums == `nCount_RNA` exactly | TRUE | TRUE |
| colNNZ == `nFeature_RNA` exactly | TRUE | TRUE |
| mismatched cells | **0 / 23,584** | **0 / 28,466** |
| counts integral / non-negative | TRUE / TRUE | TRUE / TRUE |

All 52,050 cells reproduce the producer's own per-cell totals exactly across
166,144,275 nonzero entries.

## What this does and does not establish

**Does:** the attribute-only reader decodes the physical count layers exactly.
Every downstream quantity in this lane — guide × donor pseudobulk, target
engagement — rests on correctly decoded counts.

**Does not:** parity is a *reader* property. It says nothing about whether the
downstream statistical treatment is appropriate, and target engagement remains a
narrow readout rather than a transcriptome-wide characterization.

## Provenance

```
source objects (unchanged, authenticated)
  GSE301119_CRISPRa_seurat5.rds   345,798,341 B
  GSE301119_CRISPRi_seurat5.rds   406,836,813 B
checker   crosscheck_seurat5_counts_v1.R   7c2f9fd9…  (verbatim from PR #81)
receipts  CRISPR{a,i}_pr81_count_parity.csv
          CRISPR{a,i}_count_reader_verification.csv
```

```
JEPA_TRAINING=OFF · THERAPEUTIC_RANKING=OFF · PROTECTED_FULL104_OUTCOMES=UNOPENED
```
