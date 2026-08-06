# Stage81A1D Living-Human Data Bridge

Stage81A1D acquires and audits processed living-human expression and regulatory
references before Stage81A2. It does not harmonize expression values, choose a
gene vocabulary or donor split, merge matrices, or train a model.

## Biological roles

- HVS surgical neocortex is a direct living-cortex foundation candidate pending
  exact feature and donor harmonization. Its epilepsy/tumor surgical context is
  retained and is not described as a healthy-volunteer cohort.
- The 52-donor NPH release is split only through exact source annotations. Its
  pathology fields are written to an ignored sealed sidecar that foundation
  selection must not load.
- CSF, PBMC, whole-blood, olfactory and miRNA studies remain tissue-specific
  adapter or validation candidates. They are not pooled with cortical cells.
- GSE146639 remains a postmortem microglia reference and is not redownloaded.
- Synapse candidates are audited file by file without accepting terms or
  printing credentials. Controlled optional data do not block open acquisition.

## Commands

Run in the `sea-ad-jepa-v3` environment:

```powershell
conda run -n sea-ad-jepa-v3 python scripts/v4/stage81a1d_acquire_living_human.py `
  --mode catalog --project-dir . --output-dir results/v4

conda run -n sea-ad-jepa-v3 python scripts/v4/stage81a1d_acquire_living_human.py `
  --mode acquire --resume --project-dir . --output-dir results/v4

conda run -n sea-ad-jepa-v3 python scripts/v4/stage81a1d_acquire_living_human.py `
  --mode audit --offline --project-dir . --output-dir results/v4
```

`--study HVS` or another study ID bounds acquisition to one study. Catalog mode
performs metadata requests only. Required downloads are written below
`data/external/v4/living_human/` through resumable `.part` files. The script
checks actual free space before transfers and applies no arbitrary stage cap.

## Claim boundaries

The outputs are acquisition and provenance evidence. Living surgical, NPH,
CSF, blood and olfactory measurements are biologically distinct. No pathology
label is foundation supervision, ATAC peaks are not RNA features, bulk samples
are not cells, and no source is a validated regulatory or causal model.
