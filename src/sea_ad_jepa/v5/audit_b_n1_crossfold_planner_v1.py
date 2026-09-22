"""Two-pass-per-target all-fold Audit-B partner planner V1.

Optimization target
-------------------
The frozen partner functions are fold-specific but their sufficient statistics
are donor-local. Re-reading FULL104 separately for four outer folds is therefore
unnecessary.

Pass 1, once per target:
- collect target-vs-every-other-core-address statistics for all 104 donors;
- derive TOP8, all four RIDGE candidate pools, and all PREFIX3 decisions for all
  folds from those donor-local statistics.

Pass 2, once per target:
- collect cross-products only for the union of the four RIDGE candidate pools
  (<=256 addresses);
- derive each fold's RIDGE8 weights/partners.

This module is required to be exactly parity-tested against the original frozen
fold-by-fold private functions. It does not touch held-out scoring outcomes.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from .audit_b_n1_cached_planner_v1 import AuditBTargetFoldPartnersV1
from .full104_masking_streaming_executor_v1 import (
    _EPS,
    _collect_stats,
    _inner_donor_groups,
    _rank_by_score,
)


def _candidate_positions(candidates: np.ndarray) -> dict[int, int]:
    return {int(col): i for i, col in enumerate(candidates)}


def _abs_corr_from_stats(
    *,
    stats: dict,
    donors: np.ndarray,
    positions: np.ndarray,
    source_by_donor: np.ndarray,
) -> np.ndarray:
    if positions.size == 0:
        return np.empty(0, dtype=np.float64)
    per_source: dict[object, list[np.ndarray]] = {}
    for raw in donors:
        d = int(raw)
        st = stats[d]
        sx = st.sum_x[positions]
        sx2 = st.sum_x2[positions]
        sxy = st.sum_xy[positions]
        vx = np.maximum(sx2 - (sx * sx) / st.n, 0.0)
        vy = max(st.sum_y2 - (st.sum_y * st.sum_y) / st.n, 0.0)
        cov = sxy - sx * (st.sum_y / st.n)
        den = np.sqrt(vx * vy)
        corr = np.divide(
            np.abs(cov),
            den,
            out=np.zeros_like(cov),
            where=den > _EPS,
        )
        per_source.setdefault(source_by_donor[d], []).append(corr)
    if not per_source:
        raise ValueError("correlation screening requires donors")
    return np.mean(
        np.vstack(
            [np.mean(np.vstack(values), axis=0) for values in per_source.values()]
        ),
        axis=0,
    )


def _single_partner_score_from_stats(
    *,
    stats: dict,
    donors: np.ndarray,
    position: int,
    source_by_donor: np.ndarray,
) -> float:
    per_source: dict[object, list[float]] = {}
    for raw in donors:
        d = int(raw)
        st = stats[d]
        sx = float(st.sum_x[position])
        sx2 = float(st.sum_x2[position])
        sxy = float(st.sum_xy[position])
        vx = max(sx2 - (sx * sx) / st.n, 0.0)
        vy = max(st.sum_y2 - (st.sum_y * st.sum_y) / st.n, 0.0)
        cov = sxy - sx * (st.sum_y / st.n)
        den = float(np.sqrt(vx * vy))
        r = 0.0 if den <= _EPS else cov / den
        per_source.setdefault(source_by_donor[d], []).append(r * r)
    return float(np.mean([np.mean(values) for values in per_source.values()]))


def _fit_ridge_from_union_stats(
    *,
    stats: dict,
    donors: np.ndarray,
    union_positions: np.ndarray,
    alpha: float,
) -> np.ndarray:
    p = union_positions.size
    if p == 0:
        return np.empty(0, dtype=np.float64)
    gram = np.zeros((p, p), dtype=np.float64)
    rhs = np.zeros(p, dtype=np.float64)
    rss_y = 0.0
    n_total = 0

    for raw in donors:
        st = stats[int(raw)]
        sx = st.sum_x[union_positions]
        sx2 = st.sum_x2[union_positions]
        sxy = st.sum_xy[union_positions]
        if st.sum_xx is None:
            raise ValueError("ridge union statistics require sum_xx")
        sxx = st.sum_xx[np.ix_(union_positions, union_positions)]

        mean_x = sx / st.n
        var_x = np.maximum(sx2 / st.n - mean_x * mean_x, 0.0)
        sd = np.sqrt(var_x)
        sd = np.where(sd > _EPS, sd, 1.0)
        centered_xx = sxx - np.outer(sx, sx) / st.n
        gram += centered_xx / (sd[:, None] * sd[None, :])
        centered_xy = sxy - sx * (st.sum_y / st.n)
        rhs += centered_xy / sd
        rss_y += max(st.sum_y2 - (st.sum_y * st.sum_y) / st.n, 0.0)
        n_total += st.n

    if n_total == 0:
        raise ValueError("ridge fit requires training rows")
    scale = float(np.sqrt(max(rss_y / n_total, 0.0)))
    if scale <= _EPS:
        return np.zeros(p, dtype=np.float64)
    regularized = gram + (float(alpha) * n_total) * np.eye(p, dtype=np.float64)
    return np.linalg.solve(regularized, rhs / scale)


def _prefix3_from_first_pass(
    *,
    stream: Any,
    stats: dict,
    candidates: np.ndarray,
    pos_by_col: dict[int, int],
    train_donors: np.ndarray,
    target_col: int,
    candidate_count: int,
    cap: int,
    floor: float,
    reduction: float,
    global_seed: int,
) -> tuple[int, ...]:
    groups = _inner_donor_groups(
        stream,
        train_donors=train_donors,
        global_seed=global_seed,
    )
    if groups is None:
        return ()

    selected_sets: list[tuple[int, ...]] = []
    source = np.asarray(stream.source_by_donor, dtype=object)
    all_positions = np.arange(candidates.size, dtype=np.int64)

    for rotation in range(3):
        screen_donors = groups[rotation]
        rank_donors = groups[(rotation + 1) % 3]
        validate_donors = groups[(rotation + 2) % 3]

        screen = _abs_corr_from_stats(
            stats=stats,
            donors=screen_donors,
            positions=all_positions,
            source_by_donor=source,
        )
        selected_candidates = _rank_by_score(
            candidates,
            screen,
            int(candidate_count),
        )
        if selected_candidates.size == 0:
            selected_sets.append(())
            continue

        def remaining_proxy_score(remaining: np.ndarray) -> float:
            if remaining.size == 0:
                return 0.0
            positions = np.asarray(
                [pos_by_col[int(col)] for col in remaining],
                dtype=np.int64,
            )
            rank_score = _abs_corr_from_stats(
                stats=stats,
                donors=rank_donors,
                positions=positions,
                source_by_donor=source,
            )
            best = int(_rank_by_score(remaining, rank_score, 1)[0])
            return _single_partner_score_from_stats(
                stats=stats,
                donors=validate_donors,
                position=pos_by_col[best],
                source_by_donor=source,
            )

        baseline = remaining_proxy_score(selected_candidates)
        if baseline < float(floor):
            selected_sets.append(())
            continue

        chosen: tuple[int, ...] = ()
        for k in range(1, min(int(cap), selected_candidates.size) + 1):
            remaining = selected_candidates[k:]
            if remaining_proxy_score(remaining) <= (1.0 - float(reduction)) * baseline:
                chosen = tuple(map(int, selected_candidates[:k]))
                break
        selected_sets.append(chosen)

    support: dict[int, int] = {}
    for selected in selected_sets:
        for col in set(selected):
            support[col] = support.get(col, 0) + 1
    if not support:
        return ()

    items = np.asarray(sorted(support), dtype=np.int64)
    positions = np.asarray([pos_by_col[int(col)] for col in items], dtype=np.int64)
    evidence = _abs_corr_from_stats(
        stats=stats,
        donors=train_donors,
        positions=positions,
        source_by_donor=source,
    )
    support_count = np.asarray([support[int(col)] for col in items], dtype=np.int64)
    order = np.lexsort((items, -evidence, -support_count))
    return tuple(map(int, items[order[: min(int(cap), items.size)]]))


def select_all_fold_partners_two_pass(
    *,
    stream: Any,
    target_col: int,
    parameters: Any,
    global_seed: int,
) -> tuple[AuditBTargetFoldPartnersV1, ...]:
    """Return exact partner sets for folds 0..3 using two stream passes/target."""
    parameters.validate()
    target = int(target_col)
    candidates = np.asarray(
        [int(col) for col in stream.universe_cols if int(col) != target],
        dtype=np.int64,
    )
    if candidates.size == 0:
        raise ValueError("partner selection requires non-target candidates")
    all_donors = np.arange(len(stream.fold_by_donor), dtype=np.int64)
    source = np.asarray(stream.source_by_donor, dtype=object)
    pos_by_col = _candidate_positions(candidates)
    all_positions = np.arange(candidates.size, dtype=np.int64)

    first = _collect_stats(
        stream,
        donors=all_donors,
        target_col=target,
        feature_cols=candidates,
        need_xx=False,
    )

    top_by_fold: dict[int, tuple[int, ...]] = {}
    prefix_by_fold: dict[int, tuple[int, ...]] = {}
    ridge_pool_by_fold: dict[int, np.ndarray] = {}

    for fold in range(4):
        train = np.flatnonzero(stream.fold_by_donor != fold).astype(np.int64)
        if train.size == 0:
            raise ValueError("outer fold has no training donors")

        screen = _abs_corr_from_stats(
            stats=first,
            donors=train,
            positions=all_positions,
            source_by_donor=source,
        )
        top_by_fold[fold] = tuple(
            map(int, _rank_by_score(candidates, screen, int(parameters.targeted_partner_cap)))
        )
        ridge_pool_by_fold[fold] = _rank_by_score(
            candidates,
            screen,
            int(parameters.ridge_candidate_pool_count),
        )
        prefix_by_fold[fold] = _prefix3_from_first_pass(
            stream=stream,
            stats=first,
            candidates=candidates,
            pos_by_col=pos_by_col,
            train_donors=train,
            target_col=target,
            candidate_count=int(parameters.prefix_candidate_count),
            cap=int(parameters.targeted_partner_cap),
            floor=float(parameters.prefix_floor),
            reduction=float(parameters.prefix_reduction),
            global_seed=int(global_seed),
        )

    union_cols = np.asarray(
        sorted(
            {
                int(col)
                for pool in ridge_pool_by_fold.values()
                for col in pool
            }
        ),
        dtype=np.int64,
    )
    if union_cols.size > 4 * int(parameters.ridge_candidate_pool_count):
        raise ValueError("ridge union unexpectedly exceeds four candidate pools")

    second = _collect_stats(
        stream,
        donors=all_donors,
        target_col=target,
        feature_cols=union_cols,
        need_xx=True,
    )
    union_pos = {int(col): i for i, col in enumerate(union_cols)}

    out: list[AuditBTargetFoldPartnersV1] = []
    for fold in range(4):
        train = np.flatnonzero(stream.fold_by_donor != fold).astype(np.int64)
        pool = ridge_pool_by_fold[fold]
        positions = np.asarray([union_pos[int(col)] for col in pool], dtype=np.int64)
        weights = _fit_ridge_from_union_stats(
            stats=second,
            donors=train,
            union_positions=positions,
            alpha=float(parameters.ridge_alpha),
        )
        order = np.lexsort((pool, -np.abs(weights)))
        ridge = tuple(
            map(
                int,
                pool[order[: min(int(parameters.targeted_partner_cap), pool.size)]],
            )
        )
        out.append(
            AuditBTargetFoldPartnersV1(
                target_col=target,
                fold_index=fold,
                uniform_random=(),
                top8_correlation=top_by_fold[fold],
                ridge8_conditional=ridge,
                prefix3_selective=prefix_by_fold[fold],
            )
        )

    return tuple(out)
