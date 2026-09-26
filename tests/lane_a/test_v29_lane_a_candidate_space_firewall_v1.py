"""Adversarial tests for the Lane A candidate-space firewall.

One positive control proves the real proposal passes. Every other test mutates the
proposal into a specific scientific or governance failure and proves the firewall
stops it. A firewall with no failing input is not a firewall.
"""
from __future__ import annotations

import importlib.util
import json
import pathlib
import re

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]
PROPOSAL = ROOT / "docs/agent/lane_a/JEPA_V29_LANE_A_TEACHER_TARGET_PROPOSAL_V1_20260926.json"
FIREWALL = ROOT / "scripts/v5/lane_a/v29_lane_a_candidate_space_firewall_v1.py"

_spec = importlib.util.spec_from_file_location("lane_a_firewall", FIREWALL)
_module = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_module)
check = _module.check
Stop = _module.Stop
UNSET = _module.UNSET


def good() -> dict:
    return json.loads(PROPOSAL.read_text(encoding="utf-8"))


def mutate(fn):
    doc = good()
    fn(doc)
    return doc


def decision(doc: dict, did: str) -> dict:
    return next(d for d in doc["decisions_open"] if d["id"] == did)


def control(doc: dict, name: str) -> dict:
    return next(c for c in doc["controls"] if c["name"] == name)


def rejects(doc: dict, fragment: str) -> None:
    with pytest.raises(Stop) as excinfo:
        check(doc)
    assert fragment in str(excinfo.value), str(excinfo.value)


# --------------------------------------------------------------------------- #
# Positive control
# --------------------------------------------------------------------------- #

def test_positive_control_real_proposal_passes_as_nonauthorizing():
    assert check(good()) == "PASS_LANEA_NONAUTHORIZING_CANDIDATE_SPACE"


def test_positive_control_markdown_companion_exists_and_carries_the_footer():
    md = (ROOT / "docs/agent/lane_a/JEPA_V29_LANE_A_TEACHER_TARGET_DECISION_SHEET_V1_20260926.md")
    text = md.read_text(encoding="utf-8")
    assert "TRAINING=OFF" in text
    assert "D_SHARED_G5=UNOPENED" in text
    assert "THERAPEUTIC_RANKING=OFF" in text
    assert "training_authorized" not in text.lower().replace(" ", "")


# --------------------------------------------------------------------------- #
# Authority may never be issued by this document
# --------------------------------------------------------------------------- #

def test_training_authority_key_cannot_be_smuggled_in():
    rejects(mutate(lambda d: d.__setitem__("training_authorized", False)),
            "TRAINING_AUTHORITY_KEY_PRESENT")


def test_nested_training_authority_key_is_also_rejected():
    rejects(mutate(lambda d: d["governance"].__setitem__("training_authorized", True)),
            "TRAINING_AUTHORITY_KEY_PRESENT")


def test_any_authorizing_key_set_true_is_rejected():
    rejects(mutate(lambda d: d["governance"].__setitem__("execution_authorized", True)),
            "TRAINING_AUTHORITY_KEY_PRESENT")


def test_authorization_language_in_a_string_value_is_rejected():
    rejects(mutate(lambda d: d.__setitem__("approval", "TRAINING_AUTHORIZED_BY_THIS_FILE")),
            "AUTHORIZATION_LANGUAGE")


def test_authorization_language_inside_a_list_is_rejected():
    rejects(mutate(lambda d: d["owner_decisions_required"].append("EXECUTION_AUTHORIZATION_GRANTED")),
            "AUTHORIZATION_LANGUAGE")


# --------------------------------------------------------------------------- #
# The candidate space must stay a space
# --------------------------------------------------------------------------- #

def test_a_silently_selected_candidate_is_rejected():
    rejects(mutate(lambda d: d.__setitem__("selected_candidate", "T_A")),
            "CANDIDATE_SILENTLY_SELECTED")


def test_dropping_a_competing_candidate_is_rejected():
    rejects(mutate(lambda d: d["candidates"].pop("T_B1")), "MISSING_CANDIDATE_T_B1")


