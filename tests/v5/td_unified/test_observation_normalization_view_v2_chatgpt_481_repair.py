"""ChatGPT repair guards for PR #479 A1-A3 against immutable Macha #481 tests.

Fixture only. This file does not repair inherited #474 A4, authenticate source
rights, resolve gene aliases/residual mass, or authorize real training.
"""
from copy import deepcopy

import pytest

from scripts.v5.td_unified import observation_normalization_view_v2_fixture as V2
from scripts.v5.td_unified.canonical_v1 import canonical_sha256
from scripts.v5.td_unified.q_excluded_depth_v1 import QExcludedObservationError


MS = "MEASURED_SCALAR"


def _world():
    return {
        "cells": [{
            "cell_id": "C", "donor_id": "D", "source_id": "S", "operator_id": "O",
            "library_total": 15, "counts": {"B": 5, "E": 3, "Q": 7},
        }],
        "address_rights": {"B": "RNA:BASE", "E": "RNA:EXT", "Q": "RNA:QUERY"},
        "operator_states": {"O": {"B": MS, "E": MS, "Q": MS}},
        "ladder": [
            {"level_id": "L0", "evidence_rights": ["RNA:BASE"]},
            {"level_id": "L1", "evidence_rights": ["RNA:BASE", "RNA:EXT", "RNA:QUERY"]},
        ],
        "query_address_id": "Q",
    }


def _resign(view):
    body = {k: v for k, v in view.items() if k != "observable_sha256"}
    view["observable_sha256"] = canonical_sha256(body)
    return view


def test_a1_depth_equals_published_base_visible_scalar_sum():
    view = V2.produce_fixture_teacher_view_v2(**_world())
    receipt = V2.validate_fixture_observation_view_v2(view)
    assert receipt["authority_effect"] == "NONE"
    base_sum = sum(
        r["count"] for r in view["rows"]
        if r["state"] == MS and r["evidence_right"] == "RNA:BASE"
    )
    depths = {
        r["base_rights_normalization_depth"] for r in view["rows"] if r["state"] == MS
    }
    assert depths == {base_sum}


def test_a2_base_rights_binding_is_not_caller_expandable():
    view = V2.produce_fixture_student_view_v2(**_world())
    view["base_evidence_rights"] = ["RNA:BASE", "RNA:EXT"]
    with pytest.raises(QExcludedObservationError, match="base rights"):
        V2.validate_fixture_observation_view_v2(_resign(view))


def test_a2_student_cannot_expose_ext_even_with_valid_count_and_depth():
    view = V2.produce_fixture_student_view_v2(**_world())
    depth = next(r["base_rights_normalization_depth"] for r in view["rows"] if r["state"] == MS)
    for row in view["rows"]:
        if row["address_id"] == "E":
            row["state"] = MS
            row["count"] = 3
            row["base_rights_normalization_depth"] = depth
    with pytest.raises(QExcludedObservationError, match="non-base"):
        V2.validate_fixture_observation_view_v2(_resign(view))


def test_fixture_base_ladder_is_code_pinned_not_silently_redefined():
    world = deepcopy(_world())
    world["ladder"][0]["evidence_rights"] = ["RNA:BASE", "RNA:EXT"]
    with pytest.raises(QExcludedObservationError, match="code-pinned"):
        V2.produce_fixture_student_view_v2(**world)
