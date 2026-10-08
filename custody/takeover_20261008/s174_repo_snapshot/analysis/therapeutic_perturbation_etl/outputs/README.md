# Perturbation ETL data outputs — 2026-09-24

Result data, committed so it can be used directly rather than regenerated. Every
file here was produced by a committed producer in `../scripts/`; nothing was made
by hand or in a scratchpad.

## `gse178317/` — recovered from raw SRA reads

This is the expensive data. The guide-to-cell assignment is absent from the
processed GEO deposit and regenerating it requires streaming 221,434,278 spots
from SRA, about 47 minutes. It is committed in full for that reason.

| file | bytes | sha256 (16) | what it is |
|---|---|---|---|
| `gse178317_cell_guide_umi_counts_v2.npz` | 3,121,266 | `170a16797d681124` | 58,302 cells x 81 guides deduplicated UMI matrix, plus cell ids, lane labels, guide names and guide-to-target map. The primary artifact: any calling rule can be re-evaluated from it in seconds. |
| `gse178317_cell_guide_assignments_v2.csv.gz` | 227,864 | `87d032b6a4b84367` | 11,775 assigned cells: cell id, lane, barcode, sgRNA, target gene, NTC flag, guide UMI, cell total, fraction, robust z. From the lane-support-gated call. |
| `gse178317_target_engagement_v2.csv` | 2,573 | `c6d6f0013d791147` | Per target: cells, lanes, engagement log2FC, technical well spread. `biological_uncertainty_estimable` is FALSE throughout; see below. |
| `gse178317_top_effects_v2.csv.gz` | 22,119 | `b55bd4b22c51fcf1` | Top 25 up and down genes per target. |
| `gse178317_vs_crisprbrain_engagement_v1.csv` | 2,231 | `fff45935c994d3fb` | Our engagement beside the depositors' published value, per target. |

**Read these with the scope in mind.** The four 10x lanes are capture wells from
one pool of day-eight iTF-Microglia, not independent differentiations, donors or
cell lines. Spread across them is technical. There is **no biological error bar**
on any target here and none can be produced from this experiment as deposited.
The assignment thresholds were declared after an inspected 0.27% smoke run, so
the scope is DEVELOPMENT, not prospective confirmation. See
`../GSE178317_RECOVERY_QUALIFIED_20260924.md`.

## `crisprbrain/` — acquired from the CRISPRbrain data commons

Per perturbed target, a differential expression profile across the
transcriptome: columns `Gene`, `Log2CPM`, `Log2FC`, `P Value`, `FDR`, `name`
(the perturbed target), `P Value (Signed -Log10)`.

The five **microglia** screens are committed, gzipped, since they are the ones
this project works in:

| file | bytes | sha256 (16) | targets |
|---|---|---|---|
| `iTF_Microglia-Day-8-CROP-seq-CRISPRi.csv.gz` | 13,586,532 | `201e8fb28a63dfb9` | 39 |
| `iTF-Microglia-CROP-seq-CRISPRi.csv.gz` | 20,358,929 | `58c48fa4400d469a` | 31 |
| `iPSC-Microglia-CROP-seq-CRISPRi.csv.gz` | 16,133,002 | `818ae3c383811c94` | 31 |
| `iTF-Microglia-CITE-seq-CRISPRi.csv.gz` | 187,443 | `dcc204e858264e1e` | 31 |
| `iPSC-Microglia-CITE-seq-CRISPRi.csv.gz` | 188,965 | `d032364a457e1406` | 31 |

The four **neuron and iPSC** screens are NOT committed. They total 347 MB raw
and are fetched in minutes by the committed producer, so carrying them in git
history is not worth the cost. Digests of exactly what was acquired:

```
Glutamatergic_Neuron-RNA-Seq-CRISPRa-2020.csv   86,055,877  bae3dee340bc24038f1e595c04a1eab98e35718f7c984622267110af9200e76f
Glutamatergic_Neuron-RNA-Seq-CRISPRi-2019.csv   49,409,869  976adc4bc08728f8c42b7f1624ed0093dede449e93cfe605cb532229e8e02dd0
Glutamatergic_Neuron-RNA-Seq-CRISPRi-2020.csv  163,362,857  cc50a1b837ed463cfd21e2b013f7b6dc82d07f57961b0218fde06edb6b8515fc
iPSC-RNA-Seq-CRISPRi-2019.csv                   48,619,012  178dda2fbfcd00514003a8f702d4f5d7fe92fa89cb5e7afc249e590492e10955
```

To regenerate all nine plus the catalogue and the FULL104 overlap receipt:

```
pip install crisprbrain
python ../scripts/acquire_crisprbrain_screens_v1.py \
  --out-dir <dir> \
  --full104-registry <path to stage81a2r_foundation_molecular_address_registry_candidate.csv>
```

**CRISPRbrain tables are reference data, not independent replication.** The
Day-8 screen is the depositors' own analysis of the same experiment our
GSE178317 recovery reads. Agreement between them tests our pipeline; it does not
show the biology reproducing.

## Reading the two together

`gse178317_vs_crisprbrain_engagement_v1.csv` joins our per-target engagement to
the published value. Read it together with
`../evidence/gse178317_recovery/gse178317_vs_crisprbrain_support_qualified_v3.csv`,
which carries the authoritative figures.

Two of the 35 comparable targets lack matched-well support and are excluded by
the authenticated lane-support receipt: AARS (42 cells, one paired well) and
LSM6 (33 cells, one paired well). Over the **33 support-qualified** targets all
33 agree in direction, Spearman 0.7473, Pearson 0.6398, magnitude ratio 2.932x.
The larger magnitudes are the expected consequence of a stricter guide caller
carrying fewer misassigned cells to dilute each estimate.

The superseded 35-target figures (Spearman 0.720, 3.07x) survive only in the v1
and v2 receipts as historical evidence and must not be inherited.

```
TRAINING=OFF · AUDIT_B_N1=UNOPENED · PROTECTED_OUTCOMES=UNOPENED · THERAPEUTIC_RANKING=OFF
```
