#!/usr/bin/env python3
"""Fail-closed reviewer for the Lane A teacher-target candidate-space proposal.

This checker proves one narrow thing: that the proposal keeps every open choice
open, attaches a falsifying outcome to every control, and issues no authority.

It never issues permission of any kind, and a green result is not evidence about
biology, not a target selection, and not permission to train.

Usage:
    PYTHONPATH=src:. python scripts/v5/lane_a/v29_lane_a_candidate_space_firewall_v1.py <proposal.json>
"""
from __future__ import annotations

import json
import pathlib
import re
import sys
from typing import Any, Iterator

UNSET = "UNSET_REQUIRES_APPROVAL"

SCHEMA = "V29_LANE_A_TEACHER_TARGET_CANDIDATE_SPACE_PROPOSAL_V1"
ROLE = "NON_AUTHORIZING_SCIENCE_DECISION_REQUEST__NOT_AUTHORITY"

# Any of these appearing as a live key is an authority assertion this document may not make.
FORBIDDEN_AUTHORITY_KEYS = {"training_authorized", "execution_authorized", "trainingauthorized"}

# Non-negated authorization vocabulary in a string value.
BANNED_AUTHORIZATION = re.compile(
    r"(?<!UN)(?<!NOT_)(?<!NEVER_)(?<!NO_)(?<!NON_)AUTHORIZ(?:ED|ES|ATION)"
)

# Subtrees in which no numeric literal may appear at all. This is how historical and
# synthetic numeric spillover (0.40 mask, 0.99 / 0.996 EMA, width 160, depth 6,
# 128x8 geometry, 4 heads, 48 identity dims, 16 blocks) is kept out structurally,
# rather than by blacklisting individual constants.
NUMBER_FREE_SUBTREES = ("unset_parameters", "decisions_open", "candidates", "controls")

REQUIRED_DECISIONS = ("D0", "D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8", "D9")

REQUIRED_CANDIDATES = ("T_A", "T_B1", "T_B2", "T_C")

REQUIRED_CANDIDATE_FIELDS = (
    "teacher_molecular_inputs",
    "query_identity_supply",
    "query_scalar_withholding_point",
    "contextual_mixing_operation",
    "teacher_stop_gradient_boundary",
    "exact_target_construction",
    "leakage_verdict",
)

REQUIRED_CONTROL_NAMES = {
    "IDENTITY_ONLY",
    "GLOBAL_CONTEXT_ONLY",
    "TECHNICAL_ONLY",
    "REMAINING_RNA_NECESSITY",
    "LEAK_INJECTION",
    "DONOR_OR_CELL_KEY_CHEAT",
}

REQUIRED_LEAKAGE_IDS = tuple(f"L{n}" for n in range(1, 15))

REQUIRED_UNSET = (
    "mask_fraction",
    "training_population",
    "held_out_donor_ids",
    "training_donor_ids",
    "split_seed",
    "model_width",
    "model_depth",
    "attention_heads",
    "ema_half_life",
    "optimizer",
    "learning_rate",
    "seed",
    "update_budget",
    "batch_geometry",
    "evaluation_metric",
    "minimum_effect_threshold",
)

REQUIRED_GOVERNANCE = {
    "training": "OFF",
    "audit_b_n1": "UNOPENED",
    "protected_full104_outcomes": "UNOPENED",
    "d_shared_g5": "UNOPENED",
    "rare_tail_molecular": "UNOPENED",
    "therapeutic_ranking": "OFF",
    "reader_validation22": "CLOSED",
    "reader_oracle23": "SEALED",
    "foundation_development24": "CLOSED",
    "foundation_sealed24": "SEALED",
    "external_siletti": "SEALED",
    "pathology": "CLOSED",
}

REQUIRED_SUBSTRATE = {
    "cells": 4553407,
    "donors": 104,
    "operators": 42,
    "addresses": 41238,
    "common_core_addresses": 17186,
    "level4_blocks": 8915,
    "source_donors": {"SEA_AD": 46, "HVS": 41, "NPH52": 17},
}

REQUIRED_FORBIDDEN_INHERITED = {
    "mask_fraction_0.40",
    "ema_0.99",
    "ema_0.996",
    "depth_6_blocks",
    "width_160",
    "batch_geometry_128x8",
}


class Stop(ValueError):
    """Raised on any fail-closed violation."""


def _stop(tag: str) -> None:
    raise Stop("STOP_LANEA_" + tag)


