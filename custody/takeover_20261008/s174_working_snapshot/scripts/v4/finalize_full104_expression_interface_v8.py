#!/usr/bin/env python3
"""Fail-closed staging/package finalizer for FULL104 expression interface V8."""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENVELOPE = ROOT / "outputs/full104_v014_20260826/_staging_full104_expression_interface_v8_retry2"
PACKAGE = ENVELOPE / "FULL104_EXPRESSION_INTERFACE_V8"
MANIFEST = PACKAGE / "FULL104_EXPRESSION_INTERFACE_V8_SHA256_MANIFEST.csv"
ANCHOR = ENVELOPE / "FULL104_EXPRESSION_INTERFACE_V8.PACKAGE_ROOT_SHA256.txt"
CODE_NAMES = [
    "full104_expression_interface_preflight.py",
    "full104_expression_interface_nph_v8.R",
    "full104_expression_interface_consumer.py",
    "full104_production_expression_firewall.py",
    "build_nph_reader_fit_quarantine.R",
    "verify_nph_reader_fit_quarantine.R",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 << 20), b""):
            h.update(block)
    return h.hexdigest()


def copy_code() -> None:
    target = PACKAGE / "code"
    target.mkdir(exist_ok=False)
    rows = []
    for name in CODE_NAMES:
        source = ROOT / "scripts/v4" / name
        dest = target / name
        shutil.copy2(source, dest)
        if sha256(source) != sha256(dest):
            raise RuntimeError(f"code copy mismatch: {name}")
        rows.append({"path": name, "bytes": dest.stat().st_size, "sha256": sha256(dest)})
    with (target / "CODE_COPY_SHA256.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=["path", "bytes", "sha256"], lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_manifest() -> str:
    rows = []
    for path in sorted(PACKAGE.rglob("*"), key=lambda p: p.relative_to(PACKAGE).as_posix()):
        if path.is_file() and path != MANIFEST:
            rows.append({
                "path": path.relative_to(PACKAGE).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            })
    with MANIFEST.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=["path", "bytes", "sha256"], lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    digest = sha256(MANIFEST)
    ANCHOR.write_text(digest + "\n", encoding="ascii")
    return digest


def load_consumer():
    source = PACKAGE / "code/full104_expression_interface_consumer.py"
    spec = importlib.util.spec_from_file_location("frozen_full104_consumer", source)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load frozen consumer")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verify_manifest_complete() -> None:
    rows = list(csv.DictReader(MANIFEST.open("r", newline="", encoding="utf-8-sig")))
    declared = {row["path"] for row in rows}
    actual = {
        path.relative_to(PACKAGE).as_posix()
        for path in PACKAGE.rglob("*")
        if path.is_file() and path != MANIFEST
    }
    if declared != actual or len(declared) != len(rows):
        raise RuntimeError("package manifest coverage mismatch")
    for row in rows:
        path = PACKAGE / row["path"]
        if path.stat().st_size != int(row["bytes"]) or sha256(path) != row["sha256"]:
            raise RuntimeError(f"package manifest mismatch: {row['path']}")
    if sha256(MANIFEST) != ANCHOR.read_text(encoding="ascii").strip():
        raise RuntimeError("external package anchor mismatch")


def prepare() -> None:
    copy_code()
    write_manifest()
    inputs = load_consumer().load_teacher_inputs(PACKAGE)
    selftest = {
        "status": "PASS_FROZEN_CONSUMER_SELFTEST",
        "return_keys": sorted(inputs),
        "shape": list(inputs["normalized_values"].shape),
        "normalized_values_dtype": str(inputs["normalized_values"].dtype),
        "observation_states_dtype": str(inputs["observation_states"].dtype),
        "identity_in_model_input_api": False,
    }
    (PACKAGE / "CONSUMER_SELFTEST.json").write_text(
        json.dumps(selftest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    digest = write_manifest()
    verify_manifest_complete()
    load_consumer().load_teacher_inputs(PACKAGE)
    print(json.dumps({"status": "PASS_PROVISIONAL_PACKAGE", "manifest_sha256": digest}, indent=2))


def seal() -> None:
    status = PACKAGE / "FULL104_EXPRESSION_INTERFACE_V8_STATUS.json"
    required = [
        PACKAGE / "governance/DATASET_FIDELITY_REVIEW.md",
        PACKAGE / "governance/RED_TEAM_REVIEW.md",
        status,
    ]
    if any(not path.is_file() for path in required):
        raise RuntimeError("final reviews/status absent")
    content = json.loads(status.read_text(encoding="utf-8"))
    if content.get("status") != "PASS_FULL104_EXPRESSION_INTERFACE_VERIFIED":
        raise RuntimeError("terminal PASS absent")
    digest = write_manifest()
    verify_manifest_complete()
    load_consumer().load_teacher_inputs(PACKAGE)
    print(json.dumps({"status": content["status"], "manifest_sha256": digest}, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["prepare", "seal"])
    args = parser.parse_args()
    prepare() if args.mode == "prepare" else seal()


if __name__ == "__main__":
    main()
