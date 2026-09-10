"""V5 relational shortcut-superiority guard over a frozen shortcut family.

The learned representation must beat the strongest member of the exact shortcut
family in every held-out case by a strictly positive, prospectively frozen
increment. Above-chance performance and comparison to a cherry-picked weak
shortcut are insufficient. This module grants no training authority.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping
import math


def _num(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be explicit numeric")
    out = float(value)
    if not math.isfinite(out):
        raise ValueError(f"{name} must be finite")
    return out


def _id(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be nonempty")
    return value


@dataclass(frozen=True)
class RelationalShortcutSuperiorityAuthorityV2:
    shortcut_family_authority_id: str
    expected_shortcut_ids: tuple[str, ...]
    shortcut_family_frozen_before_checkpoint_outcome: bool
    minimum_absolute_increment: float
    increment_frozen_before_checkpoint_outcome: bool
    heldout_unit_policy_id: str
    multiplicity_policy_id: str
    require_every_case: bool

    def validate(self) -> None:
        _id(self.shortcut_family_authority_id, "shortcut_family_authority_id")
        _id(self.heldout_unit_policy_id, "heldout_unit_policy_id")
        _id(self.multiplicity_policy_id, "multiplicity_policy_id")
        if not isinstance(self.expected_shortcut_ids, tuple) or not self.expected_shortcut_ids:
            raise ValueError("expected_shortcut_ids must be a nonempty tuple")
        ids = tuple(_id(x, "shortcut_id") for x in self.expected_shortcut_ids)
        if len(set(ids)) != len(ids):
            raise ValueError("expected_shortcut_ids must be unique")
        if ids != tuple(sorted(ids)):
            raise ValueError("expected_shortcut_ids must be in canonical sorted order")
        if self.shortcut_family_frozen_before_checkpoint_outcome is not True:
            raise ValueError("shortcut family must be frozen before checkpoint outcome")
        if self.increment_frozen_before_checkpoint_outcome is not True:
            raise ValueError("superiority increment must be frozen before checkpoint outcome")
        if _num(self.minimum_absolute_increment, "minimum_absolute_increment") <= 0:
            raise ValueError("minimum_absolute_increment must be strictly positive")
        if self.require_every_case is not True:
            raise ValueError("production qualification requires every held-out case")


def qualify_relational_superiority(
    *,
    learned_case_metrics: Mapping[str, object],
    shortcut_metrics_by_id: Mapping[str, Mapping[str, object]],
    authority: RelationalShortcutSuperiorityAuthorityV2,
) -> dict[str, object]:
    authority.validate()
    if not isinstance(learned_case_metrics, Mapping) or not learned_case_metrics:
        raise ValueError("learned_case_metrics must be a nonempty mapping")
    if not isinstance(shortcut_metrics_by_id, Mapping):
        raise ValueError("shortcut_metrics_by_id must be a mapping")

    expected_ids = set(authority.expected_shortcut_ids)
    observed_ids = set(shortcut_metrics_by_id)
    if observed_ids != expected_ids:
        missing = sorted(expected_ids - observed_ids)
        extra = sorted(observed_ids - expected_ids)
        raise ValueError(f"shortcut family mismatch: missing={missing}, extra={extra}")

    cases = set(learned_case_metrics)
    for sid in authority.expected_shortcut_ids:
        metrics = shortcut_metrics_by_id[sid]
        if not isinstance(metrics, Mapping) or set(metrics) != cases:
            raise ValueError(f"held-out case set mismatch for shortcut {sid}")

    detail: dict[str, object] = {}
    failed: list[str] = []
    margin = float(authority.minimum_absolute_increment)
    for case in sorted(cases):
        learned = _num(learned_case_metrics[case], f"learned[{case}]")
        by_shortcut = {
            sid: _num(shortcut_metrics_by_id[sid][case], f"shortcut[{sid}][{case}]")
            for sid in authority.expected_shortcut_ids
        }
        strongest = max(by_shortcut.values())
        strongest_ids = tuple(sorted(sid for sid, value in by_shortcut.items() if value == strongest))
        required = strongest + margin
        passed = learned > required
        detail[case] = {
            "learned": learned,
            "strongest_shortcut": strongest,
            "strongest_shortcut_ids": strongest_ids,
            "all_shortcuts": by_shortcut,
            "required_strictly_greater_than": required,
            "pass": passed,
        }
        if not passed:
            failed.append(case)

    if failed:
        raise RuntimeError(f"STOP_RELATIONAL_SHORTCUT_SUPERIORITY_NOT_EARNED: {failed}")
    return {
        "schema": "JEPA_V5_RELATIONAL_SHORTCUT_SUPERIORITY_V2",
        "passed": True,
        "cases": detail,
        "shortcut_family_authority_id": authority.shortcut_family_authority_id,
        "shortcut_ids": authority.expected_shortcut_ids,
        "heldout_unit_policy_id": authority.heldout_unit_policy_id,
        "multiplicity_policy_id": authority.multiplicity_policy_id,
        "minimum_absolute_increment": margin,
        "training_authorized": False,
    }
