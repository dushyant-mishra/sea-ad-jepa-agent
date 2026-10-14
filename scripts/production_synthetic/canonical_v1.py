"""Canonical identity and serialization contract for production synthetic V3.1.1.

Implements V3.1 section 3: every identity-bearing artifact has a raw-byte
SHA-256 and a semantic SHA-256 computed from a canonical serialization.

Contract (each decision is a single authority; nothing else in the package may
redefine it):

1. ``raw_sha256(data)``: plain SHA-256 hex of the exact bytes. Only ``bytes``
   is accepted; ``str``, ``bytearray`` and ``memoryview`` are rejected rather
   than silently encoded.
2. ``canonical_json_bytes(obj)``: UTF-8, mapping keys sorted by Unicode code
   point, compact separators, no trailing newline.
   - Mapping keys must be ``str`` (anything else, including bool, is rejected).
   - ``bool`` is never an int; ``True`` -> ``true``.
   - ``None`` -> ``null`` is the ONLY missing-value representation. A measured
     zero (``0`` / ``0.0``) is never ``null``.
   - NaN and +/-Inf are REJECTED, never mapped to ``null``.
   - Python ints are exact (arbitrary precision).
   - Floats use shortest round-trip ``repr``; ``-0.0`` is normalized to
     ``0.0``. An integer-valued float stays a float (``1.0`` != ``1``).
   - numpy integer / floating / bool scalars convert to the Python equivalent
     (a numpy float is widened to float64 first, so float32 0.1 serializes as
     its float64 value). numpy arrays are rejected.
   - Sequences: lists and tuples are both arrays (tuple == list); list order is
     significant. Sets, frozensets, bytes, complex and any other type are
     rejected.
   - String values and keys: CRLF and lone CR are normalized to LF. No Unicode
     normalization (NFC/NFD) is applied; identifiers stay exact. Keys that
     collide after line-ending normalization are rejected.
   - Every rejection raises ``CanonicalError``.
3. ``semantic_sha256(obj)``: SHA-256 over a domain prefix + canonical bytes, so
   a semantic identity can never equal the raw identity of the same bytes.
   If ``obj`` is ``bytes`` it is a UTF-8 text artifact: strict decode, strip
   one leading BOM, normalize CRLF/CR to LF, then hash under a distinct text
   domain prefix (line-ending-equivalent text shares a semantic identity while
   raw hashes differ). Other objects hash under the JSON domain prefix.
4. ``ordered_registry_digest(rows, identity_keys)``: ORDER-SENSITIVE digest of a
   registry (positional index semantics). Binds row count, identity keys and
   each row's canonical content, in the given order. Rejects empty registries,
   empty/duplicated/missing identity keys, missing-valued (``None``) identity
   values and duplicate identity tuples. Reordering rows changes the digest.
5. ``semantic_row_set_sha256(rows, identity_keys)``: ORDER-INVARIANT identity of
   a row set (the one helper beyond the four core interfaces). Rows are sorted
   by the canonical encoding of their identity tuple, so permuted rows or
   shards concatenated in any order give the same identity; any value change,
   addition or removal changes it. Own domain prefix; same rejections as (4).
"""
from __future__ import annotations

import hashlib
import math
from collections.abc import Mapping
from typing import Any, Iterable, Sequence

import numpy as np

__all__ = [
    "CanonicalError",
    "canonical_json_bytes",
    "raw_sha256",
    "semantic_sha256",
    "ordered_registry_digest",
    "semantic_row_set_sha256",
]

_JSON_DOMAIN = b"JEPA-PRODUCTION-SYNTHETIC-SEMANTIC-V1\x00"
_TEXT_DOMAIN = b"JEPA-PRODUCTION-SYNTHETIC-SEMANTIC-TEXT-V1\x00"
_REGISTRY_DOMAIN = b"JEPA-PRODUCTION-SYNTHETIC-ORDERED-REGISTRY-V1\x00"
_ROWSET_DOMAIN = b"JEPA-PRODUCTION-SYNTHETIC-ROW-SET-V1\x00"
_BOM = "﻿"


class CanonicalError(ValueError):
    """Raised for any input the canonical contract rejects."""


def _norm_eol(s: str) -> str:
    return s.replace("\r\n", "\n").replace("\r", "\n")


def _enc_str(s: str) -> str:
    out = ['"']
    for ch in s:
        o = ord(ch)
        if ch == '"':
            out.append('\\"')
        elif ch == "\\":
            out.append("\\\\")
        elif ch == "\n":
            out.append("\\n")
        elif ch == "\t":
            out.append("\\t")
        elif ch == "\r":
            out.append("\\r")
        elif ch == "\b":
            out.append("\\b")
        elif ch == "\f":
            out.append("\\f")
        elif o < 0x20:
            out.append("\\u%04x" % o)
        else:
            out.append(ch)
    out.append('"')
    return "".join(out)


def _enc_float(x: float) -> str:
    if math.isnan(x) or math.isinf(x):
        raise CanonicalError("NaN/Inf are not representable; None is the only missing value")
    if x == 0.0:
        return "0.0"  # normalizes -0.0
    return repr(float(x))


