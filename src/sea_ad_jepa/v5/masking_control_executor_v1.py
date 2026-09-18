"""Current FULL104 masking controls without discovery-era data-path spillover.

Positive control
----------------
A proxy address is selected deterministically from the *current* eligible
strict-core target universe, independently of expression values or masking
outcomes.  The virtual target is exactly that proxy's normalized expression.
This is deliberately an easy planted shortcut: the purpose is to prove that
the current screening/attacker path can detect a shortcut and that targeted
co-masking can remove it.

Negative control
----------------
The real target vector is deterministically permuted within each donor.  This
preserves each donor's target-value distribution while destroying cell-level
molecular coupling.  Any systematic targeted-mask advantage after this
intervention is a false-positive signal.

No discovery paths, fixed discovery target positions, 15%/900 burden, or
historical target lists are used here.  Callers provide current FULL104
authorities and target/proxy eligibility.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
from typing import Any, Sequence

import numpy as np

from . import full104_masking_streaming_executor_v1 as stream_impl


_EPS = 1e-12
PLANTED_PROXY_NAMESPACE = "V5_FULL104_PLANTED_PROXY_V1"
NEGATIVE_SHUFFLE_NAMESPACE = "V5_FULL104_WITHIN_DONOR_NEGATIVE_V1"


def _as_int_vector(value: Any, name: str) -> np.ndarray:
    out = np.asarray(value)
    if out.ndim != 1 or not np.issubdtype(out.dtype, np.integer):
        raise ValueError(f"{name} must be a one-dimensional integer array")
    return out.astype(np.int64, copy=False)


def _seed(*parts: object) -> int:
    payload = "|".join(str(part) for part in parts).encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big", signed=False)


def select_planted_proxy(
    *,
    eligible_cols: Sequence[int],
    target_col: int,
    target_id: object,
) -> int:
    """Select one outcome-blind proxy from the current eligible strict core."""

    cols = _as_int_vector(eligible_cols, "eligible_cols")
    candidates = [int(c) for c in cols if int(c) != int(target_col)]
    if not candidates:
        raise ValueError("planted control requires at least one eligible non-target proxy")
    return min(
        candidates,
        key=lambda col: hashlib.sha256(
            f"{PLANTED_PROXY_NAMESPACE}|{target_id}|{int(target_col)}|{col}".encode("utf-8")
        ).digest(),
    )


def materialize_stream_column(
    stream: stream_impl.Full104ManifestStreamV1,
    *,
    column: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Materialize one normalized FULL104 column plus donor code by selection row."""

    stream.validate_layout()
    if isinstance(column, bool) or not isinstance(column, (int, np.integer)):
        raise ValueError("column must be an integer")
    values = np.full(stream.expected_cell_count, np.nan, dtype=np.float64)
    donor_code = np.full(stream.expected_cell_count, -1, dtype=np.int64)
    seen = np.zeros(stream.expected_cell_count, dtype=np.bool_)
    for block in stream.iter_blocks(columns=np.asarray([int(column)], dtype=np.int64)):
        rows = np.asarray(block.selection_rows, dtype=np.int64)
        if np.any(seen[rows]):
            raise ValueError("duplicate selection row while materializing control target")
        local = block.X.toarray().reshape(-1).astype(np.float64)
        values[rows] = local
        donor_code[rows] = np.asarray(block.donor_code, dtype=np.int64)
        seen[rows] = True
    if not np.all(seen) or np.any(~np.isfinite(values)) or np.any(donor_code < 0):
        raise ValueError("control target materialization did not close over FULL104 rows")
    return values, donor_code


def deterministic_within_donor_shuffle(
    values: np.ndarray,
    donor_code: np.ndarray,
    *,
    target_id: object,
    global_seed: int,
) -> np.ndarray:
    """Deterministically permute target values independently within each donor."""

    y = np.asarray(values, dtype=np.float64).reshape(-1)
    donor = _as_int_vector(donor_code, "donor_code")
    if y.size != donor.size or y.size == 0 or np.any(~np.isfinite(y)):
        raise ValueError("values and donor_code must be finite, nonempty and aligned")
    if isinstance(global_seed, bool) or not isinstance(global_seed, int) or global_seed < 0:
        raise ValueError("global_seed must be a nonnegative integer")
    out = y.copy()
    for raw_donor in np.unique(donor):
        d = int(raw_donor)
        ix = np.flatnonzero(donor == d)
        rng = np.random.default_rng(
            _seed(NEGATIVE_SHUFFLE_NAMESPACE, global_seed, target_id, d)
        )
        out[ix] = y[ix][rng.permutation(ix.size)]
    return out


