#!/usr/bin/env bash
# V69: measure cisTarget worker scaling on a FIXED workload.
#
# The same 16 motifs, the same region FASTA, the same cbust and the same parameters at
# every worker count. The ONLY thing that varies is -t. Outputs must be digest-identical
# across worker counts; that is checked by compare_bench_runs_v1.py, and a difference
# stops the full build.
#
# WORKLOAD CHOICE, recorded because it is a trade-off and not a free parameter.
# The mandate asked for the 120-motif subset. At one worker that is roughly eight hours
# for a single point and about fifteen hours for the whole table, which would cost more
# than the speedup it is meant to inform. The 16-motif batch gives the same five-point
# curve in under two hours. The cost is GRANULARITY at the top of the curve: 16 motifs
# on 16 workers is a single wave, so that point cannot show queueing effects. This is
# stated in the receipt rather than hidden, and the 4- and 8-worker points (4 and 2
# waves) remain informative about saturation.
#
# Each run writes to its OWN directory, so no run can overwrite another's provenance.
set -euo pipefail

FASTA="${1:?region fasta}"
MOTIF_LIST="${2:?motif list}"
OUT_ROOT="${3:?output root}"
WORKERS="${4:-1 2 4 8 16}"

mkdir -p "$OUT_ROOT"
echo "workload: $(wc -l < "$MOTIF_LIST") motifs x $(grep -c '^>' "$FASTA") regions"
sha256sum "$MOTIF_LIST" "$FASTA"

for W in $WORKERS; do
  RUN_ID="SCALE_t${W}"
  RUN_DIR="$OUT_ROOT/$RUN_ID"
  if [ -s "$RUN_DIR/$RUN_ID.bench.json" ]; then
    echo "=== $RUN_ID already measured, skipping ==="
    continue
  fi
  echo "=== $RUN_ID : $W worker(s) ==="
  mkdir -p "$RUN_DIR"
  bash /tmp/bench_run_immutable.sh "$RUN_ID" "$FASTA" "$MOTIF_LIST" "$RUN_DIR" "$W" \
    > "$RUN_DIR/$RUN_ID.driver.log" 2>&1
  grep -E '"(wall_clock_seconds|cbust_scoring_seconds)"' "$RUN_DIR/$RUN_ID.bench.json"
done

echo "=== SCALING TABLE FINISHED ==="
