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

The SEA-AD MTG AnnData file is more than 30 GiB and should never be pushed to GitHub.

## Suggested First Commit

After initializing git:

```powershell
git init
git add README.md environment.yml requirements.txt .gitignore docs scripts
git commit -m "Initialize SEA-AD JEPA agent project"
```

## Suggested Repository Description

```text
JEPA-agent framework for Alzheimer disease gene-network discovery from SEA-AD single-nucleus transcriptomics and neuropathology data.
```

## Suggested GitHub Topics

```text
single-cell
scrna-seq
alzheimers-disease
jepa
gene-regulatory-networks
bioinformatics
neurodegeneration
multimodal-learning
```

## README Checks

Before publishing, confirm:

- The project goal is clear in the first screen.
- Data source links are included.
- Large data files are excluded by `.gitignore`.
- The setup commands work in a fresh conda environment.
- The current workflow can reproduce metadata target tables from public files.
- Any claims are framed as hypothesis generation unless experimentally validated.

