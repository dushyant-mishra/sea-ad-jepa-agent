"""Canonical scientific identity primitives for Unified TD Task 1.

For JSON-compatible values, canonical byte rules intentionally preserve the
reviewed production-synthetic Task 1 behavior: sorted string keys, compact UTF-8,
None as the only missing value, bool distinct from int, float distinct from int,
-0.0 normalized to 0.0, CRLF/CR normalized to LF in strings, and NaN/Inf rejected.

Unified receipt identities use a new explicit domain and are not aliases for old
production-synthetic semantic identities.
"""
from __future__ import annotations

import hashlib
import math
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Callable

__all__ = [
    "CanonicalError",
    "VerifiedReceipt",
    "canonical_bytes",
    "canonical_sha256",
    "make_scientific_receipt",
    "verify_scientific_receipt",
]

_RECEIPT_SCHEMA = "SCIENTIFIC_RECEIPT_V1"
_CANONICAL_DOMAIN = b"JEPA-TD-UNIFIED-CANONICAL-V1\x00"
_HEX = set("0123456789abcdef")


class CanonicalError(ValueError):
    """Fail-closed error for invalid canonical or receipt input."""


@dataclass(frozen=True)
class VerifiedReceipt:
    receipt_sha256: str
    payload_sha256: str
    verified_parent_shas: tuple[str, ...]


def _norm_eol(value: str) -> str:
    return value.replace("\r\n", "\n").replace("\r", "\n")


def _encode_string(value: str) -> str:
    out = ['"']
    for ch in _norm_eol(value):
        code = ord(ch)
        if 0xD800 <= code <= 0xDFFF:
            raise CanonicalError("lone surrogate is not valid canonical text")
        if ch == '"':
            out.append('\\"')
        elif ch == "\\":
            out.append("\\\\")
        elif ch == "\n":
            out.append("\\n")
        elif ch == "\t":
            out.append("\\t")
        elif ch == "\b":
            out.append("\\b")
        elif ch == "\f":
            out.append("\\f")
        elif code < 0x20:
            out.append(f"\\u{code:04x}")
        else:
            out.append(ch)
    out.append('"')
    return "".join(out)


def _encode(value: Any, out: list[str]) -> None:
    if value is None:
        out.append("null")
    elif isinstance(value, bool):
        out.append("true" if value else "false")
    elif isinstance(value, int):
        try:
            out.append(str(value))
        except ValueError as exc:
            raise CanonicalError("integer too large to serialize exactly") from exc
    elif isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            raise CanonicalError("NaN/Inf are forbidden; None is the only missing value")
        out.append("0.0" if value == 0.0 else repr(value))
    elif isinstance(value, str):
        out.append(_encode_string(value))
    elif isinstance(value, Mapping):
        normalized: dict[str, Any] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise CanonicalError("canonical mapping keys must be strings")
            key_n = _norm_eol(key)
            if key_n in normalized:
                raise CanonicalError("mapping keys collide after line-ending normalization")
            normalized[key_n] = item
        out.append("{")
        for index, key in enumerate(sorted(normalized)):
            if index:
                out.append(",")
            out.append(_encode_string(key))
            out.append(":")
            _encode(normalized[key], out)
        out.append("}")
    elif isinstance(value, (list, tuple)):
        out.append("[")
        for index, item in enumerate(value):
            if index:
                out.append(",")
            _encode(item, out)
        out.append("]")
    else:
        raise CanonicalError(f"unsupported canonical type: {type(value).__name__}")


def canonical_bytes(payload: Mapping[str, object] | object) -> bytes:
    out: list[str] = []
    try:
        _encode(payload, out)
        return "".join(out).encode("utf-8")
    except (RecursionError, UnicodeEncodeError) as exc:
        raise CanonicalError("payload is not canonically serializable") from exc


def canonical_sha256(payload: Mapping[str, object] | object) -> str:
    return hashlib.sha256(_CANONICAL_DOMAIN + canonical_bytes(payload)).hexdigest()


def _is_hex(value: object, length: int) -> bool:
    return isinstance(value, str) and len(value) == length and set(value) <= _HEX


def _require_hex(name: str, value: object, length: int) -> None:
    if not _is_hex(value, length):
        raise CanonicalError(f"{name} must be lowercase {length}-hex")


def _normalize_hash_list(name: str, values: object) -> list[str]:
    if not isinstance(values, list):
        raise CanonicalError(f"{name} must be a list")
    for value in values:
        _require_hex(name, value, 64)
    if len(values) != len(set(values)):
        raise CanonicalError(f"duplicate {name} identity")
    return list(values)


def _receipt_body(receipt: Mapping[str, object]) -> dict[str, object]:
    return {key: value for key, value in receipt.items() if key != "receipt_sha256"}


