"""Fixture-only observation projection with *distinct* depth and library semantics.

Existing CaseBundle V1 and G7 V3 use `library_size` as physical-total-shaped
mass. PR474's `library_size` contains a different quantity: base-rights-
invariant normalization depth. Reusing the old field is scientifically
ambiguous and can either reject lawful richer teacher counts or leak q mass.

This V2 proposal does NOT change CaseBundle V1, G7, a production registry,
or the historical PR474 producer. Two SEPARATE public entry points return
only one rights-scoped view. The physical total stays in the caller's private
input; no physical total, its hash, or complete physical source artifact is
returned in either view. The interface itself cannot enforce external custody
or prevent a caller from passing the teacher view to the student.

At fixture scope this adapter requires exact equality between each cell's
physical total and the sum of fully mapped measured address counts. This
conservative rule rejects every possible off-ledger or collision residual,
rather than assuming that residual contains only lawful base molecules.
Even equality cannot authenticate the source or prove gene mapping, cellular
identity, donor identity, QC selection independence, or an issuer's rights.
The genuine production issuer and a reviewed V2 consumer are still absent.
"""
from __future__ import annotations

from scripts.v5.td_unified.q_excluded_depth_v1 import (
    MEASURED_SCALAR,
    QExcludedDepthNotEstimable,
    QExcludedObservationError,
    _snapshot,
    canonical_sha256,
    produce_rights_ladder_observations,
)

_SCHEMA = "TD_OBSERVATION_NORMALIZATION_VIEW_V2_FIXTURE"
_DEPTH_SEMANTICS = "BASE_RIGHTS_INVARIANT_NORMALIZATION_DEPTH_NOT_PHYSICAL_TOTAL"
_STUDENT = "STUDENT_BASE_RIGHTS"
_TEACHER = "TEACHER_RICHER_RIGHTS"
# Fixture contract only. A real issuer must bind source-specific rights separately.
_FIXTURE_BASE_EVIDENCE_RIGHTS = ("RNA:BASE",)


def _make_view(*, cells, address_rights, operator_states, ladder,
               query_address_id, view_kind):
    # Exact builtin-copy before *any* comparison or lookup. Do not evaluate
    # equality / formatting / repr on hostile caller-controlled subclasses.
    snap = _snapshot({
        "cells": cells, "address_rights": address_rights,
        "operator_states": operator_states, "ladder": ladder,
        "query_address_id": query_address_id,
    })
    q = snap["query_address_id"]
    if type(q) is not str or not q or q != q.strip() or any(ord(c) < 32 for c in q):
        raise QExcludedObservationError("query address must be an exact, trimmed nonempty string")
    rights = snap["address_rights"]
    levels = snap["ladder"]
    if type(rights) is not dict or q not in rights:
        raise QExcludedDepthNotEstimable("query address lacks a source-mapped rights entry")
    if type(levels) is not list or not levels:
        raise QExcludedObservationError("rights ladder missing")
    base = levels[0]
    if type(base) is not dict or type(base.get("evidence_rights")) is not list:
        raise QExcludedObservationError("base rights malformed")
    if base["evidence_rights"] != list(_FIXTURE_BASE_EVIDENCE_RIGHTS):
        raise QExcludedObservationError("fixture base rights differ from code-pinned V2 contract")
    if rights[q] in base["evidence_rights"]:
        raise QExcludedDepthNotEstimable("queried address is permitted at the student base level")

    # Reuse Macha's original exact source-to-rights-ladder producer, do not
    # define another synthetic biology, rights ladder, or target constructor.
    result = produce_rights_ladder_observations(
        cells=snap["cells"], address_rights=rights,
        operator_states=snap["operator_states"], ladder=levels,
    )
    # The fixture itself can check a *necessary* conservation property: all
    # mass represented by the source total must be accounted for as scalar
    # mapped counts. A positive residual cannot be assumed safe (unmapped q,
    # alias mass, unresolved collision). Even equality is not external proof.
    for cell in snap["cells"]:
        total = cell["library_total"]
        measured = sum(cell["counts"].values())
        if total != measured:
            raise QExcludedDepthNotEstimable(
                "unmapped or unresolved source library mass: cannot prove q-excluded depth")
    selected = result["levels"][0 if view_kind == _STUDENT else -1]
    rows = []
    for row in selected["rows"]:
        # A distinct covariate key is required: do not silently re-label it
        # `library_size`, whose V1 semantics enforce physical mass bounds.
        rows.append({
            "cell_id": row["cell_id"],
            "donor_id": row["donor_id"],
            "source_id": row["source_id"],
            "operator_id": row["operator_id"],
            "address_id": row["address_id"],
            "evidence_right": row["right"],
            "state": row["state"],
            "count": row["count"],
            "base_rights_normalization_depth": row["library_size"],
        })
    if view_kind == _STUDENT:
        for row in rows:
            if row["address_id"] == q and (
                row["state"] == MEASURED_SCALAR or
                row["count"] is not None or
                row["base_rights_normalization_depth"] is not None
            ):
                raise QExcludedObservationError("queried scalar reached student projection")
    payload = {
        "schema": _SCHEMA,
        "view_kind": view_kind,
        "authority_scope": "FIXTURE_ONLY",
        "query_address_id": q,
        "base_evidence_rights": list(_FIXTURE_BASE_EVIDENCE_RIGHTS),
        "reader_partition": "reader_fit",
        "depth_semantics": _DEPTH_SEMANTICS,
        "rows": rows,
        "source_authenticated": False,
        "donor_identity_authenticated": False,
        "physical_measurement_identity_authenticated": False,
        "q_rights_issuer_authenticated": False,
        "source_feature_mapping_authenticated": False,
        "external_truth_access_authorized": False,
        "same_code_path_authorized": False,
        "real_training_authorized": False,
        "authority_effect": "NONE",
    }
    # Only hash *published observable* bytes. Hashing the private input or
    # source physical total into a student-visible receipt would create an
    # avoidable information channel, even if it looked like provenance.
    return {**payload, "observable_sha256": canonical_sha256(payload)}


