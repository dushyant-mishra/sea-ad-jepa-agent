"""Audit B -- read-only mask-plan generator.

Purpose
-------
Produce the exact mask that each frozen policy would apply, for a given
target x fold, **without computing any held-out score**.

Why this is safe, and why it does not change which partners are selected
------------------------------------------------------------------------
In ``run_primary_fold_streaming`` the only function that touches held-out
donors is ``_ridge_primary_score``. Every partner-selection function --
``_top_partners``, ``_ridge_partners``, ``_prefix3_partners`` -- takes
``train_donors`` and nothing else. The mask itself is assembled by
``_base_uniform_mask``, ``_removable_order`` and ``apply_burden_preserving_swaps``,
none of which see held-out data either.

So this module does not reimplement anything. It imports and calls the frozen
functions verbatim, in the same order and with the same arguments, and simply
stops before the scoring call. Nothing is reimplemented, so nothing can drift;
the parity test in ``tests/test_v5_audit_b_mask_plan_v1.py`` pins that by
comparing against the real executor's own reported ``targeted_cols``,
``mask_cardinality`` and ``effective_targeted_n``.

STOP boundary
-------------
This module must never import or call ``_ridge_primary_score``, and must never
be given a held-out donor set. It computes mask GEOMETRY and input burden only.

Deterministic target subset
---------------------------
Full enumeration is prohibitive: ``_top_partners`` scores the target against the
entire 17,186-address universe, which costs one streaming pass over the training
donors PER TARGET PER FOLD. When a subset is used it is chosen by a declared
hash rule fixed before any result is seen -- never hand-picked -- so the subset
is reproducible and cannot have been selected to favour an outcome.

Nothing here opens a terminal masking outcome, target-panel ladder,
null-equivalence margin, D_shared, protected/pathology/DEV/SEALED data, or
training.
"""
from __future__ import annotations

import hashlib
from typing import Any, Iterable

import numpy as np

from sea_ad_jepa.v5.full104_masking_qualification_runner_v1 import apply_burden_preserving_swaps
from sea_ad_jepa.v5.full104_masking_streaming_executor_v1 import (
    _METHODS,
    _base_uniform_mask,
    _prefix3_partners,
    _removable_order,
    _ridge_partners,
    _top_partners,
)

SCHEMA = "V5_FULL104_MASK_PLAN_V1"


def deterministic_target_subset(target_ids: Iterable[object], *, count: int,
                                salt: str = "V5_AUDIT_B_TARGET_SUBSET_20260920") -> np.ndarray:
    """Indices of a reproducible target subset, fixed before any result is seen.

    Ordering is by SHA-256 of ``salt|target_id``, which depends on nothing about
    the target's data. Declaring the rule here, in code, is what makes the subset
    auditable rather than a convenience sample.
    """
    ids = [str(t) for t in target_ids]
    order = sorted(
        range(len(ids)),
        key=lambda i: hashlib.sha256(f"{salt}|{ids[i]}".encode("utf-8")).digest(),
    )
    return np.asarray(order[:count], dtype=np.int64)


def _policy_targets_for_target(
    *,
    stream: Any,
    fold_index: int,
    target_col: int,
    parameters: Any,
    global_seed: int,
) -> dict[str, tuple[int, ...]]:
    """Compute training-side partners once; burden rung is deliberately absent."""
    train_donors = np.flatnonzero(stream.fold_by_donor != fold_index).astype(np.int64)
    if train_donors.size == 0:
        raise ValueError("outer fold must contain training donors")
    return {
        "UNIFORM_RANDOM": (),
        "TOP8_CORRELATION": tuple(map(int, _top_partners(
            stream,
            train_donors=train_donors,
            target_col=int(target_col),
            cap=int(parameters.targeted_partner_cap),
        ))),
        "RIDGE8_CONDITIONAL": tuple(map(int, _ridge_partners(
            stream,
            train_donors=train_donors,
            target_col=int(target_col),
            candidate_pool_count=int(parameters.ridge_candidate_pool_count),
            cap=int(parameters.targeted_partner_cap),
            alpha=float(parameters.ridge_alpha),
        ))),
        "PREFIX3_SELECTIVE": tuple(map(int, _prefix3_partners(
            stream,
            train_donors=train_donors,
            target_col=int(target_col),
            candidate_count=int(parameters.prefix_candidate_count),
            cap=int(parameters.targeted_partner_cap),
            floor=float(parameters.prefix_floor),
            reduction=float(parameters.prefix_reduction),
            global_seed=int(global_seed),
        ))),
    }


