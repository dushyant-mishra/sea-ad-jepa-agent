"""Verify, then regenerate, the FULL104 pass1 rebuild evidence SHA-256 manifest.

Two phases, in this order, because regeneration must never be able to paper over
a mismatch:

**Phase 1 -- VERIFY.** Every existing row whose ``location`` is ``repository`` is
checked against disk on three independent conditions: the file exists, its byte
count equals the recorded byte count, and its SHA-256 equals the recorded digest.
Any single failure on any row aborts the run with a non-zero exit status and the
manifest is left untouched. Rows marked ``GPU_MACHINE_NOT_COMMITTED`` name
artifacts too large to commit; they are verified opportunistically when the path
is reachable on this machine and reported as ``UNREACHABLE_HERE`` otherwise,
which is not a failure.

**Phase 2 -- REGENERATE.** Only if phase 1 recorded zero mismatches, the manifest
is rewritten to cover every file currently under the rebuild directory, carrying
the external rows through unchanged.

Usage::

    python verify_and_regenerate_evidence_manifest_20260920.py            # verify only
    python verify_and_regenerate_evidence_manifest_20260920.py --write    # verify, then rewrite

Nothing here opens a terminal masking outcome, target-panel ladder,
null-equivalence margin, D_shared, protected/pathology/DEV/SEALED data, or
training.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import sys
from pathlib import Path

REBUILD_DIR = Path("analysis/v5_full104_pass1_rebuild_20260920")
MANIFEST = REBUILD_DIR / "CLAUDE_FULL104_PASS1_REBUILD_EVIDENCE_SHA256.csv"
FIELDS = ("path", "bytes", "sha256", "location")

REPOSITORY = "repository"
EXTERNAL = "GPU_MACHINE_NOT_COMMITTED"


def sha256_file(path: Path) -> tuple[str, int]:
    """Return (hex digest, byte count) read in one pass."""
    h = hashlib.sha256()
    total = 0
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 22), b""):
            h.update(chunk)
            total += len(chunk)
    return h.hexdigest(), total


#: Recorded-digest prefix for a directory row. The value after ``=`` is the
#: SHA-256 of the directory's block manifest, NOT an aggregate digest over the
#: directory's contents.
#:
#: What such a row authenticates, exactly:
#:   * the total byte count of the tree, and
#:   * the SHA-256 of PHASE2_EXPRESSION_BLOCK_MANIFEST.csv inside it.
#: It does NOT content-address every file in the directory. The block manifest
#: in turn records per-block paths that the shakedown verifies at read time;
#: that chain is what binds the contents, and it is a separate check from this
#: one. Do not describe a row of this shape as a directory checksum.
DIRECTORY_PREFIX = "DIRECTORY__manifest="
BLOCK_MANIFEST_NAME = "PHASE2_EXPRESSION_BLOCK_MANIFEST.csv"


def measure_tree(root: Path) -> tuple[int, int]:
    """Return (file count, total bytes) for a directory, without hashing contents."""
    count = 0
    total = 0
    for path in root.rglob("*"):
        if path.is_file():
            count += 1
            total += path.stat().st_size
    return count, total


def verify(rows: list[dict]) -> tuple[list[str], list[str]]:
    """Check every row. Returns (failures, notes)."""
    failures: list[str] = []
    notes: list[str] = []
    print(f"  {'state':<18} {'bytes':>13}  path")
    print("  " + "-" * 92)
    for row in rows:
        path = Path(row["path"])
        recorded_bytes = int(row["bytes"])
        recorded_sha = row["sha256"].strip().lower()
        external = row["location"] != REPOSITORY

        if not path.exists():
            state = "UNREACHABLE_HERE" if external else "MISSING"
            if external:
                notes.append(f"{row['path']}: not present on this machine")
            else:
                failures.append(f"{row['path']}: file does not exist")
            print(f"  {state:<18} {'-':>13}  {row['path']}")
            continue

        problems = []
        if path.is_dir():
            if not row["sha256"].startswith(DIRECTORY_PREFIX):
                failures.append(
                    f"{row['path']}: is a directory but its digest is not recorded "
                    f"as {DIRECTORY_PREFIX}<sha>"
                )
                print(f"  {'BAD_ROW_SHAPE':<18} {'-':>13}  {row['path']}")
                continue
            expected_manifest = row["sha256"][len(DIRECTORY_PREFIX):].strip().lower()
            count, size = measure_tree(path)
            detail = f"{count} files; block manifest authenticated"
            block_manifest = path / BLOCK_MANIFEST_NAME
            if not block_manifest.is_file():
                problems.append(f"{BLOCK_MANIFEST_NAME} absent")
            else:
                digest, _ = sha256_file(block_manifest)
                if digest != expected_manifest:
                    problems.append(
                        f"{BLOCK_MANIFEST_NAME} sha256 {digest} != recorded {expected_manifest}"
                    )
        else:
            digest, size = sha256_file(path)
            detail = ""
            if digest != recorded_sha:
                problems.append(f"sha256 {digest} != recorded {recorded_sha}")

        if size != recorded_bytes:
            problems.append(f"byte count {size} != recorded {recorded_bytes}")

        if problems:
            failures.append(f"{row['path']}: " + "; ".join(problems))
            state = "MISMATCH"
        else:
            state = "VERIFIED" if not external else "VERIFIED_EXTERNAL"
        print(f"  {state:<18} {size:>13,}  {row['path']} {detail}")
    return failures, notes


def regenerate(rows: list[dict], include: list[str] | None = None) -> list[dict]:
    """Rebuild repository rows from the current tree; carry external rows through."""
    external = [r for r in rows if r["location"] != REPOSITORY]
    external_paths = {r["path"] for r in external}

    # Repository rows recorded outside the rebuild directory are kept and re-hashed;
    # dropping them would silently narrow the manifest.
    outside = [
        r for r in rows
        if r["location"] == REPOSITORY and not Path(r["path"]).is_relative_to(REBUILD_DIR)
    ]
    known = {r["path"] for r in outside}
    for extra in include or []:
        rel = extra.replace("\\", "/")
        if rel not in known:
            outside.append({"path": rel, "bytes": "0", "sha256": "", "location": REPOSITORY})
            known.add(rel)

    fresh: list[dict] = []
    for path in sorted(p for p in REBUILD_DIR.rglob("*") if p.is_file()):
        rel = path.as_posix()
        if rel == MANIFEST.as_posix() or rel in external_paths:
            continue  # a manifest cannot contain its own digest
        digest, size = sha256_file(path)
        fresh.append({"path": rel, "bytes": str(size), "sha256": digest, "location": REPOSITORY})

    for row in outside:
        path = Path(row["path"])
        if not path.exists():
            raise SystemExit(f"cannot regenerate: {row['path']} is recorded but absent")
        digest, size = sha256_file(path)
        fresh.append({"path": path.as_posix(), "bytes": str(size), "sha256": digest,
                      "location": REPOSITORY})

    fresh.sort(key=lambda r: r["path"])
    return fresh + sorted(external, key=lambda r: r["path"])


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--write", action="store_true",
                    help="rewrite the manifest after a clean verification")
    ap.add_argument("--accept-changed", action="append", default=[], metavar="PATH",
                    help="acknowledge that PATH was deliberately changed this session, so its "
                         "recorded digest is stale rather than wrong. Each path must be named "
                         "explicitly; there is no blanket override, and a path that is named but "
                         "did not actually change is itself an error.")
    ap.add_argument("--include", action="append", default=[], metavar="PATH",
                    help="add a repository file outside the rebuild directory to the manifest")
    args = ap.parse_args()

    if not MANIFEST.is_file():
        raise SystemExit(f"manifest not found at {MANIFEST}; run from the worktree root")

    rows = list(csv.DictReader(MANIFEST.open(newline="", encoding="utf-8")))
    print("=" * 96)
    print(f"PHASE 1 -- VERIFY  ({len(rows)} recorded rows)")
    print("=" * 96)
    failures, notes = verify(rows)

    print()
    repo = sum(1 for r in rows if r["location"] == REPOSITORY)
    print(f"  repository rows           : {repo}")
    print(f"  external rows             : {len(rows) - repo}  ({EXTERNAL})")
    print(f"  mismatches                : {len(failures)}")
    for f in failures:
        print("    FAIL:", f)
    for n in notes:
        print("    note:", n)

    accepted = {p.replace("\\", "/") for p in args.accept_changed}
    if accepted:
        unaccounted = []
        matched = set()
        for failure in failures:
            path = failure.split(":", 1)[0]
            if path in accepted:
                matched.add(path)
            else:
                unaccounted.append(failure)
        for path in sorted(accepted - matched):
            unaccounted.append(
                f"{path}: named with --accept-changed but its recorded digest verified, "
                "or it is not a failing row"
            )
        if matched:
            print()
            for path in sorted(matched):
                print("    ACCEPTED_AS_DELIBERATELY_CHANGED:", path)
        failures = unaccounted

    if failures:
        print("\n  VERIFICATION FAILED -- manifest left untouched.")
        for f in failures:
            print("    ", f)
        return 1
    print("\n  VERIFICATION PASSED -- zero unexplained mismatches on any repository row.")

    if not args.write:
        print("  (--write not given; manifest not regenerated)")
        return 0

    print()
    print("=" * 96)
    print("PHASE 2 -- REGENERATE")
    print("=" * 96)
    fresh = regenerate(rows, args.include)
    before = {r["path"] for r in rows}
    after = {r["path"] for r in fresh}
    for path in sorted(after - before):
        print("  ADDED   ", path)
    for path in sorted(before - after):
        print("  REMOVED ", path)
    changed = [r for r in fresh
               if r["path"] in before
               and r["sha256"] != next(x["sha256"] for x in rows if x["path"] == r["path"])]
    for row in changed:
        print("  UPDATED ", row["path"])

    with MANIFEST.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(fresh)
    print(f"\n  wrote {len(fresh)} rows to {MANIFEST}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
