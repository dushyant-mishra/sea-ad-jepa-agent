"""Exact-root V2 teacher-target receipt bound to closure V2 and preexecution V2."""
from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

from .current_authority_roots_v2 import CURRENT_V5_RECEIPT_AUTHORITY_ROOTS_V2

KIND = "v5_current_teacher_target_receipt_v2"
SCOPE = "CURRENT_V5_DATASET_DERIVED_TEACHER_TARGET_V2"


def _sha(value: object, name: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or value != value.lower():
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{name} must be a lowercase SHA-256 digest") from exc
    return value


def _digest(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode()).hexdigest()


def _roots(values: object) -> dict[str, str]:
    if not isinstance(values, Mapping) or tuple(values) != CURRENT_V5_RECEIPT_AUTHORITY_ROOTS_V2:
        raise ValueError("authority_roots must exactly match current V2 receipt roots")
    return {name: _sha(values[name], name) for name in CURRENT_V5_RECEIPT_AUTHORITY_ROOTS_V2}


def _core(target_package_root: str, authority_roots: object, closure_v2_sha256: str) -> dict[str, Any]:
    return {
        "kind": KIND,
        "scope": SCOPE,
        "target_package_root": _sha(target_package_root, "target_package_root"),
        "authority_roots": _roots(authority_roots),
        "closure_v2_sha256": _sha(closure_v2_sha256, "closure_v2_sha256"),
        "training_authorized": False,
    }


def seal_current_teacher_target_receipt_v2(*, target_package_root: str, authority_roots: Mapping[str, str], closure_v2_sha256: str) -> dict[str, Any]:
    core = _core(target_package_root, authority_roots, closure_v2_sha256)
    return {**core, "receipt_digest": _digest(core)}


def validate_current_teacher_target_receipt_v2(receipt: Mapping[str, Any], *, expected_target_package_root: str, expected_authority_roots: Mapping[str, str], expected_closure_v2_sha256: str) -> dict[str, Any]:
    if not isinstance(receipt, Mapping):
        raise ValueError("receipt must be a mapping")
    expected_fields = {"kind", "scope", "target_package_root", "authority_roots", "closure_v2_sha256", "training_authorized", "receipt_digest"}
    if set(receipt) != expected_fields:
        raise ValueError("receipt fields must exactly match V2 schema")
    if receipt.get("kind") != KIND or receipt.get("scope") != SCOPE:
        raise ValueError("receipt V2 kind or scope mismatch")
    if receipt.get("training_authorized") is not False:
        raise ValueError("receipt cannot authorize training")
    expected_roots = _roots(expected_authority_roots)
    core = _core(receipt.get("target_package_root"), receipt.get("authority_roots"), receipt.get("closure_v2_sha256"))
    if core["target_package_root"] != _sha(expected_target_package_root, "expected_target_package_root"):
        raise ValueError("target_package_root mismatch")
    if core["authority_roots"] != expected_roots:
        raise ValueError("authority_roots mismatch")
    if core["closure_v2_sha256"] != _sha(expected_closure_v2_sha256, "expected_closure_v2_sha256"):
        raise ValueError("closure_v2_sha256 mismatch")
    digest = _sha(receipt.get("receipt_digest"), "receipt_digest")
    if digest != _digest(core):
        raise ValueError("receipt digest mismatch")
    return {**core, "receipt_digest": digest}
