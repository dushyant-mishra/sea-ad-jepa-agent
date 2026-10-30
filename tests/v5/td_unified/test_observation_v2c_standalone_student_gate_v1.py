"""Independent-adversarial-case replay on *new*, detached V2C student API.

Macha #512 exact original tests remain RED on #510; this suite makes explicit
their adaptation to the new separate entry without editing #512. A Python
package/stdlib restriction is a test condition, NOT deployed process ACL.
"""
import importlib.util
import json
import sys
from copy import deepcopy
from pathlib import Path

import pytest

from scripts.v5.td_unified import observation_v2c_standalone_student_gate_v1 as C
from scripts.v5.td_unified import observation_normalization_view_v2_bound_content_v1 as B

MS="MEASURED_SCALAR"
SU="STRUCTURALLY_UNMEASURED"
MCU="MEASURED_COLLISION_UNRESOLVED"
W="WITHHELD_BY_EVIDENCE_RIGHTS"


def world(q=(7,23)):
    return {
        "cells":[{"cell_id":f"V2C_ROW{i}","donor_id":f"D{i}",
                  "source_id":"S","operator_id":"O",
                  "library_total":9+n,"counts":{"A":5,"B":4,"Q":n}}
                 for i,n in enumerate(q)],
        "address_rights":{"A":"BASE","B":"BASE","Q":"QUERY"},
        "operator_states":{"O":{"A":MS,"B":MS,"Q":MS}},
        "ladder":[{"level_id":"L0","evidence_rights":["BASE"]},
                  {"level_id":"L1","evidence_rights":["BASE","QUERY"]}],
        "query_address_id":"Q",
    }


def policy(w):
    return {
        "query_address_id":w["query_address_id"],
        "base_evidence_rights":deepcopy(w["ladder"][0]["evidence_rights"]),
        "address_rights":deepcopy(w["address_rights"]),
        "operator_states":deepcopy(w["operator_states"]),
        "cell_roster":[{k:v for k,v in x.items() if k in
                        ("cell_id","donor_id","source_id","operator_id")}
                       for x in w["cells"]],
    }


def issued(w=None):
    w=world() if w is None else w
    return B.produce_fixture_student_view_v2_bound(**w)


def sign(v):
    v=deepcopy(v)
    v["observable_sha256"]=B.canonical_sha256(
        {k:x for k,x in v.items() if k!="observable_sha256"})
    return v


@pytest.fixture(autouse=True)
def no_test_registry_spill():
    with B._VIEW_BINDINGS_LOCK:
        old=dict(B._VIEW_BINDINGS)
        B._VIEW_BINDINGS.clear()
    try:
        yield
    finally:
        with B._VIEW_BINDINGS_LOCK:
            B._VIEW_BINDINGS.clear()
            B._VIEW_BINDINGS.update(old)


def test_self_contained_module_has_no_teacher_issuer_import_edge():
    import ast
    module=Path(C.__file__)
    tree=ast.parse(module.read_text(encoding="utf8"))
    imports=[node for node in ast.walk(tree)
             if isinstance(node,(ast.Import,ast.ImportFrom))]
    assert len(imports)==2
    assert {n.module if isinstance(n,ast.ImportFrom) else n.names[0].name
            for n in imports}=={"hashlib","__future__"}
    assert not hasattr(C,"B")
    assert not hasattr(C,"_VIEW_BINDINGS")
    # Isolation is only enforceable when the deployed process doesn't have
    # old #502 module on PYTHONPATH or imported in its process.


def test_canonical_domain_matches_existing_independent_encoder():
    v=issued()
    assert C._sha({k:x for k,x in v.items() if k!="observable_sha256"})==v["observable_sha256"]
    p=policy(world())
    assert C._sha(p)==B.canonical_sha256(p)
    r=C.validate_student_v2c(student_view=v,expected_policy=p)
    assert r["validated_student_view_sha256"]==v["observable_sha256"]
    assert r["complete_policy_sha256"]==B.canonical_sha256(p)
    assert r["receipt_sha256"]==B.canonical_sha256(
        {k:x for k,x in r.items() if k!="receipt_sha256"})


def test_teacher_candidates_all_constant_without_bypass_from_module():
    for hidden in ((7,23),(8,24),(0,0),(31,31)):
        w=world(hidden)
        student=issued(w)
        teacher=B.produce_fixture_teacher_view_v2_bound(**w)
        results=set()
        for q0 in range(32):
            for q1 in range(32):
                trial=deepcopy(student)
                trial["view_kind"]="TEACHER_RICHER_RIGHTS"
                for row in trial["rows"]:
                    if row["state"]==W:
                        row.update(state=MS,count=(q0 if row["cell_id"]=="V2C_ROW0" else q1),
                                   base_rights_normalization_depth=9)
                trial=sign(trial)
                try:
                    C.validate_student_v2c(student_view=trial,expected_policy=policy(w))
                except C.StudentV2CRefusal as e:
                    results.add((type(e),e.args,e.__cause__))
        for trial in (teacher,):
            with pytest.raises(C.StudentV2CRefusal) as ex:
                C.validate_student_v2c(student_view=trial,expected_policy=policy(w))
            results.add((type(ex.value),ex.value.args,ex.value.__cause__))
        assert len(results)==1
        assert next(iter(results))[1]==("V2C accepts STUDENT_BASE_RIGHTS only",)


