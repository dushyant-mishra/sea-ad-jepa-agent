#!/usr/bin/env python3
"""Qualification execution custody for V79 V2_CORE.

Controller-side preparation binds the future execution authorization to exact frozen
qualification bytes and the controller-derived opaque seed ledger. Fit-side loading
accepts only the isolated custody directory: blinded inputs, fit-contract view,
sanitary authorization and custody receipt. No root mapping or truth may be present.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

import v79_v2_core_fit_contract as FC
import v79_v2_core_fit_surface as F
import v79_v2_core_qualification_plan as Q

SOURCE_CONTRACT_SHA256 = FC.SOURCE_CONTRACT_SHA256
QUALIFICATION_INDEX_SHA256 = F.QUALIFICATION_INDEX_SHA256
AUTH_SCHEMA = "V79_V2_CORE_QUALIFICATION_EXECUTION_AUTHORIZATION_V1"
AUTH_NAME = "V79_V2_CORE_QUALIFICATION_EXECUTION_AUTHORIZATION_V1.json"
RECEIPT_SCHEMA = "V79_V2_CORE_QUALIFICATION_CUSTODY_V1"
RECEIPT_NAME = "V79_V2_CORE_QUALIFICATION_CUSTODY_V1.json"
FIT_VIEW_NAME = "V79_V2_CORE_FIT_CONTRACT_VIEW_V1.json"
EXPECTED_FITS = 1056


class QualificationCustodyRefused(RuntimeError):
    pass


def _refuse(msg: str):
    raise QualificationCustodyRefused(f"REFUSED V2_CORE qualification custody: {msg}")


def _canonical(obj) -> bytes:
    return (json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def _sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _digest(base: Path) -> str:
    h=hashlib.sha256(); base=Path(base)
    for p in sorted((p for p in base.rglob("*") if p.is_file()), key=lambda x:x.relative_to(base).as_posix()):
        rel=p.relative_to(base).as_posix(); h.update(rel.encode()); h.update(b"\0"); h.update(hashlib.sha256(p.read_bytes()).digest()); h.update(b"\0")
    return h.hexdigest()


def _canonical_ledger(ledger) -> list[dict]:
    if not isinstance(ledger, list) or len(ledger) != EXPECTED_FITS:
        _refuse(f"fit seed ledger must contain exactly {EXPECTED_FITS} records")
    out=[]; seen=set()
    for rec in ledger:
        if not isinstance(rec, Mapping) or set(rec) != {"fit_id", "primary_seed", "escalation_seed"}:
            _refuse("fit seed ledger record schema differs")
        fid=str(rec["fit_id"]); primary=rec["primary_seed"]; escalation=rec["escalation_seed"]
        if not re.fullmatch(r"[0-9a-f]{64}",fid): _refuse("fit seed ledger contains invalid fit_id")
        if fid in seen: _refuse("fit seed ledger contains duplicate identity")
        for name,seed in (("primary_seed",primary),("escalation_seed",escalation)):
            if not isinstance(seed,int) or not (0<=seed<=0xffffffff): _refuse(f"fit seed ledger contains invalid {name}")
        if primary==escalation: _refuse("primary and escalation seeds must differ")
        seen.add(fid); out.append({"fit_id":fid,"primary_seed":int(primary),"escalation_seed":int(escalation)})
    out.sort(key=lambda x:x["fit_id"]); return out


def _contains_forbidden_identity(obj) -> bool:
    text=json.dumps(obj,sort_keys=True)
    forbidden=("Q00","Q01","Q02","Q03","Q04","Q05","Q06","Q07","Q08","Q09","Q10","Q11",
               "world_name","world_index","controller_truth","operator","matrix")
    return any(x in text for x in forbidden)


def sanitize_execution_authorization(auth: Mapping | None, *, expected_seed_ledger: list[Mapping]) -> dict:
    if not isinstance(auth,Mapping) or auth.get("schema")!=AUTH_SCHEMA: _refuse("missing/wrong qualification execution authorization")
    if auth.get("qualification_campaign_authorized") is not True or auth.get("benchmark_controller_pass") is not True:
        _refuse("qualification campaign requires explicit authorization and benchmark controller pass")
    if auth.get("contract_sha256")!=SOURCE_CONTRACT_SHA256 or auth.get("blinded_index_sha256")!=QUALIFICATION_INDEX_SHA256:
        _refuse("authorization does not bind frozen contract/index")
    if auth.get("scoring_authorized") is not False or auth.get("training_authorized") is not False:
        _refuse("authorization crosses later scoring/training gates")
    expected=_canonical_ledger(list(expected_seed_ledger)); observed=_canonical_ledger(copy.deepcopy(auth.get("fit_seed_ledger")))
    if observed!=expected: _refuse("authorization seed ledger differs from controller-derived frozen ledger")
    out={"schema":AUTH_SCHEMA,"qualification_campaign_authorized":True,"benchmark_controller_pass":True,
         "contract_sha256":SOURCE_CONTRACT_SHA256,"blinded_index_sha256":QUALIFICATION_INDEX_SHA256,
         "fit_seed_ledger":observed,"scoring_authorized":False,"training_authorized":False}
    if _contains_forbidden_identity(out): _refuse("sanitized authorization leaks controller identity")
    return out


@dataclass(frozen=True)
class QualificationCustody:
    custody_dir: Path
    receipt_sha256: str
    receipt: Mapping
    fit_contract: Mapping
    authorization: Mapping
    blinded_index: F.BlindedIndex
    queue: tuple[Mapping, ...]
    seeds_by_fit_id: Mapping[str,Mapping[str,int]]


def load_qualification_custody(custody_dir: Path, *, expected_receipt_sha256: str) -> QualificationCustody:
    custody_dir=Path(custody_dir)
    if not re.fullmatch(r"[0-9a-f]{64}",str(expected_receipt_sha256)): _refuse("64-hex custody receipt SHA required")
    if not custody_dir.is_dir(): _refuse("custody directory missing")
    expected_top={F.FIT_ROOT_NAME,FIT_VIEW_NAME,AUTH_NAME,RECEIPT_NAME}; top={p.name for p in custody_dir.iterdir()}
    if top!=expected_top: _refuse(f"custody top-level set differs; extra={sorted(top-expected_top)}, missing={sorted(expected_top-top)}")
    rpath=custody_dir/RECEIPT_NAME; raw=rpath.read_bytes(); actual=hashlib.sha256(raw).hexdigest()
    if actual!=expected_receipt_sha256: _refuse("custody receipt hash mismatch")
    try: receipt=json.loads(raw.decode("utf-8"))
    except Exception as exc: _refuse(f"invalid custody receipt: {exc}")
    if _canonical(receipt)!=raw or receipt.get("schema")!=RECEIPT_SCHEMA: _refuse("noncanonical/wrong custody receipt")
    if _contains_forbidden_identity(receipt): _refuse("custody receipt leaks controller identity")
    required={"schema","executor_code_head","source_contract_sha256","root_manifest_sha256","blinded_index_sha256",
              "blinded_directory_digest","fit_contract_view_path","fit_contract_view_sha256","authorization_path",
              "authorization_sha256","fit_count","ppc_draws","donor_draws_stored","qualification_fits_run",
              "scoring_run","truth_accessed","training_authorized"}
    if set(receipt)!=required: _refuse("custody receipt key set differs")
    if receipt.get("source_contract_sha256")!=SOURCE_CONTRACT_SHA256 or receipt.get("root_manifest_sha256")!=F.QUALIFICATION_ROOT_MANIFEST_SHA256 or receipt.get("blinded_index_sha256")!=QUALIFICATION_INDEX_SHA256:
        _refuse("custody does not bind frozen qualification authority")
    if receipt.get("fit_count")!=EXPECTED_FITS or receipt.get("qualification_fits_run")!=0 or receipt.get("scoring_run") is not False or receipt.get("truth_accessed") is not False or receipt.get("training_authorized") is not False:
        _refuse("custody execution boundary differs")
    if not isinstance(receipt.get("ppc_draws"),int) or receipt["ppc_draws"]<=0 or not isinstance(receipt.get("donor_draws_stored"),int) or receipt["donor_draws_stored"]<=0:
        _refuse("qualification output counts are missing/invalid")
    fit_contract=FC.load_fit_contract_view(custody_dir/FIT_VIEW_NAME,expected_sha256=str(receipt["fit_contract_view_sha256"]))
    apath=custody_dir/AUTH_NAME
    if _sha(apath)!=receipt.get("authorization_sha256"): _refuse("authorization hash mismatch")
    try: auth=json.loads(apath.read_text(encoding="utf-8"))
    except Exception as exc: _refuse(f"invalid authorization: {exc}")
    if _canonical(auth)!=apath.read_bytes() or _contains_forbidden_identity(auth): _refuse("authorization bytes/identity firewall differ")
    fit_root=custody_dir/F.FIT_ROOT_NAME
    if _digest(fit_root)!=receipt.get("blinded_directory_digest"): _refuse("blinded directory digest mismatch")
    index_path=fit_root/F.FIT_INDEX_NAME
    if _sha(index_path)!=QUALIFICATION_INDEX_SHA256: _refuse("qualification blinded index hash mismatch")
    index_json=json.loads(index_path.read_text(encoding="utf-8"))
    index=F.BlindedIndex(fit_root=fit_root,execution_mode="QUALIFICATION_TRUTH_FREEZE",
        root_manifest_sha256=F.QUALIFICATION_ROOT_MANIFEST_SHA256,index_sha256=QUALIFICATION_INDEX_SHA256,
        index=index_json,opaque_world_ids=tuple(x["opaque_world_id"] for x in index_json["worlds"]))
    queue=Q.build_qualification_queue(fit_contract,index_json)
    expected_ids={x["fit_id"] for x in queue}
    ledger=_canonical_ledger(auth.get("fit_seed_ledger"))
    seeds_by={x["fit_id"]:{"primary_seed":int(x["primary_seed"]),"escalation_seed":int(x["escalation_seed"])} for x in ledger}
    if set(seeds_by)!=expected_ids: _refuse("authorization seed ledger does not cover exact qualification queue")
    if auth.get("schema")!=AUTH_SCHEMA or auth.get("qualification_campaign_authorized") is not True or auth.get("benchmark_controller_pass") is not True or auth.get("contract_sha256")!=SOURCE_CONTRACT_SHA256 or auth.get("blinded_index_sha256")!=QUALIFICATION_INDEX_SHA256 or auth.get("scoring_authorized") is not False or auth.get("training_authorized") is not False:
        _refuse("authorization semantics differ")
    return QualificationCustody(custody_dir,actual,receipt,fit_contract,auth,index,tuple(queue),seeds_by)
