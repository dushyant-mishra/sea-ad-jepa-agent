#!/usr/bin/env python3
"""Reproduce the CRISPRbrain screen-reliability result from a clean checkout.

What this script actually does, in order:

1.  Reads the committed receipt and takes the commit it says it ran from.
2.  Creates a git worktree at THAT commit and refuses to continue unless the
    worktree is clean and its HEAD matches.
3.  Checks the producer file's SHA-256 against the digest in the receipt, so a
    different copy of the same filename cannot satisfy the reproduction.
4.  Runs the producer inside the worktree, writing to a scratch directory.
5.  Compares every output CSV byte-for-byte by SHA-256 and every scientific
    field of the receipt value-for-value.
6.  Exits nonzero on any mismatch, and prints exactly which field differed.

Volatile fields (wall-clock time, interpreter version, absolute paths, the
worktree's own HEAD) are excluded from the comparison and are listed in
VOLATILE below, so the exclusion is auditable rather than implicit.

Usage
-----
    python analysis/therapeutic_perturbation_etl/scripts/\
reproduce_crisprbrain_screen_reliability_v1.py --repo .
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_REL = Path("analysis/therapeutic_perturbation_etl")
RECEIPT_REL = REPO_REL / "evidence/crisprbrain_reliability/CRISPRBRAIN_SCREEN_RELIABILITY_RECEIPT_V1.json"
PRODUCER_REL = REPO_REL / "scripts/assess_crisprbrain_screen_reliability_v1.py"

VOLATILE = {
    "generated_utc",
    "environment",
    "git_head",
    "git_dirty",
    "status",
    "outputs",
    "inputs",
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for blk in iter(lambda: fh.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def _git_argv(repo: Path):
    # See the note in the producer: -c safe.directory is supplied per
    # invocation so no global git config is mutated.
    return ["git", "-c", "safe.directory=%s" % Path(repo).as_posix(), "-C", str(repo)]


def git(repo: Path, *args: str) -> str:
    return subprocess.check_output(_git_argv(repo) + list(args), text=True).strip()


def flatten(obj, prefix=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            for item in flatten(v, prefix + "/" + str(k)):
                yield item
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            for item in flatten(v, prefix + "/" + str(i)):
                yield item
    else:
        yield prefix, obj


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--keep", action="store_true", help="keep the worktree for inspection")
    ap.add_argument(
        "--scratch",
        default=None,
        help="directory to build the worktree in.  Defaults to a sibling of the "
        "repository, because git refuses to operate on a worktree that lives on "
        "a filesystem which does not record ownership (a cross-drive temp dir on "
        "Windows).  This is a placement fix only; the method is unchanged.",
    )
    args = ap.parse_args()
    repo = Path(args.repo).resolve()

    receipt_path = repo / RECEIPT_REL
    if not receipt_path.is_file():
        print("FAIL: no committed receipt at %s" % RECEIPT_REL)
        return 2
    committed = json.loads(receipt_path.read_text(encoding="utf-8"))
    anchor = committed.get("git_head", "")
    if not anchor or not all(c in "0123456789abcdef" for c in anchor):
        print("FAIL: receipt does not name a commit it ran from (git_head=%r)" % anchor)
        return 2
    if committed.get("git_dirty") is not False:
        print(
            "FAIL: the receipt records git_dirty=%r.  A result produced from a "
            "dirty tree cannot be anchored to a commit and must be re-run from a "
            "clean one." % committed.get("git_dirty")
        )
        return 2

    scratch_root = Path(args.scratch).resolve() if args.scratch else repo.parent
    scratch_root.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix="crb_repro_", dir=str(scratch_root)))
    wt = tmp / "wt"
    out = tmp / "out"
    failures = []
    try:
        print("anchor commit          : %s" % anchor)
        subprocess.check_call(
            _git_argv(repo) + ["worktree", "add", "--detach", str(wt), anchor],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT,
        )
        head = git(wt, "rev-parse", "HEAD")
        dirty = git(wt, "status", "--porcelain")
        print("worktree HEAD          : %s" % head)
        print("worktree clean         : %s" % (not dirty))
        if head != anchor:
            failures.append("worktree HEAD %s != anchor %s" % (head, anchor))
        if dirty:
            failures.append("worktree is not clean: %s" % dirty.splitlines()[:3])

        prod = wt / PRODUCER_REL
        if not prod.is_file():
            failures.append("producer absent at the anchor commit: %s" % PRODUCER_REL)
        else:
            got = sha256_file(prod)
            want = committed.get("producer_sha256", "")
            print("producer sha256        : %s" % got)
            if want and got != want:
                failures.append("producer digest %s != receipt %s" % (got, want))
        if failures:
            for f in failures:
                print("FAIL: %s" % f)
            return 1

        out.mkdir(parents=True, exist_ok=True)
        print("running producer ...")
        rc = subprocess.call(
            [sys.executable, str(prod), "--repo", str(wt), "--out", str(out)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT,
        )
        if rc != 0:
            print("FAIL: producer exited %d in the clean worktree" % rc)
            return 1

        fresh = json.loads(
            (out / "CRISPRBRAIN_SCREEN_RELIABILITY_RECEIPT_V1.json").read_text(
                encoding="utf-8"
            )
        )

        # 1. every output CSV must be byte-identical
        for rec in committed.get("outputs", []):
            name = Path(rec["path"]).name
            p = out / name
            if not p.is_file():
                failures.append("output missing in replay: %s" % name)
                continue
            got = sha256_file(p)
            if got != rec["sha256"]:
                failures.append(
                    "output %s digest %s != committed %s" % (name, got, rec["sha256"])
                )

        # 2. every scientific field must match exactly
        a = dict(flatten({k: v for k, v in committed.items() if k not in VOLATILE}))
        b = dict(flatten({k: v for k, v in fresh.items() if k not in VOLATILE}))
        for key in sorted(set(a) | set(b)):
            if key not in a:
                failures.append("field only in replay: %s = %r" % (key, b[key]))
            elif key not in b:
                failures.append("field only in committed receipt: %s = %r" % (key, a[key]))
            elif a[key] != b[key]:
                failures.append("field differs: %s  committed=%r  replay=%r" % (key, a[key], b[key]))

        print("output files compared  : %d" % len(committed.get("outputs", [])))
        print("receipt fields compared: %d" % len(set(a) | set(b)))
        if failures:
            print("\nREPRODUCTION FAILED, %d difference(s):" % len(failures))
            for f in failures[:40]:
                print("  - %s" % f)
            return 1
        print("\nREPRODUCTION OK: every output digest and every scientific field matched.")
        return 0
    finally:
        if not args.keep:
            subprocess.call(
                _git_argv(repo) + ["worktree", "remove", "--force", str(wt)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.STDOUT,
            )
            shutil.rmtree(tmp, ignore_errors=True)
        else:
            print("worktree kept at %s" % wt)


if __name__ == "__main__":
    raise SystemExit(main())
