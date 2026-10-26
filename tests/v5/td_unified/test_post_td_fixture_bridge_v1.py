"""Prospective cross-lane adapter hostile tests; no human values or training."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import pytest

from scripts.v5.td_unified.post_td_fixture_bridge_v1 import (
    stage_fixture_downstream, FixtureBridgeError,
)
from scripts.v5.td_unified.casebundle_v1 import CaseBundleError
from scripts.v5.td_unified.mode_equivalence_v1 import (
    SCIENTIFIC_ROLES, FixtureStage, PathEquivalenceError,
)
from scripts.v5 import jepa_post_td_harness_contract_v1 as legacy

def h(s: bytes) -> str:
    return hashlib.sha256(s).hexdigest()

def case():
    return {
        "schema":"KNOWN_TRUTH_CASEBUNDLE_V1",
        "case_id":"PLANTED_FIT_ONLY",
        "authority_scope":"FIXTURE_ONLY",
        "manifest_sha256":h(b"dummy manifest"),
        "population_access_policy_sha256":h(b"dummy policy"),
        "address_universe_sha256":h(b"dummy universe"),
        "reader_partition":"reader_fit",
        "observations":[
            {"cell_id":"C1","donor_id":"D1","source_id":"SRC1",
             "operator_id":"OP1","address_id":"ADDR1",
             "state":"MEASURED_SCALAR","count":0,"library_size":11,
             "evidence_right":"RNA:CORE"},
            {"cell_id":"C1","donor_id":"D1","source_id":"SRC1",
             "operator_id":"OP1","address_id":"ADDR2",
             "state":"STRUCTURALLY_UNMEASURED","count":None,"library_size":None,
             "evidence_right":"RNA:EXT"},
        ],
    }

def _stage(label):
    def run(payload):
        return {"stage":label,"previous":h(repr(payload).encode())}
    return run

def stages():
    return tuple(FixtureStage(role, _stage(role)) for role in SCIENTIFIC_ROLES)

def test_none_target_first_class_and_no_legacy_portfolio_issued():
    r=stage_fixture_downstream(case_payload=case(),stages=stages())
    assert r["target_candidate_fixture"]=="NONE"
    assert r["post_td_portfolio"] is None
    assert r["post_td_architecture_plan"] is None
    assert r["authenticated_target_bundle_consumed"] is False
    assert r["real_training_authorized"] is False
    assert r["mode_path_receipt"]["same_code_path_authorized"] is False

def test_shared_foundation_fixture_uses_existing_post_td_semantics():
    r=stage_fixture_downstream(case_payload=case(),stages=stages(),
              fixture_candidate="C1",fixture_qualifications={"C1":"PASS"})
    p=r["post_td_portfolio"]
    a=r["post_td_architecture_plan"]
    assert p["schema"]==legacy.PORTFOLIO_SCHEMA
    assert [x["block_type"] for x in p["blocks"]]==["SHARED"]
    assert a["schema"]==legacy.ARCHITECTURE_SCHEMA
    assert a["teacher_topology"]=="SHARED_TYPED_HEADS"
    assert a["ema"]["native_unit"]=="SUCCESSFUL_BASE_CELL_PRESENTATIONS"
    assert a["ema"]["production_half_life_selected"] is False
    assert all(v is False for v in a["authority"].values())
    assert r["authority_effect"]=="NONE"

def test_c4_cannot_bypass_existing_c6_dependency():
    q={"C1":"PASS","C2":"PASS","C3":"PASS","C4":"PASS"}
    with pytest.raises(FixtureBridgeError):
        stage_fixture_downstream(case_payload=case(),stages=stages(),
                                 fixture_candidate="C4",fixture_qualifications=q)
    for c6 in ("FAIL","NOT_ESTIMABLE"):
        with pytest.raises(FixtureBridgeError):
            stage_fixture_downstream(case_payload=case(),stages=stages(),
                         fixture_candidate="C4",fixture_qualifications={**q,"C6":c6})
    success=stage_fixture_downstream(case_payload=case(),stages=stages(),
                     fixture_candidate="C4",fixture_qualifications={**q,"C6":"PASS"})
    assert success["post_td_portfolio"]["fused_candidate"]=="C4"
    assert success["real_training_authorized"] is False

def test_candidate_pass_still_cannot_promote_real_target():
    for cand,qs in [("C1",{"C1":"PASS"}),("C6",{"C1":"PASS","C3":"PASS","C6":"PASS"})]:
        r=stage_fixture_downstream(case_payload=case(),stages=stages(),
                         fixture_candidate=cand,fixture_qualifications=qs)
        assert r["status"]=="FIXTURE_ONLY__NOT_TARGET_QUALIFIED"
        assert r["authenticated_target_bundle_consumed"] is False
        assert r["same_code_path_authorized"] is False
        assert r["stage4_authorized"] is False

@pytest.mark.parametrize("bad",[
    {"C1":"AUTHENTICATED_EMPIRICAL_CALIBRATION"},
    {"C1":"QUALIFIED"},
    {"C1":True},
    {"C1":"KNOWN_TRUTH_QUALIFIED"},
])
def test_unlawful_qualification_shortcuts_rejected(bad):
    with pytest.raises(FixtureBridgeError):
        stage_fixture_downstream(case_payload=case(),stages=stages(),
                         fixture_candidate="C1",fixture_qualifications=bad)

def test_none_cannot_smuggle_fake_pass_qualifications():
    with pytest.raises(FixtureBridgeError):
        stage_fixture_downstream(case_payload=case(),stages=stages(),
                                 fixture_qualifications={"C1":"PASS"})

def test_protected_reader_partition_refused():
    c=case()
    c["reader_partition"]="reader_oracle"
    with pytest.raises(CaseBundleError):
        stage_fixture_downstream(case_payload=c,stages=stages())

def test_bad_observation_cannot_reach_existing_downstream_harness(monkeypatch):
    def fail_if_called(*args,**kwargs):
        raise AssertionError("legacy harness invoked before Task5 observation validation")
    monkeypatch.setattr(legacy,"build_target_portfolio",fail_if_called)
    c=case()
    c["observations"][0]["count"]=-2
    with pytest.raises(CaseBundleError):
        stage_fixture_downstream(case_payload=c,stages=stages(),
                      fixture_candidate="C1",fixture_qualifications={"C1":"PASS"})

def test_different_scientific_stage_roster_fails_before_architecture_planning(monkeypatch):
    monkeypatch.setattr(legacy,"build_target_portfolio",lambda **kwargs: (_ for _ in ()).throw(
      AssertionError("legacy harness invoked despite mismatched scientific-stage contract")))
    s=list(stages())
    s[2]=FixtureStage("NOT_A_PRODUCER",_stage("NOT_A_PRODUCER"))
    with pytest.raises(PathEquivalenceError):
        stage_fixture_downstream(case_payload=case(),stages=tuple(s),
                      fixture_candidate="C1",fixture_qualifications={"C1":"PASS"})

def test_contract_does_not_mutate_input_and_produces_stable_fixture_digests():
    c=case()
    a=stage_fixture_downstream(case_payload=c,stages=stages())
    b=stage_fixture_downstream(case_payload=deepcopy(c),stages=stages())
    assert a==b
    assert c==case()

def test_invalid_ema_budget_cannot_reach_mechanics_plan():
    with pytest.raises(FixtureBridgeError):
        stage_fixture_downstream(case_payload=case(),stages=stages(),
                      fixture_candidate="C1",fixture_qualifications={"C1":"PASS"},
                      ema_half_life_presentations=0)
