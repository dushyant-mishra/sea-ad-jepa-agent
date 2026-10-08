# Stage76 F10 - perturbation readiness audit

F10 audits whether the frozen Stage75/76 regulatory evidence can be represented
by the current frozen JEPA feature space and encoder. It does not run
perturbation simulations, retrain JEPA, fine-tune JEPA, or infer biology.

The configured encoder candidate is:

`results/models/microglia_pvm_jepa_ema_var_expanded_balanced_e40/gene_jepa_epoch_030.pt`

The feature order is read from:

`data/processed/sea_ad_mtg_microglia_pvm_all_hvg3k_expanded_modules.h5ad`

## Runtime

On Windows, the torch-capable runtime is:

`C:\Users\dushy\anaconda3\envs\sea-ad-jepa-v3\python.exe`

Run the audit from PowerShell with the checked runner:

```powershell
cd "D:\Jepa project"
.\scripts\stage76_run_perturbation_readiness.ps1
```

The runner validates `torch`, `h5py`, `numpy`, `pandas`, and `yaml` inside `sea-ad-jepa-v3` before launching the audit. The direct command is:

```powershell
conda run -n sea-ad-jepa-v3 python scripts/stage76_audit_perturbation_readiness.py --config configs/stage75f_out_of_core_v1.yaml --project-dir "D:\Jepa project"
```

The WSL runner is still available only when `PYTHON_BIN` points to a WSL runtime that has the required packages. It now checks those packages before running:

```bash
cd "/mnt/d/Jepa project"
PYTHON_BIN=python3 bash scripts/stage76_run_perturbation_readiness_wsl.sh
echo "EXIT_CODE=$?"
```

## F10B provenance and reproduction checks

The audit records:

- checkpoint, model-definition, preprocessing-source, H5AD, feature-order, and baseline-reference hashes
- the training input contract from `scripts/train_jepa_snrna.py`
- the embedding extraction contract from `scripts/embed_jepa_snrna.py`
- matrix source as `adata.X` / H5AD `X`, with no additional normalization, log1p, scaling, clipping, or imputation in those scripts
- sparse input conversion to dense `float32` before model input
- inference through `GeneJEPA.encode`, which uses the context encoder with L2 normalization
- model eval/no-grad inference with no stochastic masks or augmentations
- same-runtime repeated inference metrics on a bounded exact cell-ID subset
- archived baseline comparison on exact matched cells and `jepa_*` embedding columns
- a reviewed project-level deterministic inference tolerance for the current frozen JEPA inference pathway

The report separates:

- `global_readiness_pass`
- `tier_a_mvp_readiness_pass`
- `per_regulator_readiness_status`

Tier A MVP readiness does not require F9 desired directionality to be resolved;
F11 must preserve both up and down simulation scenarios for unresolved TFs.

## Approved reproduction tolerance

The approved deterministic inference-reproduction tolerance is:

```yaml
baseline_reproduction_tolerance:
  max_abs_diff: 1.0e-6
  min_cosine_similarity: 0.999999
```

This is a numerical inference-reproduction tolerance for the current frozen JEPA
inference pathway. It is intended to detect checkpoint, preprocessing,
feature-order, encoder, or inference-contract mismatches. It is not a biological
effect-size threshold and must not be interpreted as one.

The tolerance was selected after exact same-runtime repeated inference on the
bounded matched-cell subset:

- `max_abs_diff=0.0`
- `mean_abs_diff=0.0`
- `min_cosine=1.0`

Formal archived-baseline reproduction passes only when checkpoint loading,
preprocessing provenance, feature-order verification, archived-reference
provenance, and the approved numerical tolerance all pass.

## Outputs

- `results/tables/stage76_jepa_feature_coverage_v1.csv`
- `results/tables/stage76_perturbation_graph_edge_coverage_v1.csv`
- `results/tables/stage76_regulator_readiness_v1.csv`
- `results/tables/stage76_jepa_baseline_reproduction_v1.csv`
- `results/reports/stage76_perturbation_readiness_v1.json`

F10B can report `tier_a_mvp_ready` while keeping `global_readiness_pass=false`
when Tier B regulators are outside the JEPA feature space or when the archived
global readiness is held back by Tier B feature gaps. Continuous
reproduction metrics are reported and formal baseline reproduction uses the
approved project-level deterministic inference tolerance.

This is a readiness gate only. It makes no validated regulation, validated-GRN,
causal, therapeutic, or simulated-response claim.
