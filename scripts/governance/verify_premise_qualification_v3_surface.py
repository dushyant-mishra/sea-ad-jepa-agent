#!/usr/bin/env python3
import json
import sys
from pathlib import Path


EXPECTED_SCHEMA = "JEPA_PREMISE_QUALIFICATION_V3_STATE_20261006"
EXPECTED_ROLE = "PROSPECTIVE_SCIENTIFIC_GOVERNANCE__PREFREEZE_ONLY"
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
EXPECTED_STAGE_A_VERDICTS = {
    "QUALIFIED_FOR_RNA_REPRESENTATION",
    "INFORMATIVE_BUT_NOT_QUALIFIED",
    "FAIL_LEAKAGE",
    "FAIL_SHORTCUT",
    "FAIL_TRANSPORT",
    "NONRECOVERABLE_FROM_VIEW",
    "INDETERMINATE",
}
EXPECTED_TEMPERING_RULE = "SCIENTIFIC_ESTIMAND_PARAMETER__NO_POST_HOC_OUTCOME_TUNING"
EXPECTED_OBSERVATION_DESCRIPTORS = {
    "ASSAY_CLASS",
    "PLATFORM_OR_CHEMISTRY",
    "MEASURED_VOCABULARY",
    "DEPTH_CHARACTERISTICS",
    "DETECTION_CHARACTERISTICS",
    "COUNT_SPLIT_NOISE",
    "DOCUMENTED_ACQUISITION_PROPERTIES",
}
EXPECTED_STABILITY_DIAGNOSTICS = {
    "DONOR_BALANCED_BOOTSTRAP",
    "LEAVE_DONOR_GROUP_OUT",
    "PRINCIPAL_ANGLES",
    "CANONICAL_CORRELATIONS",
    "PROCRUSTES_ORTHOGONAL_ALIGNMENT",
    "COORDINATE_STABILITY_AFTER_ALIGNMENT",
    "EIGENVALUE_GAP_OR_DEGENERACY_AUDIT",
}
EXPECTED_STABILITY_STATUSES = {
    "STABLE_COORDINATES",
    "STABLE_SUBSPACE_ONLY",
    "UNSTABLE_REPRESENTATION",
    "INDETERMINATE__INSUFFICIENT_BIOLOGICAL_UNITS",
}
EXPECTED_SOURCE_DOCUMENTS = {
    "docs/superpowers/specs/2026-10-06-premise-qualification-contract-v3-design.md",
    "docs/agent/JEPA_REPRESENTATION_FAMILY_QUALIFICATION_V3_PREFREEZE_20261006.md",
    "docs/agent/JEPA_OBSERVATION_OPERATOR_CONTRACT_V1_PREFREEZE_20261006.md",
    "docs/agent/JEPA_EXTERNAL_VALIDATION_ASSET_MATRIX_V3_DRAFT_20261006.md",
    "docs/agent/JEPA_FOUNDATION_POPULATION_ESTIMAND_V3_PREFREEZE_20261006.md",
    "docs/agent/JEPA_REPRESENTATION_STABILITY_PROTOCOL_20261006.md",
    "docs/agent/JEPA_EVIDENCE_VS_DEPTH_CONVERGENCE_PROTOCOL_20261006.md",
    "docs/agent/JEPA_CLAIM_LADDER_V3_PREFREEZE_20261006.md",
    "docs/agent/JEPA_STAGE_A_REAL_RNA_TARGET_GATE_V3_PREFREEZE_20261006.md",
}

