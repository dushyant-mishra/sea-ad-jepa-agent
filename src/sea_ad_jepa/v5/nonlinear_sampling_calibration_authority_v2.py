"""FULL104 nonlinear row-cap calibration successor V2."""
from __future__ import annotations
from dataclasses import asdict,dataclass
import hashlib,json
from typing import Mapping,Tuple,Any

from .nonlinear_sampling_calibration_authority_v1 import NonlinearCapControlVerdictV1

CAP_LADDER:Tuple[int,...]=(64,128,256,512,1024)
LADDER_ID="FULL104_NONLINEAR_DONOR_CAP_CAPACITY_LADDER_V2"
SELECTION_RULE_ID="LOWEST_PLANTED_VS_SHUFFLED_QUALIFYING_NONLINEAR_CAP_V2"
OUTCOME_FIREWALL_ID="REAL_MASKING_POLICY_OUTCOMES_FORBIDDEN_DURING_NONLINEAR_CAP_CALIBRATION_V1"


def _sha(v,n):
    if not isinstance(v,str) or len(v)!=64 or v!=v.lower():
        raise ValueError(f"{n} must be a lowercase SHA-256 digest")
    try:int(v,16)
    except ValueError as e: raise ValueError(f"{n} must be a lowercase SHA-256 digest") from e
    return v

def _digest(p:Mapping)->str:
    return hashlib.sha256(json.dumps(p,sort_keys=True,separators=(",",":"),ensure_ascii=True,allow_nan=False).encode()).hexdigest()

@dataclass(frozen=True)
class NonlinearSamplingCalibrationPlanV2:
    authority_id:str
    target_panel_authority_sha256:str
    precision_authority_sha256:str
    outer_split_authority_sha256:str
    primary_parameters_authority_sha256:str
    model_capacity_authority_sha256:str
    calibration_cache_manifest_sha256:str
    ladder_id:str=LADDER_ID
    selection_rule_id:str=SELECTION_RULE_ID
    outcome_firewall_policy_id:str=OUTCOME_FIREWALL_ID
    cap_ladder:Tuple[int,...]=CAP_LADDER
    terminal_outcomes_inspected_before_freeze:bool=False
    training_authorized:bool=False

    def validate(self)->None:
        roots=tuple(_sha(getattr(self,name),name) for name in (
            "target_panel_authority_sha256","precision_authority_sha256",
            "outer_split_authority_sha256","primary_parameters_authority_sha256",
            "model_capacity_authority_sha256","calibration_cache_manifest_sha256",
        ))
        if len(set(roots))!=6:
            raise ValueError("nonlinear calibration V2 roots must be role-distinct")
        if self.ladder_id!=LADDER_ID:
            raise ValueError("ladder_id mismatch")
        if self.selection_rule_id!=SELECTION_RULE_ID:
            raise ValueError("selection_rule_id mismatch")
        if self.outcome_firewall_policy_id!=OUTCOME_FIREWALL_ID:
            raise ValueError("outcome_firewall_policy_id mismatch")
        if tuple(self.cap_ladder)!=CAP_LADDER:
            raise ValueError("nonlinear cap ladder is frozen and cannot be reordered or extended")
        if self.terminal_outcomes_inspected_before_freeze is not False:
            raise ValueError("nonlinear cap calibration plan must freeze before terminal outcomes")
        if self.training_authorized is not False:
            raise ValueError("nonlinear cap calibration plan cannot authorize training")

    def select(self,verdicts:Mapping[int,NonlinearCapControlVerdictV1])->int|None:
        self.validate()
        keys=tuple(verdicts.keys())
        if keys!=self.cap_ladder[:len(keys)]:
            raise ValueError("nonlinear cap verdicts must form an exact ladder prefix")
        first=None
        for i,cap in enumerate(keys):
            verdict=verdicts[cap]; verdict.validate()
            if verdict.max_cells_per_donor!=cap:
                raise ValueError("nonlinear cap verdict mismatch")
            if verdict.qualified:
                first=i; break
        if first is not None:
            if first!=len(keys)-1:
                raise ValueError("higher nonlinear cap opened after lower cap already qualified")
            return keys[first]
        if len(keys)==len(self.cap_ladder):
            raise ValueError("FAIL_CLOSED_NO_CAPACITY_QUALIFYING_NONLINEAR_CAP")
        return None

    def next_cap(self,verdicts:Mapping[int,NonlinearCapControlVerdictV1])->int:
        selected=self.select(verdicts)
        if selected is not None:
            raise ValueError("nonlinear cap already qualified; do not open a higher rung")
        return self.cap_ladder[len(verdicts)]

    def bind_current_roots(self,*,panel:Any,precision:Any,outer_split:Any,parameters:Any,model:Any,cache_manifest:Any)->None:
        self.validate()
        for obj,name,expected in (
            (panel,"target panel",self.target_panel_authority_sha256),
            (precision,"precision",self.precision_authority_sha256),
            (outer_split,"outer split",self.outer_split_authority_sha256),
            (parameters,"parameters",self.primary_parameters_authority_sha256),
            (model,"nonlinear capacity model",self.model_capacity_authority_sha256),
            (cache_manifest,"calibration cache",self.calibration_cache_manifest_sha256),
        ):
            obj.validate()
            if obj.canonical_digest()!=expected:
                raise ValueError(f"{name} root mismatch")
        if getattr(cache_manifest,"terminal_masking_qualification_authorized",None) is not False:
            raise ValueError("nonlinear cap calibration cache cannot authorize terminal masking")
        if getattr(panel,"target_count",None)!=getattr(precision,"required_target_count",None):
            raise ValueError("target panel and precision target counts disagree")
        model.bind_primary_parameters(parameters)

    def canonical_digest(self)->str:
        self.validate()
        payload=dict(asdict(self)); payload["cap_ladder"]=list(self.cap_ladder)
        return _digest({"schema":"V5_NONLINEAR_SAMPLING_CALIBRATION_PLAN_V2",**payload})

