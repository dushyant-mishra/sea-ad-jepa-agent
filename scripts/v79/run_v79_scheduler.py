#!/usr/bin/env python3
"""V79 fit scheduler: one queue for CPU and GPU fits with ONE machine-wide cap.

Every running fit counts, wherever it runs: Windows Python fits and WSL (GPU) fits alike, because a GPU fit still
drives NUTS from the host and uses CPU (self-audit 45). Jobs run in priority order; each runs in its own Git Bash
under a timeout and writes one start and one end record to a JSONL ledger. The end record classifies the outcome
mechanically, never statistically:
  OUTPUT_WRITTEN            exit 0 and the expected output file exists (its SHA-256 is recorded)
  TIMEOUT                   exit 124
  LAUNCH_OR_RUNTIME_FAILURE any other exit, or exit 0 without the output file
A statistical verdict comes only from the output file itself (v79_recovery_rules.combine_parts).

Job file: JSON list of {"name", "cmd", "log", "out", "device": "cpu"|"gpu"}. A gpu cmd is a Linux command line run
inside WSL. Usage: run_v79_scheduler.py <jobs.json> <ledger.jsonl> [--slots 2] [--timeout 43200] [--settle 120]
"""
from __future__ import annotations

import argparse
import json
import shlex
import shutil
import subprocess
import time
from datetime import datetime, timezone

WIN_FIT = "run_v79_(recovery|qualification|inference|phase_c|ppc_heldout|benchmark)"
WSL_FIT = r"^/home/[^ ]*/python[0-9.]* -u [^ ]*run_v79_(recovery|qualification|inference|phase_c|ppc_heldout|benchmark)"


def windows_fits() -> int:
    ps = ("@(Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'python.exe' -and "
          f"$_.CommandLine -match '{WIN_FIT}' }}).Count")
    r = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True)
    return int(r.stdout.strip())


def wsl_fits() -> int:
    r = subprocess.run(["wsl", "-e", "pgrep", "-fc", WSL_FIT], capture_output=True, text=True)
    out = r.stdout.replace("\x00", "").strip()
    return int(out) if out.isdigit() else 0


def running_fits() -> int:
    try:
        return windows_fits() + wsl_fits()
    except (ValueError, OSError):
        return 10 ** 6                                  # unreadable: assume full, never oversubscribe


def git_bash() -> str:
    """Git Bash by PATH lookup; a bare "bash" resolves System32 (WSL) first (self-audit 46)."""
    b = shutil.which("bash")
    if not b or "system32" in b.lower() or "windowsapps" in b.lower():
        raise SystemExit(f"refusing: bash resolves to {b!r}, not Git Bash")
    return b


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def wrapped(job: dict, bash: str, timeout: int, ledger: str) -> str:
    inner = job["cmd"] if job.get("device", "cpu") == "cpu" else \
        "MSYS_NO_PATHCONV=1 wsl -e bash -c " + shlex.quote(job["cmd"])
    out = job["out"]
    return (f'timeout {timeout} "{bash}" -c {shlex.quote(inner)} > "{job["log"]}" 2>&1; rc=$?; '
            f'if [ "$rc" = 124 ]; then cls=TIMEOUT; elif [ "$rc" = 0 ] && [ -f "{out}" ]; then cls=OUTPUT_WRITTEN; '
            # exit 10 from v79_family_gate.py: the family already failed a world, so this world is not run
            f'elif [ "$rc" = 10 ] && [ ! -f "{out}" ]; then cls=SKIPPED_FAMILY_STOPPED; '
            f'else cls=LAUNCH_OR_RUNTIME_FAILURE; fi; '
            # stdin from /dev/null: a detached job has no console, and sha256sum otherwise fails silently in the pipe
            f'if [ -f "{out}" ]; then sha=$(sha256sum "{out}" </dev/null 2>/dev/null | cut -c1-64); '
            f'[ ${{#sha}} = 64 ] || sha=UNAVAILABLE; else sha=none; fi; '
            f'printf \'{{"event":"end","name":"%s","utc":"%s","exit":%s,"class":"%s","out":"%s","out_sha256":"%s"}}\\n\' '
            f'{shlex.quote(job["name"])} "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$rc" "$cls" {shlex.quote(out)} "$sha" '
            f'>> "{ledger}"')


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("jobs")
    ap.add_argument("ledger")
    ap.add_argument("--slots", type=int, default=2)
    ap.add_argument("--timeout", type=int, default=43200)
    ap.add_argument("--settle", type=int, default=120, help="seconds to wait after a launch before recounting")
    a = ap.parse_args()
    jobs = json.load(open(a.jobs, encoding="utf-8"))
    for j in jobs:
        for k in ("name", "cmd", "log", "out"):
            if k not in j:
                raise SystemExit(f"job {j.get('name')!r} lacks {k!r}")
    bash = git_bash()
    for j in jobs:
        while running_fits() >= a.slots:
            time.sleep(60)
        subprocess.Popen([bash, "-c", wrapped(j, bash, a.timeout, a.ledger)],
                         creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS)
        with open(a.ledger, "a", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(dict(event="start", name=j["name"], utc=now(), device=j.get("device", "cpu"),
                                     slots=a.slots, cmd=j["cmd"])) + "\n")
        time.sleep(a.settle)
    with open(a.ledger, "a", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(dict(event="all_launched", utc=now(), n=len(jobs))) + "\n")


if __name__ == "__main__":
    main()
