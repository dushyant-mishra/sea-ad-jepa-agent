"""Outcome-blind V2 real-TD directional/structural gate executors.

This module implements only PR #338 Scientific Amendment V2 Class-A rules.
Direction-only inference is explicitly forbidden for the blocked magnitude,
stability, increment, transfer, and coverage rules.
"""
from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from pathlib import Path

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
    "G3_CORRECT_CELL_SPECIFICITY", "G4_DONOR_RECURRENCE", "G5_SOURCE_REPLICATION",
    "G10_COLLAPSE_SHORTCUT_RESISTANCE", "S3_IDENTITY_SUPPORT_BASELINE_DEFEAT",
    "R3_FINE_NEIGHBOR_WRONG_CELL_DEFEAT", "Q4_Q_COUNT_ONLY_DEFEAT",
    "Q5_Q_ADDRESS_ONLY_DEFEAT", "Q6_QUERY_AGNOSTIC_DEFEAT", "Q7_WRONG_Q_DEFEAT",
    "Q8_TECHNICAL_PLUS_Q_DEFEAT", "M1_CIRCULARITY_CONTROL", "M2_INDEPENDENT_PROVENANCE",
    "M3_CAUSAL_CLAIM_FALSE", "M4_SUPPORT_ABSTENTION",
})

BLOCKED_V2_GATES = frozenset({
    "G2_NONTRIVIAL_BIOLOGICAL_CONTENT", "G6_TEACHER_INFORMATION_ADVANTAGE",
    "G7_EVIDENCE_CONVERGENCE", "G8_MEASUREMENT_ROBUSTNESS", "G9_LEARNED_TEACHER_CONTINUITY",
    "G11_TRANSFER", "G12_COVERAGE_ABSTENTION", "S1_DISJOINT_VIEW_RECURRENCE",
    "S2_DONOR_BALANCED_SUBSPACE_STABILITY", "R1_SCALE_FREE_RELATIONAL_RECURRENCE",
    "R4_INCREMENT_OVER_C1_SHARED", "C6_INCREMENT_OVER_C1_C3", "C4_INCREMENT_OVER_CONSTITUENTS",
})

_SINGLE_DIRECTIONAL = frozenset({
    "G4_DONOR_RECURRENCE", "S3_IDENTITY_SUPPORT_BASELINE_DEFEAT",
    "R3_FINE_NEIGHBOR_WRONG_CELL_DEFEAT", "Q4_Q_COUNT_ONLY_DEFEAT",
    "Q5_Q_ADDRESS_ONLY_DEFEAT", "Q6_QUERY_AGNOSTIC_DEFEAT", "Q7_WRONG_Q_DEFEAT",
    "Q8_TECHNICAL_PLUS_Q_DEFEAT",
})
_REQUIRED_SOURCES = ("HVS", "NPH52", "SEA_AD")
_QUALIFICATION_FIELDS = {
    "schema", "status", "executor_sha256", "quantitative_components_sha256",
    "tournament_contract_sha256", "executor_bundle_sha256", "candidate_outcomes_opened",
    "real_tournament_authorized",
}