def test_collapsing_every_candidate_onto_one_scalar_seam_is_rejected():
    def collapse(d):
        seam = d["candidates"]["T_A"]["query_scalar_withholding_point"]
        for name in ("T_B1", "T_B2", "T_C"):
            d["candidates"][name]["query_scalar_withholding_point"] = seam
    rejects(mutate(collapse), "CANDIDATE_SPACE_COLLAPSED_TO_ONE_SCALAR_SEAM")


def test_candidate_without_a_stated_scalar_withholding_point_is_rejected():
    rejects(mutate(lambda d: d["candidates"]["T_B1"].__setitem__("query_scalar_withholding_point", "")),
            "CANDIDATE_FIELD_MISSING_T_B1_query_scalar_withholding_point")


def test_candidate_without_a_stop_gradient_boundary_is_rejected():
    rejects(mutate(lambda d: d["candidates"]["T_C"].pop("teacher_stop_gradient_boundary")),
            "CANDIDATE_FIELD_MISSING_T_C_teacher_stop_gradient_boundary")


def test_candidate_presented_without_its_downside_is_rejected():
    rejects(mutate(lambda d: d["candidates"]["T_B1"].__setitem__("against", [])),
            "CANDIDATE_TRADEOFF_MISSING_T_B1_against")


def test_a_preselected_decision_is_rejected():
    rejects(mutate(lambda d: decision(d, "D1").__setitem__("selected", "T_A")),
            "DECISION_PRESELECTED_D1")


def test_a_decision_offered_with_no_alternative_is_rejected():
    rejects(mutate(lambda d: decision(d, "D0").__setitem__("options", ["N_TOTAL_COUNT_INCLUDING_QUERY"])),
            "DECISION_WITHOUT_ALTERNATIVES_D0")


def test_every_required_decision_must_be_present():
    rejects(mutate(lambda d: d["decisions_open"].remove(decision(d, "D0"))), "MISSING_DECISION_D0")


# --------------------------------------------------------------------------- #
# A control with no failing outcome is not a control
# --------------------------------------------------------------------------- #

def test_control_without_a_disqualifying_outcome_is_rejected():
    rejects(mutate(lambda d: control(d, "IDENTITY_ONLY").__setitem__("disqualifying_outcome", "")),
            "CONTROL_WITHOUT_FAILING_OUTCOME")


def test_negative_control_whose_outcome_never_disqualifies_is_rejected():
    rejects(mutate(lambda d: control(d, "TECHNICAL_ONLY").__setitem__(
        "disqualifying_outcome", "Report the technical-only score alongside the full score.")),
        "CONTROL_OUTCOME_NOT_FALSIFYING")


def test_removing_the_positive_control_is_rejected():
    def drop(d):
        d["controls"] = [c for c in d["controls"] if c["name"] != "LEAK_INJECTION"]
    rejects(mutate(drop), "MISSING_CONTROL_LEAK_INJECTION")


def test_demoting_the_only_positive_control_to_a_negative_is_rejected():
    def demote(d):
        c = control(d, "LEAK_INJECTION")
        c["polarity"] = "NEGATIVE_MUST_FAIL"
        c["disqualifying_outcome"] = "disqualified if the injected value helps"
    rejects(mutate(demote), "NO_POSITIVE_CONTROL")


def test_removing_the_remaining_rna_necessity_control_is_rejected():
    def drop(d):
        d["controls"] = [c for c in d["controls"] if c["name"] != "REMAINING_RNA_NECESSITY"]
    rejects(mutate(drop), "MISSING_CONTROL_REMAINING_RNA_NECESSITY")


def test_a_preset_control_margin_is_rejected():
    rejects(mutate(lambda d: control(d, "IDENTITY_ONLY").__setitem__("margin", 0.05)),
            "CONTROL_MARGIN_PRESET")


def test_control_with_undeclared_polarity_is_rejected():
    rejects(mutate(lambda d: control(d, "GLOBAL_CONTEXT_ONLY").__setitem__("polarity", "SOMETIMES")),
            "CONTROL_POLARITY_UNDECLARED")


# --------------------------------------------------------------------------- #
# Measurement state stays a separate detached output
# --------------------------------------------------------------------------- #