def _assemble_plans(
    *,
    stream: Any,
    fold_index: int,
    target_col: int,
    target_id: object,
    policy_targets: dict[str, tuple[int, ...]],
    co_mask_count: int,
    global_seed: int,
) -> dict[str, dict[str, Any]]:
    base_mask = _base_uniform_mask(
        stream.universe_cols,
        target_col=int(target_col),
        co_mask_count=int(co_mask_count),
        fold_index=int(fold_index),
        target_id=target_id,
        global_seed=int(global_seed),
    )
    removable = _removable_order(
        base_mask,
        target_col=int(target_col),
        fold_index=int(fold_index),
        target_id=target_id,
        global_seed=int(global_seed),
    )
    plans: dict[str, dict[str, Any]] = {}
    for method in _METHODS:
        targeted = tuple(map(int, policy_targets[method]))
        mask = (
            set(base_mask)
            if method == "UNIFORM_RANDOM"
            else apply_burden_preserving_swaps(
                base_mask=base_mask,
                target_col=int(target_col),
                targeted_cols=targeted,
                removable_order=removable,
            )
        )
        effective = len([c for c in targeted if c not in base_mask and c != int(target_col)])
        plans[method] = {
            "mask": mask,
            "targeted_cols": targeted,
            "targeted_n": len(targeted),
            "effective_targeted_n": int(effective),
            "mask_cardinality": len(mask),
            "added_vs_base": sorted(mask - base_mask),
            "dropped_vs_base": sorted(base_mask - mask),
        }
    plans["_base_mask"] = {"mask": set(base_mask), "mask_cardinality": len(base_mask)}
    return plans


def plan_masks_for_target(
    *,
    stream: Any,
    fold_index: int,
    target_col: int,
    target_id: object,
    parameters: Any,
    co_mask_count: int,
    global_seed: int,
) -> dict[str, dict[str, Any]]:
    """Return the exact single-rung mask for every policy, without scoring."""
    policy_targets = _policy_targets_for_target(
        stream=stream,
        fold_index=fold_index,
        target_col=target_col,
        parameters=parameters,
        global_seed=global_seed,
    )
    return _assemble_plans(
        stream=stream,
        fold_index=fold_index,
        target_col=target_col,
        target_id=target_id,
        policy_targets=policy_targets,
        co_mask_count=co_mask_count,
        global_seed=global_seed,
    )


def plan_masks_for_target_ladder(
    *,
    stream: Any,
    fold_index: int,
    target_col: int,
    target_id: object,
    parameters: Any,
    co_mask_counts: Iterable[int],
    global_seed: int,
) -> dict[int, dict[str, dict[str, Any]]]:
    """Replay multiple burden rungs while computing training partners only once.

    This is an execution optimization only. Each rung is assembled by the same
    frozen base-mask/removal/swap functions used by :func:`plan_masks_for_target`.
    """
    counts = [int(x) for x in co_mask_counts]
    if not counts or any(x < 0 for x in counts) or len(set(counts)) != len(counts):
        raise ValueError("co_mask_counts must be unique nonnegative integers")
    policy_targets = _policy_targets_for_target(
        stream=stream,
        fold_index=fold_index,
        target_col=target_col,
        parameters=parameters,
        global_seed=global_seed,
    )
    return {
        count: _assemble_plans(
            stream=stream,
            fold_index=fold_index,
            target_col=target_col,
            target_id=target_id,
            policy_targets=policy_targets,
            co_mask_count=count,
            global_seed=global_seed,
        )
        for count in counts
    }
