# GitHub Repository Checklist

Use this checklist before uploading the project to GitHub.

## Keep in the Repository

Commit these files:

```text
README.md
environment.yml
requirements.txt
.gitignore
docs/
scripts/
```

These describe the project and make the metadata/pilot workflow reproducible.

## Do Not Commit

Do not commit local datasets or generated outputs:

```text
data/raw/
data/processed/
results/
*.h5ad
*.h5
*.hdf5
*.zarr/
*.rds
```

The SEA-AD MTG AnnData file is very large and should never be pushed to GitHub.

## Suggested First Commit

After initializing git:

```powershell
git init
git add README.md environment.yml requirements.txt .gitignore docs scripts
git commit -m "Initialize SEA-AD JEPA agent project"
```

## Suggested Repository Description

```text
Graph-JEPA framework for SEA-AD Alzheimer microglia: pathology-grounded representation learning, donor-held-out validation, and counterfactual gene-network hypothesis generation.
```

## Suggested GitHub Topics

```text
alzheimer-disease
single-cell-rna-seq
jepa
graph-neural-network
causal-discovery
bioinformatics
pytorch
sea-ad
microglia
computational-biology
```

## README Checks

Before publishing, confirm:

- The project goal is clear in the first screen.
- The v1-to-v2 story is clear: flat-vector JEPA exposed failure modes, Graph-JEPA addresses gene topology.
- The Stage A/B/C training curriculum is explained.
- Current Stage C sweep results and limitations are included.
- Public schematics and result graphs are linked from `docs/figure_gallery.md`.
- Data source links are included.
- Large data files are excluded by `.gitignore`.
- The setup commands work in a fresh conda environment.
- The current workflow can reproduce metadata target tables from public files.
- Any claims are framed as hypothesis generation unless experimentally validated.
