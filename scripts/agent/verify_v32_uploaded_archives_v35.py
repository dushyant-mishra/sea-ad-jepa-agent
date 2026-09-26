#!/usr/bin/env python3
"""Independently re-read V32 ZIPs committed to GitHub and replay bounded V4 tests.

NON-AUTHORIZING: never reads protected outcomes or remote heavy data.
Requires only repository checkout, Python, numpy/scipy/scikit-learn for V4 tests.
The ORIGINAL sha256 and git blob hashes are exact approved transfer receipts.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import stat
import subprocess
import sys
import tempfile
import unittest
import zipfile

DIR = Path(__file__).resolve().parents[2] / "docs/agent/v32-downloads"
V4 = "JEPA_TEACHER_TARGET_V4_NONAUTHORIZING_RESEARCH_PACKAGE_20260926.zip"
STAGE = "STAGE75_PILOT_COVERAGE_AUDIT_20260926.zip"
COMPLETE = "JEPA_V32_COMPLETE_LOCAL_EVIDENCE_AND_HANDOFF_20260926.zip"
EXPECTED = {
    COMPLETE: (36717, "d49c7a1bba1e48f21fdf8fceb92e8c1176a3c309c2c662249099d6c109b5dc79", "d5433975def9fc51551be3f608948b3a1809a999", 5),
    V4: (29224, "349b6ef604084b9c5220f91f9382e6875ce37e34314bf94aa08023725e8f50b4", "d38a446ca365c53a806f9d05645053737b5da7aa", 14),
    STAGE: (6226, "7cde16dcf1300a1a3012bb4f7b547efa553b48290db45e503d9f5794ae1e9439", "ec2be3cef08af4bf887a9286cbabefb3b2b53f29", 4),
}
V4_TEST_FILES = {
    "teacher_target_raw_adapter_v3.py",
    "teacher_target_visible_only_adapter_v4.py",
    "test_teacher_target_raw_adapter_v3.py",
    "test_teacher_target_visible_only_adapter_v4.py",
}


def check_zip(raw: bytes, name: str, count: int) -> zipfile.ZipFile:
    z = zipfile.ZipFile(io.BytesIO(raw), mode="r")
    members = z.infolist()
    if len(members) != count:
        raise AssertionError(f"{name}: ZIP entry count {len(members)} != {count}")
    names = [m.filename for m in members]
    if len(names) != len(set(names)):
        raise AssertionError(f"{name}: duplicate ZIP member name")
    for m in members:
        path = PurePosixPath(m.filename.replace("\\", "/"))
        if (path.is_absolute() or ".." in path.parts or
            ":" in path.parts[0] or m.filename.startswith(("\\", "/"))):
            raise AssertionError(f"{name}: unsafe member path {m.filename}")
        mode = m.external_attr >> 16
        if stat.S_IFMT(mode) == stat.S_IFLNK:
            raise AssertionError(f"{name}: ZIP symlink {m.filename}")
        if m.is_dir():
            raise AssertionError(f"{name}: unexpected directory {m.filename}")
    if z.testzip() is not None:
        raise AssertionError(f"{name}: ZIP CRC failed")
    return z


def main() -> None:
    archives = {}
    for name, (size, sha256, gitsha, n) in EXPECTED.items():
        file = DIR / name
        raw = file.read_bytes()
        if len(raw) != size:
            raise AssertionError(f"{name}: wrong exact byte size")
        if hashlib.sha256(raw).hexdigest() != sha256:
            raise AssertionError(f"{name}: SHA256 mismatch")
        blob = subprocess.check_output(["git", "hash-object", str(file)], text=True).strip()
        if blob != gitsha:
            raise AssertionError(f"{name}: git blob identity mismatch")
        archives[name] = check_zip(raw, name, n)
        print(f"VERIFIED_GITHUB_ARCHIVE {name} {size} bytes {sha256}", flush=True)

    # Independently re-read the nested binaries, not just the outer manifest.
    outer = archives[COMPLETE]
    for name in (V4, STAGE):
        original = (DIR / name).read_bytes()
        if outer.read(name) != original:
            raise AssertionError(f"combined handoff nested bytes differ: {name}")
    print("COMBINED_TRANSFER_EXACT_NESTED_BYTE_PARITY_PASS", flush=True)

    v4zip = archives[V4]
    if not V4_TEST_FILES.issubset(set(v4zip.namelist())):
        raise AssertionError("V4 package missing required adapter or test file")
    # Run only the bounded tests that need no original large expression archives.
    with tempfile.TemporaryDirectory(prefix="v35_v4_replay_") as tmp:
        temp = Path(tmp)
        for name in V4_TEST_FILES:
            (temp / name).write_bytes(v4zip.read(name))
        # Compilation detects truncation and invalid source encoding.
        for path in temp.glob("*.py"):
            compile(path.read_bytes(), str(path), "exec")
        sys.path.insert(0, str(temp))
        suite = unittest.defaultTestLoader.loadTestsFromNames([
            "test_teacher_target_raw_adapter_v3",
            "test_teacher_target_visible_only_adapter_v4",
        ])
        if suite.countTestCases() != 15:
            raise AssertionError(f"expected exactly 15 authentic V4 tests; found {suite.countTestCases()}")
        result = unittest.TextTestRunner(verbosity=2).run(suite)
        if (not result.wasSuccessful() or result.testsRun != 15 or
            result.skipped or result.expectedFailures or result.unexpectedSuccesses):
            raise AssertionError("V4 test suite not 15 exact passing, zero skips/XFAIL")
    print("V4_UPLOADED_SOURCE_15_OF_15_PASS_NONAUTHORIZING", flush=True)

    stage = archives[STAGE]
    for name in ("README.md", "audit_stage75_pilot.py",
                 "stage75_pilot_coverage_summary.json",
                 "stage75_pilot_historical_registry_crosswalk.csv"):
        if name not in stage.namelist():
            raise AssertionError(f"Stage75 ZIP missing {name}")
    compile(stage.read("audit_stage75_pilot.py"), "audit_stage75_pilot.py", "exec")
    report = json.loads(stage.read("stage75_pilot_coverage_summary.json"))
    rows = list(csv.DictReader(io.StringIO(stage.read(
        "stage75_pilot_historical_registry_crosswalk.csv").decode("utf-8"))))
    if not isinstance(report, dict) or len(rows) < 33:
        raise AssertionError("Stage75 historical summary/crosswalk malformed")
    text = stage.read("stage75_pilot_historical_registry_crosswalk.csv").decode("utf-8")
    if not all(label in text for label in ("HLA-DPA1", "HLA-DPB1")):
        raise AssertionError("Stage75 ambiguity records missing")
    print(f"STAGE75_UPLOADED_RESULTS_PARSABLE rows={len(rows)}; "
          "historic registry not independently replayed in CI", flush=True)
    print("NO_TRAINING_AUTHORITY__NO_PROTECTED_OUTCOMES__NO_FULL104_EXECUTION", flush=True)


if __name__ == "__main__":
    main()
