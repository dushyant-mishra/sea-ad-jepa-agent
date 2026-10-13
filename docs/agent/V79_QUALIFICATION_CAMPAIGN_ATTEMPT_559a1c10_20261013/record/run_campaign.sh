#!/usr/bin/env bash
# The single authorized V79 V2_CORE qualification campaign (PR #308 comment 6134273489).
# Runs the frozen campaign runner. After an ordinary interruption, the SAME command is re-run unchanged (same
# checkout, custody, result directory and custody receipt SHA); the runner itself accepts only a valid contiguous
# prefix. No retry of a refused run, no setting change, no repair.
set -u
B=D:/jepa_v79_qualification_campaign_559a1c10
REC=$B/record
W=D:/jepa_wt_v79_qualification_559a1c10
PY=C:/Users/dushy/anaconda3/envs/v79-bayes/python.exe
CUSTODY_SHA=48581e7330020fd8c8e283fe95277bff6c9a585163c93920662d5fa9f6204d66
cd "$W" || exit 90
[ "$(git rev-parse HEAD)" = 559a1c104c8f1f56d2c05509eecf6b9dc05846a5 ] || { echo "head mismatch $(date -u +%FT%TZ)" >> "$REC/CAMPAIGN_RUN_RECORD.txt"; exit 91; }
[ -z "$(git status --porcelain)" ] || { echo "worktree not clean $(date -u +%FT%TZ)" >> "$REC/CAMPAIGN_RUN_RECORD.txt"; exit 92; }
N=$(grep -c '^campaign_start_utc=' "$REC/CAMPAIGN_RUN_RECORD.txt" 2>/dev/null || true); N=$(( ${N:-0} + 1 ))
typeperf "\\Processor(_Total)\\% Processor Time" -si 30 -o "$(cygpath -w "$REC/MACHINE_CPU_TYPEPERF_invocation$N.csv")" -y > /dev/null 2>&1 &
TP=$!
echo "campaign_start_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ) invocation=$N head=$(git rev-parse HEAD) status=[$(git status --porcelain)] result_dir_existed=$([ -e "$B/result" ] && echo yes || echo no) cmd=python scripts/v79/run_v79_v2_core_qualification.py $W $B/fit_custody $B/result $CUSTODY_SHA" >> "$REC/CAMPAIGN_RUN_RECORD.txt"
PYTHONDONTWRITEBYTECODE=1 "$PY" -B scripts/v79/run_v79_v2_core_qualification.py "$W" "$B/fit_custody" "$B/result" "$CUSTODY_SHA" > "$REC/CAMPAIGN_STDOUT_invocation$N.json" 2> "$REC/CAMPAIGN_STDERR_invocation$N.txt"
RC=$?
echo "campaign_exit=$RC invocation=$N campaign_end_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ) status_after=[$(git status --porcelain)] fit_receipts=$(ls "$B/result"/fit_*.json 2>/dev/null | wc -l) campaign_receipt=$([ -e "$B/result/V79_V2_CORE_QUALIFICATION_CAMPAIGN_RECEIPT_V1.json" ] && echo yes || echo no)" >> "$REC/CAMPAIGN_RUN_RECORD.txt"
kill "$TP" 2>/dev/null; taskkill //F //IM typeperf.exe > /dev/null 2>&1
exit $RC
