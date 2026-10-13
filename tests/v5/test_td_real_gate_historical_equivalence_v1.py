from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "v5"))

import td_real_gate_rule_registry_v1 as R  # noqa: E402

LEDGER = ROOT / "results" / "target_discovery" / "real_tournament" / "TD_REAL_GATE_HISTORICAL_EQUIVALENCE_V1.json"


def _load():
    with LEDGER.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def test_equivalence_ledger_partitions_exact_33_gate_universe_without_promotion_drift():
    ledger = _load()
    assert ledger["schema"] == "JEPA_TD_REAL_GATE_HISTORICAL_EQUIVALENCE_V1"
    groups = ledger["gate_groups"]
    assert set(groups) == {
        "EXACT_COMPONENT_REUSED_WITH_GATE_WRAPPER",
        "NEW_PROSPECTIVE_STRUCTURAL_WRAPPER",
        "NO_EXACT_QUALIFIED_GATE_EXECUTOR_FOUND__PROSPECTIVE_RULE_REQUIRED",
    }
    all_gates = [gate for group in groups.values() for gate in group]
    assert len(all_gates) == len(set(all_gates)) == 33
    assert set(all_gates) == set(R.RULES)
    assert set(groups["EXACT_COMPONENT_REUSED_WITH_GATE_WRAPPER"]) == {
        "Q1_Q_SCALAR_STUDENT_ABSENT",
        "Q3_TARGET_NORMALIZATION_Q_SCALAR_FREE",
    }
    assert set(groups["NEW_PROSPECTIVE_STRUCTURAL_WRAPPER"]) == {
        "G1_INTEGRITY_LINEAGE",
        "R2_LOCALITY_RULE_FROZEN_NO_FINE_MINING",
        "Q2_Q_EXCLUDED_TEACHER_PRIMARY_ANCHOR",
    }
    assert set(groups["NO_EXACT_QUALIFIED_GATE_EXECUTOR_FOUND__PROSPECTIVE_RULE_REQUIRED"]) == set(R.RULES) - R.CALLABLE_STRUCTURAL


def test_exact_reuse_is_bound_to_the_existing_query_information_guard_and_tests():
    ledger = _load()
    reuse = ledger["exact_reuse_evidence"]
    assert set(reuse) == {"Q1_Q_SCALAR_STUDENT_ABSENT", "Q3_TARGET_NORMALIZATION_Q_SCALAR_FREE"}
    for gate_id, evidence in reuse.items():
        assert evidence == {
            "path": "scripts/v5/td_query_information_guard.py",
            "git_blob_sha": "3ca60c5f82b7b07f5f6123a52e7b50f9027a6ebe",
            "test_path": "tests/v5/test_td_query_information_guard.py",
            "test_git_blob_sha": "849cfd9b65fadd0c54dfb9f534bcdddc413b4c98",
            "equivalence_scope": "dependency-lineage exclusion of direct/transitive q scalar from the relevant sink only",
            "does_not_supply_biological_threshold": True,
        }
        assert R.RULES[gate_id]["historical_reuse"]["git_blob_sha"] == evidence["git_blob_sha"]


def test_ledger_does_not_promote_historical_descriptive_cutoffs_or_authority():
    ledger = _load()
    assert ledger["historical_descriptive_cutoffs_promoted"] is False
    assert ledger["candidate_outcomes_opened"] is False
    assert ledger["real_tournament_qualify_eligible"] is False
    assert all(value is False for value in ledger["authority"].values())
    unresolved = ledger["gate_groups"]["NO_EXACT_QUALIFIED_GATE_EXECUTOR_FOUND__PROSPECTIVE_RULE_REQUIRED"]
    assert "G6_TEACHER_INFORMATION_ADVANTAGE" in unresolved
    assert "C6_INCREMENT_OVER_C1_C3" in unresolved
    assert "C4_INCREMENT_OVER_CONSTITUENTS" in unresolved
