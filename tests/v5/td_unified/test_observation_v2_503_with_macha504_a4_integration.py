"""Composition: exact Macha #504 A4 producer + ChatGPT #502/#503 V2 APIs.

Original source and Macha A4 tests are copied byte-identically. Original
Macha #481 review is not edited; its A4 case is explicitly replayed through
the bound-version adapter rather than the incompatible legacy shape API.
"""
from copy import deepcopy
import hashlib
from pathlib import Path

import pytest

from scripts.v5.td_unified import observation_normalization_view_v2_bound_content_v1 as B
from scripts.v5.td_unified import observation_normalization_view_v2_fixture as V
from scripts.v5.td_unified import q_excluded_depth_v1 as Q
from tests.v5.td_unified import test_v2_bound_content_macha481_replay as REPLAY

MACHA504_BLOB="10a02426e0b8ec079831c26bfae972586533d4f1"


def test_exact_macha_reviewed_producer_file_is_integrated():
    path=Path(Q.__file__)
    raw=path.read_bytes()
    gitsha=hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
    assert gitsha==MACHA504_BLOB


def test_exact_original_macha481_a4_case_on_new_bound_contract():
    # This imported test runs unchanged reviewer logic, which compares the
    # exact refusal class+message for hidden q=0 versus q=5.
    REPLAY.REVIEW.test_red_refusal_of_an_empty_base_cell_does_not_depend_on_withheld_mass()


def world(q):
    return {
        "cells":[{"cell_id":"C","donor_id":"D","source_id":"S",
                  "operator_id":"O","library_total":q,
                  "counts":{"Q":q} if q else {}}],
        "address_rights":{"B":"RNA:BASE","Q":"RNA:QUERY"},
        "operator_states":{"O":{"B":"MEASURED_SCALAR","Q":"MEASURED_SCALAR"}},
        "ladder":[
            {"level_id":"L0","evidence_rights":["RNA:BASE"]},
            {"level_id":"L1","evidence_rights":["RNA:BASE","RNA:QUERY"]},
        ],
        "query_address_id":"Q",
    }


@pytest.mark.parametrize("make",[
    B.produce_fixture_student_view_v2_bound,
    B.produce_fixture_teacher_view_v2_bound,
    V.produce_fixture_student_view_v2,
    V.produce_fixture_teacher_view_v2,
])
def test_upstream_zero_base_complete_refusal_same_at_both_v2_interfaces(make):
    observed=[]
    for q in (0,1,5,100,2**20):
        try:
            make(**deepcopy(world(q)))
        except Q.QExcludedObservationError as exc:
            observed.append((type(exc),exc.args,exc.__cause__))
        else:
            pytest.fail("zero-base query-only cell was emitted")
    assert len(set(observed))==1
    assert observed[0][0] is Q.QExcludedDepthNotEstimable


def test_nonzero_base_keeps_lawful_student_bytes_constant():
    out=[]
    for q in (0,1,5,100):
        w=world(q)
        w["cells"][0]["counts"]["B"]=3
        w["cells"][0]["library_total"]+=3
        student=B.produce_fixture_student_view_v2_bound(**w)
        assert B.validate_fixture_observation_view_v2_bound(student)["authority_effect"]=="NONE"
        out.append(student)
    assert all(v==out[0] for v in out)
