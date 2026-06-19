# Existing Graph-JEPA environment package audit v1

This audit script is read-only: no package installs, model training, benchmarks, evidence-level changes, or external validation are run by the script.

## Existing environments audited

| env_name | python_version | requested packages available | path |
|---|---:|---:|---|
| base_current | 3.9.7 | 8/22 | C:\Users\dushy\anaconda3 |
| sea-ad-jepa | 3.11.15 | 14/22 | C:\Users\dushy\anaconda3\envs\sea-ad-jepa |
| sea-ad-jepa-v3 | 3.11.15 | 22/22 | C:\Users\dushy\anaconda3\envs\sea-ad-jepa-v3 |

## V2 training environment

`sea-ad-jepa` is treated as the v2 training/runtime environment because prior project commands used `conda run -n sea-ad-jepa ...`.

## Focus package availability

| env_name | package | available | version | notes |
|---|---|---:|---|---|
| base_current | torch | False |  | ModuleNotFoundError: No module named 'torch' |
| base_current | torch_geometric | False |  | ModuleNotFoundError: No module named 'torch_geometric' |
| base_current | scanpy | False |  | ModuleNotFoundError: No module named 'scanpy' |
| base_current | anndata | False |  | ModuleNotFoundError: No module named 'anndata' |
| base_current | umap | False |  | ModuleNotFoundError: No module named 'umap' |
| base_current | phate | False |  | ModuleNotFoundError: No module named 'phate' |
| base_current | dowhy | False |  | ModuleNotFoundError: No module named 'dowhy' |
| base_current | econml | False |  | ModuleNotFoundError: No module named 'econml' |
| sea-ad-jepa | torch | True | 2.7.0+cu128 | torch_cuda=12.8; gpu=NVIDIA GeForce RTX 3080 Laptop GPU |
| sea-ad-jepa | torch_geometric | True | 2.7.0 |  |
| sea-ad-jepa | scanpy | True | 1.11.5 |  |
| sea-ad-jepa | anndata | True | 0.12.16 |  |
| sea-ad-jepa | umap | True | 0.5.6 |  |
| sea-ad-jepa | phate | False |  | ModuleNotFoundError: No module named 'phate' |
| sea-ad-jepa | dowhy | False |  | ModuleNotFoundError: No module named 'dowhy' |
| sea-ad-jepa | econml | False |  | ModuleNotFoundError: No module named 'econml' |
| sea-ad-jepa-v3 | torch | True | 2.7.0+cu128 | torch_cuda=12.8; gpu=NVIDIA GeForce RTX 3080 Laptop GPU |
| sea-ad-jepa-v3 | torch_geometric | True | 2.7.0 |  |
| sea-ad-jepa-v3 | scanpy | True | 1.11.5 |  |
| sea-ad-jepa-v3 | anndata | True | 0.12.16 |  |
| sea-ad-jepa-v3 | umap | True | 0.5.6 |  |
| sea-ad-jepa-v3 | phate | True | 2.0.0 |  |
| sea-ad-jepa-v3 | dowhy | True | 0.14 |  |
| sea-ad-jepa-v3 | econml | True | 0.16.0 |  |

## `sea-ad-jepa` key checks

- torch available: yes
- torch_geometric available: yes
- scanpy available: yes
- anndata available: yes
- lightweight `sea_ad_jepa` import available: yes
- lightweight `sea_ad_jepa.graph_jepa` import available: yes

## Missing packages from `sea-ad-jepa`

openTSNE, phate, pydiffmap, scvi, xgboost, lightgbm, dowhy, econml

## Recommendation

Recommended strategy: use `sea-ad-jepa-v3` for v3 evaluation/runtime.

Rationale: `sea-ad-jepa-v3` now imports the cloned v2 neural stack, torch/PyG with CUDA, project runtime modules, and the requested optional v3 baseline/causal packages.

Stage 23 availability checks using the current/base interpreter should not be treated as the true project runtime if they did not use `conda run -n sea-ad-jepa`.

## Note on `sea-ad-jepa-v3` presence

`sea-ad-jepa-v3` is present and currently passes the requested v3 runtime import checks. It should be treated as the selected v3 runtime, not as the historical v2 runtime.
