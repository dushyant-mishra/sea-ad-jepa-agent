"""Fail-closed G6 decision repair after hostile real-data review.

V2 proved useful arithmetic but allowed caller-typed qualification tokens and a
zero substantive margin. V3 deliberately separates a diagnostic recurrence
calculation from human biological PASS/FAIL authority. Until an independently
sealed decision-qualification receipt is frozen in code, no caller-supplied
string or token can authorize a human G6 verdict.
"""
from __future__ import annotations

import math
import re
from collections.abc import Mapping


class TeacherInformationDecisionV3Error(ValueError):
    pass


SCHEMA = "JEPA_TD_REAL_G6_MARGIN_AWARE_DECISION_V3"
REFERENCE_SCHEMA = "JEPA_TD_REAL_G6_REFERENCE_MARGIN_V3"
METRIC = "DONOR_BALANCED_OUTER_MSE_DELTA"
ORIENTATION = "STUDENT_MSE_MINUS_TEACHER_MSE__LARGER_IS_BETTER"
FAMILY_ALPHA = 0.01
HEX64 = re.compile(r"^[0-9a-f]{64}$")

# Deliberately unset. A later, separate qualification lane may freeze an exact
# independently produced receipt only after hostile sealed-world qualification.
SEALED_EXTERNAL_DECISION_QUALIFICATION_SHA256: str | None = None

NO_AUTHORITY = {
    "value_read_authorized": False,
    "real_tournament_authorized": False,
    "target_selection_authorized": False,
    "representation_selection_authorized": False,
    "td60_authorized": False,
    "stage4_authorized": False,
    "training_authorized": False,
}


def _hex(value: object, label: str) -> str:
    if not isinstance(value, str) or HEX64.fullmatch(value) is None:
        raise TeacherInformationDecisionV3Error(f"{label} must be lowercase 64-hex")
    return value


def _base(*, status: str, reason: str, binding: str | None, diagnostic_status: str | None = None,
          donor_contrasts: list[dict] | None = None, positive_test: dict | None = None,
          negative_test: dict | None = None) -> dict:
    return {
        "schema": SCHEMA,
        "status": status,
        "reason": reason,
        "diagnostic_status": diagnostic_status,
        "metric": METRIC,
        "orientation": ORIENTATION,
        "family_alpha": FAMILY_ALPHA,
        "input_binding_sha256": binding,
        "donor_contrasts": [] if donor_contrasts is None else donor_contrasts,
        "positive_recurrence_test": positive_test,
        "negative_recurrence_test": negative_test,
        "human_pass_fail_authorized": False,
        "claim_boundary": "FINITE_LINEAR_DIAGNOSTIC_ONLY__NO_INFORMATION_THEORETIC_ABSENCE_CLAIM",
        "authority": dict(NO_AUTHORITY),
    }


def _exact_one_sided_sign_tail(*, successes: int, n: int) -> float:
    if n <= 0:
        return 1.0
    return sum(math.comb(n, k) for k in range(successes, n + 1)) / (2 ** n)


def _sign_recurrence(values: list[float], *, positive: bool) -> dict:
    nonzero = [v for v in values if v != 0.0]
    n = len(nonzero)
    if positive:
        successes = sum(v > 0.0 for v in nonzero)
        direction = "POSITIVE"
    else:
        successes = sum(v < 0.0 for v in nonzero)
        direction = "NEGATIVE"
    p = _exact_one_sided_sign_tail(successes=successes, n=n)
    resolution_estimable = n > 0 and (0.5 ** n) <= FAMILY_ALPHA
    return {
        "direction": direction,
        "n_nonzero": n,
        "successes": successes,
        "p_value": p,
        "alpha": FAMILY_ALPHA,
        "resolution_estimable": resolution_estimable,
        "pass": bool(resolution_estimable and p <= FAMILY_ALPHA),
    }


def _normalize_probe(probe_result: Mapping) -> tuple[str, str, str, list[tuple[str, float]] | None]:
    if not isinstance(probe_result, Mapping):
        raise TeacherInformationDecisionV3Error("probe_result must be a mapping")
    status = probe_result.get("status")
    if status not in {"PASS", "FAIL", "NOT_ESTIMABLE"}:
        raise TeacherInformationDecisionV3Error("probe status must be PASS, FAIL, or NOT_ESTIMABLE")
    binding = _hex(probe_result.get("input_binding_sha256"), "probe input binding")
    scale = _hex(probe_result.get("target_scale_contract_sha256"), "probe target scale contract")
    rows = probe_result.get("donor_deltas")
    if not isinstance(rows, list):
        raise TeacherInformationDecisionV3Error("probe donor_deltas must be a list")
    seen: set[str] = set()
    normalized: list[tuple[str, float]] = []
    for row in rows:
        if not isinstance(row, Mapping) or set(row) != {"donor_id", "delta"}:
            raise TeacherInformationDecisionV3Error("probe donor rows must contain exactly donor_id and delta")
        donor = row["donor_id"]
        if not isinstance(donor, str) or not donor or donor in seen:
            raise TeacherInformationDecisionV3Error("probe donor IDs must be unique nonempty strings")
        seen.add(donor)
        value = row["delta"]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
            return status, binding, scale, None
        normalized.append((donor, float(value)))
    return status, binding, scale, normalized


