#!/usr/bin/env python3
"""Run V79 fits in priority order with at most --slots fit processes machine-wide (fits started elsewhere count),
each under its own timeout and log, appending one progress line per finished job (self-audit 41: eight fits were
lost to a 4 h timeout when four suites oversubscribed 16 cores).

Job file: JSON list of {"name", "cmd", "log"}; cmd is one shell command run with `bash -c`.
Usage: run_v79_scheduler.py <jobs.json> <progress.txt> [--slots 4] [--timeout 43200] [--settle 120]
"""
from __future__ import annotations

import argparse
import json
import subprocess
import time
from datetime import datetime, timezone

FIT_PATTERN = "run_v79_(recovery|qualification|inference|phase_c|ppc_heldout|benchmark)"


def running_fits() -> int:
    ps = ("@(Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'python.exe' -and "
          f"$_.CommandLine -match '{FIT_PATTERN}' }}).Count")
    r = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True)
    try:
        return int(r.stdout.strip() or 0)
    except ValueError:
        return 10 ** 6                                  # unreadable: assume full, never oversubscribe


def now() -> str:
    return datetime.now(timezone.utc).strftime("%H:%M:%SZ")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("jobs")
    ap.add_argument("progress")
    ap.add_argument("--slots", type=int, default=4)
    ap.add_argument("--timeout", type=int, default=43200)
    ap.add_argument("--settle", type=int, default=120, help="seconds to wait after a launch before recounting")
    a = ap.parse_args()
    jobs = json.load(open(a.jobs, encoding="utf-8"))
    for j in jobs:
        while running_fits() >= a.slots:
            time.sleep(60)
        wrapped = (f'timeout {a.timeout} {j["cmd"]} > "{j["log"]}" 2>&1; '
                   f'echo "{j["name"]} exit $? $(date -u +%H:%M:%SZ)" >> "{a.progress}"')
        subprocess.Popen(["bash", "-c", wrapped],
                         creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS)
        with open(a.progress, "a", encoding="utf-8", newline="\n") as fh:
            fh.write(f"{j['name']} start {now()}\n")
        time.sleep(a.settle)
    with open(a.progress, "a", encoding="utf-8", newline="\n") as fh:
        fh.write(f"scheduler: all {len(jobs)} jobs launched {now()}\n")


if __name__ == "__main__":
    main()