@dataclass
class _OverrideStats:
    n: int
    sum_y: float
    sum_y2: float
    sum_x: np.ndarray
    sum_x2: np.ndarray
    sum_xy: np.ndarray
    sum_xx: np.ndarray | None


def _collect_override_stats(
    stream: stream_impl.Full104ManifestStreamV1,
    *,
    donors: np.ndarray,
    y_by_selection: np.ndarray,
    feature_cols: np.ndarray,
    need_xx: bool,
) -> dict[int, _OverrideStats]:
    donor_ids = _as_int_vector(donors, "donors")
    features = _as_int_vector(feature_cols, "feature_cols")
    y_all = np.asarray(y_by_selection, dtype=np.float64).reshape(-1)
    if y_all.size != stream.expected_cell_count or np.any(~np.isfinite(y_all)):
        raise ValueError("override target must contain one finite value per FULL104 row")
    wanted = set(map(int, donor_ids))
    stats: dict[int, _OverrideStats] = {}

    for block in stream.iter_blocks(columns=features):
        present = sorted(set(map(int, block.donor_code)) & wanted)
        if not present:
            continue
        block_y = y_all[np.asarray(block.selection_rows, dtype=np.int64)]
        for donor in present:
            ix = np.asarray(block.donor_code) == donor
            A = block.X[ix].tocsr()
            y = block_y[ix]
            n = int(A.shape[0])
            if n == 0:
                continue
            sx = np.asarray(A.sum(axis=0)).reshape(-1)
            sx2 = np.asarray(A.power(2).sum(axis=0)).reshape(-1)
            sxy = np.asarray(A.T @ y).reshape(-1)
            sy = float(np.sum(y))
            sy2 = float(np.dot(y, y))
            sxx = (
                (A.T @ A).toarray()
                if need_xx and features.size
                else (np.zeros((0, 0), dtype=np.float64) if need_xx else None)
            )
            current = stats.get(donor)
            if current is None:
                stats[donor] = _OverrideStats(
                    n=n,
                    sum_y=sy,
                    sum_y2=sy2,
                    sum_x=sx.astype(np.float64, copy=False),
                    sum_x2=sx2.astype(np.float64, copy=False),
                    sum_xy=sxy.astype(np.float64, copy=False),
                    sum_xx=None if sxx is None else np.asarray(sxx, dtype=np.float64),
                )
            else:
                current.n += n
                current.sum_y += sy
                current.sum_y2 += sy2
                current.sum_x += sx
                current.sum_x2 += sx2
                current.sum_xy += sxy
                if need_xx:
                    assert current.sum_xx is not None and sxx is not None
                    current.sum_xx += sxx

    missing = [int(d) for d in donor_ids if int(d) not in stats]
    if missing:
        raise ValueError(f"control stream contains no rows for donors: {missing[:5]}")
    return stats


def _standardized_components(
    st: _OverrideStats,
) -> tuple[np.ndarray, np.ndarray, float]:
    if st.sum_x.size == 0:
        return np.zeros((0, 0), dtype=np.float64), np.empty(0, dtype=np.float64), max(
            st.sum_y2 - (st.sum_y * st.sum_y) / st.n, 0.0
        )
    if st.sum_xx is None:
        raise ValueError("sum_xx is required for standardized control statistics")
    mean_x = st.sum_x / st.n
    var_x = np.maximum(st.sum_x2 / st.n - mean_x * mean_x, 0.0)
    sd = np.sqrt(var_x)
    sd = np.where(sd > _EPS, sd, 1.0)
    centered_xx = st.sum_xx - np.outer(st.sum_x, st.sum_x) / st.n
    gram = centered_xx / (sd[:, None] * sd[None, :])
    centered_xy = st.sum_xy - st.sum_x * (st.sum_y / st.n)
    rhs = centered_xy / sd
    rss_y = max(st.sum_y2 - (st.sum_y * st.sum_y) / st.n, 0.0)
    return gram, rhs, rss_y


