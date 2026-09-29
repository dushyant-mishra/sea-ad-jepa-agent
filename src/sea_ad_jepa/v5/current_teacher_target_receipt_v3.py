"""Exact-root V3 teacher-target receipt."""
from __future__ import annotations
import hashlib,json
from typing import Any,Mapping
from .current_authority_roots_v3 import CURRENT_V5_RECEIPT_AUTHORITY_ROOTS_V3
KIND="v5_current_teacher_target_receipt_v3";SCOPE="CURRENT_V5_DATASET_DERIVED_TEACHER_TARGET_V3"
def _sha(v:object,n:str)->str:
    if not isinstance(v,str) or len(v)!=64 or v!=v.lower():raise ValueError(f"{n} must be lowercase SHA-256")
    try:int(v,16)
    except ValueError as e:raise ValueError(f"{n} must be lowercase SHA-256") from e
    return v
def _digest(p:Mapping[str,Any])->str:return hashlib.sha256(json.dumps(p,sort_keys=True,separators=(",",":"),ensure_ascii=True,allow_nan=False).encode()).hexdigest()
def _roots(v):
    if not isinstance(v,Mapping) or tuple(v)!=CURRENT_V5_RECEIPT_AUTHORITY_ROOTS_V3:raise ValueError("authority_roots must exactly match V3 receipt roots")
    return {k:_sha(v[k],k) for k in CURRENT_V5_RECEIPT_AUTHORITY_ROOTS_V3}
def _core(target_package_root,authority_roots,closure_v3_sha256):return {"kind":KIND,"scope":SCOPE,"target_package_root":_sha(target_package_root,"target_package_root"),"authority_roots":_roots(authority_roots),"closure_v3_sha256":_sha(closure_v3_sha256,"closure_v3_sha256"),"training_authorized":False}
def seal_current_teacher_target_receipt_v3(*,target_package_root,authority_roots,closure_v3_sha256):
    c=_core(target_package_root,authority_roots,closure_v3_sha256);return {**c,"receipt_digest":_digest(c)}
def validate_current_teacher_target_receipt_v3(receipt:Mapping[str,Any],*,expected_target_package_root,expected_authority_roots,expected_closure_v3_sha256):
    if not isinstance(receipt,Mapping):raise ValueError("receipt must be mapping")
    c=_core(receipt.get("target_package_root"),receipt.get("authority_roots"),receipt.get("closure_v3_sha256"))
    if receipt.get("kind")!=KIND or receipt.get("scope")!=SCOPE or receipt.get("training_authorized") is not False:raise ValueError("receipt V3 kind/scope/state mismatch")
    if c["target_package_root"]!=_sha(expected_target_package_root,"expected_target_package_root") or c["authority_roots"]!=_roots(expected_authority_roots) or c["closure_v3_sha256"]!=_sha(expected_closure_v3_sha256,"expected_closure_v3_sha256"):raise ValueError("receipt V3 binding mismatch")
    d=_sha(receipt.get("receipt_digest"),"receipt_digest")
    if d!=_digest(c):raise ValueError("receipt digest mismatch")
    return {**c,"receipt_digest":d}
