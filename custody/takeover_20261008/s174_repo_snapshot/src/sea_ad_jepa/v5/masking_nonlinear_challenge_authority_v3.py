"""FULL104 nonlinear challenge V3 with control-calibrated donor sampling cap."""
from __future__ import annotations
from dataclasses import asdict, dataclass
import hashlib,json
from typing import Any,Mapping

CHALLENGE_ID="NONLINEAR_TREE_ENSEMBLE_EXPRESSION_PROXY_CHALLENGE_V1"
MODEL_FAMILY_ID="HIST_GRADIENT_BOOSTING_REGRESSOR_EXPLICIT_V1"
SAMPLING_POLICY_ID="DETERMINISTIC_HASH_BOTTOM_K_PER_DONOR_V1"
DONOR_WEIGHTING_POLICY_ID="EQUAL_TOTAL_WEIGHT_PER_DONOR_V1"
RETUNING_POLICY_ID="NONLINEAR_REPORTED_WITHOUT_POLICY_RETUNING_V1"
ORIGIN_POLICY_ID="DISCOVERY_NONLINEAR_CAPACITY_REAUTHORIZED_FOR_FULL104_CONFIRMATION_V1"
SEED_NAMESPACE="V5_FULL104_NONLINEAR_ROOT_DERIVED_V3"

def _sha(v,n):
    if not isinstance(v,str) or len(v)!=64 or v!=v.lower(): raise ValueError(f"{n} must be a lowercase SHA-256 digest")
    try:int(v,16)
    except ValueError as e: raise ValueError(f"{n} must be a lowercase SHA-256 digest") from e
    return v
def _canonical(p): return json.dumps(p,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode()
def _digest(p): return hashlib.sha256(_canonical(p)).hexdigest()

@dataclass(frozen=True)
class NonlinearMaskingChallengeAuthorityV3:
    authority_id:str
    primary_parameters_authority_sha256:str
    outer_split_authority_sha256:str
    target_panel_authority_sha256:str
    historical_nonlinear_script_sha256:str
    historical_nonlinear_summary_sha256:str
    sampling_calibration_plan_sha256:str
    sampling_calibration_receipt_sha256:str
    max_cells_per_donor:int
    challenge_id:str=CHALLENGE_ID
    model_family_id:str=MODEL_FAMILY_ID
    sampling_policy_id:str=SAMPLING_POLICY_ID
    donor_weighting_policy_id:str=DONOR_WEIGHTING_POLICY_ID
    retuning_policy_id:str=RETUNING_POLICY_ID
    parameter_origin_policy_id:str=ORIGIN_POLICY_ID
    feature_count:int=32
    learning_rate_numerator:int=1
    learning_rate_denominator:int=10
    max_iter:int=50
    max_leaf_nodes:int=15
    min_samples_leaf:int=20
    l2_regularization_numerator:int=1
    l2_regularization_denominator:int=1
    max_bins:int=255
    early_stopping:bool=False
    terminal_outcomes_inspected_before_freeze:bool=False
    training_authorized:bool=False

    @property
    def learning_rate(self): self.validate(); return self.learning_rate_numerator/self.learning_rate_denominator
    @property
    def l2_regularization(self): self.validate(); return self.l2_regularization_numerator/self.l2_regularization_denominator
    @property
    def random_seed(self):
        self.validate()
        return int.from_bytes(hashlib.sha256(_canonical({
            "schema":"V5_FULL104_NONLINEAR_ROOT_DERIVED_SEED_V3","namespace":SEED_NAMESPACE,
            "parameters":self.primary_parameters_authority_sha256,"split":self.outer_split_authority_sha256,
            "panel":self.target_panel_authority_sha256,"sampling":self.sampling_calibration_receipt_sha256
        })).digest()[:8],"big")

    def validate(self):
        roots=tuple(_sha(getattr(self,n),n) for n in (
            "primary_parameters_authority_sha256","outer_split_authority_sha256","target_panel_authority_sha256",
            "historical_nonlinear_script_sha256","historical_nonlinear_summary_sha256",
            "sampling_calibration_plan_sha256","sampling_calibration_receipt_sha256"))
        if len(set(roots))!=len(roots): raise ValueError("nonlinear V3 roots must be role-distinct")
        if self.max_cells_per_donor not in (64,128,256,512,1024): raise ValueError("max_cells_per_donor must come from control-calibrated ladder")
        if self.challenge_id!=CHALLENGE_ID or self.model_family_id!=MODEL_FAMILY_ID: raise ValueError("nonlinear challenge/model family mismatch")
        if self.sampling_policy_id!=SAMPLING_POLICY_ID or self.donor_weighting_policy_id!=DONOR_WEIGHTING_POLICY_ID: raise ValueError("nonlinear sampling policy mismatch")
        if self.retuning_policy_id!=RETUNING_POLICY_ID or self.parameter_origin_policy_id!=ORIGIN_POLICY_ID: raise ValueError("nonlinear provenance policy mismatch")
        expected=(self.feature_count,self.learning_rate_numerator,self.learning_rate_denominator,self.max_iter,self.max_leaf_nodes,self.min_samples_leaf,self.l2_regularization_numerator,self.l2_regularization_denominator,self.max_bins)
        if expected!=(32,1,10,50,15,20,1,1,255): raise ValueError("historical nonlinear model-capacity tuple drifted")
        if self.early_stopping is not False: raise ValueError("early_stopping must remain False")
        if self.terminal_outcomes_inspected_before_freeze is not False: raise ValueError("nonlinear V3 must freeze before terminal outcomes")
        if self.training_authorized is not False: raise ValueError("nonlinear challenge cannot authorize training")

    def bind_sampling_calibration(self,plan:Any,receipt:Any):
        self.validate(); plan.validate(); receipt.validate()
        if plan.canonical_digest()!=self.sampling_calibration_plan_sha256: raise ValueError("sampling calibration plan root mismatch")
        if receipt.canonical_digest()!=self.sampling_calibration_receipt_sha256: raise ValueError("sampling calibration receipt root mismatch")
        if receipt.plan_authority_sha256!=self.sampling_calibration_plan_sha256: raise ValueError("sampling receipt bound to different plan")
        if receipt.selected_max_cells_per_donor!=self.max_cells_per_donor: raise ValueError("nonlinear cap disagrees with control calibration")

    def canonical_digest(self):
        self.validate()
        return _digest({"schema":"V5_NONLINEAR_MASKING_CHALLENGE_AUTHORITY_V3",**asdict(self),"random_seed":self.random_seed})
