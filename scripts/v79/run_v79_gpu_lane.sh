#!/usr/bin/env bash
# V79 GPU lane (run inside WSL): recovery fits on the CUDA device, at most SLOTS fit processes at once.
# Small models leave a GPU idle between tiny sequential sampler steps, so several fits share it. Each process
# preallocates a fixed share of GPU memory with JAX's default (BFC) allocator: the JAX docs call the on-demand
# 'platform' allocator very slow and recommend a per-process XLA_PYTHON_CLIENT_MEM_FRACTION for multi-process use
# (self-audit 44). Progress is streamed so a hang shows. Jobs file: one "likelihood fit" pair per line.
# Usage: run_v79_gpu_lane.sh <jobs file> <slots> <snapshot dir> <results dir> [mem_fraction]
set -u
JOBS=$1; SLOTS=$2; SNAP=$3; R=$4; FRAC=${5:-0.18}
PY=/home/dushyant_mishra/miniconda3/envs/v79-bayes-gpu/bin/python
export XLA_PYTHON_CLIENT_PREALLOCATE=true XLA_PYTHON_CLIENT_MEM_FRACTION=$FRAC V79_PROGRESS=1
running() { pgrep -fc "^$PY -u .*run_v79_recovery" || true; }
cd /tmp
while read -r lik fit; do
  [ -z "${lik:-}" ] && continue
  while [ "$(running)" -ge "$SLOTS" ]; do sleep 30; done
  (
    echo "$lik $fit gpu start $(date -u +%H:%M:%SZ) alloc=bfc frac=$FRAC" >> "$R/progress.txt"
    timeout 43200 "$PY" -u "$SNAP/scripts/v79/run_v79_recovery.py" --likelihood "$lik" --fits "$fit" --genes 20 \
      --out "$R/part_${lik}_${fit}.json" > "$R/log_${lik}_${fit}.txt" 2>&1
    echo "$lik $fit gpu exit $? $(date -u +%H:%M:%SZ)" >> "$R/progress.txt"
  ) &
  sleep 120
done < "$JOBS"
wait
echo "gpu lane done $(date -u +%H:%M:%SZ)" >> "$R/progress.txt"
