import importlib.util
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
STATE = ROOT / "docs/agent/JEPA_PREMISE_QUALIFICATION_V3_STATE_20261006.json"
VALIDATOR = ROOT / "scripts/governance/verify_premise_qualification_v3_surface.py"
WORKFLOW = ROOT / ".github/workflows/premise-qualification-v3-surface-guard.yml"
DESIGN = ROOT / "docs/superpowers/specs/2026-10-06-premise-qualification-contract-v3-design.md"
REPRESENTATION_CONTRACT = ROOT / "docs/agent/JEPA_REPRESENTATION_FAMILY_QUALIFICATION_V3_PREFREEZE_20261006.md"


def _load_validator():
    spec = importlib.util.spec_from_file_location("premise_v3_validator", VALIDATOR)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


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
        "GLOBAL_CELL_STATE", "QUERY_LOCAL_STATE", "PROGRAM_STATE", "STRUCTURED_COMBINED_STATE"
    }


def test_machine_state_binds_all_hard_execution_boundaries():
    state = _state()
    assert state["multimodal_training_authorized"] is False
    assert state["stage4_authorized"] is False
    assert state["five_hundred_k_authorized"] is False


def test_all_machine_referenced_source_documents_exist():
    state = _state()
    missing = [path for path in state["source_documents"] if not (ROOT / path).is_file()]
    assert missing == []


def test_every_binding_source_document_triggers_guard():
    workflow = WORKFLOW.read_text()
    for path in _state()["source_documents"]:
        assert path in workflow, f"binding source does not trigger V3 guard: {path}"


def test_binding_docs_use_canonical_stability_status_vocabulary():
    text = DESIGN.read_text() + "\n" + REPRESENTATION_CONTRACT.read_text()
    for stale in ("AXES_STABLE", "SUBSPACE_STABLE_AXES_ROTATE", "SUBSPACE_UNSTABLE"):
        assert stale not in text, f"stale stability status remains in binding prose: {stale}"


def test_validator_accepts_canonical_state():
    validator = _load_validator()
    assert validator.validate_state(_state()) == []


