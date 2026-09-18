"""Prospective FULL104 target-panel sizing authority.

The current rule is deliberately independent of masking outcomes:
use at least as many target units as independent donor units, then round upward
to the next power of two for deterministic batching.  With 104 FULL104 donors,
that freezes the qualification panel at 128 targets.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any, Mapping

SIZING_RULE_ID = "NEXT_POWER_OF_TWO_AT_LEAST_FULL104_DONOR_COUNT_V1"
FULL104_DONOR_COUNT = 104
FULL104_ELIGIBLE_TARGET_COUNT = 17053
FROZEN_TARGET_COUNT = 128


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


def next_power_of_two_at_least(value: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError("value must be a positive integer")
    return 1 << (value - 1).bit_length()


@dataclass(frozen=True)
class TargetPanelSizingAuthorityV1:
    authority_id: str
    census_authority_sha256: str
    target_eligibility_receipt_sha256: str
    sizing_rule_id: str
    independent_donor_count: int
    eligible_target_count: int
    target_count: int
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
            raise ValueError("sizing authority roots must be role-distinct")
        if self.sizing_rule_id != SIZING_RULE_ID:
            raise ValueError("sizing_rule_id mismatch")
        if self.independent_donor_count != FULL104_DONOR_COUNT:
            raise ValueError("independent_donor_count must equal 104")
        if self.eligible_target_count != FULL104_ELIGIBLE_TARGET_COUNT:
            raise ValueError("eligible_target_count must equal 17053")
        expected = next_power_of_two_at_least(self.independent_donor_count)
        if expected != FROZEN_TARGET_COUNT or self.target_count != expected:
            raise ValueError("target_count must equal prospective FULL104 value 128")
        if self.target_count > self.eligible_target_count:
            raise ValueError("target_count exceeds eligible target count")
        if self.terminal_outcomes_inspected_before_freeze is not False:
            raise ValueError("target-panel sizing must freeze before terminal outcomes")
        if self.training_authorized is not False:
            raise ValueError("target-panel sizing cannot authorize training")

    def canonical_digest(self) -> str:
        self.validate()
        return _digest({"schema": "V5_TARGET_PANEL_SIZING_AUTHORITY_V1", **asdict(self)})
