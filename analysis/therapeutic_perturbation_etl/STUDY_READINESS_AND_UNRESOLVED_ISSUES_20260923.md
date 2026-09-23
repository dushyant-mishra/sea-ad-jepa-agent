# Study-by-study readiness and unresolved issues

Date: 2026-09-23
Branch: `analysis/perturbation-etl-gse301119-claude-20260923`

All 16 processed assets across 8 studies are **physically authenticated**
(`PASS_PERTURBATION_ETL_PHYSICAL_ATLAS_V1`, 0 mismatches). Physical authentication
is *not* ETL qualification, and the two are kept separate below.

---

## Status

| study | system | physical | ETL qualified | measured effects | blocker |
|---|---|---|---|---|---|
| **GSE301119** | primary human macrophage, CRISPRi + CRISPRa | ✅ | ✅ | ✅ target engagement, 2 objects | — |
| **GSE254205** | APOE4/4 iMG, fAβ ± GNE-317 | ✅ | ✅ *(bulk arm)* | ✅ 3 drug contrasts | other 3 assets not yet done |
| **GSE293118** | HMC3, noncoding CRISPRi | ✅ | identity ✅, matrix in progress | pending | 356M-entry MEX stream |
| GSE178317 | iPSC microglia CRISPRi/a | ✅ | ❌ | ❌ | lane-matched GEX↔sgRNA join |
| GSE311359 | iPSC microglia Perturb-seq | ✅ | ❌ | ❌ | per-sample matrix + perturbation metadata |
| GSE175721 | engineered microglia in organoids | ✅ | ❌ | ❌ | guide→cell assignment |
| GSE241858 | TREM2 R47H ± LPS/IFNγ | ✅ | ❌ | ❌ | bulk schema not yet built |
| GSE240609 | APOE3ch coculture | ✅ | ❌ | ❌ | bulk schema not yet built |

## Qualified: GSE301119

Feature blocker resolved — CRISPRa's 19,162 features are an **exact subset** of
CRISPRi's 36,601, so the 17,439 CRISPRi-only features are masked as unmeasured,
never zero-filled. Structural counts reproduce the historical object audit
exactly. Target engagement validates the pipeline: CRISPRi median log2FC −0.811,
CRISPRa +2.115, donors reproducing at r = +0.526 / +0.776, and 177 of 203 shared
targets opposing in sign.

**Unresolved:** two donors is not a donor distribution; effects are target
engagement rather than transcriptome-wide differential tests; this is macrophage,
not microglia.

## Qualified: GSE254205, bulk GNE-317 arm

```
NT rep1..3 | AB rep1..3 | AB_GNE rep1..3     9 samples, 58,395 Ensembl genes
genes detected anywhere 36,117   masked as unmeasured 22,278

AB_vs_NT        2,253 genes |log2FC| > 1
AB_GNE_vs_AB    3,840 genes |log2FC| > 1,  481 > 2     <- drug in amyloid context
AB_GNE_vs_NT    2,030 genes |log2FC| > 1
```

Replicates preserved before aggregation; each effect carries n and a
replicate-level SE. **No rescue or reversal claim is computed** — showing a
compound moves expression is not showing it restores a healthy state, and this
ETL deliberately stops before that inference.

**Unresolved:** only the treatment arm is done. The snRNA-seq `ad_raw.h5ad.gz`
(734 MB), the ATAC arm and the LD-sort arm are authenticated but unprocessed.
One cell model, one timepoint, three replicates — a thin basis for any transport
claim.

## In progress: GSE293118

Identity resolved and committed. The structure is more heterogeneous than the
registry suggested:

| target class | targets | guides |
|---|---|---|
| `gene` | 6 | 16 |
| `gene_symbol_unmatched` | 1 | 3 |
| `noncoding_variant` (rs IDs) | 73 | 218 |
| `noncoding_deletion` (`del1..3`) | 3 | 9 |
| `non_targeting_control` | 1 class | 23 |

Verified rather than assumed: the protospacer calls (GSM8876720) and the matrix
(GSM8876719) carry **different GSM accessions**, and all 83,564 called barcodes
are a subset of the 96,639 matrix barcodes with **zero orphans**.

**The honest scope limit.** Target engagement is definable for **6 targets only**
— BIN1, CLU, RAB1A, SNX1, SYVN1, TSPAN14. The 73 variants and 3 deletions have no
same-named measured feature, and `RPA1-SMYD4` is a read-through locus with no
single symbol. Assigning them a cis-target would be inventing information, so
engagement is recorded as *unavailable* with the reason attached. Their value is
transcriptome-wide response against non-targeting controls, which requires a
nominated cis-target before it can be read as regulatory-element effect.

Multiplicity is real: 64,148 cells carry one guide, 12,698 carry two, with a tail
to six or more. Single-perturbation effects use singly-assigned cells only and
the multiplet fraction is reported, not silently collapsed.

## Not started, with the specific blocker

* **GSE178317** — two assets, 16 archive members. Needs lane-matched
  gene-expression ↔ sgRNA-enrichment joins. Assignments must come from the
  authenticated records, never from filename inference.
* **GSE311359** — one asset, 21 members. Needs per-sample matrix resolution and
  perturbation metadata.
* **GSE175721** — organoid-engineered microglia; a `CRISPR_seq.fa.gz` guide
  library plus a 160 MB RAW archive. Guide→cell assignment unresolved.
* **GSE241858** — TREM2 R47H/+ ± LPS/IFNγ, two bulk count files. A cytokine
  stimulation design; needs its own bulk schema, and is genotype × context, not
  CRISPR.
* **GSE240609** — APOE3 Christchurch coculture, 440 KB RAW archive.

## Cross-cutting unresolved issues

1. **Feature namespaces differ across studies.** GSE301119 and GSE293118 use HGNC
   symbols; GSE254205 uses Ensembl IDs. Cross-study comparison needs an explicit,
   tested mapping with a documented collision policy — not a silent join.
2. **No cis-target authority for noncoding elements.** Blocks 76 of GSE293118's
   84 targets from contributing interpretable regulatory effects.
3. **Engagement is not penetrance.** 17 % of GSE301119 CRISPRi targets were not
   repressed at all. Any model conditioning on engagement risks leaking outcome;
   ignoring it models an intervention that did not happen.
4. **Replicate depth is thin.** Two donors (GSE301119), three replicates
   (GSE254205). Sufficient for effect estimation, weak for transport claims.
5. **Reader environment.** The installed Seurat is 4.1.1 / SeuratObject 4.1.0 and
   cannot correctly read the Seurat 5.4.0 `Assay5` objects — `dim()` returns empty
   rather than raising. Extraction is attribute-only for that reason. Installing
   SeuratObject ≥ 5 would remove the hazard.

```
JEPA_TRAINING=OFF · THERAPEUTIC_RANKING=OFF · PROTECTED_FULL104_OUTCOMES=UNOPENED
HISTORICAL_IN_SILICO_PERTURBATIONS != MEASURED_INTERVENTION_EFFECTS
```
