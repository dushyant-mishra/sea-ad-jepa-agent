from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "v5"))

import td_real_gate_rule_registry_v1 as R  # noqa: E402
import td_real_tournament_contract_v1 as C  # noqa: E402


CALLABLE_STRUCTURAL = {
    "G1_INTEGRITY_LINEAGE",
    "R2_LOCALITY_RULE_FROZEN_NO_FINE_MINING",
    "Q1_Q_SCALAR_STUDENT_ABSENT",
    "Q2_Q_EXCLUDED_TEACHER_PRIMARY_ANCHOR",
    "Q3_TARGET_NORMALIZATION_Q_SCALAR_FREE",
}
QUERY_GUARD_SHA = "3ca60c5f82b7b07f5f6123a52e7b50f9027a6ebe"
QUERY_GUARD_TEST_SHA = "849cfd9b65fadd0c54dfb9f534bcdddc413b4c98"


def _gate_universe():
    contract = C.load_real_tournament_contract()
    registry = C.validate_candidate_registry(contract)
    return list(dict.fromkeys(g for candidate in C.CANDIDATE_IDS for g in registry[candidate]["required_gates"]))


def test_registry_covers_exact_frozen_gate_universe_once():
    universe = _gate_universe()
    assert len(universe) == 33
    assert set(R.RULES) == set(universe)
    assert R.validate_rule_registry() == {
        "gate_count": 33,
        "callable_structural_count": len(CALLABLE_STRUCTURAL),
        "blocked_quantitative_count": 33 - len(CALLABLE_STRUCTURAL),
    }


def test_only_explicitly_structural_rules_are_callable_before_quantitative_prefreeze():
    assert {gate for gate, rule in R.RULES.items() if rule["readiness"] == "CALLABLE_NEEDS_QUALIFICATION"} == CALLABLE_STRUCTURAL
    for gate_id, rule in R.RULES.items():
        assert rule["gate_id"] == gate_id
        assert rule["primary_biological_unit"] == "donor"
        assert rule["source_semantics"] == "observation_operator_not_biological_replicate"
        if gate_id in CALLABLE_STRUCTURAL:
            assert rule["rule_kind"] == "STRUCTURAL_PROVENANCE"
            assert rule["callable_implementation"] == "td_real_gate_rule_registry_v1.execute_structural_gate"
            assert len(rule["estimand_sha256"]) == 64
            assert len(rule["decision_rule_sha256"]) == 64
            assert rule["threshold_source"] == "NO_NUMERIC_THRESHOLD__FROZEN_STRUCTURAL_RULE"
        else:
            assert rule["readiness"] == "RULE_NOT_MATERIALIZED"
            assert rule["callable_implementation"] == ""
            assert rule["estimand_sha256"] == ""
            assert rule["decision_rule_sha256"] == ""
            assert rule["threshold_source"] == "BLOCKED_PROSPECTIVE_RULE_REQUIRED"


def test_q1_q3_reuse_exact_historical_dependency_guard():
    for gate_id in {"Q1_Q_SCALAR_STUDENT_ABSENT", "Q3_TARGET_NORMALIZATION_Q_SCALAR_FREE"}:
        reuse = R.RULES[gate_id]["historical_reuse"]
        assert reuse == {
            "path": "scripts/v5/td_query_information_guard.py",
            "git_blob_sha": QUERY_GUARD_SHA,
            "test_path": "tests/v5/test_td_query_information_guard.py",
            "test_git_blob_sha": QUERY_GUARD_TEST_SHA,
            "status": "EXACT_COMPONENT_REUSED_WITH_GATE_WRAPPER",
        }


def test_g6_remains_blocked_because_exact_contrast_and_threshold_are_not_frozen():
    rule = R.RULES["G6_TEACHER_INFORMATION_ADVANTAGE"]
    assert rule["readiness"] == "RULE_NOT_MATERIALIZED"
    assert rule["threshold_source"] == "BLOCKED_PROSPECTIVE_RULE_REQUIRED"
    with pytest.raises(R.GateRuleError):
        R.evaluate_structural_gate("G6_TEACHER_INFORMATION_ADVANTAGE", {})