def test_measurement_state_offered_as_a_primary_input_is_rejected():
    rejects(mutate(lambda d: decision(d, "D6")["options"].append("INPUT_TO_PRIMARY_PATH")),
            "MEASUREMENT_STATE_OFFERED_AS_INPUT")


def test_removing_the_ban_on_measurement_state_as_input_is_rejected():
    rejects(mutate(lambda d: decision(d, "D6").__setitem__("forbidden_option", "NONE")),
            "MEASUREMENT_STATE_INPUT_NOT_FORBIDDEN")


def test_technical_control_without_the_detached_output_requirement_is_rejected():
    rejects(mutate(lambda d: control(d, "TECHNICAL_ONLY").__setitem__(
        "architectural_requirement", "MAY_BE_SUPPLIED_TO_THE_ENCODER")),
        "MEASUREMENT_STATE_NOT_CONFINED_TO_SEPARATE_OUTPUTS")


# --------------------------------------------------------------------------- #
# Every leakage seam stays enumerated, detectable and repairable
# --------------------------------------------------------------------------- #

def test_dropping_the_teacher_context_seam_is_rejected():
    def drop(d):
        d["leakage_paths"] = [p for p in d["leakage_paths"] if p["id"] != "L1"]
    rejects(mutate(drop), "MISSING_LEAKAGE_PATH_L1")


def test_dropping_the_normalization_seam_is_rejected():
    def drop(d):
        d["leakage_paths"] = [p for p in d["leakage_paths"] if p["id"] != "L2"]
    rejects(mutate(drop), "MISSING_LEAKAGE_PATH_L2")


def test_leakage_path_without_a_detection_method_is_rejected():
    def blank(d):
        next(p for p in d["leakage_paths"] if p["id"] == "L9")["detection"] = ""
    rejects(mutate(blank), "LEAKAGE_PATH_WITHOUT_DETECTION_L9")


def test_leakage_path_without_a_repair_is_rejected():
    def blank(d):
        next(p for p in d["leakage_paths"] if p["id"] == "L5")["repair"] = "   "
    rejects(mutate(blank), "LEAKAGE_PATH_WITHOUT_REPAIR_L5")


def test_relabelling_l1_away_from_the_teacher_seam_is_rejected():
    def rename(d):
        next(p for p in d["leakage_paths"] if p["id"] == "L1")["name"] = "STUDENT_SIDE_ONLY"
    rejects(mutate(rename), "L1_IS_NOT_THE_TEACHER_CONTEXT_SEAM")


# --------------------------------------------------------------------------- #
# No parameter, historical or synthetic, may acquire a value here
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize(
    "field,value",
    [
        ("mask_fraction", 0.40),
        ("ema_half_life", 0.996),
        ("model_width", 160),
        ("model_depth", 6),
        ("attention_heads", 4),
        ("batch_geometry", "128x8"),
        ("seed", 1234),
        ("minimum_effect_threshold", 0.01),
        ("held_out_donor_ids", ["D001", "D002"]),
        ("training_population", "ALL_104"),
    ],
)
def test_no_unset_parameter_may_acquire_a_value(field, value):
    rejects(mutate(lambda d: d["unset_parameters"].__setitem__(field, value)),
            "UNSET_PARAMETER_HAS_A_VALUE_" + field)


def test_deleting_an_unset_parameter_rather_than_leaving_it_open_is_rejected():
    rejects(mutate(lambda d: d["unset_parameters"].pop("ema_half_life")),
            "MISSING_UNSET_PARAMETER_ema_half_life")


def test_a_number_anywhere_in_the_decision_subtree_is_rejected():
    rejects(mutate(lambda d: decision(d, "D7").__setitem__("bar", 0.05)),
            "NUMERIC_SPILLOVER")


def test_a_number_anywhere_in_the_candidate_subtree_is_rejected():
    rejects(mutate(lambda d: d["candidates"]["T_B1"].__setitem__("proposed_width", 160)),
            "NUMERIC_SPILLOVER")


def test_a_number_inside_a_candidate_list_is_rejected():
    rejects(mutate(lambda d: d["candidates"]["T_A"]["in_favour"].append(384)),
            "NUMERIC_SPILLOVER")


