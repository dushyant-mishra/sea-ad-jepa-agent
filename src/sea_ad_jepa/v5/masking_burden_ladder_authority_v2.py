"""Outcome-minimizing successor to the FULL104 burden ladder.

The rungs remain the census-derived 5/10/15/20/30/50 percent ladder, but
terminal execution is sequential and stops at the first fully qualifying rung.
Higher burdens must remain unopened once the lowest qualifying burden is known.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from fractions import Fraction
import hashlib
import json
from typing import Mapping, Tuple

from .masking_burden_ladder_authority_v1 import (
    FROZEN_BURDEN_LADDER,
    TERMINAL_UNIVERSE_SIZE,
)

LADDER_ID = "FULL104_CENSUS_BURDEN_LADDER_20260917_V1"
SELECTION_RULE_ID = "LOWEST_QUALIFYING_BURDEN_V1"
ESCALATION_RULE_ID = "ASCENDING_STOP_AT_FIRST_FULLY_QUALIFYING_RUNG_V2"
NO_QUALIFIER_POLICY_ID = "FAIL_CLOSED_NO_MASKING_AUTHORITY_V1"


def _sha(value: object, name: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or value != value.lower():
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{name} must be a lowercase SHA-256 digest") from exc
    return value


def _digest(payload: dict) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


@dataclass(frozen=True)
class MaskingBurdenLadderAuthorityV2:
    authority_id: str
    census_authority_sha256: str
    ladder_id: str = LADDER_ID
    selection_rule_id: str = SELECTION_RULE_ID
    escalation_rule_id: str = ESCALATION_RULE_ID
    no_qualifier_policy_id: str = NO_QUALIFIER_POLICY_ID
    terminal_universe_size: int = TERMINAL_UNIVERSE_SIZE
    rungs: Tuple[Tuple[int, int], ...] = FROZEN_BURDEN_LADDER
    training_authorized: bool = False

    def validate(self) -> None:
        if not isinstance(self.authority_id, str) or not self.authority_id.strip():
            raise ValueError("authority_id must be nonempty")
        _sha(self.census_authority_sha256, "census_authority_sha256")
        if self.ladder_id != LADDER_ID:
            raise ValueError("ladder_id mismatch")
        if self.selection_rule_id != SELECTION_RULE_ID:
            raise ValueError("selection_rule_id mismatch")
        if self.escalation_rule_id != ESCALATION_RULE_ID:
            raise ValueError("escalation_rule_id mismatch")
        if self.no_qualifier_policy_id != NO_QUALIFIER_POLICY_ID:
            raise ValueError("no_qualifier_policy_id mismatch")
        if self.terminal_universe_size != TERMINAL_UNIVERSE_SIZE:
            raise ValueError("terminal universe must remain the strict 17,186-address core")
        if tuple(tuple(x) for x in self.rungs) != FROZEN_BURDEN_LADDER:
            raise ValueError("burden ladder rungs are frozen and cannot be reordered or extended")
        if self.training_authorized is not False:
            raise ValueError("burden ladder cannot authorize training")

    def ordered_rungs(self) -> tuple[Fraction, ...]:
        self.validate()
        return tuple(Fraction(n, d) for n, d in self.rungs)

    def _validated_prefix(self, verdicts: Mapping[Fraction, bool]) -> tuple[Fraction, ...]:
        self.validate()
        rungs = self.ordered_rungs()
        keys = tuple(verdicts.keys())
        expected = rungs[: len(keys)]
        if keys != expected:
            raise ValueError(
                "evaluated burden verdicts must be an exact contiguous prefix of the "
                "frozen ascending ladder; outcomes may not be skipped or reordered"
            )
        first_true = next((i for i, rung in enumerate(keys) if verdicts[rung] is True), None)
        if first_true is not None and first_true != len(keys) - 1:
            raise ValueError(
                "terminal outcomes were opened after a lower burden had already fully "
                "qualified; higher burdens must remain unopened"
            )
        for rung in keys:
            if verdicts[rung] not in (True, False):
                raise ValueError("each evaluated rung needs an explicit boolean verdict")
        return keys

    def next_rung(self, verdicts: Mapping[Fraction, bool]) -> Fraction | None:
        """Return the only lawful next rung; None means stop after a qualification."""

        keys = self._validated_prefix(verdicts)
        rungs = self.ordered_rungs()
        if keys and verdicts[keys[-1]] is True:
            return None
        if len(keys) == len(rungs):
            raise ValueError(
                "FAIL_CLOSED_NO_MASKING_AUTHORITY: every frozen burden rung failed"
            )
        return rungs[len(keys)]

    def selected_rung(self, verdicts: Mapping[Fraction, bool]) -> Fraction:
        keys = self._validated_prefix(verdicts)
        if not keys or verdicts[keys[-1]] is not True:
            raise ValueError("no fully qualifying burden has been reached")
        return keys[-1]

    def canonical_digest(self) -> str:
        self.validate()
        payload = dict(asdict(self))
        payload["rungs"] = [list(x) for x in self.rungs]
        return _digest({"schema": "V5_MASKING_BURDEN_LADDER_AUTHORITY_V2", **payload})