_RULE_SPECS = {
    "G3_CORRECT_CELL_SPECIFICITY": (
        "donor-primary correct-cell predictive advantage over matched wrong-cell B3 and relational B4 where applicable",
        "required B3 and applicable B4 donor sign subtests combine noncompensatingly; missing required legal comparator is NOT_ESTIMABLE",
    ),
    "G4_DONOR_RECURRENCE": (
        "predeclared candidate-primary donor predictive-information delta",
        "exact donor sign recurrence; direction only; insufficient exact resolution is NOT_ESTIMABLE",
    ),
    "G5_SOURCE_REPLICATION": (
        "candidate-primary donor delta separately within HVS, NPH52, and SEA_AD",
        "all three frozen source strata must independently pass; no pooling or compensation",
    ),
    "G10_COLLAPSE_SHORTCUT_RESISTANCE": (
        "donor-primary defeat of every mandatory candidate-specific frozen falsifier",
        "exact frozen mandatory falsifier set; all required subtests pass noncompensatingly",
    ),
    "S3_IDENTITY_SUPPORT_BASELINE_DEFEAT": (
        "donor-primary improvement over identity_support_only baseline",
        "exact donor sign baseline-defeat test only; does not establish shared-state magnitude",
    ),
    "R3_FINE_NEIGHBOR_WRONG_CELL_DEFEAT": (
        "donor-primary fine-neighborhood wrong-cell loss minus relational student loss",
        "exact donor sign falsifier defeat; unavailable lawful comparator is NOT_ESTIMABLE",
    ),
    "Q4_Q_COUNT_ONLY_DEFEAT": ("donor-primary query-target improvement over q_count_only", "exact donor sign falsifier defeat"),
    "Q5_Q_ADDRESS_ONLY_DEFEAT": ("donor-primary query-target improvement over q_address_only", "exact donor sign falsifier defeat"),
    "Q6_QUERY_AGNOSTIC_DEFEAT": ("donor-primary query-target improvement over query_agnostic", "exact donor sign falsifier defeat"),
    "Q7_WRONG_Q_DEFEAT": ("donor-primary query-target improvement over lawful wrong_q comparator", "exact donor sign falsifier defeat; unavailable lawful wrong-q is NOT_ESTIMABLE"),
    "Q8_TECHNICAL_PLUS_Q_DEFEAT": ("donor-primary query-target improvement over technical_plus_q", "exact donor sign falsifier defeat"),
    "M1_CIRCULARITY_CONTROL": (
        "construction evidence identity is disjoint from deciding evidence identity",
        "PASS iff both nonempty evidence-ID sets are disjoint; overlap FAIL; missing identity evidence NOT_ESTIMABLE",
    ),
    "M2_INDEPENDENT_PROVENANCE": (
        "regulatory specialist evidence has authenticated provenance and is independent of target selection",
        "PASS iff both provenance predicates are explicitly true; false FAIL; missing predicate NOT_ESTIMABLE",
    ),
    "M3_CAUSAL_CLAIM_FALSE": (
        "regulatory specialist claim remains noncausal",
        "PASS iff causal_claim_asserted is explicitly false; true FAIL; missing NOT_ESTIMABLE",
    ),
    "M4_SUPPORT_ABSTENTION": (
        "missing or structurally unsupported regulatory evidence remains abstained rather than numeric/imputed",
        "PASS iff unsupported-to-numeric, missing-to-zero, and imputation flags are all false; any violation FAIL; missing predicate NOT_ESTIMABLE",
    ),
}


def canonical_sha256(value) -> str:
    try:
        raw = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise DirectionalGateError("value must be canonical-JSON serializable") from exc
    return hashlib.sha256(raw).hexdigest()


