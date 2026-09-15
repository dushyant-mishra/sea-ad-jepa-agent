"""Fail-closed execution authority for explicitly required current-V5 tests."""
from __future__ import annotations
from dataclasses import dataclass
import hashlib, json
from typing import Any, Mapping, Sequence

def _id(v:object,name:str)->str:
    if not isinstance(v,str) or not v.strip(): raise ValueError(f"{name} must be nonempty")
    return v.strip()
def _sha(v:object,name:str)->str:
    if not isinstance(v,str) or len(v)!=64 or v!=v.lower(): raise ValueError(f"{name} must be a lowercase SHA-256 digest")
    try: int(v,16)
    except ValueError as exc: raise ValueError(f"{name} must be a lowercase SHA-256 digest") from exc
    return v
def _digest(p:Mapping[str,Any])->str:
    return hashlib.sha256(json.dumps(p,sort_keys=True,separators=(",",":"),ensure_ascii=True,allow_nan=False).encode()).hexdigest()
@dataclass(frozen=True)
class CriticalTestExecutionAuthorityV1:
    authority_id: str
    required_test_ids: Sequence[str]
    test_suite_source_sha256: str
    status_by_test: Mapping[str,str]
    training_authorized: bool=False
    def normalized_required(self)->tuple[str,...]:
        _id(self.authority_id,'authority_id'); _sha(self.test_suite_source_sha256,'test_suite_source_sha256')
        if self.training_authorized is not False: raise ValueError('critical-test authority cannot authorize training')
        if not isinstance(self.required_test_ids,Sequence) or isinstance(self.required_test_ids,(str,bytes)) or not self.required_test_ids: raise ValueError('required_test_ids must be a nonempty sequence')
        required=tuple(_id(x,'required_test_id') for x in self.required_test_ids)
        if len(set(required))!=len(required): raise ValueError('required_test_ids must be unique')
        return tuple(sorted(required))
    def normalized_status(self)->dict[str,str]:
        required=self.normalized_required()
        if not isinstance(self.status_by_test,Mapping): raise ValueError('status_by_test must be a mapping')
        if set(self.status_by_test)!=set(required): raise ValueError('status_by_test must exactly match required_test_ids')
        out={}
        for test_id in required:
            status=_id(self.status_by_test[test_id],f'status for {test_id}')
            if status!='EXECUTED_PASS': raise ValueError(f'{test_id} must be EXECUTED_PASS')
            out[test_id]=status
        return out
    def canonical_digest(self)->str:
        return _digest({'schema':'V5_CRITICAL_TEST_EXECUTION_AUTHORITY_V1','authority_id':_id(self.authority_id,'authority_id'),'required_test_ids':list(self.normalized_required()),'test_suite_source_sha256':_sha(self.test_suite_source_sha256,'test_suite_source_sha256'),'status_by_test':self.normalized_status(),'training_authorized':False})
    def validate(self)->None:
        self.normalized_status(); self.canonical_digest()
