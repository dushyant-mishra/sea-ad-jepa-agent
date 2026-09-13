"""Fail-closed executable evidence authority for V5 control artifacts.

The validator recomputes SHA-256 from exact raw bytes and deterministically
recomputes verdicts from check-level observations and prospectively bound
thresholds/operators. Declared PASS booleans are never accepted on faith.
"""
from __future__ import annotations

import hashlib
import json
import math
import operator
from typing import Mapping

SCHEMA = "JEPA_V5_EXECUTABLE_CONTROL_EVIDENCE_V1"
_ALLOWED_PROVENANCE = frozenset({"PROSPECTIVE_PREMODEL", "INDEPENDENT_CALIBRATION"})
_VERDICT_KEYS = (
    "minimum_acceptable_signal_present",
    "minimum_rejection_violation_present",
    "gate_accepts_valid_control",
    "gate_rejects_invalid_control",
)
_OPS = {
    ">": operator.gt,
    ">=": operator.ge,
    "<": operator.lt,
    "<=": operator.le,
    "==": operator.eq,
}


def _sha(value: object, name: str) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise ValueError(f"{name} must be a SHA-256 hex digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{name} must be hexadecimal") from exc
    return value.lower()


def _finite_number(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be numeric")
    out = float(value)
    if not math.isfinite(out):
        raise ValueError(f"{name} must be finite")
    return out


def _recompute_check(check: Mapping[str, object], *, role: str, index: int) -> bool:
    if not isinstance(check, Mapping) or set(check) != {"id", "observed", "operator", "threshold"}:
        raise ValueError(f"{role}[{index}] check schema mismatch")
    cid = check.get("id")
    if not isinstance(cid, str) or not cid.strip():
        raise ValueError(f"{role}[{index}].id must be nonempty")
    op_name = check.get("operator")
    if op_name not in _OPS:
        raise ValueError(f"{role}[{index}].operator is not allowed")
    observed = _finite_number(check.get("observed"), f"{role}[{index}].observed")
    threshold = _finite_number(check.get("threshold"), f"{role}[{index}].threshold")
    return bool(_OPS[op_name](observed, threshold))


def recompute_control_artifact(
    raw_bytes: bytes,
    *,
    expected_gate_id: str,
    expected_geometry_sha256: str,
    declared_raw_sha256: str,
) -> dict[str, object]:
    if not isinstance(raw_bytes, bytes) or not raw_bytes:
        raise ValueError("raw_bytes must be nonempty bytes")
    if not isinstance(expected_gate_id, str) or not expected_gate_id.strip():
        raise ValueError("expected_gate_id must be nonempty")
    geometry = _sha(expected_geometry_sha256, "expected_geometry_sha256")
    declared = _sha(declared_raw_sha256, "declared_raw_sha256")
    actual = hashlib.sha256(raw_bytes).hexdigest()
    if actual != declared:
        raise RuntimeError("STOP_V5_EXECUTABLE_EVIDENCE_RAW_SHA256_MISMATCH")

    try:
        payload = json.loads(raw_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("raw_bytes must contain one UTF-8 JSON object") from exc
    if not isinstance(payload, Mapping):
        raise ValueError("raw evidence payload must be an object")
    expected_fields = {"schema", "gate_id", "geometry_sha256", "threshold_provenance", "checks"}
    if set(payload) != expected_fields:
        raise ValueError("raw evidence payload schema mismatch")
    if payload.get("schema") != SCHEMA:
        raise ValueError("unexpected executable evidence schema")
    if payload.get("gate_id") != expected_gate_id:
        raise RuntimeError("STOP_V5_EXECUTABLE_EVIDENCE_GATE_SUBSTITUTION")
    if _sha(payload.get("geometry_sha256"), "geometry_sha256") != geometry:
        raise RuntimeError("STOP_V5_EXECUTABLE_EVIDENCE_GEOMETRY_MISMATCH")
    if payload.get("threshold_provenance") not in _ALLOWED_PROVENANCE:
        raise RuntimeError("STOP_V5_EXECUTABLE_EVIDENCE_THRESHOLD_PROVENANCE")

    checks = payload.get("checks")
    if not isinstance(checks, Mapping) or set(checks) != set(_VERDICT_KEYS):
        raise ValueError("executable evidence checks must cover exactly the canonical verdict set")
    verdicts: dict[str, bool] = {}
    for role in _VERDICT_KEYS:
        role_checks = checks[role]
        if not isinstance(role_checks, list) or not role_checks:
            raise ValueError(f"{role} must contain at least one executable check")
        verdicts[role] = all(
            _recompute_check(check, role=role, index=i)
            for i, check in enumerate(role_checks)
        )

    return {
        "schema": SCHEMA,
        "gate_id": expected_gate_id,
        "geometry_sha256": geometry,
        "raw_sha256": actual,
        "threshold_provenance": payload["threshold_provenance"],
        "verdicts": verdicts,
        "training_authorized": False,
    }


def verify_declared_control_verdicts(
    raw_bytes: bytes,
    *,
    expected_gate_id: str,
    expected_geometry_sha256: str,
    declared_raw_sha256: str,
    declared_verdicts: Mapping[str, object],
) -> dict[str, object]:
    if not isinstance(declared_verdicts, Mapping) or set(declared_verdicts) != set(_VERDICT_KEYS):
        raise ValueError("declared_verdicts must cover exactly the canonical verdict set")
    if any(type(declared_verdicts[key]) is not bool for key in _VERDICT_KEYS):
        raise ValueError("declared verdicts must be booleans")
    recomputed = recompute_control_artifact(
        raw_bytes,
        expected_gate_id=expected_gate_id,
        expected_geometry_sha256=expected_geometry_sha256,
        declared_raw_sha256=declared_raw_sha256,
    )
    if dict(declared_verdicts) != recomputed["verdicts"]:
        raise RuntimeError("STOP_V5_EXECUTABLE_EVIDENCE_DECLARED_VERDICT_MISMATCH")
    return recomputed
