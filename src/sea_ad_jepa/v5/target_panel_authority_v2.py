"""FULL104 target-panel authority V2 bound to sizing and selection receipts."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any, Mapping

STRICT_SUPPORT_ID = "STRICT_MEASURED_SCALAR_ONLY__COLLISION_UNRESOLVED_EXCLUDED_V1"
SELECTION_POLICY_ID = "DETERMINISTIC_HASH_RANKED_ELIGIBLE_TARGET_PANEL_V2"
OUTCOME_FIREWALL_ID = "MASKING_QUALIFICATION_OUTCOME_NOT_USED_FOR_SELECTION_V1"
TARGET_COUNT = 128


def _sha(value: object, name: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or value != value.lower():
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{name} must be a lowercase SHA-256 digest") from exc
    return value


def _digest(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    ).hexdigest()


@dataclass(frozen=True)
class TargetPanelAuthorityV2:
    authority_id: str
    full104_substrate_sha256: str
    canonical_registry_authority_sha256: str
    support_estimability_authority_sha256: str
    target_eligibility_receipt_sha256: str
    target_panel_sizing_authority_sha256: str
    target_selection_receipt_sha256: str
    selector_source_sha256: str
    support_state_policy_id: str
    selection_policy_id: str
    outcome_firewall_policy_id: str
    target_count: int
    terminal_outcomes_inspected_before_freeze: bool = False
    training_authorized: bool = False

    def validate(self) -> None:
        if not isinstance(self.authority_id, str) or not self.authority_id.strip():
            raise ValueError("authority_id must be nonempty")
        roots = (
            _sha(self.full104_substrate_sha256, "full104_substrate_sha256"),
            _sha(self.canonical_registry_authority_sha256, "canonical_registry_authority_sha256"),
            _sha(self.support_estimability_authority_sha256, "support_estimability_authority_sha256"),
            _sha(self.target_eligibility_receipt_sha256, "target_eligibility_receipt_sha256"),
            _sha(self.target_panel_sizing_authority_sha256, "target_panel_sizing_authority_sha256"),
            _sha(self.target_selection_receipt_sha256, "target_selection_receipt_sha256"),
            _sha(self.selector_source_sha256, "selector_source_sha256"),
        )
        if len(set(roots)) != len(roots):
            raise ValueError("target-panel V2 roots must be role-distinct")
        if self.support_state_policy_id != STRICT_SUPPORT_ID:
            raise ValueError("support_state_policy_id mismatch")
        if self.selection_policy_id != SELECTION_POLICY_ID:
            raise ValueError("selection_policy_id mismatch")
        if self.outcome_firewall_policy_id != OUTCOME_FIREWALL_ID:
            raise ValueError("outcome_firewall_policy_id mismatch")
        if self.target_count != TARGET_COUNT:
            raise ValueError("target_count must equal the frozen 128-target FULL104 panel")
        if self.terminal_outcomes_inspected_before_freeze is not False:
            raise ValueError("target panel must freeze before terminal outcomes")
        if self.training_authorized is not False:
            raise ValueError("target panel cannot authorize training")

    def bind_sizing_and_selection(self, sizing: Any, selection: Any) -> None:
        self.validate()
        sizing.validate()
        selection.validate()
        if sizing.canonical_digest() != self.target_panel_sizing_authority_sha256:
            raise ValueError("target-panel sizing authority root mismatch")
        if selection.canonical_digest() != self.target_selection_receipt_sha256:
            raise ValueError("target selection receipt root mismatch")
        if sizing.target_count != self.target_count or selection.target_count != self.target_count:
            raise ValueError("target counts disagree across sizing, selection and panel authority")
        if sizing.target_eligibility_receipt_sha256 != self.target_eligibility_receipt_sha256:
            raise ValueError("sizing authority is bound to a different eligibility receipt")
        if selection.eligibility_receipt_sha256 != self.target_eligibility_receipt_sha256:
            raise ValueError("selection receipt is bound to a different eligibility receipt")

    def canonical_digest(self) -> str:
        self.validate()
        return _digest({"schema": "V5_TARGET_PANEL_AUTHORITY_V2", **asdict(self)})
