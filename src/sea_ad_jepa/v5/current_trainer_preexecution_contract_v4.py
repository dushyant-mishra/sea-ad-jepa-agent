"""Current-V5 preexecution authority V4 bound to closure V4."""
from __future__ import annotations
from dataclasses import dataclass
import hashlib, json
from typing import Mapping
from .current_authority_roots_v4 import CURRENT_V5_UPSTREAM_AUTHORITY_ROOTS_V4
from .current_authority_closure_v4 import CurrentAuthorityClosureV4

def _sha(v: object,name:str)->str:
    if not isinstance(v,str) or len(v)!=64 or v!=v.lower():
        raise ValueError(f"{name} must be lowercase SHA-256")
    int(v,16); return v

def _digest(p):
    return hashlib.sha256(json.dumps(p,sort_keys=True,separators=(",",":"),
                                     ensure_ascii=True,allow_nan=False).encode()).hexdigest()

@dataclass(frozen=True)
class CurrentTrainerPreexecutionAuthorityV4:
    authority_roots: Mapping[str,str]
    closure_v4_sha256: str
    protected_registry_authority_sha256: str
    critical_test_authority_sha256: str
    critical_test_execution_authority_sha256: str
    relational_training_active: bool
    optimizer_started: bool
    training_authorized: bool=False

    def normalized_roots(self)->dict[str,str]:
        if tuple(self.authority_roots) != CURRENT_V5_UPSTREAM_AUTHORITY_ROOTS_V4:
            raise ValueError("preexecution requires exact V4 root vocabulary")
        return {k:_sha(self.authority_roots[k],k) for k in CURRENT_V5_UPSTREAM_AUTHORITY_ROOTS_V4}

    def validate(self)->None:
        r=self.normalized_roots()
        _sha(self.closure_v4_sha256,"closure_v4_sha256")
        for field,root in (
            ("protected_registry_authority_sha256","protected_registry_authority_sha256"),
            ("critical_test_authority_sha256","critical_test_authority_sha256"),
            ("critical_test_execution_authority_sha256","critical_test_execution_authority_sha256"),
        ):
            if _sha(getattr(self,field),field)!=r[root]:
                raise ValueError(f"{field} root mismatch")
        if self.relational_training_active is not False or self.optimizer_started is not False:
            raise ValueError("training/optimizer must remain inactive at preexecution")
        if self.training_authorized is not False:
            raise ValueError("preexecution cannot authorize training")

    def bind_closure_v4(self, closure: CurrentAuthorityClosureV4)->str:
        self.validate(); closure.validate()
        if closure.normalized_roots()!=self.normalized_roots():
            raise ValueError("closure V4 roots mismatch")
        d=closure.canonical_digest()
        if d!=self.closure_v4_sha256:
            raise ValueError("closure V4 digest mismatch")
        return d

    def canonical_digest(self)->str:
        self.validate()
        return _digest({"schema":"V5_CURRENT_TRAINER_PREEXECUTION_AUTHORITY_V4",
                        "authority_roots":self.normalized_roots(),
                        "closure_v4_sha256":self.closure_v4_sha256,
                        "protected_registry_authority_sha256":self.protected_registry_authority_sha256,
                        "critical_test_authority_sha256":self.critical_test_authority_sha256,
                        "critical_test_execution_authority_sha256":self.critical_test_execution_authority_sha256,
                        "relational_training_active":False,"optimizer_started":False,
                        "training_authorized":False})
