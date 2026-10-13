from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STATE = ROOT / "results/target_discovery/TD_CONTROLLER_CONVERGENCE_STATE_20261013.json"
RECOVERY = ROOT / "results/target_discovery/real_tournament/TD_REAL_QUANTITATIVE_RULE_RECOVERY_MAP_V1.json"


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_synthetic_qualification_does_not_create_real_authority():
    state = _load(STATE)
    assert state["synthetic_phase2"]["qualification_status"] == "QUALIFIED"
    assert state["synthetic_phase2"]["audit_status"] == "PASS_PHASE2_EXECUTION_AND_CUSTODY"
    assert state["synthetic_phase2"]["challenge_count"] == 9
    assert state["synthetic_phase2"]["matched_count"] == 9
    assert state["synthetic_phase2"]["scientific_scope"] == "TEST_QUALIFICATION_ONLY"
    assert all(value is False for value in state["authority"].values())


def test_unresolved_real_gate_map_remains_fully_blocked():
    state = _load(STATE)
    recovery = _load(RECOVERY)
    gates = recovery["gates"]
    assert len(gates) == 28
    assert all(record["readiness_after_audit"] == "RULE_NOT_MATERIALIZED" for record in gates.values())
    assert recovery["candidate_outcomes_opened"] is False
    assert recovery["historical_descriptive_cutoffs_promoted"] is False
    assert recovery["real_tournament_qualify_eligible"] is False
    assert state["real_tournament_readiness"]["unique_unresolved_rules"] == len(gates)
    assert state["real_tournament_readiness"]["real_tournament_qualify_eligible"] is False
    assert state["real_tournament_readiness"]["biological_outcomes_opened"] is False


def test_terminal_cannot_be_misread_as_target_selection():
    state = _load(STATE)
    assert state["terminal"] == (
        "SYNTHETIC_RELATIONAL_TEST_QUALIFIED__REAL_TOURNAMENT_BLOCKED_ON_PROSPECTIVE_RULES__NO_BIOLOGICAL_AUTHORITY"
    )
    text = " ".join(state["interpretation"]["not_established"])
    assert "human biological target" in text
    assert state["real_tournament_readiness"]["rule_not_materialized_required_roles"] > 0