def _abs_corr_scores(
    stream: stream_impl.Full104ManifestStreamV1,
    *,
    donors: np.ndarray,
    y_by_selection: np.ndarray,
    candidate_cols: np.ndarray,
) -> np.ndarray:
    cols = _as_int_vector(candidate_cols, "candidate_cols")
    if cols.size == 0:
        return np.empty(0, dtype=np.float64)
    stats = _collect_override_stats(
        stream,
        donors=donors,
        y_by_selection=y_by_selection,
        feature_cols=cols,
        need_xx=False,
    )
    by_source: dict[object, list[np.ndarray]] = {}
    for raw_donor in donors:
        donor = int(raw_donor)
        st = stats[donor]
        vx = np.maximum(st.sum_x2 - (st.sum_x * st.sum_x) / st.n, 0.0)
        vy = max(st.sum_y2 - (st.sum_y * st.sum_y) / st.n, 0.0)
        cov = st.sum_xy - st.sum_x * (st.sum_y / st.n)
        den = np.sqrt(vx * vy)
        corr = np.divide(np.abs(cov), den, out=np.zeros_like(cov), where=den > _EPS)
        by_source.setdefault(stream.source_by_donor[donor], []).append(corr)
    return np.mean(
        np.vstack([np.mean(np.vstack(values), axis=0) for values in by_source.values()]),
        axis=0,
    )


def _fit_ridge(
    stream: stream_impl.Full104ManifestStreamV1,
    *,
    donors: np.ndarray,
    y_by_selection: np.ndarray,
    feature_cols: np.ndarray,
    alpha: float,
) -> np.ndarray:
    features = _as_int_vector(feature_cols, "feature_cols")
    stats = _collect_override_stats(
        stream,
        donors=donors,
        y_by_selection=y_by_selection,
        feature_cols=features,
        need_xx=True,
    )
    gram = np.zeros((features.size, features.size), dtype=np.float64)
    rhs = np.zeros(features.size, dtype=np.float64)
    rss_y = 0.0
    n_total = 0
    for raw_donor in donors:
        donor = int(raw_donor)
        local_gram, local_rhs, local_rss = _standardized_components(stats[donor])
        gram += local_gram
        rhs += local_rhs
        rss_y += local_rss
        n_total += stats[donor].n
    if n_total == 0:
        raise ValueError("control ridge fit has no training rows")
    scale = float(np.sqrt(max(rss_y / n_total, 0.0)))
    if scale <= _EPS or features.size == 0:
        return np.zeros(features.size, dtype=np.float64)
    return np.linalg.solve(
        gram + float(alpha) * n_total * np.eye(features.size, dtype=np.float64),
        rhs / scale,
    )


def _donor_scores(
    stream: stream_impl.Full104ManifestStreamV1,
    *,
    donors: np.ndarray,
    y_by_selection: np.ndarray,
    feature_cols: np.ndarray,
    weights: np.ndarray,
) -> dict[int, float]:
    features = _as_int_vector(feature_cols, "feature_cols")
    stats = _collect_override_stats(
        stream,
        donors=donors,
        y_by_selection=y_by_selection,
        feature_cols=features,
        need_xx=True,
    )
    out: dict[int, float] = {}
    for raw_donor in donors:
        donor = int(raw_donor)
        gram, rhs, rss_y = _standardized_components(stats[donor])
        pred_ss = float(weights @ gram @ weights)
        cov = float(weights @ rhs)
        den = float(np.sqrt(max(rss_y, 0.0) * max(pred_ss, 0.0)))
        r = 0.0 if den <= _EPS else cov / den
        out[donor] = r * r
    return out


def _source_balanced_mean(
    donor_scores: dict[int, float],
    source_by_donor: np.ndarray,
) -> float:
    grouped: dict[object, list[float]] = {}
    for donor, score in donor_scores.items():
        grouped.setdefault(source_by_donor[int(donor)], []).append(float(score))
    if not grouped:
        raise ValueError("control score has no donors")
    return float(np.mean([np.mean(values) for values in grouped.values()]))


