"""Exact-root teacher-target receipt V4."""
from __future__ import annotations
import hashlib, json
from typing import Mapping, Any
from .current_authority_roots_v4 import CURRENT_V5_RECEIPT_AUTHORITY_ROOTS_V4

KIND="v5_current_teacher_target_receipt_v4"
SCOPE="CURRENT_V5_RNA_PLUS_VALIDATED_E2_TEACHER_TARGET_V4"

def _sha(v: object,name:str)->str:
    if not isinstance(v,str) or len(v)!=64 or v!=v.lower():
        raise ValueError(f"{name} must be lowercase SHA-256")
    int(v,16); return v

def _digest(p):
    return hashlib.sha256(json.dumps(p,sort_keys=True,separators=(",",":"),
                                     ensure_ascii=True,allow_nan=False).encode()).hexdigest()

def _roots(v: object)->dict[str,str]:
    if not isinstance(v,Mapping) or tuple(v)!=CURRENT_V5_RECEIPT_AUTHORITY_ROOTS_V4:
        raise ValueError("receipt roots must exactly match V4 vocabulary")
    return {k:_sha(v[k],k) for k in CURRENT_V5_RECEIPT_AUTHORITY_ROOTS_V4}

def seal_current_teacher_target_receipt_v4(*,target_package_root:str,
                                           authority_roots:Mapping[str,str],
                                           closure_v4_sha256:str)->dict[str,Any]:
    core={"kind":KIND,"scope":SCOPE,
          "target_package_root":_sha(target_package_root,"target_package_root"),
          "authority_roots":_roots(authority_roots),
          "closure_v4_sha256":_sha(closure_v4_sha256,"closure_v4_sha256"),
          "training_authorized":False}
    return {**core,"receipt_digest":_digest(core)}

def validate_current_teacher_target_receipt_v4(receipt:Mapping[str,Any],*,
                                                expected_target_package_root:str,
                                                expected_authority_roots:Mapping[str,str],
                                                expected_closure_v4_sha256:str)->dict[str,Any]:
    fields={"kind","scope","target_package_root","authority_roots","closure_v4_sha256",
            "training_authorized","receipt_digest"}
    if not isinstance(receipt,Mapping) or set(receipt)!=fields:
        raise ValueError("receipt fields must exactly match V4 schema")
    if receipt["kind"]!=KIND or receipt["scope"]!=SCOPE:
        raise ValueError("receipt kind/scope mismatch")
    if receipt["training_authorized"] is not False:
        raise ValueError("receipt cannot authorize training")
    roots=_roots(receipt["authority_roots"])
    if roots!=_roots(expected_authority_roots):
        raise ValueError("receipt roots mismatch")
    if _sha(receipt["target_package_root"],"target_package_root")!=_sha(expected_target_package_root,"expected_target_package_root"):
        raise ValueError("target package root mismatch")
    if _sha(receipt["closure_v4_sha256"],"closure_v4_sha256")!=_sha(expected_closure_v4_sha256,"expected_closure_v4_sha256"):
        raise ValueError("closure V4 mismatch")
    core={k:receipt[k] for k in ("kind","scope","target_package_root","authority_roots",
                                  "closure_v4_sha256","training_authorized")}
    if _sha(receipt["receipt_digest"],"receipt_digest")!=_digest(core):
        raise ValueError("receipt digest mismatch")
    return dict(receipt)
