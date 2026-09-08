"""Runtime verification of the exact integrated Teacher/Student V4 source authority.

The execution-binding overlay names a SHA-256 source root. That name is not
trusted on its own: before successor-u0 materialization or any optimizer update,
this module rehashes the V4 manifest and every listed source file from the code
tree that is actually executing.
"""
from __future__ import annotations

import csv
import hashlib
from pathlib import Path
from typing import Any

MANIFEST_REL = Path("docs/agent/TEACHER_STUDENT_INTEGRATED_SOURCE_MANIFEST_V4.csv")
ROOT_REL = Path("docs/agent/TEACHER_STUDENT_INTEGRATED_SOURCE_ROOT_V4.txt")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def repository_root() -> Path:
    return Path(__file__).resolve().parents[3]


def verify_source_authority(
    expected_root_sha256: str,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    expected = str(expected_root_sha256)
    if len(expected) != 64 or any(ch not in "0123456789abcdef" for ch in expected):
        raise RuntimeError("integrated source root is not a SHA-256")
    root = repository_root() if root is None else Path(root).resolve()
    manifest = root / MANIFEST_REL
    root_file = root / ROOT_REL
    if not manifest.is_file() or not root_file.is_file():
        raise RuntimeError("integrated V4 source authority manifest/root missing")

    manifest_sha = sha256_file(manifest)
    recorded = root_file.read_text(encoding="utf-8").strip()
    if manifest_sha != expected or recorded != expected:
        raise RuntimeError(
            "integrated V4 source manifest root mismatch: "
            f"expected={expected} manifest={manifest_sha} recorded={recorded}"
        )

    with manifest.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    paths = [row["path"] for row in rows]
    if not rows or len(paths) != len(set(paths)):
        raise RuntimeError(
            "integrated V4 source manifest is empty or has duplicate paths"
        )

    mismatches: list[str] = []
    for row in rows:
        path = root / row["path"]
        if not path.is_file():
            mismatches.append(row["path"] + ":MISSING")
            continue
        if path.stat().st_size != int(row["bytes"]):
            mismatches.append(row["path"] + ":SIZE")
            continue
        if sha256_file(path) != row["sha256"]:
            mismatches.append(row["path"] + ":SHA256")
    if mismatches:
        raise RuntimeError(
            "executing source bytes do not match integrated V4 authority: "
            + ", ".join(mismatches[:12])
        )

    return {
        "schema": "TEACHER_STUDENT_SOURCE_AUTHORITY_VERIFICATION_V4",
        "manifest_rows": len(rows),
        "source_root_sha256": expected,
        "passed": True,
        "terminal": "PASS_TEACHER_STUDENT_EXECUTING_SOURCE_AUTHORITY_V4",
    }