def _rank(cols: np.ndarray, scores: np.ndarray, count: int) -> np.ndarray:
    order = np.lexsort((cols, -scores))
    return cols[order[: min(int(count), cols.size)]]


def _ridge_targets(
    stream: stream_impl.Full104ManifestStreamV1,
    *,
    train_donors: np.ndarray,
    y_by_selection: np.ndarray,
    target_col: int,
    parameters: Any,
) -> tuple[int, ...]:
    universe = np.asarray(
        [int(c) for c in stream.universe_cols if int(c) != int(target_col)],
        dtype=np.int64,
    )
    screen = _abs_corr_scores(
        stream,
        donors=train_donors,
        y_by_selection=y_by_selection,
        candidate_cols=universe,
    )
    pool = _rank(universe, screen, int(parameters.ridge_candidate_pool_count))
    weights = _fit_ridge(
        stream,
        donors=train_donors,
        y_by_selection=y_by_selection,
        feature_cols=pool,
        alpha=float(parameters.ridge_alpha),
    )
    order = np.lexsort((pool, -np.abs(weights)))
    return tuple(
        map(int, pool[order[: min(int(parameters.targeted_partner_cap), pool.size)]])
    )


def _top_targets(
    stream: stream_impl.Full104ManifestStreamV1,
    *,
    train_donors: np.ndarray,
    y_by_selection: np.ndarray,
    target_col: int,
    parameters: Any,
) -> tuple[int, ...]:
    universe = np.asarray(
        [int(col) for col in stream.universe_cols if int(col) != int(target_col)],
        dtype=np.int64,
    )
    score = _abs_corr_scores(
        stream,
        donors=train_donors,
        y_by_selection=y_by_selection,
        candidate_cols=universe,
    )
    return tuple(
        map(int, _rank(universe, score, int(parameters.targeted_partner_cap)))
    )


def _single_partner_score_override(
    stream: stream_impl.Full104ManifestStreamV1,
    *,
    donors: np.ndarray,
    y_by_selection: np.ndarray,
    partner_col: int,
) -> float:
    cols = np.asarray([int(partner_col)], dtype=np.int64)
    stats = _collect_override_stats(
        stream,
        donors=donors,
        y_by_selection=y_by_selection,
        feature_cols=cols,
        need_xx=False,
    )
    donor_scores: dict[int, float] = {}
    for raw_donor in donors:
        donor = int(raw_donor)
        st = stats[donor]
        vx = max(float(st.sum_x2[0] - (st.sum_x[0] * st.sum_x[0]) / st.n), 0.0)
        vy = max(float(st.sum_y2 - (st.sum_y * st.sum_y) / st.n), 0.0)
        cov = float(st.sum_xy[0] - st.sum_x[0] * (st.sum_y / st.n))
        den = float(np.sqrt(vx * vy))
        r = 0.0 if den <= _EPS else cov / den
        donor_scores[donor] = r * r
    return _source_balanced_mean(donor_scores, stream.source_by_donor)


