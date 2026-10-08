#!/usr/bin/env python3
"""Build the hash-bound WSL block-major ALL implementation gate atomically."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shutil
from pathlib import Path


FREEZE_ROOT = "593e14872b6fe07d3f2855a49dd8eac57bfa5819465b8801b801dd9f6d4b510c"
EXPECTED = {
    "historical_cross_blas_stop_sha256": "bbce0b3d1754db178525c0de0310058d43415bd8afa45e4874090cb1636ad58c",
    "historical_red_team_stop_sha256": "c76653f18f733960ab8b0234c278fd0d569b13e178255fe34d53af1465336c98",
    "scope_correction_sha256": "2ac7759fd374ffb2d5dede7e3fb50c7908add8edc8569cc494c52f9299ef5b4d",
    "corrected_numerical_parity_sha256": "e4969b4ba7d2bede0a445ff329d298805cccdf71494cbe57e38350734279d349",
    "corrected_red_team_sha256": "15abd8552058d45d314048129e1589ae99f9ea501f0316e80d6e181d20ac9e97",
    "targeted_parity_v12_sha256": "1835d98b77d86b5de2bc105e1b2166c8f28d1d8e1bf8c04482ba419a59854c83",
    "wsl_benchmark_sha256": "3582be0e373ca22043ef2cc27bbf715f9bbf05ddebb1ee7af1e7208c87512f2d",
    "wsl_environment_sha256": "6e61a2ea722b7da6675349cb15e8164c2be8dcea1b34a629c7ca14a27e6a30b8",
    "matrix_manifest_sha256": "986c9508314fdceadfac2397dad94767f2590126fb5902221307aea536accf91",
    "all_plan_authority_sha256": "751f585a681aa392446341fc519797f8ad60c99e2edf0fbccccc4f9bea6016d2",
    "all_plan_sha256": "fc7249c4e1aefccc6a9535a30cd311e8b6fa6cf980b85c1c0a7607b65d611a21",
    "all_plan_semantic_sha256": "132fa3c3b9594a742daa650497d7f212375056f104fdc087375349bcb35b6b20",
    "gold_report_sha256": "dcc236700dc240abe2d984c002a9d7ebf300e3bc090d03d71066dc944ec922a3",
    "gold_basis_audit_sha256": "7ae00037e6c025ca92841ed993bfe3bb8158e408a8606026384c77e83910702a",
}


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 << 20), b""):
            h.update(block)
    return h.hexdigest()


def canonical_sha(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def write_json(path: Path, value: object) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    project = Path(args.project).resolve()
    out = Path(args.out).resolve()
    if out.exists():
        raise RuntimeError("refusing to overwrite implementation gate")
    staging = out.with_name(out.name + ".staging")
    if staging.exists():
        raise RuntimeError("staging already exists")
    staging.mkdir(parents=True)
    artifacts = staging / "artifacts"
    artifacts.mkdir()

    base = project / "outputs/full104_v014_20260826/03_phase2_state_derivation_v1"
    corrected = base / "wsl_cross_blas_promotion_corrected_v1"
    sources = {
        "runner_sha256": project / "scripts/v4/run_full104_refit_null_block_major_v1.py",
        "sequential_helper_sha256": project / "scripts/v4/run_full104_refit_null_sensitivity_v1.py",
        "core_sha256": project / "scripts/v4/full104_refit_null_sensitivity_core_v1.py",
        "fit_basis_code_sha256": project / "scripts/v4/derive_full104_phase2_shared_state.py",
        "targeted_test_code_sha256": project / "scripts/v4/test_full104_block_major_executor_v1.py",
        "benchmark_code_sha256": project / "scripts/v4/benchmark_full104_block_major_executor_v1.py",
        "gold_validator_current_sha256": project / "scripts/v4/validate_full104_block_major_gold_replicate_v1.py",
        "production_command_sha256": project / "scripts/v4/launch_full104_block_major_wsl_all_v1.sh",
        "gate_builder_code_sha256": Path(__file__).resolve(),
    }
    evidence = {
        "historical_cross_blas_stop_sha256": base / "wsl_cross_blas_promotion_check_v1/CROSS_BLAS_DECISION_INVARIANCE.json",
        "historical_red_team_stop_sha256": base / "wsl_cross_blas_promotion_check_v1/SCIENTIFIC_RED_TEAM.json",
        "scope_correction_sha256": corrected / "FULL104_CROSS_BLAS_PROMOTION_SCOPE_CORRECTION_V1.json",
        "corrected_numerical_parity_sha256": corrected / "CORRECTED_GOLD_REPLICATE_NUMERICAL_PARITY.json",
        "corrected_red_team_sha256": corrected / "CORRECTED_SCIENTIFIC_RED_TEAM.json",
        "council_sha256": corrected / "TARGETED_IMPLEMENTATION_COUNCIL_V1.json",
        "targeted_parity_v12_sha256": base / "block_major_targeted_tests_v12/BLOCK_MAJOR_TARGETED_PARITY.json",
        "wsl_benchmark_sha256": base / "block_major_batch_benchmark_wsl_v1/BLOCK_MAJOR_BATCH_BENCHMARK.json",
        "wsl_environment_sha256": base / "wsl_backend_preflight_v1/WSL_BACKEND_PREFLIGHT.json",
        "matrix_manifest_sha256": base / "feature_matrix_level4/PHASE2_FEATURE_MATRIX_MANIFEST.csv",
        "all_plan_authority_sha256": base / "shared_refit_null_sensitivity_results_v2_lossless_scoped/cap_ALL/LOSSLESS_PLAN_AUTHORITY.json",
        "gold_report_sha256": base / "block_major_full104_gold_parity_v5_wsl/FULL104_GOLD_REPLICATE_PARITY.json",
        "gold_basis_audit_sha256": base / "block_major_full104_gold_parity_v5_wsl/AUTHENTICATED_OLD_OBSERVED_BASIS_AUDIT.json",
    }
    for key, expected in EXPECTED.items():
        if key in evidence and sha(evidence[key]) != expected:
            raise RuntimeError(f"authority hash mismatch: {key}")
    council = json.loads(evidence["council_sha256"].read_text())
    parity = json.loads(evidence["targeted_parity_v12_sha256"].read_text())
    benchmark = json.loads(evidence["wsl_benchmark_sha256"].read_text())
    if council.get("status") != "PROCEED" or parity.get("status") != "PASS_BLOCK_MAJOR_TARGETED_PARITY":
        raise RuntimeError("council or targeted parity did not pass")
    if benchmark.get("status") != "PASS_BLOCK_MAJOR_BATCH_SIZE_DERIVED" or benchmark.get("selected_K") != 32 or benchmark.get("selected_checkpoint_every_strata") != 1400:
        raise RuntimeError("WSL resource authority mismatch")
    projection = benchmark["projection"]
    if projection.get("K_selected_WSL") != 32 or projection.get("number_of_A_passes") != 8 or projection.get("number_of_B_passes") != 8:
        raise RuntimeError("WSL projection mismatch")

    components = {key: sha(path) for key, path in sources.items()}
    components.update({key: sha(path) for key, path in evidence.items()})
    components.update({
        "freeze_root": FREEZE_ROOT,
        "gold_validator_executed_v5_reconstructed_sha256": "f55275914d05eec1f0ee37ccc8cc61423dd22642cdaf3a3b3914ef3dd2f14363",
        "gold_runner_executed_sha256": "93566984c394eb63a3207e4649903718dd90ffc57cc753b4ad5c7f0e80660871",
        "all_plan_sha256": EXPECTED["all_plan_sha256"],
        "all_plan_semantic_sha256": EXPECTED["all_plan_semantic_sha256"],
        "backend": "WSL2_CUDA_RTX3080_LAPTOP",
        "batch_size": 32,
        "checkpoint_every_strata": 1400,
        "checkpoint_policy": "NO_IN_BATCH_CHECKPOINT__BATCH_BOUNDARY_RECOVERY",
        "benchmark_fixture_replicates_per_hour": projection["measured_replicates_per_hour"],
    })
    package = {"components": components, "implementation_fingerprint": canonical_sha(components)}
    write_json(staging / "IMPLEMENTATION_COMPONENTS.json", package)

    manifest_rows = []
    for index, (key, path) in enumerate([*sources.items(), *evidence.items()]):
        destination = artifacts / f"{index:02d}_{path.name}"
        shutil.copy2(path, destination)
        manifest_rows.append({"path": str(destination.relative_to(staging)), "bytes": destination.stat().st_size, "sha256": sha(destination), "role": key})
    manifest_rows.append({"path": "IMPLEMENTATION_COMPONENTS.json", "bytes": (staging / "IMPLEMENTATION_COMPONENTS.json").stat().st_size, "sha256": sha(staging / "IMPLEMENTATION_COMPONENTS.json"), "role": "fingerprint_components"})
    manifest = staging / "IMPLEMENTATION_GATE_MANIFEST.csv"
    with manifest.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["path", "bytes", "sha256", "role"], lineterminator="\n")
        writer.writeheader()
        writer.writerows(manifest_rows)
        stream.flush()
        os.fsync(stream.fileno())
    status = {
        "schema": "full104-block-major-wsl-implementation-gate-v1",
        "status": "PASS_IMPLEMENTATION_AND_COMPUTE_GATE",
        "freeze_root": FREEZE_ROOT,
        "implementation_fingerprint": package["implementation_fingerprint"],
        "gate_manifest_sha256": sha(manifest),
        "backend": components["backend"],
        "batch_size": 32,
        "checkpoint_every_strata": 1400,
        "checkpoint_policy": components["checkpoint_policy"],
        "benchmark_fixture_replicates_per_hour": components["benchmark_fixture_replicates_per_hour"],
        "scientific_outcome_inspected": False,
        "authorization": "FRESH_ALL_ONLY",
        "terminal_hold": "ALL_COMPLETE_AWAITING_INDEPENDENT_REAL_RESULT_VALIDATION",
    }
    write_json(staging / "IMPLEMENTATION_PREFLIGHT_STATUS.json", status)
    root_manifest = staging / "IMPLEMENTATION_GATE_ROOT_MANIFEST.csv"
    root_rows = []
    for path in sorted(p for p in staging.rglob("*") if p.is_file() and p != root_manifest):
        root_rows.append({"path": str(path.relative_to(staging)), "bytes": path.stat().st_size, "sha256": sha(path)})
    with root_manifest.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["path", "bytes", "sha256"], lineterminator="\n")
        writer.writeheader()
        writer.writerows(root_rows)
        stream.flush()
        os.fsync(stream.fileno())
    (staging / "IMPLEMENTATION_GATE_ROOT_SHA256.txt").write_text(sha(root_manifest) + "\n", encoding="utf-8")
    os.replace(staging, out)
    print(json.dumps({"status": status["status"], "implementation_fingerprint": package["implementation_fingerprint"], "gate_manifest_sha256": status["gate_manifest_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
