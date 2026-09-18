"""Control-only calibration of the FULL104 nonlinear donor sampling cap."""
from __future__ import annotations
from dataclasses import asdict,dataclass
import hashlib,json
from typing import Mapping,Tuple

CAP_LADDER:Tuple[int,...]=(64,128,256,512,1024)
LADDER_ID="FULL104_NONLINEAR_DONOR_CAP_CONTROL_LADDER_V1"
SELECTION_RULE_ID="LOWEST_PLANTED_CONTROL_QUALIFYING_NONLINEAR_CAP_V1"
OUTCOME_FIREWALL_ID="REAL_MASKING_POLICY_OUTCOMES_FORBIDDEN_DURING_NONLINEAR_CAP_CALIBRATION_V1"

def _sha(v,n):
    if not isinstance(v,str) or len(v)!=64 or v!=v.lower(): raise ValueError(f"{n} must be a lowercase SHA-256 digest")
    try:int(v,16)
    except ValueError as e: raise ValueError(f"{n} must be a lowercase SHA-256 digest") from e
    return v
def _digest(p): return hashlib.sha256(json.dumps(p,sort_keys=True,separators=(",",":"),ensure_ascii=True,allow_nan=False).encode()).hexdigest()

@dataclass(frozen=True)
class NonlinearCapControlVerdictV1:
    max_cells_per_donor:int
    raw_control_evidence_sha256:str
    negative_lower_two_sided:float
    negative_upper_two_sided:float
    planted_detect_lower_one_sided:float
    planted_after_mask_upper_one_sided:float
    replay_exact:bool
    all_donors_represented:bool
    real_masking_policy_outcomes_inspected:bool=False

    def validate(self):
        _sha(self.raw_control_evidence_sha256,"raw_control_evidence_sha256")
        if self.max_cells_per_donor not in CAP_LADDER: raise ValueError("max_cells_per_donor is not a frozen calibration rung")
        import math
        vals=(self.negative_lower_two_sided,self.negative_upper_two_sided,self.planted_detect_lower_one_sided,self.planted_after_mask_upper_one_sided)
        if not all(math.isfinite(float(x)) for x in vals): raise ValueError("nonlinear control intervals must be finite")
        if self.negative_lower_two_sided>0 or self.negative_upper_two_sided<0: raise ValueError("nonlinear negative-control interval must contain zero")
        if self.real_masking_policy_outcomes_inspected is not False: raise ValueError("nonlinear cap calibration cannot inspect real masking-policy outcomes")
    @property
    def null_noise_tolerance(self)->float:
        self.validate(); return float(max(abs(self.negative_lower_two_sided),abs(self.negative_upper_two_sided)))
    @property
    def qualified(self)->bool:
        self.validate(); tol=self.null_noise_tolerance
        return bool(self.planted_detect_lower_one_sided>tol and self.planted_after_mask_upper_one_sided<=tol and self.replay_exact and self.all_donors_represented)
    def canonical_digest(self)->str:
        self.validate()
        return _digest({"schema":"V5_NONLINEAR_CAP_CONTROL_VERDICT_V1",**asdict(self),"null_noise_tolerance":self.null_noise_tolerance,"qualified":self.qualified})

