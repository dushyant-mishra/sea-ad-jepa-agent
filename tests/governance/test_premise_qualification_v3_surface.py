import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
STATE = ROOT / "docs/agent/JEPA_PREMISE_QUALIFICATION_V3_STATE_20261006.json"
VALIDATOR = ROOT / "scripts/governance/verify_premise_qualification_v3_surface.py"


def _load_validator():
    spec = importlib.util.spec_from_file_location("premise_v3_validator", VALIDATOR)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_v3_state_is_fail_closed_and_neutral():
    state = json.loads(STATE.read_text())
    assert state["training_authorized"] is False
    assert state["stage_a_execution_authorized"] is False
    assert state["optimizer_updates_during_target_discrimination"] == 0
    assert state["ema_updates_during_target_discrimination"] == 0
    assert state["test_state"] == "SEALED"
    assert state["morabito_state"] == "PROTECTED"
    assert state["production_target_winner"] is None
    assert state["representation_winner"] is None
    assert state["selected_estimand"] == "UNSET_REQUIRES_APPROVAL"
    assert state["deciding_numeric_thresholds"] == "UNSET_REQUIRES_APPROVAL"
    assert set(state["representation_families"]) == {
        "GLOBAL_CELL_STATE",
        "QUERY_LOCAL_STATE",
        "PROGRAM_STATE",
        "STRUCTURED_COMBINED_STATE",
    }


def test_validator_accepts_canonical_state():
    validator = _load_validator()
    assert validator.validate_state(json.loads(STATE.read_text())) == []


def test_validator_rejects_training_authorization():
    validator = _load_validator()
    state = json.loads(STATE.read_text())
    state["training_authorized"] = True
    assert "training_authorized must remain false" in validator.validate_state(state)


def test_validator_rejects_representation_winner():
    validator = _load_validator()
    state = json.loads(STATE.read_text())
    state["representation_winner"] = "GLOBAL_CELL_STATE"
    assert "representation_winner must remain null" in validator.validate_state(state)


def test_validator_rejects_collapsed_uncertainty_axes():
    validator = _load_validator()
    state = json.loads(STATE.read_text())
    state["uncertainty_axes"]["must_remain_separate"] = False
    assert "biological-evidence and measurement-depth uncertainty must remain separate" in validator.validate_state(state)


def test_validator_rejects_coordinate_claim_from_subspace_only():
    validator = _load_validator()
    state = json.loads(STATE.read_text())
    state["representation_stability"]["coordinate_claim_allowed_when_subspace_only"] = True
    assert "coordinate claims are forbidden for stable-subspace-only results" in validator.validate_state(state)


def test_validator_rejects_unrestricted_dataset_identity():
    validator = _load_validator()
    state = json.loads(STATE.read_text())
    state["observation_operator"]["forbidden_free_shortcuts"] = ["DONOR_ID"]
    assert "unrestricted dataset and arbitrary matrix identifiers must remain forbidden shortcuts" in validator.validate_state(state)


def test_validator_rejects_estimand_selection():
    validator = _load_validator()
    state = json.loads(STATE.read_text())
    state["selected_estimand"] = "DONOR_WEIGHTED"
    assert "selected_estimand must remain UNSET_REQUIRES_APPROVAL" in validator.validate_state(state)
