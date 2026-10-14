r"""Canonical identity and serialization contract for production synthetic V3.1.1.

Implements V3.1 section 3: every identity-bearing artifact has a raw-byte
SHA-256 and a semantic SHA-256 computed from a canonical serialization.

This docstring is a byte-level specification: a second implementation that
follows it must reproduce every digest bit for bit. Each decision is a single
authority; nothing else in the package may redefine it. All digests are
lowercase hex SHA-256. ``||`` is byte concatenation.

Public functions: ``canonical_json_bytes``, ``raw_sha256``, ``semantic_sha256``,
``ordered_registry_digest`` (the four core interfaces) plus these extras:
``semantic_row_set_sha256``, ``load_canonical_json``, ``semantic_text_sha256``
and ``semantic_json_file_sha256``. ``CanonicalError`` (a ``ValueError``) is
raised for every rejection.

1. CANONICAL JSON BYTES (``canonical_json_bytes``)
   Output is UTF-8 with no BOM, no insignificant whitespace (separators are
   exactly "," and ":") and no trailing newline.
   - null: ``None`` -> ``null``. This is the ONLY missing-value representation.
     A measured zero is never null. NaN and +/-Inf are REJECTED.
   - bool: ``true`` / ``false`` (Python bool and numpy bool_). A bool is never
     an integer.
   - int: decimal digits with optional leading "-", no "+", no leading zeros,
     exact (arbitrary precision) up to the interpreter's int-to-str digit limit
     (4300 digits by default); larger ints are rejected, never truncated.
     numpy integer scalars convert to Python int.
   - float: take float64, replace -0.0 by 0.0, then write Python 3 ``repr`` of
     that float64 (shortest round-trip). Exponent form is used by ``repr`` when
     the decimal exponent is < -4 or >= 16 and is written like ``1e+16``,
     ``1e-05``, ``5e-324``, ``1.5e+300`` (always a sign and at least two
     exponent digits; NO ".0" is inserted before an exponent). Otherwise
     positional form is used and an integer-valued float keeps its ".0"
     (``1.0``, ``100000.0``, ``0.0``). So ``1.0`` and ``1`` are different
     bytes. numpy float16/float32 are widened to float64 first (float32 0.1
     writes as 0.10000000149011612); numpy floating types wider than 8 bytes
     (longdouble where it is wider than float64) are REJECTED.
   - str: line endings are normalized first (CRLF -> LF, then lone CR -> LF);
     NO Unicode normalization (NFC/NFD) is applied, identifiers stay exact.
     The string is written between double quotes with exactly this escape
     table: ``"`` -> ``\"``; ``\`` -> ``\\``; LF -> ``\n``; TAB -> ``\t``;
     BS (0x08) -> ``\b``; FF (0x0c) -> ``\f``; every other code point below
     0x20 -> ``\u`` followed by four LOWERCASE hex digits (e.g. ``\u0000``,
     ``\u001f``; CR can never occur after normalization). DEL (0x7f) and all
     non-ASCII code points are written raw as UTF-8 (no ``\u`` escapes, no
     surrogate pairs). "/" is not escaped. Lone surrogates are rejected.
   - mapping: keys must be ``str`` (anything else, including bool, is
     rejected); keys are line-ending-normalized with the same rule and keys
     that collide after normalization are rejected. Members are emitted sorted
     by key in Unicode code point order (Python ``str`` ordering). This is NOT
     RFC 8785 / JCS ordering, which sorts by UTF-16 code unit and differs for
     code points above U+FFFF. Format: ``{key:value,key:value}``.
   - list and tuple: both are arrays, ``[v,v]``, order is significant. A tuple
     is indistinguishable from a list.
   - Rejected types: set, frozenset, bytes/bytearray, complex, numpy arrays,
     numpy datetime64/timedelta64 (incl. NaT), and any other object.

2. RAW IDENTITY: ``raw_sha256(data)`` = SHA-256(data) of the exact bytes. Only
   ``bytes`` is accepted; ``str``, ``bytearray`` and ``memoryview`` are
   rejected rather than silently encoded.

3. SEMANTIC IDENTITIES. Each kind has its own literal domain prefix (bytes,
   including the trailing NUL) so no semantic identity can equal a raw one, and
   no two kinds can collide:
     JSON domain    = b"JEPA-PRODUCTION-SYNTHETIC-SEMANTIC-V1\x00"
     TEXT domain    = b"JEPA-PRODUCTION-SYNTHETIC-SEMANTIC-TEXT-V1\x00"
     REGISTRY domain= b"JEPA-PRODUCTION-SYNTHETIC-ORDERED-REGISTRY-V1\x00"
     ROW-SET domain = b"JEPA-PRODUCTION-SYNTHETIC-ROW-SET-V1\x00"
   - ``semantic_sha256(obj)`` = SHA-256(JSON domain || canonical_json_bytes(obj)).
     There is NO type dispatch: ``bytes`` input is REJECTED. Use one of the two
     explicit entry points below for file artifacts.
   - ``semantic_text_sha256(raw)`` (text artifacts, e.g. TSV/CSV/Markdown):
     strict UTF-8 decode, strip ONE leading U+FEFF, CRLF -> LF then lone
     CR -> LF, re-encode UTF-8; digest = SHA-256(TEXT domain || those bytes).
   - ``semantic_json_file_sha256(raw)`` (JSON file artifacts) =
     ``semantic_sha256(load_canonical_json(raw))``. Whitespace, line-ending,
     BOM and key-order variants of the same JSON share this identity, while
     their raw hashes and ``semantic_text_sha256`` values differ.

4. STRICT LOADER (``load_canonical_json(data: bytes)``): parses UTF-8 JSON (one
   leading BOM stripped) and rejects duplicate object keys (also keys that
   collide after CRLF/CR -> LF normalization), NaN/Infinity/-Infinity,
   overflowing floats (1e999), trailing garbage, non-bytes input, lone-surrogate
   strings, and nonzero float literals that underflow to 0.0 (a nonzero value
   must never become a measured zero; a literal whose mantissa is all zeros,
   e.g. 0e-400 or -0.0, is a true zero and is accepted). Other nonzero
   literals parse as float64, so excess digits or subnormal rounding
   (0.10000000000000000001 -> 0.1) are accepted as ordinary float64 rounding,
   never to zero. Ints parse exactly; floats parse as float.

5. FRAMING AND IDENTITY KEYS (used by both row digests below).
   frame(b) = len(b) as 8-byte big-endian unsigned || b.
   ``identity_keys`` must be a non-empty list/tuple of unique ``str`` names
   (not a bare string). Names are line-ending-normalized like row keys, must
   stay unique after normalization, and are then SORTED by code point, so
   ["a", "b"] and ["b", "a"] give the same digest. Every row must be a mapping
   containing every identity key with a non-None value (``None`` can never be
   an identity). identity_bytes(row) = canonical_json_bytes([row[k] for k in
   sorted identity keys]). Duplicate identity_bytes are rejected. ``rows`` must
   be a non-empty iterable of mappings (None / a number is rejected).
   header = canonical_json_bytes({"identity_keys": <sorted keys>,
   "n_rows": <row count>}).

6. ``ordered_registry_digest(rows, identity_keys)``: ORDER-SENSITIVE (positional
   index semantics; a consistent reordering MUST change it).
   body = SHA-256 over, for each row in the GIVEN order,
          frame(canonical_json_bytes(row))        (raw 32-byte digest)
   digest = SHA-256(REGISTRY domain || frame(header) || body).

7. ``semantic_row_set_sha256(rows, identity_keys)``: ORDER-INVARIANT identity of a
   row set (permuted rows, or shards concatenated in any order, give the same
   value; any value change, addition or removal changes it). Entries
   (identity_bytes, canonical_json_bytes(row)) are sorted BYTEWISE (unsigned
   byte order) by identity_bytes.
   body = SHA-256 over, for each entry in that order,
          frame(identity_bytes) || frame(row_bytes)   (raw 32-byte digest)
   digest = SHA-256(ROW-SET domain || frame(header) || body).
"""
from __future__ import annotations

