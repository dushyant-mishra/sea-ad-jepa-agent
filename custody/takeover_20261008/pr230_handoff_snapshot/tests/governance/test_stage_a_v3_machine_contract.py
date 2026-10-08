import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
STATE = ROOT / "docs/agent/JEPA_PREMISE_QUALIFICATION_V3_STATE_20261006.json"
VALIDATOR = ROOT / "scripts/governance/verify_premise_qualification_v3_surface.py"

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


def _run_cli(state: dict, tmp_path):
    supplied = tmp_path / "supplied_state.json"
    supplied.write_text(json.dumps(state))
    return subprocess.run(
        [sys.executable, str(VALIDATOR), str(supplied)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )


def test_stage_a_verdict_roster_is_frozen():
    assert set(_state()["stage_a_verdicts"]) == EXPECTED_VERDICTS


def test_diagnostic_readout_firewall_is_inner_train_only():
    firewall = _state()["diagnostic_readout_firewall"]
    assert firewall["fit_partition"] == "INNER_TRAIN_ONLY"
    assert firewall["freeze_before_held_donor_evaluation"] is True
    assert firewall["held_out_units_may_influence_fit"] is False
    assert firewall["authorizes_jepa_training"] is False


def test_cli_rejects_supplied_stage_a_verdict_drift(tmp_path):
    state = _state()
    state["stage_a_verdicts"] = ["PASS"]
    result = _run_cli(state, tmp_path)
    assert result.returncode != 0
    assert "Stage-A verdict roster must remain frozen" in result.stdout


def test_cli_rejects_supplied_diagnostic_firewall_drift(tmp_path):
    state = _state()
    state["diagnostic_readout_firewall"] = {
        "fit_partition": "ALL_DATA",
        "freeze_before_held_donor_evaluation": False,
        "held_out_units_may_influence_fit": True,
        "authorizes_jepa_training": True,
    }
    result = _run_cli(state, tmp_path)
    assert result.returncode != 0
    assert "diagnostic readout firewall must remain inner-TRAIN-only and frozen before held-donor evaluation" in result.stdout


def test_standalone_claim_and_stage_a_contracts_are_machine_bound():
    sources = set(_state()["source_documents"])
    assert "docs/agent/JEPA_CLAIM_LADDER_V3_PREFREEZE_20261006.md" in sources
    assert "docs/agent/JEPA_STAGE_A_REAL_RNA_TARGET_GATE_V3_PREFREEZE_20261006.md" in sources
