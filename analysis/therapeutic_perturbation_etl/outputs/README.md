# Perturbation ETL data outputs — 2026-09-24

Result data, committed so it can be used directly rather than regenerated. Every
file here was produced by a committed producer in `../scripts/`; nothing was made
by hand or in a scratchpad.

## `gse178317/` — recovered from raw SRA reads

This is the expensive data. The guide-to-cell assignment is absent from the
processed GEO deposit and regenerating it requires streaming 221,434,278 spots
from SRA, about 47 minutes. It is committed in full for that reason.

| file | bytes | sha256 (16/full where available) | what it is |
|---|---|---|---|
| `gse178317_cell_guide_umi_counts_v2.npz` | 3,121,266 | `170a16797d681124` / `170a16797d681124a9083eb4170794b0f377b8a64ec3603e63b3435567fe3b4c` | 58,302 cells x 81 guides deduplicated UMI matrix, plus cell ids, lane labels, guide names and guide-to-target map. The primary artifact: any calling rule can be re-evaluated from it in seconds. |
| `gse178317_cell_guide_assignments_v2.csv.gz` | 227,864 | `87d032b6a4b84367` | 11,775 assigned cells: cell id, lane, barcode, sgRNA, target gene, NTC flag, guide UMI, cell total, fraction, robust z. From the lane-support-gated call. |
| `gse178317_target_engagement_v2.csv` | 2,573 | `c6d6f0013d791147` | Per target: cells, lanes, engagement log2FC, technical well spread. `biological_uncertainty_estimable` is FALSE throughout; see below. |
| `gse178317_top_effects_v2.csv.gz` | 22,119 | `b55bd4b22c51fcf1` | Top 25 up and down genes per target. |
| `gse178317_vs_crisprbrain_engagement_v1.csv` | 2,231 | `fff45935c994d3fb` / `fff45935c994d3fbce3293a9ddc53bce3acaa9507040e1ceb79ef19e8418a7e0` | Historical same-experiment reference comparison for 35 comparable targets. Two targets in this file, AARS and LSM6, fail the later matched-well support gate; do not present its correlations as the support-qualified result. |
| `gse178317_vs_crisprbrain_engagement_v2_matched_well_support.csv` | 4,100 | `e66a09a8729570d7f82cba40dae0bb01be5bb35ccdbca83f529ac2daf127e55d` | Same-experiment reference comparison filtered to the 33 comparable targets that pass the authenticated matched-well support gate. |

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
|---|---:|---|---:|
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
the published value for the 35 historically comparable targets. All 35 agree in
direction and the historical Spearman correlation is 0.720, but that file
includes AARS and LSM6, which do not pass the authenticated matched-well support
gate. The support-qualified comparison is therefore the 33-target V2 file:
33/33 same-direction agreement, Pearson r 0.6398, Spearman rho 0.7473, median
ours -0.7146, median reference -0.2437, and ratio of medians 2.932.

The magnitude difference is a diagnostic observation, not a demonstrated causal
consequence of the stricter guide caller. Testing that mechanism requires a
separate caller-sensitivity analysis on the same count matrix with all other
processing fixed.

```
TRAINING=OFF · AUDIT_B_N1=UNOPENED · PROTECTED_OUTCOMES=UNOPENED · THERAPEUTIC_RANKING=OFF
```
