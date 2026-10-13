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
BLINDED_INDEX_SHA256="8ea3e0cb6637c97b3e940eac54476622bd4f790febb07abee2e8ccdeea751e40"
REALIZATION_AUDIT_RECEIPT_SHA256="6bd05349516a969ac7e83fc991d03d6274335b22068f8c6577f5a9de11b3f9b3"
CAMPAIGN_SCHEMA="V79_V2_CORE_QUALIFICATION_CAMPAIGN_RECEIPT_V1"
AUTH_SCHEMA="V79_V2_CORE_QUALIFICATION_SCORING_AUTHORIZATION_V1"
DESCRIPTIVE_SCHEMA="V79_V2_CORE_DESCRIPTIVE_METRICS_V1"
ADJUDICATION_SCHEMA="V79_V2_CORE_QUALIFICATION_ADJUDICATION_V1"
EXPECTED_FITS=1056
EXPECTED_GATES=292
# Frozen completed qualification campaign (evidence/v79-qualification-campaign-complete-a61437ba-20261013).
CAMPAIGN_RECEIPT_SHA256="a0065925789c58409a85ccbf72d24f5c7b1be142a4d17eddc434babdf0d0e340"
CAMPAIGN_CODE_SHA="a61437ba284e9e75b0557157ad68e56eacd8f8fe"
CUSTODY_RECEIPT_SHA256="c5116d6273f82fd3b3c5450b6bb8d701e03ef7d17ba6ada98eb5ff5aec906b63"
RESULT_LEDGER_SHA256="d467bb9b51336278ee46566173148a4f112eaa79cf578b8bbfae502cb4388b89"
RESULT_FILE_COUNT=2113
NOT_DIAGNOSED_FIT_IDS=frozenset({
    "09bbe252aeb91c12eb996fbd60e5a420237ba4f317255278cdc6e4bfacf9daa6",
    "6ca5f0876ccdac9c86bf5b2f07a4413fdd9f8b824ec8ad45ae84090d657e2f43",
    "ede8a3a369d69133a85fa4a35a3bd24ca87e4a6c680599b671b9693efe7104a5",
})
# Frozen realization authority (results/v79/v2_core_realization_audit_freeze_v1, receipt above).
REALIZATION_LEDGER_SHA256="4e65f213d2eeb2d66b8bd7a9031eeb47eadee5801a9bd0880bd3c78dae88cd65"
WORLD_SET_DIRECTORY_DIGEST="40458efea66e62f3f39cb773641d29c24b80505529baa65bdab31d3975a2a286"
REALIZED_FILE_COUNT=498
CONTROLLER_TRUTH_FILE_COUNT=350
COMMITTED_PACKAGE_FILE_COUNT=366
BLINDED_FIT_FILE_COUNT=145
DESCRIPTIVE_FAMILIES={"parameter_recovery","donor_recovery","detection_heldout","positive_heldout","ppc_q10_q11_second_stage"}

class ScoreAuthorityRefused(RuntimeError): pass

def _refuse(msg:str): raise ScoreAuthorityRefused(f"REFUSED V2_CORE scoring authority: {msg}")
def _canon(obj:Mapping)->bytes: return (json.dumps(dict(obj),sort_keys=True,separators=(",",":"),ensure_ascii=False)+"\n").encode("utf-8")
def _hex64(value)->bool: return isinstance(value,str) and re.fullmatch(r"[0-9a-f]{64}",value) is not None
def _git_sha(value)->bool: return isinstance(value,str) and re.fullmatch(r"[0-9a-f]{40}",value) is not None


def load_completed_campaign(path:Path, *, expected_sha256:str)->dict:
    path=Path(path)
    if not _hex64(expected_sha256) or not path.is_file(): _refuse("campaign receipt path/hash missing")
    if expected_sha256!=CAMPAIGN_RECEIPT_SHA256: _refuse("expected campaign receipt is not the frozen completed campaign")
    raw=path.read_bytes(); actual=hashlib.sha256(raw).hexdigest()
    if actual!=expected_sha256: _refuse("campaign receipt SHA-256 mismatch")
    try: rec=json.loads(raw.decode("utf-8"))
    except Exception as exc: _refuse(f"invalid campaign receipt JSON: {exc}")
    if _canon(rec)!=raw or rec.get("schema")!=CAMPAIGN_SCHEMA: _refuse("campaign receipt schema/canonical bytes differ")
    if rec.get("code_sha")!=CAMPAIGN_CODE_SHA:
        _refuse(f"campaign code head {rec.get('code_sha')!r} differs from the frozen campaign code head")
    if rec.get("custody_receipt_sha256")!=CUSTODY_RECEIPT_SHA256:
        _refuse("campaign custody receipt differs from the frozen custody receipt")
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
              "root_manifest_sha256","blinded_index_sha256","realization_audit_receipt_sha256","campaign_receipt_sha256",
              "scorer_code_sha","real_train_posterior_authorized","factorial_science_authorized","training_authorized"}
    if set(auth)!=required: _refuse("scoring authorization key set differs")
    if auth.get("scoring_authorized") is not True or auth.get("qualification_campaign_controller_pass") is not True:
        _refuse("scoring requires explicit post-campaign controller PASS")
    if (auth.get("contract_sha256")!=CONTRACT_SHA256 or auth.get("root_manifest_sha256")!=ROOT_MANIFEST_SHA256 or
        auth.get("blinded_index_sha256")!=BLINDED_INDEX_SHA256 or auth.get("realization_audit_receipt_sha256")!=REALIZATION_AUDIT_RECEIPT_SHA256):
        _refuse("scoring authorization does not bind frozen V79 authorities")
    if not _hex64(campaign_receipt_sha256) or auth.get("campaign_receipt_sha256")!=campaign_receipt_sha256:
        _refuse("scoring authorization campaign receipt hash differs")
    if campaign_receipt_sha256!=CAMPAIGN_RECEIPT_SHA256:
        _refuse("scoring authorization must bind the frozen completed campaign receipt")
    if not _git_sha(scorer_code_sha) or auth.get("scorer_code_sha")!=scorer_code_sha:
        _refuse("scoring authorization scorer code head differs")
    if auth.get("real_train_posterior_authorized") is not False or auth.get("factorial_science_authorized") is not False or auth.get("training_authorized") is not False:
        _refuse("scoring authorization crosses downstream gates")
    return dict(auth)


