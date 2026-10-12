#!/usr/bin/env bash
# The single authorized repaired engineering benchmark attempt (PR #308, rulings 6128881654 / 6129078915).
# Runs the frozen runner exactly once. No retry, no setting change, no repair.
set -u
B=D:/jepa_v79_engineering_benchmark_rerun_559a1c10
REC=$B/record
W=D:/jepa_wt_v79_benchmark_559a1c10
PY=C:/Users/dushy/anaconda3/envs/v79-bayes/python.exe
PREP_SHA=ee89a67ba3919a6593b2f20e4cc4030904e4032ef78c28438fecdab0cfed8170
cd "$W" || exit 90
[ "$(git rev-parse HEAD)" = 559a1c104c8f1f56d2c05509eecf6b9dc05846a5 ] || { echo "head mismatch" >> "$REC/BENCH_RUN_RECORD.txt"; exit 91; }
[ -e "$B/result" ] && { echo "result dir exists" >> "$REC/BENCH_RUN_RECORD.txt"; exit 92; }
typeperf "\\Processor(_Total)\\% Processor Time" -si 5 -o "$(cygpath -w "$REC/MACHINE_CPU_TYPEPERF.csv")" -y > /dev/null 2>&1 &
TP=$!
echo "bench_start_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ) head=$(git rev-parse HEAD) status=[$(git status --porcelain)] cmd=python scripts/v79/run_v79_v2_core_benchmark.py $W $B/fit_custody $B/result $PREP_SHA" > "$REC/BENCH_RUN_RECORD.txt"
PYTHONDONTWRITEBYTECODE=1 "$PY" -B scripts/v79/run_v79_v2_core_benchmark.py "$W" "$B/fit_custody" "$B/result" "$PREP_SHA" > "$REC/BENCH_STDOUT.json" 2> "$REC/BENCH_STDERR.txt"
RC=$?
echo "bench_exit=$RC bench_end_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ) status_after=[$(git status --porcelain)]" >> "$REC/BENCH_RUN_RECORD.txt"
kill "$TP" 2>/dev/null; taskkill //F //IM typeperf.exe > /dev/null 2>&1
exit $RC