def test_cli_accepts_canonical_state():
    result = subprocess.run([sys.executable, str(VALIDATOR)], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0
    assert "PASS:" in result.stdout


def test_cli_rejects_supplied_corrupt_state(tmp_path):
    state = _state()
    state["training_authorized"] = True
    result = _run_cli(state, tmp_path)
    assert result.returncode != 0
    assert "training_authorized must remain false" in result.stdout


def test_cli_rejects_missing_required_contract_field(tmp_path):
    state = _state()
    del state["stage_a_verdicts"]
    result = _run_cli(state, tmp_path)
    assert result.returncode != 0
    assert "missing required contract fields" in result.stdout


def test_cli_rejects_unrecognized_top_level_contract_field(tmp_path):
    state = _state()
    state["surprise_authority"] = True
    result = _run_cli(state, tmp_path)
    assert result.returncode != 0
    assert "unrecognized contract fields" in result.stdout


def test_cli_rejects_unrecognized_nested_contract_field(tmp_path):
    state = _state()
    state["diagnostic_readout_firewall"]["held_out_override"] = True
    result = _run_cli(state, tmp_path)
    assert result.returncode != 0
    assert "unrecognized diagnostic_readout_firewall fields" in result.stdout


def test_validator_rejects_training_authorization():
    validator = _load_validator(); state = _state(); state["training_authorized"] = True
    assert "training_authorized must remain false" in validator.validate_state(state)


def test_validator_rejects_multimodal_training_authorization():
    validator = _load_validator(); state = _state(); state["multimodal_training_authorized"] = True
    assert "multimodal training must remain unauthorized" in validator.validate_state(state)


def test_validator_rejects_stage4_or_500k_authorization():
    validator = _load_validator(); state = _state(); state["stage4_authorized"] = True
    assert "Stage 4 must remain unauthorized" in validator.validate_state(state)
    state = _state(); state["five_hundred_k_authorized"] = True
    assert "500K must remain unauthorized" in validator.validate_state(state)


def test_validator_rejects_representation_winner():
    validator = _load_validator(); state = _state(); state["representation_winner"] = "GLOBAL_CELL_STATE"
    assert "representation_winner must remain null" in validator.validate_state(state)


def test_validator_rejects_collapsed_uncertainty_axes():
    validator = _load_validator(); state = _state(); state["uncertainty_axes"]["must_remain_separate"] = False
    assert "biological-evidence and measurement-depth uncertainty must remain separate" in validator.validate_state(state)


def test_validator_rejects_same_operator_for_bio_evidence_and_depth():
    validator = _load_validator(); state = _state()
    state["uncertainty_axes"]["biological_evidence_convergence"]["operator_class"] = "COUNT_DEPTH_THINNING"
    assert "biological-evidence perturbation must not be count-depth thinning" in validator.validate_state(state)


def test_validator_requires_measurement_depth_to_hold_information_universe_fixed():
    validator = _load_validator(); state = _state()
    state["uncertainty_axes"]["measurement_depth_convergence"]["information_universe_fixed"] = False
    assert "measurement-depth perturbation must hold the information universe fixed" in validator.validate_state(state)


def test_validator_rejects_coordinate_claim_from_subspace_only():
    validator = _load_validator(); state = _state(); state["representation_stability"]["coordinate_claim_allowed_when_subspace_only"] = True
    assert "coordinate claims are forbidden for stable-subspace-only results" in validator.validate_state(state)


def test_validator_requires_inner_train_frozen_alignment():
    validator = _load_validator(); state = _state()
    state["representation_stability"]["alignment_fit_partition"] = "HELD_DONOR"
    assert "coordinate alignment must fit on inner TRAIN and freeze before held-donor evaluation" in validator.validate_state(state)


def test_validator_rejects_held_donor_influence_on_alignment():
    validator = _load_validator(); state = _state()
    state["representation_stability"]["held_out_donors_may_influence_alignment"] = True
    assert "held-out donors must not influence coordinate alignment" in validator.validate_state(state)


def test_validator_rejects_unrestricted_dataset_identity():
    validator = _load_validator(); state = _state(); state["observation_operator"]["forbidden_free_shortcuts"] = ["DONOR_ID"]
    assert "unrestricted dataset and arbitrary matrix identifiers must remain forbidden shortcuts" in validator.validate_state(state)


def test_validator_rejects_donor_id_as_free_observation_covariate():
    validator = _load_validator(); state = _state()
    state["observation_operator"]["forbidden_free_shortcuts"] = ["UNRESTRICTED_DATASET_ID", "ARBITRARY_MATRIX_ID"]
    assert "donor identity must remain a forbidden free observation shortcut" in validator.validate_state(state)


def test_validator_requires_outcome_and_study_memorization_shortcuts_to_remain_forbidden():
    validator = _load_validator(); state = _state()
    state["observation_operator"]["forbidden_free_shortcuts"] = [
        "DONOR_ID", "UNRESTRICTED_DATASET_ID", "ARBITRARY_MATRIX_ID"
    ]
    assert "pathology/outcome and unrestricted study identity must remain forbidden observation shortcuts" in validator.validate_state(state)


def test_validator_rejects_blanket_technology_invariance_requirement():
    validator = _load_validator(); state = _state(); state["observation_operator"]["technology_invariance_is_not_blanket_requirement"] = False
    assert "technology invariance must not become a blanket qualification rule" in validator.validate_state(state)


def test_validator_rejects_estimand_selection():
    validator = _load_validator(); state = _state(); state["selected_estimand"] = "DONOR_WEIGHTED"
    assert "selected_estimand must remain UNSET_REQUIRES_APPROVAL" in validator.validate_state(state)


def test_validator_rejects_estimand_roster_drift():
    validator = _load_validator(); state = _state(); state["estimand_candidates"] = ["CELL_WEIGHTED_EMPIRICAL", "DONOR_WEIGHTED"]
    assert "estimand candidate roster must remain prospectively explicit" in validator.validate_state(state)


def test_validator_rejects_post_hoc_tempering_parameter():
    validator = _load_validator(); state = _state(); state["hierarchical_tempering_parameter"] = "TUNE_ON_BIOLOGICAL_OUTCOME"
    assert "hierarchical tempering may not be tuned post hoc on biological outcomes" in validator.validate_state(state)


def test_validator_rejects_recoverability_conflation():
    validator = _load_validator(); state = _state(); state["recoverability_semantics"]["automatic_equivalence_forbidden"] = False
    assert "target-object recoverability must not be equated with biological-truth recoverability" in validator.validate_state(state)


def test_validator_rejects_collapsed_transfer_axes():
    validator = _load_validator(); state = _state(); state["transport_axes"] = ["DONOR_TRANSFER", "TECHNOLOGY_TRANSFER"]
    assert "donor/operator/study/technology transfer axes must remain separate" in validator.validate_state(state)


def test_validator_rejects_collapsed_ood_axes():
    validator = _load_validator(); state = _state(); state["ood_axes"] = ["GENERIC_OOD"]
    assert "biological-support OOD and measurement-regime OOD must remain separate" in validator.validate_state(state)


def test_validator_rejects_claim_ladder_shortening():
    validator = _load_validator(); state = _state(); state["claim_ladder"] = ["RNA_REPRESENTATION", "TRANSFERABLE_BIOLOGICAL_STATE"]
    assert "claim ladder must preserve four non-automatic levels" in validator.validate_state(state)


def test_validator_rejects_stage_a_biological_promotion():
    validator = _load_validator(); state = _state(); state["stage_a_maximum_claim"] = "TRANSFERABLE_BIOLOGICAL_STATE"
    assert "Stage A maximum claim must remain RNA_REPRESENTATION" in validator.validate_state(state)


def test_validator_rejects_protected_asset_selection():
    validator = _load_validator(); state = _state(); state["external_asset_rules"]["protected_assets_forbidden_for_target_selection"] = False
    assert "protected assets must remain forbidden for target selection" in validator.validate_state(state)


def test_validator_rejects_cell_count_as_donor_substitute():
    validator = _load_validator(); state = _state(); state["external_asset_rules"]["cell_count_cannot_substitute_for_donor_count"] = False
    assert "cell count must not substitute for donor count" in validator.validate_state(state)


def test_validator_rejects_observational_to_causal_promotion():
    validator = _load_validator(); state = _state(); state["external_asset_rules"]["observational_multimodal_support_is_not_causal"] = False
    assert "observational multimodal support must not be promoted to causal evidence" in validator.validate_state(state)


def test_validator_rejects_external_equal_independent():
    validator = _load_validator(); state = _state(); state["external_asset_rules"]["external_not_equal_independent"] = False
    assert "external assets must not be assumed independent" in validator.validate_state(state)


def test_validator_rejects_access_equal_exposure():
    validator = _load_validator(); state = _state(); state["external_asset_rules"]["access_not_equal_exposure"] = False
    assert "access and prior exposure must remain separate axes" in validator.validate_state(state)


def test_validator_rejects_pairing_class_collapse():
    validator = _load_validator(); state = _state(); state["external_asset_rules"]["same_nucleus_pairing_not_equal_separate_nucleus_evidence"] = False
    assert "same-nucleus and separate-nucleus evidence classes must remain distinct" in validator.validate_state(state)


def test_validator_rejects_unknown_field_guessing():
    validator = _load_validator(); state = _state(); state["external_asset_rules"]["unknown_fields_fail_closed"] = False
    assert "unknown external-asset fields must fail closed" in validator.validate_state(state)
