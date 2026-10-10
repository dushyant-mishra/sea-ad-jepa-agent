#!/usr/bin/env python3
"""Shared fail-closed custody gates for future TD G6/G7 standalone V2.

THIS MODULE DOES NOT AUTHORIZE A VALUE READ.

It validates only already-created evidence objects. A runtime authorization object is not created by
this code and must not exist until a separate owner decision after reviewed V3 G4/G5 PASS evidence.
"""
from __future__ import annotations

import hashlib
import json
import math
import subprocess
from pathlib import Path

PREFLIGHT_SCHEMA = "JEPA_TD_RELATIONAL_PREFLIGHT_DRIVER_RECEIPT_V3"
MAPPING_SCHEMA = "JEPA_TD_RELATIONAL_MAPPING_PREFLIGHT_V3"
PREFLIGHT_PASS = "PASS_TD_RELATIONAL_PREFLIGHT_DRIVER_VALUE_BLIND"

VALUE_AUTH_SCHEMA = "JEPA_TD_RELATIONAL_VALUE_READ_AUTHORIZATION_V2"
VALUE_AUTHORIZATION = "AUTHORIZE_EXACT_TD_SAMPLE_A_9216_CORRECTED_VALUE_MATERIALIZATION_V2_ONLY"
VALUE_SCOPE = (
    "TRAIN-only historical A_NATURAL_MIXTURE 25000 cells; exact frozen 9216 TD56-TD59 addresses; "
    "HVS/SEA corrected physical-ID reads on exact Sample-A matrices; NPH52 authenticated historical "
    "clean-path pass-through; G6/G7 integrity only; no corrected TD biological replay, target selection, "
    "TD60, model fitting, EMA, training, TEST, DEV/SEALED, pathology, or external biology"
)

COMMON_ENTRYPOINT = "scripts/v5/td_relational_value_read_v2_common.py"
G6_ENTRYPOINT = "scripts/v5/materialize_td_relational_corrected_sampleA_v2.py"
G7_ENTRYPOINT = "scripts/v5/audit_td_relational_g7_s174_overlap_v2.py"

EXPECTED_INPUT_HASHES = {
    "sample_freeze_sha256": "79eb005c719788119d9c3021e211148d34198301a59393707c9a2dc88dcef9a6",
    "provenance_sha256": "df0cb60f2308c08adaeacb1db5d1099c9cd12e90323af8e3958c428d6869cd51",
    "collision_ledger_sha256": "f6909f81a2e73383b4346f8cf6d8b3ecfc282f81bfb42d695c6d6896b6c74722",
    "calibration_zip_sha256": "07748d5bd21fe0857ccad3002fba3946d1791d25898b841d41056a3707117444",
    "td_artifacts_zip_sha256": "c84849f5568f5260ac80b7c53e8af34f8bdad03fdbc16e0e8b29e7663dcf2417",
    "macha_freeze_sha256": "240b2b71a94802477ca726a2b4bb020d2ad5542ccf31c4e732906008f81e967c",
    "replay_manifest_sha256": "4bde5f8041394410bf81e9c7c7edbf8553767a87bb31956f0b47bb50026f7660",
}

REQUIRED_MAPPING_CHECKS = (
    "sample_A_h5_matrix_count_exact_34",
    "all_sample_A_h5_matrices_present",
    "frozen_h5_matrix_count_exact_35",
    "all_35_h5_source_sha256_verified",
    "all_9216_addresses_one_to_one",
    "all_sample_A_h5_cell_rows_exact",
    "source_files_exactly_hash_bound",
    "count_arrays_never_opened_by_design",
)

EXPECTED_SAMPLE_A_CONTRACT = {
    "label": "A_NATURAL_MIXTURE",
    "cells": 25_000,
    "source_counts": {"HVS": 1_129, "NPH52": 1_310, "SEA_AD": 22_561},
    "h5_matrices": 34,
}
EXPECTED_SUBSTRATE_CONTRACT = {
    "frozen_h5_matrices": 35,
    "all_frozen_h5_bytes_must_authenticate": True,
}


def sha256_file(path: Path, chunk: int = 8 << 20) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(chunk), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_text_sha256(path: Path) -> str:
    """Hash executable text with newline normalization so CRLF/LF checkout policy cannot change identity."""
    raw = Path(path).read_bytes()
    canonical = raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(canonical).hexdigest()


def _git_root(path: Path) -> Path:
    try:
        root = subprocess.check_output(
            ["git", "-C", str(Path(path).resolve().parent), "rev-parse", "--show-toplevel"],
            stderr=subprocess.STDOUT,
            text=True,
        ).strip()
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f"cannot resolve implementation git root: {exc.output}") from exc
    return Path(root).resolve()


