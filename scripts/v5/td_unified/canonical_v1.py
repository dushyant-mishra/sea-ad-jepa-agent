"""Canonical scientific identity primitives for Unified TD Task 1.

FINGERPRINT FORMAT V1
=====================
Scientific JSON values are serialized to UTF-8 with no BOM, no insignificant
whitespace and no trailing newline. Mapping keys are exact built-in ``str``
values, line endings are normalized CRLF -> LF then CR -> LF, keys are sorted
in Unicode code-point order, and values are emitted recursively. ``None`` is
the only missing value. Built-in ``bool``, ``int``, ``float`` and ``str`` are
accepted only at their exact Python types; subclasses are rejected so a value
cannot override ``repr``, ``str`` or ``replace`` and choose its own canonical
bytes. Exact built-in ``dict``, ``list`` and ``tuple`` are the container types.

The frozen NumPy scalar policy matches the reviewed old Task 1 contract:
``np.bool_`` maps to bool; exact NumPy integer scalar types map through Python
``int``; exact NumPy floating scalar types of width <= 8 bytes widen to Python
float64 and then use the built-in float encoder; wider NumPy floats are
rejected. NumPy datetime/timedelta, strings, arrays and other NumPy objects are
rejected. ``-0.0`` is normalized to ``0.0`` and NaN/Inf are rejected.

``canonical_sha256(payload)`` is lowercase SHA-256 of the literal domain
``b"JEPA-TD-UNIFIED-CANONICAL-V1\\x00"`` concatenated with the canonical bytes.
Known answer: ``{"a":1,"b":[true,null,1.0]}`` hashes to
``8b441603e35b6bb16384a91a82453ad13144a79cc9b5b15750a4dc00d09030e9``.

A scientific receipt carries a 40-hex ``producer_code_sha`` which is the Git
blob SHA-1 of the exact producer bytes: SHA1(b"blob " + decimal_length + b"\\0"
+ raw_bytes). Verification resolves those exact bytes and recomputes the Git
blob identity. Authority-bearing dependency objects are canonical objects with
an ``object_role`` tag. OUTPUT, MANIFEST, REGISTRY and ACCESS_POLICY roles are
separate and may not share one identity; ordinary INPUT objects carry INPUT.
Receipt-shaped inputs/parents are recursively verified under receipt semantics.

Receipt identity is ``canonical_sha256`` over the full receipt body excluding
``receipt_sha256``. Declared digests are comparisons only; payload, producer
code, inputs, parents, output, manifest, registry and access-policy identities
are independently resolved/recomputed during verification.

Unified receipt identities use this explicit V1 domain and are not aliases for
old production-synthetic semantic identities.
"""
from __future__ import annotations

import hashlib
import math
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Callable

import numpy as np

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
_ROLE_BY_LABEL = {
    "input": "INPUT",
    "output": "OUTPUT",
    "manifest": "MANIFEST",
    "registry": "REGISTRY",
    "access": "ACCESS_POLICY",
}


class CanonicalError(ValueError):
    """Fail-closed error for invalid canonical or receipt input."""


@dataclass(frozen=True)
class VerifiedReceipt:
    receipt_sha256: str
    payload_sha256: str
    verified_parent_shas: tuple[str, ...]


def _norm_eol(value: str) -> str:
    return str.replace(str.replace(value, "\r\n", "\n"), "\r", "\n")


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


def _encode_float(value: float) -> str:
    if math.isnan(value) or math.isinf(value):
        raise CanonicalError("NaN/Inf are forbidden; None is the only missing value")
    return "0.0" if value == 0.0 else float.__repr__(value)


def _is_exact_numpy_scalar(value: object) -> bool:
    return isinstance(value, np.generic) and type(value) is value.dtype.type


def _encode(value: Any, out: list[str]) -> None:
    value_type = type(value)
    if value is None:
        out.append("null")
    elif value_type is bool:
        out.append("true" if value else "false")
    elif value_type is int:
        try:
            out.append(int.__str__(value))
        except ValueError as exc:
            raise CanonicalError("integer too large to serialize exactly") from exc
    elif value_type is float:
        out.append(_encode_float(value))
    elif value_type is str:
        out.append(_encode_string(value))
    elif _is_exact_numpy_scalar(value):
        if isinstance(value, np.bool_):
            out.append("true" if bool(value) else "false")
        elif isinstance(value, (np.datetime64, np.timedelta64)):
            raise CanonicalError(f"unsupported canonical type: {value_type.__name__}")
        elif isinstance(value, np.integer):
            try:
                out.append(str(int(value)))
            except ValueError as exc:
                raise CanonicalError("integer too large to serialize exactly") from exc
        elif isinstance(value, np.floating):
            if value.dtype.itemsize > 8:
                raise CanonicalError(f"numpy floating type wider than float64 is unsupported: {value.dtype}")
            out.append(_encode_float(float(value)))
        else:
            raise CanonicalError(f"unsupported canonical type: {value_type.__name__}")
    elif value_type is dict:
        normalized: dict[str, Any] = {}
        for key, item in dict.items(value):
            if type(key) is not str:
                raise CanonicalError("canonical mapping keys must be exact built-in strings")
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
    elif value_type in (list, tuple):
        out.append("[")
        for index, item in enumerate(value):
            if index:
                out.append(",")
            _encode(item, out)
        out.append("]")
    else:
        raise CanonicalError(f"unsupported canonical type or subclass: {value_type.__name__}")


def canonical_bytes(payload: Mapping[str, object] | object) -> bytes:
    out: list[str] = []
    try:
        _encode(payload, out)
        return "".join(out).encode("utf-8")
    except (RecursionError, UnicodeEncodeError) as exc:
        raise CanonicalError("payload is not canonically serializable") from exc