def _normalize_reference(reference_artifact: Mapping, *, binding: str, scale: str,
                         donors: set[str]) -> tuple[dict[str, float] | None, str | None]:
    if not isinstance(reference_artifact, Mapping):
        raise TeacherInformationDecisionV3Error("reference artifact is required")
    required = {
        "schema", "frozen", "qualified", "metric", "orientation", "reference_kind",
        "donor_margins", "input_binding_sha256", "target_scale_contract_sha256",
        "reference_receipt_sha256", "independent_non_degenerate_reference",
    }
    if set(reference_artifact) != required:
        raise TeacherInformationDecisionV3Error("reference artifact fields differ from V3 schema")
    if reference_artifact["schema"] != REFERENCE_SCHEMA:
        raise TeacherInformationDecisionV3Error("reference schema mismatch")
    if reference_artifact["frozen"] is not True or reference_artifact["qualified"] is not True:
        raise TeacherInformationDecisionV3Error("reference must be frozen and qualified")
    if reference_artifact["metric"] != METRIC or reference_artifact["orientation"] != ORIENTATION:
        raise TeacherInformationDecisionV3Error("reference metric/orientation mismatch")
    ref_binding = _hex(reference_artifact["input_binding_sha256"], "reference input binding")
    if ref_binding != binding:
        raise TeacherInformationDecisionV3Error("reference binding must match probe binding exactly")
    ref_scale = _hex(reference_artifact["target_scale_contract_sha256"], "reference target scale contract")
    if ref_scale != scale:
        raise TeacherInformationDecisionV3Error("reference target scale contract must match probe scale exactly")
    _hex(reference_artifact["reference_receipt_sha256"], "reference receipt")
    raw = reference_artifact["donor_margins"]
    if not isinstance(raw, Mapping) or set(raw) != donors:
        raise TeacherInformationDecisionV3Error("reference donor roster must match probe exactly")
    margins: dict[str, float] = {}
    for donor, value in raw.items():
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
            return None, "NUMERICAL_FAILURE"
        margins[donor] = float(value)
    if (
        reference_artifact["independent_non_degenerate_reference"] is not True
        or not margins
        or any(value <= 0.0 for value in margins.values())
    ):
        return margins, "NONDEGENERATE_SUBSTANTIVE_MARGIN_NOT_ESTABLISHED"
    return margins, None


def adjudicate_g6_v3(*, probe_result, reference_artifact,
                      external_qualification_receipt_sha256=None, alpha: float = FAMILY_ALPHA) -> dict:
    if isinstance(alpha, bool) or not isinstance(alpha, (int, float)) or float(alpha) != FAMILY_ALPHA:
        raise TeacherInformationDecisionV3Error(f"alpha is frozen at {FAMILY_ALPHA}")

    status, binding, scale, probe = _normalize_probe(probe_result)
    if status == "NOT_ESTIMABLE":
        return _base(status="NOT_ESTIMABLE", reason="PROBE_NOT_ESTIMABLE", binding=binding)
    if probe is None:
        return _base(status="NUMERICAL_FAILURE", reason="NONFINITE_PROBE_VALUE", binding=binding)

    donors = {donor for donor, _ in probe}
    margins, reference_problem = _normalize_reference(
        reference_artifact, binding=binding, scale=scale, donors=donors
    )
    if reference_problem == "NUMERICAL_FAILURE":
        return _base(status="NUMERICAL_FAILURE", reason="NONFINITE_REFERENCE_VALUE", binding=binding)
    if reference_problem == "NONDEGENERATE_SUBSTANTIVE_MARGIN_NOT_ESTABLISHED":
        return _base(
            status="NOT_ESTIMABLE",
            reason="NONDEGENERATE_SUBSTANTIVE_MARGIN_NOT_ESTABLISHED",
            binding=binding,
        )
    assert margins is not None

    contrasts = [
        {
            "donor_id": donor,
            "raw_delta": raw,
            "substantive_margin": margins[donor],
            "margin_adjusted_delta": raw - margins[donor],
        }
        for donor, raw in probe
    ]
    adjusted = [row["margin_adjusted_delta"] for row in contrasts]
    pos = _sign_recurrence(adjusted, positive=True)
    neg = _sign_recurrence(adjusted, positive=False)
    if pos["pass"] and not neg["pass"]:
        diagnostic = "ADVANTAGE_RECURRENT_BEYOND_MARGIN"
    elif neg["pass"] and not pos["pass"]:
        diagnostic = "NONADVANTAGE_RECURRENT_BEYOND_MARGIN"
    else:
        diagnostic = "INCONCLUSIVE"

    frozen = SEALED_EXTERNAL_DECISION_QUALIFICATION_SHA256
    if frozen is None:
        return _base(
            status="NOT_ESTIMABLE",
            reason="SEALED_EXTERNAL_DECISION_QUALIFICATION_NOT_FROZEN",
            binding=binding,
            diagnostic_status=diagnostic,
            donor_contrasts=contrasts,
            positive_test=pos,
            negative_test=neg,
        )
    if external_qualification_receipt_sha256 != frozen:
        return _base(
            status="NOT_ESTIMABLE",
            reason="SEALED_EXTERNAL_DECISION_QUALIFICATION_RECEIPT_MISMATCH",
            binding=binding,
            diagnostic_status=diagnostic,
            donor_contrasts=contrasts,
            positive_test=pos,
            negative_test=neg,
        )

    # V3 intentionally contains no human PASS/FAIL mapping. A later version may
    # add it only after the exact external qualification receipt is frozen.
    return _base(
        status="NOT_ESTIMABLE",
        reason="HUMAN_G6_MAPPING_NOT_IMPLEMENTED_IN_V3",
        binding=binding,
        diagnostic_status=diagnostic,
        donor_contrasts=contrasts,
        positive_test=pos,
        negative_test=neg,
    )
