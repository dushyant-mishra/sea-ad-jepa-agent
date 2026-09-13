"""Hash-bound legacy T0/V21 target receipt retained for mechanics replay.

This receipt predates the dataset-first V5 target-discovery/teacher-authority
chain.  It remains useful for reproducing bounded optimizer-guard mechanics,
but it is *not* a current V5 biological teacher authority and may not authorize
a current V5 base-learning update.  The production-facing runtime enforces that
separation explicitly.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

STOP = "STOP_V5_QUALIFIED_TARGET_RECEIPT_INVALID"
KIND = "v5_qualified_teacher_target_receipt_v1"
TARGET_KIND = "t0_v21_target_freeze_receipt_v1"
MODE = "BOUNDED_QUALIFICATION_ONLY"
LEGACY_T0_AUTHORITY_SCOPE = "LEGACY_T0_V21_BOUNDED_QUALIFICATION_MECHANICS_ONLY"
REQUIRED_V5_ROOTS = (
    "trainer_preexecution_authority_sha256",
    "preexecution_bundle_sha256",
    "full104_expression_root_digest",
    "representation_firewall_sha256",
    "v5_runtime_source_sha256",
)


def _fail(message: str) -> None:
    raise RuntimeError(f"{STOP}: {message}")


def _sha(name: str, value: Any) -> str:
    text = str(value)
    if len(text) != 64 or any(c not in "0123456789abcdef" for c in text):
        _fail(f"{name} must be a lowercase SHA-256 digest")
    return text


def _digest(value: Mapping[str, Any]) -> str:
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(
        b"V5_QUALIFIED_TEACHER_TARGET_RECEIPT_V1\0" + payload
    ).hexdigest()


def seal_qualified_teacher_target_receipt(
    *,
    target_freeze_receipt: Mapping[str, Any],
    v5_authority_roots: Mapping[str, str],
) -> dict[str, Any]:
    """Seal the historical V21 receipt without promoting its scientific scope."""
    if target_freeze_receipt.get("kind") != TARGET_KIND:
        _fail("target must be the V21 46-donor freeze receipt")
    if int(target_freeze_receipt.get("n_development_donors", -1)) != 46:
        _fail("target freeze receipt must bind exactly 46 development donors")

    target_root = _sha("target package_root", target_freeze_receipt.get("package_root"))
    bindings = target_freeze_receipt.get("bindings", {})
    for name in (
        "code_sha",
        "contract_sha",
        "expression_root_digest",
        "role_ledger_digest",
    ):
        if name not in bindings:
            _fail(f"target binding {name} missing")
        _sha(f"target.{name}", bindings[name])

    missing = [key for key in REQUIRED_V5_ROOTS if key not in v5_authority_roots]
    extra = sorted(set(v5_authority_roots) - set(REQUIRED_V5_ROOTS))
    if missing or extra:
        _fail(f"V5 authority roots mismatch missing={missing} extra={extra}")
    roots = {key: _sha(key, v5_authority_roots[key]) for key in REQUIRED_V5_ROOTS}

    # Preserve the historical serialized body/digest exactly.  Scope is returned
    # by validation as metadata rather than inserted here, so existing forensic
    # receipts remain byte/hash reproducible.
    body = {
        "kind": KIND,
        "execution_mode": MODE,
        "target_kind": TARGET_KIND,
        "target_package_root": target_root,
        "target_n_development_donors": 46,
        "target_estimator_id": str(target_freeze_receipt.get("estimator_id", "")),
        "target_code_sha": str(bindings["code_sha"]),
        "target_contract_sha": str(bindings["contract_sha"]),
        "target_expression_root_digest": str(bindings["expression_root_digest"]),
        "target_role_ledger_digest": str(bindings["role_ledger_digest"]),
        "v5_authority_roots": roots,
        "production_training_authorized": False,
    }
    if not body["target_estimator_id"]:
        _fail("target estimator id must be nonempty")
    body["receipt_digest"] = _digest(body)
    return body


def validate_qualified_teacher_target_receipt(
    receipt: Mapping[str, Any],
    *,
    expected_target_package_root: str,
    expected_v5_authority_roots: Mapping[str, str],
) -> dict[str, Any]:
    """Validate a historical receipt and return its non-production scope."""
    if not isinstance(receipt, Mapping) or receipt.get("kind") != KIND:
        _fail("qualified teacher-target receipt is required")
    if receipt.get("execution_mode") != MODE:
        _fail("only bounded qualification mode is allowed")
    if receipt.get("production_training_authorized") is not False:
        _fail("receipt may not claim production training authority")
    if int(receipt.get("target_n_development_donors", -1)) != 46:
        _fail("receipt is not bound to the 46-donor successor target")
    if receipt.get("target_kind") != TARGET_KIND:
        _fail("target kind mismatch")

    expected_root = _sha("expected_target_package_root", expected_target_package_root)
    if receipt.get("target_package_root") != expected_root:
        _fail("target package root mismatch")

    observed_roots = receipt.get("v5_authority_roots", {})
    for key in REQUIRED_V5_ROOTS:
        if key not in expected_v5_authority_roots:
            _fail(f"expected V5 authority root {key} missing")
        expected = _sha(key, expected_v5_authority_roots[key])
        if observed_roots.get(key) != expected:
            _fail(f"V5 authority root mismatch for {key}")

    body = {key: receipt[key] for key in receipt if key != "receipt_digest"}
    if receipt.get("receipt_digest") != _digest(body):
        _fail("receipt digest does not recompute")

    return {
        "verified": True,
        "receipt_digest": receipt["receipt_digest"],
        "target_package_root": receipt["target_package_root"],
        "execution_mode": MODE,
        "authority_scope": LEGACY_T0_AUTHORITY_SCOPE,
        "current_v5_teacher_authority": False,
        "production_training_authorized": False,
    }