def _prefix3_targets(
    stream: stream_impl.Full104ManifestStreamV1,
    *,
    train_donors: np.ndarray,
    y_by_selection: np.ndarray,
    target_col: int,
    parameters: Any,
    global_seed: int,
) -> tuple[int, ...]:
    groups = stream_impl._inner_donor_groups(
        stream,
        train_donors=train_donors,
        global_seed=int(global_seed),
    )
    if groups is None:
        return ()
    universe = np.asarray(
        [int(col) for col in stream.universe_cols if int(col) != int(target_col)],
        dtype=np.int64,
    )
    selected_sets: list[tuple[int, ...]] = []
    for rotation in range(3):
        screen_donors = groups[rotation]
        rank_donors = groups[(rotation + 1) % 3]
        validate_donors = groups[(rotation + 2) % 3]
        screen = _abs_corr_scores(
            stream,
            donors=screen_donors,
            y_by_selection=y_by_selection,
            candidate_cols=universe,
        )
        candidates = _rank(universe, screen, int(parameters.prefix_candidate_count))
        if candidates.size == 0:
            selected_sets.append(())
            continue

        def remaining_proxy_score(remaining: np.ndarray) -> float:
            if remaining.size == 0:
                return 0.0
            rank_score = _abs_corr_scores(
                stream,
                donors=rank_donors,
                y_by_selection=y_by_selection,
                candidate_cols=remaining,
            )
            best = int(_rank(remaining, rank_score, 1)[0])
            return _single_partner_score_override(
                stream,
                donors=validate_donors,
                y_by_selection=y_by_selection,
                partner_col=best,
            )

        baseline = remaining_proxy_score(candidates)
        if baseline < float(parameters.prefix_floor):
            selected_sets.append(())
            continue
        chosen: tuple[int, ...] = ()
        for k in range(1, min(int(parameters.targeted_partner_cap), candidates.size) + 1):
            remaining = candidates[k:]
            if remaining_proxy_score(remaining) <= (
                1.0 - float(parameters.prefix_reduction)
            ) * baseline:
                chosen = tuple(map(int, candidates[:k]))
                break
        selected_sets.append(chosen)

    support: dict[int, int] = {}
    for selected in selected_sets:
        for col in set(selected):
            support[col] = support.get(col, 0) + 1
    if not support:
        return ()
    items = np.asarray(sorted(support), dtype=np.int64)
    evidence = _abs_corr_scores(
        stream,
        donors=train_donors,
        y_by_selection=y_by_selection,
        candidate_cols=items,
    )
    support_count = np.asarray([support[int(col)] for col in items], dtype=np.int64)
    order = np.lexsort((items, -evidence, -support_count))
    return tuple(
        map(
            int,
            items[
                order[: min(int(parameters.targeted_partner_cap), items.size)]
            ],
        )
    )


def _policy_targets(
    method: str,
    *,
    stream: stream_impl.Full104ManifestStreamV1,
    train_donors: np.ndarray,
    y_by_selection: np.ndarray,
    target_col: int,
    parameters: Any,
    global_seed: int,
) -> tuple[int, ...]:
    if method == "UNIFORM_RANDOM":
        return ()
    if method == "TOP8_CORRELATION":
        return _top_targets(
            stream,
            train_donors=train_donors,
            y_by_selection=y_by_selection,
            target_col=target_col,
            parameters=parameters,
        )
    if method == "RIDGE8_CONDITIONAL":
        return _ridge_targets(
            stream,
            train_donors=train_donors,
            y_by_selection=y_by_selection,
            target_col=target_col,
            parameters=parameters,
        )
    if method == "PREFIX3_SELECTIVE":
        return _prefix3_targets(
            stream,
            train_donors=train_donors,
            y_by_selection=y_by_selection,
            target_col=target_col,
            parameters=parameters,
            global_seed=global_seed,
        )
    raise ValueError(f"unapproved masking policy for control execution: {method!r}")


def _policy_mask(
    method: str,
    *,
    stream: stream_impl.Full104ManifestStreamV1,
    target_col: int,
    target_id: object,
    fold_index: int,
    global_seed: int,
    co_mask_count: int,
    targeted: tuple[int, ...],
) -> tuple[set[int], set[int]]:
    base = stream_impl._base_uniform_mask(
        stream.universe_cols,
        target_col=int(target_col),
        co_mask_count=int(co_mask_count),
        fold_index=int(fold_index),
        target_id=target_id,
        global_seed=int(global_seed),
    )
    if method == "UNIFORM_RANDOM":
        return set(base), set(base)
    removable = stream_impl._removable_order(
        base,
        target_col=int(target_col),
        fold_index=int(fold_index),
        target_id=target_id,
        global_seed=int(global_seed),
    )
    masked = stream_impl.apply_burden_preserving_swaps(
        base_mask=base,
        target_col=int(target_col),
        targeted_cols=targeted,
        removable_order=removable,
    )
    return set(base), masked


