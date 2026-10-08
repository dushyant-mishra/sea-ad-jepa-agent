"""Pure current-V5 preexecution authority closure; no duplicated numeric policy."""
from __future__ import annotations
from dataclasses import dataclass
import hashlib, json
from typing import Any, Mapping
from .current_authority_roots_v1 import CURRENT_V5_UPSTREAM_AUTHORITY_ROOTS

def _sha(v:object,name:str)->str:
    if not isinstance(v,str) or len(v)!=64 or v!=v.lower(): raise ValueError(f"{name} must be a lowercase SHA-256 digest")
    try: int(v,16)
    except ValueError as exc: raise ValueError(f"{name} must be a lowercase SHA-256 digest") from exc
    return v
def _digest(p:Mapping[str,Any])->str:
    return hashlib.sha256(json.dumps(p,sort_keys=True,separators=(",",":"),ensure_ascii=True,allow_nan=False).encode()).hexdigest()
@dataclass(frozen=True)
class CurrentTrainerPreexecutionAuthorityV1:
    authority_roots: Mapping[str,str]
    protected_registry_authority_sha256: str
    critical_test_authority_sha256: str
    relational_training_active: bool
    optimizer_started: bool
    training_authorized: bool=False
    def normalized_roots(self)->dict[str,str]:
        if not isinstance(self.authority_roots,Mapping): raise ValueError('authority_roots must be a mapping')
        required=set(CURRENT_V5_UPSTREAM_AUTHORITY_ROOTS)
        if set(self.authority_roots)!=required: raise ValueError('authority_roots must exactly match current V5 upstream roots')
        return {name:_sha(self.authority_roots[name],name) for name in CURRENT_V5_UPSTREAM_AUTHORITY_ROOTS}
    def validate(self)->None:
        self.normalized_roots()
        _sha(self.protected_registry_authority_sha256,'protected_registry_authority_sha256')
        _sha(self.critical_test_authority_sha256,'critical_test_authority_sha256')
        if self.relational_training_active is not False: raise ValueError('relational training must remain inactive')
        if self.optimizer_started is not False: raise ValueError('optimizer must not be started before preexecution closure')
        if self.training_authorized is not False: raise ValueError('preexecution authority cannot authorize training')
    def canonical_digest(self)->str:
        self.validate()
        return _digest({'schema':'V5_CURRENT_TRAINER_PREEXECUTION_AUTHORITY_V1','authority_roots':self.normalized_roots(),'protected_registry_authority_sha256':self.protected_registry_authority_sha256,'critical_test_authority_sha256':self.critical_test_authority_sha256,'relational_training_active':False,'optimizer_started':False,'training_authorized':False})
