"""Certification bridge from immutable TD target bundle to JEPA teacher/student use.

Certification proves the downstream transformation preserves the TD scientific
contract. It never grants real-training or Stage4 authority.
"""
from __future__ import annotations

from collections.abc import Mapping

from scripts.v5 import td_target_qualification_bundle_v1 as T


_REQUIRED_KINDS = {
    "TEACHER_TARGET_CONSTRUCTION",
    "STUDENT_EVIDENCE_RESTRICTION",
    "LEAKAGE_FIREWALL",
    "SOURCE_SUPPORT_BOUNDARY",
    "OBSERVATION_OPERATOR_PRESERVATION",
    "REPRESENTATION_SEMANTICS_PRESERVATION",
    "JEPA_LOSS_EVALUATION_CONTRACT",
}
_LEAKAGE_CHECKS = {
    "hidden_target",
    "query_address",
    "totals",
    "support",
    "normalization",
    "teacher_student_oracle",
}
_AUTHORITY = {
    "target_selection": False,
    "representation_selection": False,
    "td60": False,
    "stage4": False,
    "real_training": False,
}


def _is_sha256(value: object) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value)


def _common_receipt_valid(kind: str, receipt: object, bundle_sha: str) -> bool:
    return bool(
        isinstance(receipt, Mapping)
        and receipt.get("schema") == "JEPA_TD_DOWNSTREAM_CERTIFICATION_RECEIPT_V1"
        and receipt.get("kind") == kind
        and receipt.get("status") == "PASS"
        and receipt.get("target_bundle_sha256") == bundle_sha
        and _is_sha256(receipt.get("producer_code_sha256"))
        and _is_sha256(receipt.get("receipt_sha256"))
    )


def _kind_specific_valid(kind: str, receipt: Mapping[str, object], bundle: Mapping[str, object]) -> bool:
    if kind == "TEACHER_TARGET_CONSTRUCTION":
        return receipt.get("teacher_constructs_td_target") is True
    if kind == "STUDENT_EVIDENCE_RESTRICTION":
        return receipt.get("student_only_uses_permitted_evidence") is True
    if kind == "LEAKAGE_FIREWALL":
        checks = receipt.get("checks")
        return isinstance(checks, Mapping) and set(checks) == _LEAKAGE_CHECKS and all(v == "PASS" for v in checks.values())
    if kind == "SOURCE_SUPPORT_BOUNDARY":
        return receipt.get("source_noncompensation_preserved") is True
    if kind == "OBSERVATION_OPERATOR_PRESERVATION":
        return receipt.get("observation_operator_contract_sha256") == bundle["policy_identities"]["observation_operator_contract_sha256"]
    if kind == "REPRESENTATION_SEMANTICS_PRESERVATION":
        return bool(
            receipt.get("support_estimability_map_sha256") == bundle["policy_identities"]["support_estimability_map_sha256"]
            and receipt.get("relational_semantics_sha256") == bundle["policy_identities"]["relational_semantics_sha256"]
        )
    if kind == "JEPA_LOSS_EVALUATION_CONTRACT":
        return receipt.get("target_is_not_visible_to_student_loss_input") is True
    return False


def validate_downstream_certification(*, target_bundle: Mapping[str, object], receipts: Mapping[str, object]) -> dict:
    bundle = T.validate_target_qualification_bundle(target_bundle)
    if not isinstance(receipts, Mapping):
        receipts = {}

    if bundle["selection"] == "NONE":
        if receipts:
            return {
                "schema": "JEPA_TD_DOWNSTREAM_CERTIFICATION_RESULT_V1",
                "status": "BLOCKED",
                "certification_complete": False,
                "blockers": ["NO_TARGET_MUST_NOT_CARRY_DOWNSTREAM_TARGET_CERTIFICATION_RECEIPTS"],
                "real_training_eligible": False,
                "authority": dict(_AUTHORITY),
            }
        return {
            "schema": "JEPA_TD_DOWNSTREAM_CERTIFICATION_RESULT_V1",
            "status": "NOT_APPLICABLE_NO_TARGET",
            "certification_complete": True,
            "blockers": [],
            "real_training_eligible": False,
            "authority": dict(_AUTHORITY),
        }

    blockers: list[str] = []
    for missing in sorted(_REQUIRED_KINDS - set(receipts)):
        blockers.append(missing)
    for extra in sorted(set(receipts) - _REQUIRED_KINDS):
        blockers.append(extra)

    for kind in sorted(_REQUIRED_KINDS & set(receipts)):
        receipt = receipts[kind]
        if not _common_receipt_valid(kind, receipt, bundle["bundle_sha256"]):
            blockers.append(kind)
            continue
        if not _kind_specific_valid(kind, receipt, bundle):
            blockers.append(kind)

    blockers = list(dict.fromkeys(blockers))
    complete = not blockers
    return {
        "schema": "JEPA_TD_DOWNSTREAM_CERTIFICATION_RESULT_V1",
        "status": "DOWNSTREAM_CERTIFIED" if complete else "BLOCKED",
        "certification_complete": complete,
        "blockers": blockers,
        "target_bundle_sha256": bundle["bundle_sha256"],
        "real_training_eligible": False,
        "authority": dict(_AUTHORITY),
    }