def _score_mask(
    stream: stream_impl.Full104ManifestStreamV1,
    *,
    train_donors: np.ndarray,
    heldout_donors: np.ndarray,
    y_by_selection: np.ndarray,
    target_col: int,
    mask: set[int],
    parameters: Any,
) -> tuple[float, dict[int, float]]:
    visible = np.asarray(
        [
            int(c)
            for c in stream.universe_cols
            if int(c) not in mask and int(c) != int(target_col)
        ],
        dtype=np.int64,
    )
    if visible.size == 0:
        donor_scores = {int(d): 0.0 for d in heldout_donors}
        return _source_balanced_mean(donor_scores, stream.source_by_donor), donor_scores
    screen = _abs_corr_scores(
        stream,
        donors=train_donors,
        y_by_selection=y_by_selection,
        candidate_cols=visible,
    )
    features = _rank(visible, screen, int(parameters.ridge_score_feature_count))
    weights = _fit_ridge(
        stream,
        donors=train_donors,
        y_by_selection=y_by_selection,
        feature_cols=features,
        alpha=float(parameters.ridge_alpha),
    )
    donor_scores = _donor_scores(
        stream,
        donors=heldout_donors,
        y_by_selection=y_by_selection,
        feature_cols=features,
        weights=weights,
    )
    return _source_balanced_mean(donor_scores, stream.source_by_donor), donor_scores


def run_planted_proxy_control_fold(
    *,
    stream: stream_impl.Full104ManifestStreamV1,
    fold_index: int,
    parameters: Any,
    evidence_budget: Any,
    target_col: int,
    target_id: object,
    eligible_proxy_cols: Sequence[int],
    method: str,
    global_seed: int,
) -> dict[str, Any]:
    """Run the current planted-shortcut control for one held-donor fold."""

    stream.validate_layout()
    parameters.validate()
    evidence_budget.validate()
    proxy_col = select_planted_proxy(
        eligible_cols=eligible_proxy_cols,
        target_col=int(target_col),
        target_id=target_id,
    )
    y, donor_by_row = materialize_stream_column(stream, column=proxy_col)
    if not np.array_equal(
        np.sort(np.unique(donor_by_row)),
        np.arange(stream.source_by_donor.size, dtype=np.int64),
    ):
        raise ValueError("planted control target does not cover the donor registry")

    heldout = np.flatnonzero(stream.fold_by_donor == int(fold_index)).astype(np.int64)
    train = np.flatnonzero(stream.fold_by_donor != int(fold_index)).astype(np.int64)
    if heldout.size == 0 or train.size == 0:
        raise ValueError("control fold requires train and heldout donors")

    detection_mask = {int(target_col)}
    detect_score, detect_donor = _score_mask(
        stream,
        train_donors=train,
        heldout_donors=heldout,
        y_by_selection=y,
        target_col=int(target_col),
        mask=detection_mask,
        parameters=parameters,
    )
    targeted = _policy_targets(
        method,
        stream=stream,
        train_donors=train,
        y_by_selection=y,
        target_col=int(target_col),
        parameters=parameters,
        global_seed=int(global_seed),
    )
    eligible_non_target = int(stream.universe_cols.size - 1)
    co_mask_count = int(evidence_budget.mask_count(eligible_non_target))
    base, targeted_mask = _policy_mask(
        method,
        stream=stream,
        target_col=int(target_col),
        target_id=target_id,
        fold_index=int(fold_index),
        global_seed=int(global_seed),
        co_mask_count=co_mask_count,
        targeted=targeted,
    )
    after_score, after_donor = _score_mask(
        stream,
        train_donors=train,
        heldout_donors=heldout,
        y_by_selection=y,
        target_col=int(target_col),
        mask=targeted_mask,
        parameters=parameters,
    )
    shuffled_y = deterministic_within_donor_shuffle(
        y,
        donor_by_row,
        target_id=f"PLANTED|{target_id}",
        global_seed=int(global_seed),
    )
    shuffled_detect_score, shuffled_detect_donor = _score_mask(
        stream,
        train_donors=train,
        heldout_donors=heldout,
        y_by_selection=shuffled_y,
        target_col=int(target_col),
        mask=detection_mask,
        parameters=parameters,
    )
    shuffled_after_score, shuffled_after_donor = _score_mask(
        stream,
        train_donors=train,
        heldout_donors=heldout,
        y_by_selection=shuffled_y,
        target_col=int(target_col),
        mask=targeted_mask,
        parameters=parameters,
    )
    return {
        "control_id": "PLANTED_SHORTCUT_POSITIVE_CONTROL_V1",
        "fold": int(fold_index),
        "method": method,
        "target_col": int(target_col),
        "target_id": target_id,
        "proxy_col": int(proxy_col),
        "proxy_selected": int(proxy_col) in set(targeted),
        "targeted_cols": targeted,
        "detect_score": float(detect_score),
        "after_mask_score": float(after_score),
        "shuffled_detect_score": float(shuffled_detect_score),
        "shuffled_after_mask_score": float(shuffled_after_score),
        "detect_excess": float(detect_score - shuffled_detect_score),
        "after_mask_excess": float(after_score - shuffled_after_score),
        "detect_donor_scores": tuple(sorted((int(k), float(v)) for k, v in detect_donor.items())),
        "after_mask_donor_scores": tuple(sorted((int(k), float(v)) for k, v in after_donor.items())),
        "shuffled_detect_donor_scores": tuple(sorted((int(k), float(v)) for k, v in shuffled_detect_donor.items())),
        "shuffled_after_mask_donor_scores": tuple(sorted((int(k), float(v)) for k, v in shuffled_after_donor.items())),
        "mask_cardinality": len(targeted_mask),
        "uniform_mask_cardinality": len(base),
    }


