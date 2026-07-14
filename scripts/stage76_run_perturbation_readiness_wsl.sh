#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$(cd "${SCRIPT_DIR}/.." && pwd)}"
CONFIG="${CONFIG:-configs/stage75f_out_of_core_v1.yaml}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

cd "${PROJECT_DIR}"
mkdir -p results/tables results/reports results/stage75e_container

"${PYTHON_BIN}" - <<'PY'
import importlib.util
import sys
mods = ["torch", "h5py", "numpy", "pandas", "yaml"]
missing = [m for m in mods if importlib.util.find_spec(m) is None]
if missing:
    raise SystemExit(
        "Stage76 readiness runtime is missing packages: "
        + ", ".join(missing)
        + ". Use scripts/stage76_run_perturbation_readiness.ps1 with conda env sea-ad-jepa-v3, or set PYTHON_BIN to a WSL Python that has these packages."
    )
import torch
print(f"python={sys.executable}", flush=True)
print(f"torch={torch.__version__}", flush=True)
print(f"cuda_available={torch.cuda.is_available()}", flush=True)
PY

"${PYTHON_BIN}" -u   scripts/stage76_audit_perturbation_readiness.py   --config "${CONFIG}"   --project-dir "${PROJECT_DIR}"   2>&1 | tee     results/stage75e_container/stage76_perturbation_readiness.log
