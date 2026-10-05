"""Streaming nonlinear expression-proxy challenge for current FULL104 masking."""
from __future__ import annotations

import hashlib
import heapq
from typing import Any, Mapping

import numpy as np

from . import full104_masking_streaming_executor_v1 as stream_impl
from . import masking_control_executor_v1 as control_impl

_EPS = 1e-12


def _priority(selection_row: int, donor: int, target_id: object, fold_index: int, seed: int) -> int:
    raw = f"V5_NONLINEAR_SAMPLE_V1|{seed}|{fold_index}|{target_id}|{donor}|{selection_row}".encode("utf-8")
    return int.from_bytes(hashlib.sha256(raw).digest()[:8], "big", signed=False)


def _screen_features(stream, *, train_donors, target_col, mask, feature_count, y_override):
    visible = np.asarray(
        [int(c) for c in stream.universe_cols if int(c) not in mask and int(c) != int(target_col)],
        dtype=np.int64,
    )
    if visible.size == 0:
        return visible
    if y_override is None:
        scores = stream_impl._source_balanced_abs_corr_scores(
            stream, donors=train_donors, target_col=int(target_col), candidate_cols=visible
        )
    else:
        scores = control_impl._abs_corr_scores(
            stream, donors=train_donors, y_by_selection=y_override, candidate_cols=visible
        )
    return stream_impl._rank_by_score(visible, scores, int(feature_count))


def _collect_exact_stats(stream, *, donors, target_col, features, y_override):
    if y_override is None:
        return stream_impl._collect_stats(
            stream, donors=donors, target_col=int(target_col), feature_cols=features, need_xx=False
        )
    return control_impl._collect_override_stats(
        stream, donors=donors, y_by_selection=y_override, feature_cols=features, need_xx=False
    )


def _sample_rows(
    stream,
    *,
    donors,
    target_col,
    target_id,
    fold_index,
    features,
    cap,
    seed,
    y_override,
):
    wanted = set(map(int, donors))
    heaps = {d: [] for d in wanted}
    cols = np.concatenate(([int(target_col)], features)) if y_override is None else np.asarray(features, dtype=np.int64)
    override = None if y_override is None else np.asarray(y_override, dtype=np.float64).reshape(-1)
    if override is not None and (override.size != stream.expected_cell_count or np.any(~np.isfinite(override))):
        raise ValueError("override target must contain one finite value per FULL104 row")

    for block in stream.iter_blocks(columns=cols):
        donor_code = np.asarray(block.donor_code, dtype=np.int64)
        selection = np.asarray(block.selection_rows, dtype=np.int64)
        dense = block.X.toarray().astype(np.float64)
        if y_override is None:
            y_block, x_block = dense[:, 0], dense[:, 1:]
        else:
            y_block, x_block = override[selection], dense
        for donor in sorted(set(map(int, donor_code)) & wanted):
            local = np.flatnonzero(donor_code == donor)
            if local.size == 0:
                continue
            priorities = np.asarray(
                [_priority(int(selection[i]), donor, target_id, int(fold_index), int(seed)) for i in local],
                dtype=np.uint64,
            )
            k = min(int(cap), int(local.size))
            chosen = local if k == local.size else local[np.argpartition(priorities, kth=k - 1)[:k]]
            heap = heaps[donor]
            for i in chosen:
                p = _priority(int(selection[i]), donor, target_id, int(fold_index), int(seed))
                item = (-p, -int(selection[i]), float(y_block[i]), tuple(map(float, x_block[i])))
                if len(heap) < int(cap):
                    heapq.heappush(heap, item)
                elif item > heap[0]:
                    heapq.heapreplace(heap, item)

    out = {}
    for donor in sorted(wanted):
        if not heaps[donor]:
            raise ValueError(f"nonlinear sampler found no rows for donor {donor}")
        rows = [(-neg_sel, y, np.asarray(x, dtype=np.float64)) for _, neg_sel, y, x in heaps[donor]]
        rows.sort(key=lambda z: z[0])
        out[donor] = rows
    return out


def _standardize(samples: Mapping[int, list], stats: Mapping[int, Any]):
    xs, ys, ds, ws = [], [], [], []
    for donor in sorted(samples):
        st = stats[donor]
        mean_x = np.asarray(st.sum_x, dtype=np.float64) / int(st.n)
        var_x = np.maximum(np.asarray(st.sum_x2, dtype=np.float64) / int(st.n) - mean_x * mean_x, 0.0)
        sd_x = np.where(np.sqrt(var_x) > _EPS, np.sqrt(var_x), 1.0)
        mean_y = float(st.sum_y) / int(st.n)
        rows = samples[donor]
        w = 1.0 / len(rows)
        for _, y, x in rows:
            xs.append((np.asarray(x, dtype=np.float64) - mean_x) / sd_x)
            ys.append(float(y) - mean_y)
            ds.append(int(donor))
            ws.append(w)
    return np.vstack(xs), np.asarray(ys), np.asarray(ds, dtype=np.int64), np.asarray(ws)


