from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

import td_test_qualification_package_v1 as P


_ALLOWED_STATUS = {"PASS", "FAIL", "NOT_ESTIMABLE"}
_EXPECTED_BY_SEMANTIC = {
    "POSITIVE_TRUTH": "PASS",
    "NEGATIVE_TRUTH": "FAIL",
    "UNDERIDENTIFIED_TRUTH": "NOT_ESTIMABLE",
}
_AUTHORITY = {
    "real_tournament_authorized": False,
    "target_selection_authorized": False,
    "td60_authorized": False,
    "stage4_authorized": False,
    "training_authorized": False,
}


class GateQualificationError(ValueError):
    pass


@dataclass(frozen=True)
class GateQualificationReceipt:
    candidate_id: str
    gate_id: str
    executor_sha256: str
    estimand_sha256: str
    decision_rule_sha256: str
    package_sha256: str
    challenge_results: tuple[dict, ...]
    qualification_status: str
    failure_scope: str
    authority: dict[str, bool]


def _is_sha256(value) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(ch in "0123456789abcdef" for ch in value)


def adjudicate_gate_qualification(
    *,
    candidate_id: str,
    gate_id: str,
    gate_binding: Mapping,
    package: P.ValidatedExternalPackage,
    gate_outputs: Mapping[str, Mapping],
    expected_status_by_capability: Mapping[str, str] | None = None,
) -> GateQualificationReceipt:
    if not isinstance(candidate_id, str) or not candidate_id or not isinstance(gate_id, str) or not gate_id:
        raise GateQualificationError("candidate_id and gate_id must be nonempty strings")
    required_ids = ("qualified_gate_executor_sha256", "estimand_sha256", "decision_rule_sha256")
    for field in required_ids:
        if not _is_sha256(gate_binding.get(field)):
            raise GateQualificationError(f"invalid gate binding identity: {field}")
    failure_scope = gate_binding.get("failure_scope")
    if not isinstance(failure_scope, str) or not failure_scope:
        raise GateQualificationError("failure_scope must be a nonempty string")
    required_capabilities = gate_binding.get("required_capabilities")
    if not isinstance(required_capabilities, list) or not required_capabilities:
        raise GateQualificationError("required_capabilities must be a nonempty list")

    missing = [cap for cap in required_capabilities if cap not in package.capabilities]
    if missing:
        return GateQualificationReceipt(
            candidate_id=candidate_id,
            gate_id=gate_id,
            executor_sha256=gate_binding[required_ids[0]],
            estimand_sha256=gate_binding[required_ids[1]],
            decision_rule_sha256=gate_binding[required_ids[2]],
            package_sha256=package.package_sha256,
            challenge_results=tuple(),
            qualification_status="INCOMPLETE",
            failure_scope=failure_scope,
            authority=dict(_AUTHORITY),
        )

    expected_status_by_capability = dict(expected_status_by_capability or {})
    expected_challenges = {package.capabilities[cap]["challenge_id"] for cap in required_capabilities}
    if set(gate_outputs) != expected_challenges:
        raise GateQualificationError("gate_outputs must cover the exact required challenge set")

    challenge_results = []
    any_mismatch = False
    for capability_id in required_capabilities:
        capability = package.capabilities[capability_id]
        challenge_id = capability["challenge_id"]
        output = gate_outputs.get(challenge_id)
        if not isinstance(output, Mapping):
            return GateQualificationReceipt(
                candidate_id=candidate_id,
                gate_id=gate_id,
                executor_sha256=gate_binding[required_ids[0]],
                estimand_sha256=gate_binding[required_ids[1]],
                decision_rule_sha256=gate_binding[required_ids[2]],
                package_sha256=package.package_sha256,
                challenge_results=tuple(challenge_results),
                qualification_status="INCOMPLETE",
                failure_scope=failure_scope,
                authority=dict(_AUTHORITY),
            )
        for field in required_ids:
            if output.get(field) != gate_binding[field]:
                raise GateQualificationError(f"{field} mismatch for challenge {challenge_id}")
        status = output.get("status")
        if status not in _ALLOWED_STATUS:
            raise GateQualificationError(f"invalid gate status for challenge {challenge_id}")
        if not _is_sha256(output.get("evidence_payload_sha256")):
            raise GateQualificationError(f"invalid evidence_payload_sha256 for challenge {challenge_id}")
        if not isinstance(output.get("raw_sufficient_statistics"), Mapping):
            raise GateQualificationError(f"raw_sufficient_statistics required for challenge {challenge_id}")

        semantic = capability["semantic_class"]
        expected = _EXPECTED_BY_SEMANTIC.get(semantic)
        if semantic == "STRESS_TRUTH":
            expected = expected_status_by_capability.get(capability_id)
            if expected not in _ALLOWED_STATUS:
                raise GateQualificationError(f"STRESS_TRUTH requires controller-only expected status: {capability_id}")
        elif capability_id in expected_status_by_capability and expected_status_by_capability[capability_id] != expected:
            raise GateQualificationError(f"expected status contradicts semantic class: {capability_id}")
        if expected is None:
            raise GateQualificationError(f"semantic class requires an explicit future rule: {semantic}")

        matched = status == expected
        any_mismatch = any_mismatch or not matched
        challenge_results.append({
            "capability_id": capability_id,
            "challenge_id": challenge_id,
            "semantic_class": semantic,
            "expected_status": expected,
            "observed_status": status,
            "matched": matched,
            "evidence_payload_sha256": output["evidence_payload_sha256"],
            "raw_sufficient_statistics": dict(output["raw_sufficient_statistics"]),
        })

    return GateQualificationReceipt(
        candidate_id=candidate_id,
        gate_id=gate_id,
        executor_sha256=gate_binding[required_ids[0]],
        estimand_sha256=gate_binding[required_ids[1]],
        decision_rule_sha256=gate_binding[required_ids[2]],
        package_sha256=package.package_sha256,
        challenge_results=tuple(challenge_results),
        qualification_status="NOT_QUALIFIED" if any_mismatch else "QUALIFIED",
        failure_scope=failure_scope,
        authority=dict(_AUTHORITY),
    )
