"""Outcome-blind registry for real-TD gate decision rules.

Only structural/provenance rules that are already explicit in the frozen target-
tournament specification are callable here. Biological/quantitative gates stay
blocked until an endpoint-specific prospective estimand and decision rule are
materialized. This module opens no candidate outcomes and grants no authority.
"""
from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence

import td_query_information_guard as Q
import td_real_tournament_contract_v1 as C


class GateRuleError(ValueError):
    pass


CALLABLE_STRUCTURAL = {
    "G1_INTEGRITY_LINEAGE",
    "R2_LOCALITY_RULE_FROZEN_NO_FINE_MINING",
    "Q1_Q_SCALAR_STUDENT_ABSENT",
    "Q2_Q_EXCLUDED_TEACHER_PRIMARY_ANCHOR",
    "Q3_TARGET_NORMALIZATION_Q_SCALAR_FREE",
}

_QUERY_GUARD_REUSE = {
    "path": "scripts/v5/td_query_information_guard.py",
    "git_blob_sha": "3ca60c5f82b7b07f5f6123a52e7b50f9027a6ebe",
    "test_path": "tests/v5/test_td_query_information_guard.py",
    "test_git_blob_sha": "849cfd9b65fadd0c54dfb9f534bcdddc413b4c98",
    "status": "EXACT_COMPONENT_REUSED_WITH_GATE_WRAPPER",
}

_STRUCTURAL_SPECS = {
    "G1_INTEGRITY_LINEAGE": {
        "estimand": "complete prospective binding of code/population/split/support/operator/evidence-rights/null-seed/prefreeze identities with no post-outcome redesign or relabeling",
        "required_fields": [
            "required_identity_names", "bound_identity_sha256",
            "post_outcome_redesign", "post_outcome_relabeling",
        ],
        "decision_rule": "PASS iff required identity names are nonempty/unique, bound SHA-256 keys match them exactly with valid lowercase hashes, and redesign/relabeling are both false; missing fields are NOT_ESTIMABLE; contradiction is FAIL",
        "historical_reuse": {},
    },
    "R2_LOCALITY_RULE_FROZEN_NO_FINE_MINING": {
        "estimand": "locality rule was frozen prospectively and no fine-neighborhood mining was used",
        "required_fields": ["locality_rule_prefrozen", "fine_neighborhood_mining_used"],
        "decision_rule": "PASS iff locality_rule_prefrozen is true and fine_neighborhood_mining_used is false; missing fields are NOT_ESTIMABLE; contradiction is FAIL",
        "historical_reuse": {},
    },
    "Q1_Q_SCALAR_STUDENT_ABSENT": {
        "estimand": "q-conditioned student dependency graph contains no direct or transitive q-scalar/q-scalar-descendant path",
        "required_fields": ["dependency_graph", "dependency_roles"],
        "decision_rule": "PASS iff a student_sink exists and the qualified dependency-lineage guard accepts the exact graph/roles; missing graph/roles are NOT_ESTIMABLE; invalid graph or q-scalar leakage is FAIL",
        "historical_reuse": _QUERY_GUARD_REUSE,
    },
    "Q2_Q_EXCLUDED_TEACHER_PRIMARY_ANCHOR": {
        "estimand": "primary measured teacher anchor excludes q scalar",
        "required_fields": ["q_excluded_teacher_primary_anchor"],
        "decision_rule": "PASS iff q_excluded_teacher_primary_anchor is true; missing field is NOT_ESTIMABLE; false is FAIL",
        "historical_reuse": {},
    },
    "Q3_TARGET_NORMALIZATION_Q_SCALAR_FREE": {
        "estimand": "primary q-conditioned target-normalization dependency graph contains no direct or transitive q-scalar/q-scalar-descendant path",
        "required_fields": ["dependency_graph", "dependency_roles"],
        "decision_rule": "PASS iff a target_normalization_sink exists and the qualified dependency-lineage guard accepts the exact graph/roles; missing graph/roles are NOT_ESTIMABLE; invalid graph or q-scalar leakage is FAIL",
        "historical_reuse": _QUERY_GUARD_REUSE,
    },
}


def _sha(value) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _gate_universe() -> list[str]:
    contract = C.load_real_tournament_contract()
    registry = C.validate_candidate_registry(contract)
    return list(dict.fromkeys(
        gate_id
        for candidate_id in C.CANDIDATE_IDS
        for gate_id in registry[candidate_id]["required_gates"]
    ))


def _build_rules() -> dict[str, dict]:
    rules = {}
    for gate_id in _gate_universe():
        base = {
            "gate_id": gate_id,
            "primary_biological_unit": "donor",
            "source_semantics": "observation_operator_not_biological_replicate",
            "historical_reuse": {},
        }
        if gate_id in CALLABLE_STRUCTURAL:
            spec = _STRUCTURAL_SPECS[gate_id]
            base.update({
                "readiness": "CALLABLE_NEEDS_QUALIFICATION",
                "rule_kind": "STRUCTURAL_PROVENANCE",
                "estimand": spec["estimand"],
                "required_fields": list(spec["required_fields"]),
                "decision_rule": spec["decision_rule"],
                "threshold_source": "NO_NUMERIC_THRESHOLD__FROZEN_STRUCTURAL_RULE",
                "callable_implementation": "td_real_gate_rule_registry_v1.evaluate_structural_gate",
                "estimand_sha256": _sha({"gate_id": gate_id, "estimand": spec["estimand"]}),
                "decision_rule_sha256": _sha({
                    "gate_id": gate_id,
                    "required_fields": spec["required_fields"],
                    "decision_rule": spec["decision_rule"],
                    "historical_reuse": spec["historical_reuse"],
                }),
                "historical_reuse": dict(spec["historical_reuse"]),
            })
        else:
            base.update({
                "readiness": "RULE_NOT_MATERIALIZED",
                "rule_kind": "QUANTITATIVE_OR_UNDERDEFINED",
                "estimand": "",
                "required_fields": [],
                "decision_rule": "BLOCKED_PROSPECTIVE_RULE_REQUIRED",
                "threshold_source": "BLOCKED_PROSPECTIVE_RULE_REQUIRED",
                "callable_implementation": "",
                "estimand_sha256": "",
                "decision_rule_sha256": "",
            })
        rules[gate_id] = base
    return rules


