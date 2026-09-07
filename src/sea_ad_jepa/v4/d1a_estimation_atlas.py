"""D1-A V2 synthetic/u0-safe estimation and ranking atlas.

This module is intentionally zero-update and non-confirmatory.  It implements the
prospective D1-A V2 prototype only; it is not the final real-trained-teacher D1
algorithm and refuses real trained-teacher modes/protected outcome metadata.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Mapping, Sequence

import numpy as np
import pandas as pd

from sea_ad_jepa.v4.foundation_state_stability import (
    hungarian_axis_match,
    principal_angle_metrics,
)

ALGORITHM_ID = "D1A_SYNTHETIC_ESTIMATION_ATLAS_V2"
CONTRACT_ROOT = "6af28682da4a5c37a212ad1926fbc6acf5a7fea88c46c49f69295cbaae8a3a81"

BOOTSTRAP_RESAMPLES = 128
BOOTSTRAP_SEED = 9107001
DONOR_SPLIT_SEED = "D1A_SPLIT_V1"
TAIL_FRACTION = 0.05
REPRESENTATIVE_CELLS = 5
REPRESENTATIVE_DONORS = 5
TOP_FEATURES_PER_SIGN = 10
CORRELATION_MIN_CELLS = 3
CI_QUANTILES = (0.025, 0.975)

ALLOWED_MODES = {"synthetic", "u0_safe"}
FORBIDDEN_METADATA_TOKENS = (
    "pathology",
    "oracle",
    "sealed",
    "development",
    "diagnosis",
    "braak",
    "amyloid",
    "tau",
)
REQUIRED_METADATA = ("canonical_cell_id", "donor", "source", "operator")


@dataclass(frozen=True)
class D1AAtlasResult:
    program_table: pd.DataFrame
    state_loading_table: pd.DataFrame
    cell_ranking_table: pd.DataFrame
    molecular_table: pd.DataFrame
    donor_table: pd.DataFrame
    source_table: pd.DataFrame
    operator_table: pd.DataFrame
    hypothesis_catalog: pd.DataFrame
    diagnostics: dict[str, object]


def _as_float64(values: np.ndarray, *, name: str) -> np.ndarray:
    out = np.asarray(values, dtype=np.float64)
    if out.ndim != 2:
        raise ValueError(f"{name} must be a 2-D array")
    return np.ascontiguousarray(out)


def _validate_inputs(
    states: np.ndarray,
    metadata: pd.DataFrame,
    molecular_values: np.ndarray,
    measured_mask: np.ndarray,
    feature_ids: Sequence[str],
    *,
    mode: str,
    n_components: int,
    known_molecular_reference_programs: Mapping[str, np.ndarray] | None,
) -> tuple[np.ndarray, pd.DataFrame, np.ndarray, np.ndarray, list[str], dict[str, np.ndarray]]:
    if mode not in ALLOWED_MODES:
        raise ValueError("D1-A V2 mode must be one of synthetic/u0_safe; real trained-teacher execution is unauthorized")

    states64 = _as_float64(states, name="states")
    if states64.shape[1] != 160:
        raise ValueError("states must have shape [cells,160]")
    if states64.shape[0] < 3 or not np.isfinite(states64).all():
        raise ValueError("states must contain at least three finite cells")

    if not isinstance(metadata, pd.DataFrame):
        raise TypeError("metadata must be a pandas DataFrame")
    missing = [column for column in REQUIRED_METADATA if column not in metadata.columns]
    if missing:
        raise ValueError(f"metadata missing required columns: {missing}")
    for column in metadata.columns:
        lower = str(column).lower()
        if any(token in lower for token in FORBIDDEN_METADATA_TOKENS):
            raise ValueError(f"protected outcome metadata is forbidden in D1-A: {column}")
    meta = metadata.loc[:, list(REQUIRED_METADATA)].copy().reset_index(drop=True)
    if len(meta) != len(states64):
        raise ValueError("metadata row count must match states")
    for column in REQUIRED_METADATA:
        if meta[column].isna().any():
            raise ValueError(f"metadata column contains missing values: {column}")
        meta[column] = meta[column].astype(str)
    if not meta["canonical_cell_id"].is_unique:
        raise ValueError("canonical_cell_id must be unique")

    molecular64 = _as_float64(molecular_values, name="molecular_values")
    mask = np.asarray(measured_mask, dtype=bool)
    if molecular64.shape != mask.shape:
        raise ValueError("measured_mask must match molecular_values shape")
    if molecular64.shape[0] != states64.shape[0]:
        raise ValueError("molecular_values row count must match states")
    if not np.isfinite(molecular64[mask]).all():
        raise ValueError("physically measured molecular values must be finite")

    features = [str(item) for item in feature_ids]
    if len(features) != molecular64.shape[1] or len(set(features)) != len(features):
        raise ValueError("feature_ids must be unique and match molecular feature count")

    rank_bound = min(states64.shape[0] - 1, states64.shape[1])
    if not isinstance(n_components, int) or n_components <= 0 or n_components > rank_bound:
        raise ValueError("n_components exceeds the D1-A deterministic rank bound")

    refs: dict[str, np.ndarray] = {}
    for key, vector in (known_molecular_reference_programs or {}).items():
        name = str(key)
        arr = np.asarray(vector, dtype=np.float64)
        if arr.shape != (len(features),) or not np.isfinite(arr).all():
            raise ValueError(f"known molecular reference {name!r} must be finite with one value per feature")
        if float(np.linalg.norm(arr)) == 0.0:
            raise ValueError(f"known molecular reference {name!r} cannot be all zero")
        refs[name] = np.ascontiguousarray(arr)

    return states64, meta, molecular64, mask, features, refs


def _hash_chunk(hasher: "hashlib._Hash", payload: bytes) -> None:
    hasher.update(len(payload).to_bytes(8, byteorder="big", signed=False))
    hasher.update(payload)


def _array_payload(values: np.ndarray, dtype: np.dtype) -> bytes:
    arr = np.ascontiguousarray(values, dtype=dtype)
    shape = json.dumps(list(arr.shape), separators=(",", ":")).encode("ascii")
    return len(shape).to_bytes(8, "big") + shape + arr.tobytes(order="C")


def _input_root(
    states: np.ndarray,
    meta: pd.DataFrame,
    molecular: np.ndarray,
    mask: np.ndarray,
    feature_ids: Sequence[str],
    refs: Mapping[str, np.ndarray],
    *,
    mode: str,
) -> str:
    h = hashlib.sha256()
    _hash_chunk(h, ALGORITHM_ID.encode("utf-8"))
    _hash_chunk(h, mode.encode("utf-8"))
    _hash_chunk(h, _array_payload(states, np.float64))

    rows = [
        {key: str(row[key]) for key in REQUIRED_METADATA}
        for row in meta.to_dict(orient="records")
    ]
    _hash_chunk(
        h,
        json.dumps(rows, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8"),
    )
    _hash_chunk(h, _array_payload(molecular, np.float64))
    _hash_chunk(h, _array_payload(mask.astype(np.uint8), np.uint8))
    _hash_chunk(h, json.dumps(list(feature_ids), ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
    for name, vector in refs.items():
        _hash_chunk(h, name.encode("utf-8"))
        _hash_chunk(h, _array_payload(vector.reshape(1, -1), np.float64))
    return h.hexdigest()


def _orient_components(components: np.ndarray) -> np.ndarray:
    oriented = np.asarray(components, dtype=np.float64).copy()
    for row in oriented:
        pivot = int(np.argmax(np.abs(row)))
        if row[pivot] < 0.0:
            row *= -1.0
    return oriented


def _fit_pca(states: np.ndarray, n_components: int) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    mean = states.mean(axis=0)
    centered = states - mean
    _, singular, vh = np.linalg.svd(centered, full_matrices=False)
    total = float(np.square(singular).sum())
    if not np.isfinite(total) or total <= 0.0:
        raise ValueError("states have no finite variance for D1-A decomposition")
    components = _orient_components(vh[:n_components])
    scores = centered @ components.T
    explained = np.square(singular[:n_components]) / total
    return mean, components, scores, explained


def _pearson(x: np.ndarray, y: np.ndarray) -> float:
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    good = np.isfinite(x) & np.isfinite(y)
    if int(good.sum()) < CORRELATION_MIN_CELLS:
        return float("nan")
    xv = x[good]
    yv = y[good]
    xv = xv - xv.mean()
    yv = yv - yv.mean()
    denom = float(np.sqrt(np.square(xv).sum() * np.square(yv).sum()))
    if denom <= 0.0:
        return float("nan")
    return float(np.dot(xv, yv) / denom)


def _eta_squared(values: np.ndarray, groups: Sequence[str]) -> float:
    x = np.asarray(values, dtype=np.float64)
    labels = np.asarray(groups, dtype=object)
    unique = np.unique(labels)
    if len(unique) <= 1:
        return 0.0
    grand = float(x.mean())
    total = float(np.square(x - grand).sum())
    if total <= 0.0:
        return 0.0
    between = 0.0
    for group in unique:
        part = x[labels == group]
        between += float(len(part)) * float((part.mean() - grand) ** 2)
    return float(np.clip(between / total, 0.0, 1.0))


def _center_vector_by_group(values: np.ndarray, groups: Sequence[str]) -> np.ndarray:
    out = np.asarray(values, dtype=np.float64).copy()
    labels = np.asarray(groups, dtype=object)
    for group in np.unique(labels):
        idx = labels == group
        out[idx] -= out[idx].mean()
    return out


def _center_molecular_by_donor(
    values: np.ndarray,
    mask: np.ndarray,
    donors: Sequence[str],
) -> np.ndarray:
    centered = np.full(values.shape, np.nan, dtype=np.float64)
    labels = np.asarray(donors, dtype=object)
    for donor in np.unique(labels):
        idx = labels == donor
        sub_mask = mask[idx]
        sub_values = values[idx]
        counts = sub_mask.sum(axis=0)
        sums = np.where(sub_mask, sub_values, 0.0).sum(axis=0)
        means = np.divide(sums, counts, out=np.zeros_like(sums), where=counts > 0)
        centered[idx] = np.where(sub_mask, sub_values - means, np.nan)
    return centered


def _vectorized_correlations(x: np.ndarray, y: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """Per-feature Pearson correlations using pairwise physical measurement masks."""
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    mask = np.asarray(mask, dtype=bool)
    if y.ndim != 2 or mask.shape != y.shape or len(x) != len(y):
        raise ValueError("correlation geometry mismatch")

    n = mask.sum(axis=0).astype(np.float64)
    y0 = np.where(mask, y, 0.0)
    sx = (mask * x[:, None]).sum(axis=0)
    sy = y0.sum(axis=0)
    mx = np.divide(sx, n, out=np.zeros_like(sx), where=n > 0)
    my = np.divide(sy, n, out=np.zeros_like(sy), where=n > 0)
    dx = x[:, None] - mx
    dy = np.where(mask, y - my, 0.0)
    cov = (np.where(mask, dx, 0.0) * dy).sum(axis=0)
    vx = np.square(np.where(mask, dx, 0.0)).sum(axis=0)
    vy = np.square(dy).sum(axis=0)
    denom = np.sqrt(vx * vy)
    corr = np.divide(cov, denom, out=np.full_like(cov, np.nan), where=denom > 0)
    corr[n < CORRELATION_MIN_CELLS] = np.nan
    return np.clip(corr, -1.0, 1.0)


def _group_sign_support(
    score: np.ndarray,
    molecular_centered: np.ndarray,
    mask: np.ndarray,
    groups: Sequence[str],
    global_effect: np.ndarray,
) -> np.ndarray:
    labels = np.asarray(groups, dtype=object)
    matches = np.zeros(molecular_centered.shape[1], dtype=np.float64)
    evaluable = np.zeros_like(matches)
    global_sign = np.sign(global_effect)
    for group in np.unique(labels):
        idx = labels == group
        corr = _vectorized_correlations(score[idx], molecular_centered[idx], mask[idx])
        good = np.isfinite(corr) & np.isfinite(global_effect) & (global_sign != 0)
        matches[good] += (np.sign(corr[good]) == global_sign[good]).astype(np.float64)
        evaluable[good] += 1.0
    return np.divide(matches, evaluable, out=np.full_like(matches, np.nan), where=evaluable > 0)


def _bootstrap_indices(donors: Sequence[str]) -> list[np.ndarray]:
    labels = np.asarray(donors, dtype=object)
    unique = np.unique(labels)
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    by_donor = {donor: np.flatnonzero(labels == donor) for donor in unique}
    samples = []
    for _ in range(BOOTSTRAP_RESAMPLES):
        draw = rng.choice(unique, size=len(unique), replace=True)
        samples.append(np.concatenate([by_donor[donor] for donor in draw]))
    return samples


def _deterministic_donor_halves(donors: Sequence[str]) -> tuple[np.ndarray, np.ndarray]:
    unique = sorted(set(map(str, donors)))
    if len(unique) < 2:
        raise ValueError("split stability requires at least two donors")
    def key(donor: str) -> str:
        return hashlib.sha256((DONOR_SPLIT_SEED + "\0" + donor).encode("utf-8")).hexdigest()
    ordered = sorted(unique, key=key)
    a = set(ordered[0::2])
    b = set(ordered[1::2])
    labels = np.asarray(donors, dtype=object)
    return np.flatnonzero(np.isin(labels, list(a))), np.flatnonzero(np.isin(labels, list(b)))


def _split_axis_stability(states: np.ndarray, donors: Sequence[str], reference_components: np.ndarray) -> np.ndarray:
    parts = _deterministic_donor_halves(donors)
    values = []
    for idx in parts:
        k = min(reference_components.shape[0], len(idx) - 1, states.shape[1])
        if k <= 0:
            values.append(np.full(reference_components.shape[0], np.nan))
            continue
        _, candidate, _, _ = _fit_pca(states[idx], k)
        similarity = np.abs(reference_components @ candidate.T)
        values.append(similarity.max(axis=1))
    return np.nanmean(np.stack(values, axis=0), axis=0)


def _ordinal_percentile(scores: np.ndarray, cell_ids: Sequence[str]) -> np.ndarray:
    n = len(scores)
    if n == 1:
        return np.asarray([0.5], dtype=np.float64)
    order = np.lexsort((np.asarray(cell_ids, dtype=str), np.asarray(scores, dtype=np.float64)))
    rank = np.empty(n, dtype=np.int64)
    rank[order] = np.arange(n, dtype=np.int64)
    return rank.astype(np.float64) / float(n - 1)


def _direction_sha(direction: np.ndarray) -> str:
    return hashlib.sha256(np.ascontiguousarray(direction, dtype=np.float64).tobytes()).hexdigest()


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    good = np.isfinite(a) & np.isfinite(b)
    if int(good.sum()) == 0:
        return float("nan")
    av = a[good]
    bv = b[good]
    denom = float(np.linalg.norm(av) * np.linalg.norm(bv))
    if denom <= 0.0:
        return float("nan")
    return float(np.dot(av, bv) / denom)


def _known_reference_summary(effect: np.ndarray, refs: Mapping[str, np.ndarray]) -> tuple[str | None, float, float]:
    if not refs:
        return None, float("nan"), float("nan")
    candidates = []
    for name, vector in refs.items():
        value = abs(_cosine(effect, vector))
        if np.isfinite(value):
            candidates.append((value, name))
    if not candidates:
        return None, float("nan"), float("nan")
    value, name = max(candidates, key=lambda item: (item[0], item[1]))
    return name, float(value), float(1.0 - value)


def _redundancy(effect_vectors: np.ndarray) -> np.ndarray:
    k = effect_vectors.shape[0]
    out = np.zeros(k, dtype=np.float64)
    for i in range(k):
        others = [abs(_cosine(effect_vectors[i], effect_vectors[j])) for j in range(k) if j != i]
        finite = [value for value in others if np.isfinite(value)]
        out[i] = max(finite) if finite else 0.0
    return out


def _top_feature_lists(molecular: pd.DataFrame, program_id: str) -> tuple[list[str], list[str]]:
    frame = molecular[molecular["program_id"] == program_id].copy()
    finite = frame[np.isfinite(frame["effect"].to_numpy(dtype=float))].copy()
    positive = finite.sort_values(["effect", "feature_id"], ascending=[False, True])
    negative = finite.sort_values(["effect", "feature_id"], ascending=[True, True])
    pos = positive[positive["effect"] > 0]["feature_id"].head(TOP_FEATURES_PER_SIGN).astype(str).tolist()
    neg = negative[negative["effect"] < 0]["feature_id"].head(TOP_FEATURES_PER_SIGN).astype(str).tolist()
    return pos, neg


def build_d1a_atlas(
    states: np.ndarray,
    metadata: pd.DataFrame,
    molecular_values: np.ndarray,
    measured_mask: np.ndarray,
    feature_ids: Sequence[str],
    *,
    n_components: int,
    mode: str,
    known_molecular_reference_programs: Mapping[str, np.ndarray] | None = None,
) -> D1AAtlasResult:
    """Build the D1-A V2 continuous estimation/ranking atlas.

    Returns descriptive discovery tables only.  No PASS/FAIL/STOP adjudication is
    produced and no optimizer/EMA operation is possible from this API.
    """
    states, meta, molecular, mask, features, refs = _validate_inputs(
        states,
        metadata,
        molecular_values,
        measured_mask,
        feature_ids,
        mode=mode,
        n_components=n_components,
        known_molecular_reference_programs=known_molecular_reference_programs,
    )
    root = _input_root(states, meta, molecular, mask, features, refs, mode=mode)
    _, components, scores, explained = _fit_pca(states, n_components)
    program_ids = [f"D1A_PC{i + 1:03d}" for i in range(n_components)]

    donors = meta["donor"].to_numpy(dtype=str)
    sources = meta["source"].to_numpy(dtype=str)
    operators = meta["operator"].to_numpy(dtype=str)
    cell_ids = meta["canonical_cell_id"].to_numpy(dtype=str)
    measurement_support = mask.mean(axis=1, dtype=np.float64)

    centered_scores = np.column_stack([
        _center_vector_by_group(scores[:, j], donors)
        for j in range(n_components)
    ])
    molecular_centered = _center_molecular_by_donor(molecular, mask, donors)

    boot = _bootstrap_indices(donors)
    magnitude_samples = np.full((BOOTSTRAP_RESAMPLES, n_components), np.nan)
    axis_samples = np.full_like(magnitude_samples, np.nan)
    subspace_samples = np.full(BOOTSTRAP_RESAMPLES, np.nan)
    molecular_boot = np.full((BOOTSTRAP_RESAMPLES, n_components, len(features)), np.nan)

    for b, idx in enumerate(boot):
        for j in range(n_components):
            if len(idx) > 1:
                magnitude_samples[b, j] = float(np.std(scores[idx, j], ddof=1))
            molecular_boot[b, j] = _vectorized_correlations(
                centered_scores[idx, j],
                molecular_centered[idx],
                mask[idx],
            )

        k = min(n_components, len(idx) - 1, states.shape[1])
        if k > 0:
            _, candidate, _, _ = _fit_pca(states[idx], k)
            similarity = np.abs(components @ candidate.T)
            axis_samples[b] = similarity.max(axis=1)
            subspace = principal_angle_metrics(components[:k].T, candidate.T)
            subspace_samples[b] = float(subspace["median_canonical_correlation"])

    magnitude = np.std(scores, axis=0, ddof=1)
    magnitude_lo = np.nanquantile(magnitude_samples, CI_QUANTILES[0], axis=0)
    magnitude_hi = np.nanquantile(magnitude_samples, CI_QUANTILES[1], axis=0)
    axis_stability = np.nanmedian(axis_samples, axis=0)
    subspace_stability = float(np.nanmedian(subspace_samples))
    split_stability = _split_axis_stability(states, donors, components)

    cell_rows: list[dict[str, object]] = []
    donor_recurrence = np.zeros(n_components, dtype=np.float64)
    representative_cells: list[str] = []
    representative_donors: list[str] = []
    percentiles_by_program: list[np.ndarray] = []

    for j, pid in enumerate(program_ids):
        percentile = _ordinal_percentile(scores[:, j], cell_ids)
        percentiles_by_program.append(percentile)
        tails = np.where(
            percentile <= TAIL_FRACTION,
            "BOTTOM_5PCT",
            np.where(percentile >= 1.0 - TAIL_FRACTION, "TOP_5PCT", "NONE"),
        )
        tail_donors = set(donors[tails != "NONE"])
        donor_recurrence[j] = len(tail_donors) / len(set(donors))

        rep_order = np.lexsort((cell_ids, -np.abs(centered_scores[:, j])))
        rep_cells = cell_ids[rep_order[:REPRESENTATIVE_CELLS]].tolist()
        representative_cells.append(";".join(rep_cells))
        rep_donor_list: list[str] = []
        for idx in rep_order:
            donor = str(donors[idx])
            if donor not in rep_donor_list:
                rep_donor_list.append(donor)
            if len(rep_donor_list) == REPRESENTATIVE_DONORS:
                break
        representative_donors.append(";".join(rep_donor_list))

        for i in range(len(states)):
            cell_rows.append({
                "program_id": pid,
                "canonical_cell_id": cell_ids[i],
                "donor": donors[i],
                "source": sources[i],
                "operator": operators[i],
                "raw_score": float(scores[i, j]),
                "within_donor_centered_score": float(centered_scores[i, j]),
                "percentile": float(percentile[i]),
                "measurement_support": float(measurement_support[i]),
                "tail_membership": str(tails[i]),
                "input_root_sha256": root,
            })

    cell_table = pd.DataFrame(cell_rows)

    molecular_rows: list[dict[str, object]] = []
    effect_vectors = np.full((n_components, len(features)), np.nan)
    donor_sign_vectors = np.full_like(effect_vectors, np.nan)
    operator_sign_vectors = np.full_like(effect_vectors, np.nan)

    for j, pid in enumerate(program_ids):
        effect = _vectorized_correlations(centered_scores[:, j], molecular_centered, mask)
        effect_vectors[j] = effect
        donor_sign = _group_sign_support(centered_scores[:, j], molecular_centered, mask, donors, effect)
        operator_sign = _group_sign_support(centered_scores[:, j], molecular_centered, mask, operators, effect)
        donor_sign_vectors[j] = donor_sign
        operator_sign_vectors[j] = operator_sign
        ci_low = np.nanquantile(molecular_boot[:, j, :], CI_QUANTILES[0], axis=0)
        ci_high = np.nanquantile(molecular_boot[:, j, :], CI_QUANTILES[1], axis=0)

        keys = []
        for f_idx, feature in enumerate(features):
            value = effect[f_idx]
            abs_key = -abs(value) if np.isfinite(value) else float("inf")
            keys.append((abs_key, feature, f_idx))
        rank_lookup = {f_idx: rank + 1 for rank, (_, _, f_idx) in enumerate(sorted(keys))}

        measured_fraction = mask.mean(axis=0, dtype=np.float64)
        for f_idx, feature in enumerate(features):
            molecular_rows.append({
                "program_id": pid,
                "feature_id": feature,
                "effect": float(effect[f_idx]),
                "ci_low": float(ci_low[f_idx]),
                "ci_high": float(ci_high[f_idx]),
                "fraction_measured": float(measured_fraction[f_idx]),
                "donor_sign_recurrence": float(donor_sign[f_idx]),
                "operator_sign_support": float(operator_sign[f_idx]),
                "effect_rank": int(rank_lookup[f_idx]),
                "input_root_sha256": root,
            })

    molecular_table = pd.DataFrame(molecular_rows)
    redundancy = _redundancy(effect_vectors)

    state_rows: list[dict[str, object]] = []
    direction_shas: list[str] = []
    for j, pid in enumerate(program_ids):
        direction = components[j]
        sha = _direction_sha(direction)
        direction_shas.append(sha)
        order = np.lexsort((np.arange(160), -np.abs(direction)))
        rank_lookup = {int(dim): rank + 1 for rank, dim in enumerate(order)}
        for dim in range(160):
            state_rows.append({
                "program_id": pid,
                "state_dimension": int(dim),
                "loading": float(direction[dim]),
                "absolute_loading_rank": int(rank_lookup[dim]),
                "state_direction_sha256": sha,
                "input_root_sha256": root,
            })
    state_loading_table = pd.DataFrame(state_rows)

    donor_rows: list[dict[str, object]] = []
    source_rows: list[dict[str, object]] = []
    operator_rows: list[dict[str, object]] = []

    for j, pid in enumerate(program_ids):
        percentile = percentiles_by_program[j]
        top = percentile >= 1.0 - TAIL_FRACTION
        bottom = percentile <= TAIL_FRACTION

        for donor in sorted(set(donors)):
            idx = donors == donor
            donor_rows.append({
                "program_id": pid,
                "donor": donor,
                "mean_score": float(scores[idx, j].mean()),
                "median_score": float(np.median(scores[idx, j])),
                "mean_abs_centered_score": float(np.abs(centered_scores[idx, j]).mean()),
                "top_tail_fraction": float(top[idx].mean()),
                "bottom_tail_fraction": float(bottom[idx].mean()),
                "n_cells": int(idx.sum()),
                "input_root_sha256": root,
            })

        for source in sorted(set(sources)):
            idx = sources == source
            source_rows.append({
                "program_id": pid,
                "source": source,
                "mean_score": float(scores[idx, j].mean()),
                "score_sd": float(np.std(scores[idx, j], ddof=1)) if int(idx.sum()) > 1 else float("nan"),
                "n_cells": int(idx.sum()),
                "input_root_sha256": root,
            })

        for operator in sorted(set(operators)):
            idx = operators == operator
            operator_rows.append({
                "program_id": pid,
                "operator": operator,
                "mean_score": float(scores[idx, j].mean()),
                "score_sd": float(np.std(scores[idx, j], ddof=1)) if int(idx.sum()) > 1 else float("nan"),
                "n_cells": int(idx.sum()),
                "input_root_sha256": root,
            })

    donor_table = pd.DataFrame(donor_rows)
    source_table = pd.DataFrame(source_rows)
    operator_table = pd.DataFrame(operator_rows)

    program_rows: list[dict[str, object]] = []
    known_ids: list[str | None] = []
    known_cosines: list[float] = []
    novelty_values: list[float] = []
    priority_values: list[float] = []

    for j, pid in enumerate(program_ids):
        r = _pearson(scores[:, j], measurement_support)
        measurement_r2 = 0.0 if not np.isfinite(r) else float(np.clip(r * r, 0.0, 1.0))
        source_eta = _eta_squared(scores[:, j], sources)
        operator_eta = _eta_squared(scores[:, j], operators)
        known_id, known_cosine, novelty = _known_reference_summary(effect_vectors[j], refs)
        known_ids.append(known_id)
        known_cosines.append(known_cosine)
        novelty_values.append(novelty)
        priority = (
            float(explained[j])
            * float(axis_stability[j])
            * float(donor_recurrence[j])
            * (1.0 - measurement_r2)
            * (1.0 - source_eta)
        )
        priority_values.append(float(priority))
        program_rows.append({
            "program_id": pid,
            "explained_variance_ratio": float(explained[j]),
            "magnitude": float(magnitude[j]),
            "magnitude_ci_low": float(magnitude_lo[j]),
            "magnitude_ci_high": float(magnitude_hi[j]),
            "axis_stability": float(axis_stability[j]),
            "subspace_stability": float(subspace_stability),
            "split_stability": float(split_stability[j]),
            "donor_recurrence": float(donor_recurrence[j]),
            "source_eta_squared": float(source_eta),
            "operator_eta_squared": float(operator_eta),
            "measurement_support_r2": float(measurement_r2),
            "state_direction_sha256": direction_shas[j],
            "known_reference_id": known_id,
            "known_reference_max_abs_cosine": float(known_cosine),
            "novelty_score": float(novelty),
            "redundancy": float(redundancy[j]),
            "representative_cells": representative_cells[j],
            "representative_donors": representative_donors[j],
            "input_root_sha256": root,
        })

    program_table = pd.DataFrame(program_rows)

    hypothesis_rows: list[dict[str, object]] = []
    ranking_order = sorted(
        range(n_components),
        key=lambda j: (-priority_values[j], program_ids[j]),
    )
    for rank, j in enumerate(ranking_order, start=1):
        pid = program_ids[j]
        pos, neg = _top_feature_lists(molecular_table, pid)
        description = (
            "Positive measured features: "
            + (", ".join(pos) if pos else "none")
            + "; negative measured features: "
            + (", ".join(neg) if neg else "none")
        )
        program = program_table.iloc[j]
        hypothesis_rows.append({
            "rank": int(rank),
            "program_id": pid,
            "priority_score": float(priority_values[j]),
            "magnitude": float(program["magnitude"]),
            "magnitude_ci_low": float(program["magnitude_ci_low"]),
            "magnitude_ci_high": float(program["magnitude_ci_high"]),
            "donor_recurrence": float(program["donor_recurrence"]),
            "source_eta_squared": float(program["source_eta_squared"]),
            "axis_stability": float(program["axis_stability"]),
            "measurement_support_r2": float(program["measurement_support_r2"]),
            "operator_eta_squared": float(program["operator_eta_squared"]),
            "known_reference_id": known_ids[j],
            "known_reference_max_abs_cosine": float(known_cosines[j]),
            "biological_description": description,
            "novelty_score": float(novelty_values[j]),
            "top_positive_features": ";".join(pos),
            "top_negative_features": ";".join(neg),
            "representative_cells": representative_cells[j],
            "claim_status": "DISCOVERY_ONLY",
            "input_root_sha256": root,
        })
    hypothesis_catalog = pd.DataFrame(hypothesis_rows)

    diagnostics = {
        "schema": "d1a-estimation-atlas-diagnostics-v2",
        "algorithm_id": ALGORITHM_ID,
        "contract_package_root": CONTRACT_ROOT,
        "mode": mode,
        "input_root_sha256": root,
        "n_cells": int(len(states)),
        "state_width": 160,
        "n_features": int(len(features)),
        "n_components": int(n_components),
        "bootstrap_resamples": BOOTSTRAP_RESAMPLES,
        "bootstrap_seed": BOOTSTRAP_SEED,
        "subspace_stability": subspace_stability,
        "optimizer_steps": 0,
        "ema_updates": 0,
        "claim_status": "DISCOVERY_ONLY",
        "real_d1_authorized": False,
        "confirmatory_terminal": None,
    }

    return D1AAtlasResult(
        program_table=program_table,
        state_loading_table=state_loading_table,
        cell_ranking_table=cell_table,
        molecular_table=molecular_table,
        donor_table=donor_table,
        source_table=source_table,
        operator_table=operator_table,
        hypothesis_catalog=hypothesis_catalog,
        diagnostics=diagnostics,
    )
