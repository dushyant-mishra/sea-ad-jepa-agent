"""N1-only cached mask planner with parity to frozen Audit-B plan generator.

Partner discovery is a function of target x fold and the frozen parameters; it
does not depend on burden rung. N1 spans six rungs, so recomputing training-side
partner discovery six times would waste most of the execution cost.

This module calls the same frozen private selection functions as the original
read-only plan generator, once per target x fold, then applies the same
common-random base-mask and exact burden-preserving swap mechanics per rung.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

import numpy as np

from sea_ad_jepa.v5.full104_masking_qualification_runner_v1 import (
    apply_burden_preserving_swaps,
)
from sea_ad_jepa.v5.full104_masking_streaming_executor_v1 import (
    _METHODS,
    _base_uniform_mask,
    _prefix3_partners,
    _removable_order,
    _ridge_partners,
    _top_partners,
)


@dataclass(frozen=True)
class AuditBTargetFoldPartnersV1:
    target_col: int
    fold_index: int
    uniform_random: tuple[int, ...]
    top8_correlation: tuple[int, ...]
    ridge8_conditional: tuple[int, ...]
    prefix3_selective: tuple[int, ...]

    def by_policy(self) -> Mapping[str, tuple[int, ...]]:
        return {
            "UNIFORM_RANDOM": self.uniform_random,
            "TOP8_CORRELATION": self.top8_correlation,
            "RIDGE8_CONDITIONAL": self.ridge8_conditional,
            "PREFIX3_SELECTIVE": self.prefix3_selective,
        }


def select_target_fold_partners(
    *,
    stream: Any,
    fold_index: int,
    target_col: int,
    parameters: Any,
    global_seed: int,
) -> AuditBTargetFoldPartnersV1:
    if fold_index not in (0, 1, 2, 3):
        raise ValueError("fold_index must be 0..3")
    train_donors = np.flatnonzero(stream.fold_by_donor != fold_index).astype(np.int64)
    if train_donors.size == 0:
        raise ValueError("outer fold must contain training donors")

    return AuditBTargetFoldPartnersV1(
        target_col=int(target_col),
        fold_index=int(fold_index),
        uniform_random=(),
        top8_correlation=tuple(
            map(
                int,
                _top_partners(
                    stream,
                    train_donors=train_donors,
                    target_col=int(target_col),
                    cap=int(parameters.targeted_partner_cap),
                ),
            )
        ),
        ridge8_conditional=tuple(
            map(
                int,
                _ridge_partners(
                    stream,
                    train_donors=train_donors,
                    target_col=int(target_col),
                    candidate_pool_count=int(parameters.ridge_candidate_pool_count),
                    cap=int(parameters.targeted_partner_cap),
                    alpha=float(parameters.ridge_alpha),
                ),
            )
        ),
        prefix3_selective=tuple(
            map(
                int,
                _prefix3_partners(
                    stream,
                    train_donors=train_donors,
                    target_col=int(target_col),
                    candidate_count=int(parameters.prefix_candidate_count),
                    cap=int(parameters.targeted_partner_cap),
                    floor=float(parameters.prefix_floor),
                    reduction=float(parameters.prefix_reduction),
                    global_seed=int(global_seed),
                ),
            )
        ),
    )


def plans_from_cached_partners(
    *,
    stream: Any,
    partners: AuditBTargetFoldPartnersV1,
    target_id: object,
    co_mask_count: int,
    global_seed: int,
) -> dict[str, dict[str, Any]]:
    if co_mask_count < 0 or co_mask_count >= len(stream.universe_cols):
        raise ValueError("co_mask_count is out of range")
    target_col = int(partners.target_col)
    fold_index = int(partners.fold_index)

    base_mask = _base_uniform_mask(
        stream.universe_cols,
        target_col=target_col,
        co_mask_count=int(co_mask_count),
        fold_index=fold_index,
        target_id=target_id,
        global_seed=int(global_seed),
    )
    removable = _removable_order(
        base_mask,
        target_col=target_col,
        fold_index=fold_index,
        target_id=target_id,
        global_seed=int(global_seed),
    )
    policy_targets = partners.by_policy()

    plans: dict[str, dict[str, Any]] = {}
    for method in _METHODS:
        targeted = tuple(map(int, policy_targets[method]))
        if method == "UNIFORM_RANDOM":
            mask = set(base_mask)
        else:
            mask = apply_burden_preserving_swaps(
                base_mask=base_mask,
                target_col=target_col,
                targeted_cols=targeted,
                removable_order=removable,
            )
        effective = len(
            [c for c in targeted if c not in base_mask and c != target_col]
        )
        plans[method] = {
            "mask": mask,
            "targeted_cols": targeted,
            "targeted_n": len(targeted),
            "effective_targeted_n": int(effective),
            "mask_cardinality": len(mask),
            "added_vs_base": sorted(mask - base_mask),
            "dropped_vs_base": sorted(base_mask - mask),
        }
    plans["_base_mask"] = {
        "mask": set(base_mask),
        "mask_cardinality": len(base_mask),
    }
    return plans
