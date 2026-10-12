"""Authenticated bridge from qualified gate-specific executors to candidate status.

This module deliberately does not invent numerical thresholds. Gate-specific
executors remain responsible for their prospectively frozen estimands and
rules. This bridge validates their identities and complete outputs, preserves
raw sufficient statistics, and applies only the frozen PASS/FAIL/NOT_ESTIMABLE
candidate aggregation semantics.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

import td_real_tournament_contract_v1 as C


class GateBridgeError(ValueError):
    pass


_ALLOWED_STATUS = {"PASS", "FAIL", "NOT_ESTIMABLE"}
_IDENTITY_FIELDS = (
    "qualified_gate_executor_sha256", "estimand_sha256", "decision_rule_sha256"
)


def _is_sha256(value) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(ch in "0123456789abcdef" for ch in value)


@dataclass(frozen=True)
class CandidateGateReceipt:
    candidate_id: str
    gates: dict[str, dict]
    status: str
    authority: dict[str, bool]


def evaluate_candidate(candidate_id: str, gate_outputs: Mapping[str, Mapping], gate_bindings: Mapping[str, Mapping]) -> CandidateGateReceipt:
    contract = C.load_real_tournament_contract()
    registry = C.validate_candidate_registry(contract)
    if candidate_id not in registry:
        raise GateBridgeError(f"unknown candidate_id: {candidate_id}")
    required = list(registry[candidate_id]["required_gates"])
    if not isinstance(gate_outputs, Mapping) or set(gate_outputs) != set(required):
        raise GateBridgeError("gate_outputs must cover the exact required gate set")
    if not isinstance(gate_bindings, Mapping) or set(gate_bindings) != set(required):
        raise GateBridgeError("gate_bindings must cover the exact required gate set")

    gates = {}
    statuses = []
    for gate_id in required:
        output = gate_outputs[gate_id]
        bound = gate_bindings[gate_id]
        if not isinstance(output, Mapping) or not isinstance(bound, Mapping):
            raise GateBridgeError(f"gate output/binding must be mappings: {gate_id}")
        for field in _IDENTITY_FIELDS:
            expected = bound.get(field)
            actual = output.get(field)
            if not _is_sha256(expected):
                raise GateBridgeError(f"binding {field} must be lowercase SHA-256: {gate_id}")
            if actual != expected:
                raise GateBridgeError(f"{field} mismatch for gate {gate_id}")
        status = output.get("status")
        if status not in _ALLOWED_STATUS:
            raise GateBridgeError(f"gate status must be PASS/FAIL/NOT_ESTIMABLE: {gate_id}")
        evidence_sha = output.get("evidence_payload_sha256")
        if not _is_sha256(evidence_sha):
            raise GateBridgeError(f"evidence_payload_sha256 must be lowercase SHA-256: {gate_id}")
        raw = output.get("raw_sufficient_statistics")
        if not isinstance(raw, Mapping):
            raise GateBridgeError(f"raw_sufficient_statistics mapping required: {gate_id}")
        gates[gate_id] = {
            "status": status,
            "qualified_gate_executor_sha256": output["qualified_gate_executor_sha256"],
            "estimand_sha256": output["estimand_sha256"],
            "decision_rule_sha256": output["decision_rule_sha256"],
            "evidence_payload_sha256": evidence_sha,
            "raw_sufficient_statistics": dict(raw),
        }
        statuses.append(status)

    if "FAIL" in statuses:
        candidate_status = "FAIL"
    elif "NOT_ESTIMABLE" in statuses:
        candidate_status = "NOT_ESTIMABLE"
    else:
        candidate_status = "PASS"
    return CandidateGateReceipt(
        candidate_id=candidate_id,
        gates=gates,
        status=candidate_status,
        authority={key: False for key in sorted(C.AUTHORITY_KEYS)},
    )