def make_scientific_receipt(
    *,
    payload: Mapping[str, object],
    producer_code_sha: str,
    input_shas: list[str],
    parent_receipt_shas: list[str],
    output_sha: str,
    manifest_sha: str,
    registry_sha: str,
    access_policy_sha: str,
) -> dict[str, object]:
    if not isinstance(payload, Mapping):
        raise CanonicalError("payload must be a mapping")
    _require_hex("producer_code_sha", producer_code_sha, 40)
    inputs = _normalize_hash_list("input_shas", input_shas)
    parents = _normalize_hash_list("parent_receipt_shas", parent_receipt_shas)
    for name, value in (
        ("output_sha", output_sha),
        ("manifest_sha", manifest_sha),
        ("registry_sha", registry_sha),
        ("access_policy_sha", access_policy_sha),
    ):
        _require_hex(name, value, 64)

    body: dict[str, object] = {
        "receipt_schema": _RECEIPT_SCHEMA,
        "producer_code_sha": producer_code_sha,
        "input_shas": inputs,
        "parent_receipt_shas": parents,
        "output_sha": output_sha,
        "manifest_sha": manifest_sha,
        "registry_sha": registry_sha,
        "access_policy_sha": access_policy_sha,
        "payload": dict(payload),
        "payload_sha256": canonical_sha256(payload),
    }
    body["receipt_sha256"] = canonical_sha256(body)
    return body


def _verify_resolved_input(
    input_sha: str,
    resolved: object,
    object_resolver: Callable[[str], object | None],
    stack: frozenset[str],
) -> None:
    if resolved is None:
        raise CanonicalError(f"input object unavailable: {input_sha}")
    if isinstance(resolved, Mapping) and resolved.get("receipt_schema") == _RECEIPT_SCHEMA:
        verified = verify_scientific_receipt(resolved, object_resolver, _stack=stack)
        if verified.receipt_sha256 != input_sha:
            raise CanonicalError("input receipt identity mismatch")
        return
    try:
        actual = canonical_sha256(resolved)
    except CanonicalError as exc:
        raise CanonicalError(f"input object is not canonically verifiable: {input_sha}") from exc
    if actual != input_sha:
        raise CanonicalError("input object digest mismatch")


def verify_scientific_receipt(
    receipt: Mapping[str, object],
    object_resolver: Callable[[str], object | None],
    *,
    _stack: frozenset[str] | None = None,
) -> VerifiedReceipt:
    if not isinstance(receipt, Mapping):
        raise CanonicalError("receipt must be a mapping")
    required = {
        "receipt_schema",
        "producer_code_sha",
        "input_shas",
        "parent_receipt_shas",
        "output_sha",
        "manifest_sha",
        "registry_sha",
        "access_policy_sha",
        "payload",
        "payload_sha256",
        "receipt_sha256",
    }
    if set(receipt) != required:
        raise CanonicalError("receipt fields do not match SCIENTIFIC_RECEIPT_V1")
    if receipt["receipt_schema"] != _RECEIPT_SCHEMA:
        raise CanonicalError("unknown receipt schema")
    _require_hex("producer_code_sha", receipt["producer_code_sha"], 40)
    inputs = _normalize_hash_list("input_shas", receipt["input_shas"])
    parents = _normalize_hash_list("parent_receipt_shas", receipt["parent_receipt_shas"])
    for name in ("output_sha", "manifest_sha", "registry_sha", "access_policy_sha", "payload_sha256", "receipt_sha256"):
        _require_hex(name, receipt[name], 64)
    if not isinstance(receipt["payload"], Mapping):
        raise CanonicalError("payload must be a mapping")
    actual_payload = canonical_sha256(receipt["payload"])
    if actual_payload != receipt["payload_sha256"]:
        raise CanonicalError("payload digest mismatch")
    actual_receipt = canonical_sha256(_receipt_body(receipt))
    if actual_receipt != receipt["receipt_sha256"]:
        raise CanonicalError("receipt digest mismatch")

    receipt_sha = str(receipt["receipt_sha256"])
    stack = _stack or frozenset()
    if receipt_sha in stack:
        raise CanonicalError("parent receipt cycle detected")
    next_stack = stack | {receipt_sha}

    for input_sha in inputs:
        _verify_resolved_input(input_sha, object_resolver(input_sha), object_resolver, next_stack)

    verified_parents: list[str] = []
    for parent_sha in parents:
        parent = object_resolver(parent_sha)
        if parent is None:
            raise CanonicalError(f"parent receipt unavailable: {parent_sha}")
        if not isinstance(parent, Mapping):
            raise CanonicalError("parent receipt must resolve to a mapping")
        verified = verify_scientific_receipt(parent, object_resolver, _stack=next_stack)
        if verified.receipt_sha256 != parent_sha:
            raise CanonicalError("parent receipt identity mismatch")
        verified_parents.append(parent_sha)

    return VerifiedReceipt(receipt_sha, actual_payload, tuple(verified_parents))