def test_forbidden_inherited_values_must_stay_listed():
    def drop(d):
        d["forbidden_inherited_values"]["historical_v4_mechanics_only"] = ["width_160"]
    rejects(mutate(drop), "FORBIDDEN_INHERITED_VALUE_NOT_LISTED")


# --------------------------------------------------------------------------- #
# The failed masking grid may not be relabelled
# --------------------------------------------------------------------------- #

def test_relabelling_the_september16_grid_as_qualified_is_rejected():
    rejects(mutate(lambda d: d["masking_status"].__setitem__(
        "previous_september16_result", "DONOR_RECURRENT_QUALIFIED")),
        "FALSE_MASK_QUALIFICATION")


def test_claiming_this_document_resolved_masking_authority_is_rejected():
    rejects(mutate(lambda d: d["masking_status"].__setitem__(
        "masking_authority_resolved_by_this_document", True)),
        "MASK_AUTHORITY_FALSELY_RESOLVED")


def test_claiming_a_new_threshold_made_an_arm_pass_is_rejected():
    rejects(mutate(lambda d: d["masking_status"].__setitem__(
        "no_new_threshold_was_introduced_to_make_something_pass", False)),
        "THRESHOLD_WIDENING_CLAIM")


def test_overwriting_the_standing_masking_terminal_is_rejected():
    rejects(mutate(lambda d: d["masking_status"].__setitem__(
        "standing_terminal", "MASKING_SHORTCUT_AUTHORITY_RESOLVED")),
        "MASK_TERMINAL_OVERWRITTEN")


# --------------------------------------------------------------------------- #
# Population, substrate and inference-unit integrity
# --------------------------------------------------------------------------- #

def test_the_old_94_donor_population_cannot_replace_the_current_104():
    rejects(mutate(lambda d: d["substrate_reference"].__setitem__("donors", 94)),
            "SUBSTRATE_donors")


def test_a_wrong_cell_count_is_rejected():
    rejects(mutate(lambda d: d["substrate_reference"].__setitem__("cells", 4553000)),
            "SUBSTRATE_cells")


def test_a_wrong_source_donor_split_is_rejected():
    rejects(mutate(lambda d: d["substrate_reference"].__setitem__(
        "source_donors", {"SEA_AD": 46, "HVS": 41, "NPH52": 18})),
        "SUBSTRATE_source_donors")


def test_presenting_the_substrate_as_a_fresh_computation_is_rejected():
    rejects(mutate(lambda d: d["substrate_reference"].__setitem__(
        "role", "PHYSICALLY_REMEASURED_BY_THIS_DOCUMENT")),
        "SUBSTRATE_PRESENTED_AS_FRESH_COMPUTATION")


def test_making_the_cell_the_independent_unit_is_rejected():
    rejects(mutate(lambda d: d["control_protocol"].__setitem__("independent_unit", "CELL")),
            "INDEPENDENT_UNIT_IS_NOT_THE_DONOR")


def test_manufacturing_cell_level_independent_n_is_rejected():
    rejects(mutate(lambda d: d["control_protocol"].__setitem__("independent_unit_count", 4553407)),
            "INDEPENDENT_UNIT_COUNT")


def test_dropping_donor_clustered_uncertainty_is_rejected():
    rejects(mutate(lambda d: d["control_protocol"].__setitem__(
        "uncertainty_method", "IID_CELL_BOOTSTRAP")),
        "UNCERTAINTY_NOT_DONOR_CLUSTERED")


def test_preselecting_the_evaluation_metric_is_rejected():
    rejects(mutate(lambda d: d["control_protocol"].__setitem__("metric", "COSINE")),
            "METRIC_PRESELECTED")


def test_conditional_on_success_reporting_is_rejected():
    rejects(mutate(lambda d: d["control_protocol"].__setitem__(
        "reporting", "CONDITIONAL_ON_CONVERGED_RUNS_ONLY")),
        "REPORTING_NOT_UNCONDITIONAL")


def test_unpaired_controls_are_rejected():
    rejects(mutate(lambda d: d["control_protocol"].__setitem__(
        "pairing", "INDEPENDENT_DRAWS_PER_CONDITION")),
        "CONTROLS_NOT_PAIRED_UNDER_COMMON_RANDOM_NUMBERS")


