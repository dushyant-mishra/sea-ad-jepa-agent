"""Hostile V2B public student validation against unchanged Macha #507 findings.

The original #507 remains RED against the old public API. This suite targets a
NEW explicitly separate student-facing interface; no 'repaired #502' claim.
"""
from copy import deepcopy
import json

import pytest

from scripts.v5.td_unified import observation_normalization_view_v2_bound_content_v1 as B
from scripts.v5.td_unified import observation_v2b_public_student_gate_v1 as S
from scripts.v5.td_unified.q_excluded_depth_v1 import QExcludedObservationError

MS="MEASURED_SCALAR"
LADDER=[
    {"level_id":"L0","evidence_rights":["RNA:BASE"]},
    {"level_id":"L1","evidence_rights":["RNA:BASE","RNA:EXT","RNA:QUERY"]},
]


def world(qs=(7,23)):
    return {
        "cells":[{"cell_id":f"C{i}","donor_id":"D","source_id":"S",
                  "operator_id":"O","library_total":9+q,
                  "counts":{"B":9,"Q":q}} for i,q in enumerate(qs)],
        "address_rights":{"B":"RNA:BASE","Q":"RNA:QUERY"},
        "operator_states":{"O":{"B":MS,"Q":MS}},
        "ladder":deepcopy(LADDER),"query_address_id":"Q",
    }


def policy(w):
    return {
        "query_address_id":w["query_address_id"],
        "base_evidence_rights":deepcopy(w["ladder"][0]["evidence_rights"]),
        "address_rights":deepcopy(w["address_rights"]),
        "operator_states":deepcopy(w["operator_states"]),
        "cell_roster":[{k:c[k] for k in ("cell_id","donor_id","source_id","operator_id")}
                       for c in w["cells"]],
    }


def candidate(student,guess):
    v=deepcopy(student)
    v["view_kind"]="TEACHER_RICHER_RIGHTS"
    for row in v["rows"]:
        if row["state"]=="WITHHELD_BY_EVIDENCE_RIGHTS":
            row["state"]=MS
            row["count"]=guess[row["cell_id"]]
            row["base_rights_normalization_depth"]=9
    v.pop("observable_sha256")
    v["observable_sha256"]=B.canonical_sha256(v)
    return v


def fail(v,p):
    try:
        S.validate_public_student_v2b(student_view=v,expected_policy=p)
    except QExcludedObservationError as exc:
        return (type(exc).__name__,str(exc))
    return ("VALIDATED","")


def test_public_gate_never_looks_up_teacher_issuance_through_1024_candidates():
    w=world()
    student=B.produce_fixture_student_view_v2_bound(**w)
    p=policy(w)
    honest=S.validate_public_student_v2b(student_view=student,expected_policy=p)
    assert honest["status"]==S.RESULT_STATUS
    assert honest["source_rights_issuer_authenticated"] is False
    # Issue an actual teacher into the old vulnerable registry; the new
    # student gate must not depend on whether this teacher is issued.
    B.produce_fixture_teacher_view_v2_bound(**w)
    outcomes={fail(candidate(student,{"C0":q0,"C1":q1}),p)
              for q0 in range(32) for q1 in range(32)}
    assert outcomes=={("QExcludedObservationError",
                       "public V2B only accepts STUDENT_BASE_RIGHTS")}


def test_public_gate_result_and_candidate_responses_independent_of_hidden_counts():
    results=[]
    for qs in ((7,23),(8,24),(0,0),(31,31)):
        w=world(qs)
        s=B.produce_fixture_student_view_v2_bound(**w)
        B.produce_fixture_teacher_view_v2_bound(**w)
        results.append((s,S.validate_public_student_v2b(student_view=s,expected_policy=policy(w)),
                        fail(candidate(s,{"C0":7,"C1":23}),policy(w))))
    assert all(x==results[0] for x in results)


def substitution(mode):
    w={
        "cells":[{"cell_id":"C0","donor_id":"D","source_id":"S","operator_id":"O",
                  "library_total":26,"counts":{"B":9,"E":4,"Q":11,"Z":2}}],
        "address_rights":{"B":"RNA:BASE","E":"RNA:EXT","Q":"RNA:QUERY","Z":"RNA:EXT"},
        "operator_states":{"O":dict.fromkeys(("B","E","Q","Z"),MS)},
        "ladder":deepcopy(LADDER),"query_address_id":"Q",
    }
    if mode=="base_promoted":
        w["ladder"][0]["evidence_rights"]=["RNA:BASE","RNA:EXT"]
    elif mode=="decoy_query":
        w["address_rights"]["Q"]="RNA:BASE"
        w["address_rights"]["Z"]="RNA:QUERY"
        w["query_address_id"]="Z"
    return w


