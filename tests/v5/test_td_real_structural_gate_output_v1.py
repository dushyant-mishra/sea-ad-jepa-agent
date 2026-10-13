from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "v5"))

import td_real_gate_rule_registry_v1 as R  # noqa: E402


def _sha_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _qualification_receipt():
    registry_sha = _sha_file(ROOT / "scripts" / "v5" / "td_real_gate_rule_registry_v1.py")
    query_guard_sha = _sha_file(ROOT / "scripts" / "v5" / "td_query_information_guard.py")
    components = {
        "query_guard_sha256": query_guard_sha,
        "registry_sha256": registry_sha,
    }
    bundle_sha = hashlib.sha256(json.dumps(components, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return {
        "schema": "JEPA_TD_REAL_STRUCTURAL_GATE_QUALIFICATION_V1",
        "status": "PASS_OUTCOME_BLIND_STRUCTURAL_EXECUTOR_MECHANICS",
        "registry_sha256": registry_sha,
        "query_guard_sha256": query_guard_sha,
        "executor_bundle_sha256": bundle_sha,
        "candidate_outcomes_opened": False,
        "real_tournament_authorized": False,
    }


def test_authenticated_structural_executor_emits_bridge_compatible_identity_and_raw_evidence():
    receipt = _qualification_receipt()
    evidence = {
        "locality_rule_prefrozen": True,
        "fine_neighborhood_mining_used": False,
    }
    output = R.execute_structural_gate(
        "R2_LOCALITY_RULE_FROZEN_NO_FINE_MINING",
        evidence,
        qualification_receipt=receipt,
    )
    rule = R.RULES["R2_LOCALITY_RULE_FROZEN_NO_FINE_MINING"]
    assert output == {
        "status": "PASS",
        "qualified_gate_executor_sha256": receipt["executor_bundle_sha256"],
        "estimand_sha256": rule["estimand_sha256"],
        "decision_rule_sha256": rule["decision_rule_sha256"],
        "evidence_payload_sha256": R.canonical_sha256(evidence),
        "raw_sufficient_statistics": evidence,
    }


def test_authenticated_structural_executor_preserves_not_estimable_and_fail():
    receipt = _qualification_receipt()
    missing = R.execute_structural_gate(
        "Q2_Q_EXCLUDED_TEACHER_PRIMARY_ANCHOR", {}, qualification_receipt=receipt
    )
    failed = R.execute_structural_gate(
        "Q2_Q_EXCLUDED_TEACHER_PRIMARY_ANCHOR",
        {"q_excluded_teacher_primary_anchor": False},
        qualification_receipt=receipt,
    )
    assert missing["status"] == "NOT_ESTIMABLE"
    assert failed["status"] == "FAIL"


def test_structural_executor_refuses_tampered_or_authorizing_qualification_receipt():
    receipt = _qualification_receipt()
    tampered = dict(receipt, registry_sha256="0" * 64)
    with pytest.raises(R.GateRuleError):
        R.execute_structural_gate(
            "R2_LOCALITY_RULE_FROZEN_NO_FINE_MINING",
            {"locality_rule_prefrozen": True, "fine_neighborhood_mining_used": False},
            qualification_receipt=tampered,
        )
    authorizing = dict(receipt, real_tournament_authorized=True)
    with pytest.raises(R.GateRuleError):
        R.execute_structural_gate(
            "R2_LOCALITY_RULE_FROZEN_NO_FINE_MINING",
            {"locality_rule_prefrozen": True, "fine_neighborhood_mining_used": False},
            qualification_receipt=authorizing,
        )


def test_quantitative_gate_cannot_use_structural_executor_even_with_valid_receipt():
    with pytest.raises(R.GateRuleError):
        R.execute_structural_gate(
            "G2_NONTRIVIAL_BIOLOGICAL_CONTENT", {}, qualification_receipt=_qualification_receipt()
        )
