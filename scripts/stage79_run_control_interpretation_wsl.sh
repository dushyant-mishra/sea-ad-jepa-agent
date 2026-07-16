#!/usr/bin/env bash
set -euo pipefail
PROJECT_DIR="${PROJECT_DIR:-/mnt/d/Jepa project}"
POWERSHELL_EXE="${POWERSHELL_EXE:-powershell.exe}"
cd "${PROJECT_DIR}"
"${POWERSHELL_EXE}" -NoProfile -ExecutionPolicy Bypass -Command 'Set-Location "D:\Jepa project"; conda run -n sea-ad-jepa-v3 python scripts/stage79_interpret_graph_controls.py --config configs/stage75f_out_of_core_v1.yaml --project-dir .; exit $LASTEXITCODE'
