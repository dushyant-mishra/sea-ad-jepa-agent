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
mods = ["h5py", "numpy", "pandas", "yaml"]
missing = [m for m in mods if importlib.util.find_spec(m) is None]
if missing:
    raise SystemExit("Stage77 runtime is missing packages: " + ", ".join(missing))
print(f"python={sys.executable}", flush=True)
PY
"${PYTHON_BIN}" -u scripts/stage77_simulate_tier_a_perturbations.py --config "${CONFIG}" --project-dir "${PROJECT_DIR}" 2>&1 | tee results/stage75e_container/stage77_tier_a_perturbation_mvp.log
