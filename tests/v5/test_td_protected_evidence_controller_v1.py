from __future__ import annotations
import sys
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"scripts"/"v5"))
import td_protected_evidence_controller_v1 as P


def auth(stage,subject_hash="a"*64,protocol_hash="b"*64,evidence_hash="c"*64):
    return {"schema":"JEPA_TD_PROTECTED_EVIDENCE_AUTHORITY_V1","stage":stage,"subject_sha256":subject_hash,"protocol_sha256":protocol_hash,"protected_evidence_manifest_sha256":evidence_hash,"execute_once":True,"target_selection_authorized":False,"td60_authorized":False,"stage4_authorized":False,"training_authorized":False}

def test_h2h_qualify_binds_exact_survivor_set_without_value_read(tmp_path):
    q=P.qualify_head_to_head(["C1_SHARED_EMERGENT","C3_QUERY_MEASURED"],subject_sha256="a"*64,protocol_sha256="b"*64,protected_evidence_manifest_sha256="c"*64,namespace=tmp_path/"x")
    assert q["protected_values_read"] is False
    assert q["survivors"]==["C1_SHARED_EMERGENT","C3_QUERY_MEASURED"]
    assert not (tmp_path/"x").exists()

def test_h2h_execute_writes_marker_before_runner_and_routes_thresholded_pairs(tmp_path):
    ns=tmp_path/"h2h"; seen={}
    def runner(path):
        seen["marker"]=(path/"START_MARKER.json").exists()
        dims={k:"NONINFERIOR" for k in P.H2H_DIMENSIONS}; dims["BIOLOGICAL_INFORMATION"]="BETTER"
        return [{"candidate_a":"C1_SHARED_EMERGENT","candidate_b":"C3_QUERY_MEASURED","dimensions":dims}]
    out=P.execute_head_to_head(["C1_SHARED_EMERGENT","C3_QUERY_MEASURED"],subject_sha256="a"*64,protocol_sha256="b"*64,protected_evidence_manifest_sha256="c"*64,namespace=ns,authority=auth("HEAD_TO_HEAD"),runner=runner)
    assert seen["marker"] is True
    assert out["leader"]=="C1_SHARED_EMERGENT"
    assert out["spent_authority"] is True

def test_confirmation_adjudicates_pass_fail_not_estimable_and_never_selects_target(tmp_path):
    dims={name:"PASS" for name in P.CONFIRMATION_DIMENSIONS}
    def runner(_): return dims
    out=P.execute_confirmation("C1_SHARED_EMERGENT",candidate_definition_sha256="d"*64,protocol_sha256="b"*64,protected_evidence_manifest_sha256="c"*64,namespace=tmp_path/"ok",authority=auth("CONFIRMATION","d"*64),runner=runner)
    assert out["terminal"]=="PROTECTED_CONFIRMATION_PASS__SEPARATE_TARGET_SELECTION_AUTHORITY_REQUIRED"
    assert out["target_selection_authorized"] is False
    dims2=dict(dims); dims2["DONOR_RECURRENCE_TRANSFER"]="FAIL"
    out=P.execute_confirmation("C1_SHARED_EMERGENT",candidate_definition_sha256="e"*64,protocol_sha256="b"*64,protected_evidence_manifest_sha256="c"*64,namespace=tmp_path/"fail",authority=auth("CONFIRMATION","e"*64),runner=lambda _:dims2)
    assert out["terminal"].startswith("PROTECTED_CONFIRMATION_FAIL")
    dims3=dict(dims); dims3["SOURCE_TRANSFER"]="NOT_ESTIMABLE"
    out=P.execute_confirmation("C1_SHARED_EMERGENT",candidate_definition_sha256="f"*64,protocol_sha256="b"*64,protected_evidence_manifest_sha256="c"*64,namespace=tmp_path/"ne",authority=auth("CONFIRMATION","f"*64),runner=lambda _:dims3)
    assert out["terminal"]=="PROTECTED_CONFIRMATION_NOT_ESTIMABLE__NO_TARGET_AUTHORITY"

def test_identity_mismatch_or_reused_namespace_refuses(tmp_path):
    ns=tmp_path/"x"
    with pytest.raises(P.ProtectedEvidenceError,match="subject binding"):
        P.execute_confirmation("C1_SHARED_EMERGENT",candidate_definition_sha256="d"*64,protocol_sha256="b"*64,protected_evidence_manifest_sha256="c"*64,namespace=ns,authority=auth("CONFIRMATION","e"*64),runner=lambda _: {})
    ns.mkdir()
    with pytest.raises(P.ProtectedEvidenceError,match="namespace"):
        P.execute_confirmation("C1_SHARED_EMERGENT",candidate_definition_sha256="d"*64,protocol_sha256="b"*64,protected_evidence_manifest_sha256="c"*64,namespace=ns,authority=auth("CONFIRMATION","d"*64),runner=lambda _: {})
