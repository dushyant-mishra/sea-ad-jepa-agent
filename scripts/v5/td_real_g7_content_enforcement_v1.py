"""Real Target Discovery G7: content-level E3 biological-evidence rights validator.

Implements the *content* semantics mandated by V3.1.1 E3. This is a
fixture-only candidate for the real G7 validation path, NOT independent
attestation of the producer, protected outcomes, references or same-code-path
qualification. It does not replace the accepted G7 V3 source-aware decision
law. Never promote the result to HUMAN_EXECUTABLE.
"""
from __future__ import annotations

import hashlib
import json
import math
import re

from scripts.v5.td_real_evidence_ladder_contract_v1 import derive_evidence_ladder

RIGHTS_TOKEN_SCHEMA = "JEPA_TD_REAL_G7_EVIDENCE_RIGHTS_TOKEN_V1"
_ALLOWED_ATOM_STATES = frozenset({
    "MEASURED_SCALAR", "STRUCTURALLY_UNMEASURED",
    "MEASURED_COLLISION_UNRESOLVED", "WITHHELD_BY_EVIDENCE_RIGHTS",
})
_RAW_STATES = _ALLOWED_ATOM_STATES - {"WITHHELD_BY_EVIDENCE_RIGHTS"}
_ATOM_KEYS = frozenset({
    "atom_id", "source", "donor_id", "right", "state", "count", "library_size"
})
_TOKEN_KEYS = frozenset({
    "schema", "candidate_id", "level_id", "evidence_rights",
    "manifest_sha256", "full_atoms_sha256"
})
_LEVEL_KEYS = frozenset({"level_id", "rights_token", "atoms"})
_PINS_KEYS = frozenset({
    "manifest_sha256", "full_atoms_sha256",
    "token_sha256_by_level", "atoms_sha256_by_level"
})
_HEX = re.compile(r"^[a-f0-9]{64}$")


class G7ContentError(ValueError):
    """Untrusted or inconsistent evidence-rights content."""


def _strict_json(obj):
    """Reject polymorphic equality, ambiguous keys and nonfinite JSON."""
    if obj is None or type(obj) in (bool, int, str):
        if type(obj) is str:
            if any(0xD800 <= ord(c) <= 0xDFFF for c in obj):
                raise G7ContentError("surrogate string is not canonical evidence")
        return
    if type(obj) is float:
        if not math.isfinite(obj):
            raise G7ContentError("nonfinite number in evidence")
        return
    if type(obj) is list:
        for item in obj:
            _strict_json(item)
        return
    if type(obj) is dict:
        for k, v in obj.items():
            if type(k) is not str:
                raise G7ContentError("evidence JSON keys must be exact strings")
            _strict_json(k)
            _strict_json(v)
        return
    raise G7ContentError("evidence includes noncanonical Python type")


def _bytes(obj):
    _strict_json(obj)
    try:
        return json.dumps(
            obj, sort_keys=True, separators=(",", ":"),
            ensure_ascii=False, allow_nan=False
        ).encode("utf-8")
    except (ValueError, UnicodeError, TypeError, OverflowError):
        raise G7ContentError("could not canonicalize evidence") from None


def canonical_sha256(obj) -> str:
    """Domain-local canonical JSON SHA-256 for fixture content verification."""
    return hashlib.sha256(_bytes(obj)).hexdigest()


def _digest(value, label):
    if type(value) is not str or not _HEX.fullmatch(value):
        raise G7ContentError(label + " requires exact lowercase SHA-256")
    return value


def _token(value, label):
    if (type(value) is not str or not value
            or value != value.strip() or "\x00" in value):
        raise G7ContentError(label + " requires canonical nonempty string")
    return value


def _same_bytes(a, b) -> bool:
    return _bytes(a) == _bytes(b)


def _atom(raw, *, full, full_rights):
    if type(raw) is not dict or set(raw) != _ATOM_KEYS:
        raise G7ContentError("evidence atom fields are not exact")
    a = dict(raw)
    for field in ("atom_id", "source", "donor_id", "right"):
        _token(a[field], field)
    if a["right"] not in full_rights:
        raise G7ContentError("evidence right not part of frozen ladder")
    state = a["state"]
    if type(state) is not str or state not in _ALLOWED_ATOM_STATES:
        raise G7ContentError("unknown or invalid four-state evidence state")
    if full and state not in _RAW_STATES:
        raise G7ContentError("full source cannot contain rights-withheld measurement")
    if state == "MEASURED_SCALAR":
        if (type(a["count"]) is not int or a["count"] < 0
                or type(a["library_size"]) is not int
                or a["library_size"] < a["count"]):
            raise G7ContentError("measured scalar requires intact nonnegative count/library")
    elif a["count"] is not None or a["library_size"] is not None:
        raise G7ContentError("non-scalar state cannot expose count/library")
    return a


def _atoms(rows, *, full, full_rights):
    if type(rows) is not list or not rows:
        raise G7ContentError("evidence atoms must form a nonempty materialized list")
    out = {}
    for raw in rows:
        a = _atom(raw, full=full, full_rights=full_rights)
        identity = a["atom_id"]
        if identity in out:
            raise G7ContentError("duplicate scientific atom identity")
        out[identity] = a
    return out


