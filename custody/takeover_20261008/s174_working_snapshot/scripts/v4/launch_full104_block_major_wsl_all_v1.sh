#!/usr/bin/env bash
set -euo pipefail

cd "/mnt/d/Jepa project"

PYTHON="/home/dushyant_mishra/miniconda3/envs/jepa-full104/bin/python"
BASE="outputs/full104_v014_20260826/03_phase2_state_derivation_v1"
OUT="$BASE/shared_refit_null_sensitivity_results_v4_block_major_wsl"

if [[ -e "$OUT" ]]; then
  echo "STOP: fresh ALL output already exists: $OUT" >&2
  exit 2
fi

exec "$PYTHON" scripts/v4/run_full104_refit_null_block_major_v1.py \
  --freeze "$BASE/shared_refit_null_sensitivity_freeze_v1" \
  --matrix "$BASE/feature_matrix_level4" \
  --analytic "$BASE/shared_analytic_level4_v1" \
  --plan-authority-dir "$BASE/shared_refit_null_sensitivity_results_v2_lossless_scoped/cap_ALL" \
  --gate "$BASE/block_major_wsl_implementation_gate_v4" \
  --out "$OUT" \
  --batch-size 32 \
  --checkpoint-every-strata 1400 \
  --device cuda
