# v3 status, scorecard, and dataset registry lock v1

## Summary

This commit locks the active Graph-JEPA v3 control layer before Stage 27 model training. It documents the official internal benchmark, scorecard evidence labels, dataset-role leakage rules, and the merged GEO/CELLxGENE role registry.

## Files created or updated

- `docs/ACTIVE_V3_STATUS.md`
- `docs/V3_SCORECARD.md`
- `docs/DATASET_REGISTRY.md`
- `README.md`
- `docs/current_status.md`
- `results/tables/v3_scorecard_status_v1.csv`
- `results/tables/v3_dataset_role_registry_v1.csv`
- `results/reports/v3_status_scorecard_dataset_registry_lock_v1.md`

## Boundaries

- No v3 training was performed.
- No graph neural model was run.
- No external validation was performed.
- No expression matrix or H5AD payload was downloaded.
- No evidence level was changed.
- No manuscript conclusions were rewritten.

## Dataset-role leakage rules

If a dataset is used for training, pretraining, auxiliary supervision, architecture choice, threshold setting, candidate filtering, or model selection, it cannot later be called clean validation. Clean external holdout candidates remain untouched until architecture/training decisions are frozen.

Mouse datasets require ortholog mapping and are not human validation. Peripheral immune datasets are plausibility/auxiliary only and are not direct brain microglia validation. Already-used datasets are plausibility/context only.

## Next recommended commit

The next implementation commit should be Stage 27A/27B:

- Stage 27A: SEA-AD-only non-graph v3.
- Stage 27B: external-pretrained non-graph v3.

Both are training regimes inside one Graph-JEPA v3 framework.