def canonical_sha256(payload: Mapping[str, object] | object) -> str:
    return hashlib.sha256(_CANONICAL_DOMAIN + canonical_bytes(payload)).hexdigest()


def _git_blob_sha1(raw: bytes) -> str:
    if type(raw) is not bytes:
        raise CanonicalError("producer code must resolve to exact bytes")
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()


def _is_hex(value: object, length: int) -> bool:
    return type(value) is str and len(value) == length and set(value) <= _HEX


def _require_hex(name: str, value: object, length: int) -> None:
    if not _is_hex(value, length):
        raise CanonicalError(f"{name} must be lowercase {length}-hex")


def _normalize_hash_list(name: str, values: object) -> list[str]:
    if type(values) is not list:
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
    if type(payload) is not dict:
        raise CanonicalError("payload must be an exact built-in mapping")
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


def _verify_dependency(
    label: str,
    expected_sha: str,
    resolved: object,
    object_resolver: Callable[[str], object | None],
    stack: frozenset[str],
) -> None:
    if resolved is None:
        raise CanonicalError(f"{label} object unavailable: {expected_sha}")
    if isinstance(resolved, Mapping) and resolved.get("receipt_schema") == _RECEIPT_SCHEMA:
        if label != "input" and label != "parent":
            raise CanonicalError(f"{label} role cannot be filled by a scientific receipt")
        verified = verify_scientific_receipt(resolved, object_resolver, _stack=stack)
        if verified.receipt_sha256 != expected_sha:
            raise CanonicalError(f"{label} receipt identity mismatch")
        return
    if type(resolved) is not dict:
        raise CanonicalError(f"{label} object must be an exact built-in mapping")
    expected_role = _ROLE_BY_LABEL.get(label)
    if expected_role is not None and resolved.get("object_role") != expected_role:
        raise CanonicalError(f"{label} object role mismatch: expected {expected_role}")
    try:
        actual = canonical_sha256(resolved)
    except CanonicalError as exc:
        raise CanonicalError(f"{label} object is not canonically verifiable: {expected_sha}") from exc
    if actual != expected_sha:
        raise CanonicalError(f"{label} object digest mismatch")


def _reject_cross_role_identity_reuse(receipt: Mapping[str, object], inputs: list[str], parents: list[str]) -> None:
    roles: list[tuple[str, str]] = []
    roles.extend(("input", sha) for sha in inputs)
    roles.extend(("parent", sha) for sha in parents)
    roles.extend(
        (
            ("output", str(receipt["output_sha"])),
            ("manifest", str(receipt["manifest_sha"])),
            ("registry", str(receipt["registry_sha"])),
            ("access", str(receipt["access_policy_sha"])),
        )
    )
    seen: dict[str, str] = {}
    for role, sha in roles:
        prior = seen.get(sha)
        if prior is not None and prior != role:
            raise CanonicalError(f"one identity cannot fill distinct receipt roles: {prior} and {role}")
        seen[sha] = role


def verify_scientific_receipt(
    receipt: Mapping[str, object],
    object_resolver: Callable[[str], object | None],
    *,
    _stack: frozenset[str] | None = None,
) -> VerifiedReceipt:
    if type(receipt) is not dict:
        raise CanonicalError("receipt must be an exact built-in mapping")
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
    if type(receipt["payload"]) is not dict:
        raise CanonicalError("payload must be an exact built-in mapping")
    actual_payload = canonical_sha256(receipt["payload"])
    if actual_payload != receipt["payload_sha256"]:
        raise CanonicalError("payload digest mismatch")
    actual_receipt = canonical_sha256(_receipt_body(receipt))
    if actual_receipt != receipt["receipt_sha256"]:
        raise CanonicalError("receipt digest mismatch")

    producer_sha = str(receipt["producer_code_sha"])
    producer_bytes = object_resolver(producer_sha)
    if producer_bytes is None:
        raise CanonicalError("producer code object unavailable")
    if _git_blob_sha1(producer_bytes) != producer_sha:
        raise CanonicalError("producer code identity mismatch")

    _reject_cross_role_identity_reuse(receipt, inputs, parents)

    receipt_sha = str(receipt["receipt_sha256"])
    stack = _stack or frozenset()
    if receipt_sha in stack:
        raise CanonicalError("parent receipt cycle detected")
    next_stack = stack | {receipt_sha}

    for input_sha in inputs:
        _verify_dependency("input", input_sha, object_resolver(input_sha), object_resolver, next_stack)

    dependency_fields = (
        ("output", str(receipt["output_sha"])),
        ("manifest", str(receipt["manifest_sha"])),
        ("registry", str(receipt["registry_sha"])),
        ("access", str(receipt["access_policy_sha"])),
    )
    for label, dependency_sha in dependency_fields:
        _verify_dependency(label, dependency_sha, object_resolver(dependency_sha), object_resolver, next_stack)

    verified_parents: list[str] = []
    for parent_sha in parents:
        parent = object_resolver(parent_sha)
        if parent is None:
            raise CanonicalError(f"parent receipt unavailable: {parent_sha}")
        if type(parent) is not dict:
            raise CanonicalError("parent receipt must resolve to an exact built-in mapping")
        verified = verify_scientific_receipt(parent, object_resolver, _stack=next_stack)
        if verified.receipt_sha256 != parent_sha:
            raise CanonicalError("parent receipt identity mismatch")
        verified_parents.append(parent_sha)

    return VerifiedReceipt(receipt_sha, actual_payload, tuple(verified_parents))