def git_commit_sha(path: Path) -> str:
    """Bind execution to the exact repository commit containing the candidate code."""
    root = _git_root(path)
    try:
        commit = subprocess.check_output(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            stderr=subprocess.STDOUT,
            text=True,
        ).strip()
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f"cannot resolve implementation git commit: {exc.output}") from exc
    if len(commit) != 40:
        raise RuntimeError(f"invalid implementation git commit SHA: {commit!r}")
    return commit


def require_git_clean_path(path: Path) -> None:
    """Reject tracked-code drift while tolerating Git's configured newline clean filters."""
    path = Path(path).resolve()
    root = _git_root(path)
    try:
        relative = path.relative_to(root).as_posix()
    except ValueError as exc:
        raise RuntimeError(f"controlling script is outside repository root: {path}") from exc
    result = subprocess.run(
        ["git", "-C", str(root), "diff", "--quiet", "HEAD", "--", relative],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.returncode == 1:
        raise RuntimeError(f"controlling script has uncommitted drift: {relative}")
    if result.returncode != 0:
        raise RuntimeError(f"cannot verify controlling script cleanliness: {relative}: {result.stderr}")
    tracked = subprocess.run(
        ["git", "-C", str(root), "ls-files", "--error-unmatch", "--", relative],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if tracked.returncode != 0:
        raise RuntimeError(f"controlling script is not tracked at implementation commit: {relative}")


def code_identity(g6_path: Path, g7_path: Path) -> dict[str, str]:
    """Return platform-stable identity for every local code surface controlling the value boundary."""
    common_path = Path(__file__).resolve()
    g6_path = Path(g6_path).resolve()
    g7_path = Path(g7_path).resolve()
    for path in (common_path, g6_path, g7_path):
        require_git_clean_path(path)
    commits = {git_commit_sha(common_path), git_commit_sha(g6_path), git_commit_sha(g7_path)}
    if len(commits) != 1:
        raise RuntimeError(f"G6/G7/common code are not from one implementation commit: {sorted(commits)}")
    return {
        "implementation_commit_sha": next(iter(commits)),
        "common_script_sha256": canonical_text_sha256(common_path),
        "g6_script_sha256": canonical_text_sha256(g6_path),
        "g7_script_sha256": canonical_text_sha256(g7_path),
        "common_entrypoint": COMMON_ENTRYPOINT,
        "g6_entrypoint": G6_ENTRYPOINT,
        "g7_entrypoint": G7_ENTRYPOINT,
    }


def _read_json(path: Path, label: str) -> dict:
    path = Path(path)
    if not path.is_file():
        raise RuntimeError(f"missing {label}: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise RuntimeError(f"invalid {label} JSON: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise RuntimeError(f"invalid {label}: top level must be an object")
    return value


def _require_false(rec: dict, key: str, label: str) -> None:
    if rec.get(key) is not False:
        raise RuntimeError(f"{label} must explicitly keep {key}=false")


def load_runtime_authorization(
    path: Path,
    *,
    preflight_path: Path,
    mapping_path: Path,
    g6_path: Path,
    g7_path: Path,
) -> dict:
    """Validate a separately created V2 authority against exact evidence and platform-stable code identity."""
    rec = _read_json(path, "runtime value authorization")
    if rec.get("schema") != VALUE_AUTH_SCHEMA:
        raise RuntimeError("value authorization schema mismatch")
    if rec.get("authorization") != VALUE_AUTHORIZATION:
        raise RuntimeError("value authorization token mismatch")
    if rec.get("scope") != VALUE_SCOPE:
        raise RuntimeError("value authorization scope mismatch")

    for key, label in (
        ("training_authorized", "training authority"),
        ("biological_replay_authorized", "biological replay authority"),
        ("target_selection_authorized", "target-selection authority"),
        ("td60_authorized", "TD60 authority"),
    ):
        _require_false(rec, key, label)

    expected = {
        "preflight_result_sha256": sha256_file(Path(preflight_path)),
        "mapping_receipt_sha256": sha256_file(Path(mapping_path)),
        **code_identity(Path(g6_path), Path(g7_path)),
    }
    for key, actual in expected.items():
        if rec.get(key) != actual:
            if key.endswith("sha256"):
                raise RuntimeError(f"runtime authorization {key} SHA binding mismatch")
            if key.endswith("entrypoint"):
                raise RuntimeError(f"runtime authorization entrypoint binding mismatch: {key}")
            if key == "implementation_commit_sha":
                raise RuntimeError("runtime authorization implementation commit binding mismatch")
            raise RuntimeError(f"runtime authorization binding mismatch: {key}")
    return rec


def _validate_mapping_receipt(mapping: dict) -> None:
    if mapping.get("schema") != MAPPING_SCHEMA:
        raise RuntimeError("mapping schema mismatch")
    if mapping.get("status") != PREFLIGHT_PASS:
        raise RuntimeError(f"mapping preflight is not PASS: {mapping.get('status')}")
    if mapping.get("sample_A_contract") != EXPECTED_SAMPLE_A_CONTRACT:
        raise RuntimeError("Sample-A V3 contract mismatch; require A_NATURAL_MIXTURE / 25000 / exact source counts / 34 H5 matrices")
    if mapping.get("substrate_custody_contract") != EXPECTED_SUBSTRATE_CONTRACT:
        raise RuntimeError("substrate custody V3 contract mismatch; require exact 35 frozen H5 matrices")
    checks = mapping.get("checks")
    if not isinstance(checks, dict):
        raise RuntimeError("mapping checks missing")
    missing_or_false = [key for key in REQUIRED_MAPPING_CHECKS if checks.get(key) is not True]
    if missing_or_false:
        raise RuntimeError(f"required V3 mapping check missing/false: {missing_or_false}")
    _require_false(mapping, "training_authorized", "mapping receipt")
    _require_false(mapping, "real_value_replay_authorized_by_this_receipt", "mapping receipt")


def load_bound_preflight(
    preflight_path: Path,
    mapping_path: Path,
    *,
    expected_preflight_sha: str,
    expected_mapping_sha: str,
) -> tuple[dict, dict]:
    """Validate exact V3 PASS evidence by bytes and semantics; reject old/pass-only JSON."""
    preflight_path = Path(preflight_path)
    mapping_path = Path(mapping_path)
    if sha256_file(preflight_path) != expected_preflight_sha:
        raise RuntimeError("preflight receipt SHA mismatch")
    if sha256_file(mapping_path) != expected_mapping_sha:
        raise RuntimeError("mapping receipt SHA mismatch")

    mapping = _read_json(mapping_path, "V3 mapping receipt")
    _validate_mapping_receipt(mapping)

    preflight = _read_json(preflight_path, "V3 preflight receipt")
    if preflight.get("schema") != PREFLIGHT_SCHEMA:
        raise RuntimeError("preflight schema mismatch")
    if preflight.get("status") != PREFLIGHT_PASS:
        raise RuntimeError(f"value-blind preflight is not PASS: {preflight.get('status')}")
    _require_false(preflight, "real_value_replay_authorized", "preflight receipt")
    _require_false(preflight, "training_authorized", "preflight receipt")

    inputs = preflight.get("inputs")
    if not isinstance(inputs, dict):
        raise RuntimeError("preflight inputs missing")
    for key, expected in EXPECTED_INPUT_HASHES.items():
        if inputs.get(key) != expected:
            raise RuntimeError(f"preflight frozen input hash mismatch: {key}")

    if preflight.get("mapping_receipt_schema") != MAPPING_SCHEMA:
        raise RuntimeError("preflight mapping receipt schema mismatch")
    embedded_checks = preflight.get("mapping_checks")
    if not isinstance(embedded_checks, dict):
        raise RuntimeError("preflight embedded mapping checks missing")
    for key in REQUIRED_MAPPING_CHECKS:
        if embedded_checks.get(key) is not True:
            raise RuntimeError(f"preflight embedded mapping check missing/false: {key}")
        if mapping["checks"].get(key) is not True:
            raise RuntimeError(f"mapping receipt check missing/false: {key}")
    return preflight, mapping


def verify_source_file(path: Path, source_rec: dict) -> str:
    """Authenticate physical source bytes immediately before any caller opens value arrays."""
    path = Path(path)
    if not path.is_file():
        raise RuntimeError(f"source file missing: {path}")
    expected_size = int(source_rec["bytes"])
    if path.stat().st_size != expected_size:
        raise RuntimeError(f"source size mismatch: {path.stat().st_size} != {expected_size}: {path}")
    actual = sha256_file(path)
    expected = str(source_rec["sha256"])
    if actual != expected:
        raise RuntimeError(f"source SHA mismatch: {actual} != {expected}: {path}")
    return actual


def strict_raw_integer(value) -> int:
    """Return an exact nonnegative integer raw count; never round transformed/fractional values."""
    numeric = float(value)
    if not math.isfinite(numeric):
        raise RuntimeError("raw count must be finite")
    if numeric < 0:
        raise RuntimeError("raw count must be nonnegative")
    if not numeric.is_integer():
        raise RuntimeError("raw count must be exactly integer-valued; rounding is forbidden")
    return int(numeric)
