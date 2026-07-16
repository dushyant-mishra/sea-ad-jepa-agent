#!/usr/bin/env bash
set -euo pipefail
PROJECT_DIR="${PROJECT_DIR:-/mnt/d/Jepa project}"
POWERSHELL_EXE="${POWERSHELL_EXE:-powershell.exe}"
cd "${PROJECT_DIR}"
"${POWERSHELL_EXE}" -NoProfile -ExecutionPolicy Bypass -File "D:\Jepa project\scripts\stage79_run_graph_controls.ps1"
