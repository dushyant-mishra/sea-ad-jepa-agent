"""FULL104 precision authority V4 bound to control-calibrated target count."""
from __future__ import annotations
from dataclasses import asdict, dataclass
import hashlib,json
from typing import Any,Mapping
from .precision_authority_v2 import paired_target_donor_bootstrap

METHOD_ID="PAIRED_TARGET_AND_DONOR_WITHIN_SOURCE_BOOTSTRAP_V2"
INSUFFICIENT_POLICY_ID="FAIL_CLOSED_IF_BELOW_PRECISION_V2"
CONFIDENCE_NUMERATOR=95
CONFIDENCE_DENOMINATOR=100
BOOTSTRAP_REPLICATES=4096
SEED_NAMESPACE="V5_FULL104_PRECISION_ROOT_DERIVED_V4"

def _sha(v,n):
    if not isinstance(v,str) or len(v)!=64 or v!=v.lower(): raise ValueError(f"{n} must be a lowercase SHA-256 digest")
    try:int(v,16)
    except ValueError as e: raise ValueError(f"{n} must be a lowercase SHA-256 digest") from e
    return v
def _canonical(p): return json.dumps(p,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode()
def _digest(p): return hashlib.sha256(_canonical(p)).hexdigest()

@dataclass(frozen=True)
class QualificationPrecisionAuthorityV4:
    authority_id:str
    support_estimability_authority_sha256:str
    target_panel_authority_sha256:str
    target_panel_sizing_receipt_sha256:str
    outer_split_authority_sha256:str
    required_target_count:int
    uncertainty_method_id:str=METHOD_ID
    confidence_level_numerator:int=CONFIDENCE_NUMERATOR
    confidence_level_denominator:int=CONFIDENCE_DENOMINATOR
    bootstrap_replicates:int=BOOTSTRAP_REPLICATES
    min_donor_count:int=104
    min_outer_fold_count:int=4
    insufficient_support_policy_id:str=INSUFFICIENT_POLICY_ID
    terminal_outcomes_inspected_before_freeze:bool=False
    training_authorized:bool=False

    @property
    def confidence_level(self):
        self.validate(); return self.confidence_level_numerator/self.confidence_level_denominator
    @property
    def bootstrap_seed(self):
        self.validate()
        return int.from_bytes(hashlib.sha256(_canonical({
            "schema":"V5_FULL104_PRECISION_ROOT_DERIVED_SEED_V4","namespace":SEED_NAMESPACE,
            "support":self.support_estimability_authority_sha256,"panel":self.target_panel_authority_sha256,
            "sizing":self.target_panel_sizing_receipt_sha256,"split":self.outer_split_authority_sha256
        })).digest()[:8],"big")

    def validate(self):
        roots=tuple(_sha(getattr(self,n),n) for n in (
            "support_estimability_authority_sha256","target_panel_authority_sha256",
            "target_panel_sizing_receipt_sha256","outer_split_authority_sha256"))
        if len(set(roots))!=len(roots): raise ValueError("precision V4 roots must be role-distinct")
        if self.required_target_count not in (128,256,512,1024): raise ValueError("required_target_count must come from calibrated target-panel ladder")
        if self.uncertainty_method_id!=METHOD_ID: raise ValueError("uncertainty_method_id mismatch")
        if (self.confidence_level_numerator,self.confidence_level_denominator)!=(95,100): raise ValueError("confidence level must remain 95/100")
        if self.bootstrap_replicates!=4096: raise ValueError("bootstrap_replicates must remain 4096")
        if self.min_donor_count!=104 or self.min_outer_fold_count!=4: raise ValueError("donor/fold minima must remain FULL104 values")
        if self.insufficient_support_policy_id!=INSUFFICIENT_POLICY_ID: raise ValueError("insufficient_support_policy_id mismatch")
        if self.terminal_outcomes_inspected_before_freeze is not False: raise ValueError("precision authority must freeze before terminal outcomes")
        if self.training_authorized is not False: raise ValueError("precision authority cannot authorize training")

    def bind_target_panel(self,panel:Any,sizing_receipt:Any):
        self.validate(); panel.validate(); sizing_receipt.validate()
        if panel.canonical_digest()!=self.target_panel_authority_sha256: raise ValueError("target panel root mismatch")
        if sizing_receipt.canonical_digest()!=self.target_panel_sizing_receipt_sha256: raise ValueError("sizing receipt root mismatch")
        if panel.target_count!=self.required_target_count or sizing_receipt.selected_target_count!=self.required_target_count: raise ValueError("precision target count disagrees with calibrated panel")

    def assert_sufficient(self,*,target_count:int,donor_count:int,outer_fold_count:int):
        self.validate()
        if target_count<self.required_target_count: raise ValueError("target_count below calibrated precision requirement")
        if donor_count<104: raise ValueError("donor_count below FULL104 precision requirement")
        if outer_fold_count<4: raise ValueError("outer_fold_count below FULL104 precision requirement")

    def interval(self,matrix,donor_source_code):
        self.validate()
        return paired_target_donor_bootstrap(matrix,donor_source_code,replicates=self.bootstrap_replicates,seed=self.bootstrap_seed,confidence_level=self.confidence_level)

    def canonical_digest(self):
        self.validate()
        return _digest({"schema":"V5_QUALIFICATION_PRECISION_AUTHORITY_V4",**asdict(self),"bootstrap_seed":self.bootstrap_seed})
