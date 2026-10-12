from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import pytest

ROOT=Path(__file__).resolve().parents[2]
HERE=ROOT/"scripts"/"v79"
sys.path.insert(0,str(HERE))
import v79_v2_core_score_authority as A  # noqa: E402


def _campaign():
    rows=[{"fit_id":f"{i:064x}","path":f"fit_{i:04d}.json","sha256":f"{i+1:064x}"} for i in range(A.EXPECTED_FITS)]
    return {"schema":A.CAMPAIGN_SCHEMA,"code_sha":"a"*40,"custody_receipt_sha256":"b"*64,
            "planned_fit_count":A.EXPECTED_FITS,"fit_records":rows,"qualification_fits_run":A.EXPECTED_FITS,
            "benchmark_run":False,"scoring_run":False,"truth_accessed":False,"training_authorized":False}


def _auth(campaign_sha="c"*64,code_sha="d"*40):
    return {"schema":A.AUTH_SCHEMA,"scoring_authorized":True,"qualification_campaign_controller_pass":True,
            "contract_sha256":A.CONTRACT_SHA256,"root_manifest_sha256":A.ROOT_MANIFEST_SHA256,
            "blinded_index_sha256":A.BLINDED_INDEX_SHA256,"realization_audit_receipt_sha256":A.REALIZATION_AUDIT_RECEIPT_SHA256,
            "campaign_receipt_sha256":campaign_sha,"scorer_code_sha":code_sha,
            "real_train_posterior_authorized":False,"factorial_science_authorized":False,"training_authorized":False}


def _descriptive():
    return {"schema":A.DESCRIPTIVE_SCHEMA,"gating":False,
            "families":{k:{"status":"STRUCTURAL_FIXTURE"} for k in sorted(A.DESCRIPTIVE_FAMILIES)}}


def _gate_table(*,hard_fail=None,limit_fail=None):
    rows=[]
    for i in range(A.EXPECTED_GATES):
        verdict="LIMIT" if i in {3,7,11,15} else "FAIL"
        passed=not (i==hard_fail or i==limit_fail)
        rows.append({"world":"Q00_BASELINE","part":"detection","gate":f"G{i}","kind":"STAT",
                     "verdict_class":verdict,"passed":passed,"statistic":{},"detail":{},"frozen_gate":{},"interpretation":"CONFIRMATORY"})
    terminal={"terminal":"V2_CORE_SYNTHETIC_QUALIFICATION_NOT_QUALIFIED" if hard_fail is not None else "V2_CORE_SYNTHETIC_QUALIFICATION_QUALIFIED",
              "first_hard_fail_index":hard_fail,"post_terminal_count":0,"limit_failures":1 if limit_fail is not None else 0}
    return {"schema":"V79_V2_CORE_GATE_SCORE_TABLE_V1","rows":rows,"terminal":terminal,
            "counts":{"hard_statistical":260,"hard_rule":28,"limit_statistical":4,"limit_rule":0},"alpha_per_gate":0.05/260}


def test_completed_campaign_requires_exact_1056_fit_ledger_and_boundary_flags(tmp_path):
    rec=_campaign(); raw=A._canon(rec); p=tmp_path/"campaign.json"; p.write_bytes(raw); sha=hashlib.sha256(raw).hexdigest()
    got=A.load_completed_campaign(p,expected_sha256=sha)
    assert got["qualification_fits_run"]==1056 and len(got["fit_records"])==1056
    bad=dict(rec); bad["scoring_run"]=True; p2=tmp_path/"bad.json"; p2.write_bytes(A._canon(bad))
    with pytest.raises(A.ScoreAuthorityRefused): A.load_completed_campaign(p2,expected_sha256=hashlib.sha256(p2.read_bytes()).hexdigest())


