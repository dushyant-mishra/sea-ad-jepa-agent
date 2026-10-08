#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$(cd "${SCRIPT_DIR}/.." && pwd)}"
CONFIG="${CONFIG:-configs/stage75f_out_of_core_v1.yaml}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
cd "${PROJECT_DIR}"
mkdir -p results/visualization results/stage75e_container
check_runtime() {
  "${PYTHON_BIN}" - <<'PY'
import importlib.util
import sys
mods = ["pandas", "yaml"]
missing = [m for m in mods if importlib.util.find_spec(m) is None]
if missing:
    raise SystemExit(1)
print(f"python={sys.executable}", flush=True)
PY
}
if ! check_runtime; then
  WINDOWS_PYTHON="/mnt/c/Users/dushy/anaconda3/envs/sea-ad-jepa-v3/python.exe"
  if [[ -x "${WINDOWS_PYTHON}" ]]; then
    PYTHON_BIN="${WINDOWS_PYTHON}"
    check_runtime
  else
    echo "Stage77 F11V runtime is missing packages: pandas, yaml" >&2
    exit 1
  fi
fi
PROJECT_ARG="${PROJECT_DIR}"
CONFIG_ARG="${CONFIG}"
if [[ "${PYTHON_BIN}" == *.exe ]]; then
  PROJECT_ARG="$(wslpath -w "${PROJECT_DIR}")"
  if [[ "${CONFIG}" == /mnt/* ]]; then
    CONFIG_ARG="$(wslpath -w "${CONFIG}")"
  fi
fi
"${PYTHON_BIN}" -u scripts/stage77_build_perturbation_graph_visualization.py --config "${CONFIG_ARG}" --project-dir "${PROJECT_ARG}" 2>&1 | tee results/stage75e_container/stage77_perturbation_graph_visualization.log