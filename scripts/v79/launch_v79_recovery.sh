#!/usr/bin/env bash
# Run the recovery fits (6 scenarios per likelihood) as independent processes, N at a time, each limited to
# 4 host devices (one per chain) and single-threaded XLA kernels so processes do not oversubscribe the CPU.
# Usage: launch_v79_recovery.sh <python> <out_dir> [genes] [warmup] [draws] [likelihoods] [concurrent]
#   likelihoods: space-separated, default "gaussian bernoulli"; concurrent: default 4
set -u
PY="$1"; OUT="$2"; G="${3:-20}"; W="${4:-1000}"; D="${5:-1000}"; LIKS="${6:-gaussian bernoulli}"; N="${7:-4}"
HERE="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$OUT"
export XLA_FLAGS="--xla_force_host_platform_device_count=4 --xla_cpu_multi_thread_eigen=false"
jobs_running() { jobs -rp | wc -l; }
for lik in $LIKS; do
  for fit in S1_present S0_class_absent S2_class_permuted S3_donor_only S4_operator_only S5_labels_removed; do
    while [ "$(jobs_running)" -ge "$N" ]; do sleep 5; done
    ( timeout 14400 "$PY" "$HERE/run_v79_recovery.py" --likelihood "$lik" --fits "$fit" --genes "$G" \
        --warmup "$W" --draws "$D" --out "$OUT/part_${lik}_${fit}.json" > "$OUT/log_${lik}_${fit}.txt" 2>&1
      echo "$lik $fit exit $? $(date -u +%H:%M:%SZ)" >> "$OUT/progress.txt" ) &
  done
done
wait
for lik in $LIKS; do
  "$PY" "$HERE/run_v79_recovery.py" --combine "$OUT/V79_SIMULATION_RECOVERY_${lik}.json" "$OUT"/part_${lik}_*.json
done