@dataclass(frozen=True)
class NonlinearSamplingCalibrationPlanV1:
    authority_id:str
    target_panel_authority_sha256:str
    outer_split_authority_sha256:str
    primary_parameters_authority_sha256:str
    ladder_id:str=LADDER_ID
    selection_rule_id:str=SELECTION_RULE_ID
    outcome_firewall_policy_id:str=OUTCOME_FIREWALL_ID
    cap_ladder:Tuple[int,...]=CAP_LADDER
    terminal_outcomes_inspected_before_freeze:bool=False
    training_authorized:bool=False

    def validate(self):
        roots=tuple(_sha(getattr(self,n),n) for n in ("target_panel_authority_sha256","outer_split_authority_sha256","primary_parameters_authority_sha256"))
        if len(set(roots))!=3: raise ValueError("nonlinear calibration roots must be role-distinct")
        if self.ladder_id!=LADDER_ID or self.selection_rule_id!=SELECTION_RULE_ID or self.outcome_firewall_policy_id!=OUTCOME_FIREWALL_ID: raise ValueError("nonlinear calibration policy mismatch")
        if tuple(self.cap_ladder)!=CAP_LADDER: raise ValueError("nonlinear cap ladder is frozen")
        if self.terminal_outcomes_inspected_before_freeze is not False: raise ValueError("nonlinear cap plan must freeze before terminal outcomes")
        if self.training_authorized is not False: raise ValueError("nonlinear cap plan cannot authorize training")

    def select(self,verdicts:Mapping[int,NonlinearCapControlVerdictV1])->int|None:
        self.validate(); keys=tuple(verdicts.keys())
        if keys!=self.cap_ladder[:len(keys)]: raise ValueError("nonlinear cap verdicts must form an exact ladder prefix")
        first=None
        for i,cap in enumerate(keys):
            v=verdicts[cap]; v.validate()
            if v.max_cells_per_donor!=cap: raise ValueError("nonlinear cap verdict mismatch")
            if v.qualified: first=i; break
        if first is not None:
            if first!=len(keys)-1: raise ValueError("higher nonlinear cap opened after lower cap already qualified")
            return keys[first]
        if len(keys)==len(self.cap_ladder): raise ValueError("FAIL_CLOSED_NO_CONTROL_QUALIFYING_NONLINEAR_CAP")
        return None

    def next_cap(self,verdicts:Mapping[int,NonlinearCapControlVerdictV1])->int:
        selected=self.select(verdicts)
        if selected is not None: raise ValueError("nonlinear cap already qualified; do not open higher cap")
        return self.cap_ladder[len(verdicts)]

    def canonical_digest(self)->str:
        self.validate(); p=dict(asdict(self)); p["cap_ladder"]=list(self.cap_ladder)
        return _digest({"schema":"V5_NONLINEAR_SAMPLING_CALIBRATION_PLAN_V1",**p})

@dataclass(frozen=True)
class NonlinearSamplingCalibrationReceiptV1:
    plan_authority_sha256:str
    selected_max_cells_per_donor:int
    evaluated_caps:Tuple[int,...]
    verdict_digest_by_cap:Mapping[int,str]
    real_masking_policy_outcomes_inspected:bool=False
    training_authorized:bool=False

    def validate(self):
        _sha(self.plan_authority_sha256,"plan_authority_sha256")
        if self.selected_max_cells_per_donor not in CAP_LADDER: raise ValueError("selected nonlinear cap is not approved")
        if tuple(self.evaluated_caps)!=CAP_LADDER[:len(self.evaluated_caps)]: raise ValueError("evaluated nonlinear caps must form exact ladder prefix")
        if not self.evaluated_caps or self.evaluated_caps[-1]!=self.selected_max_cells_per_donor: raise ValueError("selected nonlinear cap must be final evaluated rung")
        if set(self.verdict_digest_by_cap)!=set(self.evaluated_caps): raise ValueError("receipt must bind every evaluated nonlinear cap")
        for c,d in self.verdict_digest_by_cap.items(): _sha(d,f"verdict_digest_by_cap[{c}]")
        if self.real_masking_policy_outcomes_inspected is not False: raise ValueError("nonlinear cap calibration cannot use real policy outcomes")
        if self.training_authorized is not False: raise ValueError("nonlinear calibration receipt cannot authorize training")

    def bind_verdicts(self,plan:NonlinearSamplingCalibrationPlanV1,verdicts:Mapping[int,NonlinearCapControlVerdictV1])->None:
        self.validate(); plan.validate()
        if plan.canonical_digest()!=self.plan_authority_sha256: raise ValueError("nonlinear calibration plan root mismatch")
        selected=plan.select(verdicts)
        if selected!=self.selected_max_cells_per_donor: raise ValueError("receipt cap disagrees with mechanical control calibration")
        observed={c:v.canonical_digest() for c,v in verdicts.items()}
        if dict(observed)!=dict(self.verdict_digest_by_cap): raise ValueError("nonlinear calibration verdict digests mismatch")

    def canonical_digest(self)->str:
        self.validate(); p=dict(asdict(self)); p["evaluated_caps"]=list(self.evaluated_caps); p["verdict_digest_by_cap"]={str(k):v for k,v in sorted(self.verdict_digest_by_cap.items())}
        return _digest({"schema":"V5_NONLINEAR_SAMPLING_CALIBRATION_RECEIPT_V1",**p})
