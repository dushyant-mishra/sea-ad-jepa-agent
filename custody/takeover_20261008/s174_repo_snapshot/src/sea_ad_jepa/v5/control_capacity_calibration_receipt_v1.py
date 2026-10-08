"""Capacity-calibration receipt for planted-vs-shuffled control separation.

The receipt binds the calibration-only substrate that generated the evidence.
That substrate is explicitly forbidden as terminal FULL104 masking input.
"""
from __future__ import annotations
from dataclasses import asdict,dataclass
import hashlib,json,math
from typing import Mapping

from .full104_control_calibration_cache_v1 import CACHE_ROLE_ID

APPROVED_SCOPE_IDS=(
    "TARGET_PANEL_SIZE_CAPACITY_CALIBRATION_V1",
    "NONLINEAR_CAP_CAPACITY_CALIBRATION_V1",
)

def _sha(v,n):
    if not isinstance(v,str) or len(v)!=64 or v!=v.lower(): raise ValueError(f"{n} must be a lowercase SHA-256 digest")
    try:int(v,16)
    except ValueError as e: raise ValueError(f"{n} must be a lowercase SHA-256 digest") from e
    return v

def _digest(p:Mapping)->str:
    return hashlib.sha256(json.dumps(p,sort_keys=True,separators=(",",":"),ensure_ascii=True,allow_nan=False).encode()).hexdigest()

@dataclass(frozen=True)
class ControlCapacityCalibrationReceiptV1:
    scope_id:str
    candidate_value:int
    calibration_cache_manifest_sha256:str
    calibration_cache_role_id:str
    raw_planted_evidence_sha256:str
    raw_shuffled_evidence_sha256:str
    precision_root_sha256:str
    planted_minus_shuffled_mean:float
    planted_minus_shuffled_lower_one_sided:float
    donor_count:int
    target_count:int
    bootstrap_replicates:int
    confidence_level_numerator:int
    confidence_level_denominator:int
    replay_exact:bool
    real_masking_policy_outcomes_inspected:bool=False
    training_authorized:bool=False

    def validate(self):
        if self.scope_id not in APPROVED_SCOPE_IDS: raise ValueError("scope_id mismatch")
        if isinstance(self.candidate_value,bool) or not isinstance(self.candidate_value,int) or self.candidate_value<1: raise ValueError("candidate_value must be positive")
        if self.calibration_cache_role_id != CACHE_ROLE_ID:
            raise ValueError("capacity receipt requires the current calibration-only cache role")
        roots=(
            _sha(self.calibration_cache_manifest_sha256,"calibration_cache_manifest_sha256"),
            _sha(self.raw_planted_evidence_sha256,"raw_planted_evidence_sha256"),
            _sha(self.raw_shuffled_evidence_sha256,"raw_shuffled_evidence_sha256"),
            _sha(self.precision_root_sha256,"precision_root_sha256"),
        )
        if len(set(roots))!=4: raise ValueError("capacity-calibration evidence roots must be role-distinct")
        if not math.isfinite(float(self.planted_minus_shuffled_mean)) or not math.isfinite(float(self.planted_minus_shuffled_lower_one_sided)):
            raise ValueError("capacity-calibration statistics must be finite")
        if self.donor_count!=104: raise ValueError("donor_count must equal current FULL104 value 104")
        if self.target_count<1: raise ValueError("target_count must be positive")
        if self.bootstrap_replicates!=4096: raise ValueError("bootstrap_replicates must remain 4096")
        if (self.confidence_level_numerator,self.confidence_level_denominator)!=(95,100): raise ValueError("confidence level must remain 95/100")
        if not isinstance(self.replay_exact,bool): raise ValueError("replay_exact must be boolean")
        if self.real_masking_policy_outcomes_inspected is not False: raise ValueError("capacity calibration cannot inspect real masking-policy outcomes")
        if self.training_authorized is not False: raise ValueError("capacity calibration cannot authorize training")

    @property
    def detects_planted_shortcut(self)->bool:
        self.validate()
        return bool(self.planted_minus_shuffled_lower_one_sided>0.0 and self.replay_exact)

    def canonical_digest(self)->str:
        self.validate()
        return _digest({"schema":"V5_CONTROL_CAPACITY_CALIBRATION_RECEIPT_V1",**asdict(self),"detects_planted_shortcut":self.detects_planted_shortcut})
