"""Fail-closed biological-specificity authority for current V5 target state."""
from __future__ import annotations
from dataclasses import dataclass
import hashlib, json
from typing import Any, Mapping

def _sha(v:object,n:str)->str:
    if not isinstance(v,str) or len(v)!=64 or v!=v.lower(): raise ValueError(f"{n} must be lowercase SHA-256")
    try:int(v,16)
    except ValueError as e: raise ValueError(f"{n} must be lowercase SHA-256") from e
    return v

def _id(v:object,n:str)->str:
    if not isinstance(v,str) or not v.strip(): raise ValueError(f"{n} must be nonempty")
    return v.strip()

def _digest(p:Mapping[str,Any])->str:
    return hashlib.sha256(json.dumps(p,sort_keys=True,separators=(",",":"),ensure_ascii=True,allow_nan=False).encode()).hexdigest()

@dataclass(frozen=True)
class BiologicalSpecificityAuthorityV1:
    authority_id:str
    target_construction_authority_sha256:str
    external_regulatory_object_authority_sha256:str
    nuisance_class_contract_sha256:str
    synthetic_specificity_execution_sha256:str
    prospective_real_validation_protocol_sha256:str
    biological_validation_execution_sha256:str
    semantic_twin_boundary_id:str
    evidence_class:str="BIOLOGICAL_VALIDATION"
    passed:bool=True
    training_authorized:bool=False
    def _payload(self)->dict[str,Any]:
        if self.evidence_class!="BIOLOGICAL_VALIDATION": raise ValueError("biological specificity requires BIOLOGICAL_VALIDATION evidence class")
        if self.passed is not True: raise ValueError("biological specificity execution must pass")
        if self.training_authorized is not False: raise ValueError("biological specificity authority cannot authorize training")
        return {"schema":"V5_BIOLOGICAL_SPECIFICITY_AUTHORITY_V1","authority_id":_id(self.authority_id,"authority_id"),
            "target_construction_authority_sha256":_sha(self.target_construction_authority_sha256,"target_construction_authority_sha256"),
            "external_regulatory_object_authority_sha256":_sha(self.external_regulatory_object_authority_sha256,"external_regulatory_object_authority_sha256"),
            "nuisance_class_contract_sha256":_sha(self.nuisance_class_contract_sha256,"nuisance_class_contract_sha256"),
            "synthetic_specificity_execution_sha256":_sha(self.synthetic_specificity_execution_sha256,"synthetic_specificity_execution_sha256"),
            "prospective_real_validation_protocol_sha256":_sha(self.prospective_real_validation_protocol_sha256,"prospective_real_validation_protocol_sha256"),
            "biological_validation_execution_sha256":_sha(self.biological_validation_execution_sha256,"biological_validation_execution_sha256"),
            "semantic_twin_boundary_id":_id(self.semantic_twin_boundary_id,"semantic_twin_boundary_id"),"evidence_class":"BIOLOGICAL_VALIDATION","passed":True,"training_authorized":False}
    def validate(self)->None:self._payload()
    def canonical_digest(self)->str:return _digest(self._payload())
