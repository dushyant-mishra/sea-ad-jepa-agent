#!/usr/bin/env bash
# Detection V2 (every random component non-centred) on recovery worlds S0 and S1, GPU, snapshot 61df6088.
# Precommitted (self-audit 48): last sampler setting tried for detection.
E=/mnt/d/jepa_wt_v79_bayes_20261009/results/v79/recovery/experiments_V2_detection
P=/mnt/d/jepa_wt_v79_bayes_20261009/results/v79/recovery/progress.txt
PY=/home/dushyant_mishra/miniconda3/envs/v79-bayes-gpu/bin/python
RUN=/mnt/d/v79_runs/61df6088/scripts/v79/run_v79_recovery.py
V2='{"op": 0.0, "logsd_op": 0.0, "donor": 0.0, "logsd_donor": 0.0, "dk": 0.0, "logsd_dk": 0.0}'
export XLA_PYTHON_CLIENT_PREALLOCATE=true XLA_PYTHON_CLIENT_MEM_FRACTION=0.18 V79_PROGRESS=1
cd /tmp
for f in S0_class_absent S1_present; do
  (
    echo "bernoulli V2 $f gpu start $(date -u +%H:%M:%SZ)" >> "$P"
    timeout 43200 "$PY" -u "$RUN" --likelihood bernoulli --fits "$f" --genes 20 --centring "$V2" \
      --out "$E/part_bernoulli_V2_$f.json" > "$E/log_bernoulli_V2_$f.txt" 2>&1
    echo "bernoulli V2 $f gpu exit $? $(date -u +%H:%M:%SZ)" >> "$P"
  ) &
  sleep 60
done
wait