def validate_g7_e3_content(*, manifest, full_atoms, levels, expected_pins):
    """Enforce rights semantics using actual atom content, not declared labels.

    `expected_pins` must ultimately come from a qualified independent producer.
    This function checks their consistency but CANNOT authenticate their issuer.
    A caller able to substitute the full source and the pins can still forge
    fixture-consistent inputs. Thus it deliberately returns no human/same-code
    path authority and does not expose the underlying values.
    """
    if type(manifest) is not dict:
        raise G7ContentError("frozen manifest must be an exact mapping")
    _strict_json(manifest)
    ladder = derive_evidence_ladder(manifest)
    if ladder["status"] != "EVIDENCE_LADDER_FROZEN":
        raise G7ContentError("G7 terminal ladder must have three or more rights levels")
    if type(expected_pins) is not dict or set(expected_pins) != _PINS_KEYS:
        raise G7ContentError("exact independently pinned evidence identifiers required")
    if type(levels) is not list or len(levels) != len(ladder["levels"]):
        raise G7ContentError("every frozen evidence level must be materialized")
    for key in ("manifest_sha256", "full_atoms_sha256"):
        _digest(expected_pins[key], key)
    if canonical_sha256(manifest) != expected_pins["manifest_sha256"]:
        raise G7ContentError("manifest does not match frozen identifier")
    if canonical_sha256(full_atoms) != expected_pins["full_atoms_sha256"]:
        raise G7ContentError("full observation content does not match frozen identifier")
    ids = [x["level_id"] for x in ladder["levels"]]
    rights = ladder["full_evidence_rights"]
    base = _atoms(full_atoms, full=True, full_rights=set(rights))
    for field in ("token_sha256_by_level", "atoms_sha256_by_level"):
        m = expected_pins[field]
        if type(m) is not dict or set(m) != set(ids):
            raise G7ContentError("one exact content digest required for every level")
        for digest in m.values():
            _digest(digest, field)

    counts = {}
    previous_visible = {}
    for level_data, frozen_level in zip(levels, ladder["levels"]):
        if type(level_data) is not dict or set(level_data) != _LEVEL_KEYS:
            raise G7ContentError("evidence package level fields are not exact")
        level_id = frozen_level["level_id"]
        if level_data["level_id"] != level_id or type(level_data["level_id"]) is not str:
            raise G7ContentError("evidence-level order/identity differs from frozen ladder")
        token = level_data["rights_token"]
        if type(token) is not dict or set(token) != _TOKEN_KEYS:
            raise G7ContentError("rights token fields are not exact")
        expected_token = {
            "schema": RIGHTS_TOKEN_SCHEMA,
            "candidate_id": ladder["candidate_id"],
            "level_id": level_id,
            "evidence_rights": frozen_level["evidence_rights"],
            "manifest_sha256": expected_pins["manifest_sha256"],
            "full_atoms_sha256": expected_pins["full_atoms_sha256"],
        }
        if not _same_bytes(token, expected_token):
            raise G7ContentError("rights token content differs from frozen manifest")
        if canonical_sha256(token) != expected_pins["token_sha256_by_level"][level_id]:
            raise G7ContentError("rights token content SHA does not match pinned token")
        atoms = level_data["atoms"]
        if canonical_sha256(atoms) != expected_pins["atoms_sha256_by_level"][level_id]:
            raise G7ContentError("level evidence bytes differ from pinned content")
        seen = _atoms(atoms, full=False, full_rights=set(rights))
        if set(seen) != set(base):
            raise G7ContentError("atom roster changed under biological-right restriction")
        allowed = set(frozen_level["evidence_rights"])
        visible = {}
        for atom_id, original in base.items():
            actual = seen[atom_id]
            for key in ("atom_id", "source", "donor_id", "right"):
                if type(actual[key]) is not str or actual[key] != original[key]:
                    raise G7ContentError("atom identity or evidence-right class swapped")
            if original["state"] != "MEASURED_SCALAR":
                if not _same_bytes(actual, original):
                    raise G7ContentError("structural/unresolved support cannot be withheld or recoded")
            elif original["right"] in allowed:
                if not _same_bytes(actual, original):
                    raise G7ContentError("biological rights cannot thin count, depth or visible bytes")
                visible[atom_id] = _bytes(actual)
            elif (
                actual["state"] != "WITHHELD_BY_EVIDENCE_RIGHTS"
                or actual["count"] is not None
                or actual["library_size"] is not None
            ):
                raise G7ContentError("hidden scalar must carry distinct withheld state and no values")
            if atom_id in previous_visible and visible.get(atom_id) != previous_visible[atom_id]:
                raise G7ContentError("previously visible atom changed or was removed")
        counts[level_id] = len(visible)
        previous_visible = visible
    # Deliberate nonpromotion: hashes bind bytes, NOT issuer/producer trust.
    return {
        "schema": "JEPA_TD_REAL_G7_E3_CONTENT_CHECK_V1",
        "status": "E3_CONTENT_MECHANICS_VERIFIED_FIXTURE_ONLY",
        "visible_by_level": counts,
        "manifest_sha256": expected_pins["manifest_sha256"],
        "full_atoms_sha256": expected_pins["full_atoms_sha256"],
        "externally_authenticated": False,
        "same_code_path_authorized": False,
        "human_g7_authorized": False,
        "authority_effect": "NONE",
    }
