"""A1/A2 synthetic consumer tests: a private *fixture* issuer binding is not real authority.

The Macha #481 hostile suite is preserved byte-identically in a separate file.
These tests additionally inject a policy-bound *malformed* receipt to prove that
consumer checks do more than reject digests never recorded by the producer.
"""
from copy import deepcopy
import json

import pytest

from scripts.v5.td_unified import observation_normalization_view_v2_fixture as V2
from scripts.v5.td_unified.q_excluded_depth_v1 import QExcludedObservationError

MS = "MEASURED_SCALAR"
LADDER = [
    {"level_id": "L0", "evidence_rights": ["RNA:BASE"]},
    {"level_id": "L1", "evidence_rights": ["RNA:BASE", "RNA:EXT", "RNA:QUERY"]},
]


def _world():
    return {
        "cells": [{
            "cell_id": "C", "donor_id": "D", "source_id": "S", "operator_id": "O",
            "library_total": 21, "counts": {"B": 3, "E": 7, "Q": 11},
        }],
        "address_rights": {"B": "RNA:BASE", "E": "RNA:EXT", "Q": "RNA:QUERY"},
        "operator_states": {"O": {"B": MS, "E": MS, "Q": MS}},
        "ladder": deepcopy(LADDER), "query_address_id": "Q",
    }


def _resign(view):
    v = deepcopy(view)
    v.pop("observable_sha256")
    return {**v, "observable_sha256": V2.canonical_sha256(v)}


def _check_as_bound_for_test(forged, honest):
    """Unit-test only: simulate a producer that signed a bad view, retaining its
    frozen rights policy, to independently exercise consumer arithmetic.
    This is NOT a public issuer or a real authority path.
    """
    key, source_key = forged["observable_sha256"], honest["observable_sha256"]
    with V2._VIEW_BINDINGS_LOCK:
        assert key not in V2._VIEW_BINDINGS
        V2._VIEW_BINDINGS[key] = V2._VIEW_BINDINGS[source_key]
    try:
        return V2.validate_fixture_observation_view_v2(forged)
    finally:
        with V2._VIEW_BINDINGS_LOCK:
            del V2._VIEW_BINDINGS[key]


@pytest.mark.parametrize("teacher", [False, True])
def test_real_view_and_json_roundtrip_remain_valid_without_physical_total(teacher):
    make = V2.produce_fixture_teacher_view_v2 if teacher else V2.produce_fixture_student_view_v2
    view = make(**_world())
    assert V2.validate_fixture_observation_view_v2(json.loads(json.dumps(view)))["status"] == (
        "V2_FIXTURE_VIEW_VALIDATED_NO_AUTHORITY"
    )
    assert all("library_total" not in r and "library_size" not in r for r in view["rows"])
    assert all(r["base_rights_normalization_depth"] == 3
               for r in view["rows"] if r["state"] == MS)
    if teacher:
        assert next(r for r in view["rows"] if r["address_id"] == "Q")["count"] == 11


@pytest.mark.parametrize("teacher", [False, True])
@pytest.mark.parametrize("bad_depth", [4, 6, 21])
def test_a1_consumer_rejects_wrong_depth_even_if_private_binding_is_injected(teacher, bad_depth):
    make = V2.produce_fixture_teacher_view_v2 if teacher else V2.produce_fixture_student_view_v2
    honest = make(**_world())
    forged = deepcopy(honest)
    for row in forged["rows"]:
        if row["state"] == MS:
            row["base_rights_normalization_depth"] = bad_depth
    forged = _resign(forged)
    with pytest.raises(QExcludedObservationError, match="normalization depth"):
        _check_as_bound_for_test(forged, honest)


@pytest.mark.parametrize("address", ["E", "Q"])
def test_a2_nonbase_scalar_refused_even_if_bound_as_original_student(address):
    honest = V2.produce_fixture_student_view_v2(**_world())
    forged = deepcopy(honest)
    for row in forged["rows"]:
        if row["address_id"] == address:
            row["state"] = MS
            row["count"] = 7 if address == "E" else 11
            row["base_rights_normalization_depth"] = 3
    forged = _resign(forged)
    with pytest.raises(QExcludedObservationError, match="frozen view rights"):
        _check_as_bound_for_test(forged, honest)


def test_a2_query_relabel_refused_against_bound_original_query():
    honest = V2.produce_fixture_student_view_v2(**_world())
    forged = _resign({**honest, "query_address_id": "B"})
    with pytest.raises(QExcludedObservationError, match="query or role"):
        _check_as_bound_for_test(forged, honest)


def test_re_signed_but_not_issued_json_is_refused():
    honest = V2.produce_fixture_student_view_v2(**_world())
    forged = deepcopy(honest)
    forged["rows"][0]["base_rights_normalization_depth"] = 14
    forged = _resign(forged)
    with pytest.raises(QExcludedObservationError, match="rights binding missing"):
        V2.validate_fixture_observation_view_v2(forged)


def test_orphan_valid_json_has_no_durable_or_source_authority():
    honest = V2.produce_fixture_student_view_v2(**_world())
    digest = honest["observable_sha256"]
    with V2._VIEW_BINDINGS_LOCK:
        binding = V2._VIEW_BINDINGS.pop(digest)
    try:
        with pytest.raises(QExcludedObservationError, match="rights binding missing"):
            V2.validate_fixture_observation_view_v2(json.loads(json.dumps(honest)))
    finally:
        with V2._VIEW_BINDINGS_LOCK:
            V2._VIEW_BINDINGS[digest] = binding


def test_drop_address_row_is_refused_even_with_registered_policy():
    honest = V2.produce_fixture_student_view_v2(**_world())
    forged = _resign({**honest, "rows": [r for r in honest["rows"] if r["address_id"] != "E"]})
    with pytest.raises(QExcludedObservationError, match="address coverage"):
        _check_as_bound_for_test(forged, honest)
