#!/usr/bin/env python3
"""Verify the committed perturbation output SHA-256 manifest.

This is an integrity verifier only. It does not authorize biological validation,
training, N1 execution, therapeutic ranking, or any protected outcome access.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def git_blob_sha1(repo_root: Path, path: Path) -> str:
    rel = path.relative_to(repo_root)
    try:
        out = subprocess.check_output(
            ["git", "hash-object", str(rel)], cwd=str(repo_root), text=True
        ).strip()
    except Exception as exc:  # pragma: no cover - environment failure path
        raise SystemExit(f"STOP: could not compute git blob SHA for {rel}: {exc}")
    return out


def verify_manifest(repo_root: Path, manifest_path: Path) -> dict:
    with manifest_path.open("r", encoding="utf-8") as fh:
        manifest = json.load(fh)

    if manifest.get("schema") != "JEPA_PERTURBATION_COMMITTED_OUTPUT_SHA256_V1":
        raise SystemExit("STOP: unsupported manifest schema")
    if manifest.get("biological_validation_authorized") is not False:
        raise SystemExit("STOP: manifest must not authorize biological validation")
    if manifest.get("jepa_training_authorized") is not False:
        raise SystemExit("STOP: manifest must not authorize JEPA training")
    if manifest.get("scope") != "COMMITTED_DEVELOPMENT_BINARIES_ONLY":
        raise SystemExit("STOP: manifest scope drift")

    files = manifest.get("files")
    if not isinstance(files, list) or not files:
        raise SystemExit("STOP: manifest has no files list")

    seen: set[str] = set()
    verified = []
    for idx, rec in enumerate(files):
        path = rec.get("repo_relative_path")
        sha256 = rec.get("sha256")
        git_sha = rec.get("git_blob_sha1")
        expected_bytes = rec.get("exact_bytes")
        if not isinstance(path, str) or not path.startswith(
            "analysis/therapeutic_perturbation_etl/outputs/"
        ):
            raise SystemExit(f"STOP: bad output path at manifest index {idx}: {path!r}")
        if path in seen:
            raise SystemExit(f"STOP: duplicate manifest path {path}")
        seen.add(path)
        if not isinstance(expected_bytes, int) or expected_bytes <= 0:
            raise SystemExit(f"STOP: invalid byte count for {path}")
        if not isinstance(sha256, str) or not HEX64.fullmatch(sha256):
            raise SystemExit(f"STOP: invalid SHA-256 for {path}")
        if not isinstance(git_sha, str) or not HEX40.fullmatch(git_sha):
            raise SystemExit(f"STOP: invalid git blob SHA-1 for {path}")

        abs_path = repo_root / path
        if not abs_path.is_file():
            raise SystemExit(f"STOP: listed output missing: {path}")
        actual_bytes = abs_path.stat().st_size
        actual_sha256 = sha256_file(abs_path)
        actual_git_sha = git_blob_sha1(repo_root, abs_path)
        if actual_bytes != expected_bytes:
            raise SystemExit(
                f"STOP: byte count mismatch for {path}: {actual_bytes} != {expected_bytes}"
            )
        if actual_sha256 != sha256:
            raise SystemExit(f"STOP: SHA-256 mismatch for {path}")
        if actual_git_sha != git_sha:
            raise SystemExit(f"STOP: git blob SHA mismatch for {path}")
        verified.append(path)

    declared_n = manifest.get("n_committed_output_binaries")
    if declared_n != len(verified):
        raise SystemExit(
            f"STOP: declared n_committed_output_binaries={declared_n} but verified {len(verified)}"
        )

    return {"result": "PASS", "verified_files": len(verified), "paths": verified}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo-root", default=".")
    ap.add_argument(
        "--manifest",
        default="analysis/therapeutic_perturbation_etl/evidence/committed_outputs_full_sha256_v1.json",
    )
    args = ap.parse_args()
    repo_root = Path(args.repo_root).resolve()
    manifest_path = (repo_root / args.manifest).resolve()
    result = verify_manifest(repo_root, manifest_path)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