# --------------------------------------------------------------------------- #
# Governance seals and honest classification
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize(
    "key,value",
    [
        ("training", "ON"),
        ("d_shared_g5", "OPENED"),
        ("pathology", "OPEN"),
        ("reader_oracle23", "OPEN"),
        ("audit_b_n1", "OPENED"),
        ("rare_tail_molecular", "OPENED"),
        ("therapeutic_ranking", "ON"),
    ],
)
def test_no_seal_may_be_opened_by_this_document(key, value):
    rejects(mutate(lambda d: d["governance"].__setitem__(key, value)), "GOVERNANCE_" + key)


def test_claiming_a_protected_outcome_informed_the_design_is_rejected():
    rejects(mutate(lambda d: d["governance"].__setitem__(
        "protected_outcome_informed_any_statement_in_this_document", True)),
        "GOVERNANCE_protected_outcome_informed_any_statement_in_this_document")


def test_treating_a_provisional_width_as_a_measured_biological_dimension_is_rejected():
    rejects(mutate(lambda d: d["governance"].__setitem__(
        "provisional_network_width_treated_as_a_measured_biological_dimension", True)),
        "GOVERNANCE_provisional_network_width_treated_as_a_measured_biological_dimension")


def test_claiming_this_document_selects_a_candidate_is_rejected():
    rejects(mutate(lambda d: d["governance"].__setitem__("this_document_selects_a_candidate", True)),
            "GOVERNANCE_this_document_selects_a_candidate")


def test_claiming_pr152_is_superseded_is_rejected():
    rejects(mutate(lambda d: d["companion_of"].__setitem__(
        "relationship", "SUPERSEDES_PR152")),
        "PR152_TREATED_AS_SUPERSEDED")


def test_classifying_an_open_dimension_as_already_done_is_rejected():
    def relabel(d):
        for row in d["classification_against_pr152"]:
            if row["element"] == "competing_target_constructions":
                row["classification"] = "ALREADY_DONE"
    rejects(mutate(relabel), "CLASSIFICATION_NOT_STATED_competing_target_constructions")


def test_claiming_nothing_in_pr152_was_already_done_is_rejected():
    def relabel(d):
        for row in d["classification_against_pr152"]:
            if row["classification"] == "ALREADY_DONE":
                row["classification"] = "GENUINELY_OPEN"
            if row["classification"] == "ALREADY_DONE_FOR_THAT_SCOPE":
                row["classification"] = "GENUINELY_OPEN"
    rejects(mutate(relabel), "CLASSIFICATION_CLAIMS_NOTHING_WAS_ALREADY_DONE")


# --------------------------------------------------------------------------- #
# Degenerate inputs must fail closed, not pass by omission
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize(
    "section",
    ["unset_parameters", "decisions_open", "candidates", "controls"],
)
def test_an_absent_required_section_fails_closed(section):
    rejects(mutate(lambda d: d.pop(section)), "MISSING_SECTION_" + section)


def test_an_empty_control_list_fails_closed():
    rejects(mutate(lambda d: d.__setitem__("controls", [])), "CONTROLS_MISSING")


def test_an_empty_document_fails_closed():
    with pytest.raises(Stop):
        check({})


def test_a_wrong_schema_fails_closed():
    rejects(mutate(lambda d: d.__setitem__("schema", "SOMETHING_ELSE_V1")), "SCHEMA")


def test_a_document_claiming_to_be_an_authority_fails_closed():
    rejects(mutate(lambda d: d.__setitem__("document_role", "FROZEN_AUTHORITY")), "ROLE")


# --------------------------------------------------------------------------- #
# A control measured silent on its own planted failure may not stay falsifying
# --------------------------------------------------------------------------- #

def test_a_non_discriminating_control_cannot_be_presented_as_falsifying():
    rejects(mutate(lambda d: control(d, "GLOBAL_CONTEXT_ONLY").__setitem__(
        "polarity", "NEGATIVE_MUST_FAIL")),
        "NON_DISCRIMINATING_CONTROL_STILL_PRESENTED_AS_FALSIFYING")