import hashlib
import json
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
    "load_canonical_json",
    "semantic_text_sha256",
    "semantic_json_file_sha256",
]

_JSON_DOMAIN = b"JEPA-PRODUCTION-SYNTHETIC-SEMANTIC-V1\x00"
_TEXT_DOMAIN = b"JEPA-PRODUCTION-SYNTHETIC-SEMANTIC-TEXT-V1\x00"
_REGISTRY_DOMAIN = b"JEPA-PRODUCTION-SYNTHETIC-ORDERED-REGISTRY-V1\x00"
_ROWSET_DOMAIN = b"JEPA-PRODUCTION-SYNTHETIC-ROW-SET-V1\x00"
_BOM = chr(0xFEFF)  # U+FEFF byte order mark


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
    elif isinstance(obj, (np.datetime64, np.timedelta64)):
        raise CanonicalError(f"unsupported type for canonical serialization: {type(obj).__name__}")
    elif isinstance(obj, (int, np.integer)):
        try:
            out.append(str(int(obj)))
        except ValueError as exc:  # interpreter int->str digit limit
            raise CanonicalError("integer too large to serialize exactly") from exc
    elif isinstance(obj, (float, np.floating)):
        if isinstance(obj, np.floating) and obj.dtype.itemsize > 8:
            raise CanonicalError(f"numpy floating type wider than float64 is not supported: {obj.dtype}")
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
    if isinstance(obj, (bytes, bytearray, memoryview)):
        raise CanonicalError(
            "semantic_sha256 does not accept bytes; use semantic_text_sha256 or semantic_json_file_sha256"
        )
    return hashlib.sha256(_JSON_DOMAIN + canonical_json_bytes(obj)).hexdigest()


