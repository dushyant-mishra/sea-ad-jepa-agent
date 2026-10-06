import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
STATE = ROOT / "docs/agent/JEPA_PREMISE_QUALIFICATION_V3_STATE_20261006.json"

EXPECTED_VERDICTS = {
    "QUALIFIED_FOR_RNA_REPRESENTATION",
    "INFORMATIVE_BUT_NOT_QUALIFIED",
    "FAIL_LEAKAGE",
    "FAIL_SHORTCUT",
    "FAIL_TRANSPORT",
    "NONRECOVERABLE_FROM_VIEW",
    "INDETERMINATE",
}


def _state():
    return json.loads(STATE.read_text())


def test_stage_a_verdict_roster_is_frozen():
    assert set(_state()["stage_a_verdicts"]) == EXPECTED_VERDICTS


def test_diagnostic_readout_firewall_is_inner_train_only():
    firewall = _state()["diagnostic_readout_firewall"]
    assert firewall["fit_partition"] == "INNER_TRAIN_ONLY"
    assert firewall["freeze_before_held_donor_evaluation"] is True
    assert firewall["held_out_units_may_influence_fit"] is False
    assert firewall["authorizes_jepa_training"] is False


def test_standalone_claim_and_stage_a_contracts_are_machine_bound():
    sources = set(_state()["source_documents"])
    assert "docs/agent/JEPA_CLAIM_LADDER_V3_PREFREEZE_20261006.md" in sources
    assert "docs/agent/JEPA_STAGE_A_REAL_RNA_TARGET_GATE_V3_PREFREEZE_20261006.md" in sources
