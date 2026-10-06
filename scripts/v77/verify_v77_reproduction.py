#!/usr/bin/env python3
"""Compare a frozen JSON artifact with an independent reproduction, and write a receipt.

Used where a frozen artifact lacked a committed producer (S141) or where its producer was
refactored (S140, the T5 extraction). The verdict is byte identity. If the bytes differ, the
receipt lists every differing leaf, and nothing is adjusted: a reproduction that does not match
is reported as a failure, never re-tolerated after the discrepancy has been seen.

Refuses to run from a tree with modified tracked files, because the receipt names a commit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True, cwd=HERE).stdout.strip()


def _leaves(x, prefix=""):
    if isinstance(x, dict):
        for k, v in x.items():
            yield from _leaves(v, f"{prefix}/{k}")
    elif isinstance(x, list):
        for i, v in enumerate(x):
            yield from _leaves(v, f"{prefix}[{i}]")
    else:
        yield prefix, x


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--frozen", required=True)
    ap.add_argument("--reproduced", required=True)
    ap.add_argument("--producer-command", required=True)
    ap.add_argument("--what", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    dirty = _git("status", "--porcelain", "--untracked-files=no")
    if dirty:
        sys.exit("refusing: tracked files are modified; the receipt must describe a committed head\n"
                 + dirty)
    fb, rb = Path(a.frozen).read_bytes(), Path(a.reproduced).read_bytes()
    fj, rj = json.loads(fb), json.loads(rb)
    fl, rl = dict(_leaves(fj)), dict(_leaves(rj))
    differing = sorted(k for k in set(fl) | set(rl) if fl.get(k, "<absent>") != rl.get(k, "<absent>"))
    rec = dict(
        schema="V77_REPRODUCTION_RECEIPT_V1",
        what=a.what,
        frozen=dict(path=a.frozen, sha256=hashlib.sha256(fb).hexdigest(), bytes=len(fb)),
        reproduced=dict(path=a.reproduced, sha256=hashlib.sha256(rb).hexdigest(), bytes=len(rb)),
        byte_identical=fb == rb,
        parsed_identical=fj == rj,
        n_leaves=len(fl), differing_leaves=differing[:200], n_differing_leaves=len(differing),
        producer_command=a.producer_command,
        source_commit=_git("rev-parse", "HEAD"),
        provenance_status="CLEAN_COMMITTED_HEAD",
        rule="byte identity, decided before the comparison; no tolerance is applied after seeing it")
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    with open(a.out, "w", newline="\n") as fh:
        fh.write(json.dumps(rec, indent=2) + "\n")
    print(json.dumps({k: rec[k] for k in ("what", "byte_identical", "parsed_identical",
                                          "n_leaves", "n_differing_leaves")}, indent=1))


if __name__ == "__main__":
    main()