def test_structural_rules_are_missing_evidence_not_estimable_and_contradictions_fail():
    for gate_id in CALLABLE_STRUCTURAL:
        assert R.evaluate_structural_gate(gate_id, {}) == "NOT_ESTIMABLE"

    assert R.evaluate_structural_gate(
        "R2_LOCALITY_RULE_FROZEN_NO_FINE_MINING",
        {"locality_rule_prefrozen": True, "fine_neighborhood_mining_used": True},
    ) == "FAIL"
    assert R.evaluate_structural_gate(
        "Q1_Q_SCALAR_STUDENT_ABSENT",
        {
            "dependency_graph": {"student_head": ["q_scalar"], "q_scalar": []},
            "dependency_roles": {"student_head": "student_sink", "q_scalar": "q_scalar"},
        },
    ) == "FAIL"
    assert R.evaluate_structural_gate(
        "Q3_TARGET_NORMALIZATION_Q_SCALAR_FREE",
        {
            "dependency_graph": {"target_norm": ["q_scalar"], "q_scalar": []},
            "dependency_roles": {"target_norm": "target_normalization_sink", "q_scalar": "q_scalar"},
        },
    ) == "FAIL"


def test_structural_rules_pass_only_when_frozen_predicates_are_satisfied():
    identities = {
        "code": "a" * 64,
        "population": "b" * 64,
        "split": "c" * 64,
        "support": "d" * 64,
        "operator": "e" * 64,
        "teacher_student_evidence_rights": "f" * 64,
        "null_seed": "1" * 64,
        "prefreeze": "2" * 64,
    }
    assert R.evaluate_structural_gate(
        "G1_INTEGRITY_LINEAGE",
        {
            "required_identity_names": list(identities),
            "bound_identity_sha256": identities,
            "post_outcome_redesign": False,
            "post_outcome_relabeling": False,
        },
    ) == "PASS"
    assert R.evaluate_structural_gate(
        "R2_LOCALITY_RULE_FROZEN_NO_FINE_MINING",
        {"locality_rule_prefrozen": True, "fine_neighborhood_mining_used": False},
    ) == "PASS"
    assert R.evaluate_structural_gate(
        "Q1_Q_SCALAR_STUDENT_ABSENT",
        {
            "dependency_graph": {"student_head": ["q_address", "masked_rna"], "q_address": [], "masked_rna": []},
            "dependency_roles": {"student_head": "student_sink", "q_address": "q_address", "masked_rna": "lawful_evidence"},
        },
    ) == "PASS"
    assert R.evaluate_structural_gate(
        "Q2_Q_EXCLUDED_TEACHER_PRIMARY_ANCHOR",
        {"q_excluded_teacher_primary_anchor": True},
    ) == "PASS"
    assert R.evaluate_structural_gate(
        "Q3_TARGET_NORMALIZATION_Q_SCALAR_FREE",
        {
            "dependency_graph": {"target_norm": ["context_counts"], "context_counts": []},
            "dependency_roles": {"target_norm": "target_normalization_sink", "context_counts": "teacher_non_q_evidence"},
        },
    ) == "PASS"


def test_query_gate_wrappers_refuse_vacuous_graphs_without_the_relevant_sink():
    evidence = {
        "dependency_graph": {"teacher_aux": []},
        "dependency_roles": {"teacher_aux": "teacher_aux_sink"},
    }
    assert R.evaluate_structural_gate("Q1_Q_SCALAR_STUDENT_ABSENT", evidence) == "FAIL"
    assert R.evaluate_structural_gate("Q3_TARGET_NORMALIZATION_Q_SCALAR_FREE", evidence) == "FAIL"


def test_quantitative_rules_cannot_be_evaluated_through_structural_entrypoint():
    with pytest.raises(R.GateRuleError):
        R.evaluate_structural_gate("G2_NONTRIVIAL_BIOLOGICAL_CONTENT", {})