def produce_fixture_student_view_v2(*, cells, address_rights, operator_states,
                                    ladder, query_address_id):
    """Produce only the base-rights student view; no rich teacher rows."""
    return _make_view(
        cells=cells, address_rights=address_rights,
        operator_states=operator_states, ladder=ladder,
        query_address_id=query_address_id, view_kind=_STUDENT,
    )


def produce_fixture_teacher_view_v2(*, cells, address_rights, operator_states,
                                    ladder, query_address_id):
    """Produce only richer measured rows; caller must route privately."""
    return _make_view(
        cells=cells, address_rights=address_rights,
        operator_states=operator_states, ladder=ladder,
        query_address_id=query_address_id, view_kind=_TEACHER,
    )


def _view_snapshot(value, depth=0):
    """Copy published V2 receipts with exact JSON booleans for negative flags.

    The source-side PR474 input copier disallows bool, as it should for raw
    counts. The V2 *receipt* has explicit false issuer/training flags; never
    loosen the original producer's numeric acceptance to accommodate them.
    """
    if depth > 32:
        raise QExcludedObservationError("V2 receipt exceeds bounded nesting")
    kind = type(value)
    if value is None:
        return None
    if kind is str:
        if any(0xD800 <= ord(c) <= 0xDFFF for c in value):
            raise QExcludedObservationError("V2 receipt contains unpaired Unicode surrogate")
        return value
    if kind is int:
        if not -(2**53) < value < (2**53):
            raise QExcludedObservationError("V2 numeric field exceeds exact canonical domain")
        return value
    if kind is bool:
        return value
    if kind is list:
        return [_view_snapshot(item, depth + 1) for item in value]
    if kind is dict:
        out = {}
        for key, item in dict.items(value):
            if type(key) is not str:
                raise QExcludedObservationError("V2 keys must be exact strings")
            out[key] = _view_snapshot(item, depth + 1)
        return out
    raise QExcludedObservationError("V2 receipt has non-exact JSON evidence type")


_VIEW_KEYS = frozenset({
    "schema", "view_kind", "authority_scope", "query_address_id",
    "base_evidence_rights", "reader_partition", "depth_semantics", "rows",
    "source_authenticated", "donor_identity_authenticated",
    "physical_measurement_identity_authenticated", "q_rights_issuer_authenticated",
    "source_feature_mapping_authenticated", "external_truth_access_authorized",
    "same_code_path_authorized", "real_training_authorized",
    "authority_effect", "observable_sha256",
})
_ROW_KEYS = frozenset({
    "cell_id", "donor_id", "source_id", "operator_id",
    "address_id", "evidence_right", "state", "count",
    "base_rights_normalization_depth",
})
_STATES = frozenset({
    "MEASURED_SCALAR", "STRUCTURALLY_UNMEASURED",
    "MEASURED_COLLISION_UNRESOLVED", "WITHHELD_BY_EVIDENCE_RIGHTS",
})