RULES = _build_rules()


def _is_seq(value) -> bool:
    return isinstance(value, Sequence) and not isinstance(value, (str, bytes))


def _is_sha256(value) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(ch in "0123456789abcdef" for ch in value)


def _missing(evidence: Mapping, fields: Sequence[str]) -> bool:
    return any(field not in evidence for field in fields)


def _query_guard_status(evidence: Mapping, required_sink: str) -> str:
    graph = evidence["dependency_graph"]
    roles = evidence["dependency_roles"]
    if not isinstance(roles, Mapping) or required_sink not in set(roles.values()):
        return "FAIL"
    try:
        Q.assert_query_safe(graph, roles)
    except (Q.QueryLeakageError, Q.DependencyCycleError, Q.QueryContractError):
        return "FAIL"
    return "PASS"


def evaluate_structural_gate(gate_id: str, evidence: Mapping) -> str:
    if gate_id not in RULES:
        raise GateRuleError(f"unknown gate_id: {gate_id}")
    rule = RULES[gate_id]
    if rule["readiness"] != "CALLABLE_NEEDS_QUALIFICATION":
        raise GateRuleError(f"gate is not a callable structural rule: {gate_id}")
    if not isinstance(evidence, Mapping):
        raise GateRuleError("evidence must be a mapping")
    if _missing(evidence, rule["required_fields"]):
        return "NOT_ESTIMABLE"

    if gate_id == "G1_INTEGRITY_LINEAGE":
        names = evidence["required_identity_names"]
        bound = evidence["bound_identity_sha256"]
        if not _is_seq(names) or not names or any(not isinstance(v, str) or not v for v in names):
            return "FAIL"
        if len(names) != len(set(names)) or not isinstance(bound, Mapping) or set(bound) != set(names):
            return "FAIL"
        if any(not _is_sha256(bound[name]) for name in names):
            return "FAIL"
        if evidence["post_outcome_redesign"] is not False or evidence["post_outcome_relabeling"] is not False:
            return "FAIL"
        return "PASS"

    if gate_id == "R2_LOCALITY_RULE_FROZEN_NO_FINE_MINING":
        return "PASS" if evidence["locality_rule_prefrozen"] is True and evidence["fine_neighborhood_mining_used"] is False else "FAIL"

    if gate_id == "Q1_Q_SCALAR_STUDENT_ABSENT":
        return _query_guard_status(evidence, "student_sink")

    if gate_id == "Q2_Q_EXCLUDED_TEACHER_PRIMARY_ANCHOR":
        return "PASS" if evidence["q_excluded_teacher_primary_anchor"] is True else "FAIL"

    if gate_id == "Q3_TARGET_NORMALIZATION_Q_SCALAR_FREE":
        return _query_guard_status(evidence, "target_normalization_sink")

    raise GateRuleError(f"structural evaluator missing implementation: {gate_id}")


def validate_rule_registry() -> dict:
    universe = _gate_universe()
    if len(universe) != len(set(universe)) or set(RULES) != set(universe):
        raise GateRuleError("gate registry differs from frozen real-tournament gate universe")
    if set(_STRUCTURAL_SPECS) != CALLABLE_STRUCTURAL:
        raise GateRuleError("callable structural spec set drift")

    callable_count = 0
    for gate_id in universe:
        rule = RULES[gate_id]
        if rule.get("gate_id") != gate_id:
            raise GateRuleError(f"gate identity drift: {gate_id}")
        if rule.get("primary_biological_unit") != "donor":
            raise GateRuleError(f"donor-primary unit drift: {gate_id}")
        if rule.get("source_semantics") != "observation_operator_not_biological_replicate":
            raise GateRuleError(f"source semantics drift: {gate_id}")
        if gate_id in CALLABLE_STRUCTURAL:
            callable_count += 1
            if rule.get("readiness") != "CALLABLE_NEEDS_QUALIFICATION":
                raise GateRuleError(f"structural rule readiness drift: {gate_id}")
            if rule.get("threshold_source") != "NO_NUMERIC_THRESHOLD__FROZEN_STRUCTURAL_RULE":
                raise GateRuleError(f"structural threshold-source drift: {gate_id}")
            if not _is_sha256(rule.get("estimand_sha256")) or not _is_sha256(rule.get("decision_rule_sha256")):
                raise GateRuleError(f"structural rule hash missing: {gate_id}")
        else:
            if rule.get("readiness") != "RULE_NOT_MATERIALIZED":
                raise GateRuleError(f"unearned quantitative readiness promotion: {gate_id}")
            if any(rule.get(field) for field in ("callable_implementation", "estimand_sha256", "decision_rule_sha256")):
                raise GateRuleError(f"unearned quantitative callable/hash identity: {gate_id}")
            if rule.get("threshold_source") != "BLOCKED_PROSPECTIVE_RULE_REQUIRED":
                raise GateRuleError(f"quantitative blocker drift: {gate_id}")

    return {
        "gate_count": len(universe),
        "callable_structural_count": callable_count,
        "blocked_quantitative_count": len(universe) - callable_count,
    }
