"""Fail-closed q-safety authority: token, denominator/QC, and teacher target."""
from __future__ import annotations
from dataclasses import dataclass
import hashlib,json
from typing import Any,Mapping
SAFE_STUDENT_MODES=frozenset({"q_excluded_total__q_token_dropped","fixed_reference__q_token_dropped"})

def _sha(v:object,n:str)->str:
    if not isinstance(v,str) or len(v)!=64 or v!=v.lower(): raise ValueError(f"{n} must be lowercase SHA-256")
    try:int(v,16)
    except ValueError as e: raise ValueError(f"{n} must be lowercase SHA-256") from e
    return v

def _id(v:object,n:str)->str:
    if not isinstance(v,str) or not v.strip():raise ValueError(f"{n} must be nonempty")
    return v.strip()

def _digest(p:Mapping[str,Any])->str:return hashlib.sha256(json.dumps(p,sort_keys=True,separators=(",",":"),ensure_ascii=True,allow_nan=False).encode()).hexdigest()

@dataclass(frozen=True)
class QSafetyAuthorityV1:
    authority_id:str
    target_construction_authority_sha256:str
    preprocessing_implementation_sha256:str
    q_intervention_execution_sha256:str
    student_preprocessing_mode:str
    teacher_target_mode:str
    q_token_dropped:bool
    passed:bool=True
    training_authorized:bool=False
    def _payload(self)->dict[str,Any]:
        mode=_id(self.student_preprocessing_mode,"student_preprocessing_mode")
        if mode not in SAFE_STUDENT_MODES: raise ValueError("student preprocessing mode is not q-safe")
        if self.q_token_dropped is not True: raise ValueError("q token must be dropped")
        if _id(self.teacher_target_mode,"teacher_target_mode")!="Q_BLIND": raise ValueError("teacher target must be Q_BLIND")
        if self.passed is not True: raise ValueError("q intervention execution must pass")
        if self.training_authorized is not False: raise ValueError("q-safety authority cannot authorize training")
        return {"schema":"V5_Q_SAFETY_AUTHORITY_V1","authority_id":_id(self.authority_id,"authority_id"),
            "target_construction_authority_sha256":_sha(self.target_construction_authority_sha256,"target_construction_authority_sha256"),
            "preprocessing_implementation_sha256":_sha(self.preprocessing_implementation_sha256,"preprocessing_implementation_sha256"),
            "q_intervention_execution_sha256":_sha(self.q_intervention_execution_sha256,"q_intervention_execution_sha256"),
            "student_preprocessing_mode":mode,"teacher_target_mode":"Q_BLIND","q_token_dropped":True,"passed":True,"training_authorized":False}
    def validate(self)->None:self._payload()
    def canonical_digest(self)->str:return _digest(self._payload())
