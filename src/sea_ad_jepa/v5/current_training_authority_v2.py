"""Final current-V5 training authority V2 consuming the V3 root graph."""
from __future__ import annotations
from dataclasses import dataclass
import hashlib,json
from typing import Any,Mapping
from .current_authority_roots_v3 import CURRENT_V5_RECEIPT_AUTHORITY_ROOTS_V3,CURRENT_V5_UPSTREAM_AUTHORITY_ROOTS_V3
from .current_teacher_target_receipt_v3 import validate_current_teacher_target_receipt_v3
from .current_trainer_preexecution_contract_v3 import CurrentTrainerPreexecutionAuthorityV3
ISSUANCE_POLICY_ID="CURRENT_V5_V3_ROOTS_SPECIFICITY_QSAFE_PROVIDER_EXECUTION_REQUIRED_V2"
def _sha(v:object,n:str)->str:
    if not isinstance(v,str) or len(v)!=64 or v!=v.lower():raise ValueError(f"{n} must be lowercase SHA-256")
    try:int(v,16)
    except ValueError as e:raise ValueError(f"{n} must be lowercase SHA-256") from e
    return v
def _digest(p:Mapping[str,Any])->str:return hashlib.sha256(json.dumps(p,sort_keys=True,separators=(",",":"),ensure_ascii=True,allow_nan=False).encode()).hexdigest()
def _live(obj:Any,n:str)->str:
    if getattr(obj,"training_authorized",False) is not False:raise ValueError(f"{n} unexpectedly authorizes training")
    obj.validate();return _sha(obj.canonical_digest(),f"{n} canonical digest")
@dataclass(frozen=True)
class CurrentTrainingAuthorityV2:
    authority_id:str; closure_v3_sha256:str; preexecution_authority_sha256:str; receipt_v3_sha256:str; target_package_root:str
    biological_specificity_authority_sha256:str; q_safety_authority_sha256:str; critical_test_v2_authority_sha256:str; runtime_source_authority_sha256:str
    issuance_policy_id:str; issuance_proof_sha256:str; training_authorized:bool=True
    def _payload(self)->dict[str,Any]:
        if not isinstance(self.authority_id,str) or not self.authority_id.strip():raise ValueError("authority_id must be nonempty")
        if self.issuance_policy_id!=ISSUANCE_POLICY_ID:raise ValueError("issuance_policy_id mismatch")
        if self.training_authorized is not True:raise ValueError("final training authority must authorize training")
        return {"schema":"V5_CURRENT_TRAINING_AUTHORITY_V2","authority_id":self.authority_id,"closure_v3_sha256":_sha(self.closure_v3_sha256,"closure_v3_sha256"),"preexecution_authority_sha256":_sha(self.preexecution_authority_sha256,"preexecution_authority_sha256"),"receipt_v3_sha256":_sha(self.receipt_v3_sha256,"receipt_v3_sha256"),"target_package_root":_sha(self.target_package_root,"target_package_root"),"biological_specificity_authority_sha256":_sha(self.biological_specificity_authority_sha256,"biological_specificity_authority_sha256"),"q_safety_authority_sha256":_sha(self.q_safety_authority_sha256,"q_safety_authority_sha256"),"critical_test_v2_authority_sha256":_sha(self.critical_test_v2_authority_sha256,"critical_test_v2_authority_sha256"),"runtime_source_authority_sha256":_sha(self.runtime_source_authority_sha256,"runtime_source_authority_sha256"),"issuance_policy_id":self.issuance_policy_id,"training_authorized":True}
    def validate(self)->None:
        if _sha(self.issuance_proof_sha256,"issuance_proof_sha256")!=_digest(self._payload()):raise ValueError("issuance proof mismatch")
    def canonical_digest(self)->str:self.validate();return _digest({**self._payload(),"issuance_proof_sha256":self.issuance_proof_sha256})
def issue_training_authority_v2(*,closure_v3:Mapping[str,Any],preexecution:CurrentTrainerPreexecutionAuthorityV3,receipt_v3:Mapping[str,Any],expected_target_package_root:str,runtime_source:Any)->CurrentTrainingAuthorityV2:
    if not isinstance(closure_v3,Mapping) or closure_v3.get("schema")!="V5_CURRENT_AUTHORITY_CLOSURE_V3" or closure_v3.get("training_authorized") is not False:raise ValueError("closure_v3 schema/state mismatch")
    roots=closure_v3.get("authority_roots")
    if not isinstance(roots,Mapping) or tuple(roots)!=CURRENT_V5_UPSTREAM_AUTHORITY_ROOTS_V3:raise ValueError("closure_v3 roots mismatch")
    closure_digest=_sha(closure_v3.get("closure_digest"),"closure_digest")
    if not isinstance(preexecution,CurrentTrainerPreexecutionAuthorityV3):raise ValueError("preexecution must use V3 schema")
    preexecution.bind_closure_v3(closure_v3);pre_digest=preexecution.canonical_digest()
    receipt_roots=dict(roots);receipt_roots["preexecution_authority_sha256"]=pre_digest
    if tuple(receipt_roots)!=CURRENT_V5_RECEIPT_AUTHORITY_ROOTS_V3:raise RuntimeError("internal V3 receipt root order mismatch")
    verified=validate_current_teacher_target_receipt_v3(receipt_v3,expected_target_package_root=expected_target_package_root,expected_authority_roots=receipt_roots,expected_closure_v3_sha256=closure_digest)
    runtime=_live(runtime_source,"runtime source")
    if runtime!=roots["runtime_source_authority_sha256"]:raise ValueError("runtime-source authority root mismatch")
    core={"schema":"V5_CURRENT_TRAINING_AUTHORITY_V2","authority_id":"V5_CURRENT_TRAINING_AUTHORITY_V2","closure_v3_sha256":closure_digest,"preexecution_authority_sha256":pre_digest,"receipt_v3_sha256":verified["receipt_digest"],"target_package_root":verified["target_package_root"],"biological_specificity_authority_sha256":roots["biological_specificity_authority_sha256"],"q_safety_authority_sha256":roots["q_safety_authority_sha256"],"critical_test_v2_authority_sha256":roots["critical_test_v2_authority_sha256"],"runtime_source_authority_sha256":runtime,"issuance_policy_id":ISSUANCE_POLICY_ID,"training_authorized":True}
    out=CurrentTrainingAuthorityV2(authority_id=core["authority_id"],closure_v3_sha256=closure_digest,preexecution_authority_sha256=pre_digest,receipt_v3_sha256=verified["receipt_digest"],target_package_root=verified["target_package_root"],biological_specificity_authority_sha256=core["biological_specificity_authority_sha256"],q_safety_authority_sha256=core["q_safety_authority_sha256"],critical_test_v2_authority_sha256=core["critical_test_v2_authority_sha256"],runtime_source_authority_sha256=runtime,issuance_policy_id=ISSUANCE_POLICY_ID,issuance_proof_sha256=_digest(core),training_authorized=True)
    out.validate();return out
