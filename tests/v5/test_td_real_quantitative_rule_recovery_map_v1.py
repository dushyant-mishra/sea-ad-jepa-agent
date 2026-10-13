from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "v5"))

import td_real_gate_rule_registry_v1 as R  # noqa: E402

PATH = ROOT / "results" / "target_discovery" / "real_tournament" / "TD_REAL_QUANTITATIVE_RULE_RECOVERY_MAP_V1.json"


def _load():
    return json.loads(PATH.read_text(encoding="utf-8"))


def test_recovery_map_covers_exact_unresolved_unique_gate_set_without_promotion():
    data = _load()
    unresolved = set(R.RULES) - R.CALLABLE_STRUCTURAL
    assert data["schema"] == "JEPA_TD_REAL_QUANTITATIVE_RULE_RECOVERY_MAP_V1"
    assert set(data["gates"]) == unresolved
    assert len(data["gates"]) == 28
    assert data["candidate_outcomes_opened"] is False
    assert data["historical_descriptive_cutoffs_promoted"] is False
    assert data["real_tournament_qualify_eligible"] is False
    assert all(value is False for value in data["authority"].values())
    assert all(rec["readiness_after_audit"] == "RULE_NOT_MATERIALIZED" for rec in data["gates"].values())


def test_every_unresolved_gate_names_reusable_components_and_exact_remaining_decision():
    data = _load()
    for gate_id, rec in data["gates"].items():
        assert rec["gate_id"] == gate_id
        assert isinstance(rec["reusable_components"], list)
        assert rec["remaining_scientific_decision"]
        assert rec["why_not_promoted"]
        assert rec["threshold_policy"] in {
            "PROSPECTIVE_NUMERIC_OR_DIRECTIONAL_RULE_REQUIRED",
            "PROSPECTIVE_ENDPOINT_AND_RULE_REQUIRED",
            "PROSPECTIVE_SPECIALIST_STRUCTURAL_CONTRACT_REQUIRED",
        }


def test_component_reuse_is_narrow_and_does_not_mislabel_synthetic_helpers_as_real_gate_executors():
    data = _load()
    g8 = data["gates"]["G8_MEASUREMENT_ROBUSTNESS"]
    assert any(component["path"] == "scripts/v5/td_measurement_noise_fixture.py" for component in g8["reusable_components"])
    assert all(component["scope"] != "QUALIFIED_REAL_GATE_EXECUTOR" for rec in data["gates"].values() for component in rec["reusable_components"])

    g6 = data["gates"]["G6_TEACHER_INFORMATION_ADVANTAGE"]
    assert any(component["path"] == "scripts/v5/td_query_information_guard.py" for component in g6["reusable_components"])
    assert "advantage" in g6["remaining_scientific_decision"].lower()


def test_specialist_m_gates_remain_blocked_pending_explicit_specialist_contract():
    data = _load()
    for gate_id in ["M1_CIRCULARITY_CONTROL", "M2_INDEPENDENT_PROVENANCE", "M3_CAUSAL_CLAIM_FALSE", "M4_SUPPORT_ABSTENTION"]:
        rec = data["gates"][gate_id]
        assert rec["threshold_policy"] == "PROSPECTIVE_SPECIALIST_STRUCTURAL_CONTRACT_REQUIRED"
        assert rec["readiness_after_audit"] == "RULE_NOT_MATERIALIZED"
