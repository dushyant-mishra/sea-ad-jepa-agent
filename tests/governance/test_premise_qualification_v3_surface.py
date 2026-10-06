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


def _state():
    return json.loads(STATE.read_text())


def test_v3_state_is_fail_closed_and_neutral():
    state = _state()
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
    assert validator.validate_state(_state()) == []


def test_validator_rejects_training_authorization():
    validator = _load_validator()
    state = _state()
    state["training_authorized"] = True
    assert "training_authorized must remain false" in validator.validate_state(state)


def test_validator_rejects_representation_winner():
    validator = _load_validator()
    state = _state()
    state["representation_winner"] = "GLOBAL_CELL_STATE"
    assert "representation_winner must remain null" in validator.validate_state(state)


def test_validator_rejects_collapsed_uncertainty_axes():
    validator = _load_validator()
    state = _state()
    state["uncertainty_axes"]["must_remain_separate"] = False
    assert "biological-evidence and measurement-depth uncertainty must remain separate" in validator.validate_state(state)


def test_validator_rejects_coordinate_claim_from_subspace_only():
    validator = _load_validator()
    state = _state()
    state["representation_stability"]["coordinate_claim_allowed_when_subspace_only"] = True
    assert "coordinate claims are forbidden for stable-subspace-only results" in validator.validate_state(state)


def test_validator_rejects_unrestricted_dataset_identity():
    validator = _load_validator()
    state = _state()
    state["observation_operator"]["forbidden_free_shortcuts"] = ["DONOR_ID"]
    assert "unrestricted dataset and arbitrary matrix identifiers must remain forbidden shortcuts" in validator.validate_state(state)


def test_validator_rejects_estimand_selection():
    validator = _load_validator()
    state = _state()
    state["selected_estimand"] = "DONOR_WEIGHTED"
    assert "selected_estimand must remain UNSET_REQUIRES_APPROVAL" in validator.validate_state(state)


def test_validator_rejects_recoverability_conflation():
    validator = _load_validator()
    state = _state()
    state["recoverability_semantics"]["automatic_equivalence_forbidden"] = False
    assert "target-object recoverability must not be equated with biological-truth recoverability" in validator.validate_state(state)


def test_validator_rejects_collapsed_transfer_axes():
    validator = _load_validator()
    state = _state()
    state["transport_axes"] = ["DONOR_TRANSFER", "TECHNOLOGY_TRANSFER"]
    assert "donor/operator/study/technology transfer axes must remain separate" in validator.validate_state(state)


def test_validator_rejects_collapsed_ood_axes():
    validator = _load_validator()
    state = _state()
    state["ood_axes"] = ["GENERIC_OOD"]
    assert "biological-support OOD and measurement-regime OOD must remain separate" in validator.validate_state(state)


def test_validator_rejects_claim_ladder_shortening():
    validator = _load_validator()
    state = _state()
    state["claim_ladder"] = ["RNA_REPRESENTATION", "TRANSFERABLE_BIOLOGICAL_STATE"]
    assert "claim ladder must preserve four non-automatic levels" in validator.validate_state(state)


def test_validator_rejects_stage_a_biological_promotion():
    validator = _load_validator()
    state = _state()
    state["stage_a_maximum_claim"] = "TRANSFERABLE_BIOLOGICAL_STATE"
    assert "Stage A maximum claim must remain RNA_REPRESENTATION" in validator.validate_state(state)


def test_validator_rejects_protected_asset_selection():
    validator = _load_validator()
    state = _state()
    state["external_asset_rules"]["protected_assets_forbidden_for_target_selection"] = False
    assert "protected assets must remain forbidden for target selection" in validator.validate_state(state)


def test_validator_rejects_cell_count_as_donor_substitute():
    validator = _load_validator()
    state = _state()
    state["external_asset_rules"]["cell_count_cannot_substitute_for_donor_count"] = False
    assert "cell count must not substitute for donor count" in validator.validate_state(state)


def test_validator_rejects_observational_to_causal_promotion():
    validator = _load_validator()
    state = _state()
    state["external_asset_rules"]["observational_multimodal_support_is_not_causal"] = False
    assert "observational multimodal support must not be promoted to causal evidence" in validator.validate_state(state)
