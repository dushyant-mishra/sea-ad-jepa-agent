"""Outcome-blind precision plan for control-only target-panel calibration."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib, json
from typing import Any, Mapping

from .precision_authority_v2 import paired_target_donor_bootstrap

METHOD_ID="PAIRED_TARGET_AND_DONOR_WITHIN_SOURCE_BOOTSTRAP_V2"
CONFIDENCE_NUMERATOR=95
CONFIDENCE_DENOMINATOR=100
BOOTSTRAP_REPLICATES=4096
DONOR_COUNT=104
SEED_NAMESPACE="V5_FULL104_CONTROL_CALIBRATION_PRECISION_V1"


def _sha(v,n):
    if not isinstance(v,str) or len(v)!=64 or v!=v.lower():
        raise ValueError(f"{n} must be a lowercase SHA-256 digest")
    try:int(v,16)
    except ValueError as e: raise ValueError(f"{n} must be a lowercase SHA-256 digest") from e
    return v

def _canonical(p:Mapping[str,Any])->bytes:
    return json.dumps(p,sort_keys=True,separators=(",",":"),ensure_ascii=True,allow_nan=False).encode("utf-8")

def _digest(p:Mapping[str,Any])->str:
    return hashlib.sha256(_canonical(p)).hexdigest()

@dataclass(frozen=True)
class ControlCalibrationPrecisionPlanV1:
    authority_id:str
    census_authority_sha256:str
    support_estimability_authority_sha256:str
    target_eligibility_receipt_sha256:str
    outer_split_authority_sha256:str
    uncertainty_method_id:str=METHOD_ID
    confidence_level_numerator:int=CONFIDENCE_NUMERATOR
    confidence_level_denominator:int=CONFIDENCE_DENOMINATOR
    bootstrap_replicates:int=BOOTSTRAP_REPLICATES
    donor_count:int=DONOR_COUNT
    terminal_policy_outcomes_inspected_before_freeze:bool=False
    training_authorized:bool=False

    def validate(self):
        roots=tuple(_sha(getattr(self,n),n) for n in (
            "census_authority_sha256",
            "support_estimability_authority_sha256",
            "target_eligibility_receipt_sha256",
            "outer_split_authority_sha256",
        ))
        if len(set(roots))!=4: raise ValueError("control-calibration precision roots must be role-distinct")
        if self.uncertainty_method_id!=METHOD_ID: raise ValueError("uncertainty_method_id mismatch")
        if (self.confidence_level_numerator,self.confidence_level_denominator)!=(95,100):
            raise ValueError("confidence level must remain 95/100")
        if self.bootstrap_replicates!=4096: raise ValueError("bootstrap_replicates must remain 4096")
        if self.donor_count!=104: raise ValueError("donor_count must remain FULL104 value 104")
        if self.terminal_policy_outcomes_inspected_before_freeze is not False:
            raise ValueError("control-calibration precision must freeze before terminal policy outcomes")
        if self.training_authorized is not False:
            raise ValueError("control-calibration precision cannot authorize training")

    @property
    def confidence_level(self)->float:
        self.validate(); return self.confidence_level_numerator/self.confidence_level_denominator

    def bootstrap_seed(self,target_count:int)->int:
        self.validate()
        if target_count not in (128,256,512,1024):
            raise ValueError("target_count must be a frozen panel-calibration rung")
        payload={
            "schema":"V5_CONTROL_CALIBRATION_BOOTSTRAP_SEED_V1",
            "namespace":SEED_NAMESPACE,
            "authority_sha256":self.canonical_digest(),
            "target_count":target_count,
        }
        return int.from_bytes(hashlib.sha256(_canonical(payload)).digest()[:8],"big")

    def interval(self,matrix,donor_source_code,*,target_count:int):
        self.validate()
        import numpy as np
        arr=np.asarray(matrix)
        if arr.ndim!=2 or arr.shape[0]!=target_count:
            raise ValueError("control-calibration matrix target dimension must equal target_count")
        if arr.shape[1]!=self.donor_count:
            raise ValueError("control-calibration matrix donor dimension must equal 104")
        return paired_target_donor_bootstrap(
            arr,donor_source_code,
            replicates=self.bootstrap_replicates,
            seed=self.bootstrap_seed(target_count),
            confidence_level=self.confidence_level,
        )

    def canonical_digest(self)->str:
        self.validate()
        return _digest({"schema":"V5_CONTROL_CALIBRATION_PRECISION_PLAN_V1",**asdict(self)})
