import hashlib, importlib.util, json
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[2]
MOD=ROOT/"scripts/v5/td_gate_case_coverage.py"
spec=importlib.util.spec_from_file_location("td_gate_case_coverage",MOD)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def canonical(obj):
    return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()


def prefreeze():
    core={
      "schema":"JEPA_TD_TARGET_TOURNAMENT_PREFREEZE_MANIFEST_V1",
      "fixture_only":True,
      "family_alpha":0.05,
      "multiplicity_method":"BONFERRONI",
      "decision_family_size":3,
      "decision_family_registry_sha256":"a"*64,
      "alpha_eff":0.05/3,
      "minimum_nonzero_donors_for_sign_resolution":7,
      "minimum_permutation_draws_for_resolution":59,
      "tournament_contract_sha256":"b"*64,
      "null_seed_material":"seed",
      "case_resolution":[
        {"case_id":"c_hvs","candidate_id":"C1_RELATIONAL_SHARED","gate_id":"G1_DONOR_PRIMARY","source":"HVS","analysis_tier":"discovery","endpoint_id":"recurrence","available_donors_upper_bound":20,"resolution_impossible_from_donor_upper_bound":False,"estimability_proven":False,"biological_result":"NOT_OPENED"},
        {"case_id":"c_nph","candidate_id":"C1_RELATIONAL_SHARED","gate_id":"G1_DONOR_PRIMARY","source":"NPH52","analysis_tier":"discovery","endpoint_id":"recurrence","available_donors_upper_bound":16,"resolution_impossible_from_donor_upper_bound":False,"estimability_proven":False,"biological_result":"NOT_OPENED"},
        {"case_id":"other","candidate_id":"C2_QUERY_MEASURED","gate_id":"G1_DONOR_PRIMARY","source":"HVS","analysis_tier":"discovery","endpoint_id":"query","available_donors_upper_bound":20,"resolution_impossible_from_donor_upper_bound":False,"estimability_proven":False,"biological_result":"NOT_OPENED"},
      ],
      "authority":{
       "value_read_authorized":False,"real_tournament_authorized":False,"target_selection_authorized":False,
       "representation_selection_authorized":False,"td60_authorized":False,"stage4_authorized":False,"training_authorized":False,
      },
    }
    out=dict(core); out["manifest_sha256"]=canonical(core); return out


def receipts():
    return [
      {"case_id":"c_hvs","candidate_id":"C1_RELATIONAL_SHARED","gate_id":"G1_DONOR_PRIMARY","source":"HVS","analysis_tier":"discovery","endpoint_id":"recurrence","status":"PASS","evidence_sha256":"1"*64},
      {"case_id":"c_nph","candidate_id":"C1_RELATIONAL_SHARED","gate_id":"G1_DONOR_PRIMARY","source":"NPH52","analysis_tier":"discovery","endpoint_id":"recurrence","status":"NOT_ESTIMABLE","evidence_sha256":"2"*64},
    ]


def audit(p=None, r=None, *, candidate_id="C1_RELATIONAL_SHARED", gate_id="G1_DONOR_PRIMARY", expected_sha=None):
    p = prefreeze() if p is None else p
    expected_sha = p["manifest_sha256"] if expected_sha is None else expected_sha
    return m.audit_gate_case_coverage(
        p,
        expected_prefreeze_manifest_sha256=expected_sha,
        candidate_id=candidate_id,
        gate_id=gate_id,
        case_receipts=receipts() if r is None else r,
    )


def test_complete_coverage_is_accepted_without_gate_adjudication():
    out=audit()
    assert out["coverage_complete"] is True
    assert out["expected_case_count"]==2
    assert out["status_counts"]=={"PASS":1,"FAIL":0,"NOT_ESTIMABLE":1}
    assert out["gate_status_not_adjudicated"] is True
    assert "pass" not in out


def test_missing_case_rejected():
    with pytest.raises(m.CoverageError): audit(r=receipts()[:1])


def test_extra_case_rejected():
    r=receipts()+[{"case_id":"extra","candidate_id":"C1_RELATIONAL_SHARED","gate_id":"G1_DONOR_PRIMARY","source":"SEA_AD","analysis_tier":"discovery","endpoint_id":"recurrence","status":"PASS","evidence_sha256":"3"*64}]
    with pytest.raises(m.CoverageError): audit(r=r)


def test_role_relabel_rejected():
    r=receipts(); r[0]=dict(r[0]); r[0]["source"]="SEA_AD"
    with pytest.raises(m.CoverageError): audit(r=r)


def test_duplicate_case_receipts_rejected():
    r=[receipts()[0],dict(receipts()[0])]
    with pytest.raises(m.CoverageError): audit(r=r)


def test_altered_prefreeze_after_hash_rejected():
    p=prefreeze(); frozen_sha=p["manifest_sha256"]; p["case_resolution"][0]["source"]="SEA_AD"
    with pytest.raises(m.CoverageError): audit(p=p, expected_sha=frozen_sha)


def test_unknown_status_rejected():
    r=receipts(); r[0]=dict(r[0]); r[0]["status"]="MAYBE"
    with pytest.raises(m.CoverageError): audit(r=r)


def test_bad_evidence_sha_rejected():
    r=receipts(); r[0]=dict(r[0]); r[0]["evidence_sha256"]="bad"
    with pytest.raises(m.CoverageError): audit(r=r)


def test_unknown_candidate_gate_pair_rejected():
    with pytest.raises(m.CoverageError):
        audit(candidate_id="C5_REGULATORY_SPECIALIST",gate_id="M1_CIRCULARITY_CONTROL",r=[])


def test_output_authority_is_false_and_bundle_hash_deterministic():
    a=audit(); b=audit(r=list(reversed(receipts())))
    assert a["case_evidence_bundle_sha256"]==b["case_evidence_bundle_sha256"]
    assert all(v is False for v in a["authority"].values())
