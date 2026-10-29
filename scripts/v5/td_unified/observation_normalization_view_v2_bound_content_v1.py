"""Separately versioned V2 *content* consumer and fixture-only producer edge.

The original observation_normalization_view_v2_fixture.py retains its
historical shape-only consumer contract. This module adds the D1 rights-bound
content law without silently changing V2 shape semantics or physical V1/G7
library_size. It reuses the original source-side V2 producer and shape gate.

The process-local issuer map is cooperative fixture custody, NOT a source
signature, donor identity, real TRAIN calibration, durable rights binding or
permission to execute biology. A hostile same-process actor can alter it.
"""
from __future__ import annotations

from threading import Lock

from scripts.v5.td_unified import observation_normalization_view_v2_fixture as V2
from scripts.v5.td_unified.q_excluded_depth_v1 import (
    MEASURED_SCALAR, QExcludedObservationError, canonical_sha256, _snapshot,
)

_SCHEMA = "TD_OBSERVATION_NORMALIZATION_VIEW_V2_BOUND_CONTENT_V1_FIXTURE"
_STATUS = "V2_BOUND_CONTENT_FIXTURE_VIEW_VALIDATED_NO_AUTHORITY"
_VIEW_BINDINGS_LOCK = Lock()
# Observable public digest -> (query, role, frozen address/right, base rights, selected rights)
# No private physical total, private source digest or teacher-view hash here.
_VIEW_BINDINGS = {}


def _issue(*, cells, address_rights, operator_states, ladder,
           query_address_id, teacher):
    # Freeze all caller objects once, before any user-controlled comparison.
    frozen = _snapshot({
        "cells": cells, "address_rights": address_rights,
        "operator_states": operator_states, "ladder": ladder,
        "query_address_id": query_address_id,
    })
    producer = (V2.produce_fixture_teacher_view_v2 if teacher
                else V2.produce_fixture_student_view_v2)
    v2 = producer(**frozen)
    body = {k: v for k, v in v2.items() if k != "observable_sha256"}
    body["schema"] = _SCHEMA
    digest = canonical_sha256(body)
    rights = frozen["address_rights"]
    levels = frozen["ladder"]
    index = -1 if teacher else 0
    binding = (
        frozen["query_address_id"], body["view_kind"],
        tuple(sorted(rights.items())),
        frozenset(levels[0]["evidence_rights"]),
        frozenset(levels[index]["evidence_rights"]),
    )
    with _VIEW_BINDINGS_LOCK:
        previous = _VIEW_BINDINGS.get(digest)
        if previous is not None and previous != binding:
            raise QExcludedObservationError("ambiguous bound-content rights for one view")
        _VIEW_BINDINGS[digest] = binding
    return {**body, "observable_sha256": digest}


def produce_fixture_student_view_v2_bound(*, cells, address_rights,
                                           operator_states, ladder,
                                           query_address_id):
    """Only base-rights counts; richer and private values never leave this API."""
    return _issue(cells=cells, address_rights=address_rights,
                  operator_states=operator_states, ladder=ladder,
                  query_address_id=query_address_id, teacher=False)


def produce_fixture_teacher_view_v2_bound(*, cells, address_rights,
                                           operator_states, ladder,
                                           query_address_id):
    """Rich observation fixture for a separately custodied teacher actor."""
    return _issue(cells=cells, address_rights=address_rights,
                  operator_states=operator_states, ladder=ladder,
                  query_address_id=query_address_id, teacher=True)


def validate_fixture_observation_view_v2_bound(view):
    """Require bound producer policy plus exact per-cell D1 mapped base sum.

    Unlike the legacy V2 shape-only validator, this rejects re-signed receipts
    and modified base counts/depth. The issuer map has only PROCESS-LOCAL
    fixture custody and cannot independently attest source or evidence rights.
    """
    value = V2._view_snapshot(view)
    if type(value) is not dict or set(value) != V2._VIEW_KEYS:
        raise QExcludedObservationError("V2 bound-content view fields differ")
    digest = value["observable_sha256"]
    body = {k: v for k, v in value.items() if k != "observable_sha256"}
    if (type(digest) is not str or len(digest) != 64 or
            any(c not in "0123456789abcdef" for c in digest) or
            canonical_sha256(body) != digest):
        raise QExcludedObservationError("V2 bound-content digest differs")
    if body["schema"] != _SCHEMA:
        raise QExcludedObservationError("wrong V2 bound-content schema")
    # Use existing, audited V2 shape checks on an explicit V2-shaped *copy*.
    # Never present the V2 shape receipt as an externally issued content proof.
    legacy = dict(body)
    legacy["schema"] = V2._SCHEMA
    legacy["observable_sha256"] = canonical_sha256(legacy)
    V2.validate_fixture_observation_view_v2(legacy)

    with _VIEW_BINDINGS_LOCK:
        binding = _VIEW_BINDINGS.get(digest)
    if binding is None:
        raise QExcludedObservationError(
            "bound-content rights not issued in this fixture process")
    q, role, frozen_rights, frozen_base, frozen_selected = binding
    rights = dict(frozen_rights)
    base, selected = frozenset(frozen_base), frozenset(frozen_selected)
    if (body["query_address_id"] != q or body["view_kind"] != role
            or not base or not base <= selected or
            q not in rights or rights[q] in base):
        raise QExcludedObservationError("bound content query/role/rights differ")
    seen, per_cell, base_sums, cell_depth = set(), {}, {}, {}
    for row in body["rows"]:
        cid, aid = row["cell_id"], row["address_id"]
        ident = (cid, aid)
        if ident in seen or aid not in rights:
            raise QExcludedObservationError("unknown or duplicate bound address")
        seen.add(ident)
        per_cell.setdefault(cid, set()).add(aid)
        right = rights[aid]
        if row["evidence_right"] != right:
            raise QExcludedObservationError("address right differs from bound roster")
        measured = row["state"] == MEASURED_SCALAR
        if measured:
            if right not in selected:
                raise QExcludedObservationError("non-base scalar exceeds bound view rights")
            depth = row["base_rights_normalization_depth"]
            if cid in cell_depth and cell_depth[cid] != depth:
                raise QExcludedObservationError("base depth differs within cell")
            cell_depth[cid] = depth
            if right in base:
                base_sums[cid] = base_sums.get(cid, 0) + row["count"]
        elif row["state"] == "WITHHELD_BY_EVIDENCE_RIGHTS" and right in selected:
            raise QExcludedObservationError("granted source right was withheld")
    universe = set(rights)
    for cid, addresses in per_cell.items():
        if addresses != universe:
            raise QExcludedObservationError("incomplete bound address coverage")
        if cid not in cell_depth or cell_depth[cid] != base_sums.get(cid, 0):
            raise QExcludedObservationError(
                "base normalization depth differs from mapped visible scalar sum")
    return {
        "schema": "TD_OBSERVATION_V2_BOUND_CONTENT_VALIDATION_V1",
        "status": _STATUS,
        "view_kind": role,
        "observable_sha256": digest,
        "source_authenticated": False,
        "q_rights_issuer_authenticated": False,
        "physical_measurement_identity_authenticated": False,
        "donor_identity_authenticated": False,
        "human_execution_authorized": False,
        "real_training_authorized": False,
        "authority_effect": "NONE",
    }
