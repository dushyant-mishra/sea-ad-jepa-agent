"""Final current-V5 training authority V2 bound to the V4 root graph.

Historical CurrentTrainingAuthorityV1 remains provenance only and is not accepted by
the V4 optimizer guard.
"""
from __future__ import annotations
from dataclasses import dataclass
import hashlib, json
from typing import Any, Mapping
from .current_authority_roots_v4 import CURRENT_V5_RECEIPT_AUTHORITY_ROOTS_V4
from .current_authority_closure_v4 import CurrentAuthorityClosureV4
from .current_trainer_preexecution_contract_v4 import CurrentTrainerPreexecutionAuthorityV4
from .current_teacher_target_receipt_v4 import validate_current_teacher_target_receipt_v4

ISSUANCE_POLICY_ID="CURRENT_V5_V4_ALL_SCIENTIFIC_AND_EXECUTION_GATES_PASS_BEFORE_TRAINING_V1"

def _sha(v: object,name:str)->str:
    if not isinstance(v,str) or len(v)!=64 or v!=v.lower():
        raise ValueError(f"{name} must be lowercase SHA-256")
    int(v,16); return v

def _digest(p):
    return hashlib.sha256(json.dumps(p,sort_keys=True,separators=(",",":"),
                                     ensure_ascii=True,allow_nan=False).encode()).hexdigest()

def _live_digest(obj:Any,name:str)->str:
    if getattr(obj,"training_authorized",False) is not False:
        raise ValueError(f"{name} unexpectedly authorizes training")
    obj.validate()
    return _sha(obj.canonical_digest(),f"{name} digest")

@dataclass(frozen=True)
class CurrentTrainingAuthorityV2:
    authority_id:str
    closure_v4_sha256:str
    preexecution_authority_sha256:str
    receipt_v4_sha256:str
    target_package_root:str
    biological_specificity_authority_sha256:str
    q_safety_authority_sha256:str
    validated_e2_authority_sha256:str
    rna_e2_target_integration_authority_sha256:str
    critical_test_execution_authority_sha256:str
    runtime_source_authority_sha256:str
    issuance_policy_id:str
    issuance_proof_sha256:str
    training_authorized:bool=True

    def _core(self)->dict:
        return {
            "schema":"V5_CURRENT_TRAINING_AUTHORITY_V2",
            "authority_id":self.authority_id,
            "closure_v4_sha256":_sha(self.closure_v4_sha256,"closure_v4_sha256"),
            "preexecution_authority_sha256":_sha(self.preexecution_authority_sha256,"preexecution_authority_sha256"),
            "receipt_v4_sha256":_sha(self.receipt_v4_sha256,"receipt_v4_sha256"),
            "target_package_root":_sha(self.target_package_root,"target_package_root"),
            "biological_specificity_authority_sha256":_sha(self.biological_specificity_authority_sha256,"biological_specificity_authority_sha256"),
            "q_safety_authority_sha256":_sha(self.q_safety_authority_sha256,"q_safety_authority_sha256"),
            "validated_e2_authority_sha256":_sha(self.validated_e2_authority_sha256,"validated_e2_authority_sha256"),
            "rna_e2_target_integration_authority_sha256":_sha(self.rna_e2_target_integration_authority_sha256,"rna_e2_target_integration_authority_sha256"),
            "critical_test_execution_authority_sha256":_sha(self.critical_test_execution_authority_sha256,"critical_test_execution_authority_sha256"),
            "runtime_source_authority_sha256":_sha(self.runtime_source_authority_sha256,"runtime_source_authority_sha256"),
            "issuance_policy_id":self.issuance_policy_id,
            "training_authorized":True,
        }

    def validate(self)->None:
        if self.issuance_policy_id!=ISSUANCE_POLICY_ID:
            raise ValueError("issuance policy mismatch")
        if self.training_authorized is not True:
            raise ValueError("final authority must explicitly authorize training")
        if _sha(self.issuance_proof_sha256,"issuance_proof_sha256")!=_digest(self._core()):
            raise ValueError("issuance proof mismatch")

    def canonical_digest(self)->str:
        self.validate()
        return _digest({**self._core(),"issuance_proof_sha256":self.issuance_proof_sha256})

def issue_training_authority_v2(*, closure_v4:CurrentAuthorityClosureV4,
                                 preexecution:CurrentTrainerPreexecutionAuthorityV4,
                                 receipt_v4:Mapping[str,Any],
                                 expected_target_package_root:str,
                                 biological_specificity:Any,q_safety:Any,
                                 validated_e2:Any,rna_e2_target_integration:Any,
                                 critical_test_execution:Any,runtime_source:Any)->CurrentTrainingAuthorityV2:
    closure_v4.validate(); roots=closure_v4.normalized_roots()
    preexecution.bind_closure_v4(closure_v4)
    pre_digest=preexecution.canonical_digest()
    receipt_roots=dict(roots); receipt_roots["preexecution_authority_sha256"]=pre_digest
    if tuple(receipt_roots)!=CURRENT_V5_RECEIPT_AUTHORITY_ROOTS_V4:
        raise RuntimeError("internal V4 receipt-root order mismatch")
    verified=validate_current_teacher_target_receipt_v4(
        receipt_v4,expected_target_package_root=expected_target_package_root,
        expected_authority_roots=receipt_roots,
        expected_closure_v4_sha256=closure_v4.canonical_digest())
    live={
        "biological_specificity_authority_sha256":_live_digest(biological_specificity,"biological specificity"),
        "q_safety_authority_sha256":_live_digest(q_safety,"q safety"),
        "validated_e2_authority_sha256":_live_digest(validated_e2,"validated E2"),
        "rna_e2_target_integration_authority_sha256":_live_digest(rna_e2_target_integration,"RNA+E2 integration"),
        "critical_test_execution_authority_sha256":_live_digest(critical_test_execution,"critical test execution"),
        "runtime_source_authority_sha256":_live_digest(runtime_source,"runtime source"),
    }
    for k,v in live.items():
        if roots[k]!=v: raise ValueError(f"{k} live-root mismatch")
    core={
        "schema":"V5_CURRENT_TRAINING_AUTHORITY_V2",
        "authority_id":"V5_CURRENT_TRAINING_AUTHORITY_V2",
        "closure_v4_sha256":closure_v4.canonical_digest(),
        "preexecution_authority_sha256":pre_digest,
        "receipt_v4_sha256":verified["receipt_digest"],
        "target_package_root":verified["target_package_root"],
        **live,
        "issuance_policy_id":ISSUANCE_POLICY_ID,
        "training_authorized":True,
    }
    a=CurrentTrainingAuthorityV2(
        authority_id=core["authority_id"],closure_v4_sha256=core["closure_v4_sha256"],
        preexecution_authority_sha256=pre_digest,receipt_v4_sha256=core["receipt_v4_sha256"],
        target_package_root=core["target_package_root"],
        biological_specificity_authority_sha256=live["biological_specificity_authority_sha256"],
        q_safety_authority_sha256=live["q_safety_authority_sha256"],
        validated_e2_authority_sha256=live["validated_e2_authority_sha256"],
        rna_e2_target_integration_authority_sha256=live["rna_e2_target_integration_authority_sha256"],
        critical_test_execution_authority_sha256=live["critical_test_execution_authority_sha256"],
        runtime_source_authority_sha256=live["runtime_source_authority_sha256"],
        issuance_policy_id=ISSUANCE_POLICY_ID,issuance_proof_sha256=_digest(core),
        training_authorized=True)
    a.validate(); return a