def validate_descriptive_metrics(metrics:Mapping|None)->dict:
    if not isinstance(metrics,Mapping) or metrics.get("schema")!=DESCRIPTIVE_SCHEMA: _refuse("descriptive metric schema differs")
    if set(metrics)!={"schema","gating","families"} or metrics.get("gating") is not False:
        _refuse("descriptive metrics must be explicitly non-gating")
    fam=metrics.get("families")
    if not isinstance(fam,Mapping) or set(fam)!=DESCRIPTIVE_FAMILIES: _refuse("five frozen descriptive metric families are required")
    if any(not isinstance(fam[k],Mapping) for k in DESCRIPTIVE_FAMILIES): _refuse("descriptive metric family payload differs")
    return dict(metrics)


def build_adjudication_receipt(*, scorer_code_sha:str, campaign_receipt_sha256:str, scoring_authorization_sha256:str,
                               gate_table:Mapping, descriptive_metrics:Mapping)->dict:
    if not _git_sha(scorer_code_sha): _refuse("scorer_code_sha must be an exact 40-hex Git commit")
    for label,value in (("campaign_receipt_sha256",campaign_receipt_sha256),("scoring_authorization_sha256",scoring_authorization_sha256)):
        if not _hex64(value): _refuse(f"{label} must be 64-hex")
    if campaign_receipt_sha256!=CAMPAIGN_RECEIPT_SHA256: _refuse("adjudication must bind the frozen completed campaign receipt")
    if not isinstance(gate_table,Mapping) or gate_table.get("schema")!="V79_V2_CORE_GATE_SCORE_TABLE_V1": _refuse("gate table schema differs")
    rows=gate_table.get("rows"); terminal=gate_table.get("terminal")
    if not isinstance(rows,list) or len(rows)!=EXPECTED_GATES or not isinstance(terminal,Mapping): _refuse("gate table is incomplete")
    term=terminal.get("terminal")
    if term not in {"V2_CORE_SYNTHETIC_QUALIFICATION_QUALIFIED","V2_CORE_SYNTHETIC_QUALIFICATION_NOT_QUALIFIED"}: _refuse("gate table terminal differs")
    hard_fail=[r for r in rows if r.get("verdict_class")=="FAIL" and r.get("passed") is False]
    limit_fail=[r for r in rows if r.get("verdict_class")=="LIMIT" and r.get("passed") is False]
    expected_term="V2_CORE_SYNTHETIC_QUALIFICATION_NOT_QUALIFIED" if hard_fail else "V2_CORE_SYNTHETIC_QUALIFICATION_QUALIFIED"
    if term!=expected_term: _refuse("terminal does not agree with hard-fail rows")
    first_index=terminal.get("first_hard_fail_index")
    expected_first=None if not hard_fail else next(i for i,r in enumerate(rows) if r.get("verdict_class")=="FAIL" and r.get("passed") is False)
    if first_index!=expected_first: _refuse("terminal first-hard-fail index differs from gate rows")
    descriptive=validate_descriptive_metrics(descriptive_metrics)
    return {
        "schema":ADJUDICATION_SCHEMA,"contract_sha256":CONTRACT_SHA256,"root_manifest_sha256":ROOT_MANIFEST_SHA256,
        "blinded_index_sha256":BLINDED_INDEX_SHA256,"realization_audit_receipt_sha256":REALIZATION_AUDIT_RECEIPT_SHA256,
        "campaign_receipt_sha256":campaign_receipt_sha256,"scoring_authorization_sha256":scoring_authorization_sha256,
        "scorer_code_sha":scorer_code_sha,"gate_count":EXPECTED_GATES,"hard_fail_count":len(hard_fail),
        "limit_fail_count":len(limit_fail),"terminal":term,"first_hard_fail_index":first_index,
        "gate_table_sha256":hashlib.sha256(_canon(gate_table)).hexdigest(),"descriptive_metrics":descriptive,
        "qualification_scoring_run":True,"real_train_posterior_authorized":False,
        "factorial_science_authorized":False,"training_authorized":False,
    }


def write_adjudication_once(path:Path, receipt:Mapping)->str:
    path=Path(path); raw=_canon(receipt); digest=hashlib.sha256(raw).hexdigest()
    if path.exists():
        if path.read_bytes()!=raw: _refuse("existing adjudication receipt differs")
        return digest
    path.parent.mkdir(parents=True,exist_ok=True); path.write_bytes(raw); return digest
