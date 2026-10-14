"""Common gate-facing TD CaseBundle for real and synthetic execution.

Known truth is controller-only. Executors receive the same real-shaped schema in
all modes and cannot branch on a synthetic/real marker.
"""
from __future__ import annotations

import copy
import math
from collections.abc import Mapping


class CaseBundleError(ValueError):
    pass


_SUPPORT_STATES = {"SUPPORTED", "UNSUPPORTED_STRUCTURAL", "BLOCKED_EVIDENCE_CONTRACT"}
_TRUTH_STATUSES = {"PASS", "FAIL", "NOT_ESTIMABLE", "NUMERICAL_FAILURE"}
_REQUIRED_CASE_KEYS = {
    "schema",
    "case_id",
    "candidate_id",
    "gate_id",
    "donor_id",
    "source",
    "operator_id",
    "support_state",
    "support_universe_sha256",
    "evidence_rights",
    "evidence_contract_sha256",
    "observation_operator",
    "input_binding_sha256",
    "payload",
}
_REQUIRED_OBSERVATION_KEYS = {
    "assay",
    "measured_vocabulary_sha256",
    "count_depth",
    "detected_gene_count",
    "normalization_library_count",
    "observation_operator_sha256",
}
_FORBIDDEN_OBSERVATION_KEYS = {"donor_id", "matrix_id", "dataset_id", "dataset_embedding", "donor_embedding"}


def _is_sha256(value: object) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value)


def _exact_id(value: object, label: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip() or "\0" in value:
        raise CaseBundleError(f"{label} must be an exact nonempty trimmed NUL-free string")
    return value


def _contains_executor_forbidden_key(value: object) -> bool:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if isinstance(key, str):
                low = key.lower()
                if "truth" in low or "synthetic" in low:
                    return True
            if _contains_executor_forbidden_key(child):
                return True
    elif isinstance(value, (list, tuple)):
        return any(_contains_executor_forbidden_key(item) for item in value)
    return False


def _nonnegative_int(value: object, label: str) -> int:
    if isinstance(value, bool) or type(value) is not int or value < 0:
        raise CaseBundleError(f"{label} must be a nonnegative integer")
    return value


def validate_executor_case(bundle: Mapping[str, object]) -> dict:
    if not isinstance(bundle, Mapping):
        raise CaseBundleError("executor case must be a mapping")
    if set(bundle) != _REQUIRED_CASE_KEYS:
        raise CaseBundleError("executor case keys do not match frozen schema")
    if bundle.get("schema") != "JEPA_TD_EXECUTOR_CASE_BUNDLE_V1":
        raise CaseBundleError("executor case schema mismatch")
    if _contains_executor_forbidden_key(bundle):
        raise CaseBundleError("controller-only truth/synthetic identity is forbidden in executor-visible case")

    for field in ("case_id", "candidate_id", "gate_id", "donor_id", "source", "operator_id"):
        _exact_id(bundle.get(field), field)
    if bundle.get("support_state") not in _SUPPORT_STATES:
        raise CaseBundleError("invalid support_state")
    for field in ("support_universe_sha256", "evidence_contract_sha256", "input_binding_sha256"):
        if not _is_sha256(bundle.get(field)):
            raise CaseBundleError(f"{field} must be an exact lowercase SHA-256")

    rights = bundle.get("evidence_rights")
    if not isinstance(rights, list) or any(not isinstance(v, str) or not v or v != v.strip() for v in rights):
        raise CaseBundleError("evidence_rights must be a list of exact nonempty strings")
    if len(rights) != len(set(rights)):
        raise CaseBundleError("duplicate evidence_rights are forbidden")

    op = bundle.get("observation_operator")
    if not isinstance(op, Mapping):
        raise CaseBundleError("observation operator must be a mapping")
    if any(key in op for key in _FORBIDDEN_OBSERVATION_KEYS):
        raise CaseBundleError("observation operator cannot contain donor/matrix/arbitrary dataset identity")
    if set(op) != _REQUIRED_OBSERVATION_KEYS:
        raise CaseBundleError("observation operator keys do not match frozen physical descriptor schema")
    _exact_id(op.get("assay"), "observation_operator.assay")
    for field in ("measured_vocabulary_sha256", "observation_operator_sha256"):
        if not _is_sha256(op.get(field)):
            raise CaseBundleError(f"observation_operator.{field} must be an exact lowercase SHA-256")
    count_depth = _nonnegative_int(op.get("count_depth"), "observation_operator.count_depth")
    _nonnegative_int(op.get("detected_gene_count"), "observation_operator.detected_gene_count")
    library = _nonnegative_int(op.get("normalization_library_count"), "observation_operator.normalization_library_count")
    if library < count_depth:
        raise CaseBundleError("normalization library count cannot be smaller than stored count depth")

    payload = bundle.get("payload")
    if not isinstance(payload, Mapping):
        raise CaseBundleError("payload must be a mapping")

    return copy.deepcopy(dict(bundle))


def bind_controller_truth(executor_case: Mapping[str, object], truth: Mapping[str, object]) -> dict:
    clean_case = validate_executor_case(executor_case)
    if not isinstance(truth, Mapping):
        raise CaseBundleError("controller truth must be a mapping")
    if "expected_gate_status" in truth and truth.get("expected_gate_status") not in _TRUTH_STATUSES:
        raise CaseBundleError("expected_gate_status must be PASS/FAIL/NOT_ESTIMABLE/NUMERICAL_FAILURE")
    if "world_id" in truth:
        _exact_id(truth.get("world_id"), "controller_truth.world_id")
    return {
        "schema": "JEPA_TD_CONTROLLER_CASE_V1",
        "executor_case": clean_case,
        "controller_truth": copy.deepcopy(dict(truth)),
    }
