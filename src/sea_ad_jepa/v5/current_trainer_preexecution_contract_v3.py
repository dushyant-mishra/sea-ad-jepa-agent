"""Current V5 preexecution contract V3 bound to V3 roots/closure."""
from __future__ import annotations
from dataclasses import dataclass
import hashlib,json
from typing import Any,Mapping
from .current_authority_roots_v3 import CURRENT_V5_UPSTREAM_AUTHORITY_ROOTS_V3

def _sha(v:object,n:str)->str:
    if not isinstance(v,str) or len(v)!=64 or v!=v.lower():raise ValueError(f"{n} must be lowercase SHA-256")
    try:int(v,16)
    except ValueError as e:raise ValueError(f"{n} must be lowercase SHA-256") from e
    return v
def _digest(p:Mapping[str,Any])->str:return hashlib.sha256(json.dumps(p,sort_keys=True,separators=(",",":"),ensure_ascii=True,allow_nan=False).encode()).hexdigest()
def _closure(c:Mapping[str,Any])->str:
    if not isinstance(c,Mapping) or c.get("schema")!="V5_CURRENT_AUTHORITY_CLOSURE_V3" or c.get("training_authorized") is not False:raise ValueError("closure_v3 schema/state mismatch")
    r=c.get("authority_roots")
    if not isinstance(r,Mapping) or tuple(r)!=CURRENT_V5_UPSTREAM_AUTHORITY_ROOTS_V3:raise ValueError("closure_v3 roots mismatch")
    nr={k:_sha(r[k],k) for k in CURRENT_V5_UPSTREAM_AUTHORITY_ROOTS_V3}
    core={"schema":"V5_CURRENT_AUTHORITY_CLOSURE_V3","predecessor_closure_v2_sha256":_sha(c.get("predecessor_closure_v2_sha256"),"predecessor_closure_v2_sha256"),"authority_roots":nr,"training_authorized":False}
    observed=_sha(c.get("closure_digest"),"closure_digest")
    if observed!=_digest(core):raise ValueError("closure_v3 digest mismatch")
    return observed
@dataclass(frozen=True)
class CurrentTrainerPreexecutionAuthorityV3:
    authority_roots:Mapping[str,str]; closure_v3_sha256:str; protected_registry_authority_sha256:str; critical_test_v2_authority_sha256:str; relational_training_active:bool; optimizer_started:bool; training_authorized:bool=False
    def normalized_roots(self):
        if not isinstance(self.authority_roots,Mapping) or tuple(self.authority_roots)!=CURRENT_V5_UPSTREAM_AUTHORITY_ROOTS_V3:raise ValueError("authority_roots must exactly match V3")
        return {k:_sha(self.authority_roots[k],k) for k in CURRENT_V5_UPSTREAM_AUTHORITY_ROOTS_V3}
    def validate(self):
        r=self.normalized_roots()
        if _sha(self.protected_registry_authority_sha256,"protected_registry")!=r["protected_registry_authority_sha256"]:raise ValueError("protected registry mismatch")
        if _sha(self.critical_test_v2_authority_sha256,"critical_test_v2")!=r["critical_test_v2_authority_sha256"]:raise ValueError("critical test V2 mismatch")
        _sha(self.closure_v3_sha256,"closure_v3_sha256")
        if self.relational_training_active is not False or self.optimizer_started is not False or self.training_authorized is not False:raise ValueError("preexecution state must remain inactive")
    def bind_closure_v3(self,c):
        self.validate(); d=_closure(c)
        if d!=self.closure_v3_sha256 or dict(c["authority_roots"])!=self.normalized_roots():raise ValueError("closure_v3 binding mismatch")
        return d
    def canonical_digest(self):
        self.validate();return _digest({"schema":"V5_CURRENT_TRAINER_PREEXECUTION_AUTHORITY_V3","authority_roots":self.normalized_roots(),"closure_v3_sha256":self.closure_v3_sha256,"protected_registry_authority_sha256":self.protected_registry_authority_sha256,"critical_test_v2_authority_sha256":self.critical_test_v2_authority_sha256,"relational_training_active":False,"optimizer_started":False,"training_authorized":False})
