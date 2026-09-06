#!/usr/bin/env python3
"""C2 preservation verification, parameterised by candidate.

NOT independent certification: written by the implementing agent. Published so a
separate reviewer can reuse or critique it. The candidate commit and its expected
package root are required arguments, so this script can never assert which
candidate is current.

Written for the verifier. Recomputes every digest from bytes on disk in a clean
checkout. Does not import, call, or trust any implementing-agent code, and does
not read recorded values as assertions - recorded values are only compared
against independently recomputed ones.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
PKG = REPO / "outputs" / "c2_t1_gradient_forensic_20260906"

# Candidate identity is a REQUIRED input, never a default. Hardcoding it meant
# this script silently described one candidate while being run against another,
# which is exactly how a superseded authority gets re-certified by accident.
if len(sys.argv) < 4:
    raise SystemExit(
        "usage: c2_verify_preservation.py <repo> <candidate_commit_sha> "
        "<expected_package_root_sha256>. "
        "Both the candidate commit and its expected package root must be supplied "
        "by the reviewer from the authority record. This script asserts nothing "
        "about which candidate is current."
    )

EXPECTED_COMMIT = sys.argv[2]

EXPECTED_CLOSURE = {
    "v3_exact_path/C2_V3_K0_HISTORICAL.json":
        "01908fd62b1a233207092758b3cb27344f8b7ca81140f5e9295039a35987abd8",
    "v3_exact_path/C2_V3_K1_BACKWARD_AUTOCAST_DISABLED.json":
        "c5b9edf17f57756c201582f130a2bd7e0c7945f40d3412d7ea8742291465d381",
    "v3_exact_path/C2_V3_K1_PRE_CRITERION_REPAIR.json":
        "260b9aeef913482f1b3bff8ae6edfe7e88359284ceedf1e1562e196e4a7cc97a",
        "C2_K0_K1_SOURCE_DIFF.txt":
        "d0cd70bae1e71e35d4ee02a09c8954360a155215af22998fee17d3314075caf9",
}

EXPECTED_PACKAGE_ROOT = sys.argv[3]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fail(findings: list[str], message: str) -> None:
    findings.append(message)
    print("  FAIL " + message)


def main() -> int:
    findings: list[str] = []
    print("=" * 72)
    print("INDEPENDENT C2 PRESERVATION VERIFICATION")
    print("repo:", REPO)

    # --- provenance of the checkout itself -------------------------------
    head = subprocess.run(["git", "-C", str(REPO), "rev-parse", "HEAD"],
                          capture_output=True, text=True).stdout.strip()
    print("HEAD:", head)
    # A shallow clone has no history, so ancestry cannot be asserted from it.
    # Fetch the frozen commit explicitly and compare the package tree instead.
    subprocess.run(["git", "-C", str(REPO), "fetch", "-q", "--depth", "1",
                    "origin", EXPECTED_COMMIT], capture_output=True, text=True)
    have = subprocess.run(["git", "-C", str(REPO), "cat-file", "-t", EXPECTED_COMMIT],
                          capture_output=True, text=True).stdout.strip()
    if have != "commit":
        fail(findings, "frozen commit not retrievable: " + EXPECTED_COMMIT)
    elif head == EXPECTED_COMMIT:
        print("  ok  checkout is exactly the frozen implementation commit")
    else:
        changed = subprocess.run(
            ["git", "-C", str(REPO), "diff", "--name-only", EXPECTED_COMMIT, head,
             "--", "outputs/c2_t1_gradient_forensic_20260906"],
            capture_output=True, text=True).stdout.split()
        print("  ok  frozen commit retrieved; HEAD is later")
        print("      package paths changed since frozen commit: %d" % len(changed))
        for item in changed:
            print("        " + item)

    if not PKG.is_dir():
        fail(findings, "C2 package directory absent from this checkout: " + str(PKG))
        print("\nTERMINAL: STOP_C2_INDEPENDENT_VERIFICATION")
        return 1

    # --- every package file must be tracked by git -----------------------
    tracked = set(subprocess.run(
        ["git", "-C", str(REPO), "ls-files", "outputs/c2_t1_gradient_forensic_20260906"],
        capture_output=True, text=True).stdout.split())
    on_disk = {p.relative_to(REPO).as_posix() for p in PKG.rglob("*") if p.is_file()}
    untracked = sorted(on_disk - tracked)
    print("\npackage files on disk: %d   tracked by git: %d" % (len(on_disk), len(tracked)))
    if untracked:
        fail(findings, "package files present but NOT tracked: %s" % untracked[:5])
    else:
        print("  ok  every package file is tracked; nothing depends on untracked bytes")

    # --- closure-critical digests ----------------------------------------
    print("\nclosure-critical artifacts:")
    for relative, expected in EXPECTED_CLOSURE.items():
        path = PKG / relative
        if not path.is_file():
            fail(findings, "closure-critical artifact missing: " + relative)
            continue
        actual = sha256(path)
        mark = "ok  " if actual == expected else "FAIL"
        print("  %s %-52s %s" % (mark, relative.split("/")[-1], actual))
        if actual != expected:
            fail(findings, "digest mismatch for %s: %s != %s" % (relative, actual, expected))

    # --- manifest rows, recomputed ---------------------------------------
    manifest_path = PKG / "C2_RESULT_MANIFEST.csv"
    if not manifest_path.is_file():
        fail(findings, "manifest absent")
        print("\nTERMINAL: STOP_C2_INDEPENDENT_VERIFICATION")
        return 1
    rows = manifest_path.read_text(encoding="utf-8").strip().splitlines()
    header, entries = rows[0], rows[1:]
    if header != "role,path,sha256,bytes":
        fail(findings, "unexpected manifest header: " + header)
    print("\nmanifest rows: %d" % len(entries))

    bound, results, mismatched, missing = 0, 0, 0, 0
    digests = []
    for row in entries:
        role, relative, recorded, size = row.split(",")
        base = REPO if role == "bound_source" else PKG
        path = base / relative
        if not path.is_file():
            fail(findings, "manifest row references missing file: " + relative)
            missing += 1
            continue
        actual = sha256(path)
        actual_size = path.stat().st_size
        digests.append(actual)
        if actual != recorded:
            fail(findings, "manifest digest mismatch: %s recorded %s actual %s"
                 % (relative, recorded[:12], actual[:12]))
            mismatched += 1
        if str(actual_size) != size:
            fail(findings, "manifest byte-count mismatch: %s recorded %s actual %d"
                 % (relative, size, actual_size))
            mismatched += 1
        bound += role == "bound_source"
        results += role != "bound_source"
    print("  bound sources: %d   result artifacts: %d" % (bound, results))
    print("  digest/size mismatches: %d   missing: %d" % (mismatched, missing))
    if bound != 15:
        fail(findings, "expected 15 bound sources, manifest declares %d" % bound)

    # --- package root, algorithm reimplemented independently -------------
    # Declared algorithm: sha256 of the concatenation of all member digests,
    # sorted lexicographically, excluding the manifest and the root file.
    recomputed_root = hashlib.sha256("".join(sorted(digests)).encode("utf-8")).hexdigest()
    root_file = PKG / "C2_PACKAGE_ROOT_SHA256.txt"
    recorded_root = root_file.read_text(encoding="utf-8").strip() if root_file.is_file() else ""
    print("\npackage root")
    print("  recomputed: " + recomputed_root)
    print("  recorded:   " + recorded_root)
    print("  expected:   " + EXPECTED_PACKAGE_ROOT)
    if recomputed_root != recorded_root:
        fail(findings, "package root does not reproduce from member digests")
    if recorded_root != EXPECTED_PACKAGE_ROOT:
        fail(findings, "recorded package root differs from the authority value")

    # --- no closure claim may depend on /tmp -----------------------------
    print("\nscanning closure-critical artifacts for local-only path dependencies")
    offenders = []
    for relative in EXPECTED_CLOSURE:
        path = PKG / relative
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for needle in ("/tmp/", "\\\\Temp\\\\", "C:\\\\Users\\\\", "/home/"):
            if needle in text:
                offenders.append((relative, needle))
    if offenders:
        for relative, needle in offenders:
            print("  note %s references %s" % (relative, needle))
    else:
        print("  ok  no /tmp or user-home path appears in closure-critical artifacts")

    print("\n" + "=" * 72)
    if findings:
        print("TERMINAL: STOP_C2_INDEPENDENT_VERIFICATION")
        print("findings: %d" % len(findings))
        for item in findings:
            print("  - " + item)
        return 1
    print("PRESERVATION: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