TOP_LEVEL_FIELDS = {
    "schema",
    "role",
    "training_authorized",
    "stage_a_execution_authorized",
    "optimizer_updates_during_target_discrimination",
    "ema_updates_during_target_discrimination",
    "test_state",
    "morabito_state",
    "production_target_winner",
    "representation_winner",
    "selected_estimand",
    "deciding_numeric_thresholds",
    "representation_families",
    "recoverability_semantics",
    "transport_axes",
    "observation_operator",
    "representation_stability",
    "uncertainty_axes",
    "ood_axes",
    "estimand_candidates",
    "hierarchical_tempering_parameter",
    "claim_ladder",
    "stage_a_maximum_claim",
    "stage_a_verdicts",
    "diagnostic_readout_firewall",
    "external_asset_rules",
    "source_documents",
}
NESTED_FIELDS = {
    "recoverability_semantics": {
        "target_object_recoverability",
        "biological_truth_recoverability",
        "automatic_equivalence_forbidden",
    },
    "observation_operator": {
        "form",
        "allowed_descriptor_classes",
        "forbidden_free_shortcuts",
        "technology_invariance_is_not_blanket_requirement",
    },
    "representation_stability": {
        "primary_resampling_unit",
        "required_diagnostics",
        "statuses",
        "coordinate_claim_allowed_when_subspace_only",
        "alignment_fit_partition",
        "alignment_freeze_before_held_donor_evaluation",
        "held_out_donors_may_influence_alignment",
    },
    "uncertainty_axes": {
        "biological_evidence_convergence",
        "measurement_depth_convergence",
        "must_remain_separate",
    },
    "biological_evidence_convergence": {
        "purpose",
        "operator_class",
        "count_depth_thinning_forbidden",
        "exact_fractions",
    },
    "measurement_depth_convergence": {
        "purpose",
        "operator_class",
        "information_universe_fixed",
        "exact_fractions",
    },
    "diagnostic_readout_firewall": {
        "fit_partition",
        "freeze_before_held_donor_evaluation",
        "held_out_units_may_influence_fit",
        "authorizes_jepa_training",
    },
    "external_asset_rules": {
        "external_not_equal_independent",
        "access_not_equal_exposure",
        "same_nucleus_pairing_not_equal_separate_nucleus_evidence",
        "cell_count_cannot_substitute_for_donor_count",
        "observational_multimodal_support_is_not_causal",
        "protected_assets_forbidden_for_target_selection",
        "unknown_fields_fail_closed",
    },
}


def _check_fields(errors: list[str], value, expected: set[str], label: str) -> dict:
    if not isinstance(value, dict):
        errors.append(f"{label} must be an object")
        return {}
    actual = set(value)
    missing = sorted(expected - actual)
    unknown = sorted(actual - expected)
    if missing:
        errors.append(f"missing required {label} fields: {', '.join(missing)}")
    if unknown:
        errors.append(f"unrecognized {label} fields: {', '.join(unknown)}")
    return value


