"""Policy-specific nonlinear evidence orchestration for FULL104 masking.

This module uses only current FULL104 authorities and current control mechanics.
It produces the six nonlinear evidence modes required by the final assembler:
real, shuffled, planted detect/after, and their matched shuffled planted baselines.
"""
from __future__ import annotations

from typing import Any, Sequence

import numpy as np

from . import masking_control_executor_v1 as controls
from .masking_nonlinear_challenge_executor_v1 import run_nonlinear_mask_score


MODES = (
    "REAL",
    "SHUFFLED",
    "PLANTED_DETECT",
    "PLANTED_AFTER",
    "PLANTED_SHUFFLED_DETECT",
    "PLANTED_SHUFFLED_AFTER",
)


def _wrap(
    result: dict[str, Any],
    *,
    mode: str,
    method: str,
    fold_index: int,
    target_col: int,
    target_id: object,
) -> dict[str, Any]:
    if mode not in MODES:
        raise ValueError("unknown nonlinear evidence mode")
    return {
        "mode": mode,
        "method": method,
        "fold": int(fold_index),
        "target_col": int(target_col),
        "target_id": target_id,
        "score": float(result["score"]),
        "donor_scores": tuple(result["donor_scores"]),
        "feature_cols": tuple(result["feature_cols"]),
        "train_sample_count": int(result["train_sample_count"]),
        "heldout_sample_count": int(result["heldout_sample_count"]),
    }


def run_policy_nonlinear_evidence_fold(
    *,
    stream: Any,
    fold_index: int,
    parameters: Any,
    evidence_budget: Any,
    nonlinear_authority: Any,
    target_col: int,
    target_id: object,
    method: str,
    primary_targeted_cols: Sequence[int],
    eligible_proxy_cols: Sequence[int],
    global_seed: int,
) -> list[dict[str, Any]]:
    stream.validate_layout()
    parameters.validate()
    evidence_budget.validate()
    nonlinear_authority.validate()

    co_mask_count = int(evidence_budget.mask_count(int(stream.universe_cols.size - 1)))

    _, real_mask = controls._policy_mask(
        method,
        stream=stream,
        target_col=int(target_col),
        target_id=target_id,
        fold_index=int(fold_index),
        global_seed=int(global_seed),
        co_mask_count=co_mask_count,
        targeted=tuple(map(int, primary_targeted_cols)),
    )
    real = run_nonlinear_mask_score(
        stream=stream,
        fold_index=int(fold_index),
        target_col=int(target_col),
        target_id=target_id,
        mask=real_mask,
        authority=nonlinear_authority,
        primary_parameters=parameters,
    )

    raw_target, donor_by_row = controls.materialize_stream_column(
        stream, column=int(target_col)
    )
    shuffled_target = controls.deterministic_within_donor_shuffle(
        raw_target,
        donor_by_row,
        target_id=target_id,
        global_seed=int(global_seed),
    )
    train = np.flatnonzero(stream.fold_by_donor != int(fold_index)).astype(np.int64)
    shuffled_targets = controls._policy_targets(
        method,
        stream=stream,
        train_donors=train,
        y_by_selection=shuffled_target,
        target_col=int(target_col),
        parameters=parameters,
        global_seed=int(global_seed),
    )
    _, shuffled_mask = controls._policy_mask(
        method,
        stream=stream,
        target_col=int(target_col),
        target_id=target_id,
        fold_index=int(fold_index),
        global_seed=int(global_seed),
        co_mask_count=co_mask_count,
        targeted=shuffled_targets,
    )
    shuffled = run_nonlinear_mask_score(
        stream=stream,
        fold_index=int(fold_index),
        target_col=int(target_col),
        target_id=target_id,
        mask=shuffled_mask,
        authority=nonlinear_authority,
        primary_parameters=parameters,
        y_override_by_selection=shuffled_target,
    )

    proxy_col = controls.select_planted_proxy(
        eligible_cols=eligible_proxy_cols,
        target_col=int(target_col),
        target_id=target_id,
    )
    planted_y, planted_donor = controls.materialize_stream_column(
        stream, column=int(proxy_col)
    )
    if not np.array_equal(planted_donor, donor_by_row):
        raise ValueError("planted proxy and real target donor identities disagree")
    planted_shuffled = controls.deterministic_within_donor_shuffle(
        planted_y,
        planted_donor,
        target_id=f"PLANTED|{target_id}",
        global_seed=int(global_seed),
    )
    planted_targets = controls._policy_targets(
        method,
        stream=stream,
        train_donors=train,
        y_by_selection=planted_y,
        target_col=int(target_col),
        parameters=parameters,
        global_seed=int(global_seed),
    )
    _, planted_mask = controls._policy_mask(
        method,
        stream=stream,
        target_col=int(target_col),
        target_id=target_id,
        fold_index=int(fold_index),
        global_seed=int(global_seed),
        co_mask_count=co_mask_count,
        targeted=planted_targets,
    )
    detection_mask = {int(target_col)}

    kwargs = dict(
        stream=stream,
        fold_index=int(fold_index),
        target_col=int(target_col),
        target_id=target_id,
        authority=nonlinear_authority,
        primary_parameters=parameters,
    )
    planted_detect = run_nonlinear_mask_score(
        **kwargs, mask=detection_mask, y_override_by_selection=planted_y
    )
    planted_after = run_nonlinear_mask_score(
        **kwargs, mask=planted_mask, y_override_by_selection=planted_y
    )
    planted_shuffled_detect = run_nonlinear_mask_score(
        **kwargs, mask=detection_mask, y_override_by_selection=planted_shuffled
    )
    planted_shuffled_after = run_nonlinear_mask_score(
        **kwargs, mask=planted_mask, y_override_by_selection=planted_shuffled
    )

    return [
        _wrap(real, mode="REAL", method=method, fold_index=fold_index, target_col=target_col, target_id=target_id),
        _wrap(shuffled, mode="SHUFFLED", method=method, fold_index=fold_index, target_col=target_col, target_id=target_id),
        _wrap(planted_detect, mode="PLANTED_DETECT", method=method, fold_index=fold_index, target_col=target_col, target_id=target_id),
        _wrap(planted_after, mode="PLANTED_AFTER", method=method, fold_index=fold_index, target_col=target_col, target_id=target_id),
        _wrap(planted_shuffled_detect, mode="PLANTED_SHUFFLED_DETECT", method=method, fold_index=fold_index, target_col=target_col, target_id=target_id),
        _wrap(planted_shuffled_after, mode="PLANTED_SHUFFLED_AFTER", method=method, fold_index=fold_index, target_col=target_col, target_id=target_id),
    ]
