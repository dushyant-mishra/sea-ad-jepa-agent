# GSE301119 — qualified end-to-end intervention-effect dataset

Date: 2026-09-23
Branch: `analysis/perturbation-etl-gse301119-claude-20260923`
Parent: `45354a9c5948ae1545135a9e40c83e78b3c05825`

```
FIRST MILESTONE: MET
  physical dataset audit  PASS_PERTURBATION_ETL_PHYSICAL_ATLAS_V1   16/16 assets
  GSE301119               QUALIFIED end to end, feature blocker resolved
```

No JEPA training, no therapeutic ranking, no disease-reversal claim, no FULL104
artifact touched. Every number below is a measured experimental observation; none
is a JEPA prediction or a simulated input erasure.

---

## 1. Physical authentication — all 16 assets

```
schema   THERAPEUTIC_PERTURBATION_ETL_ATLAS_V1
terminal PASS_PERTURBATION_ETL_PHYSICAL_ATLAS_V1
studies  8    processed assets 16    physically authenticated 16
missing or hash mismatch  0
```

Byte sizes and SHA-256 matched the historical Stage81A1C-P registries for every
asset. Local store: `data/external/v4/perturbation`, 4.2 GB.

## 2. The blocker that was open, and how it resolved

The readiness registry marked GSE301119 resolved on guides, controls, replicates
and perturbation identity, with **`feature_ids_fully_resolved = False`** — the two
objects declare different feature universes.

Measured directly from the objects:

| | CRISPRa | CRISPRi |
|---|---|---|
| features | 19,162 | 36,601 |
| cells | 23,584 | 28,466 |
| guide identities | 1,090 | 1,114 |
| target genes | 207 | 207 |
| NT control cells | 2,117 | 2,184 |
| NT control guides | 99 | 99 |
| donors | D1, D2 | D1, D2 |
| duplicate barcodes | 0 | 0 |

Every one of these matches the historical `stage81a1c_p_seurat_object_audit.csv`
exactly.

**Resolution:** the universes are nested, not merely overlapping.

```
CRISPRa ∩ CRISPRi = 19,162
CRISPRa \ CRISPRi = 0          <- CRISPRa is an exact SUBSET
CRISPRi \ CRISPRa = 17,439
```

Both use HGNC symbols in one namespace. CRISPRi carries the unfiltered CellRanger
GRCh38 reference (`MIR1302-2HG`, `FAM138A`, `AL627309.1`…); CRISPRa is filtered.

**Measurement mask, not zero-fill.** The 17,439 CRISPRi-only features are
*measured in CRISPRi and unmeasured in CRISPRa*. They are masked, never recorded
as zero expression. Two of 412 CRISPRi target rows have a targeted gene absent
from the matrix; those carry `target_gene_measured = FALSE` rather than a
fabricated zero.

## 3. A reader-environment finding worth recording

The objects are **Seurat 5.4.0 / `Assay5`**. The only Seurat on this machine is
**4.1.1 / SeuratObject 4.1.0**, which does **not** define `Assay5`:

```
isClass("Assay5")  ->  FALSE
readRDS(...)       ->  loads; RNA class reports "Assay5"
dim(x)             ->  returns EMPTY, no error raised
```

That is the dangerous shape: a v4 accessor returns nothing rather than failing,
so a pipeline trusting it could silently produce empty or misinterpreted
matrices. Extraction here is therefore **attribute-only** — `attr()` and base
indexing throughout, no S4 method dispatch — reading the serialized payload
directly rather than through a class definition that would misread it. The layers
are plain `dgCMatrix`, which the installed `Matrix` 1.4-1 handles natively.

Recommended for any successor: install SeuratObject ≥ 5, or keep the
attribute-only reader and test it against these recorded counts.

## 4. Intervention effects — measured, guide-level preserved

Pipeline: raw integer counts → **guide × donor pseudobulk** (the pre-aggregation
unit) → CPM → `log2(CPM+1)` → effect versus that object's own non-targeting
controls **within donor**.

```
CRISPRa   2,098 guide x donor groups     206 perturbed targets   412 effect rows
CRISPRi   2,137 guide x donor groups     206 perturbed targets   412 effect rows
```

Counts were asserted integral and non-negative before use. CRISPRa and CRISPRi
are kept **separate** throughout — different modalities, different feature
universes, never merged.

### Target engagement — the biological validation

| | rows | measured | median log2FC | % neg | % < −1 | % > +1 | donor r |
|---|---|---|---|---|---|---|---|
| CRISPRi | 412 | 410 | **−0.811** | 83 % | 44 % | 2 % | **+0.526** |
| CRISPRa | 412 | 410 | **+2.115** | 4 % | 1 % | 78 % | **+0.776** |

* **CRISPRi represses its target** — 83 % negative, 44 % beyond two-fold.
* **CRISPRa induces its target** — 78 % beyond two-fold up.
* **Donor reproducibility is real**: D1 and D2 are independent donors, and target
  effects correlate at r = +0.526 (CRISPRi) and +0.776 (CRISPRa).
* Of 205 CRISPRi targets present in both donors, **148 are negative in both**.

### The two modalities oppose each other

Across the **203 targets measured in both objects**:

```
CRISPRi median  −0.814        CRISPRa median  +2.155
opposite sign (i<0 and a>0)   177 / 203
magnitude correlation          r = +0.096
```

The sign separation is the meaningful result. The near-zero *magnitude*
correlation is expected rather than disappointing, and I want to be explicit
because a naive prior says it should be negative: knockdown magnitude is bounded
by how highly expressed a gene already is, activation magnitude by how silent it
is. The two are limited by opposite constraints, so their magnitudes need not
anti-correlate even when their directions reliably do.

## 5. Scope and limits

* This is **target engagement** — the response of the perturbed gene itself. The
  full transcriptome-wide effect matrix exists as guide × donor `log2(CPM+1)` on
  disk and is referenced content-addressed below; downstream differential testing
  is not done here.
* No multiple-testing correction, no significance calls, no ranking.
* Effects are within-donor versus each object's own NT controls. No cross-study,
  cross-dose or cross-timepoint merging.
* GSE301119 is **primary human macrophage**, an auxiliary myeloid system — not
  microglia and not brain tissue.
* The remaining seven studies are physically authenticated but not yet
  ETL-qualified.

## 6. Heavyweight artifacts — referenced, not committed

```
CRISPRi_guide_donor_logcpm.rds   44,098,976 B
CRISPRa_guide_donor_logcpm.rds   32,763,211 B
  D:/jepa_perturb_outputs_20260923/gse301119/
source objects (unchanged, authenticated):
  GSE301119_CRISPRi_seurat5.rds  406,836,813 B
  GSE301119_CRISPRa_seurat5.rds  345,798,341 B
```

Committed here: the two scripts, the physical-authentication receipts, the
guide × donor metadata and the target-engagement tables.

```
JEPA_TRAINING=OFF · THERAPEUTIC_RANKING=OFF · PROTECTED_FULL104_OUTCOMES=UNOPENED
HISTORICAL_IN_SILICO_PERTURBATIONS != MEASURED_INTERVENTION_EFFECTS
```
