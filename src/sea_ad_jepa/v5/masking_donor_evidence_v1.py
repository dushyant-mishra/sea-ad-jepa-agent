"""Additive donor-level evidence for the frozen masking runners.

The canonical and streaming runners remain byte-stable. This companion
reconstructs the already-frozen masks from their ordinary result rows, refits
the same ridge attacker with each runner's own primitives, and emits held-out
per-donor correlation-squared values. It fails if those donor values do not
reproduce the runner's source-balanced aggregate score.
"""
from __future__ import annotations

from typing import Any, Callable

import numpy as np

from . import full104_masking_qualification_runner_v1 as reference
from . import full104_masking_streaming_executor_v1 as streaming


_EPS = 1e-12


def _source_balanced_from_donors(
    donor_scores: dict[int, float],
    source_by_donor: np.ndarray,
) -> float:
    source = np.asarray(source_by_donor, dtype=object)
    if not donor_scores:
        raise ValueError("donor evidence cannot be empty")
    grouped: dict[object, list[float]] = {}
    for donor, score in donor_scores.items():
        if donor < 0 or donor >= source.size:
            raise ValueError("donor evidence references donor outside source metadata")
        grouped.setdefault(source[int(donor)], []).append(float(score))
    return float(np.mean([np.mean(values) for values in grouped.values()]))


def _reference_donor_scores(
    *,
    arrays: reference.QualificationArrays,
    train_donors: np.ndarray,
    heldout_donors: np.ndarray,
    target_col: int,
    mask: set[int],
    feature_count: int,
    alpha: float,
) -> tuple[float, dict[int, float]]:
    visible = np.asarray(
        [
            int(col)
            for col in arrays.universe_cols
            if int(col) not in mask and int(col) != int(target_col)
        ],
        dtype=np.int64,
    )
    if visible.size == 0:
        out = {int(d): 0.0 for d in heldout_donors}
        return _source_balanced_from_donors(out, arrays.source_by_donor), out
    screen = reference._source_balanced_abs_corr_scores(
        arrays,
        donors=train_donors,
        target_col=target_col,
        candidate_cols=visible,
    )
    features = reference._rank_by_score(visible, screen, int(feature_count))
    weights = reference._fit_ridge_weights(
        arrays,
        donors=train_donors,
        target_col=target_col,
        feature_cols=features,
        alpha=float(alpha),
    )
    rows = reference._rows_for_donors(arrays.donor_code, heldout_donors)
    A = reference._standardized_features(arrays, rows=rows, cols=features)
    pred = A @ weights
    y = (
        arrays.X.tocsr()[rows, int(target_col)]
        .toarray()
        .reshape(-1)
        .astype(np.float64)
    )
    row_donor = np.asarray(arrays.donor_code[rows], dtype=np.int64)
    out: dict[int, float] = {}
    for raw_donor in heldout_donors:
        donor = int(raw_donor)
        ix = row_donor == donor
        yy = y[ix] - float(np.mean(y[ix]))
        pp = pred[ix] - float(np.mean(pred[ix]))
        den = float(np.sqrt(np.dot(yy, yy) * np.dot(pp, pp)))
        r = 0.0 if den <= _EPS else float(np.dot(yy, pp) / den)
        out[donor] = r * r
    return _source_balanced_from_donors(out, arrays.source_by_donor), out


def _streaming_donor_scores(
    *,
    stream: streaming.Full104ManifestStreamV1,
    train_donors: np.ndarray,
    heldout_donors: np.ndarray,
    target_col: int,
    mask: set[int],
    feature_count: int,
    alpha: float,
) -> tuple[float, dict[int, float]]:
    visible = np.asarray(
        [
            int(col)
            for col in stream.universe_cols
            if int(col) not in mask and int(col) != int(target_col)
        ],
        dtype=np.int64,
    )
    if visible.size == 0:
        out = {int(d): 0.0 for d in heldout_donors}
        return _source_balanced_from_donors(out, stream.source_by_donor), out
    screen = streaming._source_balanced_abs_corr_scores(
        stream,
        donors=train_donors,
        target_col=target_col,
        candidate_cols=visible,
    )
    features = streaming._rank_by_score(visible, screen, int(feature_count))
    weights = streaming._fit_ridge_weights(
        stream,
        donors=train_donors,
        target_col=target_col,
        feature_cols=features,
        alpha=float(alpha),
    )
    stats = streaming._collect_stats(
        stream,
        donors=heldout_donors,
        target_col=target_col,
        feature_cols=features,
        need_xx=True,
    )
    out: dict[int, float] = {}
    for raw_donor in heldout_donors:
        donor = int(raw_donor)
        gram, rhs, rss_y = streaming._standardized_components(stats[donor])
        pred_ss = float(weights @ gram @ weights)
        cov = float(weights @ rhs)
        den = float(np.sqrt(max(rss_y, 0.0) * max(pred_ss, 0.0)))
        r = 0.0 if den <= _EPS else cov / den
        out[donor] = r * r
    return _source_balanced_from_donors(out, stream.source_by_donor), out