def _walk(node: Any, path: str = "") -> Iterator[tuple[str, Any, Any]]:
    """Yield (path, key, value) for every mapping entry and (path, None, value) for list items."""
    if isinstance(node, dict):
        for key, value in node.items():
            yield path, key, value
            yield from _walk(value, f"{path}.{key}" if path else str(key))
    elif isinstance(node, list):
        for index, value in enumerate(node):
            child = f"{path}[{index}]"
            yield child, None, value
            yield from _walk(value, child)


def _require(value: Any, expected: Any, tag: str) -> None:
    if type(value) is not type(expected) or value != expected:
        _stop(tag)


def _nonempty_str(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _check_no_authority_assertions(doc: dict) -> None:
    for path, key, value in _walk(doc):
        label = key.lower() if key is not None else path
        if key is not None:
            if label in FORBIDDEN_AUTHORITY_KEYS:
                _stop("TRAINING_AUTHORITY_KEY_PRESENT_" + label)
            if "authoriz" in label and not (
                value is False or value == "NONE" or value == UNSET
            ):
                _stop("AUTHORITY_ASSERTION_" + label)
        if isinstance(value, str) and BANNED_AUTHORIZATION.search(value.upper()):
            _stop("AUTHORIZATION_LANGUAGE_" + label)


def _check_number_free_subtrees(doc: dict) -> None:
    for name in NUMBER_FREE_SUBTREES:
        if name not in doc:
            _stop("MISSING_SECTION_" + name)
        for path, key, value in _walk(doc[name], name):
            if isinstance(value, bool):
                continue
            if isinstance(value, (int, float)):
                _stop("NUMERIC_SPILLOVER_" + (key or path))


def _check_unset_parameters(doc: dict) -> None:
    unset = doc["unset_parameters"]
    if not isinstance(unset, dict):
        _stop("UNSET_PARAMETERS_NOT_A_MAPPING")
    for name in REQUIRED_UNSET:
        if name not in unset:
            _stop("MISSING_UNSET_PARAMETER_" + name)
    for name, value in unset.items():
        if value != UNSET:
            _stop("UNSET_PARAMETER_HAS_A_VALUE_" + name)


def _check_decisions(doc: dict) -> None:
    decisions = doc["decisions_open"]
    if not isinstance(decisions, list):
        _stop("DECISIONS_NOT_A_LIST")
    seen = {}
    for entry in decisions:
        if not isinstance(entry, dict) or "id" not in entry:
            _stop("DECISION_MALFORMED")
        seen[entry["id"]] = entry
    for did in REQUIRED_DECISIONS:
        if did not in seen:
            _stop("MISSING_DECISION_" + did)
        entry = seen[did]
        options = entry.get("options")
        if not isinstance(options, list) or len(options) < 2:
            _stop("DECISION_WITHOUT_ALTERNATIVES_" + did)
        if entry.get("selected") != UNSET:
            _stop("DECISION_PRESELECTED_" + did)
    d6 = seen["D6"]
    if "INPUT_TO_PRIMARY_PATH" in d6.get("options", []):
        _stop("MEASUREMENT_STATE_OFFERED_AS_INPUT")
    if d6.get("forbidden_option") != "INPUT_TO_PRIMARY_PATH":
        _stop("MEASUREMENT_STATE_INPUT_NOT_FORBIDDEN")


def _check_candidates(doc: dict) -> None:
    candidates = doc["candidates"]
    if not isinstance(candidates, dict):
        _stop("CANDIDATES_NOT_A_MAPPING")
    for name in REQUIRED_CANDIDATES:
        if name not in candidates:
            _stop("MISSING_CANDIDATE_" + name)
    for name, candidate in candidates.items():
        for field in REQUIRED_CANDIDATE_FIELDS:
            if not _nonempty_str(candidate.get(field)):
                _stop(f"CANDIDATE_FIELD_MISSING_{name}_{field}")
        for side in ("in_favour", "against"):
            if not isinstance(candidate.get(side), list) or not candidate[side]:
                _stop(f"CANDIDATE_TRADEOFF_MISSING_{name}_{side}")
    seams = {candidates[name]["query_scalar_withholding_point"] for name in REQUIRED_CANDIDATES}
    if len(seams) < 2:
        _stop("CANDIDATE_SPACE_COLLAPSED_TO_ONE_SCALAR_SEAM")
    if doc.get("selected_candidate") != UNSET:
        _stop("CANDIDATE_SILENTLY_SELECTED")


def _check_controls(doc: dict) -> None:
    controls = doc["controls"]
    if not isinstance(controls, list) or not controls:
        _stop("CONTROLS_MISSING")
    names = set()
    positives = 0
    for control in controls:
        cid = control.get("id", "?")
        name = control.get("name")
        if not _nonempty_str(name):
            _stop("CONTROL_UNNAMED_" + str(cid))
        names.add(name)
        if not _nonempty_str(control.get("condition")):
            _stop("CONTROL_WITHOUT_CONDITION_" + cid)
        outcome = control.get("disqualifying_outcome")
        if not _nonempty_str(outcome):
            _stop("CONTROL_WITHOUT_FAILING_OUTCOME_" + cid)
        if control.get("margin") != UNSET:
            _stop("CONTROL_MARGIN_PRESET_" + cid)
        polarity = control.get("polarity")
        if polarity == "POSITIVE_MUST_SUCCEED":
            positives += 1
        elif polarity == "NEGATIVE_MUST_FAIL":
            if "disqualif" not in outcome.lower():
                _stop("CONTROL_OUTCOME_NOT_FALSIFYING_" + cid)
        elif polarity != "DIAGNOSTIC_NOT_DISQUALIFYING":
            _stop("CONTROL_POLARITY_UNDECLARED_" + cid)
    missing = REQUIRED_CONTROL_NAMES - names
    if missing:
        _stop("MISSING_CONTROL_" + sorted(missing)[0])
    if positives < 1:
        _stop("NO_POSITIVE_CONTROL__CONTROL_BATTERY_HAS_NO_DEMONSTRATED_SENSITIVITY")
    technical = next(c for c in controls if c.get("name") == "TECHNICAL_ONLY")
    requirement = technical.get("architectural_requirement", "")
    if "NEVER_INPUT_TO_PRIMARY_PATH" not in requirement:
        _stop("MEASUREMENT_STATE_NOT_CONFINED_TO_SEPARATE_OUTPUTS")


def _check_control_protocol(doc: dict) -> None:
    protocol = doc["control_protocol"]
    _require(protocol.get("independent_unit"), "DONOR", "INDEPENDENT_UNIT_IS_NOT_THE_DONOR")
    _require(protocol.get("independent_unit_count"), 104, "INDEPENDENT_UNIT_COUNT")
    _require(
        protocol.get("uncertainty_method"),
        "DONOR_CLUSTERED_RESAMPLING",
        "UNCERTAINTY_NOT_DONOR_CLUSTERED",
    )
    _require(protocol.get("metric"), UNSET, "METRIC_PRESELECTED")
    if "UNCONDITIONAL" not in str(protocol.get("reporting", "")):
        _stop("REPORTING_NOT_UNCONDITIONAL")
    if "COMMON_RANDOM_NUMBERS" not in str(protocol.get("pairing", "")):
        _stop("CONTROLS_NOT_PAIRED_UNDER_COMMON_RANDOM_NUMBERS")


def _check_leakage(doc: dict) -> None:
    paths = doc["leakage_paths"]
    if not isinstance(paths, list):
        _stop("LEAKAGE_PATHS_NOT_A_LIST")
    byid = {p.get("id"): p for p in paths if isinstance(p, dict)}
    for lid in REQUIRED_LEAKAGE_IDS:
        if lid not in byid:
            _stop("MISSING_LEAKAGE_PATH_" + lid)
        entry = byid[lid]
        if not _nonempty_str(entry.get("detection")):
            _stop("LEAKAGE_PATH_WITHOUT_DETECTION_" + lid)
        if not _nonempty_str(entry.get("repair")):
            _stop("LEAKAGE_PATH_WITHOUT_REPAIR_" + lid)
        if not _nonempty_str(entry.get("name")):
            _stop("LEAKAGE_PATH_UNNAMED_" + lid)
    if "TEACHER" not in byid["L1"]["name"].upper():
        _stop("L1_IS_NOT_THE_TEACHER_CONTEXT_SEAM")
    if "NORMALIZATION" not in byid["L2"]["name"].upper():
        _stop("L2_IS_NOT_THE_NORMALIZATION_SEAM")


def _check_masking(doc: dict) -> None:
    masking = doc["masking_status"]
    _require(
        masking.get("previous_september16_result"),
        "NINE_CELL_GRID_NO_QUALIFIER",
        "FALSE_MASK_QUALIFICATION",
    )
    _require(masking.get("grid_exhausted"), True, "GRID_NOT_RECORDED_AS_EXHAUSTED")
    _require(
        masking.get("no_new_threshold_was_introduced_to_make_something_pass"),
        True,
        "THRESHOLD_WIDENING_CLAIM",
    )
    _require(
        masking.get("masking_authority_resolved_by_this_document"),
        False,
        "MASK_AUTHORITY_FALSELY_RESOLVED",
    )
    _require(
        masking.get("standing_terminal"),
        "MASKING_SHORTCUT_AUTHORITY_NOT_YET_RESOLVED",
        "MASK_TERMINAL_OVERWRITTEN",
    )


def _check_forbidden_inherited(doc: dict) -> None:
    block = doc["forbidden_inherited_values"]
    listed = set()
    for value in block.values():
        if isinstance(value, list):
            listed.update(value)
    missing = REQUIRED_FORBIDDEN_INHERITED - listed
    if missing:
        _stop("FORBIDDEN_INHERITED_VALUE_NOT_LISTED_" + sorted(missing)[0])
    if "NO_ARM_OF_THE_2026_09_16_NINE_CELL_MASKING_GRID_MAY_BE_RELABELLED_AS_QUALIFIED" != block.get(
        "forbidden_relabelling"
    ):
        _stop("FAILED_MASK_ARM_RELABELLING_NOT_FORBIDDEN")


def _check_substrate(doc: dict) -> None:
    substrate = doc["substrate_reference"]
    for key, expected in REQUIRED_SUBSTRATE.items():
        _require(substrate.get(key), expected, "SUBSTRATE_" + key)
    if "NOT_RECOMPUTED" not in str(substrate.get("role", "")):
        _stop("SUBSTRATE_PRESENTED_AS_FRESH_COMPUTATION")


def _check_governance(doc: dict) -> None:
    governance = doc["governance"]
    for key, expected in REQUIRED_GOVERNANCE.items():
        _require(governance.get(key), expected, "GOVERNANCE_" + key)
    for key in (
        "protected_outcome_informed_any_statement_in_this_document",
        "provisional_network_width_treated_as_a_measured_biological_dimension",
        "this_document_selects_a_candidate",
        "this_document_sets_any_numeric_threshold",
        "this_document_issues_execution_permission",
    ):
        _require(governance.get(key), False, "GOVERNANCE_" + key)


def _check_classification(doc: dict) -> None:
    rows = doc["classification_against_pr152"]
    if not isinstance(rows, list) or not rows:
        _stop("CLASSIFICATION_MISSING")
    byelement = {r.get("element"): r.get("classification") for r in rows}
    for element in (
        "competing_target_constructions",
        "per_candidate_mechanism_specification",
        "controls_with_a_disqualifying_outcome",
        "seam_by_seam_leakage_enumeration",
    ):
        if byelement.get(element) != "GENUINELY_OPEN":
            _stop("CLASSIFICATION_NOT_STATED_" + element)
    if "ALREADY_DONE" not in set(byelement.values()):
        _stop("CLASSIFICATION_CLAIMS_NOTHING_WAS_ALREADY_DONE")
    relationship = doc["companion_of"].get("relationship", "")
    if "COMPANION_NOT_REPLACEMENT" not in relationship:
        _stop("PR152_TREATED_AS_SUPERSEDED")


def check(doc: dict) -> str:
    _require(doc.get("schema"), SCHEMA, "SCHEMA")
    _require(doc.get("document_role"), ROLE, "ROLE")
    _require(doc.get("authority_issued"), "NONE", "AUTHORITY_ISSUED")
    _check_no_authority_assertions(doc)
    _check_number_free_subtrees(doc)
    _check_unset_parameters(doc)
    _check_decisions(doc)
    _check_candidates(doc)
    _check_controls(doc)
    _check_control_protocol(doc)
    _check_leakage(doc)
    _check_masking(doc)
    _check_forbidden_inherited(doc)
    _check_substrate(doc)
    _check_governance(doc)
    _check_classification(doc)
    return "PASS_LANEA_NONAUTHORIZING_CANDIDATE_SPACE"


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: v29_lane_a_candidate_space_firewall_v1.py <proposal.json>", file=sys.stderr)
        return 2
    doc = json.loads(pathlib.Path(argv[1]).read_text(encoding="utf-8"))
    verdict = check(doc)
    print(verdict)
    print(
        "This proves only that the proposal keeps every open choice open. "
        "It is not a target selection and not permission to train."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
