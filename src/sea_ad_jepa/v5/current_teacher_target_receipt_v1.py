"""Exact-root current-V5 teacher-target receipt; schema validity is not training authority."""
from __future__ import annotations
import hashlib, json
from typing import Any, Mapping
from .current_authority_roots_v1 import CURRENT_V5_RECEIPT_AUTHORITY_ROOTS

KIND='v5_current_teacher_target_receipt_v1'
SCOPE='CURRENT_V5_DATASET_DERIVED_TEACHER_TARGET'

def _sha(v:object,name:str)->str:
    if not isinstance(v,str) or len(v)!=64 or v!=v.lower(): raise ValueError(f"{name} must be a lowercase SHA-256 digest")
    try: int(v,16)
    except ValueError as exc: raise ValueError(f"{name} must be a lowercase SHA-256 digest") from exc
    return v
def _digest(p:Mapping[str,Any])->str:
    return hashlib.sha256(json.dumps(p,sort_keys=True,separators=(",",":"),ensure_ascii=True,allow_nan=False).encode()).hexdigest()
def _roots(values:object)->dict[str,str]:
    if not isinstance(values,Mapping): raise ValueError('authority_roots must be a mapping')
    if set(values)!=set(CURRENT_V5_RECEIPT_AUTHORITY_ROOTS): raise ValueError('authority_roots must exactly match current V5 receipt roots')
    return {name:_sha(values[name],name) for name in CURRENT_V5_RECEIPT_AUTHORITY_ROOTS}
def _core(target_package_root:str, authority_roots:object)->dict[str,Any]:
    return {'kind':KIND,'scope':SCOPE,'target_package_root':_sha(target_package_root,'target_package_root'),'authority_roots':_roots(authority_roots),'training_authorized':False}
def seal_current_teacher_target_receipt_v1(target_package_root:str, authority_roots:Mapping[str,str])->dict[str,Any]:
    core=_core(target_package_root,authority_roots)
    return {**core,'receipt_digest':_digest(core)}
def validate_current_teacher_target_receipt_v1(receipt:Mapping[str,Any],*,expected_target_package_root:str,expected_authority_roots:Mapping[str,str])->dict[str,Any]:
    if not isinstance(receipt,Mapping): raise ValueError('receipt must be a mapping')
    expected_keys={'kind','scope','target_package_root','authority_roots','training_authorized','receipt_digest'}
    if set(receipt)!=expected_keys: raise ValueError('receipt fields must exactly match current schema')
    if receipt.get('kind')!=KIND: raise ValueError('receipt kind mismatch')
    if receipt.get('scope')!=SCOPE: raise ValueError('receipt scope mismatch')
    if receipt.get('training_authorized') is not False: raise ValueError('receipt cannot authorize training')
    expected_root=_sha(expected_target_package_root,'expected_target_package_root')
    expected_roots=_roots(expected_authority_roots)
    core=_core(receipt.get('target_package_root'),receipt.get('authority_roots'))
    if core['target_package_root']!=expected_root: raise ValueError('target_package_root mismatch')
    if core['authority_roots']!=expected_roots: raise ValueError('authority_roots mismatch')
    digest=_sha(receipt.get('receipt_digest'),'receipt_digest')
    if digest!=_digest(core): raise ValueError('receipt digest mismatch')
    return {**core,'receipt_digest':digest}