def _enc(obj: Any, out: list) -> None:
    # bool before int: bool is a subclass of int but is never an integer here.
    if obj is None:
        out.append("null")
    elif isinstance(obj, (bool, np.bool_)):
        out.append("true" if bool(obj) else "false")
    elif isinstance(obj, (int, np.integer)):
        out.append(str(int(obj)))
    elif isinstance(obj, (float, np.floating)):
        out.append(_enc_float(float(obj)))
    elif isinstance(obj, str):
        out.append(_enc_str(_norm_eol(obj)))
    elif isinstance(obj, Mapping):
        items = {}
        for k, v in obj.items():
            if not isinstance(k, str):
                raise CanonicalError(f"mapping keys must be str, got {type(k).__name__}")
            nk = _norm_eol(k)
            if nk in items:
                raise CanonicalError(f"mapping keys collide after normalization: {nk!r}")
            items[nk] = v
        out.append("{")
        first = True
        for k in sorted(items):
            if not first:
                out.append(",")
            first = False
            out.append(_enc_str(k))
            out.append(":")
            _enc(items[k], out)
        out.append("}")
    elif isinstance(obj, (list, tuple)):
        out.append("[")
        for i, v in enumerate(obj):
            if i:
                out.append(",")
            _enc(v, out)
        out.append("]")
    else:
        raise CanonicalError(f"unsupported type for canonical serialization: {type(obj).__name__}")


def canonical_json_bytes(obj: Any) -> bytes:
    """Canonical UTF-8 JSON bytes of ``obj`` (see module docstring)."""
    out: list = []
    try:
        _enc(obj, out)
        return "".join(out).encode("utf-8")
    except RecursionError as exc:
        raise CanonicalError("object too deeply nested or cyclic") from exc
    except UnicodeEncodeError as exc:
        raise CanonicalError(f"string is not valid Unicode text: {exc}") from exc


def raw_sha256(data: bytes) -> str:
    """SHA-256 hex of the exact bytes."""
    if not isinstance(data, bytes):
        raise CanonicalError(f"raw_sha256 requires bytes, got {type(data).__name__}")
    return hashlib.sha256(data).hexdigest()


def semantic_sha256(obj: Any) -> str:
    """Domain-separated SHA-256 of the canonical serialization of ``obj``."""
    if isinstance(obj, bytes):
        try:
            text = obj.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise CanonicalError(f"text artifact is not valid UTF-8: {exc}") from exc
        if text.startswith(_BOM):
            text = text[len(_BOM):]
        payload = _norm_eol(text).encode("utf-8")
        domain = _TEXT_DOMAIN
    else:
        payload = canonical_json_bytes(obj)
        domain = _JSON_DOMAIN
    return hashlib.sha256(domain + payload).hexdigest()


def _check_keys(identity_keys: Sequence[str]) -> list:
    if isinstance(identity_keys, (str, bytes)) or not isinstance(identity_keys, (list, tuple)):
        raise CanonicalError("identity_keys must be a list/tuple of key names")
    keys = list(identity_keys)
    if not keys:
        raise CanonicalError("identity_keys must be non-empty")
    if any(not isinstance(k, str) for k in keys):
        raise CanonicalError("identity_keys must all be str")
    if len(set(keys)) != len(keys):
        raise CanonicalError("identity_keys must be unique")
    return keys


def _identity_bytes(row: Any, keys: list, pos: int) -> bytes:
    if not isinstance(row, Mapping):
        raise CanonicalError(f"row {pos} is not a mapping")
    ident = []
    for k in keys:
        if k not in row:
            raise CanonicalError(f"row {pos} is missing identity key {k!r}")
        v = row[k]
        if v is None:
            raise CanonicalError(f"row {pos} has a missing value for identity key {k!r}")
        ident.append(v)
    return canonical_json_bytes(ident)


def _frame(b: bytes) -> bytes:
    return len(b).to_bytes(8, "big") + b


def ordered_registry_digest(rows: Iterable[Mapping], identity_keys: Sequence[str]) -> str:
    """Order-sensitive digest of a registry (reordering changes the digest)."""
    keys = _check_keys(identity_keys)
    body = hashlib.sha256()
    seen = set()
    n = 0
    for pos, row in enumerate(rows):
        ident = _identity_bytes(row, keys, pos)
        if ident in seen:
            raise CanonicalError(f"duplicate identity at row {pos}: {ident.decode('utf-8')}")
        seen.add(ident)
        body.update(_frame(canonical_json_bytes(row)))
        n += 1
    if n == 0:
        raise CanonicalError("registry must be non-empty")
    header = canonical_json_bytes({"identity_keys": keys, "n_rows": n})
    return hashlib.sha256(_REGISTRY_DOMAIN + _frame(header) + body.digest()).hexdigest()


def semantic_row_set_sha256(rows: Iterable[Mapping], identity_keys: Sequence[str]) -> str:
    """Order-invariant identity of a row set keyed by ``identity_keys``."""
    keys = _check_keys(identity_keys)
    entries = {}
    for pos, row in enumerate(rows):
        ident = _identity_bytes(row, keys, pos)
        if ident in entries:
            raise CanonicalError(f"duplicate identity at row {pos}: {ident.decode('utf-8')}")
        entries[ident] = canonical_json_bytes(row)
    if not entries:
        raise CanonicalError("row set must be non-empty")
    body = hashlib.sha256()
    for ident in sorted(entries):
        body.update(_frame(ident))
        body.update(_frame(entries[ident]))
    header = canonical_json_bytes({"identity_keys": keys, "n_rows": len(entries)})
    return hashlib.sha256(_ROWSET_DOMAIN + _frame(header) + body.digest()).hexdigest()
