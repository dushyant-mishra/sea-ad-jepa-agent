"""Prospective guard requiring learned relational biology to beat frozen shortcut baselines.

The shortcut baseline and numerical increment must be frozen before the learned
checkpoint outcome is inspected. Above-chance performance alone is insufficient.
This module grants no training authority.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Mapping
import math

def _num(x: object, name: str) -> float:
    if isinstance(x,bool) or not isinstance(x,(int,float)):
        raise ValueError(f"{name} must be explicit numeric")
    y=float(x)
    if not math.isfinite(y): raise ValueError(f"{name} must be finite")
    return y

def _id(x: object, name: str) -> str:
    if not isinstance(x,str) or not x:
        raise ValueError(f"{name} must be nonempty")
    return x

@dataclass(frozen=True)
class RelationalShortcutIncrementAuthorityV1:
    shortcut_baseline_authority_id: str
    baseline_frozen_before_checkpoint_outcome: bool
    minimum_absolute_increment: float
    require_every_case: bool
    heldout_unit_policy_id: str

    def validate(self)->None:
        _id(self.shortcut_baseline_authority_id,"shortcut_baseline_authority_id")
        _id(self.heldout_unit_policy_id,"heldout_unit_policy_id")
        if self.baseline_frozen_before_checkpoint_outcome is not True:
            raise ValueError("shortcut baseline must be frozen before checkpoint outcome")
        if self.require_every_case is not True:
            raise ValueError("production qualification requires every frozen case")
        if _num(self.minimum_absolute_increment,"minimum_absolute_increment") < 0:
            raise ValueError("minimum_absolute_increment must be nonnegative")

def qualify_relational_increment(
    *, learned_case_metrics: Mapping[str,object],
    shortcut_case_metrics: Mapping[str,object],
    authority: RelationalShortcutIncrementAuthorityV1,
)->dict[str,object]:
    authority.validate()
    if set(learned_case_metrics)!=set(shortcut_case_metrics):
        raise ValueError("learned and shortcut case IDs must match exactly")
    detail={}; failed=[]
    for case in sorted(learned_case_metrics):
        learned=_num(learned_case_metrics[case],f"learned[{case}]")
        shortcut=_num(shortcut_case_metrics[case],f"shortcut[{case}]")
        required=shortcut+float(authority.minimum_absolute_increment)
        passed=learned>required
        detail[case]={"learned":learned,"shortcut":shortcut,
                      "required_strictly_greater_than":required,"pass":passed}
        if not passed: failed.append(case)
    if failed:
        raise RuntimeError(f"STOP_RELATIONAL_SHORTCUT_INCREMENT_NOT_EARNED: {failed}")
    return {"passed":True,"cases":detail,
            "shortcut_baseline_authority_id":authority.shortcut_baseline_authority_id,
            "heldout_unit_policy_id":authority.heldout_unit_policy_id}
