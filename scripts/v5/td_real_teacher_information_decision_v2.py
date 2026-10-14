"""Prospective margin-aware decision contract for real-TD G6.

Consumes the already-qualified finite ridge probe output and an independently
qualified same-metric reference artifact. A positive raw teacher advantage is
not sufficient: donor-level student-minus-teacher MSE deltas must exceed their
pre-frozen technical/refit margins before donor-primary sign testing.

Probe and reference must bind the exact same frozen deciding input realization.
This module does not read human values itself and grants no execution authority.
"""
from __future__ import annotations

import math
import re
from collections.abc import Mapping

from scripts.v5 import td_target_tournament_precision as P


class TeacherInformationDecisionError(ValueError):
    pass


PROBE_QUAL_SCHEMA = "JEPA_TD_REAL_G6_TEACHER_INFORMATION_PROBE_QUALIFICATION_V1"
PROBE_QUAL_STATUS = "PASS_KNOWN_TRUTH_G6_PROBE_QUALIFICATION"
PROBE_SCOPE = "MATCHED_MULTI_OUTPUT_RIDGE_OPERATIONAL_DIAGNOSTIC"
REFERENCE_SCHEMA = "JEPA_TD_REAL_G6_REFERENCE_MARGIN_V1"
METRIC = "DONOR_BALANCED_OUTER_MSE_DELTA"
ORIENTATION = "STUDENT_MSE_MINUS_TEACHER_MSE__LARGER_IS_BETTER"
REFERENCE_KINDS = {"U_REFIT", "U_MEASUREMENT", "MAX_U_REFIT_U_MEASUREMENT"}
HEX64 = re.compile(r"^[0-9a-f]{64}$")
NO_AUTHORITY = {
    "value_read_authorized": False,
    "real_tournament_authorized": False,
    "target_selection_authorized": False,
    "representation_selection_authorized": False,
    "td60_authorized": False,
    "stage4_authorized": False,
    "training_authorized": False,
}


