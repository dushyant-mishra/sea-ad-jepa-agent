from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
import subprocess
import sys
from pathlib import Path

from sea_ad_jepa.v5.audit_b_execution_contract_v1 import (
    CANONICAL_REGISTRY_SHA256,
    FULL104_MANIFEST_SHA256,
    HEAVY_ARTIFACT_SHA256,
    MASK_PLAN_GENERATOR_SHA256,
    PHASE_IV_SAMPLE_FREEZE_DIGEST,
    AuditBExecutionContractV1,
)
from sea_ad_jepa.v5.masking_rng_replay_authority_v3 import MaskingRngReplayAuthorityV3

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/agent/validate_full104_audit_b_execution_preflight_v1_20260921.py"


def h(x: str) -> str:
    return hashlib.sha256(x.encode()).hexdigest()


def unresolved_payload() -> dict:
    rng = MaskingRngReplayAuthorityV3(
        authority_id="TEST_CLI_RNG",
        full104_substrate_sha256=FULL104_MANIFEST_SHA256,
        canonical_registry_sha256=CANONICAL_REGISTRY_SHA256,
        outer_split_receipt_sha256="1" * 64,
        qualification_parameters_authority_sha256="2" * 64,
        burden_ladder_authority_sha256="3" * 64,
    )
    c = AuditBExecutionContractV1(
        contract_id="TEST_CLI_CONTRACT",
        phase_iv_sample_freeze_digest=PHASE_IV_SAMPLE_FREEZE_DIGEST,
        phase_iv_sample_artifact_sha256=h("sample"),
        full104_manifest_sha256=FULL104_MANIFEST_SHA256,
        canonical_registry_sha256=CANONICAL_REGISTRY_SHA256,
        heavy_artifact_sha256=HEAVY_ARTIFACT_SHA256,
        heavy_qualification_receipt_sha256=h("heavy"),
        rng_authority_sha256=rng.canonical_digest(),
        mask_plan_generator_sha256=MASK_PLAN_GENERATOR_SHA256,
        burden_estimator_source_sha256=h("estimator"),
    )
    return {
        "schema": "V5_AUDIT_B_EXECUTION_CONTRACT_V1",
        **asdict(c),
        "sample_ladder": list(c.sample_ladder),
        "execution_requirements": list(c.execution_requirements),
        "execution_authorized": c.execution_authorized,
        "contract_sha256": c.canonical_digest(),
        "terminal_masking_outcomes_inspected": False,
        "training_authorized": False,
    }


def test_cli_stops_on_unresolved_precision_before_touching_runtime_files(tmp_path: Path) -> None:
    contract = tmp_path / "contract.json"
    contract.write_text(json.dumps(unresolved_payload()))
    missing = tmp_path / "intentionally-missing"
    cmd = [
        sys.executable,
        str(SCRIPT),
        "--contract", str(contract),
        "--sample-freeze", str(missing),
        "--heavy-artifact", str(missing),
        "--heavy-qualification-receipt", str(missing),
        "--rng-authority", str(missing),
        "--mask-plan-generator", str(missing),
        "--burden-estimator-source", str(missing),
        "--full104-manifest", str(missing),
        "--canonical-registry", str(missing),
    ]
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=60)
    assert proc.returncode != 0
    combined = proc.stdout + proc.stderr
    assert "STOP_PRECISION_SCOPE_UNRESOLVED" in combined
    assert "required file is missing" not in combined
