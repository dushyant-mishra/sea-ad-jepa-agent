from __future__ import annotations
import sys
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"scripts"/"v5"))
import td_real_tournament_gates_v1 as G
import td_real_tournament_contract_v1 as C
import td_real_tournament_bundle_v1 as B

def receipt(candidate,status):
    return G.CandidateGateReceipt(candidate_id=candidate,gates={"fixture":{"status":status}},status=status,authority={k:False for k in C.AUTHORITY_KEYS})

def test_relational_fail_requires_only_independent_foundation_receipts():
    receipts={c:receipt(c,"PASS") for c in ("C1_SHARED_EMERGENT","C3_QUERY_MEASURED","C6_SHARED_QUERY_COMPOSITE")}
    bundle=B.validate_bundle(receipts, corrected_relational_replay_status="FAIL")
    assert bundle["candidate_statuses"]["C2_RELATIONAL_SHARED"]=="ELIMINATED"
    assert bundle["candidate_statuses"]["C4_STRUCTURED_COMPOSITE"]=="BLOCKED_BY_CONSTITUENT"
    assert bundle["candidate_statuses"]["C6_SHARED_QUERY_COMPOSITE"]=="ELIGIBLE"

def test_relational_not_estimable_keeps_c2_c4_unresolved():
    receipts={c:receipt(c,"PASS") for c in ("C1_SHARED_EMERGENT","C3_QUERY_MEASURED","C6_SHARED_QUERY_COMPOSITE")}
    bundle=B.validate_bundle(receipts, corrected_relational_replay_status="NOT_ESTIMABLE")
    assert bundle["candidate_statuses"]["C2_RELATIONAL_SHARED"]=="UNRESOLVED"
    assert bundle["candidate_statuses"]["C4_STRUCTURED_COMPOSITE"]=="UNRESOLVED_BY_CONSTITUENT"

def test_relational_pass_requires_all_foundation_receipts():
    receipts={c:receipt(c,"PASS") for c in ("C1_SHARED_EMERGENT","C2_RELATIONAL_SHARED","C3_QUERY_MEASURED","C6_SHARED_QUERY_COMPOSITE","C4_STRUCTURED_COMPOSITE")}
    bundle=B.validate_bundle(receipts, corrected_relational_replay_status="PASS")
    assert set(bundle["eligible_foundation_candidates"])==set(receipts)
    receipts.pop("C2_RELATIONAL_SHARED")
    with pytest.raises(B.BundleError,match="required candidate receipts"):
        B.validate_bundle(receipts, corrected_relational_replay_status="PASS")

def test_candidate_fail_and_not_estimable_project_without_rescue():
    receipts={
        "C1_SHARED_EMERGENT":receipt("C1_SHARED_EMERGENT","FAIL"),
        "C3_QUERY_MEASURED":receipt("C3_QUERY_MEASURED","PASS"),
        "C6_SHARED_QUERY_COMPOSITE":receipt("C6_SHARED_QUERY_COMPOSITE","PASS"),
    }
    bundle=B.validate_bundle(receipts, corrected_relational_replay_status="FAIL")
    assert bundle["candidate_statuses"]["C1_SHARED_EMERGENT"]=="ELIMINATED"
    assert bundle["candidate_statuses"]["C6_SHARED_QUERY_COMPOSITE"]=="BLOCKED_BY_CONSTITUENT"

def test_specialist_is_isolated_and_authority_false():
    receipts={c:receipt(c,"PASS") for c in ("C1_SHARED_EMERGENT","C3_QUERY_MEASURED","C6_SHARED_QUERY_COMPOSITE")}
    receipts["C5_REGULATORY_SPECIALIST"]=receipt("C5_REGULATORY_SPECIALIST","PASS")
    bundle=B.validate_bundle(receipts, corrected_relational_replay_status="FAIL")
    assert bundle["optional_specialists_eligible"]==["C5_REGULATORY_SPECIALIST"]
    assert bundle["target_selected"] is False and bundle["training_authorized"] is False