def test_dropping_the_capacity_matching_requirement_is_rejected():
    rejects(mutate(lambda d: control(d, "GLOBAL_CONTEXT_ONLY").pop(
        "capacity_matching_requirement")),
        "ABLATED_CONDITION_NOT_CAPACITY_MATCHED")


def test_removing_the_replacement_control_is_rejected():
    def drop(d):
        d["controls"] = [c for c in d["controls"] if c["name"] != "QUERY_EXCHANGEABILITY"]
    rejects(mutate(drop), "MISSING_CONTROL_QUERY_EXCHANGEABILITY")


def test_unassigned_falsifying_role_is_rejected():
    rejects(mutate(lambda d: control(d, "QUERY_EXCHANGEABILITY").__setitem__(
        "replaces_falsifying_role_of", "SOMETHING_ELSE")),
        "FALSIFYING_ROLE_NOT_REASSIGNED")


def test_replacement_control_demoted_to_a_diagnostic_is_rejected():
    def demote(d):
        c = control(d, "QUERY_EXCHANGEABILITY")
        c["polarity"] = "DIAGNOSTIC_NOT_DISQUALIFYING"
    rejects(mutate(demote), "REPLACEMENT_CONTROL_NOT_FALSIFYING")


# --------------------------------------------------------------------------- #
# Measured control sensitivity must stay attached and honest
# --------------------------------------------------------------------------- #

def test_missing_control_sensitivity_section_fails_closed():
    rejects(mutate(lambda d: d.pop("control_sensitivity_evidence")),
            "MISSING_SECTION_control_sensitivity_evidence")


@pytest.mark.parametrize(
    "key",
    [
        "c1_identity_only",
        "c2_global_context_only",
        "c2b_query_exchangeability",
        "c3_technical_only",
        "c4_remaining_rna_necessity",
        "c5_leak_injection_positive_control",
        "c6_donor_key_cheat",
    ],
)
def test_every_control_must_carry_measured_sensitivity_evidence(key):
    rejects(mutate(lambda d: d["control_sensitivity_evidence"].pop(key)),
            "MISSING_CONTROL_SENSITIVITY_EVIDENCE_" + key)


def test_synthetic_evidence_relabelled_as_real_is_rejected():
    rejects(mutate(lambda d: d["control_sensitivity_evidence"].__setitem__(
        "role", "MEASURED_ON_FULL104_HELD_OUT_DONORS")),
        "CONTROL_EVIDENCE_NOT_LABELLED_SYNTHETIC")


def test_evidence_not_separated_from_full104_is_rejected():
    rejects(mutate(lambda d: d["control_sensitivity_evidence"].__setitem__(
        "role", "SYNTHETIC_PLANTED_STRUCTURE_ONLY__DERIVED_FROM_FULL104")),
        "CONTROL_EVIDENCE_NOT_SEPARATED_FROM_FULL104")


def test_overwriting_the_c2_non_discrimination_finding_is_rejected():
    rejects(mutate(lambda d: d["control_sensitivity_evidence"][
        "c2_global_context_only"].__setitem__("fires", True)),
        "C2_NON_DISCRIMINATION_FINDING_OVERWRITTEN")


def test_a_replacement_control_that_never_fires_is_rejected():
    rejects(mutate(lambda d: d["control_sensitivity_evidence"][
        "c2b_query_exchangeability"].__setitem__("fires", False)),
        "REPLACEMENT_CONTROL_NOT_SHOWN_TO_FIRE")


def test_a_replacement_control_that_fires_on_a_healthy_target_is_rejected():
    rejects(mutate(lambda d: d["control_sensitivity_evidence"][
        "c2b_query_exchangeability"]["healthy_regime"].__setitem__("fires", True)),
        "REPLACEMENT_CONTROL_FIRES_ON_A_HEALTHY_TARGET")


def test_an_insensitive_leak_detector_is_rejected():
    rejects(mutate(lambda d: d["control_sensitivity_evidence"][
        "c5_leak_injection_positive_control"].__setitem__("detector_sensitive", False)),
        "LEAK_DETECTOR_NOT_SHOWN_SENSITIVE")


def test_a_leak_detector_that_always_fires_is_rejected():
    rejects(mutate(lambda d: d["control_sensitivity_evidence"][
        "c5_leak_injection_positive_control"].__setitem__(
            "not_trivially_always_positive", False)),
        "LEAK_DETECTOR_NOT_SHOWN_TO_HAVE_A_QUIET_CASE")


