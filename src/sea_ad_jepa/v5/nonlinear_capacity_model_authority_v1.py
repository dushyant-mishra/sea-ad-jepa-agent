"""Reauthorized nonlinear model capacity for FULL104 control calibration.

Only the model family/capacity is inherited from discovery as a confirmation
hypothesis. Dataset, target list, universe, burden, folds, sampling cap and seed
are explicitly outside this authority.
"""
from __future__ import annotations
from dataclasses import asdict,dataclass
import hashlib,json
from typing import Any,Mapping

MODEL_FAMILY_ID="HIST_GRADIENT_BOOSTING_REGRESSOR_EXPLICIT_V1"
CAPACITY_SCOPE_ID="DISCOVERY_MODEL_CAPACITY_ONLY__FULL104_DATA_AND_ROW_CAP_EXCLUDED_V1"
RETUNING_POLICY_ID="NONLINEAR_REPORTED_WITHOUT_POLICY_RETUNING_V1"
FEATURE_COUNT=32
LEARNING_RATE_NUMERATOR=1
LEARNING_RATE_DENOMINATOR=10
MAX_ITER=50
MAX_LEAF_NODES=15
MIN_SAMPLES_LEAF=20
L2_NUMERATOR=1
L2_DENOMINATOR=1
MAX_BINS=255


def _sha(v,n):
    if not isinstance(v,str) or len(v)!=64 or v!=v.lower():
        raise ValueError(f"{n} must be a lowercase SHA-256 digest")
    try:int(v,16)
    except ValueError as e: raise ValueError(f"{n} must be a lowercase SHA-256 digest") from e
    return v

def _canonical(p:Mapping)->bytes:
    return json.dumps(p,sort_keys=True,separators=(",",":"),ensure_ascii=True,allow_nan=False).encode("utf-8")

def _digest(p:Mapping)->str:
    return hashlib.sha256(_canonical(p)).hexdigest()

@dataclass(frozen=True)
class NonlinearCapacityModelAuthorityV1:
    authority_id:str
    primary_parameters_authority_sha256:str
    historical_nonlinear_script_sha256:str
    historical_nonlinear_summary_sha256:str
    model_family_id:str=MODEL_FAMILY_ID
    capacity_scope_id:str=CAPACITY_SCOPE_ID
    retuning_policy_id:str=RETUNING_POLICY_ID
    feature_count:int=FEATURE_COUNT
    learning_rate_numerator:int=LEARNING_RATE_NUMERATOR
    learning_rate_denominator:int=LEARNING_RATE_DENOMINATOR
    max_iter:int=MAX_ITER
    max_leaf_nodes:int=MAX_LEAF_NODES
    min_samples_leaf:int=MIN_SAMPLES_LEAF
    l2_regularization_numerator:int=L2_NUMERATOR
    l2_regularization_denominator:int=L2_DENOMINATOR
    max_bins:int=MAX_BINS
    early_stopping:bool=False
    discovery_dataset_authorized_for_full104:bool=False
    discovery_target_list_authorized_for_full104:bool=False
    discovery_burden_authorized_for_full104:bool=False
    discovery_seed_authorized_for_full104:bool=False
    discovery_fold_assignment_authorized_for_full104:bool=False
    row_cap_frozen_here:bool=False
    terminal_masking_outcomes_inspected_before_freeze:bool=False
    training_authorized:bool=False

    @property
    def learning_rate(self)->float:
        self.validate(); return self.learning_rate_numerator/self.learning_rate_denominator

    @property
    def l2_regularization(self)->float:
        self.validate(); return self.l2_regularization_numerator/self.l2_regularization_denominator

    def validate(self)->None:
        if not isinstance(self.authority_id,str) or not self.authority_id.strip():
            raise ValueError("authority_id must be nonempty")
        roots=(
            _sha(self.primary_parameters_authority_sha256,"primary_parameters_authority_sha256"),
            _sha(self.historical_nonlinear_script_sha256,"historical_nonlinear_script_sha256"),
            _sha(self.historical_nonlinear_summary_sha256,"historical_nonlinear_summary_sha256"),
        )
        if len(set(roots))!=3:
            raise ValueError("nonlinear capacity provenance roots must be role-distinct")
        if self.model_family_id!=MODEL_FAMILY_ID:
            raise ValueError("model_family_id mismatch")
        if self.capacity_scope_id!=CAPACITY_SCOPE_ID:
            raise ValueError("capacity_scope_id mismatch")
        if self.retuning_policy_id!=RETUNING_POLICY_ID:
            raise ValueError("retuning_policy_id mismatch")
        observed=(
            self.feature_count,self.learning_rate_numerator,self.learning_rate_denominator,
            self.max_iter,self.max_leaf_nodes,self.min_samples_leaf,
            self.l2_regularization_numerator,self.l2_regularization_denominator,self.max_bins,
        )
        expected=(32,1,10,50,15,20,1,1,255)
        if observed!=expected:
            raise ValueError("nonlinear model-capacity tuple drifted")
        if self.early_stopping is not False:
            raise ValueError("early_stopping must remain False")
        for name in (
            "discovery_dataset_authorized_for_full104",
            "discovery_target_list_authorized_for_full104",
            "discovery_burden_authorized_for_full104",
            "discovery_seed_authorized_for_full104",
            "discovery_fold_assignment_authorized_for_full104",
            "row_cap_frozen_here",
            "terminal_masking_outcomes_inspected_before_freeze",
            "training_authorized",
        ):
            if getattr(self,name) is not False:
                raise ValueError(f"{name} must remain False")

    def bind_primary_parameters(self,parameters:Any)->None:
        self.validate(); parameters.validate()
        if parameters.canonical_digest()!=self.primary_parameters_authority_sha256:
            raise ValueError("primary parameter authority root mismatch")
        if int(parameters.ridge_score_feature_count)!=self.feature_count:
            raise ValueError("nonlinear feature count must equal current 32-feature attacker capacity")

    def canonical_digest(self)->str:
        self.validate()
        return _digest({"schema":"V5_NONLINEAR_CAPACITY_MODEL_AUTHORITY_V1",**asdict(self)})
