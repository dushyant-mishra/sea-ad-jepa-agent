from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

from sea_ad_jepa.v5.audit_b_n1_execution_authority_v1 import (
    AuditBN1ExecutionAuthorityV1,
)

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/agent/build_full104_audit_b_n1_execution_authority_v1_20260922.py"
PHASE_IV = ROOT / "analysis/v5_full104_information_channel_redteam_20260920/evidence/phase_iv"
B4 = PHASE_IV / "AUDIT_B_EXECUTION_CONTRACT_V2.json"
PREFLIGHT = PHASE_IV / "B4_FULL_RUNTIME_PREFLIGHT_RECEIPT.json"
COMMITTED = PHASE_IV / "AUDIT_B_N1_EXECUTION_AUTHORITY_V1.json"


def test_builder_reproduces_committed_n1_authority(tmp_path: Path) -> None:
    out = tmp_path / "authority.json"
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--b4-contract", str(B4),
            "--b4-preflight-receipt", str(PREFLIGHT),
            "--out", str(out),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    built = json.loads(out.read_text(encoding="utf-8"))
    committed = json.loads(COMMITTED.read_text(encoding="utf-8"))
    assert built["authority_sha256"] == committed["authority_sha256"]

    names = {f.name for f in __import__("dataclasses").fields(AuditBN1ExecutionAuthorityV1)}
    authority = AuditBN1ExecutionAuthorityV1(
        **{name: built[name] for name in names}
    )
    assert authority.canonical_digest() == built["authority_sha256"]
    assert built["sample_level"] == "N1"
    assert built["target_count"] == 256
    assert built["n2_directly_authorized"] is False


def test_builder_rejects_preflight_that_claims_burden_was_computed(
    tmp_path: Path,
) -> None:
    receipt = json.loads(PREFLIGHT.read_text(encoding="utf-8"))
    receipt["burden_computed"] = True
    bad = tmp_path / "bad-preflight.json"
    bad.write_text(json.dumps(receipt), encoding="utf-8")
    out = tmp_path / "authority.json"

    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--b4-contract", str(B4),
            "--b4-preflight-receipt", str(bad),
            "--out", str(out),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert proc.returncode != 0
    assert "burden_computed" in (proc.stdout + proc.stderr)
    assert not out.exists()
