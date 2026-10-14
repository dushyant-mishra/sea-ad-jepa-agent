"""Outcome-blind support-aware terminal decision contract for real-TD G7.

This module adjudicates only a prospectively supplied penultimate->full evidence
convergence summary against a separately qualified same-metric reference margin.
It does not construct biological evidence, read human candidate outcomes, or
authorize real TD.
"""
from __future__ import annotations

import math
import re
from collections.abc import Mapping, Sequence

from scripts.v5 import td_target_tournament_precision as P


class G7DecisionError(ValueError):
    pass


QUAL_SCHEMA = "JEPA_TD_REAL_G7_TERMINAL_DECISION_QUALIFICATION_V2"
QUAL_PASS = "PASS_KNOWN_TRUTH_G7_TERMINAL_DECISION"
REFERENCE_SCHEMA = "JEPA_TD_REAL_G7_TERMINAL_REFERENCE_MARGIN_V1"
METRIC = "TERMINAL_PENULTIMATE_TO_FULL_DISPLACEMENT"
ORIENTATION = "SMALLER_IS_MORE_CONVERGED"
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
        raise G7DecisionError(f"{label} must be finite numeric")
    out = float(value)
    if not math.isfinite(out):
        raise G7DecisionError(f"{label} must be finite numeric")
    if nonnegative and out < 0:
        raise G7DecisionError(f"{label} must be nonnegative")
    return out