def validate_fixture_observation_view_v2(view):
    """Independent V2 *shape* consumer; never infers an authenticated issuer.

    Explicitly does NOT enforce count <= depth or sum(count) <= depth.
    Those are physical-library properties, not rights-invariant covariate
    properties. A real human/scientific consumer requires a separate issued
    source artifact and a reviewed, authority-bearing contract.
    """
    value = _view_snapshot(view)
    if type(value) is not dict or set(value) != _VIEW_KEYS:
        raise QExcludedObservationError("V2 fixture view has unknown or missing fields")
    digest = value.pop("observable_sha256")
    if type(digest) is not str or len(digest) != 64 or not all(
        c in "0123456789abcdef" for c in digest
    ) or canonical_sha256(value) != digest:
        raise QExcludedObservationError("V2 observable content digest differs from exact view")
    if (value["schema"] != _SCHEMA or value["authority_scope"] != "FIXTURE_ONLY"
            or value["reader_partition"] != "reader_fit"
            or value["depth_semantics"] != _DEPTH_SEMANTICS
            or value["authority_effect"] != "NONE"
            or value["view_kind"] not in (_STUDENT, _TEACHER)):
        raise QExcludedObservationError("V2 fixture view cannot assume real or legacy authority")
    base_rights = value["base_evidence_rights"]
    if type(base_rights) is not list or base_rights != list(_FIXTURE_BASE_EVIDENCE_RIGHTS):
        raise QExcludedObservationError("V2 fixture base rights are not code-pinned")
    for key in (
        "source_authenticated", "donor_identity_authenticated",
        "physical_measurement_identity_authenticated",
        "q_rights_issuer_authenticated", "source_feature_mapping_authenticated",
        "external_truth_access_authorized", "same_code_path_authorized",
        "real_training_authorized",
    ):
        if value[key] is not False:
            raise QExcludedObservationError("V2 fixture observation has forbidden issuer claim")
    query = value["query_address_id"]
    if type(query) is not str or not query or query != query.strip():
        raise QExcludedObservationError("V2 fixture query address is malformed")
    rows = value["rows"]
    if type(rows) is not list or not rows:
        raise QExcludedObservationError("V2 fixture observations absent")
    seen, hierarchy, cell_depth, base_sum = set(), {}, {}, {}
    for row in rows:
        if type(row) is not dict or set(row) != _ROW_KEYS:
            raise QExcludedObservationError("V2 row cannot contain physical total or unknown field")
        for k in ("cell_id", "donor_id", "source_id", "operator_id",
                  "address_id", "evidence_right"):
            if type(row[k]) is not str or not row[k] or row[k] != row[k].strip():
                raise QExcludedObservationError("V2 row noncanonical address or source")
        identity = row["cell_id"], row["address_id"]
        if identity in seen:
            raise QExcludedObservationError("duplicate V2 cell-address row")
        seen.add(identity)
        h = row["donor_id"], row["source_id"], row["operator_id"]
        if row["cell_id"] in hierarchy and hierarchy[row["cell_id"]] != h:
            raise QExcludedObservationError("V2 cell switches source/donor/operator")
        hierarchy[row["cell_id"]] = h
        if type(row["state"]) is not str or row["state"] not in _STATES:
            raise QExcludedObservationError("V2 state unknown")
        depth, count = row["base_rights_normalization_depth"], row["count"]
        if row["state"] == MEASURED_SCALAR:
            if (type(count) is not int or count < 0 or
                    type(depth) is not int or depth <= 0):
                raise QExcludedObservationError("measured V2 row needs count and positive depth")
            if row["cell_id"] in cell_depth and cell_depth[row["cell_id"]] != depth:
                raise QExcludedObservationError("V2 base depth changes between addresses")
            cell_depth[row["cell_id"]] = depth
            if row["evidence_right"] in base_rights:
                base_sum[row["cell_id"]] = base_sum.get(row["cell_id"], 0) + count
            elif value["view_kind"] == _STUDENT:
                raise QExcludedObservationError("student view exposes a non-base evidence right")
        elif count is not None or depth is not None:
            raise QExcludedObservationError("V2 non-scalar row exposes count or depth")
        if value["view_kind"] == _STUDENT and row["address_id"] == query:
            if row["state"] == MEASURED_SCALAR:
                raise QExcludedObservationError("student view exposes queried scalar")
    for cell_id, depth in cell_depth.items():
        if base_sum.get(cell_id, 0) != depth:
            raise QExcludedObservationError(
                "V2 base depth must equal the published base-visible measured scalar sum"
            )
    return {
        "schema": "TD_OBSERVATION_VIEW_V2_FIXTURE_VALIDATION_RECEIPT",
        "status": "V2_FIXTURE_VIEW_VALIDATED_NO_AUTHORITY",
        "view_kind": value["view_kind"],
        "observable_sha256": digest,
        "externally_authenticated": False,
        "human_execution_authorized": False,
        "authority_effect": "NONE",
    }
