from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

ROOT=Path(__file__).resolve().parents[2]
HERE=ROOT/"scripts"/"v79"
sys.path.insert(0,str(HERE))
import run_v79_v2_core_scoring as R  # noqa: E402
import v79_v2_core_score_authority as A  # noqa: E402


def _canon(x): return (json.dumps(x,sort_keys=True,separators=(",",":"),ensure_ascii=False)+"\n").encode("utf-8")
def _sha_bytes(b): return hashlib.sha256(b).hexdigest()


@pytest.fixture(autouse=True)
def _synthetic_frozen_campaign(monkeypatch):
    """Synthetic campaign identity for these unit tests; the frozen production value is pinned in
    test_v79_v2_core_score_orchestrator.py::test_frozen_production_bindings_are_exact_full_values."""
    monkeypatch.setattr(A,"CAMPAIGN_RECEIPT_SHA256","a"*64)


def _auth(campaign_sha="a"*64,code="b"*40):
    return {
        "schema":A.AUTH_SCHEMA,"scoring_authorized":True,"qualification_campaign_controller_pass":True,
        "contract_sha256":A.CONTRACT_SHA256,"root_manifest_sha256":A.ROOT_MANIFEST_SHA256,
        "blinded_index_sha256":A.BLINDED_INDEX_SHA256,"realization_audit_receipt_sha256":A.REALIZATION_AUDIT_RECEIPT_SHA256,
        "campaign_receipt_sha256":campaign_sha,"scorer_code_sha":code,"real_train_posterior_authorized":False,
        "factorial_science_authorized":False,"training_authorized":False,
    }


def test_load_fit_receipts_verifies_every_campaign_hash_and_refuses_extra(tmp_path):
    out=tmp_path/"results"; out.mkdir(); rows=[]
    for i in range(2):
        fid=f"{i+1:064x}"; rec={"fit_id":fid,"schema":"fixture"}; raw=_canon(rec); name=f"fit_{fid}.json"; (out/name).write_bytes(raw)
        rows.append({"fit_id":fid,"path":name,"sha256":_sha_bytes(raw)})
    loaded=R.load_fit_receipts({"fit_records":rows},out)
    assert [x["fit_id"] for x in loaded]==[x["fit_id"] for x in rows]
    extra=out/f"fit_{'f'*64}.json"; extra.write_bytes(_canon({"fit_id":"f"*64}))
    with pytest.raises(R.ScoringRunRefused): R.load_fit_receipts({"fit_records":rows},out)


def test_load_fit_receipts_refuses_missing_or_tampered_file(tmp_path):
    out=tmp_path/"results"; out.mkdir(); fid="1"*64; name=f"fit_{fid}.json"; raw=_canon({"fit_id":fid})
    row={"fit_id":fid,"path":name,"sha256":_sha_bytes(raw)}
    with pytest.raises(R.ScoringRunRefused): R.load_fit_receipts({"fit_records":[row]},out)
    (out/name).write_bytes(raw+b"tamper")
    with pytest.raises(R.ScoringRunRefused): R.load_fit_receipts({"fit_records":[row]},out)


def test_load_scoring_authorization_requires_canonical_exact_hash_and_scorer_head(tmp_path):
    campaign_sha="a"*64; code="b"*40; auth=_auth(campaign_sha,code); raw=_canon(auth); path=tmp_path/"auth.json"; path.write_bytes(raw)
    got=R.load_scoring_authorization(path,expected_sha256=_sha_bytes(raw),campaign_receipt_sha256=campaign_sha,scorer_code_sha=code)
    assert got==auth
    with pytest.raises(R.ScoringRunRefused): R.load_scoring_authorization(path,expected_sha256="c"*64,campaign_receipt_sha256=campaign_sha,scorer_code_sha=code)
    with pytest.raises(Exception): R.load_scoring_authorization(path,expected_sha256=_sha_bytes(raw),campaign_receipt_sha256=campaign_sha,scorer_code_sha="d"*40)


def test_write_json_once_is_canonical_idempotent_and_refuses_change(tmp_path):
    p=tmp_path/"x.json"; obj={"b":2,"a":1}; sha=R.write_json_once(p,obj)
    assert p.read_bytes()==_canon(obj) and sha==_sha_bytes(_canon(obj))
    assert R.write_json_once(p,{"a":1,"b":2})==sha
    with pytest.raises(R.ScoringRunRefused): R.write_json_once(p,{"a":2,"b":2})


def test_new_donor_metric_convention_is_frozen_by_part():
    det={"part":"detection","heldout_predictive":{"new_donor":{"mean_log_loss":0.7}}}
    pos={"part":"positive","heldout_predictive":{"new_donor":{"mean_lpd":-1.3}}}
    assert R.q10_q11_heldout_model_metric(det)==0.7
    assert R.q10_q11_heldout_model_metric(pos)==-1.3
    with pytest.raises(R.ScoringRunRefused): R.q10_q11_heldout_model_metric({"part":"detection","heldout_predictive":{}})


def test_scoring_run_receipt_binds_all_outputs_and_keeps_downstream_off():
    outputs={k:f"{i+1:064x}" for i,k in enumerate(R.SCORING_OUTPUT_KEYS)}
    r=R.scoring_run_receipt(scorer_code_sha="b"*40,campaign_receipt_sha256="a"*64,scoring_authorization_sha256="c"*64,
                            outputs=outputs,authentication_steps=["output_guard"])
    assert r["qualification_scoring_run"] is True
    assert r["real_train_posterior_authorized"] is False and r["factorial_science_authorized"] is False and r["training_authorized"] is False
    assert set(r["outputs"])=={"scored_rows","gate_table","heldout_oracle","descriptive_metrics","adjudication"}
