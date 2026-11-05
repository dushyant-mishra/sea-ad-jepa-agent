#!/usr/bin/env python3
"""Measure V2 attempt-journal I/O. SYNTHETIC OPAQUE BYTES ONLY.

No model, optimizer, GPU, RNA or controller truth. Linux only (/proc/self/io).

Usage: measure_attempt_journal_v2_io_no_training.py LABEL DIR STATE_BYTES UPDATES

Runs open -> (begin, commit) x UPDATES -> close -> inspect -> forensic in DIR
(deleted afterwards) and prints one JSON line: per-phase seconds, rchar/wchar,
storage read/write bytes, checkpoint (.state.bin) reads, scrub-boundary cost,
peak RSS and disk footprint. Exits 1 if the writer reads more checkpoints than
1 + UPDATES + (full scrubs at every 32nd update) + a small slack.
"""
import hashlib, json, os, resource, shutil, sys, time
from pathlib import Path
from scripts.v5 import jepa_synth2048_attempt_journal_v2 as v

PANEL = "1" * 64
U0 = {"cell_centered_energy": 0.25, "same_gene_cross_cell_variance": 0.5,
      "same_cell_expression_shuffle_delta": 0.125}


def probe(update, sha):
    return {"state_update": update, "state_payload_sha256": sha,
            "probe_panel_sha256": PANEL, "operator_homogeneous_eval_mode": True,
            "identical_gene_sets": True, "metrics": dict(U0),
            "cell_distinct_row_count": 64, "probe_cells": 64, "nonfinite_values": 0,
            "measurement_origin": "CALLER_REPORTED__NOT_PHYSICALLY_PROVED"}


def io():
    out = {}
    with open("/proc/self/io") as fh:
        for line in fh:
            k, val = line.split(":")
            out[k] = int(val)
    return out


label, base, size, n = sys.argv[1], Path(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])
shutil.rmtree(base, ignore_errors=True)
base.mkdir(parents=True)
root, custody = base / "run", base / "outside-head"
reads = {"n": 0, "bytes": 0}
real_read = v._read


def counted(path, limit, *, twin_ok=False):
    raw = real_read(path, limit, twin_ok=twin_ok)
    if Path(path).name.endswith(".state.bin"):
        reads["n"] += 1
        reads["bytes"] += len(raw)
    return raw


v._read = counted
block = os.urandom(size - 8)
calls = []


def timed(_name, _update, _fn, **kw):
    i0, r0, t0 = io(), dict(reads), time.perf_counter()
    out = _fn(**kw)
    dt = time.perf_counter() - t0
    i1 = io()
    calls.append({"call": _name, "update": _update, "seconds": dt,
                  "rchar": i1["rchar"] - i0["rchar"], "wchar": i1["wchar"] - i0["wchar"],
                  "read_bytes": i1["read_bytes"] - i0["read_bytes"],
                  "write_bytes": i1["write_bytes"] - i0["write_bytes"],
                  "state_reads": reads["n"] - r0["n"],
                  "state_bytes_read": reads["bytes"] - r0["bytes"]})
    return out


def state(u):
    raw = u.to_bytes(8, "little") + block
    return raw, hashlib.sha256(raw).hexdigest()


raw0, sha0 = state(0)
timed("open", 0, v.open_journal, root=root, custody=custody, run_id="io", horizon=n,
      panel_sha256=PANEL, config_sha256="2" * 64, rights_sha256="3" * 64,
      initial_state_bytes=raw0, initial_probe=probe(0, sha0))
for u in range(1, n + 1):
    timed("begin", u, v.begin_attempt, root=root, custody=custody, update=u)
    raw, sha = state(u)
    timed("commit", u, v.commit_reported_update, root=root, custody=custody,
          update=u, state_bytes=raw, probe=probe(u, sha))
    del raw
timed("close", n, v.close_run, root=root, custody=custody)
timed("inspect", n, v.inspect_journal, root=root, custody=custody)
timed("forensic", n, v.inspect_forensic_prefix, root=root, custody=custody)
disk = sum(p.stat().st_size for d in (root, custody) for p in d.rglob("*") if p.is_file())


def total(names):
    sel = [c for c in calls if c["call"] in names]
    return {k: round(sum(c[k] for c in sel), 3) if k == "seconds" else sum(c[k] for c in sel)
            for k in ("seconds", "rchar", "wchar", "read_bytes", "write_bytes",
                      "state_reads", "state_bytes_read")}


summary = {
    "label": label, "dir": str(base), "state_bytes": size, "updates": n,
    "writer_open_begin_commit": total({"open", "begin", "commit"}),
    "close": total({"close"}), "inspect": total({"inspect"}), "forensic": total({"forensic"}),
    "boundary": {c["call"] + str(c["update"]): {"state_reads": c["state_reads"],
                 "seconds": round(c["seconds"], 4)}
                 for c in calls if c["call"] == "begin" and c["update"] in (31, 32, 33)},
    "state_reads_per_update": [sum(c["state_reads"] for c in calls
                                   if c["update"] == u and c["call"] in ("begin", "commit"))
                               for u in range(1, n + 1)],
    "begin_seconds": [round(c["seconds"], 4) for c in calls if c["call"] == "begin"],
    "commit_seconds": [round(c["seconds"], 4) for c in calls if c["call"] == "commit"],
    "max_single_call_seconds": round(max(c["seconds"] for c in calls), 4),
    "peak_rss_mib": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 1),
    "disk_footprint_bytes": disk,
}
every = getattr(v, "FULL_SCRUB_EVERY_ATTEMPTS", 32)
expected = 1 + n + sum(range(every, n + 1, every))
summary["writer_checkpoint_read_budget"] = expected
print(json.dumps(summary))
shutil.rmtree(base, ignore_errors=True)
if summary["writer_open_begin_commit"]["state_reads"] > expected + n // 10 + 2:
    sys.exit("READ_BUDGET_EXCEEDED")
