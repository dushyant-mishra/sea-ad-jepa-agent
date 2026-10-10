#!/usr/bin/env bash
# Run a queue of commands N at a time. Queue file: one command per line; a line "WAIT" is a barrier (every
# earlier job must finish first); blank lines and lines starting with # are skipped. Each job's output goes to
# <log_dir>/job_<n>.log and one progress line per job (exit code, UTC time) to <log_dir>/progress.txt.
# Usage: run_v79_queue.sh <N> <queue_file> <log_dir>
set -u
N="$1"; Q="$2"; LOG="$3"
mkdir -p "$LOG"
jobs_running() { jobs -rp | wc -l; }
n=0
while IFS= read -r line || [ -n "$line" ]; do
  case "$line" in ''|'#'*) continue ;; esac
  if [ "$line" = "WAIT" ]; then wait; echo "barrier $(date -u +%H:%M:%SZ)" >> "$LOG/progress.txt"; continue; fi
  while [ "$(jobs_running)" -ge "$N" ]; do sleep 5; done
  n=$((n + 1))
  ( bash -c "$line" > "$LOG/job_${n}.log" 2>&1
    echo "job $n exit $? $(date -u +%H:%M:%SZ) :: $line" >> "$LOG/progress.txt" ) &
  echo "job $n start $(date -u +%H:%M:%SZ) :: $line" >> "$LOG/progress.txt"
done < "$Q"
wait
echo "queue done $(date -u +%H:%M:%SZ)" >> "$LOG/progress.txt"
