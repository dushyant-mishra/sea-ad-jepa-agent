from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "v5"))

import audit_td_real_gate_executor_readiness_v2 as A  # noqa: E402
import td_real_gate_rule_registry_v1 as R  # noqa: E402
import td_real_tournament_contract_v1 as C  # noqa: E402


def test_v2_projection_preserves_exact_cartesian_matrix_and_authority_boundary():
    result = A.audit()
    assert result["candidate_gate_rows"] == 198
    assert result["required_roles"] == 117
    assert result["readiness_counts"] == {
        "CALLABLE_AND_QUALIFIED": 0,
        "CALLABLE_NEEDS_QUALIFICATION": 17,
        "RULE_NOT_MATERIALIZED": 100,
        "BLOCKED_ON_DEPENDENCY": 0,
        "NOT_APPLICABLE": 81,
    }
    assert result["real_tournament_qualify_eligible"] is False
    assert all(value is False for value in result["authority"].values())


def test_v2_projection_reuses_one_rule_per_gate_across_candidate_roles():
    rows = A.project_rows()
    callable_rows = [row for row in rows if row["readiness"] == "CALLABLE_NEEDS_QUALIFICATION"]
    assert len(callable_rows) == 17
    by_gate = {}
    for row in callable_rows:
        gate = row["gate_id"]
        identity = (
            row["callable_implementation"], row["estimand_sha256"],
            row["decision_rule_sha256"], row["threshold_source"],
        )
        by_gate.setdefault(gate, set()).add(identity)
    assert set(by_gate) == R.CALLABLE_STRUCTURAL
    assert all(len(identities) == 1 for identities in by_gate.values())


def test_v2_projection_keeps_every_other_required_role_blocked_and_nonrequired_na():
    rows = A.project_rows()
    counts = Counter(row["readiness"] for row in rows)
    assert counts["RULE_NOT_MATERIALIZED"] == 100
    assert counts["NOT_APPLICABLE"] == 81
    for row in rows:
        required = row["required"] == "True"
        if not required:
            assert row["readiness"] == "NOT_APPLICABLE"
        elif row["gate_id"] not in R.CALLABLE_STRUCTURAL:
            assert row["readiness"] == "RULE_NOT_MATERIALIZED"
            assert row["blocker"] == "BLOCKED_PROSPECTIVE_RULE_REQUIRED"
            assert row["callable_implementation"] == ""
            assert row["estimand_sha256"] == ""
            assert row["decision_rule_sha256"] == ""


def test_v2_projection_preserves_donor_source_support_and_candidate_falsifiers():
    contract = C.load_real_tournament_contract()
    registry = C.validate_candidate_registry(contract)
    for row in A.project_rows():
        if row["required"] != "True":
            continue
        assert row["primary_biological_unit"] == "donor"
        assert row["source_semantics"] == "observation_operator_not_biological_replicate"
        assert A.decode_json(row["support_eligibility_rule"]) == contract["support_semantics"]
        assert A.decode_json(row["mandatory_candidate_falsifiers"]) == registry[row["candidate_id"]]["mandatory_falsifiers"]
