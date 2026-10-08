#!/usr/bin/env bash
set -euo pipefail

cd "/mnt/d/Jepa project"
BASE="outputs/full104_v014_20260826/03_phase2_state_derivation_v1"
LOG="$BASE/ALL_BLOCK_MAJOR_WSL_V3.log"
PID_FILE="$BASE/ALL_BLOCK_MAJOR_WSL_V3.pid"

if [[ -e "$BASE/shared_refit_null_sensitivity_results_v3_block_major_wsl" ]]; then
  echo "STOP: fresh ALL output already exists" >&2
  exit 2
fi

nohup bash scripts/v4/launch_full104_block_major_wsl_all_v1.sh >"$LOG" 2>&1 &
pid=$!
printf '%s\n' "$pid" >"$PID_FILE"
echo "PID=$pid"
echo "LOG=$LOG"
