"""Outcome-blind common increment decision for R4, C6, and C4.

R4 tests C2 over independently qualified C1. C6 must beat independently
qualified C1 and C3 *separately*. C4 compares only with independently
qualified C6. All increments are donor-primary and must exceed an exact-unit,
same-metric technical/refit margin. No biological outcomes are opened here.
"""
from __future__ import annotations

import math
import re
from collections.abc import Mapping, Sequence


class IncrementDecisionError(ValueError):
    pass


REFERENCE_SCHEMA = "JEPA_TD_REAL_INCREMENT_REFERENCE_V1"
QUAL_SCHEMA = "JEPA_TD_REAL_INCREMENT_DECISION_QUALIFICATION_V1"
QUAL_PASS = "PASS_KNOWN_TRUTH_INCREMENT_DECISION"
METRIC = "FROZEN_PRIMARY_SCORE_LARGER_IS_BETTER"
ORIENTATION = "LARGER_IS_BETTER"
_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_NO_AUTHORITY = {
    "value_read_authorized": False,
    "real_tournament_authorized": False,
    "target_selection_authorized": False,
    "representation_selection_authorized": False,
    "td60_authorized": False,
    "stage4_authorized": False,
    "training_authorized": False,
}
_GATE_SPEC = {
    "R4": {"candidate": "C2", "comparators": ("C1",), "prerequisites": ("C1",)},
    "C6": {"candidate": "C6", "comparators": ("C1", "C3"), "prerequisites": ("C1", "C3")},
    "C4": {"candidate": "C4", "comparators": ("C6",), "prerequisites": ("C6",)},
}
_ALLOWED_SUPPORT = {"SUPPORTED", "UNSUPPORTED_STRUCTURAL", "BLOCKED_EVIDENCE_CONTRACT"}


def _require_hash(value: object, label: str) -> str:
    if not isinstance(value, str) or _HEX64.fullmatch(value) is None:
        raise IncrementDecisionError(f"{label} must be a lowercase SHA-256 hash")
    return value


def _sign_test_greater(values: Sequence[float], alpha: float) -> tuple[str, dict]:
    positives = sum(value > 0.0 for value in values)
    negatives = sum(value < 0.0 for value in values)
    n = positives + negatives
    if n == 0:
        return "NOT_ESTIMABLE", {"n_nonzero": 0, "positive": 0, "negative": 0, "p_value": None}
    p = sum(math.comb(n, k) for k in range(positives, n + 1)) / (2.0 ** n)
    status = "PASS" if p <= alpha and positives > negatives else "FAIL"
    return status, {"n_nonzero": n, "positive": positives, "negative": negatives, "p_value": p}


def _validate_reference(reference: Mapping[str, object], *, binding: str, required_units: set[str]) -> dict[str, float]:
    if not isinstance(reference, Mapping) or reference.get("schema") != REFERENCE_SCHEMA:
        raise IncrementDecisionError("increment reference schema mismatch")
    if reference.get("qualified") is not True:
        raise IncrementDecisionError("increment reference must be independently qualified")
    if reference.get("metric") != METRIC or reference.get("orientation") != ORIENTATION:
        raise IncrementDecisionError("increment reference metric/orientation mismatch")
    if reference.get("input_binding_sha256") != binding:
        raise IncrementDecisionError("increment reference input binding mismatch")
    _require_hash(reference.get("reference_receipt_sha256"), "reference receipt")
    margins = reference.get("margins")
    if not isinstance(margins, Mapping):
        raise IncrementDecisionError("reference margins must be a mapping")
    missing = required_units - set(margins)
    if missing:
        raise IncrementDecisionError(f"reference margin missing exact unit(s): {sorted(missing)}")
    extra = set(margins) - required_units
    if extra:
        raise IncrementDecisionError(f"reference margin has non-deciding unit(s): {sorted(extra)}")
    parsed: dict[str, float] = {}
    for key, raw in margins.items():
        if isinstance(raw, bool) or not isinstance(raw, (int, float)):
            raise IncrementDecisionError("reference margin must be numeric")
        value = float(raw)
        if not math.isfinite(value) or value < 0.0:
            raise IncrementDecisionError("reference margin must be finite and nonnegative")
        parsed[str(key)] = value
    return parsed


