"""Critical-test V2: bind required passes to GitHub Actions evidence receipts.

V1 accepted caller-declared EXECUTED_PASS strings. V2 requires an explicit
GitHub Actions run/job identity, repository, workflow path, head SHA, test-source
SHA and downloaded provider-artifact SHA for every required test.
"""
from __future__ import annotations
from dataclasses import dataclass
import hashlib,json
from typing import Any,Mapping,Sequence
ALLOWED_PROVIDERS=frozenset({"GITHUB_ACTIONS"})
def _sha(v:object,n:str)->str:
    if not isinstance(v,str) or len(v)!=64 or v!=v.lower():raise ValueError(f"{n} must be lowercase SHA-256")
    try:int(v,16)
    except ValueError as e:raise ValueError(f"{n} must be lowercase SHA-256") from e
    return v
def _id(v:object,n:str)->str:
    if not isinstance(v,str) or not v.strip():raise ValueError(f"{n} must be nonempty")
    return v.strip()
def _digest(p:Mapping[str,Any])->str:return hashlib.sha256(json.dumps(p,sort_keys=True,separators=(",",":"),ensure_ascii=True,allow_nan=False).encode()).hexdigest()
@dataclass(frozen=True)
class ProviderTestReceiptV1:
    test_id:str
    provider_id:str
    provider_repository:str
    provider_workflow_path:str
    provider_head_sha256:str
    provider_run_id:str
    provider_job_id:str
    test_source_sha256:str
    provider_artifact_sha256:str
    outcome:str
    def payload(self)->dict[str,str]:
        p=_id(self.provider_id,"provider_id")
        if p not in ALLOWED_PROVIDERS: raise ValueError("provider_id is not approved")
        repo=_id(self.provider_repository,"provider_repository")
        if "/" not in repo or repo.startswith("/") or repo.endswith("/"): raise ValueError("provider_repository must be owner/repo")
        workflow=_id(self.provider_workflow_path,"provider_workflow_path")
        if not workflow.startswith(".github/workflows/"): raise ValueError("provider_workflow_path must name a GitHub Actions workflow")
        if _id(self.outcome,"outcome")!="PASS": raise ValueError("provider receipt outcome must be PASS")
        return {"test_id":_id(self.test_id,"test_id"),"provider_id":p,"provider_repository":repo,"provider_workflow_path":workflow,
                "provider_head_sha256":_sha(self.provider_head_sha256,"provider_head_sha256"),"provider_run_id":_id(self.provider_run_id,"provider_run_id"),
                "provider_job_id":_id(self.provider_job_id,"provider_job_id"),"test_source_sha256":_sha(self.test_source_sha256,"test_source_sha256"),
                "provider_artifact_sha256":_sha(self.provider_artifact_sha256,"provider_artifact_sha256"),"outcome":"PASS"}
    def canonical_digest(self)->str:return _digest({"schema":"V5_PROVIDER_TEST_RECEIPT_V1",**self.payload()})
@dataclass(frozen=True)
class CriticalTestExecutionAuthorityV2:
    authority_id:str
    predecessor_v1_sha256:str
    required_test_ids:Sequence[str]
    receipts:Sequence[ProviderTestReceiptV1]
    training_authorized:bool=False
    def _payload(self)->dict[str,Any]:
        if self.training_authorized is not False: raise ValueError("critical-test authority cannot authorize training")
        req=tuple(sorted(_id(x,"required_test_id") for x in self.required_test_ids))
        if not req or len(set(req))!=len(req): raise ValueError("required_test_ids must be nonempty and unique")
        if not isinstance(self.receipts,Sequence) or isinstance(self.receipts,(str,bytes)):raise ValueError("receipts must be a sequence")
        rows=[r.payload() if isinstance(r,ProviderTestReceiptV1) else (_ for _ in ()).throw(ValueError("receipt must use ProviderTestReceiptV1")) for r in self.receipts]
        by={r["test_id"]:r for r in rows}
        if len(by)!=len(rows) or set(by)!=set(req): raise ValueError("exactly one provider receipt is required per critical test")
        return {"schema":"V5_CRITICAL_TEST_EXECUTION_AUTHORITY_V2","authority_id":_id(self.authority_id,"authority_id"),"predecessor_v1_sha256":_sha(self.predecessor_v1_sha256,"predecessor_v1_sha256"),"required_test_ids":list(req),"provider_receipts":[by[x] for x in req],"training_authorized":False}
    def validate(self)->None:self._payload()
    def canonical_digest(self)->str:return _digest(self._payload())
