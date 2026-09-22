from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

from sea_ad_jepa.v5.audit_b_execution_preflight_v2 import load_contract

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/agent/build_full104_audit_b_execution_contract_v2_20260922.py"
PHASE_IV = ROOT / "analysis/v5_full104_information_channel_redteam_20260920/evidence/phase_iv"
PARENT = PHASE_IV / "AUDIT_B_EXECUTION_CONTRACT_V1.json"
RESOLUTION = PHASE_IV / "AUDIT_B_SCIENTIFIC_RESOLUTION_V3.json"
PRECISION = PHASE_IV / "AUDIT_B_PRECISION_RULE_AUTHORITY_V2.json"
REAL_B4 = PHASE_IV / "AUDIT_B_EXECUTION_CONTRACT_V2.json"


def test_builder_materializes_execution_ready_b4_from_real_semantic_parents(
    tmp_path: Path,
) -> None:
    out = tmp_path / "b4.json"
    cmd = [
        sys.executable,
        str(SCRIPT),
        "--parent-contract", str(PARENT),
        "--scientific-resolution", str(RESOLUTION),
        "--precision-rule-authority", str(PRECISION),
        "--out", str(out),
    ]
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=60)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["schema"] == "V5_AUDIT_B_EXECUTION_CONTRACT_V2"
    assert payload["execution_authorized"] is True
    assert payload["terminal_masking_authorized"] is False
    assert payload["training_authorized"] is False

    contract = load_contract(out)
    contract.require_execution_ready()
    assert payload["contract_sha256"] == contract.canonical_digest()

    committed = json.loads(REAL_B4.read_text(encoding="utf-8"))
    committed_contract = load_contract(REAL_B4)
    assert committed["contract_sha256"] == contract.canonical_digest()
    assert committed_contract.canonical_digest() == contract.canonical_digest()


def test_builder_refuses_overwrite_before_touching_inputs(tmp_path: Path) -> None:
    out = tmp_path / "b4.json"
    out.write_text("sentinel", encoding="utf-8")
    missing = tmp_path / "missing"
    cmd = [
        sys.executable,
        str(SCRIPT),
        "--parent-contract", str(missing),
        "--scientific-resolution", str(missing),
        "--precision-rule-authority", str(missing),
        "--out", str(out),
    ]
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=60)
    assert proc.returncode != 0
    assert "refuse overwrite" in (proc.stdout + proc.stderr)
    assert out.read_text(encoding="utf-8") == "sentinel"
