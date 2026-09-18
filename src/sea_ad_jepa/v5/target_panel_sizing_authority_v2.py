"""Control-calibrated successor for FULL104 target-panel sizing.

The panel-count ladder is frozen before terminal masking outcomes.  Selection is
allowed to inspect only the required planted-positive and within-donor-shuffled
negative controls plus deterministic replay/coverage diagnostics.  The real
masking-policy outcomes must remain unopened while panel size is chosen.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Mapping, Tuple

PANEL_COUNT_LADDER: Tuple[int, ...] = (128, 256, 512, 1024)
LADDER_ID = "FULL104_TARGET_PANEL_CONTROL_CALIBRATION_LADDER_V2"
SELECTION_RULE_ID = "LOWEST_CONTROL_QUALIFYING_TARGET_PANEL_V2"
OUTCOME_FIREWALL_ID = "REAL_MASKING_POLICY_OUTCOMES_FORBIDDEN_DURING_PANEL_SIZING_V1"


def _sha(value: object, name: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or value != value.lower():
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{name} must be a lowercase SHA-256 digest") from exc
    return value


def _digest(payload) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    ).hexdigest()


@dataclass(frozen=True)
class TargetPanelControlVerdictV2:
    target_count: int
    planted_detected: bool
    planted_suppressed: bool
    negative_contains_zero: bool
    replay_exact: bool
    donor_coverage_complete: bool
    bootstrap_finite: bool

    @property
    def qualified(self) -> bool:
        return all(
            (
                self.planted_detected,
                self.planted_suppressed,
                self.negative_contains_zero,
                self.replay_exact,
                self.donor_coverage_complete,
                self.bootstrap_finite,
            )
        )


@dataclass(frozen=True)
class TargetPanelSizingPlanAuthorityV2:
    authority_id: str
    census_authority_sha256: str
    target_eligibility_receipt_sha256: str
    independent_donor_count: int
    eligible_target_count: int
    ladder_id: str = LADDER_ID
    selection_rule_id: str = SELECTION_RULE_ID
    outcome_firewall_policy_id: str = OUTCOME_FIREWALL_ID
    panel_count_ladder: Tuple[int, ...] = PANEL_COUNT_LADDER
    terminal_outcomes_inspected_before_freeze: bool = False
    training_authorized: bool = False

    def validate(self) -> None:
        if not isinstance(self.authority_id, str) or not self.authority_id.strip():
            raise ValueError("authority_id must be nonempty")
        roots = (
            _sha(self.census_authority_sha256, "census_authority_sha256"),
            _sha(self.target_eligibility_receipt_sha256, "target_eligibility_receipt_sha256"),
        )
        if roots[0] == roots[1]:
            raise ValueError("target-panel sizing roots must be role-distinct")
        if self.independent_donor_count != 104:
            raise ValueError("independent_donor_count must equal current FULL104 value 104")
        if self.eligible_target_count != 17053:
            raise ValueError("eligible_target_count must equal current FULL104 value 17053")
        if self.ladder_id != LADDER_ID:
            raise ValueError("ladder_id mismatch")
        if self.selection_rule_id != SELECTION_RULE_ID:
            raise ValueError("selection_rule_id mismatch")
        if self.outcome_firewall_policy_id != OUTCOME_FIREWALL_ID:
            raise ValueError("outcome_firewall_policy_id mismatch")
        if tuple(self.panel_count_ladder) != PANEL_COUNT_LADDER:
            raise ValueError("panel-count ladder is frozen and cannot be reordered or extended")
        if self.panel_count_ladder[0] < self.independent_donor_count:
            raise ValueError("first target-panel rung must not be smaller than donor count")
        if self.panel_count_ladder[-1] > self.eligible_target_count:
            raise ValueError("panel-count ladder exceeds eligible target universe")
        if self.terminal_outcomes_inspected_before_freeze is not False:
            raise ValueError("target-panel sizing plan must freeze before terminal outcomes")
        if self.training_authorized is not False:
            raise ValueError("target-panel sizing cannot authorize training")

    def select(self, verdicts: Mapping[int, TargetPanelControlVerdictV2]) -> int | None:
        self.validate()
        keys = tuple(verdicts.keys())
        expected = self.panel_count_ladder[: len(keys)]
        if keys != expected:
            raise ValueError("target-panel control verdicts must form an exact ladder prefix")
        first_pass = None
        for i, count in enumerate(keys):
            verdict = verdicts[count]
            if verdict.target_count != count:
                raise ValueError("control verdict target_count mismatch")
            if verdict.qualified:
                first_pass = i
                break
        if first_pass is not None:
            if first_pass != len(keys) - 1:
                raise ValueError("higher panel-count controls were opened after a lower panel already qualified")
            return keys[first_pass]
        if len(keys) == len(self.panel_count_ladder):
            raise ValueError("FAIL_CLOSED_NO_CONTROL_QUALIFYING_TARGET_PANEL")
        return None

    def next_target_count(self, verdicts: Mapping[int, TargetPanelControlVerdictV2]) -> int:
        selected = self.select(verdicts)
        if selected is not None:
            raise ValueError("target-panel sizing already qualified; do not open a higher rung")
        return self.panel_count_ladder[len(verdicts)]

    def canonical_digest(self) -> str:
        self.validate()
        payload = dict(asdict(self))
        payload["panel_count_ladder"] = list(self.panel_count_ladder)
        return _digest({"schema":"V5_TARGET_PANEL_SIZING_PLAN_AUTHORITY_V2", **payload})


@dataclass(frozen=True)
class TargetPanelSizingReceiptV2:
    plan_authority_sha256: str
    selected_target_count: int
    evaluated_counts: Tuple[int, ...]
    verdict_digest_by_count: Mapping[int, str]
    real_masking_policy_outcomes_inspected: bool = False
    training_authorized: bool = False

    def validate(self) -> None:
        _sha(self.plan_authority_sha256, "plan_authority_sha256")
        if self.selected_target_count not in PANEL_COUNT_LADDER:
            raise ValueError("selected_target_count is not a frozen ladder rung")
        if tuple(self.evaluated_counts) != PANEL_COUNT_LADDER[: len(self.evaluated_counts)]:
            raise ValueError("evaluated_counts must be an exact ladder prefix")
        if not self.evaluated_counts or self.evaluated_counts[-1] != self.selected_target_count:
            raise ValueError("selected target count must be the final evaluated rung")
        if set(self.verdict_digest_by_count) != set(self.evaluated_counts):
            raise ValueError("receipt must bind one verdict digest for every evaluated rung")
        for count,digest in self.verdict_digest_by_count.items():
            if count not in PANEL_COUNT_LADDER:
                raise ValueError("receipt binds an unapproved target-count rung")
            _sha(digest, f"verdict_digest_by_count[{count}]")
        if self.real_masking_policy_outcomes_inspected is not False:
            raise ValueError("target-panel sizing cannot use real masking-policy outcomes")
        if self.training_authorized is not False:
            raise ValueError("target-panel sizing receipt cannot authorize training")

    def canonical_digest(self) -> str:
        self.validate()
        payload=dict(asdict(self))
        payload["evaluated_counts"]=list(self.evaluated_counts)
        payload["verdict_digest_by_count"]={str(k):v for k,v in sorted(self.verdict_digest_by_count.items())}
        return _digest({"schema":"V5_TARGET_PANEL_SIZING_RECEIPT_V2", **payload})