def test_a_null_fixture_that_manufactured_signal_is_rejected():
    rejects(mutate(lambda d: d["control_sensitivity_evidence"].__setitem__(
        "null_fixture_probe_score", 0.42)),
        "NULL_FIXTURE_MANUFACTURED_SIGNAL")


# --------------------------------------------------------------------------- #
# The margin check must have teeth independently of the numeric sweep
# --------------------------------------------------------------------------- #

def test_a_non_numeric_preset_margin_is_also_rejected():
    rejects(mutate(lambda d: control(d, "IDENTITY_ONLY").__setitem__(
        "margin", "FIVE_PERCENT")),
        "CONTROL_MARGIN_PRESET")


# --------------------------------------------------------------------------- #
# Structural proof that no unapproved parameter carries a value anywhere
# --------------------------------------------------------------------------- #

PARAMETER_KEY_PATTERN = re.compile(
    r"(ema|momentum|half_life|mask_fraction|mask_burden|width|depth|head|batch|"
    r"microbatch|learning_rate|weight_decay|lr_|seed|update_budget|threshold|"
    r"margin|allowance|block_count|block_size|views)",
    re.IGNORECASE,
)


def _walk_items(node, path=""):
    if isinstance(node, dict):
        for key, value in node.items():
            child = f"{path}.{key}" if path else str(key)
            yield child, key, value
            yield from _walk_items(value, child)
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from _walk_items(value, f"{path}[{index}]")


def test_no_parameter_shaped_key_carries_a_number_outside_the_forbidden_list():
    """Every geometry, schedule, seed, budget and threshold field must be open.

    The forbidden-inherited list and the measured control-sensitivity evidence are
    the only places numbers are allowed to sit next to these words, and both are
    explicitly scoped. substrate_reference is exempt because every one of its
    values is pinned to the recorded FULL104 figures by _check_substrate, so it
    cannot carry a smuggled parameter; its 81 is the smallest donor cell count,
    which is sampler capacity and not a chosen batch.
    """
    doc = good()
    offenders = []
    for path, key, value in _walk_items(doc):
        if path.startswith(("forbidden_inherited_values", "control_sensitivity_evidence", "substrate_reference")):
            continue
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            continue
        if PARAMETER_KEY_PATTERN.search(str(key)):
            offenders.append((path, value))
    assert not offenders, offenders


@pytest.mark.parametrize(
    "field",
    [
        "mask_fraction",
        "training_population",
        "held_out_donor_ids",
        "training_donor_ids",
        "split_seed",
        "model_width",
        "model_depth",
        "attention_heads",
        "ffn_width",
        "ema_half_life",
        "optimizer",
        "learning_rate",
        "weight_decay",
        "lr_schedule",
        "seed",
        "update_budget",
        "batch_geometry",
        "microbatch_token_budget",
        "evaluation_metric",
        "minimum_effect_threshold",
        "uncertainty_precision_threshold",
    ],
)
def test_every_named_unapproved_parameter_is_explicitly_open(field):
    assert good()["unset_parameters"][field] == UNSET


def test_synthetic_and_historical_constants_appear_only_as_forbidden():
    """0.40 and 0.99 are synthetic fixture values; 0.996 and 128x8 are historical V4."""
    doc = good()
    listed = set()
    for value in doc["forbidden_inherited_values"].values():
        if isinstance(value, list):
            listed.update(value)
    for banned in ("mask_fraction_0.40", "ema_0.99", "ema_0.996", "batch_geometry_128x8"):
        assert banned in listed
    for path, key, value in _walk_items(doc):
        if path.startswith(("forbidden_inherited_values", "control_sensitivity_evidence")):
            continue
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            continue
        assert value not in (0.40, 0.99, 0.996), (path, value)


def test_no_candidate_or_decision_proposes_a_numeric_default():
    doc = good()
    for section in ("candidates", "decisions_open", "controls", "unset_parameters"):
        for path, key, value in _walk_items(doc[section], section):
            assert isinstance(value, bool) or not isinstance(value, (int, float)), (path, value)
