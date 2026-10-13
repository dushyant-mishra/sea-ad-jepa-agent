#!/usr/bin/env bash
# One-shot V79 qualification scoring invocation. Refuses to start twice.
set +e
RW=D:/jepa_v79_scoring_run_ac1e73d7_20261013
W=D:/jepa_v79_scoring_exec_ac1e73d7
PY=C:/Users/dushy/anaconda3/envs/v79-bayes/python.exe
MARK=$RW/record/RUN_STARTED.marker
if [ -e "$MARK" ]; then echo "RUN ALREADY STARTED - REFUSING A SECOND INVOCATION"; exit 9; fi
date -u +%Y-%m-%dT%H:%M:%S.%3NZ > "$MARK"
ARGS=(scripts/v79/run_v79_v2_core_scoring_orchestrator.py
  --repo-root "$W"
  --campaign-result-dir D:/jepa_v79_qualification_world1_a61437ba/result
  --result-ledger D:/jepa_v79_qualification_world1_a61437ba/record/continuation/RESULT_FILE_LEDGER_SHA256.txt
  --custody-dir D:/jepa_v79_qualification_world1_a61437ba/fit_custody
  --authorization "$RW/authorization/V79_V2_CORE_QUALIFICATION_SCORING_AUTHORIZATION_ISSUED_ac1e73d7.json"
  --authorization-sha256 4793d8f9024891a6572337246c76dea871b65ebde476d8f3983c483498b80337
  --output-dir "$RW/scoring_output")
cd "$W" || exit 8
echo "run_start_utc=$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ) head=$(git rev-parse HEAD) status=[$(git status --porcelain --untracked-files=all)] ignored_lines=$(git status --porcelain --ignored | wc -l) interpreter=$PY (PYTHONDONTWRITEBYTECODE=1 -B) cwd=$W cmd=python ${ARGS[*]}" > "$RW/record/SCORING_RUN_RECORD.txt"
PYTHONDONTWRITEBYTECODE=1 "$PY" -B "${ARGS[@]}" > "$RW/record/SCORING_STDOUT.txt" 2> "$RW/record/SCORING_STDERR.txt"
rc=$?
echo "run_exit=$rc run_end_utc=$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ) status_after=[$(git status --porcelain --untracked-files=all)] ignored_after_lines=$(git status --porcelain --ignored | wc -l)" >> "$RW/record/SCORING_RUN_RECORD.txt"
cat "$RW/record/SCORING_RUN_RECORD.txt"; echo "--- stdout tail"; tail -20 "$RW/record/SCORING_STDOUT.txt"; echo "--- stderr tail"; tail -30 "$RW/record/SCORING_STDERR.txt"
exit $rc
