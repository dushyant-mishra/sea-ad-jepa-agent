"""Synthetic private V2 student/teacher pair coherence and non-promotion tests."""
from copy import deepcopy
import json

import pytest

from scripts.v5.td_unified import observation_normalization_view_v2_bound_content_v1 as B
from scripts.v5.td_unified import observation_v2_private_pair_coherence_v1 as C
from scripts.v5.td_unified.q_excluded_depth_v1 import QExcludedObservationError


def world(*, q=7, base=3, extra=11, query_right="RNA:QUERY",
          donor="D", operator="O"):
    return {
        "cells": [{
            "cell_id": "C", "donor_id": donor, "source_id": "S",
            "operator_id": operator, "library_total": q + base + extra,
            "counts": {"B": base, "E": extra, "Q": q},
        }],
        "address_rights": {"B": "RNA:BASE", "E": "RNA:EXT", "Q": query_right,
                           "U": "RNA:QUERY"},
        "operator_states": {operator: {
            "B": "MEASURED_SCALAR", "E": "MEASURED_SCALAR",
            "Q": "MEASURED_SCALAR", "U": "STRUCTURALLY_UNMEASURED",
        }},
        "ladder": [
            {"level_id": "L0", "evidence_rights": ["RNA:BASE"]},
            {"level_id": "L1", "evidence_rights": ["RNA:BASE", "RNA:EXT"]},
            {"level_id": "L2", "evidence_rights": [
                "RNA:BASE", "RNA:EXT", "RNA:QUERY"]},
        ],
        "query_address_id": "Q",
    }


def views(w=None):
    w = world() if w is None else w
    return (B.produce_fixture_student_view_v2_bound(**w),
            B.produce_fixture_teacher_view_v2_bound(**w))


def pair(student, teacher):
    return C.validate_private_v2_pair_coherence(
        student_view=student, teacher_view=teacher)


def test_consistent_pair_has_only_nonpromoting_constant_receipt():
    student, teacher = views()
    result = pair(json.loads(json.dumps(student)), json.loads(json.dumps(teacher)))
    assert result["status"] == "PAIR_COHERENCE_VERIFIED_FIXTURE_ONLY"
    assert result["authority_effect"] == "NONE"
    assert all(v is False for k, v in result.items() if k.endswith("_authenticated") or k.endswith("_authorized"))
    assert all(x not in result for x in ("rows", "teacher_digest", "teacher_view",
                                         "observable_sha256", "cell_count", "query_count"))
    assert all("library_size" not in row and "library_total" not in row for row in student["rows"])
    assert next(row for row in student["rows"] if row["address_id"] == "Q")["count"] is None
    assert next(row for row in teacher["rows"] if row["address_id"] == "Q")["count"] == 7


@pytest.mark.parametrize("q", [0, 1, 2, 7, 31, 99])
def test_private_result_and_student_bytes_ignore_teacher_query_mass(q):
    student, teacher = views(world(q=q))
    baseline_student, baseline_teacher = views(world(q=7))
    assert student == baseline_student  # full view, including public digest, is invariant
    assert pair(student, teacher) == pair(baseline_student, baseline_teacher)
    if q != 7:
        assert teacher["observable_sha256"] != baseline_teacher["observable_sha256"]


def test_mismatch_base_measured_value_is_caught_even_if_each_view_issued():
    student, _ = views(world(base=3))
    _, teacher = views(world(base=4))
    with pytest.raises(QExcludedObservationError, match="base scalar"):
        pair(student, teacher)


def test_mismatch_source_donor_operator_is_caught_after_both_valid_views():
    student, _ = views()
    for key in ("donor", "operator"):
        alt = world(**{key: "ALTERED"})
        _, teacher = views(alt)
        with pytest.raises(QExcludedObservationError, match="identity"):
            pair(student, teacher)


def test_mismatch_rights_roster_caught_without_embedded_rights_claim():
    student, _ = views()
    _, teacher = views(world(query_right="RNA:EXT"))
    with pytest.raises(QExcludedObservationError, match="rights/query"):
        pair(student, teacher)


def test_mismatched_query_mass_cannot_be_authenticated_as_same_physical_source():
    # A deliberately positive limitation: independent student and teacher
    # producer calls from different physical synthetic worlds may be coherent.
    # It is false to claim a pair receipt authenticates same-cell source truth.
    student, _ = views(world(q=1))
    _, teacher = views(world(q=99))
    receipt = pair(student, teacher)
    assert receipt["status"] == "PAIR_COHERENCE_VERIFIED_FIXTURE_ONLY"
    assert receipt["external_source_authenticated"] is False
    assert receipt["physical_measurement_identity_authenticated"] is False


def test_role_swapping_and_self_signed_teacher_receipt_refused():
    student, teacher = views()
    with pytest.raises(QExcludedObservationError, match="role"):
        pair(teacher, student)
    forged = deepcopy(teacher)
    for row in forged["rows"]:
        if row["address_id"] == "Q":
            row["count"] = 100
    forged.pop("observable_sha256")
    forged["observable_sha256"] = B.canonical_sha256(forged)
    with pytest.raises(QExcludedObservationError, match="not issued"):
        pair(student, forged)


def test_physical_total_and_injected_teacher_digest_are_never_laundered():
    student, teacher = views()
    for field in ("library_size", "library_total", "teacher_view_sha256"):
        tampered = deepcopy(student)
        tampered["rows"][0][field] = 999
        with pytest.raises(QExcludedObservationError):
            pair(tampered, teacher)


def test_invalid_unmapped_source_residual_fails_at_producer():
    w = world()
    w["cells"][0]["library_total"] += 10
    with pytest.raises(QExcludedObservationError, match="source library mass"):
        views(w)


def test_hostile_class_is_not_called_during_pair_snapshot():
    class Meta(type):
        count = 0
        def __eq__(cls, other):
            Meta.count += 1
            raise RuntimeError("payload was invoked")
        __hash__ = type.__hash__
    class Bomb(metaclass=Meta):
        pass
    student, teacher = views()
    student["rows"][0]["count"] = Bomb()
    with pytest.raises(QExcludedObservationError):
        pair(student, teacher)
    assert Meta.count == 0