def run_shuffled_negative_control_fold(
    *,
    stream: stream_impl.Full104ManifestStreamV1,
    fold_index: int,
    parameters: Any,
    evidence_budget: Any,
    target_col: int,
    target_id: object,
    method: str,
    global_seed: int,
) -> dict[str, Any]:
    """Run deterministic within-donor shuffled target control for one fold and policy."""

    stream.validate_layout()
    parameters.validate()
    evidence_budget.validate()
    raw_y, donor_by_row = materialize_stream_column(stream, column=int(target_col))
    y = deterministic_within_donor_shuffle(
        raw_y,
        donor_by_row,
        target_id=target_id,
        global_seed=int(global_seed),
    )

    heldout = np.flatnonzero(stream.fold_by_donor == int(fold_index)).astype(np.int64)
    train = np.flatnonzero(stream.fold_by_donor != int(fold_index)).astype(np.int64)
    targeted = _policy_targets(
        method,
        stream=stream,
        train_donors=train,
        y_by_selection=y,
        target_col=int(target_col),
        parameters=parameters,
        global_seed=int(global_seed),
    )
    eligible_non_target = int(stream.universe_cols.size - 1)
    co_mask_count = int(evidence_budget.mask_count(eligible_non_target))
    base, targeted_mask = _policy_mask(
        method,
        stream=stream,
        target_col=int(target_col),
        target_id=target_id,
        fold_index=int(fold_index),
        global_seed=int(global_seed),
        co_mask_count=co_mask_count,
        targeted=targeted,
    )
    uniform_score, uniform_donor = _score_mask(
        stream,
        train_donors=train,
        heldout_donors=heldout,
        y_by_selection=y,
        target_col=int(target_col),
        mask=set(base),
        parameters=parameters,
    )
    targeted_score, targeted_donor = _score_mask(
        stream,
        train_donors=train,
        heldout_donors=heldout,
        y_by_selection=y,
        target_col=int(target_col),
        mask=targeted_mask,
        parameters=parameters,
    )
    donor_delta = tuple(
        (int(d), float(uniform_donor[int(d)] - targeted_donor[int(d)]))
        for d in sorted(uniform_donor)
    )
    return {
        "control_id": "WITHIN_DONOR_SHUFFLED_NEGATIVE_CONTROL_V1",
        "method": method,
        "fold": int(fold_index),
        "target_col": int(target_col),
        "target_id": target_id,
        "uniform_score": float(uniform_score),
        "targeted_score": float(targeted_score),
        "delta": float(uniform_score - targeted_score),
        "uniform_donor_scores": tuple(
            sorted((int(d), float(v)) for d, v in uniform_donor.items())
        ),
        "targeted_donor_scores": tuple(
            sorted((int(d), float(v)) for d, v in targeted_donor.items())
        ),
        "donor_delta": donor_delta,
        "targeted_cols": targeted,
        "mask_cardinality": len(targeted_mask),
        "uniform_mask_cardinality": len(base),
    }
