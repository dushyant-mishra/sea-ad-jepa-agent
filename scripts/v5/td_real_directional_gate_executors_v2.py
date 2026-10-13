"""Outcome-blind V2 real-TD directional/structural gate executors.

This module implements only PR #338 Scientific Amendment V2 Class-A rules.
Direction-only inference is explicitly forbidden for the blocked magnitude,
stability, increment, transfer, and coverage rules.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence

from scripts.v5 import td_real_quantitative_components_v1 as Q
from scripts.v5 import td_real_tournament_contract_v1 as C


class DirectionalGateError(ValueError):
    pass


CLAIM_BOUNDARY = "DIRECTIONAL_OR_STRUCTURAL_QUALIFICATION_ONLY__NO_BIOLOGICAL_MAGNITUDE_CLAIM"
NO_AUTHORITY = {
    "real_tournament_authorized": False,
    "target_selection_authorized": False,
    "representation_selection_authorized": False,
    "td60_authorized": False,
    "production_ema_selection_authorized": False,
    "stage4_authorized": False,
    "training_authorized": False,
}

CLEARED_V2_GATES = frozenset({
    "G3_CORRECT_CELL_SPECIFICITY",
    "G4_DONOR_RECURRENCE",
    "G5_SOURCE_REPLICATION",
    "G10_COLLAPSE_SHORTCUT_RESISTANCE",
    "S3_IDENTITY_SUPPORT_BASELINE_DEFEAT",
    "R3_FINE_NEIGHBOR_WRONG_CELL_DEFEAT",
    "Q4_Q_COUNT_ONLY_DEFEAT",
    "Q5_Q_ADDRESS_ONLY_DEFEAT",
    "Q6_QUERY_AGNOSTIC_DEFEAT",
    "Q7_WRONG_Q_DEFEAT",
    "Q8_TECHNICAL_PLUS_Q_DEFEAT",
    "M1_CIRCULARITY_CONTROL",
    "M2_INDEPENDENT_PROVENANCE",
    "M3_CAUSAL_CLAIM_FALSE",
    "M4_SUPPORT_ABSTENTION",
})

BLOCKED_V2_GATES = frozenset({
    "G2_NONTRIVIAL_BIOLOGICAL_CONTENT",
    "G6_TEACHER_INFORMATION_ADVANTAGE",
    "G7_EVIDENCE_CONVERGENCE",
    "G8_MEASUREMENT_ROBUSTNESS",
    "G9_LEARNED_TEACHER_CONTINUITY",
    "G11_TRANSFER",
    "G12_COVERAGE_ABSTENTION",
    "S1_DISJOINT_VIEW_RECURRENCE",
    "S2_DONOR_BALANCED_SUBSPACE_STABILITY",
    "R1_SCALE_FREE_RELATIONAL_RECURRENCE",
    "R4_INCREMENT_OVER_C1_SHARED",
    "C6_INCREMENT_OVER_C1_C3",
    "C4_INCREMENT_OVER_CONSTITUENTS",
})

_SINGLE_DIRECTIONAL = frozenset({
    "G4_DONOR_RECURRENCE",
    "S3_IDENTITY_SUPPORT_BASELINE_DEFEAT",
    "R3_FINE_NEIGHBOR_WRONG_CELL_DEFEAT",
    "Q4_Q_COUNT_ONLY_DEFEAT",
    "Q5_Q_ADDRESS_ONLY_DEFEAT",
    "Q6_QUERY_AGNOSTIC_DEFEAT",
    "Q7_WRONG_Q_DEFEAT",
    "Q8_TECHNICAL_PLUS_Q_DEFEAT",
})
_REQUIRED_SOURCES = ("HVS", "NPH52", "SEA_AD")


def _result(status: str, **payload) -> dict:
    return {
        "status": status,
        **payload,
        "claim_boundary": CLAIM_BOUNDARY,
        "authority": dict(NO_AUTHORITY),
    }


def _directional(deltas, *, alpha_eff: float) -> dict:
    out = Q.directional_donor_contrast(deltas, alpha_eff=alpha_eff)
    return {
        "status": out["status"],
        "raw_sufficient_statistics": out["raw_sufficient_statistics"],
    }


def _candidate_registry() -> dict:
    contract = C.load_real_tournament_contract()
    return C.validate_candidate_registry(contract)


def _required_wrong_cell_subtests(candidate_id: str) -> tuple[str, ...]:
    registry = _candidate_registry()
    if candidate_id not in registry:
        raise DirectionalGateError(f"unknown candidate_id: {candidate_id}")
    required = ["matched_wrong_cell"]
    if registry[candidate_id].get("relational_dependent") is True:
        required.append("fine_neighborhood_wrong_cell")
    return tuple(required)


def _aggregate_subtests(required: Sequence[str], supplied: Mapping, *, alpha_family: float) -> dict:
    if not isinstance(supplied, Mapping):
        raise DirectionalGateError("subtests must be a mapping")
    extra = set(supplied) - set(required)
    if extra:
        raise DirectionalGateError(f"unexpected subtests: {sorted(extra)}")
    alpha_eff = alpha_family / len(required)
    results = {}
    statuses = []
    for name in required:
        if name not in supplied:
            results[name] = {"status": "NOT_ESTIMABLE"}
            statuses.append("NOT_ESTIMABLE")
            continue
        results[name] = _directional(supplied[name], alpha_eff=alpha_eff)
        statuses.append(results[name]["status"])
    return {
        "status": Q.noncompensating_status(statuses),
        "subtests": results,
        "alpha_family": alpha_family,
        "alpha_eff": alpha_eff,
    }


def _evaluate_g3(evidence: Mapping, *, alpha_family: float) -> dict:
    candidate_id = evidence.get("candidate_id")
    if not isinstance(candidate_id, str):
        return _result("NOT_ESTIMABLE")
    required = _required_wrong_cell_subtests(candidate_id)
    supplied = evidence.get("subtests", {})
    agg = _aggregate_subtests(required, supplied, alpha_family=alpha_family)
    return _result(agg.pop("status"), candidate_id=candidate_id, required_subtests=list(required), **agg)


def _evaluate_g5(evidence: Mapping, *, alpha_family: float) -> dict:
    supplied = evidence.get("source_donor_deltas")
    if not isinstance(supplied, Mapping):
        return _result("NOT_ESTIMABLE", strata={})
    extra = set(supplied) - set(_REQUIRED_SOURCES)
    if extra:
        raise DirectionalGateError(f"unexpected source strata: {sorted(extra)}")
    alpha_eff = alpha_family / len(_REQUIRED_SOURCES)
    strata = {}
    statuses = []
    for source in _REQUIRED_SOURCES:
        if source not in supplied:
            strata[source] = {"status": "NOT_ESTIMABLE"}
            statuses.append("NOT_ESTIMABLE")
            continue
        strata[source] = _directional(supplied[source], alpha_eff=alpha_eff)
        statuses.append(strata[source]["status"])
    return _result(
        Q.noncompensating_status(statuses),
        strata=strata,
        required_sources=list(_REQUIRED_SOURCES),
        alpha_family=alpha_family,
        alpha_eff=alpha_eff,
    )


def _evaluate_g10(evidence: Mapping, *, alpha_family: float) -> dict:
    candidate_id = evidence.get("candidate_id")
    if not isinstance(candidate_id, str):
        return _result("NOT_ESTIMABLE", subtests={})
    registry = _candidate_registry()
    if candidate_id not in registry:
        raise DirectionalGateError(f"unknown candidate_id: {candidate_id}")
    required = tuple(registry[candidate_id]["mandatory_falsifiers"])
    supplied = evidence.get("falsifier_donor_deltas", {})
    if not isinstance(supplied, Mapping):
        return _result("NOT_ESTIMABLE", subtests={})
    extra = set(supplied) - set(required)
    if extra:
        raise DirectionalGateError(f"unexpected mandatory-falsifier evidence: {sorted(extra)}")
    agg = _aggregate_subtests(required, supplied, alpha_family=alpha_family)
    return _result(
        agg.pop("status"),
        candidate_id=candidate_id,
        required_falsifiers=list(required),
        **agg,
    )


def _string_set(value, field: str) -> set[str]:
    if not isinstance(value, (list, tuple, set)) or not value:
        raise DirectionalGateError(f"{field} must be a nonempty sequence of strings")
    if any(not isinstance(item, str) or not item for item in value):
        raise DirectionalGateError(f"{field} must contain only nonempty strings")
    return set(value)


def _evaluate_m1(evidence: Mapping) -> dict:
    if "construction_evidence_ids" not in evidence or "deciding_evidence_ids" not in evidence:
        return _result("NOT_ESTIMABLE")
    construction = _string_set(evidence["construction_evidence_ids"], "construction_evidence_ids")
    deciding = _string_set(evidence["deciding_evidence_ids"], "deciding_evidence_ids")
    overlap = sorted(construction & deciding)
    return _result(
        "FAIL" if overlap else "PASS",
        raw_sufficient_statistics={
            "construction_evidence_count": len(construction),
            "deciding_evidence_count": len(deciding),
            "overlap_ids": overlap,
        },
    )


def _evaluate_m2(evidence: Mapping) -> dict:
    required = ("provenance_authenticated", "independent_of_target_selection")
    if any(field not in evidence for field in required):
        return _result("NOT_ESTIMABLE")
    values = {field: evidence[field] for field in required}
    if any(value not in (True, False) for value in values.values()):
        raise DirectionalGateError("M2 provenance predicates must be boolean")
    status = "PASS" if all(values.values()) else "FAIL"
    return _result(status, raw_sufficient_statistics=values)


def _evaluate_m3(evidence: Mapping) -> dict:
    if "causal_claim_asserted" not in evidence:
        return _result("NOT_ESTIMABLE")
    value = evidence["causal_claim_asserted"]
    if value is False:
        return _result("PASS", raw_sufficient_statistics={"causal_claim_asserted": False})
    if value is True:
        return _result("FAIL", raw_sufficient_statistics={"causal_claim_asserted": True})
    raise DirectionalGateError("causal_claim_asserted must be boolean")


def _evaluate_m4(evidence: Mapping) -> dict:
    fields = (
        "unsupported_converted_to_numeric",
        "missing_evidence_treated_as_zero",
        "imputation_used",
    )
    if any(field not in evidence for field in fields):
        return _result("NOT_ESTIMABLE")
    values = {field: evidence[field] for field in fields}
    if any(value not in (True, False) for value in values.values()):
        raise DirectionalGateError("M4 support/abstention predicates must be boolean")
    status = "FAIL" if any(values.values()) else "PASS"
    return _result(status, raw_sufficient_statistics=values)


def evaluate_directional_gate(gate_id: str, evidence: Mapping, *, alpha_family: float = 0.01) -> dict:
    if gate_id in BLOCKED_V2_GATES:
        raise DirectionalGateError(f"blocked prospective rule has no direction-only fallback: {gate_id}")
    if gate_id not in CLEARED_V2_GATES:
        raise DirectionalGateError(f"unknown or unauthorized V2 gate: {gate_id}")
    if not isinstance(evidence, Mapping):
        raise DirectionalGateError("evidence must be a mapping")
    if not isinstance(alpha_family, (int, float)) or not (0.0 < float(alpha_family) < 1.0):
        raise DirectionalGateError("alpha_family must lie in (0,1)")
    alpha_family = float(alpha_family)

    if gate_id == "G3_CORRECT_CELL_SPECIFICITY":
        return _evaluate_g3(evidence, alpha_family=alpha_family)
    if gate_id == "G5_SOURCE_REPLICATION":
        return _evaluate_g5(evidence, alpha_family=alpha_family)
    if gate_id == "G10_COLLAPSE_SHORTCUT_RESISTANCE":
        return _evaluate_g10(evidence, alpha_family=alpha_family)
    if gate_id == "M1_CIRCULARITY_CONTROL":
        return _evaluate_m1(evidence)
    if gate_id == "M2_INDEPENDENT_PROVENANCE":
        return _evaluate_m2(evidence)
    if gate_id == "M3_CAUSAL_CLAIM_FALSE":
        return _evaluate_m3(evidence)
    if gate_id == "M4_SUPPORT_ABSTENTION":
        return _evaluate_m4(evidence)
    if gate_id in _SINGLE_DIRECTIONAL:
        if "donor_deltas" not in evidence:
            return _result("NOT_ESTIMABLE")
        out = _directional(evidence["donor_deltas"], alpha_eff=alpha_family)
        return _result(out["status"], raw_sufficient_statistics=out["raw_sufficient_statistics"], alpha_eff=alpha_family)

    raise DirectionalGateError(f"cleared gate implementation pending TDD cycle: {gate_id}")
