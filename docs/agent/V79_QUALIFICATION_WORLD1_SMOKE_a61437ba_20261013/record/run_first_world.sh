#!/usr/bin/env bash
# The single authorized first-opaque-world 88-fit physical smoke (PR #317 comment 6137248929), through the real
# production worker run_v79_v2_core_qualification_world.py at a61437ba. Run exactly once; any exception => preserve
# and STOP. No retry, no repair, no second world.
set -u
B=D:/jepa_v79_qualification_world1_a61437ba
REC=$B/record
W=D:/jepa_wt_v79_qual_world1_a61437ba
PY=C:/Users/dushy/anaconda3/envs/v79-bayes/python.exe
CUSTODY_SHA=c5116d6273f82fd3b3c5450b6bb8d701e03ef7d17ba6ada98eb5ff5aec906b63
WORLD=2ae1cb055fed
cd "$W" || exit 90
[ "$(git rev-parse HEAD)" = a61437ba284e9e75b0557157ad68e56eacd8f8fe ] || { echo "head mismatch" >> "$REC/WORLD_RUN_RECORD.txt"; exit 91; }
[ -z "$(git status --porcelain)" ] || { echo "worktree not clean" >> "$REC/WORLD_RUN_RECORD.txt"; exit 92; }
[ -e "$B/result" ] && { echo "result dir already exists - refusing (single run)" >> "$REC/WORLD_RUN_RECORD.txt"; exit 93; }
typeperf "\\Processor(_Total)\\% Processor Time" -si 30 -o "$(cygpath -w "$REC/MACHINE_CPU_TYPEPERF.csv")" -y > /dev/null 2>&1 &
TP=$!
echo "world_start_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ) head=$(git rev-parse HEAD) status=[$(git status --porcelain)] cmd=python scripts/v79/run_v79_v2_core_qualification_world.py $W $B/fit_custody $B/result $CUSTODY_SHA $WORLD" > "$REC/WORLD_RUN_RECORD.txt"
PYTHONDONTWRITEBYTECODE=1 "$PY" -B scripts/v79/run_v79_v2_core_qualification_world.py "$W" "$B/fit_custody" "$B/result" "$CUSTODY_SHA" "$WORLD" > "$REC/WORLD_STDOUT.json" 2> "$REC/WORLD_STDERR.txt"
RC=$?
echo "world_exit=$RC world_end_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ) status_after=[$(git status --porcelain)] fit_receipts=$(ls "$B/result"/fit_*.json 2>/dev/null | wc -l) npz=$(ls "$B/result"/*.npz 2>/dev/null | wc -l) lock_present=$([ -e "$B/result/HEAVY_FIT.lock" ] && echo yes || echo no)" >> "$REC/WORLD_RUN_RECORD.txt"
kill "$TP" 2>/dev/null; taskkill //F //IM typeperf.exe > /dev/null 2>&1
exit $RC
