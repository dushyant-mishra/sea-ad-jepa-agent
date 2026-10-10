#!/usr/bin/env python3
"""One-command, value-blind preflight for the corrected TD56->TD59 replay.

This driver performs only provenance/identity work:
1. regenerates and byte-validates the exact historical 9,216-address manifest;
2. exact-hashes the frozen calibration and TD historical archives;
3. extracts the frozen Macha S174 asset inventory from its branch and hash-verifies it;
4. authenticates all 35 frozen HVS/SEA-AD H5AD source bytes, while applying Sample-A mapping/cell
   checks only to the 34 H5AD matrices actually occupied by frozen A_NATURAL_MIXTURE;
5. writes a structured PASS receipt, or a structured mapping failure receipt, in a fresh immutable namespace.

It never authorizes or reads real expression values. It stops after G4/G5.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

MACHA_BRANCH = "claude/s174-train-cache-rebuild-20261007"
MACHA_FREEZE_REPO_PATH = "results/v77/S174_REBUILD_FREEZE_V1.json"
MACHA_FREEZE_SHA256 = "240b2b71a94802477ca726a2b4bb020d2ad5542ccf31c4e732906008f81e967c"
EXPECTED_MANIFEST_SHA256 = "4bde5f8041394410bf81e9c7c7edbf8553767a87bb31956f0b47bb50026f7660"
EXPECTED_SAMPLE_FREEZE_SHA256 = "79eb005c719788119d9c3021e211148d34198301a59393707c9a2dc88dcef9a6"
EXPECTED_PROVENANCE_SHA256 = "df0cb60f2308c08adaeacb1db5d1099c9cd12e90323af8e3958c428d6869cd51"
EXPECTED_COLLISION_SHA256 = "f6909f81a2e73383b4346f8cf6d8b3ecfc282f81bfb42d695c6d6896b6c74722"
EXPECTED_CALIBRATION_SHA256 = "07748d5bd21fe0857ccad3002fba3946d1791d25898b841d41056a3707117444"
EXPECTED_TD_ARTIFACTS_SHA256 = "c84849f5568f5260ac80b7c53e8af34f8bdad03fdbc16e0e8b29e7663dcf2417"


def sha256_file(path: Path, chunk: int = 8 << 20) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for b in iter(lambda: f.read(chunk), b""):
            h.update(b)
    return h.hexdigest()


def canonical_paths(project_root: Path, stage81a3r_root: Path) -> dict[str, Path]:
    project_root = Path(project_root)
    stage81a3r_root = Path(stage81a3r_root)
    return {
        "calibration_zip": project_root / "FOUNDATION_CALIBRATION_BUNDLE_20260824.zip",
        "td_artifacts_zip": project_root / "JEPA_TARGET_DISCOVERY_WORKING_ARTIFACTS_TD41_TD58_20260908.zip",
        "sample_freeze": project_root / "exports/foundation_corpus_discovery_v1/FOUNDATION_DISCOVERY_SAMPLE_FREEZE.csv",
        "provenance": project_root / "results/v4/stage81a2r_foundation_molecular_address_source_provenance_candidate.csv.gz",
        "collision_ledger": stage81a3r_root / "results/v4/stage81a3r_expression_materialization_collision_ledger.csv.gz",
        "source_root": project_root,
    }


def default_output_dir(repo_root: Path) -> Path:
    return Path(repo_root) / "results/target_discovery/td_relational_corrected_replay_20261010/preflight_v4_sampleA_custody_split"


def assert_fresh_output(out: Path) -> None:
    out = Path(out)
    if not out.exists():
        return
    existing = sorted(p.name for p in out.iterdir())
    if existing:
        preview = ", ".join(existing[:5])
        more = "" if len(existing) <= 5 else f" (+{len(existing) - 5} more)"
        raise RuntimeError(
            f"immutable preflight namespace is non-empty; existing artifact(s): {preview}{more}; do not overwrite"
        )


def require_hash(path: Path, expected: str, label: str) -> None:
    if not path.is_file():
        raise RuntimeError(f"missing {label}: {path}")
    actual = sha256_file(path)
    if actual != expected:
        raise RuntimeError(f"{label} SHA mismatch: {actual} != {expected}: {path}")


def verify_static_archives(paths: dict[str, Path]) -> dict[str, str]:
    require_hash(paths["calibration_zip"], EXPECTED_CALIBRATION_SHA256, "FOUNDATION_CALIBRATION_BUNDLE_20260824.zip")
    require_hash(paths["td_artifacts_zip"], EXPECTED_TD_ARTIFACTS_SHA256, "TD41-TD58 historical archive")
    return {
        "calibration_zip_sha256": sha256_file(paths["calibration_zip"]),
        "td_artifacts_zip_sha256": sha256_file(paths["td_artifacts_zip"]),
    }


def run_checked(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess:
    p = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)
    if p.returncode != 0:
        raise RuntimeError(
            "command failed\n"
            + "CMD: " + " ".join(map(str, cmd)) + "\n"
            + "STDOUT:\n" + p.stdout + "\nSTDERR:\n" + p.stderr
        )
    return p


def write_failure_receipt(
    out: Path,
    *,
    phase: str,
    terminal: str,
    error: str,
    command: list[str],
    inputs: dict[str, str],
) -> Path:
    """Write a non-authorizing structured receipt without pretending a failed mapping step passed."""
    receipt = {
        "schema": "JEPA_TD_RELATIONAL_PREFLIGHT_FAILURE_RECEIPT_V1",
        "status": terminal,
        "phase": phase,
        "error": str(error),
        "command": list(map(str, command)),
        "inputs": inputs,
        "real_value_replay_authorized": False,
        "training_authorized": False,
    }
    path = Path(out) / "PREFLIGHT_FAILURE.json"
    if path.exists():
        raise RuntimeError(f"refusing to overwrite existing failure receipt: {path}")
    path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def extract_macha_freeze(repo_root: Path, out_path: Path) -> None:
    p = subprocess.run(
        ["git", "show", f"{MACHA_BRANCH}:{MACHA_FREEZE_REPO_PATH}"],
        cwd=repo_root,
        capture_output=True,
    )
    if p.returncode != 0:
        raise RuntimeError(
            f"cannot resolve {MACHA_BRANCH}:{MACHA_FREEZE_REPO_PATH}; fetch the Macha branch first\n"
            + p.stderr.decode(errors="replace")
        )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(p.stdout)
    require_hash(out_path, MACHA_FREEZE_SHA256, "Macha S174 freeze")


def manifest_command(python: Path, repo_root: Path, paths: dict[str, Path], out: Path) -> list[str]:
    return [
        str(python), str(repo_root / "scripts/v5/build_td_relational_replay_manifest.py"),
        "--calibration-zip", str(paths["calibration_zip"]),
        "--td-artifacts-zip", str(paths["td_artifacts_zip"]),
        "--manifest-out", str(out / "JEPA_TD_RELATIONAL_REPLAY_9216_MANIFEST.csv"),
        "--receipt-out", str(out / "JEPA_TD_RELATIONAL_REPLAY_9216_RECEIPT.json"),
    ]


def mapping_command(python: Path, repo_root: Path, paths: dict[str, Path], out: Path, macha_freeze: Path) -> list[str]:
    return [
        str(python), str(repo_root / "scripts/v5/audit_td_relational_replay_mapping_preflight.py"),
        "--replay-manifest", str(out / "JEPA_TD_RELATIONAL_REPLAY_9216_MANIFEST.csv"),
        "--sample-freeze", str(paths["sample_freeze"]),
        "--provenance", str(paths["provenance"]),
        "--collision-ledger", str(paths["collision_ledger"]),
        "--macha-freeze", str(macha_freeze),
        "--source-root", str(paths["source_root"]),
        "--out", str(out / "TD_RELATIONAL_MAPPING_PREFLIGHT.json"),
    ]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", type=Path, default=Path.cwd())
    ap.add_argument("--project-root", type=Path, default=Path("D:/Jepa project"))
    ap.add_argument("--stage81a3r-root", type=Path, default=Path("D:/Jepa project-stage81a3r-20260814"))
    ap.add_argument("--output-dir", type=Path)
    ap.add_argument("--python", type=Path, default=Path(sys.executable))
    args = ap.parse_args()

    repo_root = args.repo_root.resolve()
    out = args.output_dir or default_output_dir(repo_root)
    assert_fresh_output(out)
    out.mkdir(parents=True, exist_ok=True)

    paths = canonical_paths(args.project_root, args.stage81a3r_root)
    require_hash(paths["sample_freeze"], EXPECTED_SAMPLE_FREEZE_SHA256, "FOUNDATION_DISCOVERY_SAMPLE_FREEZE.csv")
    require_hash(paths["provenance"], EXPECTED_PROVENANCE_SHA256, "Stage81A2R provenance")
    require_hash(paths["collision_ledger"], EXPECTED_COLLISION_SHA256, "Stage81A3R collision ledger")
    archive_hashes = verify_static_archives(paths)

    macha_freeze = out / "S174_REBUILD_FREEZE_V1.json"
    extract_macha_freeze(repo_root, macha_freeze)

    mcmd = manifest_command(args.python, repo_root, paths, out)
    run_checked(mcmd, repo_root)
    manifest = out / "JEPA_TD_RELATIONAL_REPLAY_9216_MANIFEST.csv"
    require_hash(manifest, EXPECTED_MANIFEST_SHA256, "9,216-address replay manifest")

    input_hashes = {
        "sample_freeze_sha256": sha256_file(paths["sample_freeze"]),
        "provenance_sha256": sha256_file(paths["provenance"]),
        "collision_ledger_sha256": sha256_file(paths["collision_ledger"]),
        **archive_hashes,
        "macha_freeze_sha256": sha256_file(macha_freeze),
        "replay_manifest_sha256": sha256_file(manifest),
    }

    pcmd = mapping_command(args.python, repo_root, paths, out, macha_freeze)
    try:
        run_checked(pcmd, repo_root)
    except RuntimeError as e:
        failure_path = write_failure_receipt(
            out,
            phase="G4_G5_MAPPING_PREFLIGHT",
            terminal="FAIL_TD_RELATIONAL_PREFLIGHT_DRIVER_AT_G4_G5_MAPPING",
            error=str(e),
            command=pcmd,
            inputs=input_hashes,
        )
        raise RuntimeError(f"mapping preflight failed; structured failure receipt: {failure_path}\n{e}") from e

    preflight_path = out / "TD_RELATIONAL_MAPPING_PREFLIGHT.json"
    preflight = json.loads(preflight_path.read_text(encoding="utf-8"))
    expected_schema = "JEPA_TD_RELATIONAL_MAPPING_PREFLIGHT_V3"
    expected_status = "PASS_TD_RELATIONAL_MAPPING_PREFLIGHT_VALUE_BLIND"
    if preflight.get("schema") != expected_schema or preflight.get("status") != expected_status:
        failure_path = write_failure_receipt(
            out,
            phase="G4_G5_MAPPING_PREFLIGHT",
            terminal="FAIL_TD_RELATIONAL_PREFLIGHT_DRIVER_AT_G4_G5_MAPPING_RECEIPT",
            error=f"mapping receipt schema/status mismatch: {preflight.get('schema')} / {preflight.get('status')}",
            command=pcmd,
            inputs=input_hashes,
        )
        raise RuntimeError(f"mapping preflight did not produce required V3 PASS; receipt: {failure_path}")

    required_mapping_checks = {
        "sample_A_h5_matrix_count_exact_34",
        "all_sample_A_h5_matrices_present",
        "frozen_h5_matrix_count_exact_35",
        "all_35_h5_source_sha256_verified",
        "all_9216_addresses_one_to_one",
        "all_sample_A_h5_cell_rows_exact",
        "source_files_exactly_hash_bound",
        "count_arrays_never_opened_by_design",
    }
    mapping_checks = preflight.get("checks", {})
    missing_or_false = sorted(k for k in required_mapping_checks if mapping_checks.get(k) is not True)
    if missing_or_false:
        failure_path = write_failure_receipt(
            out,
            phase="G4_G5_MAPPING_PREFLIGHT",
            terminal="FAIL_TD_RELATIONAL_PREFLIGHT_DRIVER_AT_G4_G5_MAPPING_CHECKS",
            error=f"required mapping checks missing/false: {missing_or_false}",
            command=pcmd,
            inputs=input_hashes,
        )
        raise RuntimeError(f"mapping preflight checks incomplete; receipt: {failure_path}")

    receipt = {
        "schema": "JEPA_TD_RELATIONAL_PREFLIGHT_DRIVER_RECEIPT_V3",
        "status": "PASS_TD_RELATIONAL_PREFLIGHT_DRIVER_VALUE_BLIND",
        "scope": (
            "G1-G5 only; exact archive/source bytes + identity/mapping; all 35 frozen H5AD bytes authenticated, "
            "Sample-A mapping applied to its exact 34 H5AD matrices; no count arrays read; no real-value replay/training authority"
        ),
        "inputs": input_hashes,
        "mapping_receipt_schema": preflight.get("schema"),
        "mapping_checks": mapping_checks,
        "commands": {
            "manifest": mcmd,
            "mapping_preflight": pcmd,
        },
        "artifacts": {
            "manifest": str(manifest),
            "manifest_receipt": str(out / "JEPA_TD_RELATIONAL_REPLAY_9216_RECEIPT.json"),
            "mapping_preflight": str(preflight_path),
        },
        "next_gate": "owner review; G6/G7 remain unauthorized and require a separately qualified standalone-V2 value path",
        "real_value_replay_authorized": False,
        "training_authorized": False,
    }
    final = out / "PREFLIGHT_RESULT.json"
    final.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": receipt["status"], "output": str(final)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