def test_scoring_authorization_is_post_campaign_only_and_cannot_cross_downstream_gates():
    campaign="c"*64; code="d"*40
    assert A.validate_scoring_authorization(_auth(campaign,code),campaign_receipt_sha256=campaign,scorer_code_sha=code)["scoring_authorized"] is True
    bad=_auth(campaign,code); bad["training_authorized"]=True
    with pytest.raises(A.ScoreAuthorityRefused): A.validate_scoring_authorization(bad,campaign_receipt_sha256=campaign,scorer_code_sha=code)
    with pytest.raises(A.ScoreAuthorityRefused): A.validate_scoring_authorization(_auth(campaign,code),campaign_receipt_sha256="e"*64,scorer_code_sha=code)
    bad=_auth(campaign,code); bad["blinded_index_sha256"]="f"*64
    with pytest.raises(A.ScoreAuthorityRefused): A.validate_scoring_authorization(bad,campaign_receipt_sha256=campaign,scorer_code_sha=code)


def test_scoring_authorization_refuses_64_hex_pseudo_commit_sha():
    bad=_auth(code_sha="d"*64)
    with pytest.raises(A.ScoreAuthorityRefused):
        A.validate_scoring_authorization(bad,campaign_receipt_sha256="c"*64,scorer_code_sha="d"*64)


def test_descriptive_metrics_require_exact_five_non_gating_families():
    assert A.validate_descriptive_metrics(_descriptive())["gating"] is False
    bad=_descriptive(); bad["families"].pop("positive_heldout")
    with pytest.raises(A.ScoreAuthorityRefused): A.validate_descriptive_metrics(bad)
    bad=_descriptive(); bad["gating"]=True
    with pytest.raises(A.ScoreAuthorityRefused): A.validate_descriptive_metrics(bad)


def test_adjudication_receipt_qualified_hard_fail_and_limit_only_semantics():
    kwargs={"scorer_code_sha":"d"*40,"campaign_receipt_sha256":"c"*64,"scoring_authorization_sha256":"e"*64,"descriptive_metrics":_descriptive()}
    q=A.build_adjudication_receipt(**kwargs,gate_table=_gate_table())
    assert q["terminal"]=="V2_CORE_SYNTHETIC_QUALIFICATION_QUALIFIED" and q["hard_fail_count"]==0
    h=A.build_adjudication_receipt(**kwargs,gate_table=_gate_table(hard_fail=20))
    assert h["terminal"]=="V2_CORE_SYNTHETIC_QUALIFICATION_NOT_QUALIFIED" and h["first_hard_fail_index"]==20 and h["hard_fail_count"]==1
    l=A.build_adjudication_receipt(**kwargs,gate_table=_gate_table(limit_fail=3))
    assert l["terminal"]=="V2_CORE_SYNTHETIC_QUALIFICATION_QUALIFIED" and l["limit_fail_count"]==1 and l["hard_fail_count"]==0


def test_adjudication_refuses_missing_descriptive_family():
    bad=_descriptive(); bad["families"].pop("detection_heldout")
    with pytest.raises(A.ScoreAuthorityRefused):
        A.build_adjudication_receipt(scorer_code_sha="d"*40,campaign_receipt_sha256="c"*64,
            scoring_authorization_sha256="e"*64,gate_table=_gate_table(),descriptive_metrics=bad)


def test_adjudication_receipt_is_write_once(tmp_path):
    rec=A.build_adjudication_receipt(scorer_code_sha="d"*40,campaign_receipt_sha256="c"*64,
        scoring_authorization_sha256="e"*64,gate_table=_gate_table(),descriptive_metrics=_descriptive())
    p=tmp_path/"receipt.json"; first=A.write_adjudication_once(p,rec); second=A.write_adjudication_once(p,rec)
    assert first==second==hashlib.sha256(p.read_bytes()).hexdigest()
    bad=dict(rec); bad["training_authorized"]=True
    with pytest.raises(A.ScoreAuthorityRefused): A.write_adjudication_once(p,bad)