def _number(value, label: str, *, nonnegative: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TeacherInformationDecisionError(f"{label} must be a finite numeric value")
    out = float(value)
    if not math.isfinite(out):
        raise TeacherInformationDecisionError(f"{label} must be a finite numeric value")
    if nonnegative and out < 0.0:
        raise TeacherInformationDecisionError(f"{label} must be nonnegative")
    return out


def _hex(value, label: str) -> str:
    if not isinstance(value, str) or not HEX64.fullmatch(value):
        raise TeacherInformationDecisionError(f"{label} must be lowercase 64-hex")
    return value


def _probe_qualification_valid(value) -> bool:
    return bool(
        isinstance(value, Mapping)
        and value.get("schema") == PROBE_QUAL_SCHEMA
        and value.get("status") == PROBE_QUAL_STATUS
        and value.get("human_fail_semantics_qualified") is True
        and value.get("probe_scope") == PROBE_SCOPE
    )


def _normalize_probe(probe_result: Mapping) -> tuple[str, str, list[tuple[str, float]]]:
    if not isinstance(probe_result, Mapping):
        raise TeacherInformationDecisionError("probe_result must be a mapping")
    status = probe_result.get("status")
    if status not in {"PASS", "FAIL", "NOT_ESTIMABLE"}:
        raise TeacherInformationDecisionError("probe_result status must be PASS, FAIL, or NOT_ESTIMABLE")
    binding = _hex(probe_result.get("input_binding_sha256"), "probe input_binding_sha256")
    raw = probe_result.get("donor_deltas")
    if not isinstance(raw, list):
        raise TeacherInformationDecisionError("probe_result donor_deltas must be a list")
    seen: set[str] = set()
    normalized: list[tuple[str, float]] = []
    for index, row in enumerate(raw):
        if not isinstance(row, Mapping) or set(row) != {"donor_id", "delta"}:
            raise TeacherInformationDecisionError(
                "each probe donor delta must contain exactly donor_id and delta"
            )
        donor = row["donor_id"]
        if not isinstance(donor, str) or not donor or donor != donor.strip() or "\0" in donor:
            raise TeacherInformationDecisionError(f"probe donor_deltas[{index}] donor_id is invalid")
        if donor in seen:
            raise TeacherInformationDecisionError(f"duplicate probe donor: {donor}")
        seen.add(donor)
        normalized.append((donor, _number(row["delta"], f"probe delta for {donor}")))
    return status, binding, normalized


def _validate_reference(
    reference_artifact: Mapping,
    probe_donors: set[str],
    deciding_binding: str,
) -> dict[str, float]:
    if not isinstance(reference_artifact, Mapping):
        raise TeacherInformationDecisionError("a frozen qualified reference artifact is required")
    required = {
        "schema",
        "frozen",
        "qualified",
        "metric",
        "orientation",
        "reference_kind",
        "donor_margins",
        "deciding_namespace_disjoint",
        "input_binding_sha256",
        "reference_receipt_sha256",
    }
    if set(reference_artifact) != required:
        raise TeacherInformationDecisionError("reference artifact fields differ from the frozen schema")
    if reference_artifact["schema"] != REFERENCE_SCHEMA:
        raise TeacherInformationDecisionError("reference artifact schema mismatch")
    if reference_artifact["frozen"] is not True:
        raise TeacherInformationDecisionError("reference artifact must be frozen")
    if reference_artifact["qualified"] is not True:
        raise TeacherInformationDecisionError("reference artifact must be qualified")
    if reference_artifact["metric"] != METRIC:
        raise TeacherInformationDecisionError("reference metric is not commensurate with the G6 donor delta")
    if reference_artifact["orientation"] != ORIENTATION:
        raise TeacherInformationDecisionError("reference orientation is not commensurate with the G6 donor delta")
    if reference_artifact["reference_kind"] not in REFERENCE_KINDS:
        raise TeacherInformationDecisionError("reference_kind is not an allowed G6 substantive margin")
    if reference_artifact["deciding_namespace_disjoint"] is not True:
        raise TeacherInformationDecisionError("reference and deciding namespaces must be disjoint")
    ref_binding = _hex(reference_artifact["input_binding_sha256"], "reference input_binding_sha256")
    _hex(reference_artifact["reference_receipt_sha256"], "reference_receipt_sha256")
    if ref_binding != deciding_binding:
        raise TeacherInformationDecisionError(
            "reference input binding must equal the exact probe deciding input binding"
        )

    raw_margins = reference_artifact["donor_margins"]
    if not isinstance(raw_margins, Mapping):
        raise TeacherInformationDecisionError("reference donor_margins must be a mapping")
    margins: dict[str, float] = {}
    for donor, margin in raw_margins.items():
        if not isinstance(donor, str) or not donor or donor != donor.strip() or "\0" in donor:
            raise TeacherInformationDecisionError("reference donor IDs must be nonempty trimmed strings")
        margins[donor] = _number(margin, f"reference margin for {donor}", nonnegative=True)
    if set(margins) != probe_donors:
        raise TeacherInformationDecisionError("reference donor roster must match the probe donor roster exactly")
    return margins


def adjudicate_g6_human_decision(
    *,
    probe_result,
    probe_qualification,
    reference_artifact,
    alpha: float = 0.01,
) -> dict:
    alpha_value = _number(alpha, "alpha")
    if not (0.0 < alpha_value < 1.0):
        raise TeacherInformationDecisionError("alpha must lie in (0,1)")

    probe_status, deciding_binding, probe_deltas = _normalize_probe(probe_result)
    if probe_status == "NOT_ESTIMABLE":
        return {
            "schema": "JEPA_TD_REAL_G6_MARGIN_AWARE_DECISION_V2",
            "status": "NOT_ESTIMABLE",
            "reason": "PROBE_NOT_ESTIMABLE",
            "input_binding_sha256": deciding_binding,
            "donor_contrasts": [],
            "sign_test": None,
            "claim_boundary": "FINITE_LINEAR_DIAGNOSTIC_ONLY__NO_INFORMATION_THEORETIC_ABSENCE_CLAIM",
            "authority": dict(NO_AUTHORITY),
        }

    if not _probe_qualification_valid(probe_qualification):
        return {
            "schema": "JEPA_TD_REAL_G6_MARGIN_AWARE_DECISION_V2",
            "status": "NOT_ESTIMABLE",
            "reason": "PROBE_REJECTION_POWER_NOT_QUALIFIED",
            "input_binding_sha256": deciding_binding,
            "donor_contrasts": [],
            "sign_test": None,
            "claim_boundary": "FINITE_LINEAR_DIAGNOSTIC_ONLY__NO_INFORMATION_THEORETIC_ABSENCE_CLAIM",
            "authority": dict(NO_AUTHORITY),
        }

    donor_set = {donor for donor, _ in probe_deltas}
    margins = _validate_reference(reference_artifact, donor_set, deciding_binding)
    donor_contrasts = [
        {
            "donor_id": donor,
            "raw_delta": raw_delta,
            "substantive_margin": margins[donor],
            "margin_adjusted_delta": raw_delta - margins[donor],
        }
        for donor, raw_delta in probe_deltas
    ]
    sign_input = [
        {"donor_id": row["donor_id"], "delta": row["margin_adjusted_delta"]}
        for row in donor_contrasts
    ]
    sign_test = P.sign_recurrence_gate(sign_input, alpha_value)
    if not sign_test["resolution_estimable"]:
        status = "NOT_ESTIMABLE"
        reason = "DONOR_SIGN_RESOLUTION_INSUFFICIENT"
    elif sign_test["pass"]:
        status = "PASS"
        reason = "TEACHER_ADVANTAGE_EXCEEDS_QUALIFIED_MARGIN"
    else:
        status = "FAIL"
        reason = "TEACHER_ADVANTAGE_NOT_ESTABLISHED_BEYOND_QUALIFIED_MARGIN"

    return {
        "schema": "JEPA_TD_REAL_G6_MARGIN_AWARE_DECISION_V2",
        "status": status,
        "reason": reason,
        "metric": METRIC,
        "orientation": ORIENTATION,
        "reference_kind": reference_artifact["reference_kind"],
        "input_binding_sha256": deciding_binding,
        "donor_contrasts": donor_contrasts,
        "sign_test": sign_test,
        "raw_probe_status": probe_status,
        "claim_boundary": "FINITE_LINEAR_DIAGNOSTIC_ONLY__NO_INFORMATION_THEORETIC_ABSENCE_CLAIM",
        "authority": dict(NO_AUTHORITY),
    }
