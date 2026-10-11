#!/usr/bin/env python3
"""Measure one running fit's resources until it exits (resource-efficiency requirement 7: no parallel production
runs before one fit is measured). Attaches to the Windows python process whose command line matches a pattern and
samples every --interval seconds: resident memory (peak), process CPU (in logical processors), machine CPU and free
RAM, cumulative disk read and write bytes, and wall time. Writes a JSON summary when the process exits.

Usage: measure_v79_fit_resources.py <command-line regex> <out.json> [--interval 10]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import time
from datetime import datetime, timezone

import psutil


def _self_and_ancestors() -> set:
    pids = {os.getpid()}
    try:
        pids.update(p.pid for p in psutil.Process().parents())
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        pass
    return pids


def find(pattern: str):
    """The fitting runner (a run_v79_*.py python process) whose command line matches; never this monitor itself,
    whose own command line carries the same pattern (self-audit 54)."""
    rx = re.compile(pattern)
    skip = _self_and_ancestors()
    for p in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            cmd = " ".join(p.info["cmdline"] or [])
            if (p.info["pid"] not in skip and p.info["name"] and p.info["name"].lower().startswith("python")
                    and re.search(r"run_v79_\w+\.py", cmd) and rx.search(cmd)):
                return p
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("pattern")
    ap.add_argument("out")
    ap.add_argument("--interval", type=float, default=10.0)
    ap.add_argument("--wait", type=float, default=900.0, help="seconds to wait for the process to appear")
    a = ap.parse_args()
    t_wait = time.time()
    p = None
    while p is None and time.time() - t_wait < a.wait:
        p = find(a.pattern)
        time.sleep(2)
    if p is None:
        raise SystemExit(f"no process matching {a.pattern!r}")
    ncpu = psutil.cpu_count(logical=True)
    t0, samples = time.time(), []
    p.cpu_percent(None)
    psutil.cpu_percent(None)
    io0 = p.io_counters()
    while p.is_running():
        time.sleep(a.interval)
        try:
            mem, io = p.memory_info().rss, p.io_counters()
            samples.append(dict(t=round(time.time() - t0, 1), rss_gb=round(mem / 2 ** 30, 3),
                                proc_cpus=round(p.cpu_percent(None) / 100, 2), machine_cpu_pct=psutil.cpu_percent(None),
                                free_ram_gb=round(psutil.virtual_memory().available / 2 ** 30, 2),
                                read_mb=round((io.read_bytes - io0.read_bytes) / 2 ** 20, 1),
                                write_mb=round((io.write_bytes - io0.write_bytes) / 2 ** 20, 1)))
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            break
    s = samples or [dict(rss_gb=0, proc_cpus=0, machine_cpu_pct=0, free_ram_gb=0, read_mb=0, write_mb=0, t=0)]
    summary = dict(schema="V79_FIT_RESOURCE_MEASUREMENT_V1", pattern=a.pattern, pid=p.pid,
                   finished_utc=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                   wall_seconds=round(time.time() - t0, 1), logical_cpus=ncpu,
                   peak_rss_gb=max(x["rss_gb"] for x in s), mean_proc_cpus=round(sum(x["proc_cpus"] for x in s) / len(s), 2),
                   max_proc_cpus=max(x["proc_cpus"] for x in s),
                   mean_machine_cpu_pct=round(sum(x["machine_cpu_pct"] for x in s) / len(s), 1),
                   min_free_ram_gb=min(x["free_ram_gb"] for x in s), disk_read_mb=s[-1]["read_mb"],
                   disk_write_mb=s[-1]["write_mb"], n_samples=len(samples), samples=samples)
    with open(a.out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(summary, indent=1) + "\n")
    print(json.dumps({k: v for k, v in summary.items() if k != "samples"}))


if __name__ == "__main__":
    main()
