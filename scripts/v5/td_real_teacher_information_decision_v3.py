"""Fail-closed G6 human-decision contract after hostile real-data review.

The V2 arithmetic remains a useful diagnostic, but hostile review showed that:
- deterministic closed-form ridge can make U_refit exactly zero;
- a zero margin collapses the intended substantive decision back to direction;
- V2 human decision qualification can be represented by caller-typed schema/status
  tokens rather than an independently produced, identity-bound receipt; and
- the donor-balanced outer MSE delta is reported in raw target units, whose scale
  sensitivity remains a separate open scientific contract question.

V3 therefore does not silently change the metric. It validates what a future
substantive reference must contain and fail-closes human G6 adjudication until a
separate produced qualification receipt and scale contract are prospectively
qualified.
"""
from __future__ import annotations

import math
import re
from collections.abc import Mapping


class TeacherInformationDecisionV3Error(ValueError):
    pass


SCHEMA = "JEPA_TD_REAL_G6_HUMAN_DECISION_CONTRACT_V3"
REFERENCE_SCHEMA = "JEPA_TD_REAL_G6_REFERENCE_MARGIN_V2"
METRIC = "DONOR_BALANCED_OUTER_MSE_DELTA"
ORIENTATION = "STUDENT_MSE_MINUS_TEACHER_MSE__LARGER_IS_BETTER"
METRIC_SCALE_STATUS = "RAW_TARGET_UNITS__SCALE_SENSITIVITY_OPEN__NO_SILENT_METRIC_REWRITE"
_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_ALLOWED_REFERENCE_KINDS = {"U_MEASUREMENT", "MAX_U_REFIT_U_MEASUREMENT"}
_NO_AUTHORITY = {
    "value_read_authorized": False,
    "real_tournament_authorized": False,
    "target_selection_authorized": False,
    "representation_selection_authorized": False,
    "td60_authorized": False,
    "stage4_authorized": False,
    "training_authorized": False,
}


def _hex(value: object, label: str) -> str:
    if not isinstance(value, str) or _HEX64.fullmatch(value) is None:
        raise TeacherInformationDecisionV3Error(f"{label} must be a lowercase 64-hex SHA-256")
    return value


