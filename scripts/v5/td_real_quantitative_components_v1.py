"""Reusable outcome-blind quantitative components for future real-TD gate rules.

These functions are statistical building blocks only. They do not define any
candidate-specific biological estimand, gate threshold, or execution authority.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence

import td_target_tournament_precision as P


class QuantitativeComponentError(ValueError):
    pass


CLAIM_BOUNDARY = "REUSABLE_STATISTICAL_COMPONENTS_ONLY__NOT_GATE_RULES__NO_REAL_TD_AUTHORITY"
NO_AUTHORITY = {
    "real_tournament_authorized": False,
    "target_selection_authorized": False,
    "representation_selection_authorized": False,
    "td60_authorized": False,
    "stage4_authorized": False,
    "training_authorized": False,
}
_ALLOWED = {"PASS", "FAIL", "NOT_ESTIMABLE"}


def directional_donor_contrast(donor_deltas, *, alpha_eff: float) -> dict:
    """Map the frozen donor-bound exact sign test to PASS/FAIL/NOT_ESTIMABLE.

    Positive delta orientation must be defined prospectively by the caller's
    gate-specific estimand. This helper never decides what delta means.
    """
    try:
        stats = P.sign_recurrence_gate(donor_deltas, alpha_eff)
    except (P.PrecisionContractError, ValueError) as exc:
        raise QuantitativeComponentError(str(exc)) from exc
    if not stats["resolution_estimable"]:
        status = "NOT_ESTIMABLE"
    elif stats["pass"]:
        status = "PASS"
    else:
        status = "FAIL"
    return {
        "status": status,
        "raw_sufficient_statistics": dict(stats),
        "claim_boundary": CLAIM_BOUNDARY,
        "authority": dict(NO_AUTHORITY),
    }


def noncompensating_status(statuses: Sequence[str]) -> str:
    if isinstance(statuses, (str, bytes)) or not isinstance(statuses, Sequence) or not statuses:
        raise QuantitativeComponentError("nonempty status sequence required")
    if any(status not in _ALLOWED for status in statuses):
        raise QuantitativeComponentError("statuses must be PASS/FAIL/NOT_ESTIMABLE")
    if "FAIL" in statuses:
        return "FAIL"
    if "NOT_ESTIMABLE" in statuses:
        return "NOT_ESTIMABLE"
    return "PASS"


def required_strata_status(strata: Mapping[str, str], *, required_strata: Sequence[str]) -> dict:
    if not isinstance(strata, Mapping):
        raise QuantitativeComponentError("strata must be a mapping")
    if isinstance(required_strata, (str, bytes)) or not isinstance(required_strata, Sequence) or not required_strata:
        raise QuantitativeComponentError("required_strata must be a nonempty sequence")
    if any(not isinstance(value, str) or not value for value in required_strata):
        raise QuantitativeComponentError("required_strata values must be nonempty strings")
    if len(set(required_strata)) != len(required_strata):
        raise QuantitativeComponentError("required_strata must be unique")
    if set(strata) != set(required_strata):
        raise QuantitativeComponentError("strata must cover the exact frozen required stratum set")
    ordered = {name: strata[name] for name in required_strata}
    status = noncompensating_status(list(ordered.values()))
    return {
        "status": status,
        "strata": ordered,
        "claim_boundary": CLAIM_BOUNDARY,
        "authority": dict(NO_AUTHORITY),
    }