def semantic_text_sha256(raw: bytes) -> str:
    """Semantic identity of a UTF-8 text artifact (BOM and line endings normalized)."""
    if not isinstance(raw, bytes):
        raise CanonicalError(f"semantic_text_sha256 requires bytes, got {type(raw).__name__}")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise CanonicalError(f"text artifact is not valid UTF-8: {exc}") from exc
    if text.startswith(_BOM):
        text = text[len(_BOM):]
    try:
        payload = _norm_eol(text).encode("utf-8")
    except UnicodeEncodeError as exc:  # unreachable for strictly decoded input
        raise CanonicalError(f"text is not valid Unicode: {exc}") from exc
    return hashlib.sha256(_TEXT_DOMAIN + payload).hexdigest()


def semantic_json_file_sha256(raw: bytes) -> str:
    """Semantic identity of a JSON file artifact: semantic_sha256(load_canonical_json(raw))."""
    return semantic_sha256(load_canonical_json(raw))


def _check_keys(identity_keys: Sequence[str]) -> list:
    if isinstance(identity_keys, (str, bytes)) or not isinstance(identity_keys, (list, tuple)):
        raise CanonicalError("identity_keys must be a list/tuple of key names")
    keys = list(identity_keys)
    if not keys:
        raise CanonicalError("identity_keys must be non-empty")
    if any(not isinstance(k, str) for k in keys):
        raise CanonicalError("identity_keys must all be str")
    keys = [_norm_eol(k) for k in keys]  # row keys are normalized the same way
    if len(set(keys)) != len(keys):
        raise CanonicalError("identity_keys must be unique (after line-ending normalization)")
    return sorted(keys)  # key-name order must not matter


def _iter_rows(rows):
    try:
        return iter(rows)
    except TypeError as exc:
        raise CanonicalError(f"rows must be an iterable of mappings, got {type(rows).__name__}") from exc


def _identity_bytes(row: Any, keys: list, pos: int) -> bytes:
    if not isinstance(row, Mapping):
        raise CanonicalError(f"row {pos} is not a mapping")
    ident = []
    norm_row = {}
    for rk, rv in row.items():
        if not isinstance(rk, str):
            raise CanonicalError(f"row {pos} has a non-str key {type(rk).__name__}")
        norm_row[_norm_eol(rk)] = rv
    for k in keys:
        if k not in norm_row:
            raise CanonicalError(f"row {pos} is missing identity key {k!r}")
        v = norm_row[k]
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
    for pos, row in enumerate(_iter_rows(rows)):
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
    for pos, row in enumerate(_iter_rows(rows)):
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


def _no_dupes(pairs):
    d = {}
    seen = set()
    for k, v in pairs:
        nk = _norm_eol(k)
        if nk in seen:
            raise CanonicalError(f"duplicate JSON object key (after line-ending normalization): {k!r}")
        seen.add(nk)
        d[k] = v
    return d


def _check_strings(obj):
    """Reject lone surrogates anywhere in a parsed JSON tree (iterative)."""
    stack = [obj]
    while stack:
        o = stack.pop()
        if isinstance(o, str):
            try:
                o.encode("utf-8")
            except UnicodeEncodeError as exc:
                raise CanonicalError("JSON string contains a lone surrogate") from exc
        elif isinstance(o, dict):
            for k, v in o.items():
                stack.append(k)
                stack.append(v)
        elif isinstance(o, list):
            stack.extend(o)


def _bad_constant(name):
    raise CanonicalError(f"non-finite JSON constant rejected: {name}")


def _parse_float(text):
    x = float(text)
    if math.isinf(x):
        raise CanonicalError(f"float overflows to Inf: {text}")
    if x == 0.0 and any(c in "123456789" for c in text.lower().split("e")[0]):
        raise CanonicalError(f"nonzero float literal underflows to zero: {text}")
    return x


def load_canonical_json(data: bytes) -> Any:
    """Strictly parse a JSON artifact (see module docstring, item 5)."""
    if not isinstance(data, bytes):
        raise CanonicalError(f"load_canonical_json requires bytes, got {type(data).__name__}")
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise CanonicalError(f"JSON artifact is not valid UTF-8: {exc}") from exc
    if text.startswith(_BOM):
        text = text[len(_BOM):]
    try:
        obj = json.loads(
            text,
            object_pairs_hook=_no_dupes,
            parse_constant=_bad_constant,
            parse_float=_parse_float,
        )
        _check_strings(obj)
        return obj
    except CanonicalError:
        raise
    except (ValueError, RecursionError) as exc:
        raise CanonicalError(f"invalid JSON artifact: {exc}") from exc
