"""Offline evaluator for the FULL104 control-calibration cache.

This module consumes only a cache with role
CONTROL_CALIBRATION_ONLY__FORBIDDEN_FOR_TERMINAL_MASKING_QUALIFICATION_V1.
It never opens terminal masking-policy outcomes and cannot authorize training.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, fields
import json
from pathlib import Path
from typing import Any

import numpy as np

from .full104_census_receipt_v2 import sha256_file
from .full104_control_calibration_cache_v1 import (
    CACHE_ROLE_ID,
    Full104ControlCalibrationCacheManifestV1,
    MAX_TARGET_COUNT,
    vector_digest,
)
from .masking_control_executor_v1 import deterministic_within_donor_shuffle

_EPS = 1e-12
PANEL_CAPACITY_SHUFFLE_NAMESPACE = "JEPA_V5_FULL104_PANEL_CAPACITY_CACHE_SHUFFLE_V1"


@dataclass(frozen=True)
class LoadedControlCalibrationCacheV1:
    root: Path
    manifest: Full104ControlCalibrationCacheManifestV1
    manifest_sha256: str
    X: np.ndarray
    selection_rows: np.ndarray
    donor_code: np.ndarray
    row_rank: np.ndarray
    retained_count_by_donor: np.ndarray
    fold_by_donor: np.ndarray
    donor_source_code: np.ndarray
    target_cols: np.ndarray
    proxy_cols: np.ndarray
    distractor_cols: np.ndarray
    cache_cols: np.ndarray
    target_ids: tuple[str, ...]

    def validate(self) -> None:
        self.manifest.assert_calibration_only()
        if self.X.shape != (
            self.manifest.retained_row_count,
            self.manifest.cache_column_count,
        ):
            raise ValueError("cached matrix shape mismatch")
        if self.X.dtype != np.float32:
            raise ValueError("cached matrix must remain float32 calibration storage")
        n = self.manifest.retained_row_count
        for name in ("selection_rows", "donor_code", "row_rank"):
            arr = np.asarray(getattr(self, name))
            if arr.shape != (n,):
                raise ValueError(f"{name} must align with cached rows")
        if self.retained_count_by_donor.shape != (104,):
            raise ValueError("retained_count_by_donor must contain 104 donors")
        if self.fold_by_donor.shape != (104,) or self.donor_source_code.shape != (104,):
            raise ValueError("donor fold/source vectors must contain 104 donors")
        if self.target_cols.shape != (MAX_TARGET_COUNT,):
            raise ValueError("target_cols must contain the full 1024-target envelope")
        if self.proxy_cols.shape != (MAX_TARGET_COUNT,):
            raise ValueError("proxy_cols must align with the 1024 targets")
        if self.distractor_cols.shape != (31,):
            raise ValueError("distractor_cols must contain exactly 31 current distractors")
        if len(self.target_ids) != MAX_TARGET_COUNT or len(set(self.target_ids)) != MAX_TARGET_COUNT:
            raise ValueError("target_ids must be 1024 unique canonical identities")
        if np.unique(self.cache_cols).size != self.cache_cols.size:
            raise ValueError("cache_cols must be unique")
        if not set(map(int, self.target_cols)).issubset(set(map(int, self.cache_cols))):
            raise ValueError("all targets must be represented in cache_cols")
        if not set(map(int, self.proxy_cols)).issubset(set(map(int, self.cache_cols))):
            raise ValueError("all proxies must be represented in cache_cols")
        if not set(map(int, self.distractor_cols)).issubset(set(map(int, self.cache_cols))):
            raise ValueError("all distractors must be represented in cache_cols")
        if np.any(self.donor_code < 0) or np.any(self.donor_code >= 104):
            raise ValueError("cached donor_code is outside current donor registry")
        for donor in range(104):
            ix = np.flatnonzero(self.donor_code == donor)
            if ix.size != int(self.retained_count_by_donor[donor]):
                raise ValueError("retained donor count does not match cached rows")
            ranks = np.sort(self.row_rank[ix])
            if not np.array_equal(ranks, np.arange(ix.size, dtype=np.int64)):
                raise ValueError("row ranks are not contiguous within donor")


def _instantiate_manifest(payload: dict[str, Any]) -> Full104ControlCalibrationCacheManifestV1:
    names = {field.name for field in fields(Full104ControlCalibrationCacheManifestV1)}
    missing = names - set(payload)
    if missing:
        raise ValueError(f"cache manifest is missing fields: {sorted(missing)[:5]}")
    manifest = Full104ControlCalibrationCacheManifestV1(
        **{name: payload[name] for name in names}
    )
    manifest.validate()
    return manifest


def load_control_calibration_cache(root: Path | str) -> LoadedControlCalibrationCacheV1:
    root = Path(root)
    payload = json.loads((root / "cache_manifest.json").read_text(encoding="utf-8"))
    if payload.get("schema") != "V5_FULL104_CONTROL_CALIBRATION_CACHE_MANIFEST_V1":
        raise ValueError("cache manifest schema mismatch")
    manifest = _instantiate_manifest(payload)
    declared = payload.get("cache_manifest_sha256")
    if declared != manifest.canonical_digest():
        raise ValueError("cache manifest canonical digest mismatch")
    if manifest.cache_role_id != CACHE_ROLE_ID:
        raise ValueError("cache role is not approved for calibration")

    names = payload.get("file_names", {})
    required_names = {
        "x", "selection_rows", "donor_code", "row_rank",
        "retained_count_by_donor", "fold_by_donor", "donor_source_code",
        "target_cols", "proxy_cols", "distractor_cols", "cache_cols", "target_ids",
    }
    if set(names) != required_names:
        raise ValueError("cache file-name role set is incomplete or contains unknown roles")

    role_hash = {
        "x": manifest.x_file_sha256,
        "selection_rows": manifest.selection_rows_file_sha256,
        "donor_code": manifest.donor_code_file_sha256,
        "row_rank": manifest.row_rank_file_sha256,
        "retained_count_by_donor": manifest.retained_count_by_donor_file_sha256,
        "fold_by_donor": manifest.fold_by_donor_file_sha256,
        "donor_source_code": manifest.donor_source_code_file_sha256,
        "target_cols": manifest.target_cols_file_sha256,
        "proxy_cols": manifest.proxy_cols_file_sha256,
        "distractor_cols": manifest.distractor_cols_file_sha256,
        "cache_cols": manifest.cache_cols_file_sha256,
        "target_ids": manifest.target_ids_file_sha256,
    }
    for role, filename in names.items():
        path = root / str(filename)
        if not path.is_file():
            raise ValueError(f"cache file is missing for role {role}")
        if sha256_file(path) != role_hash[role]:
            raise ValueError(f"cache file hash mismatch for role {role}")

    X = np.load(root / names["x"], mmap_mode="r", allow_pickle=False)
    arrays = {
        role: np.load(root / names[role], allow_pickle=False)
        for role in (
            "selection_rows", "donor_code", "row_rank", "retained_count_by_donor",
            "fold_by_donor", "donor_source_code", "target_cols", "proxy_cols",
            "distractor_cols", "cache_cols",
        )
    }
    target_ids_raw = json.loads((root / names["target_ids"]).read_text(encoding="utf-8"))
    target_ids = tuple(map(str, target_ids_raw))

    semantic = {
        "target_cols": vector_digest(tuple(map(int, arrays["target_cols"]))),
        "target_ids": vector_digest(target_ids),
        "proxy_cols": vector_digest(tuple(map(int, arrays["proxy_cols"]))),
        "distractor_cols": vector_digest(tuple(map(int, arrays["distractor_cols"]))),
        "cache_cols": vector_digest(tuple(map(int, arrays["cache_cols"]))),
    }
    expected_semantic = {
        "target_cols": manifest.target_cols_semantic_sha256,
        "target_ids": manifest.target_ids_semantic_sha256,
        "proxy_cols": manifest.proxy_cols_semantic_sha256,
        "distractor_cols": manifest.distractor_cols_semantic_sha256,
        "cache_cols": manifest.cache_cols_semantic_sha256,
    }
    if semantic != expected_semantic:
        raise ValueError("cache semantic vector digest mismatch")

    loaded = LoadedControlCalibrationCacheV1(
        root=root,
        manifest=manifest,
        manifest_sha256=str(declared),
        X=X,
        selection_rows=np.asarray(arrays["selection_rows"], dtype=np.int64),
        donor_code=np.asarray(arrays["donor_code"], dtype=np.int64),
        row_rank=np.asarray(arrays["row_rank"], dtype=np.int64),
        retained_count_by_donor=np.asarray(arrays["retained_count_by_donor"], dtype=np.int64),
        fold_by_donor=np.asarray(arrays["fold_by_donor"], dtype=np.int64),
        donor_source_code=np.asarray(arrays["donor_source_code"], dtype=np.int64),
        target_cols=np.asarray(arrays["target_cols"], dtype=np.int64),
        proxy_cols=np.asarray(arrays["proxy_cols"], dtype=np.int64),
        distractor_cols=np.asarray(arrays["distractor_cols"], dtype=np.int64),
        cache_cols=np.asarray(arrays["cache_cols"], dtype=np.int64),
        target_ids=target_ids,
    )
    loaded.validate()
    return loaded


def _fit_cached_ridge(
    X: np.ndarray,
    y: np.ndarray,
    donor_code: np.ndarray,
    train_donors: np.ndarray,
    *,
    alpha: float,
) -> np.ndarray:
    p = int(X.shape[1])
    gram = np.zeros((p, p), dtype=np.float64)
    rhs = np.zeros(p, dtype=np.float64)
    rss_y = 0.0
    n_total = 0
    for raw_donor in train_donors:
        donor = int(raw_donor)
        ix = donor_code == donor
        local_x = np.asarray(X[ix], dtype=np.float64)
        local_y = np.asarray(y[ix], dtype=np.float64)
        if local_y.size == 0:
            raise ValueError(f"cached ridge has no rows for train donor {donor}")
        mean_x = local_x.mean(axis=0)
        sd_x = local_x.std(axis=0, ddof=0)
        sd_x = np.where(sd_x > _EPS, sd_x, 1.0)
        z = (local_x - mean_x) / sd_x
        yc = local_y - local_y.mean()
        gram += z.T @ z
        rhs += z.T @ yc
        rss_y += float(yc @ yc)
        n_total += int(local_y.size)
    if n_total == 0:
        raise ValueError("cached ridge has zero training rows")
    scale = float(np.sqrt(max(rss_y / n_total, 0.0)))
    if scale <= _EPS:
        return np.zeros(p, dtype=np.float64)
    return np.linalg.solve(
        gram + float(alpha) * n_total * np.eye(p, dtype=np.float64),
        rhs / scale,
    )


def _heldout_donor_r2(
    X: np.ndarray,
    y: np.ndarray,
    donor_code: np.ndarray,
    heldout_donors: np.ndarray,
    weights: np.ndarray,
) -> dict[int, float]:
    out: dict[int, float] = {}
    for raw_donor in heldout_donors:
        donor = int(raw_donor)
        ix = donor_code == donor
        local_x = np.asarray(X[ix], dtype=np.float64)
        local_y = np.asarray(y[ix], dtype=np.float64)
        if local_y.size == 0:
            raise ValueError(f"cached score has no rows for heldout donor {donor}")
        mean_x = local_x.mean(axis=0)
        sd_x = local_x.std(axis=0, ddof=0)
        sd_x = np.where(sd_x > _EPS, sd_x, 1.0)
        z = (local_x - mean_x) / sd_x
        yy = local_y - local_y.mean()
        pred = z @ weights
        pred = pred - pred.mean()
        den = float(np.sqrt(max(float(yy @ yy), 0.0) * max(float(pred @ pred), 0.0)))
        r = 0.0 if den <= _EPS else float((yy @ pred) / den)
        out[donor] = r * r
    return out


def _score_one_target(
    cache: LoadedControlCalibrationCacheV1,
    target_index: int,
    *,
    alpha: float,
    global_seed: int,
) -> tuple[int, np.ndarray, np.ndarray]:
    col_to_local = {int(col): i for i, col in enumerate(cache.cache_cols)}
    target_col = int(cache.target_cols[target_index])
    proxy_col = int(cache.proxy_cols[target_index])
    feature_cols = (proxy_col, *map(int, cache.distractor_cols))
    if len(set(feature_cols)) != 32:
        raise ValueError("capacity control must expose exactly 32 distinct features")
    feature_ix = np.asarray([col_to_local[col] for col in feature_cols], dtype=np.int64)
    target_ix = col_to_local[target_col]
    proxy_ix = col_to_local[proxy_col]

    X = np.asarray(cache.X[:, feature_ix], dtype=np.float64)
    planted_y = np.asarray(cache.X[:, proxy_ix], dtype=np.float64)
    raw_target = np.asarray(cache.X[:, target_ix], dtype=np.float64)
    shuffled_y = deterministic_within_donor_shuffle(
        raw_target,
        cache.donor_code,
        target_id=cache.target_ids[target_index],
        global_seed=int(global_seed),
    )

    planted_scores = np.full(104, np.nan, dtype=np.float64)
    shuffled_scores = np.full(104, np.nan, dtype=np.float64)
    for fold in sorted(set(map(int, cache.fold_by_donor))):
        heldout = np.flatnonzero(cache.fold_by_donor == fold).astype(np.int64)
        train = np.flatnonzero(cache.fold_by_donor != fold).astype(np.int64)
        pw = _fit_cached_ridge(X, planted_y, cache.donor_code, train, alpha=alpha)
        sw = _fit_cached_ridge(X, shuffled_y, cache.donor_code, train, alpha=alpha)
        for donor, score in _heldout_donor_r2(
            X, planted_y, cache.donor_code, heldout, pw
        ).items():
            planted_scores[donor] = score
        for donor, score in _heldout_donor_r2(
            X, shuffled_y, cache.donor_code, heldout, sw
        ).items():
            shuffled_scores[donor] = score

    if not np.all(np.isfinite(planted_scores)) or not np.all(np.isfinite(shuffled_scores)):
        raise ValueError("capacity scoring did not cover every donor")
    return target_index, planted_scores, shuffled_scores


def evaluate_linear_capacity_rung(
    cache: LoadedControlCalibrationCacheV1,
    *,
    target_count: int,
    ridge_alpha: float,
    global_seed: int,
    workers: int,
) -> tuple[np.ndarray, np.ndarray]:
    cache.validate()
    if target_count not in (128, 256, 512, 1024):
        raise ValueError("target_count must be a frozen panel-capacity rung")
    if isinstance(workers, bool) or not isinstance(workers, int) or workers < 1:
        raise ValueError("workers must be a positive integer")
    if not np.isfinite(float(ridge_alpha)) or float(ridge_alpha) <= 0:
        raise ValueError("ridge_alpha must be finite and positive")
    planted = np.full((target_count, 104), np.nan, dtype=np.float64)
    shuffled = np.full((target_count, 104), np.nan, dtype=np.float64)

    def task(index: int):
        return _score_one_target(
            cache,
            index,
            alpha=float(ridge_alpha),
            global_seed=int(global_seed),
        )

    if workers == 1:
        results = map(task, range(target_count))
        for index, p, s in results:
            planted[index] = p
            shuffled[index] = s
    else:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            for index, p, s in pool.map(task, range(target_count)):
                planted[index] = p
                shuffled[index] = s

    if not np.all(np.isfinite(planted)) or not np.all(np.isfinite(shuffled)):
        raise ValueError("capacity matrices contain non-finite values")
    return planted, shuffled
