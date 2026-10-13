#!/usr/bin/env bash
# Continuation of the same frozen V79 V2_CORE qualification campaign (PR #317 comment 6146378159): records 89-1056
# through the top-level runner, same head, same custody c5116d62, same result directory holding the accepted
# first 88. The runner validates the contiguous prefix and skips completed worlds. After an ordinary interruption
# the SAME command may be re-run unchanged; anything else => preserve and STOP. No repair, no selective rerun.
set -u
B=D:/jepa_v79_qualification_world1_a61437ba
REC=$B/record/continuation
W=D:/jepa_wt_v79_qual_world1_a61437ba
PY=C:/Users/dushy/anaconda3/envs/v79-bayes/python.exe
CUSTODY_SHA=c5116d6273f82fd3b3c5450b6bb8d701e03ef7d17ba6ada98eb5ff5aec906b63
cd "$W" || exit 90
[ "$(git rev-parse HEAD)" = a61437ba284e9e75b0557157ad68e56eacd8f8fe ] || { echo "head mismatch $(date -u +%FT%TZ)" >> "$REC/CAMPAIGN_RUN_RECORD.txt"; exit 91; }
[ -z "$(git status --porcelain)" ] || { echo "worktree not clean $(date -u +%FT%TZ)" >> "$REC/CAMPAIGN_RUN_RECORD.txt"; exit 92; }
N=$(grep -c '^campaign_start_utc=' "$REC/CAMPAIGN_RUN_RECORD.txt" 2>/dev/null || true); N=$(( ${N:-0} + 1 ))
typeperf "\\Processor(_Total)\\% Processor Time" -si 60 -o "$(cygpath -w "$REC/MACHINE_CPU_TYPEPERF_invocation$N.csv")" -y > /dev/null 2>&1 &
TP=$!
echo "campaign_start_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ) invocation=$N head=$(git rev-parse HEAD) status=[$(git status --porcelain)] fit_receipts_before=$(ls "$B/result"/fit_*.json 2>/dev/null | wc -l) cmd=python scripts/v79/run_v79_v2_core_qualification.py $W $B/fit_custody $B/result $CUSTODY_SHA" >> "$REC/CAMPAIGN_RUN_RECORD.txt"
PYTHONDONTWRITEBYTECODE=1 "$PY" -B scripts/v79/run_v79_v2_core_qualification.py "$W" "$B/fit_custody" "$B/result" "$CUSTODY_SHA" > "$REC/CAMPAIGN_STDOUT_invocation$N.json" 2> "$REC/CAMPAIGN_STDERR_invocation$N.txt"
RC=$?
echo "campaign_exit=$RC invocation=$N campaign_end_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ) status_after=[$(git status --porcelain)] fit_receipts_after=$(ls "$B/result"/fit_*.json 2>/dev/null | wc -l) npz_after=$(ls "$B/result"/*.npz 2>/dev/null | wc -l) campaign_receipt=$([ -e "$B/result/V79_V2_CORE_QUALIFICATION_CAMPAIGN_RECEIPT_V1.json" ] && echo yes || echo no) lock_present=$([ -e "$B/result/HEAVY_FIT.lock" ] && echo yes || echo no)" >> "$REC/CAMPAIGN_RUN_RECORD.txt"
kill "$TP" 2>/dev/null; taskkill //F //IM typeperf.exe > /dev/null 2>&1
exit $RC