def _donor_r2(y, pred, donor):
    out = {}
    for raw_d in np.unique(donor):
        d = int(raw_d)
        ix = donor == d
        yy = y[ix] - float(np.mean(y[ix]))
        pp = pred[ix] - float(np.mean(pred[ix]))
        den = float(np.sqrt(np.dot(yy, yy) * np.dot(pp, pp)))
        r = 0.0 if den <= _EPS else float(np.dot(yy, pp) / den)
        out[d] = r * r
    return out


def _source_balanced(scores, source_by_donor):
    grouped = {}
    for donor, value in scores.items():
        grouped.setdefault(source_by_donor[int(donor)], []).append(float(value))
    if not grouped:
        raise ValueError("nonlinear score has no heldout donors")
    return float(np.mean([np.mean(v) for v in grouped.values()]))


def run_nonlinear_mask_score(
    *,
    stream: stream_impl.Full104ManifestStreamV1,
    fold_index: int,
    target_col: int,
    target_id: object,
    mask: set[int],
    authority: Any,
    primary_parameters: Any,
    y_override_by_selection: np.ndarray | None = None,
) -> dict[str, Any]:
    stream.validate_layout()
    authority.validate()
    primary_parameters.validate()
    authority.bind_primary_parameters(primary_parameters)

    heldout = np.flatnonzero(stream.fold_by_donor == int(fold_index)).astype(np.int64)
    train = np.flatnonzero(stream.fold_by_donor != int(fold_index)).astype(np.int64)
    if heldout.size == 0 or train.size == 0:
        raise ValueError("nonlinear challenge fold requires train and heldout donors")

    features = _screen_features(
        stream,
        train_donors=train,
        target_col=int(target_col),
        mask=set(map(int, mask)),
        feature_count=int(authority.feature_count),
        y_override=y_override_by_selection,
    )
    if features.size == 0:
        return {
            "challenge_id": authority.challenge_id,
            "score": 0.0,
            "donor_scores": tuple((int(d), 0.0) for d in heldout),
            "feature_cols": (),
            "train_sample_count": 0,
            "heldout_sample_count": 0,
            "train_donor_count": int(train.size),
            "heldout_donor_count": int(heldout.size),
        }

    all_donors = np.concatenate((train, heldout))
    exact_stats = _collect_exact_stats(
        stream,
        donors=all_donors,
        target_col=int(target_col),
        features=features,
        y_override=y_override_by_selection,
    )
    sampled = _sample_rows(
        stream,
        donors=all_donors,
        target_col=int(target_col),
        target_id=target_id,
        fold_index=int(fold_index),
        features=features,
        cap=int(authority.max_cells_per_donor),
        seed=int(authority.random_seed),
        y_override=y_override_by_selection,
    )
    train_samples = {int(d): sampled[int(d)] for d in train}
    held_samples = {int(d): sampled[int(d)] for d in heldout}
    x_train, y_train, donor_train, weight_train = _standardize(train_samples, exact_stats)
    x_held, y_held, donor_held, _ = _standardize(held_samples, exact_stats)

    try:
        from sklearn.ensemble import HistGradientBoostingRegressor
    except ImportError as exc:
        raise RuntimeError("scikit-learn is required for the nonlinear challenge") from exc

    model = HistGradientBoostingRegressor(
        loss="squared_error",
        learning_rate=float(authority.learning_rate),
        max_iter=int(authority.max_iter),
        max_leaf_nodes=int(authority.max_leaf_nodes),
        max_depth=None,
        min_samples_leaf=int(authority.min_samples_leaf),
        l2_regularization=float(authority.l2_regularization),
        max_bins=int(authority.max_bins),
        categorical_features=None,
        monotonic_cst=None,
        interaction_cst=None,
        warm_start=False,
        early_stopping=False,
        random_state=int(authority.random_seed),
        verbose=0,
    )
    model.fit(x_train, y_train, sample_weight=weight_train)
    pred = model.predict(x_held)
    donor_scores = _donor_r2(y_held, pred, donor_held)
    return {
        "challenge_id": authority.challenge_id,
        "model_family_id": authority.model_family_id,
        "score": _source_balanced(donor_scores, stream.source_by_donor),
        "donor_scores": tuple(sorted((int(d), float(v)) for d, v in donor_scores.items())),
        "feature_cols": tuple(map(int, features)),
        "train_sample_count": int(x_train.shape[0]),
        "heldout_sample_count": int(x_held.shape[0]),
        "train_donor_count": int(np.unique(donor_train).size),
        "heldout_donor_count": int(np.unique(donor_held).size),
    }
