#!/usr/bin/env python3
"""Fail-closed local transfer of two small, NON-AUTHORIZING V32 ZIP archives.

Run on the laptop that physically has both archives, from a clean checkout of
handoff/jepa-v32-teacher-stage75-local-evidence-20260926. Does not push or merge.
Requires Python 3.10+, git; run git push explicitly after independent review.
"""
from pathlib import Path
import argparse
import hashlib
import subprocess
import zipfile

FILES = {
    "JEPA_TEACHER_TARGET_V4_NONAUTHORIZING_RESEARCH_PACKAGE_20260926.zip":
        ("349b6ef604084b9c5220f91f9382e6875ce37e34314bf94aa08023725e8f50b4", 29224, 14),
    "STAGE75_PILOT_COVERAGE_AUDIT_20260926.zip":
        ("7cde16dcf1300a1a3012bb4f7b547efa553b48290db45e503d9f5794ae1e9439", 6226, 4),
}
DEST = Path("research/non_authorizing/v32_20260926")
BRANCH = "handoff/jepa-v32-teacher-stage75-local-evidence-20260926"

def git(*args):
    return subprocess.check_output(["git", *args], text=True).strip()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-dir", type=Path, required=True)
    args = ap.parse_args()
    if git("branch", "--show-current") != BRANCH:
        raise SystemExit("Wrong branch; refusing to stage binaries")
    if git("status", "--porcelain"):
        raise SystemExit("Working tree not clean; refusing to stage binaries")
    DEST.mkdir(parents=True, exist_ok=True)
    for name, (expected_sha, expected_size, expected_members) in FILES.items():
        src = args.source_dir / name
        data = src.read_bytes()
        if len(data) != expected_size or hashlib.sha256(data).hexdigest() != expected_sha:
            raise SystemExit(f"FAIL: byte size or SHA-256 mismatch: {src}")
        with zipfile.ZipFile(src) as z:
            if len(z.namelist()) != expected_members or z.testzip() is not None:
                raise SystemExit(f"FAIL: member count or CRC: {src}")
            for member in z.namelist():
                p = Path(member)
                if p.is_absolute() or ".." in p.parts:
                    raise SystemExit(f"FAIL: unsafe ZIP path {member}")
        (DEST / name).write_bytes(data)
        print(f"VERIFIED {name}: {len(data)} bytes {expected_sha}")
    subprocess.check_call(["git", "add", "--", *(str(DEST / n) for n in FILES)])
    print("STAGED ONLY; review git diff --cached --stat; commit and push manually.")
if __name__ == "__main__":
    main()
