#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

from sea_ad_jepa.v5.critical_test_execution_guard_v1 import (
    validate_junit_critical_tests,
)

SCHEMA = "JEPA_V5_C2_GPU_CRITICAL_TEST_EXECUTION_MANIFEST_V1"
TERMINAL = "PASS_V5_C2_GPU_CRITICAL_EXECUTION_V1"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def validate_manifest(manifest: dict) -> dict:
    if manifest.get("schema") != SCHEMA:
        raise RuntimeError("STOP_V5_C2_GPU_MANIFEST_SCHEMA")
    expected = manifest.get("expected_test_ids")
    if not isinstance(expected, list) or len(expected) != 6 or len(set(expected)) != 6:
        raise RuntimeError("STOP_V5_C2_GPU_TEST_SET")
    req = manifest.get("requirements")
    if not isinstance(req, dict):
        raise RuntimeError("STOP_V5_C2_GPU_REQUIREMENTS")
    if req.get("cuda_required_for_execution_receipt") is not True:
        raise RuntimeError("STOP_V5_C2_GPU_CUDA_NOT_REQUIRED")
    for key in ("skipped_allowed", "missing_allowed", "failed_allowed", "errored_allowed"):
        if req.get(key) is not False:
            raise RuntimeError(f"STOP_V5_C2_GPU_FAIL_OPEN:{key}")
    if req.get("exact_historical_geometry") != {"effective_batch": 128, "microbatch": 8}:
        raise RuntimeError("STOP_V5_C2_GPU_GEOMETRY")
    for key in (
        "protected_tensors_expected",
        "adam_exp_avg_live_expected",
        "adam_exp_avg_sq_live_expected",
        "protected_parameter_motion_expected",
    ):
        if req.get(key) != 48:
            raise RuntimeError(f"STOP_V5_C2_GPU_PROTECTED_COUNT:{key}")
    production = manifest.get("required_production_geometry_test")
    if production not in expected:
        raise RuntimeError("STOP_V5_C2_GPU_PRODUCTION_TEST_NOT_REQUIRED")
    if manifest.get("cpu_ci_success_may_satisfy_gpu_receipt") is not False:
        raise RuntimeError("STOP_V5_C2_GPU_CPU_MASQUERADE")
    if manifest.get("training_authorized") is not False:
        raise RuntimeError("STOP_V5_C2_GPU_MANIFEST_AUTHORITY_ESCALATION")
    return {"expected_test_ids": expected, "source_test_file": manifest.get("source_test_file")}


def cuda_environment() -> dict:
    import torch
    if not torch.cuda.is_available():
        raise RuntimeError("STOP_V5_C2_GPU_CUDA_NOT_AVAILABLE")
    index = torch.cuda.current_device()
    props = torch.cuda.get_device_properties(index)
    return {
        "torch_version": str(torch.__version__),
        "torch_cuda_version": str(torch.version.cuda),
        "cuda_available": True,
        "device_index": int(index),
        "device_name": str(props.name),
        "compute_capability": [int(props.major), int(props.minor)],
        "total_memory_bytes": int(props.total_memory),
    }


def run_qualification(*, manifest_path: Path, output: Path, junit: Path) -> dict:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    validated = validate_manifest(manifest)
    env_info = cuda_environment()
    source = Path(validated["source_test_file"])
    if not source.is_file():
        raise RuntimeError("STOP_V5_C2_GPU_TEST_SOURCE_MISSING")

    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "-q",
        str(source),
        f"--junitxml={junit}",
    ]
    env = dict(os.environ)
    env.setdefault("PYTHONPATH", "src:.")
    completed = subprocess.run(cmd, env=env, check=False)
    if completed.returncode != 0:
        raise RuntimeError(f"STOP_V5_C2_GPU_PYTEST_RC:{completed.returncode}")
    report = validate_junit_critical_tests(
        junit, expected_test_ids=validated["expected_test_ids"]
    )
    obj = {
        "schema": "JEPA_V5_C2_GPU_CRITICAL_EXECUTION_RECEIPT_V1",
        "terminal": TERMINAL,
        "environment": env_info,
        "critical_test_report": report.__dict__,
        "manifest_sha256": sha256_file(manifest_path),
        "junit_sha256": sha256_file(junit),
        "source_test_file": str(source),
        "source_test_sha256": sha256_file(source),
        "training_authorized": False,
        "successor_u0_authorized": False,
        "td60_authorized": False,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return obj


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--manifest",
        type=Path,
        default=Path("docs/agent/TEACHER_STUDENT_V5_C2_GPU_CRITICAL_TEST_EXECUTION_MANIFEST_V1.json"),
    )
    ap.add_argument("--junit", type=Path, default=Path("v5-c2-gpu-critical-junit.xml"))
    ap.add_argument("--output", type=Path, default=Path("v5-c2-gpu-critical-receipt.json"))
    ap.add_argument("--validate-manifest-only", action="store_true")
    args = ap.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    if args.validate_manifest_only:
        validate_manifest(manifest)
        print(json.dumps({"status": "PASS_MANIFEST_ONLY", "training_authorized": False}, sort_keys=True))
        return 0
    obj = run_qualification(manifest_path=args.manifest, output=args.output, junit=args.junit)
    print(json.dumps(obj, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
