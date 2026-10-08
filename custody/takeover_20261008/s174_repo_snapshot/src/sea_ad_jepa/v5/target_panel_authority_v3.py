"""Dynamic FULL104 target-panel authority bound to control-calibrated sizing."""
from __future__ import annotations
from dataclasses import asdict, dataclass
import hashlib, json
from typing import Any, Mapping

STRICT_SUPPORT_ID="STRICT_MEASURED_SCALAR_ONLY__COLLISION_UNRESOLVED_EXCLUDED_V1"
SELECTION_POLICY_ID="DETERMINISTIC_HASH_RANKED_ELIGIBLE_TARGET_PANEL_V2"
OUTCOME_FIREWALL_ID="MASKING_QUALIFICATION_OUTCOME_NOT_USED_FOR_SELECTION_V1"

def _sha(v,n):
    if not isinstance(v,str) or len(v)!=64 or v!=v.lower(): raise ValueError(f"{n} must be a lowercase SHA-256 digest")
    try:int(v,16)
    except ValueError as e: raise ValueError(f"{n} must be a lowercase SHA-256 digest") from e
    return v
def _digest(p): return hashlib.sha256(json.dumps(p,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode()).hexdigest()

@dataclass(frozen=True)
class TargetPanelAuthorityV3:
    authority_id:str
    full104_substrate_sha256:str
    canonical_registry_authority_sha256:str
    support_estimability_authority_sha256:str
    target_eligibility_receipt_sha256:str
    target_panel_sizing_plan_sha256:str
    target_panel_sizing_receipt_sha256:str
    target_selection_receipt_sha256:str
    selector_source_sha256:str
    support_state_policy_id:str
    selection_policy_id:str
    outcome_firewall_policy_id:str
    target_count:int
    terminal_outcomes_inspected_before_freeze:bool=False
    training_authorized:bool=False

    def validate(self):
        roots=tuple(_sha(getattr(self,n),n) for n in (
            "full104_substrate_sha256","canonical_registry_authority_sha256","support_estimability_authority_sha256",
            "target_eligibility_receipt_sha256","target_panel_sizing_plan_sha256","target_panel_sizing_receipt_sha256",
            "target_selection_receipt_sha256","selector_source_sha256"))
        if len(set(roots))!=len(roots): raise ValueError("target-panel V3 roots must be role-distinct")
        if self.support_state_policy_id!=STRICT_SUPPORT_ID: raise ValueError("support_state_policy_id mismatch")
        if self.selection_policy_id!=SELECTION_POLICY_ID: raise ValueError("selection_policy_id mismatch")
        if self.outcome_firewall_policy_id!=OUTCOME_FIREWALL_ID: raise ValueError("outcome_firewall_policy_id mismatch")
        if self.target_count not in (128,256,512,1024): raise ValueError("target_count must come from control-calibrated ladder")
        if self.terminal_outcomes_inspected_before_freeze is not False: raise ValueError("target panel must freeze before terminal outcomes")
        if self.training_authorized is not False: raise ValueError("target panel cannot authorize training")

    def bind(self, plan:Any, sizing_receipt:Any, selection:Any):
        self.validate(); plan.validate(); sizing_receipt.validate(); selection.validate()
        if plan.canonical_digest()!=self.target_panel_sizing_plan_sha256: raise ValueError("target-panel sizing plan root mismatch")
        if sizing_receipt.canonical_digest()!=self.target_panel_sizing_receipt_sha256: raise ValueError("target-panel sizing receipt root mismatch")
        if sizing_receipt.plan_authority_sha256!=self.target_panel_sizing_plan_sha256: raise ValueError("sizing receipt is bound to different plan")
        if sizing_receipt.selected_target_count!=self.target_count: raise ValueError("selected target count mismatch")
        if selection.target_count!=self.target_count: raise ValueError("selection receipt target count mismatch")
        if selection.eligibility_receipt_sha256!=self.target_eligibility_receipt_sha256: raise ValueError("selection uses different eligibility receipt")

    def canonical_digest(self):
        self.validate()
        return _digest({"schema":"V5_TARGET_PANEL_AUTHORITY_V3",**asdict(self)})