@pytest.mark.parametrize("mode",["base_promoted","decoy_query"])
def test_rights_and_query_substitution_refused_against_separately_frozen_policy(mode):
    honest=substitution("honest")
    attacker=substitution(mode)
    # Both can be issued by untrusted old producer. That is not rights custody.
    view=B.produce_fixture_student_view_v2_bound(**attacker)
    assert fail(view,policy(honest))[0]=="QExcludedObservationError"
    # The alternative policy is not independently authenticated. It may pass
    # when self-supplied, so the result is *never* an authority receipt.
    own=S.validate_public_student_v2b(student_view=view,expected_policy=policy(attacker))
    good=S.validate_public_student_v2b(
        student_view=B.produce_fixture_student_view_v2_bound(**honest),
        expected_policy=policy(honest))
    assert own["policy_commitment_sha256"]!=good["policy_commitment_sha256"]
    assert own["source_rights_issuer_authenticated"] is False


def resign(v):
    v=deepcopy(v)
    v.pop("observable_sha256")
    v["observable_sha256"]=B.canonical_sha256(v)
    return v


@pytest.mark.parametrize("mutation",["depth","nonbase","drop_cell","donor","swap_base","drop_address"])
def test_consumer_refuses_re_signed_forgeries_without_membership_allowlist(mutation):
    w=world()
    s=B.produce_fixture_student_view_v2_bound(**w)
    if mutation=="depth":
        for row in s["rows"]:
            if row["state"]==MS:row["base_rights_normalization_depth"]+=1
    elif mutation=="nonbase":
        for row in s["rows"]:
            if row["address_id"]=="Q":
                row.update(state=MS,count=7,base_rights_normalization_depth=9)
    elif mutation=="drop_cell":
        s["rows"]=[x for x in s["rows"] if x["cell_id"]!="C1"]
    elif mutation=="donor":
        for row in s["rows"]:
            if row["cell_id"]=="C0":row["donor_id"]="WRONG"
    elif mutation=="swap_base":
        # More than one base gene needed to swap preserving the sum; change a
        # count in this one-base fixture: D1 must detect it.
        for row in s["rows"]:
            if row["cell_id"]=="C0" and row["address_id"]=="B":row["count"]+=1
    elif mutation=="drop_address":
        s["rows"]=[x for x in s["rows"] if not (x["cell_id"]=="C1" and x["address_id"]=="Q")]
    assert fail(resign(s),policy(w))[0]=="QExcludedObservationError"


def test_no_process_local_issuer_binding_consulted_for_public_student_receipt():
    w=world()
    s=B.produce_fixture_student_view_v2_bound(**w)
    p=policy(w)
    with B._VIEW_BINDINGS_LOCK:
        old=dict(B._VIEW_BINDINGS)
        B._VIEW_BINDINGS.clear()
    try:
        assert S.validate_public_student_v2b(student_view=s,expected_policy=p)["status"]==S.RESULT_STATUS
    finally:
        with B._VIEW_BINDINGS_LOCK:
            B._VIEW_BINDINGS.clear()
            B._VIEW_BINDINGS.update(old)


def test_source_policy_does_not_gain_authenticity_when_attacker_supplies_it():
    attacker=substitution("base_promoted")
    s=B.produce_fixture_student_view_v2_bound(**attacker)
    receipt=S.validate_public_student_v2b(student_view=s,expected_policy=policy(attacker))
    assert receipt["source_rights_issuer_authenticated"] is False
    assert receipt["g7_content_v2_authorized"] is False
    assert receipt["authority_effect"]=="NONE"
    assert not any("teacher" in key and isinstance(val,str) and len(val)==64
                   for key,val in receipt.items())


def test_exact_type_guard_catches_malicious_metaclass_without_dispatch():
    class Meta(type):
        called=False
        def __eq__(cls,other):
            Meta.called=True
            raise RuntimeError("attacker code")
        __hash__=type.__hash__
    class X(metaclass=Meta):pass
    s=B.produce_fixture_student_view_v2_bound(**world())
    s["rows"][0]["count"]=X()
    with pytest.raises(QExcludedObservationError):
        S.validate_public_student_v2b(student_view=s,expected_policy=policy(world()))
    assert Meta.called is False