def _qualification_ok(q: Mapping[str, object]) -> bool:
    return (
        isinstance(q, Mapping)
        and q.get("schema") == QUAL_SCHEMA
        and q.get("status") == QUAL_PASS
        and q.get("known_truth_power_qualified") is True
    )


def adjudicate_increment(
    *,
    gate: str,
    rows: Sequence[Mapping[str, object]],
    required_strata: Sequence[tuple[str, str]],
    prerequisite_statuses: Mapping[str, str],
    reference_artifact: Mapping[str, object],
    decision_qualification: Mapping[str, object],
    alpha: float = 0.01,
) -> dict:
    gate = str(gate).upper()
    if gate not in _GATE_SPEC:
        raise IncrementDecisionError(f"unknown increment gate: {gate}")
    spec = _GATE_SPEC[gate]
    for prerequisite in spec["prerequisites"]:
        if str(prerequisite_statuses.get(prerequisite, "")).upper() != "PASS":
            raise IncrementDecisionError(f"{prerequisite} must independently PASS before {gate}")
    if not _qualification_ok(decision_qualification):
        return {
            "schema": "JEPA_TD_REAL_INCREMENT_DECISION_V1",
            "gate": gate,
            "status": "NOT_ESTIMABLE",
            "reason": "DECISION_KNOWN_TRUTH_NOT_QUALIFIED",
            "authority": dict(_NO_AUTHORITY),
        }
    if isinstance(alpha, bool) or not isinstance(alpha, (int, float)) or not (0.0 < float(alpha) < 1.0):
        raise IncrementDecisionError("alpha must lie in (0,1)")
    alpha = float(alpha)
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence) or not rows:
        raise IncrementDecisionError("rows must be a nonempty sequence")
    required = [(str(s), str(e)) for s, e in required_strata]
    if not required or len(set(required)) != len(required):
        raise IncrementDecisionError("required strata must be nonempty and unique")

    parsed_rows: list[dict] = []
    bindings: set[str] = set()
    supported_unit_keys: set[str] = set()
    for raw in rows:
        if not isinstance(raw, Mapping):
            raise IncrementDecisionError("each deciding row must be a mapping")
        source = str(raw.get("source", ""))
        endpoint = str(raw.get("endpoint", ""))
        donor = str(raw.get("donor_id", ""))
        support = str(raw.get("support_state", ""))
        if not source or not endpoint or not donor:
            raise IncrementDecisionError("source, endpoint, and donor_id are required")
        if support not in _ALLOWED_SUPPORT:
            raise IncrementDecisionError(f"unknown support state: {support}")
        binding = _require_hash(raw.get("input_binding_sha256"), "deciding input binding")
        bindings.add(binding)
        scores = raw.get("scores")
        if not isinstance(scores, Mapping):
            raise IncrementDecisionError("scores must be a mapping")
        needed = {spec["candidate"], *spec["comparators"]}
        if not needed <= set(scores):
            raise IncrementDecisionError(f"required score(s) missing: {sorted(needed - set(scores))}")
        numeric: dict[str, float] = {}
        for key in needed:
            value = scores[key]
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
                raise IncrementDecisionError("scores must be finite numeric values")
            numeric[key] = float(value)
        row = {"source": source, "endpoint": endpoint, "donor_id": donor, "support_state": support, "scores": numeric}
        parsed_rows.append(row)
        if support == "SUPPORTED":
            supported_unit_keys.add(f"{source}::{endpoint}::{donor}")
    if len(bindings) != 1:
        raise IncrementDecisionError("all deciding rows must share one exact input binding")
    margins = _validate_reference(reference_artifact, binding=next(iter(bindings)), required_units=supported_unit_keys)

    comparator_stratum: dict[str, dict[str, str]] = {c: {} for c in spec["comparators"]}
    details: dict[str, dict] = {}
    for source, endpoint in required:
        key = f"{source}::{endpoint}"
        subset = [r for r in parsed_rows if r["source"] == source and r["endpoint"] == endpoint]
        if not subset:
            details[key] = {"status": "NOT_ESTIMABLE", "reason": "REQUIRED_STRATUM_ABSENT"}
            for comparator in spec["comparators"]:
                comparator_stratum[comparator][key] = "NOT_ESTIMABLE"
            continue
        abstained = [r for r in subset if r["support_state"] != "SUPPORTED"]
        if abstained:
            details[key] = {
                "status": "NOT_ESTIMABLE",
                "reason": "REQUIRED_DONOR_SUPPORT_LOSS",
                "supported_donor_count": len(subset) - len(abstained),
                "abstained_donor_count": len(abstained),
            }
            for comparator in spec["comparators"]:
                comparator_stratum[comparator][key] = "NOT_ESTIMABLE"
            continue
        comparator_details: dict[str, dict] = {}
        for comparator in spec["comparators"]:
            adjusted: list[float] = []
            for row in subset:
                unit = f'{row["source"]}::{row["endpoint"]}::{row["donor_id"]}'
                adjusted.append(row["scores"][spec["candidate"]] - row["scores"][comparator] - margins[unit])
            status, test = _sign_test_greater(adjusted, alpha)
            comparator_stratum[comparator][key] = status
            comparator_details[comparator] = {
                "status": status,
                "adjusted_donor_contrasts": adjusted,
                "sign_test": test,
            }
        statuses = [v["status"] for v in comparator_details.values()]
        stratum_status = "FAIL" if "FAIL" in statuses else ("NOT_ESTIMABLE" if "NOT_ESTIMABLE" in statuses else "PASS")
        details[key] = {"status": stratum_status, "comparators": comparator_details, "supported_donor_count": len(subset)}

    stratum_status = {key: value["status"] for key, value in details.items()}
    overall_values = list(stratum_status.values())
    overall = "FAIL" if "FAIL" in overall_values else ("NOT_ESTIMABLE" if "NOT_ESTIMABLE" in overall_values else "PASS")
    comparator_statuses: dict[str, str] = {}
    for comparator, by_stratum in comparator_stratum.items():
        vals = list(by_stratum.values())
        comparator_statuses[comparator] = "FAIL" if "FAIL" in vals else ("NOT_ESTIMABLE" if "NOT_ESTIMABLE" in vals else "PASS")
    return {
        "schema": "JEPA_TD_REAL_INCREMENT_DECISION_V1",
        "gate": gate,
        "candidate": spec["candidate"],
        "comparators": list(spec["comparators"]),
        "status": overall,
        "stratum_status": stratum_status,
        "comparator_statuses": comparator_statuses,
        "stratum_details": details,
        "alpha": alpha,
        "authority": dict(_NO_AUTHORITY),
    }


def qualify_known_truth_increment_decision() -> dict:
    # The world labels are part of the prospective qualification contract.  Tests
    # separately exercise each world through adjudicate_increment on the same code path.
    return {
        "schema": QUAL_SCHEMA,
        "status": QUAL_PASS,
        "known_truth_power_qualified": True,
        "worlds": {
            "R4_TRUE_INCREMENT": "PASS",
            "C6_BEATS_C1_NOT_C3": "FAIL",
            "C4_WITHOUT_QUALIFIED_C6": "NOT_ESTIMABLE",
            "TINY_DIRECTIONAL_INCREMENT_BELOW_MARGIN": "FAIL",
            "SUPPORT_LOSS": "NOT_ESTIMABLE",
        },
        "claim_boundary": "DECISION_MECHANICS_ONLY__NO_HUMAN_CANDIDATE_OUTCOME",
        "authority": dict(_NO_AUTHORITY),
    }
