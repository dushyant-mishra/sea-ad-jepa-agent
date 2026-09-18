"""Control-calibrated successor for FULL104 target-panel sizing."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib, json
from typing import Mapping, Tuple

PANEL_COUNT_LADDER: Tuple[int,...]=(128,256,512,1024)
LADDER_ID="FULL104_TARGET_PANEL_CONTROL_CALIBRATION_LADDER_V2"
SELECTION_RULE_ID="LOWEST_CONTROL_QUALIFYING_TARGET_PANEL_V2"
OUTCOME_FIREWALL_ID="REAL_MASKING_POLICY_OUTCOMES_FORBIDDEN_DURING_PANEL_SIZING_V1"

def _sha(v,n):
    if not isinstance(v,str) or len(v)!=64 or v!=v.lower(): raise ValueError(f"{n} must be a lowercase SHA-256 digest")
    try:int(v,16)
    except ValueError as e: raise ValueError(f"{n} must be a lowercase SHA-256 digest") from e
    return v
def _digest(p): return hashlib.sha256(json.dumps(p,sort_keys=True,separators=(",",":"),ensure_ascii=True,allow_nan=False).encode()).hexdigest()

@dataclass(frozen=True)
class TargetPanelControlVerdictV2:
    target_count:int
    raw_control_evidence_sha256:str
    calibration_precision_plan_sha256:str
    calibration_interval_receipt_sha256:str
    negative_lower_two_sided:float
    negative_upper_two_sided:float
    planted_detect_lower_one_sided:float
    planted_after_mask_upper_one_sided:float
    replay_exact:bool
    donor_coverage_complete:bool
    bootstrap_finite:bool
    real_masking_policy_outcomes_inspected:bool=False

    def validate(self):
        _sha(self.raw_control_evidence_sha256,"raw_control_evidence_sha256")
        _sha(self.calibration_precision_plan_sha256,"calibration_precision_plan_sha256")
        _sha(self.calibration_interval_receipt_sha256,"calibration_interval_receipt_sha256")
        if self.target_count not in PANEL_COUNT_LADDER: raise ValueError("target_count is not a frozen panel rung")
        vals=(self.negative_lower_two_sided,self.negative_upper_two_sided,self.planted_detect_lower_one_sided,self.planted_after_mask_upper_one_sided)
        import math
        if not all(math.isfinite(float(x)) for x in vals): raise ValueError("control intervals must be finite")
        if self.negative_lower_two_sided>0 or self.negative_upper_two_sided<0: raise ValueError("negative control interval must contain zero")
        for name in ("replay_exact","donor_coverage_complete","bootstrap_finite","real_masking_policy_outcomes_inspected"):
            if not isinstance(getattr(self,name),bool): raise ValueError(f"{name} must be boolean")
        if self.real_masking_policy_outcomes_inspected is not False: raise ValueError("target-panel calibration cannot inspect real masking-policy outcomes")

    @property
    def null_noise_tolerance(self)->float:
        self.validate(); return float(max(abs(self.negative_lower_two_sided),abs(self.negative_upper_two_sided)))
    @property
    def qualified(self)->bool:
        self.validate()
        tol=self.null_noise_tolerance
        return bool(
            self.planted_detect_lower_one_sided>tol
            and self.planted_after_mask_upper_one_sided<=tol
            and self.replay_exact and self.donor_coverage_complete and self.bootstrap_finite
        )
    def bind_interval_receipt(self, receipt) -> None:
        self.validate()
        receipt.validate()
        if receipt.scope_id != "TARGET_PANEL_SIZE_CONTROL_CALIBRATION_V1":
            raise ValueError("target-panel verdict requires target-panel interval scope")
        if receipt.candidate_value != self.target_count or receipt.target_count != self.target_count:
            raise ValueError("target-panel interval receipt count mismatch")
        if receipt.raw_control_evidence_sha256 != self.raw_control_evidence_sha256:
            raise ValueError("target-panel raw control evidence root mismatch")
        if receipt.precision_root_sha256 != self.calibration_precision_plan_sha256:
            raise ValueError("target-panel calibration precision root mismatch")
        if receipt.canonical_digest() != self.calibration_interval_receipt_sha256:
            raise ValueError("target-panel calibration interval receipt root mismatch")
        pairs = (
            (receipt.negative_lower_two_sided, self.negative_lower_two_sided),
            (receipt.negative_upper_two_sided, self.negative_upper_two_sided),
            (receipt.planted_detect_lower_one_sided, self.planted_detect_lower_one_sided),
            (receipt.planted_after_mask_upper_one_sided, self.planted_after_mask_upper_one_sided),
        )
        if any(float(a) != float(b) for a,b in pairs):
            raise ValueError("target-panel verdict intervals do not match bound receipt")

    def canonical_digest(self)->str:
        self.validate()
        return _digest({"schema":"V5_TARGET_PANEL_CONTROL_VERDICT_V2",**asdict(self),"null_noise_tolerance":self.null_noise_tolerance,"qualified":self.qualified})

@dataclass(frozen=True)
class TargetPanelSizingPlanAuthorityV2:
    authority_id:str
    census_authority_sha256:str
    target_eligibility_receipt_sha256:str
    independent_donor_count:int
    eligible_target_count:int
    ladder_id:str=LADDER_ID
    selection_rule_id:str=SELECTION_RULE_ID
    outcome_firewall_policy_id:str=OUTCOME_FIREWALL_ID
    panel_count_ladder:Tuple[int,...]=PANEL_COUNT_LADDER
    terminal_outcomes_inspected_before_freeze:bool=False
    training_authorized:bool=False

    def validate(self):
        a=_sha(self.census_authority_sha256,"census_authority_sha256"); b=_sha(self.target_eligibility_receipt_sha256,"target_eligibility_receipt_sha256")
        if a==b: raise ValueError("target-panel sizing roots must be role-distinct")
        if self.independent_donor_count!=104 or self.eligible_target_count!=17053: raise ValueError("FULL104 donor/eligible-target counts mismatch")
        if self.ladder_id!=LADDER_ID or self.selection_rule_id!=SELECTION_RULE_ID or self.outcome_firewall_policy_id!=OUTCOME_FIREWALL_ID: raise ValueError("target-panel sizing policy mismatch")
        if tuple(self.panel_count_ladder)!=PANEL_COUNT_LADDER: raise ValueError("panel-count ladder is frozen")
        if self.panel_count_ladder[0]<self.independent_donor_count: raise ValueError("first panel rung must not be smaller than donor count")
        if self.terminal_outcomes_inspected_before_freeze is not False: raise ValueError("target-panel sizing plan must freeze before terminal outcomes")
        if self.training_authorized is not False: raise ValueError("target-panel sizing cannot authorize training")

    def select(self,verdicts:Mapping[int,TargetPanelControlVerdictV2])->int|None:
        self.validate()
        keys=tuple(verdicts.keys())
        if keys!=self.panel_count_ladder[:len(keys)]: raise ValueError("target-panel control verdicts must form an exact ladder prefix")
        first=None
        for i,count in enumerate(keys):
            v=verdicts[count]; v.validate()
            if v.target_count!=count: raise ValueError("control verdict target_count mismatch")
            if v.qualified: first=i; break
        if first is not None:
            if first!=len(keys)-1: raise ValueError("higher panel-count controls were opened after a lower panel already qualified")
            return keys[first]
        if len(keys)==len(self.panel_count_ladder): raise ValueError("FAIL_CLOSED_NO_CONTROL_QUALIFYING_TARGET_PANEL")
        return None

    def next_target_count(self,verdicts:Mapping[int,TargetPanelControlVerdictV2])->int:
        selected=self.select(verdicts)
        if selected is not None: raise ValueError("target-panel sizing already qualified; do not open a higher rung")
        return self.panel_count_ladder[len(verdicts)]

    def canonical_digest(self)->str:
        self.validate(); p=dict(asdict(self)); p["panel_count_ladder"]=list(self.panel_count_ladder)
        return _digest({"schema":"V5_TARGET_PANEL_SIZING_PLAN_AUTHORITY_V2",**p})

@dataclass(frozen=True)
class TargetPanelSizingReceiptV2:
    plan_authority_sha256:str
    selected_target_count:int
    evaluated_counts:Tuple[int,...]
    verdict_digest_by_count:Mapping[int,str]
    real_masking_policy_outcomes_inspected:bool=False
    training_authorized:bool=False

    def validate(self):
        _sha(self.plan_authority_sha256,"plan_authority_sha256")
        if self.selected_target_count not in PANEL_COUNT_LADDER: raise ValueError("selected_target_count is not a frozen ladder rung")
        if tuple(self.evaluated_counts)!=PANEL_COUNT_LADDER[:len(self.evaluated_counts)]: raise ValueError("evaluated_counts must be an exact ladder prefix")
        if not self.evaluated_counts or self.evaluated_counts[-1]!=self.selected_target_count: raise ValueError("selected target count must be final evaluated rung")
        if set(self.verdict_digest_by_count)!=set(self.evaluated_counts): raise ValueError("receipt must bind every evaluated verdict")
        for c,d in self.verdict_digest_by_count.items(): _sha(d,f"verdict_digest_by_count[{c}]")
        if self.real_masking_policy_outcomes_inspected is not False: raise ValueError("target-panel sizing cannot use real masking-policy outcomes")
        if self.training_authorized is not False: raise ValueError("target-panel sizing receipt cannot authorize training")

    def bind_verdicts(self,plan:TargetPanelSizingPlanAuthorityV2,verdicts:Mapping[int,TargetPanelControlVerdictV2])->None:
        self.validate(); plan.validate()
        if plan.canonical_digest()!=self.plan_authority_sha256: raise ValueError("target-panel sizing plan root mismatch")
        selected=plan.select(verdicts)
        if selected!=self.selected_target_count: raise ValueError("receipt selected_target_count disagrees with mechanical control calibration")
        observed={c:v.canonical_digest() for c,v in verdicts.items()}
        if dict(observed)!=dict(self.verdict_digest_by_count): raise ValueError("receipt verdict digests do not match supplied control evidence")

    def canonical_digest(self)->str:
        self.validate(); p=dict(asdict(self)); p["evaluated_counts"]=list(self.evaluated_counts); p["verdict_digest_by_count"]={str(k):v for k,v in sorted(self.verdict_digest_by_count.items())}
        return _digest({"schema":"V5_TARGET_PANEL_SIZING_RECEIPT_V2",**p})