def validate_state(state: dict) -> list[str]:
    errors: list[str] = []
    state = _check_fields(errors, state, TOP_LEVEL_FIELDS, "contract")

    recoverability = _check_fields(
        errors, state.get("recoverability_semantics"), NESTED_FIELDS["recoverability_semantics"], "recoverability_semantics"
    )
    observation = _check_fields(
        errors, state.get("observation_operator"), NESTED_FIELDS["observation_operator"], "observation_operator"
    )
    stability = _check_fields(
        errors, state.get("representation_stability"), NESTED_FIELDS["representation_stability"], "representation_stability"
    )
    uncertainty = _check_fields(
        errors, state.get("uncertainty_axes"), NESTED_FIELDS["uncertainty_axes"], "uncertainty_axes"
    )
    biological_evidence = _check_fields(
        errors,
        uncertainty.get("biological_evidence_convergence"),
        NESTED_FIELDS["biological_evidence_convergence"],
        "biological_evidence_convergence",
    )
    measurement_depth = _check_fields(
        errors,
        uncertainty.get("measurement_depth_convergence"),
        NESTED_FIELDS["measurement_depth_convergence"],
        "measurement_depth_convergence",
    )
    firewall = _check_fields(
        errors,
        state.get("diagnostic_readout_firewall"),
        NESTED_FIELDS["diagnostic_readout_firewall"],
        "diagnostic_readout_firewall",
    )
    asset_rules = _check_fields(
        errors, state.get("external_asset_rules"), NESTED_FIELDS["external_asset_rules"], "external_asset_rules"
    )

    if state.get("schema") != EXPECTED_SCHEMA:
        errors.append("schema identifier must remain frozen")
    if state.get("role") != EXPECTED_ROLE:
        errors.append("role must remain prospective prefreeze governance only")
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

    if recoverability.get("automatic_equivalence_forbidden") is not True:
        errors.append("target-object recoverability must not be equated with biological-truth recoverability")

    if set(state.get("transport_axes", [])) != EXPECTED_TRANSPORT_AXES:
        errors.append("donor/operator/study/technology transfer axes must remain separate")
    if set(state.get("ood_axes", [])) != EXPECTED_OOD_AXES:
        errors.append("biological-support OOD and measurement-regime OOD must remain separate")

    if uncertainty.get("must_remain_separate") is not True:
        errors.append("biological-evidence and measurement-depth uncertainty must remain separate")
    if biological_evidence.get("operator_class") == "COUNT_DEPTH_THINNING" or biological_evidence.get("count_depth_thinning_forbidden") is not True:
        errors.append("biological-evidence perturbation must not be count-depth thinning")
    if measurement_depth.get("operator_class") != "COUNT_DEPTH_THINNING":
        errors.append("measurement-depth perturbation must remain count-depth thinning")
    if measurement_depth.get("information_universe_fixed") is not True:
        errors.append("measurement-depth perturbation must hold the information universe fixed")

    if stability.get("coordinate_claim_allowed_when_subspace_only") is not False:
        errors.append("coordinate claims are forbidden for stable-subspace-only results")
    if stability.get("primary_resampling_unit") != "DONOR":
        errors.append("representation stability must retain DONOR as the primary biological resampling unit")
    if set(stability.get("required_diagnostics", [])) != EXPECTED_STABILITY_DIAGNOSTICS:
        errors.append("representation stability diagnostic roster must remain frozen")
    if set(stability.get("statuses", [])) != EXPECTED_STABILITY_STATUSES:
        errors.append("representation stability status roster must remain frozen")
    if stability.get("alignment_fit_partition") != "INNER_TRAIN_ONLY" or stability.get("alignment_freeze_before_held_donor_evaluation") is not True:
        errors.append("coordinate alignment must fit on inner TRAIN and freeze before held-donor evaluation")
    if stability.get("held_out_donors_may_influence_alignment") is not False:
        errors.append("held-out donors must not influence coordinate alignment")

    forbidden = set(observation.get("forbidden_free_shortcuts", []))
    if not {"UNRESTRICTED_DATASET_ID", "ARBITRARY_MATRIX_ID"}.issubset(forbidden):
        errors.append("unrestricted dataset and arbitrary matrix identifiers must remain forbidden shortcuts")
    if "DONOR_ID" not in forbidden:
        errors.append("donor identity must remain a forbidden free observation shortcut")
    if observation.get("technology_invariance_is_not_blanket_requirement") is not True:
        errors.append("technology invariance must not become a blanket qualification rule")
    if set(observation.get("allowed_descriptor_classes", [])) != EXPECTED_OBSERVATION_DESCRIPTORS:
        errors.append("observation descriptor class roster must remain frozen")

    if set(state.get("estimand_candidates", [])) != EXPECTED_ESTIMANDS:
        errors.append("estimand candidate roster must remain prospectively explicit")
    if state.get("hierarchical_tempering_parameter") != EXPECTED_TEMPERING_RULE:
        errors.append("hierarchical tempering may not be tuned post hoc on biological outcomes")

    if state.get("claim_ladder") != EXPECTED_CLAIM_LADDER:
        errors.append("claim ladder must preserve four non-automatic levels")
    if state.get("stage_a_maximum_claim") != "RNA_REPRESENTATION":
        errors.append("Stage A maximum claim must remain RNA_REPRESENTATION")
    if set(state.get("stage_a_verdicts", [])) != EXPECTED_STAGE_A_VERDICTS:
        errors.append("Stage-A verdict roster must remain frozen")

    if not (
        firewall.get("fit_partition") == "INNER_TRAIN_ONLY"
        and firewall.get("freeze_before_held_donor_evaluation") is True
        and firewall.get("held_out_units_may_influence_fit") is False
        and firewall.get("authorizes_jepa_training") is False
    ):
        errors.append("diagnostic readout firewall must remain inner-TRAIN-only and frozen before held-donor evaluation")

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

    if set(state.get("source_documents", [])) != EXPECTED_SOURCE_DOCUMENTS:
        errors.append("source document roster must remain frozen and complete")

    return errors


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    root = Path(__file__).resolve().parents[2]
    if len(argv) > 1:
        print("ERROR: expected at most one state JSON path")
        return 2
    state_path = Path(argv[0]) if argv else root / "docs/agent/JEPA_PREMISE_QUALIFICATION_V3_STATE_20261006.json"
    try:
        state = json.loads(state_path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: cannot read premise state: {exc}")
        return 2
    errors = validate_state(state)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("PASS: premise qualification V3 contract remains schema-closed and fail-closed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
