#!/usr/bin/env python3
import json
import sys
from pathlib import Path


EXPECTED_FAMILIES = {
    "GLOBAL_CELL_STATE",
    "QUERY_LOCAL_STATE",
    "PROGRAM_STATE",
    "STRUCTURED_COMBINED_STATE",
}
EXPECTED_TRANSPORT_AXES = {
    "DONOR_TRANSFER",
    "OPERATOR_TRANSFER",
    "STUDY_TRANSFER",
    "TECHNOLOGY_TRANSFER",
}
EXPECTED_OOD_AXES = {
    "BIOLOGICAL_SUPPORT_OOD",
    "MEASUREMENT_REGIME_OOD",
}
EXPECTED_ESTIMANDS = {
    "CELL_WEIGHTED_EMPIRICAL",
    "DONOR_WEIGHTED",
    "SOURCE_BALANCED_DONOR_WEIGHTED",
    "HIERARCHICAL_TEMPERED",
}
EXPECTED_CLAIM_LADDER = [
    "RNA_REPRESENTATION",
    "TRANSFERABLE_BIOLOGICAL_STATE",
    "REGULATORY_SUPPORT",
    "CAUSAL_PERTURBATIONAL_PREDICTION",
]
EXPECTED_TEMPERING_RULE = "SCIENTIFIC_ESTIMAND_PARAMETER__NO_POST_HOC_OUTCOME_TUNING"


def validate_state(state: dict) -> list[str]:
    errors: list[str] = []

    if state.get("training_authorized") is not False:
        errors.append("training_authorized must remain false")
    if state.get("stage_a_execution_authorized") is not False:
        errors.append("stage_a_execution_authorized must remain false")
    if state.get("optimizer_updates_during_target_discrimination") != 0:
        errors.append("optimizer updates during target discrimination must remain zero")
    if state.get("ema_updates_during_target_discrimination") != 0:
        errors.append("EMA updates during target discrimination must remain zero")
    if state.get("test_state") != "SEALED":
        errors.append("TEST must remain SEALED")
    if state.get("morabito_state") != "PROTECTED":
        errors.append("Morabito must remain PROTECTED")
    if state.get("production_target_winner") is not None:
        errors.append("production_target_winner must remain null")
    if state.get("representation_winner") is not None:
        errors.append("representation_winner must remain null")
    if state.get("selected_estimand") != "UNSET_REQUIRES_APPROVAL":
        errors.append("selected_estimand must remain UNSET_REQUIRES_APPROVAL")
    if state.get("deciding_numeric_thresholds") != "UNSET_REQUIRES_APPROVAL":
        errors.append("deciding numeric thresholds must remain UNSET_REQUIRES_APPROVAL")

    if set(state.get("representation_families", [])) != EXPECTED_FAMILIES:
        errors.append("representation family roster must remain the frozen four-way neutral comparison")

    recoverability = state.get("recoverability_semantics", {})
    if recoverability.get("automatic_equivalence_forbidden") is not True:
        errors.append("target-object recoverability must not be equated with biological-truth recoverability")

    if set(state.get("transport_axes", [])) != EXPECTED_TRANSPORT_AXES:
        errors.append("donor/operator/study/technology transfer axes must remain separate")
    if set(state.get("ood_axes", [])) != EXPECTED_OOD_AXES:
        errors.append("biological-support OOD and measurement-regime OOD must remain separate")

    uncertainty = state.get("uncertainty_axes", {})
    if uncertainty.get("must_remain_separate") is not True:
        errors.append("biological-evidence and measurement-depth uncertainty must remain separate")

    stability = state.get("representation_stability", {})
    if stability.get("coordinate_claim_allowed_when_subspace_only") is not False:
        errors.append("coordinate claims are forbidden for stable-subspace-only results")

    observation = state.get("observation_operator", {})
    forbidden = set(observation.get("forbidden_free_shortcuts", []))
    if not {"UNRESTRICTED_DATASET_ID", "ARBITRARY_MATRIX_ID"}.issubset(forbidden):
        errors.append("unrestricted dataset and arbitrary matrix identifiers must remain forbidden shortcuts")
    if "DONOR_ID" not in forbidden:
        errors.append("donor identity must remain a forbidden free observation shortcut")
    if observation.get("technology_invariance_is_not_blanket_requirement") is not True:
        errors.append("technology invariance must not become a blanket qualification rule")

    if set(state.get("estimand_candidates", [])) != EXPECTED_ESTIMANDS:
        errors.append("estimand candidate roster must remain prospectively explicit")
    if state.get("hierarchical_tempering_parameter") != EXPECTED_TEMPERING_RULE:
        errors.append("hierarchical tempering may not be tuned post hoc on biological outcomes")

    if state.get("claim_ladder") != EXPECTED_CLAIM_LADDER:
        errors.append("claim ladder must preserve four non-automatic levels")
    if state.get("stage_a_maximum_claim") != "RNA_REPRESENTATION":
        errors.append("Stage A maximum claim must remain RNA_REPRESENTATION")

    asset_rules = state.get("external_asset_rules", {})
    if asset_rules.get("protected_assets_forbidden_for_target_selection") is not True:
        errors.append("protected assets must remain forbidden for target selection")
    if asset_rules.get("cell_count_cannot_substitute_for_donor_count") is not True:
        errors.append("cell count must not substitute for donor count")
    if asset_rules.get("observational_multimodal_support_is_not_causal") is not True:
        errors.append("observational multimodal support must not be promoted to causal evidence")
    if asset_rules.get("external_not_equal_independent") is not True:
        errors.append("external assets must not be assumed independent")
    if asset_rules.get("access_not_equal_exposure") is not True:
        errors.append("access and prior exposure must remain separate axes")
    if asset_rules.get("same_nucleus_pairing_not_equal_separate_nucleus_evidence") is not True:
        errors.append("same-nucleus and separate-nucleus evidence classes must remain distinct")
    if asset_rules.get("unknown_fields_fail_closed") is not True:
        errors.append("unknown external-asset fields must fail closed")

    return errors


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    state_path = root / "docs/agent/JEPA_PREMISE_QUALIFICATION_V3_STATE_20261006.json"
    state = json.loads(state_path.read_text())
    errors = validate_state(state)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("PASS: premise qualification V3 surface remains fail-closed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
