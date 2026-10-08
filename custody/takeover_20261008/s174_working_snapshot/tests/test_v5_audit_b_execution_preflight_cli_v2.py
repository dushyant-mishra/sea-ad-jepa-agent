from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/agent/validate_full104_audit_b_execution_preflight_v2_20260922.py"
PHASE_IV = ROOT / "analysis/v5_full104_information_channel_redteam_20260920/evidence/phase_iv"
CONTRACT = PHASE_IV / "AUDIT_B_EXECUTION_CONTRACT_V2.json"
RESOLUTION = PHASE_IV / "AUDIT_B_SCIENTIFIC_RESOLUTION_V3.json"
PRECISION = PHASE_IV / "AUDIT_B_PRECISION_RULE_AUTHORITY_V2.json"


def _base_cmd(tmp_path: Path, *, resolution: Path = RESOLUTION) -> list[str]:
    missing = tmp_path / "intentionally-missing"
    return [
        sys.executable,
        str(SCRIPT),
        "--contract", str(CONTRACT),
        "--scientific-resolution", str(resolution),
        "--precision-rule-authority", str(PRECISION),
        "--sample-freeze", str(missing),
        "--heavy-artifact", str(missing),
        "--heavy-qualification-receipt", str(missing),
        "--rng-authority", str(missing),
        "--mask-plan-generator", str(missing),
        "--burden-estimator-source", str(missing),
        "--full104-manifest", str(missing),
        "--canonical-registry", str(missing),
        "--repo-root", str(tmp_path),
    ]


def test_b4_cli_passes_authorization_gate_then_requires_runtime_bindings(
    tmp_path: Path,
) -> None:
    proc = subprocess.run(
        _base_cmd(tmp_path),
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert proc.returncode != 0
    combined = proc.stdout + proc.stderr
    assert "STOP_AUDIT_B_V1_PREEXECUTION_ONLY" not in combined
    assert "required file is missing" in combined or "scientific resolution" not in combined


def test_b4_cli_rejects_tampered_resolution_before_runtime_files(
    tmp_path: Path,
) -> None:
    payload = json.loads(RESOLUTION.read_text(encoding="utf-8"))
    payload["primary_policy_id"] = "TOP8_CORRELATION"
    bad = tmp_path / "bad-resolution.json"
    bad.write_text(json.dumps(payload), encoding="utf-8")

    proc = subprocess.run(
        _base_cmd(tmp_path, resolution=bad),
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert proc.returncode != 0
    combined = proc.stdout + proc.stderr
    assert "primary_policy_id drifted" in combined or "declared digest mismatch" in combined
    assert "required file is missing" not in combined
