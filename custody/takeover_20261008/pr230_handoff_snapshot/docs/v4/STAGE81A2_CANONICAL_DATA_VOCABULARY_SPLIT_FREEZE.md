# Stage81A2 Canonical Data, Vocabulary, and Split Freeze

Stage81A2 freezes the data contract for the pathology-blind v4 RNA foundation.
It does not concatenate matrices, create training shards, train a model, or
start Stage81B.

## Foundation contract

The direct foundation pool is limited to compatible brain RNA counts:

- eleven broad SEA-AD postmortem brain RNA objects using `layers/UMIs`;
- 24 HVS living surgical-cortex partitions using `raw/X`;
- exact final-annotation NPH cortical cells using the source `counts` assay,
  with only the 25 pathology-negative donors in the initial foundation.

The SEA-AD immune object remains a later Microglia/PVM specialization source.
The 19 amyloid-positive and eight amyloid-plus-tau NPH donors are separate
continuation cohorts. Siletti is a whole-study external holdout. GSE243292 and
GSE146639 remain validation sources. Spatial panels, ATAC peaks, miRNA,
olfactory, CSF, blood, perturbation, documentation, development, and sealed
data cannot shape the cortical RNA vocabulary.

HVS retains 78 exact source donor identifiers. No authoritative alias table
explains the publication-level count of 75, so Stage81A2 records the discrepancy
instead of inventing three merges.

## NPH identity audit

`stage81a2_audit_nph_freeze.R` reads the seven source and seven final annotation
QS objects. The source-defined annotation namespaces are exact:

- cell: `human_NPH_` plus the source matrix column name;
- donor: `human_` plus the source `NPH_*` donor identifier.

The compact audit accounts for 892,828 retained final-annotation cells and
64,831 cells with no exact required final annotation, totaling all 957,659
source cells. The latter are excluded as `missing_required_annotation`; they
are not described as QC failures without source evidence. The detailed ledger
and source-feature/statistic caches stay under `data/processed/v4/stage81a2/`
and are not committed.

## Gene and matrix contract

The canonical key is an unversioned Ensembl gene ID plus its exact
source-provided symbol. No fuzzy symbol mapping is allowed. NPH symbols are
accepted only when they resolve to one unique exact Ensembl/symbol pair supplied
by SEA-AD or HVS. Source and partition feature universes are hashed. Measurement
masks distinguish a measured zero from a feature absent from that source.

Vocabulary statistics use only training donors. Sparse matrices are sampled
deterministically with a bounded number of cells per donor, broad class, and
source. Statistics are aggregated by donor and study family before scoring, so
SEA-AD cell volume cannot dominate HVS or NPH. Exactly 4,096 genes are frozen
only if 4,096 genes satisfy exact identity, cross-family measurement, donor
coverage, and detection gates.

The future Stage81B transformation is frozen as library-size normalization to
10,000 followed by `log1p`, with an explicit measurement mask. Stage81A2 does
not implement the loader.

## Pathology firewall

Pathology remains in a separately hashed sidecar. It is used only to construct
the already approved NPH foundation and continuation rosters. The vocabulary
function accepts no pathology input, and foundation vocabulary outputs contain
no pathology field. SEA-AD pathology columns are never read by this stage.

## Commands

First create the local NPH exact audit caches in the established WSL R
environment after an audit/proposal has emitted the split registry:

```bash
cd "/mnt/d/Jepa project"
/home/dushyant_mishra/miniconda3/envs/stage81a1d-r-audit/bin/Rscript \
  scripts/v4/stage81a2_audit_nph_freeze.R \
  data/processed/v4/stage81a1d/sealed/nph52_annotations/annotations \
  data/processed/v4/stage81a1d/sealed/nph52_organized/organized_data/Human/brain/snRNA/NPH \
  data/processed/v4/stage81a2/nph52_cell_disposition_detail.csv.gz \
  data/processed/v4/stage81a2/nph52_cell_disposition_summary.csv \
  data/processed/v4/stage81a2/nph52_source_feature_registry.csv.gz \
  results/v4/stage81a2_split_registry.csv \
  data/processed/v4/stage81a2/nph52_donor_balanced_gene_stats.csv.gz
```

Then run each mode in the validated Windows environment:

```powershell
conda run -n sea-ad-jepa-v3 python scripts/v4/stage81a2_freeze_canonical_contract.py `
  --mode audit --config configs/v4/stage81a2_canonical_freeze.yaml `
  --output-dir results/v4 --project-dir . --seed 8102

conda run -n sea-ad-jepa-v3 python scripts/v4/stage81a2_freeze_canonical_contract.py `
  --mode propose --config configs/v4/stage81a2_canonical_freeze.yaml `
  --output-dir results/v4 --project-dir . --seed 8102

conda run -n sea-ad-jepa-v3 python scripts/v4/stage81a2_freeze_canonical_contract.py `
  --mode freeze --config configs/v4/stage81a2_canonical_freeze.yaml `
  --output-dir results/v4 --project-dir . --seed 8102
```

Freeze mode exits nonzero and refuses readiness whenever a required identity,
feature, matrix, split, vocabulary, or provenance gate fails. Cloud permission
is recorded separately and unresolved permission blocks future cloud bundles,
not the local scientific freeze.