def _margin(value: object, donor: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TeacherInformationDecisionV3Error(f"margin for donor {donor} must be finite numeric")
    out = float(value)
    if not math.isfinite(out) or out < 0.0:
        raise TeacherInformationDecisionV3Error(f"margin for donor {donor} must be finite and nonnegative")
    return out


def validate_reference_for_future_human_use(reference_artifact: Mapping[str, object]) -> dict:
    if not isinstance(reference_artifact, Mapping):
        raise TeacherInformationDecisionV3Error("reference artifact must be a mapping")
    required = {
        "schema", "frozen", "qualified", "metric", "orientation", "reference_kind",
        "input_binding_sha256", "reference_receipt_sha256", "producer_code_sha256",
        "measurement_component_present", "measurement_component_non_degenerate", "donor_margins",
    }
    if set(reference_artifact) != required:
        raise TeacherInformationDecisionV3Error("reference artifact fields differ from the V3 frozen schema")
    if reference_artifact["schema"] != REFERENCE_SCHEMA:
        raise TeacherInformationDecisionV3Error("reference schema mismatch")
    if reference_artifact["frozen"] is not True or reference_artifact["qualified"] is not True:
        raise TeacherInformationDecisionV3Error("reference must be frozen and independently qualified")
    if reference_artifact["metric"] != METRIC:
        raise TeacherInformationDecisionV3Error("reference metric mismatch")
    if reference_artifact["orientation"] != ORIENTATION:
        raise TeacherInformationDecisionV3Error("reference orientation mismatch")

    _hex(reference_artifact["input_binding_sha256"], "input binding")
    _hex(reference_artifact["reference_receipt_sha256"], "reference receipt")
    _hex(reference_artifact["producer_code_sha256"], "producer code")

    kind = reference_artifact["reference_kind"]
    if kind not in _ALLOWED_REFERENCE_KINDS:
        return {
            "schema": SCHEMA,
            "status": "NOT_ESTIMABLE_SUBSTANTIVE_MARGIN",
            "reason": "MEASUREMENT_COMPONENT_REQUIRED",
            "human_use_authorized": False,
            "metric_scale_status": METRIC_SCALE_STATUS,
            "authority": dict(_NO_AUTHORITY),
        }
    if reference_artifact["measurement_component_present"] is not True or reference_artifact["measurement_component_non_degenerate"] is not True:
        return {
            "schema": SCHEMA,
            "status": "NOT_ESTIMABLE_SUBSTANTIVE_MARGIN",
            "reason": "DEGENERATE_OR_ABSENT_MEASUREMENT_MARGIN",
            "human_use_authorized": False,
            "metric_scale_status": METRIC_SCALE_STATUS,
            "authority": dict(_NO_AUTHORITY),
        }

    raw = reference_artifact["donor_margins"]
    if not isinstance(raw, Mapping) or not raw:
        raise TeacherInformationDecisionV3Error("donor_margins must be a nonempty mapping")
    margins: dict[str, float] = {}
    for donor, value in raw.items():
        if not isinstance(donor, str) or not donor or donor != donor.strip() or "\0" in donor:
            raise TeacherInformationDecisionV3Error("donor margin IDs must be nonempty trimmed strings")
        margins[donor] = _margin(value, donor)
    if any(value <= 0.0 for value in margins.values()):
        return {
            "schema": SCHEMA,
            "status": "NOT_ESTIMABLE_SUBSTANTIVE_MARGIN",
            "reason": "NONPOSITIVE_DONOR_MARGIN",
            "human_use_authorized": False,
            "metric_scale_status": METRIC_SCALE_STATUS,
            "authority": dict(_NO_AUTHORITY),
        }

    return {
        "schema": SCHEMA,
        "status": "REFERENCE_MECHANICALLY_READY__HUMAN_DECISION_STILL_BLOCKED",
        "reason": "PRODUCED_QUALIFICATION_AND_SCALE_CONTRACT_STILL_REQUIRED",
        "human_use_authorized": False,
        "metric": METRIC,
        "orientation": ORIENTATION,
        "metric_scale_status": METRIC_SCALE_STATUS,
        "reference_kind": kind,
        "input_binding_sha256": reference_artifact["input_binding_sha256"],
        "reference_receipt_sha256": reference_artifact["reference_receipt_sha256"],
        "producer_code_sha256": reference_artifact["producer_code_sha256"],
        "authority": dict(_NO_AUTHORITY),
    }


def human_execution_readiness(*, probe_qualification, decision_qualification, reference_artifact) -> dict:
    reference = validate_reference_for_future_human_use(reference_artifact)
    # V2 qualification mappings are intentionally not inspected for authority.
    # They remain historical diagnostic evidence, not produced V3 receipts.
    return {
        "schema": SCHEMA,
        "status": "BLOCKED_G6_PRODUCED_QUALIFICATION_RECEIPT_REQUIRED",
        "reason": (
            "CALLER_TYPED_V2_QUALIFICATION_TOKENS_CANNOT_AUTHORIZE_HUMAN_G6__"
            "V3_REQUIRES_A_SEPARATELY_PRODUCED_IDENTITY_BOUND_QUALIFICATION_RECEIPT_AND_SCALE_CONTRACT"
        ),
        "reference_status": reference["status"],
        "human_g6_adjudication_authorized": False,
        "v2_probe_qualification_has_human_authority": False,
        "v2_decision_qualification_has_human_authority": False,
        "metric": METRIC,
        "orientation": ORIENTATION,
        "metric_scale_status": METRIC_SCALE_STATUS,
        "authority": dict(_NO_AUTHORITY),
    }
