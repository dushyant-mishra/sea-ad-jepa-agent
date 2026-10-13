from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "v5"))

import audit_td_real_gate_executor_readiness_v3 as A  # noqa: E402
import td_real_gate_rule_registry_v1 as R  # noqa: E402


EXPECTED_BUNDLE = "d97c75ce673b2fe629289ffb8597061c21fe7da7e13fa0f8401e617ff7989ee8"


def test_v3_promotes_only_qualified_structural_roles_and_keeps_real_tournament_blocked():
    result = A.audit()
    assert result["candidate_gate_rows"] == 198
    assert result["required_roles"] == 117
    assert result["readiness_counts"] == {
        "CALLABLE_AND_QUALIFIED": 17,
        "CALLABLE_NEEDS_QUALIFICATION": 0,
        "RULE_NOT_MATERIALIZED": 100,
        "BLOCKED_ON_DEPENDENCY": 0,
        "NOT_APPLICABLE": 81,
    }
    assert result["qualified_executor_bundle_sha256"] == EXPECTED_BUNDLE
    assert result["real_tournament_qualify_eligible"] is False
    assert all(value is False for value in result["authority"].values())


def test_v3_all_qualified_rows_are_exactly_the_five_structural_gate_roles():
    rows = A.project_rows()
    qualified = [row for row in rows if row["readiness"] == "CALLABLE_AND_QUALIFIED"]
    assert len(qualified) == 17
    assert {row["gate_id"] for row in qualified} == R.CALLABLE_STRUCTURAL
    for row in qualified:
        rule = R.RULES[row["gate_id"]]
        assert row["qualified_gate_executor_sha256"] == EXPECTED_BUNDLE
        assert row["estimand_sha256"] == rule["estimand_sha256"]
        assert row["decision_rule_sha256"] == rule["decision_rule_sha256"]
        assert row["callable_implementation"] == "td_real_gate_rule_registry_v1.execute_structural_gate"
        assert row["blocker"] == ""


def test_v3_never_promotes_unmaterialized_quantitative_roles():
    rows = A.project_rows()
    counts = Counter(row["readiness"] for row in rows)
    assert counts["RULE_NOT_MATERIALIZED"] == 100
    for row in rows:
        if row["required"] == "True" and row["gate_id"] not in R.CALLABLE_STRUCTURAL:
            assert row["readiness"] == "RULE_NOT_MATERIALIZED"
            assert row["blocker"] == "BLOCKED_PROSPECTIVE_RULE_REQUIRED"
            assert row["qualified_gate_executor_sha256"] == ""


def test_v3_fails_closed_if_frozen_qualification_receipt_is_tampered(tmp_path):
    original = A.load_qualification_receipt()
    bad = dict(original, registry_sha256="0" * 64)
    path = tmp_path / "bad.json"
    import json
    path.write_text(json.dumps(bad), encoding="utf-8")
    try:
        A.project_rows(qualification_receipt_path=path)
    except A.ReadinessV3Error:
        pass
    else:
        raise AssertionError("tampered qualification receipt must fail closed")