@pytest.mark.parametrize("kind",["drop_cell","relabel_donor","relabel_source","operator_state"])
def test_complete_enforced_policy_commitment_changes_with_roster_and_state(kind):
    w=world()
    v=issued(w)
    original=C.validate_student_v2c(student_view=v,expected_policy=policy(w))
    spoof=world()
    if kind=="drop_cell":
        spoof["cells"]=spoof["cells"][:1]
    elif kind=="relabel_donor":
        spoof["cells"][1]["donor_id"]="OTHER"
    elif kind=="relabel_source":
        spoof["cells"][1]["source_id"]="OTHER"
    else:
        spoof["operator_states"]["O"]["B"]=SU
        for c in spoof["cells"]:
            c["library_total"]-=c["counts"].pop("B")
    changed=C.validate_student_v2c(student_view=issued(spoof),expected_policy=policy(spoof))
    assert changed["complete_policy_sha256"]!=original["complete_policy_sha256"]
    assert changed["receipt_sha256"]!=original["receipt_sha256"]


@pytest.mark.parametrize("kind",["swap","laundered_q","fabrication"])
def test_receipt_commits_to_actual_student_content_not_just_policy(kind):
    p=policy(world())
    honest=C.validate_student_v2c(student_view=issued(),expected_policy=p)
    v=issued()
    for row in v["rows"]:
        if row["cell_id"]!="V2C_ROW0" or row["state"]!=MS:continue
        if kind=="swap":
            row["count"]=4 if row["address_id"]=="A" else 5
        elif kind=="laundered_q":
            row["base_rights_normalization_depth"]+=7
            row["count"]+=7 if row["address_id"]=="A" else 0
        else:
            row["count"]=50 if row["address_id"]=="A" else 1
            row["base_rights_normalization_depth"]=51
    changed=C.validate_student_v2c(student_view=sign(v),expected_policy=p)
    assert changed["complete_policy_sha256"]==honest["complete_policy_sha256"]
    assert changed["validated_student_view_sha256"]!=honest["validated_student_view_sha256"]
    assert changed["receipt_sha256"]!=honest["receipt_sha256"]
    assert changed["source_rights_issuer_authenticated"] is False


@pytest.mark.parametrize("element",[[["BASE"]],[{"x":"BASE"}]],ids=["nested_list","dict"])
def test_unhashable_policy_is_domain_refusal(element):
    p=policy(world())
    p["base_evidence_rights"]=element
    with pytest.raises(C.StudentV2CRefusal):
        C.validate_student_v2c(student_view=issued(),expected_policy=p)


@pytest.mark.parametrize("payload",[
    {"base_evidence_rights":[True]},
    {"base_evidence_rights":[1.5]},
    {"base_evidence_rights":[{"__class__":"str"}]},
])
def test_hostile_policy_cannot_escape_with_raw_exception(payload):
    p=policy(world());p.update(payload)
    with pytest.raises(C.StudentV2CRefusal):
        C.validate_student_v2c(student_view=issued(),expected_policy=p)


def test_policy_and_view_are_not_authenticated_just_because_receipt_is_distinct():
    fake=world()
    fake["address_rights"]["Q"]="BASE"
    fake["address_rights"]["B"]="QUERY"
    fake["query_address_id"]="B"
    fake["ladder"]=[{"level_id":"L0","evidence_rights":["BASE"]},
                    {"level_id":"L1","evidence_rights":["BASE","QUERY"]}]
    v=issued(fake)
    receipt=C.validate_student_v2c(student_view=v,expected_policy=policy(fake))
    assert receipt["authority_effect"]=="NONE"
    assert receipt["source_rights_issuer_authenticated"] is False
    assert receipt["real_training_authorized"] is False


def test_hidden_query_in_base_alias_remains_unqualified_even_with_receipt():
    # No independently sourced exact biological feature map is available here.
    w=world()
    honest=C.validate_student_v2c(student_view=issued(w),expected_policy=policy(w))
    w2=world()
    for cell in w2["cells"]:
        cell["counts"]["A"]+=cell["counts"]["Q"]
        cell["library_total"]+=cell["counts"]["Q"]
    # Old producer accepts these consistent synthetic bytes; not proof
    # that any actual source molecule has been assigned to the right address.
    v=issued(w2)
    altered=C.validate_student_v2c(student_view=v,expected_policy=policy(w2))
    assert altered["validated_student_view_sha256"]!=honest["validated_student_view_sha256"]
    assert altered["source_feature_alias_closure_authenticated"] is False
