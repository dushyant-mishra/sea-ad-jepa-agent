"""Hash-bound bootstrap interval receipt for control-only calibration."""
from __future__ import annotations
from dataclasses import asdict, dataclass
import hashlib, json, math
from typing import Mapping

APPROVED_SCOPE_IDS=(
    "TARGET_PANEL_SIZE_CONTROL_CALIBRATION_V1",
    "NONLINEAR_CAP_CONTROL_CALIBRATION_V1",
)

def _sha(v,n):
    if not isinstance(v,str) or len(v)!=64 or v!=v.lower():
        raise ValueError(f"{n} must be a lowercase SHA-256 digest")
    try:int(v,16)
    except ValueError as e: raise ValueError(f"{n} must be a lowercase SHA-256 digest") from e
    return v

def _digest(p:Mapping)->str:
    return hashlib.sha256(json.dumps(p,sort_keys=True,separators=(",",":"),ensure_ascii=True,allow_nan=False).encode()).hexdigest()

@dataclass(frozen=True)
class ControlCalibrationIntervalReceiptV1:
    scope_id:str
    candidate_value:int
    raw_control_evidence_sha256:str
    precision_root_sha256:str
    negative_lower_two_sided:float
    negative_upper_two_sided:float
    planted_detect_lower_one_sided:float
    planted_after_mask_upper_one_sided:float
    donor_count:int
    target_count:int
    bootstrap_replicates:int
    confidence_level_numerator:int
    confidence_level_denominator:int
    real_masking_policy_outcomes_inspected:bool=False
    training_authorized:bool=False

    def validate(self):
        if self.scope_id not in APPROVED_SCOPE_IDS: raise ValueError("scope_id mismatch")
        if isinstance(self.candidate_value,bool) or not isinstance(self.candidate_value,int) or self.candidate_value<1:
            raise ValueError("candidate_value must be a positive integer")
        _sha(self.raw_control_evidence_sha256,"raw_control_evidence_sha256")
        _sha(self.precision_root_sha256,"precision_root_sha256")
        vals=(self.negative_lower_two_sided,self.negative_upper_two_sided,self.planted_detect_lower_one_sided,self.planted_after_mask_upper_one_sided)
        if not all(math.isfinite(float(x)) for x in vals): raise ValueError("calibration intervals must be finite")
        if self.negative_lower_two_sided>0 or self.negative_upper_two_sided<0:
            raise ValueError("negative-control interval must contain zero")
        if self.donor_count!=104: raise ValueError("donor_count must equal current FULL104 value 104")
        if self.target_count<1: raise ValueError("target_count must be positive")
        if self.bootstrap_replicates!=4096: raise ValueError("bootstrap_replicates must remain 4096")
        if (self.confidence_level_numerator,self.confidence_level_denominator)!=(95,100):
            raise ValueError("confidence level must remain 95/100")
        if self.real_masking_policy_outcomes_inspected is not False:
            raise ValueError("control calibration interval cannot inspect real masking-policy outcomes")
        if self.training_authorized is not False:
            raise ValueError("control calibration interval cannot authorize training")

    @property
    def null_noise_tolerance(self)->float:
        self.validate()
        return float(max(abs(self.negative_lower_two_sided),abs(self.negative_upper_two_sided)))

    def canonical_digest(self)->str:
        self.validate()
        return _digest({"schema":"V5_CONTROL_CALIBRATION_INTERVAL_RECEIPT_V1",**asdict(self),"null_noise_tolerance":self.null_noise_tolerance})