def _token(value, label: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip() or "\0" in value:
        raise G7DecisionError(f"{label} must be a nonempty trimmed string")
    return value


def _qualification_valid(value) -> bool:
    return bool(
        isinstance(value, Mapping)
        and value.get("schema") == QUAL_SCHEMA
        and value.get("status") == QUAL_PASS
        and value.get("known_truth_power_qualified") is True
    )


def _normalize_rows(rows) -> list[dict]:
    fields = {
        "donor_id", "terminal_displacement", "penultimate_supported_evidence",
        "full_supported_evidence", "added_supported_evidence",
    }
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise G7DecisionError("rows must be a sequence")
    out: list[dict] = []
    seen: set[str] = set()
    for i, raw in enumerate(rows):
        if not isinstance(raw, Mapping) or set(raw) != fields:
            raise G7DecisionError(f"rows[{i}] fields differ from frozen schema")
        donor = _token(raw["donor_id"], "donor_id")
        if donor in seen:
            raise G7DecisionError(f"duplicate donor_id: {donor}")
        seen.add(donor)
        displacement = _number(raw["terminal_displacement"], "terminal_displacement", nonnegative=True)
        pen = raw["penultimate_supported_evidence"]
        full = raw["full_supported_evidence"]
        added = raw["added_supported_evidence"]
        for label, value in (("penultimate support", pen), ("full support", full), ("added support", added)):
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise G7DecisionError(f"{label} must be a nonnegative integer")
        if full < pen:
            raise G7DecisionError("full support cannot be lower than penultimate support")
        if added != full - pen:
            raise G7DecisionError("added support must equal full support minus penultimate support")
        out.append({
            "donor_id": donor,
            "terminal_displacement": displacement,
            "penultimate_supported_evidence": pen,
            "full_supported_evidence": full,
            "added_supported_evidence": added,
        })
    return out


def _reference(reference, donors: set[str]) -> dict[str, float]:
    required = {
        "schema", "frozen", "qualified", "metric", "orientation", "reference_kind",
        "deciding_namespace_disjoint", "input_binding_sha256", "reference_receipt_sha256",
        "donor_margins",
    }
    if not isinstance(reference, Mapping) or set(reference) != required:
        raise G7DecisionError("a frozen qualified reference artifact with exact fields is required")
    if reference["schema"] != REFERENCE_SCHEMA:
        raise G7DecisionError("reference schema mismatch")
    if reference["frozen"] is not True or reference["qualified"] is not True:
        raise G7DecisionError("reference artifact must be frozen and qualified")
    if reference["metric"] != METRIC:
        raise G7DecisionError("reference metric is not commensurate with G7 terminal displacement")
    if reference["orientation"] != ORIENTATION:
        raise G7DecisionError("reference orientation mismatch")
    if reference["reference_kind"] not in REFERENCE_KINDS:
        raise G7DecisionError("reference_kind is not allowed")
    if reference["deciding_namespace_disjoint"] is not True:
        raise G7DecisionError("reference and deciding namespaces must be disjoint")
    for key in ("input_binding_sha256", "reference_receipt_sha256"):
        if not isinstance(reference[key], str) or not HEX64.fullmatch(reference[key]):
            raise G7DecisionError(f"{key} must be lowercase 64-hex")
    margins = reference["donor_margins"]
    if not isinstance(margins, Mapping):
        raise G7DecisionError("reference donor_margins must be a mapping")
    normalized = {_token(k, "reference donor_id"): _number(v, f"reference margin {k}", nonnegative=True) for k, v in margins.items()}
    if set(normalized) != donors:
        raise G7DecisionError("reference donor roster must match deciding donor roster exactly")
    return normalized


def adjudicate_g7_terminal(*, rows, decision_qualification, reference_artifact, alpha: float = 0.01) -> dict:
    alpha_value = _number(alpha, "alpha")
    if not 0 < alpha_value < 1:
        raise G7DecisionError("alpha must lie in (0,1)")
    normalized = _normalize_rows(rows)
    if not _qualification_valid(decision_qualification):
        return {
            "schema": "JEPA_TD_REAL_G7_TERMINAL_DECISION_V2", "status": "NOT_ESTIMABLE",
            "reason": "DECISION_KNOWN_TRUTH_NOT_QUALIFIED", "donor_contrasts": [],
            "sign_test": None, "authority": dict(NO_AUTHORITY),
        }
    donors = {r["donor_id"] for r in normalized}
    margins = _reference(reference_artifact, donors)
    supported = [r for r in normalized if r["added_supported_evidence"] > 0]
    if not supported:
        return {
            "schema": "JEPA_TD_REAL_G7_TERMINAL_DECISION_V2", "status": "NOT_ESTIMABLE",
            "reason": "NO_DONORS_WITH_ADDED_SUPPORTED_EVIDENCE", "donor_contrasts": [],
            "sign_test": None, "authority": dict(NO_AUTHORITY),
        }
    # Positive contrast means observed terminal change is within the independently
    # qualified variability envelope: margin - displacement > 0.
    donor_contrasts = [{
        "donor_id": r["donor_id"],
        "terminal_displacement": r["terminal_displacement"],
        "substantive_margin": margins[r["donor_id"]],
        "margin_adjusted_convergence": margins[r["donor_id"]] - r["terminal_displacement"],
        "added_supported_evidence": r["added_supported_evidence"],
    } for r in supported]
    sign_input = [{"donor_id": r["donor_id"], "delta": r["margin_adjusted_convergence"]} for r in donor_contrasts]
    sign = P.sign_recurrence_gate(sign_input, alpha_value)
    if not sign["resolution_estimable"]:
        status, reason = "NOT_ESTIMABLE", "DONOR_SIGN_RESOLUTION_INSUFFICIENT"
    elif sign["pass"]:
        status, reason = "PASS", "TERMINAL_CHANGE_WITHIN_QUALIFIED_MARGIN"
    else:
        status, reason = "FAIL", "TERMINAL_CHANGE_EXCEEDS_QUALIFIED_MARGIN"
    return {
        "schema": "JEPA_TD_REAL_G7_TERMINAL_DECISION_V2",
        "status": status, "reason": reason, "metric": METRIC, "orientation": ORIENTATION,
        "reference_kind": reference_artifact["reference_kind"],
        "donor_contrasts": donor_contrasts, "sign_test": sign,
        "claim_boundary": "TERMINAL_EVIDENCE_CONVERGENCE_ONLY__NO_ADJACENT_MONOTONICITY__NO_DEPTH_SUBSTITUTION",
        "authority": dict(NO_AUTHORITY),
    }


def _qual(ok=True):
    return {"schema": QUAL_SCHEMA, "status": QUAL_PASS, "known_truth_power_qualified": ok}


def _ref(donors, margin=0.1):
    return {
        "schema": REFERENCE_SCHEMA, "frozen": True, "qualified": True, "metric": METRIC,
        "orientation": ORIENTATION, "reference_kind": "U_REFIT", "deciding_namespace_disjoint": True,
        "input_binding_sha256": "1" * 64, "reference_receipt_sha256": "2" * 64,
        "donor_margins": {d: margin for d in donors},
    }


def _rows(n=8, displacement=0.02, added=1):
    return [{
        "donor_id": f"D{i}", "terminal_displacement": displacement,
        "penultimate_supported_evidence": 10, "full_supported_evidence": 10 + added,
        "added_supported_evidence": added,
    } for i in range(n)]


def qualify_known_truth_g7_decision() -> dict:
    worlds: dict[str, str] = {}
    for name, rows in (
        ("CONVERGED", _rows(8, 0.02, 1)),
        ("NONCONVERGED", _rows(8, 0.5, 1)),
        ("NO_ADDED_SUPPORT", _rows(8, 0.0, 0)),
        ("UNDERPOWERED", _rows(7, 0.02, 1)),
    ):
        donors = [r["donor_id"] for r in rows]
        worlds[name] = adjudicate_g7_terminal(rows=rows, decision_qualification=_qual(), reference_artifact=_ref(donors))["status"]
    passed = worlds == {
        "CONVERGED": "PASS", "NONCONVERGED": "FAIL",
        "NO_ADDED_SUPPORT": "NOT_ESTIMABLE", "UNDERPOWERED": "NOT_ESTIMABLE",
    }
    return {
        "schema": QUAL_SCHEMA, "status": QUAL_PASS if passed else "FAIL_KNOWN_TRUTH_G7_TERMINAL_DECISION",
        "known_truth_power_qualified": bool(passed), "worlds": worlds,
        "authority": dict(NO_AUTHORITY),
    }
