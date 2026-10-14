"""G6 V3 substantive-margin decision consumer.

This layer is intentionally a consumer only. It cannot manufacture its own
known-truth qualification or reference margin. Human PASS/FAIL semantics require
separately produced, hash-bearing qualification and reference receipts.
"""
from __future__ import annotations

import math
import re
from collections.abc import Mapping

from scripts.v5 import td_target_tournament_precision as P

FAMILY_ALPHA = 0.01
METRIC = "DONOR_BALANCED_OUTER_MSE_DELTA"
ORIENTATION = "STUDENT_MSE_MINUS_TEACHER_MSE__LARGER_IS_BETTER"
REFERENCE_SCHEMA = "JEPA_TD_REAL_G6_REFERENCE_MARGIN_V2"
QUAL_SCHEMA = "JEPA_TD_REAL_G6_DECISION_QUALIFICATION_RECEIPT_V3"
QUAL_STATUS = "PASS_KNOWN_TRUTH_G6_MARGIN_DECISION_V3"
REFERENCE_KINDS = {"U_MEASUREMENT", "MAX_U_REFIT_U_MEASUREMENT", "U_REFIT"}
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


def _ne(reason: str, binding: str | None = None) -> dict:
    return {
        "schema": "JEPA_TD_REAL_G6_MARGIN_AWARE_DECISION_V3",
        "status": "NOT_ESTIMABLE",
        "reason": reason,
        "input_binding_sha256": binding,
        "donor_contrasts": [],
        "sign_test": None,
        "authority": dict(NO_AUTHORITY),
    }


def _hash(value) -> bool:
    return isinstance(value, str) and HEX64.fullmatch(value) is not None


def _qualification_valid(receipt) -> bool:
    required = {
        "schema", "status", "producer_code_sha256", "qualification_worlds_sha256",
        "receipt_sha256", "human_semantics_qualified",
    }
    return bool(
        isinstance(receipt, Mapping)
        and set(receipt) == required
        and receipt.get("schema") == QUAL_SCHEMA
        and receipt.get("status") == QUAL_STATUS
        and receipt.get("human_semantics_qualified") is True
        and all(_hash(receipt.get(k)) for k in (
            "producer_code_sha256", "qualification_worlds_sha256", "receipt_sha256"
        ))
    )


def _normalize_probe(probe_result):
    if not isinstance(probe_result, Mapping):
        return None
    status = probe_result.get("status")
    binding = probe_result.get("input_binding_sha256")
    rows = probe_result.get("donor_deltas")
    if status not in {"PASS", "FAIL", "NOT_ESTIMABLE"} or not _hash(binding) or not isinstance(rows, list):
        return None
    out = []
    seen = set()
    for row in rows:
        if not isinstance(row, Mapping) or set(row) != {"donor_id", "delta"}:
            return None
        donor = row.get("donor_id")
        value = row.get("delta")
        if not isinstance(donor, str) or not donor or donor in seen:
            return None
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
            return None
        seen.add(donor)
        out.append((donor, float(value)))
    return status, binding, out


def _reference(reference, donors: set[str], binding: str):
    required = {
        "schema", "frozen", "qualified", "metric", "orientation", "reference_kind",
        "donor_margins", "deciding_namespace_disjoint", "input_binding_sha256",
        "reference_receipt_sha256", "producer_code_sha256",
        "producer_qualification_receipt_sha256", "margin_units_sha256",
        "margin_is_non_degenerate",
    }
    if not isinstance(reference, Mapping) or set(reference) != required:
        return None
    if reference.get("schema") != REFERENCE_SCHEMA or reference.get("frozen") is not True or reference.get("qualified") is not True:
        return None
    if reference.get("metric") != METRIC or reference.get("orientation") != ORIENTATION:
        return None
    if reference.get("reference_kind") not in REFERENCE_KINDS or reference.get("deciding_namespace_disjoint") is not True:
        return None
    if reference.get("input_binding_sha256") != binding:
        return None
    if not all(_hash(reference.get(k)) for k in (
        "input_binding_sha256", "reference_receipt_sha256", "producer_code_sha256",
        "producer_qualification_receipt_sha256", "margin_units_sha256"
    )):
        return None
    raw = reference.get("donor_margins")
    if not isinstance(raw, Mapping) or set(raw) != donors:
        return None
    margins = {}
    for donor, value in raw.items():
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return None
        value = float(value)
        if not math.isfinite(value) or value < 0.0:
            return None
        margins[donor] = value
    return margins


def adjudicate_g6_human_decision_v3(*, probe_result, reference_artifact, decision_qualification_receipt) -> dict:
    probe = _normalize_probe(probe_result)
    if probe is None:
        return _ne("PROBE_RESULT_NOT_AUTHENTICATED")
    probe_status, binding, deltas = probe
    if probe_status == "NOT_ESTIMABLE":
        return _ne("PROBE_NOT_ESTIMABLE", binding)
    if not _qualification_valid(decision_qualification_receipt):
        return _ne("DECISION_QUALIFICATION_RECEIPT_NOT_AUTHENTICATED", binding)
    margins = _reference(reference_artifact, {d for d, _ in deltas}, binding)
    if margins is None:
        return _ne("REFERENCE_ARTIFACT_NOT_AUTHENTICATED", binding)
    if reference_artifact.get("margin_is_non_degenerate") is not True or not any(v > 0.0 for v in margins.values()):
        return _ne("NON_DEGENERATE_SUBSTANTIVE_MARGIN_REQUIRED", binding)

    donor_contrasts = [
        {
            "donor_id": donor,
            "raw_delta": raw,
            "substantive_margin": margins[donor],
            "margin_adjusted_delta": raw - margins[donor],
        }
        for donor, raw in deltas
    ]
    sign_test = P.sign_recurrence_gate(
        [{"donor_id": r["donor_id"], "delta": r["margin_adjusted_delta"]} for r in donor_contrasts],
        FAMILY_ALPHA,
    )
    if not sign_test["resolution_estimable"]:
        status, reason = "NOT_ESTIMABLE", "DONOR_SIGN_RESOLUTION_INSUFFICIENT"
    elif sign_test["pass"]:
        status, reason = "PASS", "TEACHER_ADVANTAGE_EXCEEDS_AUTHENTICATED_MARGIN"
    else:
        status, reason = "FAIL", "TEACHER_ADVANTAGE_NOT_ESTABLISHED_BEYOND_AUTHENTICATED_MARGIN"
    return {
        "schema": "JEPA_TD_REAL_G6_MARGIN_AWARE_DECISION_V3",
        "status": status,
        "reason": reason,
        "metric": METRIC,
        "orientation": ORIENTATION,
        "family_alpha": FAMILY_ALPHA,
        "input_binding_sha256": binding,
        "donor_contrasts": donor_contrasts,
        "sign_test": sign_test,
        "authority": dict(NO_AUTHORITY),
    }
