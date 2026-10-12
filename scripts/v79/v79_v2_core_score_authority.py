#!/usr/bin/env python3
"""Controller-only scoring authorization and immutable adjudication receipts for V79 V2_CORE.

This module never fits. It requires a separately issued post-campaign scoring
authorization bound to the exact completed qualification campaign receipt, frozen
contract and frozen realization authority. Training and real-data inference remain off.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Mapping

CONTRACT_SHA256="57e19295be824dbbb023b60a57c5039dac1f9d74e66fefe1008fc27d30fdaf26"
ROOT_MANIFEST_SHA256="84949723305dc2211ebcd451b64dd9adc8518f3580d2122f5600fcf4b38de0de"
REALIZATION_AUDIT_RECEIPT_SHA256="6bd05349516a969ac7e83fc991d03d6274335b22068f8c6577f5a9de11b3f9b3"
CAMPAIGN_SCHEMA="V79_V2_CORE_QUALIFICATION_CAMPAIGN_RECEIPT_V1"
AUTH_SCHEMA="V79_V2_CORE_QUALIFICATION_SCORING_AUTHORIZATION_V1"
ADJUDICATION_SCHEMA="V79_V2_CORE_QUALIFICATION_ADJUDICATION_V1"
EXPECTED_FITS=1056
EXPECTED_GATES=292

class ScoreAuthorityRefused(RuntimeError): pass

def _refuse(msg:str): raise ScoreAuthorityRefused(f"REFUSED V2_CORE scoring authority: {msg}")
def _sha(path:Path)->str: return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def _canon(obj:Mapping)->bytes: return (json.dumps(dict(obj),sort_keys=True,separators=(",",":"),ensure_ascii=False)+"\n").encode("utf-8")
def _hex64(value)->bool: return isinstance(value,str) and re.fullmatch(r"[0-9a-f]{64}",value) is not None


def load_completed_campaign(path:Path, *, expected_sha256:str)->dict:
    path=Path(path)
    if not _hex64(expected_sha256) or not path.is_file(): _refuse("campaign receipt path/hash missing")
    raw=path.read_bytes(); actual=hashlib.sha256(raw).hexdigest()
    if actual!=expected_sha256: _refuse("campaign receipt SHA-256 mismatch")
    try: rec=json.loads(raw.decode("utf-8"))
    except Exception as exc: _refuse(f"invalid campaign receipt JSON: {exc}")
    if _canon(rec)!=raw or rec.get("schema")!=CAMPAIGN_SCHEMA: _refuse("campaign receipt schema/canonical bytes differ")
    if rec.get("planned_fit_count")!=EXPECTED_FITS or rec.get("qualification_fits_run")!=EXPECTED_FITS:
        _refuse("campaign receipt is not the complete 1,056-fit campaign")
    if rec.get("benchmark_run") is not False or rec.get("scoring_run") is not False or rec.get("truth_accessed") is not False or rec.get("training_authorized") is not False:
        _refuse("campaign receipt crosses scoring/training boundary")
    rows=rec.get("fit_records")
    if not isinstance(rows,list) or len(rows)!=EXPECTED_FITS: _refuse("campaign fit-record ledger cardinality differs")
    seen=set()
    for row in rows:
        if not isinstance(row,Mapping) or set(row)!={"fit_id","path","sha256"}: _refuse("campaign fit-record schema differs")
        fid=row.get("fit_id"); sha=row.get("sha256"); rel=row.get("path")
        if not _hex64(fid) or not _hex64(sha) or not isinstance(rel,str) or Path(rel).name!=rel:
            _refuse("campaign fit-record identity/path/hash differs")
        if fid in seen: _refuse("duplicate fit identity in campaign receipt")
        seen.add(fid)
    return rec


def validate_scoring_authorization(auth:Mapping|None, *, campaign_receipt_sha256:str, scorer_code_sha:str)->dict:
    if not isinstance(auth,Mapping) or auth.get("schema")!=AUTH_SCHEMA: _refuse("missing/wrong scoring authorization")
    required={"schema","scoring_authorized","qualification_campaign_controller_pass","contract_sha256",
              "root_manifest_sha256","realization_audit_receipt_sha256","campaign_receipt_sha256",
              "scorer_code_sha","real_train_posterior_authorized","factorial_science_authorized","training_authorized"}
    if set(auth)!=required: _refuse("scoring authorization key set differs")
    if auth.get("scoring_authorized") is not True or auth.get("qualification_campaign_controller_pass") is not True:
        _refuse("scoring requires explicit post-campaign controller PASS")
    if auth.get("contract_sha256")!=CONTRACT_SHA256 or auth.get("root_manifest_sha256")!=ROOT_MANIFEST_SHA256 or auth.get("realization_audit_receipt_sha256")!=REALIZATION_AUDIT_RECEIPT_SHA256:
        _refuse("scoring authorization does not bind frozen V79 authorities")
    if not _hex64(campaign_receipt_sha256) or auth.get("campaign_receipt_sha256")!=campaign_receipt_sha256:
        _refuse("scoring authorization campaign receipt hash differs")
    if not _hex64(scorer_code_sha) or auth.get("scorer_code_sha")!=scorer_code_sha:
        _refuse("scoring authorization scorer code head differs")
    if auth.get("real_train_posterior_authorized") is not False or auth.get("factorial_science_authorized") is not False or auth.get("training_authorized") is not False:
        _refuse("scoring authorization crosses downstream gates")
    return dict(auth)


def build_adjudication_receipt(*, scorer_code_sha:str, campaign_receipt_sha256:str, scoring_authorization_sha256:str,
                               gate_table:Mapping, descriptive_metrics:Mapping|None=None)->dict:
    for label,value in (("scorer_code_sha",scorer_code_sha),("campaign_receipt_sha256",campaign_receipt_sha256),
                        ("scoring_authorization_sha256",scoring_authorization_sha256)):
        if not _hex64(value): _refuse(f"{label} must be 64-hex")
    if not isinstance(gate_table,Mapping): _refuse("gate table missing")
    rows=gate_table.get("rows"); terminal=gate_table.get("terminal")
    if not isinstance(rows,list) or len(rows)!=EXPECTED_GATES or not isinstance(terminal,Mapping): _refuse("gate table is incomplete")
    term=terminal.get("terminal")
    if term not in {"V2_CORE_SYNTHETIC_QUALIFICATION_QUALIFIED","V2_CORE_SYNTHETIC_QUALIFICATION_NOT_QUALIFIED"}:
        _refuse("gate table terminal differs")
    hard_fail=[r for r in rows if r.get("verdict_class")=="FAIL" and r.get("status")=="FAIL"]
    limit_fail=[r for r in rows if r.get("verdict_class")=="LIMIT" and r.get("status")=="FAIL"]
    expected_term="V2_CORE_SYNTHETIC_QUALIFICATION_NOT_QUALIFIED" if hard_fail else "V2_CORE_SYNTHETIC_QUALIFICATION_QUALIFIED"
    if term!=expected_term: _refuse("terminal does not agree with hard-fail rows")
    rec={
        "schema":ADJUDICATION_SCHEMA,
        "contract_sha256":CONTRACT_SHA256,
        "root_manifest_sha256":ROOT_MANIFEST_SHA256,
        "realization_audit_receipt_sha256":REALIZATION_AUDIT_RECEIPT_SHA256,
        "campaign_receipt_sha256":campaign_receipt_sha256,
        "scoring_authorization_sha256":scoring_authorization_sha256,
        "scorer_code_sha":scorer_code_sha,
        "gate_count":EXPECTED_GATES,
        "hard_fail_count":len(hard_fail),
        "limit_fail_count":len(limit_fail),
        "terminal":term,
        "first_hard_fail":terminal.get("first_hard_fail"),
        "gate_table_sha256":hashlib.sha256(_canon(gate_table)).hexdigest(),
        "descriptive_metrics":dict(descriptive_metrics or {}),
        "qualification_scoring_run":True,
        "real_train_posterior_authorized":False,
        "factorial_science_authorized":False,
        "training_authorized":False,
    }
    return rec


def write_adjudication_once(path:Path, receipt:Mapping)->str:
    path=Path(path); raw=_canon(receipt); digest=hashlib.sha256(raw).hexdigest()
    if path.exists():
        if path.read_bytes()!=raw: _refuse("existing adjudication receipt differs")
        return digest
    path.parent.mkdir(parents=True,exist_ok=True); path.write_bytes(raw); return digest
