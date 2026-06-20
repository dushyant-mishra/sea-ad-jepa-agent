# v3 CELLxGENE relevant dataset search v1

## 1. Executive summary

CELLxGENE Census metadata search was not completed: cellxgene-census package missing: No module named 'cellxgene_census'
No v3 training, graph neural model, external validation, model selection, or evidence-level change was run.

## 2. Search method

The script attempted to import/open `cellxgene-census`. Because this failed, no CELLxGENE metadata query was performed.

## 3. Best human AD/dementia brain candidates

Unavailable until the Census metadata search succeeds.

## 4. Best human normal brain/microglia pretraining candidates

Unavailable until the Census metadata search succeeds.

## 5. Mouse auxiliary candidates

Unavailable until the Census metadata search succeeds.

## 6. Peripheral immune candidates

Unavailable until the Census metadata search succeeds.

## 7. Datasets to avoid or review

All CELLxGENE datasets should remain unreviewed until metadata discovery is rerun successfully.

## 8. Recommended downloads

Do not download H5AD/expression matrices yet. First restore Census metadata access and rerun this audit.

## 9. Recommended integration plan

Repeat Stage 26C metadata search, then freeze dataset roles before any download/integration.

## 10. Role-freezing rules

No dataset may be used for model selection. Clean holdout candidates must remain untouched by training unless explicitly reclassified.