def _file_sha256(path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


RULES = {
    gate_id: {
        "estimand": _RULE_SPECS[gate_id][0],
        "decision_rule": _RULE_SPECS[gate_id][1],
        "estimand_sha256": canonical_sha256({"gate_id": gate_id, "estimand": _RULE_SPECS[gate_id][0]}),
        "decision_rule_sha256": canonical_sha256({"gate_id": gate_id, "decision_rule": _RULE_SPECS[gate_id][1]}),
    }
    for gate_id in sorted(CLEARED_V2_GATES)
}


def _result(status: str, **payload) -> dict:
    return {"status": status, **payload, "claim_boundary": CLAIM_BOUNDARY, "authority": dict(NO_AUTHORITY)}


def _directional(deltas, *, alpha_eff: float) -> dict:
    out = Q.directional_donor_contrast(deltas, alpha_eff=alpha_eff)
    return {"status": out["status"], "raw_sufficient_statistics": out["raw_sufficient_statistics"]}


def _candidate_registry() -> dict:
    return C.validate_candidate_registry(C.load_real_tournament_contract())


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
    results, statuses = {}, []
    for name in required:
        if name not in supplied:
            results[name] = {"status": "NOT_ESTIMABLE"}; statuses.append("NOT_ESTIMABLE"); continue
        results[name] = _directional(supplied[name], alpha_eff=alpha_eff); statuses.append(results[name]["status"])
    return {"status": Q.noncompensating_status(statuses), "subtests": results, "alpha_family": alpha_family, "alpha_eff": alpha_eff}


def _evaluate_g3(evidence: Mapping, *, alpha_family: float) -> dict:
    candidate_id = evidence.get("candidate_id")
    if not isinstance(candidate_id, str): return _result("NOT_ESTIMABLE")
    required = _required_wrong_cell_subtests(candidate_id)
    agg = _aggregate_subtests(required, evidence.get("subtests", {}), alpha_family=alpha_family)
    return _result(agg.pop("status"), candidate_id=candidate_id, required_subtests=list(required), **agg)


def _evaluate_g5(evidence: Mapping, *, alpha_family: float) -> dict:
    supplied = evidence.get("source_donor_deltas")
    if not isinstance(supplied, Mapping): return _result("NOT_ESTIMABLE", strata={})
    extra = set(supplied) - set(_REQUIRED_SOURCES)
    if extra: raise DirectionalGateError(f"unexpected source strata: {sorted(extra)}")
    alpha_eff = alpha_family / len(_REQUIRED_SOURCES); strata, statuses = {}, []
    for source in _REQUIRED_SOURCES:
        if source not in supplied: strata[source] = {"status": "NOT_ESTIMABLE"}; statuses.append("NOT_ESTIMABLE"); continue
        strata[source] = _directional(supplied[source], alpha_eff=alpha_eff); statuses.append(strata[source]["status"])
    return _result(Q.noncompensating_status(statuses), strata=strata, required_sources=list(_REQUIRED_SOURCES), alpha_family=alpha_family, alpha_eff=alpha_eff)


def _evaluate_g10(evidence: Mapping, *, alpha_family: float) -> dict:
    candidate_id = evidence.get("candidate_id")
    if not isinstance(candidate_id, str): return _result("NOT_ESTIMABLE", subtests={})
    registry = _candidate_registry()
    if candidate_id not in registry: raise DirectionalGateError(f"unknown candidate_id: {candidate_id}")
    required = tuple(registry[candidate_id]["mandatory_falsifiers"]); supplied = evidence.get("falsifier_donor_deltas", {})
    if not isinstance(supplied, Mapping): return _result("NOT_ESTIMABLE", subtests={})
    extra = set(supplied) - set(required)
    if extra: raise DirectionalGateError(f"unexpected mandatory-falsifier evidence: {sorted(extra)}")
    agg = _aggregate_subtests(required, supplied, alpha_family=alpha_family)
    return _result(agg.pop("status"), candidate_id=candidate_id, required_falsifiers=list(required), **agg)


def _string_set(value, field: str) -> set[str]:
    if not isinstance(value, (list, tuple, set)) or not value or any(not isinstance(item, str) or not item for item in value):
        raise DirectionalGateError(f"{field} must be a nonempty sequence of strings")
    return set(value)


def _evaluate_m1(evidence: Mapping) -> dict:
    if "construction_evidence_ids" not in evidence or "deciding_evidence_ids" not in evidence: return _result("NOT_ESTIMABLE")
    construction = _string_set(evidence["construction_evidence_ids"], "construction_evidence_ids")
    deciding = _string_set(evidence["deciding_evidence_ids"], "deciding_evidence_ids")
    overlap = sorted(construction & deciding)
    return _result("FAIL" if overlap else "PASS", raw_sufficient_statistics={"construction_evidence_count": len(construction), "deciding_evidence_count": len(deciding), "overlap_ids": overlap})


def _evaluate_m2(evidence: Mapping) -> dict:
    required = ("provenance_authenticated", "independent_of_target_selection")
    if any(field not in evidence for field in required): return _result("NOT_ESTIMABLE")
    values = {field: evidence[field] for field in required}
    if any(value not in (True, False) for value in values.values()): raise DirectionalGateError("M2 provenance predicates must be boolean")
    return _result("PASS" if all(values.values()) else "FAIL", raw_sufficient_statistics=values)


def _evaluate_m3(evidence: Mapping) -> dict:
    if "causal_claim_asserted" not in evidence: return _result("NOT_ESTIMABLE")
    value = evidence["causal_claim_asserted"]
    if value is False: return _result("PASS", raw_sufficient_statistics={"causal_claim_asserted": False})
    if value is True: return _result("FAIL", raw_sufficient_statistics={"causal_claim_asserted": True})
    raise DirectionalGateError("causal_claim_asserted must be boolean")


def _evaluate_m4(evidence: Mapping) -> dict:
    fields = ("unsupported_converted_to_numeric", "missing_evidence_treated_as_zero", "imputation_used")
    if any(field not in evidence for field in fields): return _result("NOT_ESTIMABLE")
    values = {field: evidence[field] for field in fields}
    if any(value not in (True, False) for value in values.values()): raise DirectionalGateError("M4 support/abstention predicates must be boolean")
    return _result("FAIL" if any(values.values()) else "PASS", raw_sufficient_statistics=values)


def evaluate_directional_gate(gate_id: str, evidence: Mapping, *, alpha_family: float = 0.01) -> dict:
    if gate_id in BLOCKED_V2_GATES: raise DirectionalGateError(f"blocked prospective rule has no direction-only fallback: {gate_id}")
    if gate_id not in CLEARED_V2_GATES: raise DirectionalGateError(f"unknown or unauthorized V2 gate: {gate_id}")
    if not isinstance(evidence, Mapping): raise DirectionalGateError("evidence must be a mapping")
    if not isinstance(alpha_family, (int, float)) or not (0.0 < float(alpha_family) < 1.0): raise DirectionalGateError("alpha_family must lie in (0,1)")
    alpha_family = float(alpha_family)
    if gate_id == "G3_CORRECT_CELL_SPECIFICITY": return _evaluate_g3(evidence, alpha_family=alpha_family)
    if gate_id == "G5_SOURCE_REPLICATION": return _evaluate_g5(evidence, alpha_family=alpha_family)
    if gate_id == "G10_COLLAPSE_SHORTCUT_RESISTANCE": return _evaluate_g10(evidence, alpha_family=alpha_family)
    if gate_id == "M1_CIRCULARITY_CONTROL": return _evaluate_m1(evidence)
    if gate_id == "M2_INDEPENDENT_PROVENANCE": return _evaluate_m2(evidence)
    if gate_id == "M3_CAUSAL_CLAIM_FALSE": return _evaluate_m3(evidence)
    if gate_id == "M4_SUPPORT_ABSTENTION": return _evaluate_m4(evidence)
    if gate_id in _SINGLE_DIRECTIONAL:
        if "donor_deltas" not in evidence: return _result("NOT_ESTIMABLE")
        out = _directional(evidence["donor_deltas"], alpha_eff=alpha_family)
        return _result(out["status"], raw_sufficient_statistics=out["raw_sufficient_statistics"], alpha_eff=alpha_family)
    raise DirectionalGateError(f"cleared gate implementation pending TDD cycle: {gate_id}")


def authenticate_qualification_receipt(receipt: Mapping) -> str:
    if not isinstance(receipt, Mapping) or set(receipt) != _QUALIFICATION_FIELDS:
        raise DirectionalGateError("exact V2 directional qualification receipt required")
    if receipt.get("schema") != "JEPA_TD_REAL_DIRECTIONAL_GATES_V2_QUALIFICATION" or receipt.get("status") != "PASS_OUTCOME_BLIND_DIRECTIONAL_STRUCTURAL_EXECUTOR_MECHANICS":
        raise DirectionalGateError("V2 directional qualification status/schema mismatch")
    if receipt.get("candidate_outcomes_opened") is not False or receipt.get("real_tournament_authorized") is not False:
        raise DirectionalGateError("V2 directional qualification may not open outcomes or authorize real tournament")
    executor_sha, quantitative_sha, contract_sha = _file_sha256(__file__), _file_sha256(Q.__file__), _file_sha256(C.__file__)
    if receipt.get("executor_sha256") != executor_sha: raise DirectionalGateError("executor SHA-256 mismatch")
    if receipt.get("quantitative_components_sha256") != quantitative_sha: raise DirectionalGateError("quantitative components SHA-256 mismatch")
    if receipt.get("tournament_contract_sha256") != contract_sha: raise DirectionalGateError("tournament contract SHA-256 mismatch")
    bundle = canonical_sha256({"executor_sha256": executor_sha, "quantitative_components_sha256": quantitative_sha, "tournament_contract_sha256": contract_sha})
    if receipt.get("executor_bundle_sha256") != bundle: raise DirectionalGateError("executor bundle SHA-256 mismatch")
    return bundle


def execute_directional_gate(gate_id: str, evidence: Mapping, *, qualification_receipt: Mapping, alpha_family: float = 0.01) -> dict:
    bundle = authenticate_qualification_receipt(qualification_receipt)
    if gate_id not in CLEARED_V2_GATES: raise DirectionalGateError(f"gate is not a V2-cleared executor: {gate_id}")
    raw = dict(evidence) if isinstance(evidence, Mapping) else evidence
    evaluated = evaluate_directional_gate(gate_id, evidence, alpha_family=alpha_family)
    rule = RULES[gate_id]
    return {
        "status": evaluated["status"],
        "qualified_gate_executor_sha256": bundle,
        "estimand_sha256": rule["estimand_sha256"],
        "decision_rule_sha256": rule["decision_rule_sha256"],
        "evidence_payload_sha256": canonical_sha256(raw),
        "raw_sufficient_statistics": raw,
        "claim_boundary": CLAIM_BOUNDARY,
        "authority": dict(NO_AUTHORITY),
    }