def _mask_from_row(
    *,
    universe_cols: np.ndarray,
    target_col: int,
    target_id: object,
    fold_index: int,
    global_seed: int,
    co_mask_count: int,
    method: str,
    targeted_cols: tuple[int, ...],
    base_mask_fn: Callable[..., set[int]],
    removable_order_fn: Callable[..., tuple[int, ...]],
) -> set[int]:
    base = base_mask_fn(
        universe_cols,
        target_col=int(target_col),
        co_mask_count=int(co_mask_count),
        fold_index=int(fold_index),
        target_id=target_id,
        global_seed=int(global_seed),
    )
    if method == "UNIFORM_RANDOM":
        return set(base)
    removable = removable_order_fn(
        base,
        target_col=int(target_col),
        fold_index=int(fold_index),
        target_id=target_id,
        global_seed=int(global_seed),
    )
    return reference.apply_burden_preserving_swaps(
        base_mask=base,
        target_col=int(target_col),
        targeted_cols=tuple(map(int, targeted_cols)),
        removable_order=removable,
    )


def run_reference_fold_with_donor_evidence(
    *,
    arrays: reference.QualificationArrays,
    fold_index: int,
    parameters: Any,
    evidence_budget: Any,
    global_seed: int,
) -> list[dict[str, Any]]:
    rows = reference.run_primary_fold(
        arrays=arrays,
        fold_index=fold_index,
        parameters=parameters,
        evidence_budget=evidence_budget,
        global_seed=global_seed,
    )
    co_mask_count = int(evidence_budget.mask_count(int(arrays.universe_cols.size - 1)))
    folds = np.asarray(arrays.fold_by_donor, dtype=np.int64)
    heldout = np.flatnonzero(folds == fold_index).astype(np.int64)
    train = np.flatnonzero(folds != fold_index).astype(np.int64)
    out: list[dict[str, Any]] = []
    for row in rows:
        mask = _mask_from_row(
            universe_cols=arrays.universe_cols,
            target_col=int(row["target_col"]),
            target_id=row["target_id"],
            fold_index=fold_index,
            global_seed=global_seed,
            co_mask_count=co_mask_count,
            method=str(row["method"]),
            targeted_cols=tuple(row["targeted_cols"]),
            base_mask_fn=reference._base_uniform_mask,
            removable_order_fn=reference._removable_order,
        )
        aggregate, donor_scores = _reference_donor_scores(
            arrays=arrays,
            train_donors=train,
            heldout_donors=heldout,
            target_col=int(row["target_col"]),
            mask=mask,
            feature_count=int(parameters.ridge_score_feature_count),
            alpha=float(parameters.ridge_alpha),
        )
        if not np.isclose(aggregate, float(row["score"]), rtol=0.0, atol=1e-12):
            raise ValueError("donor evidence does not reproduce canonical aggregate score")
        enriched = dict(row)
        enriched["heldout_donor_scores"] = tuple(
            (int(d), float(donor_scores[int(d)])) for d in sorted(donor_scores)
        )
        out.append(enriched)
    return out


def run_streaming_fold_with_donor_evidence(
    *,
    stream: streaming.Full104ManifestStreamV1,
    fold_index: int,
    parameters: Any,
    evidence_budget: Any,
    global_seed: int,
) -> list[dict[str, Any]]:
    rows = streaming.run_primary_fold_streaming(
        stream=stream,
        fold_index=fold_index,
        parameters=parameters,
        evidence_budget=evidence_budget,
        global_seed=global_seed,
    )
    co_mask_count = int(evidence_budget.mask_count(int(stream.universe_cols.size - 1)))
    folds = np.asarray(stream.fold_by_donor, dtype=np.int64)
    heldout = np.flatnonzero(folds == fold_index).astype(np.int64)
    train = np.flatnonzero(folds != fold_index).astype(np.int64)
    out: list[dict[str, Any]] = []
    for row in rows:
        mask = _mask_from_row(
            universe_cols=stream.universe_cols,
            target_col=int(row["target_col"]),
            target_id=row["target_id"],
            fold_index=fold_index,
            global_seed=global_seed,
            co_mask_count=co_mask_count,
            method=str(row["method"]),
            targeted_cols=tuple(row["targeted_cols"]),
            base_mask_fn=streaming._base_uniform_mask,
            removable_order_fn=streaming._removable_order,
        )
        aggregate, donor_scores = _streaming_donor_scores(
            stream=stream,
            train_donors=train,
            heldout_donors=heldout,
            target_col=int(row["target_col"]),
            mask=mask,
            feature_count=int(parameters.ridge_score_feature_count),
            alpha=float(parameters.ridge_alpha),
        )
        if not np.isclose(aggregate, float(row["score"]), rtol=0.0, atol=1e-12):
            raise ValueError("donor evidence does not reproduce streaming aggregate score")
        enriched = dict(row)
        enriched["heldout_donor_scores"] = tuple(
            (int(d), float(donor_scores[int(d)])) for d in sorted(donor_scores)
        )
        out.append(enriched)
    return out
