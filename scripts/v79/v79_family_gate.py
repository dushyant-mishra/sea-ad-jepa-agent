#!/usr/bin/env python3
"""Fail-closed family gate for the fresh recovery suites (controller ruling 2026-10-11, item 6).

Run before each world's fit: reads the family's completed part files in the suite directory and applies the frozen
criteria world by world (v79_recovery_rules.world_failures). If any completed world has failed, the family is
NOT_QUALIFIED: write FAMILY_STOPPED_<likelihood>.json (once; never rewritten) and exit 10, so the scheduler records
the remaining worlds as SKIPPED_FAMILY_STOPPED, neither a launch failure nor a statistical result. Exit 11 refuses
parts that mix code snapshots, sampler configurations or rules (an integrity failure, not a statistical one).

Usage: v79_family_gate.py <suite dir> <likelihood>
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import v79_recovery_rules as RR  # noqa: E402


def main() -> int:
    suite, lik = Path(sys.argv[1]), sys.argv[2]
    parts = []
    for p in sorted(suite.glob(f"part_{lik}_*.json")):
        rec = json.loads(p.read_text(encoding="utf-8"))
        if rec.get("schema") != "V79_SIMULATION_RECOVERY_V2" or rec.get("likelihood") != lik:
            print(f"refuse: {p.name} is not a V2 {lik} part", file=sys.stderr)
            return 11
        parts.append((p.name, rec))
    for key in ("code_snapshot",):
        if len({rec.get(key) for _, rec in parts}) > 1:
            print(f"refuse: parts mix {key}", file=sys.stderr)
            return 11
    for key in ("sampler_config", "sampler_rules"):
        if len({(rec.get(key) or {}).get("sha256") for _, rec in parts}) > 1:
            print(f"refuse: parts mix {key}", file=sys.stderr)
            return 11
    fits = {w: f for _, rec in parts for w, f in rec["fits"].items()}
    failed = {w: c for w, c in RR.world_failures(fits).items() if c}
    if not failed:
        print(f"gate: {lik} continues ({len(fits)} completed worlds, none failed)")
        return 0
    stop = suite / f"FAMILY_STOPPED_{lik}.json"
    if not stop.exists():
        rec = dict(schema="V79_FAMILY_STOPPED_V1", likelihood=lik, terminal="NOT_QUALIFIED", failed=failed,
                   completed_worlds=sorted(fits), parts={n: r.get("code_snapshot") for n, r in parts},
                   rule="controller ruling 2026-10-11 item 6: a family failing any required world after its frozen "
                        "retry/extension path is NOT_QUALIFIED and stopped; no new parameterization",
                   utc=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
        fd = os.open(stop, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0), 0o644)
        with os.fdopen(fd, "wb") as fh:
            fh.write((json.dumps(rec, indent=1) + "\n").encode("utf-8"))
    print(f"gate: {lik} STOPPED, failed worlds {failed}")
    return 10


if __name__ == "__main__":
    raise SystemExit(main())
