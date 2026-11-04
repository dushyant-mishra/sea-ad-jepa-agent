"""Prepare a strict V2C-only Docker build context pinned to reviewed source bytes.

This is an author-only deployment experiment, not a source-rights issuer or an
independent validation. The historical original #514 blob remains unchanged;
this V9 branch re-pins the candidate new source. Never give Docker the full repo.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "scripts/v5/td_unified/observation_v2c_standalone_student_gate_v1.py"
HERE = Path(__file__).resolve().parent
EXPECTED_BLOB = "3470ad2ad17f7cea72b9238f7b7f675a27614b70"
SCHEMA = "JEPA_STUDENT_V2C_ISOLATED_BUILD_CONTEXT_V1"
FILES = {
    "student_v2c.py": SOURCE,
    "entrypoint.py": HERE / "entrypoint_v1.py",
    "Dockerfile": HERE / "Dockerfile.v1",
}


def git_blob_sha1(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\x00" + raw).hexdigest()


def produce_context(out: Path) -> dict:
    if out.exists() and any(out.iterdir()):
        raise ValueError("build context must be absent or empty")
    raw = SOURCE.read_bytes()
    if git_blob_sha1(raw) != EXPECTED_BLOB:
        raise ValueError("V2C verifier bytes differ from exact V9 source pin")
    out.mkdir(parents=True, exist_ok=True)
    evidence = {}
    for name, source in FILES.items():
        data = raw if name == "student_v2c.py" else source.read_bytes()
        (out / name).write_bytes(data)
        evidence[name] = hashlib.sha256(data).hexdigest()
    manifest = {
        "schema": SCHEMA,
        "source_pr": 538,
        "historical_source_pr": 514,
        "source_blob_sha1": EXPECTED_BLOB,
        "student_verifier_sha256": evidence["student_v2c.py"],
        "build_context_files_sha256": evidence,
        "production_source_rights_issuer_authenticated": False,
        "student_deployment_independently_accepted": False,
        "real_training_authorized": False,
        "authority_effect": "NONE",
    }
    (out / "manifest.json").write_text(
        json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    if {p.name for p in out.iterdir()} != set(FILES) | {"manifest.json"}:
        raise ValueError("unexpected file in isolated build context")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(produce_context(args.out), sort_keys=True))
