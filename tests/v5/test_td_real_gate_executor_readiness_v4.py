from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

import pytest

import scripts.v5.audit_td_real_gate_executor_readiness_v4 as A
import scripts.v5.td_real_directional_gate_executors_v2 as D
import scripts.v5.td_real_quantitative_components_v1 as Q
import scripts.v5.td_real_tournament_contract_v1 as C
import scripts.v5.td_real_gate_rule_registry_v1 as R


FROZEN_RECEIPT = Path("results/target_discovery/real_tournament/TD_REAL_DIRECTIONAL_GATES_V2_QUALIFICATION_RECEIPT.json")


def _sha(path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _canon(value) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _receipt() -> dict:
    executor_sha = _sha(D.__file__)
    quantitative_sha = _sha(Q.__file__)
    contract_sha = _sha(C.__file__)
    bundle = _canon({
        "executor_sha256": executor_sha,
        "quantitative_components_sha256": quantitative_sha,
        "tournament_contract_sha256": contract_sha,
    })
    return {
        "schema": "JEPA_TD_REAL_DIRECTIONAL_GATES_V2_QUALIFICATION",
        "status": "PASS_OUTCOME_BLIND_DIRECTIONAL_STRUCTURAL_EXECUTOR_MECHANICS",
        "executor_sha256": executor_sha,
        "quantitative_components_sha256": quantitative_sha,
        "tournament_contract_sha256": contract_sha,
        "executor_bundle_sha256": bundle,
        "candidate_outcomes_opened": False,
        "real_tournament_authorized": False,
    }


def _write_receipt(tmp_path, receipt=None):
    path = tmp_path / "receipt.json"
    path.write_text(json.dumps(receipt or _receipt(), sort_keys=True), encoding="utf-8")
    return path


def _positive(n=10):
    return [{"donor_id": f"D{i:03d}", "delta": 1.0} for i in range(n)]


def test_frozen_receipt_authenticates_exact_current_executor_bundle():
    receipt = json.loads(FROZEN_RECEIPT.read_text(encoding="utf-8"))
    assert receipt == _receipt()
    assert D.authenticate_qualification_receipt(receipt) == receipt["executor_bundle_sha256"]


def test_authenticated_executor_emits_bridge_identity_and_no_authority():
    out = D.execute_directional_gate(
        "G4_DONOR_RECURRENCE",
        {"donor_deltas": _positive()},
        qualification_receipt=_receipt(),
    )
    assert out["status"] == "PASS"
    assert len(out["qualified_gate_executor_sha256"]) == 64
    assert len(out["estimand_sha256"]) == 64
    assert len(out["decision_rule_sha256"]) == 64
    assert len(out["evidence_payload_sha256"]) == 64
    assert out["claim_boundary"] == D.CLAIM_BOUNDARY
    assert not any(out["authority"].values())


def test_authenticated_executor_rejects_tampered_qualification():
    bad = dict(_receipt(), executor_sha256="0" * 64)
    with pytest.raises(D.DirectionalGateError, match="SHA-256 mismatch"):
        D.execute_directional_gate(
            "G4_DONOR_RECURRENCE",
            {"donor_deltas": _positive()},
            qualification_receipt=bad,
        )


def test_v4_promotes_exactly_49_new_required_roles_and_keeps_13_rules_blocked(tmp_path):
    result = A.audit(qualification_receipt_path=_write_receipt(tmp_path))
    assert result["candidate_gate_rows"] == 198
    assert result["required_roles"] == 117
    assert result["newly_qualified_role_count"] == 49
    assert result["newly_qualified_unique_gates"] == sorted(D.CLEARED_V2_GATES)
    assert result["blocked_unique_gates"] == sorted(D.BLOCKED_V2_GATES)
    assert result["readiness_counts"] == {
        "CALLABLE_AND_QUALIFIED": 66,
        "CALLABLE_NEEDS_QUALIFICATION": 0,
        "RULE_NOT_MATERIALIZED": 51,
        "BLOCKED_ON_DEPENDENCY": 0,
        "NOT_APPLICABLE": 81,
    }
    assert result["real_tournament_qualify_eligible"] is False
    assert not any(result["authority"].values())


def test_v4_qualified_gate_set_is_old_structural_plus_v2_cleared(tmp_path):
    rows = A.project_rows(qualification_receipt_path=_write_receipt(tmp_path))
    required = [row for row in rows if row["required"] == "True"]
    qualified = [row for row in required if row["readiness"] == "CALLABLE_AND_QUALIFIED"]
    assert len(qualified) == 66
    assert {row["gate_id"] for row in qualified} == R.CALLABLE_STRUCTURAL | D.CLEARED_V2_GATES
    for row in qualified:
        if row["gate_id"] in D.CLEARED_V2_GATES:
            assert row["callable_implementation"] == "td_real_directional_gate_executors_v2.execute_directional_gate"
            assert row["blocker"] == ""
            assert len(row["qualified_gate_executor_sha256"]) == 64


def test_v4_never_promotes_any_v2_blocked_rule(tmp_path):
    rows = A.project_rows(qualification_receipt_path=_write_receipt(tmp_path))
    blocked = [
        row for row in rows
        if row["required"] == "True" and row["gate_id"] in D.BLOCKED_V2_GATES
    ]
    assert blocked
    assert {row["gate_id"] for row in blocked} == D.BLOCKED_V2_GATES
    assert all(row["readiness"] == "RULE_NOT_MATERIALIZED" for row in blocked)
    assert all(row["blocker"] == "BLOCKED_PROSPECTIVE_RULE_REQUIRED" for row in blocked)


def test_v4_fails_closed_on_tampered_receipt(tmp_path):
    bad = dict(_receipt(), quantitative_components_sha256="f" * 64)
    with pytest.raises((A.ReadinessV4Error, D.DirectionalGateError)):
        A.project_rows(qualification_receipt_path=_write_receipt(tmp_path, bad))