@dataclass(frozen=True)
class NonlinearSamplingCalibrationReceiptV2:
    plan_authority_sha256:str
    calibration_cache_manifest_sha256:str
    precision_authority_sha256:str
    model_capacity_authority_sha256:str
    selected_max_cells_per_donor:int
    evaluated_caps:Tuple[int,...]
    verdict_digest_by_cap:Mapping[int,str]
    real_masking_policy_outcomes_inspected:bool=False
    training_authorized:bool=False

    def validate(self)->None:
        roots=(
            _sha(self.plan_authority_sha256,"plan_authority_sha256"),
            _sha(self.calibration_cache_manifest_sha256,"calibration_cache_manifest_sha256"),
            _sha(self.precision_authority_sha256,"precision_authority_sha256"),
            _sha(self.model_capacity_authority_sha256,"model_capacity_authority_sha256"),
        )
        if len(set(roots))!=4:
            raise ValueError("nonlinear calibration receipt roots must be role-distinct")
        if self.selected_max_cells_per_donor not in CAP_LADDER:
            raise ValueError("selected nonlinear cap is not approved")
        if tuple(self.evaluated_caps)!=CAP_LADDER[:len(self.evaluated_caps)]:
            raise ValueError("evaluated nonlinear caps must form an exact ladder prefix")
        if not self.evaluated_caps or self.evaluated_caps[-1]!=self.selected_max_cells_per_donor:
            raise ValueError("selected nonlinear cap must be final evaluated rung")
        if set(self.verdict_digest_by_cap)!=set(self.evaluated_caps):
            raise ValueError("receipt must bind every evaluated nonlinear cap")
        for cap,digest in self.verdict_digest_by_cap.items():
            if cap not in CAP_LADDER:
                raise ValueError("receipt binds unapproved nonlinear cap")
            _sha(digest,f"verdict_digest_by_cap[{cap}]")
        if self.real_masking_policy_outcomes_inspected is not False:
            raise ValueError("nonlinear cap calibration receipt cannot use real policy outcomes")
        if self.training_authorized is not False:
            raise ValueError("nonlinear calibration receipt cannot authorize training")

    def bind_verdicts(self,plan:NonlinearSamplingCalibrationPlanV2,verdicts:Mapping[int,NonlinearCapControlVerdictV1])->None:
        self.validate(); plan.validate()
        if plan.canonical_digest()!=self.plan_authority_sha256:
            raise ValueError("nonlinear calibration plan root mismatch")
        if plan.calibration_cache_manifest_sha256!=self.calibration_cache_manifest_sha256:
            raise ValueError("nonlinear calibration receipt cache root mismatch")
        if plan.precision_authority_sha256!=self.precision_authority_sha256:
            raise ValueError("nonlinear calibration receipt precision root mismatch")
        if plan.model_capacity_authority_sha256!=self.model_capacity_authority_sha256:
            raise ValueError("nonlinear calibration receipt model-capacity root mismatch")
        selected=plan.select(verdicts)
        if selected!=self.selected_max_cells_per_donor:
            raise ValueError("receipt cap disagrees with mechanical capacity calibration")
        observed={cap:verdict.canonical_digest() for cap,verdict in verdicts.items()}
        if dict(observed)!=dict(self.verdict_digest_by_cap):
            raise ValueError("nonlinear calibration verdict digests mismatch")

    def canonical_digest(self)->str:
        self.validate()
        payload=dict(asdict(self))
        payload["evaluated_caps"]=list(self.evaluated_caps)
        payload["verdict_digest_by_cap"]={str(k):v for k,v in sorted(self.verdict_digest_by_cap.items())}
        return _digest({"schema":"V5_NONLINEAR_SAMPLING_CALIBRATION_RECEIPT_V2",**payload})
