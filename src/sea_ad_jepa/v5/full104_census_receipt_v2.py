"""Reproducible FULL104 census receipts from the authenticated sparsity census.

This module contains only outcome-blind support and precision accounting helpers.
It never reads masking-policy outcomes and cannot authorize training.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

import numpy as np


FULL104_N_CELLS = 4_553_407
FULL104_N_DONORS = 104
FULL104_CORE_SIZE = 17_186
FULL104_CORE_ZERO_COUNT = 65_184_935_567
FULL104_CORE_NONZERO_COUNT = 13_069_917_135
FULL104_CORE_SLOT_COUNT = FULL104_N_CELLS * FULL104_CORE_SIZE
FULL104_CORE_ZERO_FREQUENCY = FULL104_CORE_ZERO_COUNT / FULL104_CORE_SLOT_COUNT
SOURCE_NAMES = ("HVS", "NPH52", "SEA_AD")
SPLIT_NAMESPACE = "JEPA_FULL104_CENSUS_FOLD"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 22), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_sha(payload: Mapping[str, Any]) -> str:
    raw = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def core_zero_crosscheck(
    cell_nnz_core: np.ndarray,
    donor_addr_nnz: np.ndarray,
    core: np.ndarray,
) -> dict[str, int | float]:
    """Cross-check core nonzeros by two independently accumulated pass-1 views."""

    per_cell = np.asarray(cell_nnz_core)
    donor_address = np.asarray(donor_addr_nnz)
    core_cols = np.asarray(core)
    if per_cell.ndim != 1 or per_cell.size == 0:
        raise ValueError("cell_nnz_core must be a nonempty vector")
    if donor_address.ndim != 2 or donor_address.shape[0] == 0:
        raise ValueError("donor_addr_nnz must be a nonempty matrix")
    if core_cols.ndim != 1 or core_cols.size == 0:
        raise ValueError("core must be a nonempty vector")
    if not np.issubdtype(core_cols.dtype, np.integer):
        raise ValueError("core must contain integer columns")
    if core_cols.min() < 0 or core_cols.max() >= donor_address.shape[1]:
        raise ValueError("core contains an out-of-range address")

    by_cell = int(np.asarray(per_cell, dtype=np.int64).sum(dtype=np.int64))
    selected = donor_address[:, core_cols.astype(np.int64, copy=False)]
    by_donor_address = int(np.asarray(selected, dtype=np.int64).sum(dtype=np.int64))
    if by_cell != by_donor_address:
        raise ValueError(
            "independent core-nonzero accumulations disagree: "
            f"per_cell={by_cell} donor_address={by_donor_address}"
        )
    total_slots = int(per_cell.size) * int(core_cols.size)
    zero_count = total_slots - by_cell
    if zero_count < 0:
        raise ValueError("core nonzero count exceeds total core slots")
    return {
        "total_core_slots": total_slots,
        "core_nonzero_sum_per_cell": by_cell,
        "core_nonzero_sum_donor_address": by_donor_address,
        "core_measured_zero_count": zero_count,
        "core_measured_zero_frequency": zero_count / total_slots,
    }


def source_stratified_fold_assignment(
    donor_source_code: np.ndarray,
    *,
    n_folds: int = 4,
    source_names: tuple[str, ...] = SOURCE_NAMES,
    namespace: str = SPLIT_NAMESPACE,
) -> np.ndarray:
    """Reproduce the outcome-blind source-stratified donor split from the census."""

    source = np.asarray(donor_source_code)
    if source.ndim != 1 or source.size == 0:
        raise ValueError("donor_source_code must be a nonempty vector")
    if not np.issubdtype(source.dtype, np.integer):
        raise ValueError("donor_source_code must be integer")
    if isinstance(n_folds, bool) or not isinstance(n_folds, int) or n_folds < 2:
        raise ValueError("n_folds must be an integer >= 2")
    if source.min() < 0 or source.max() >= len(source_names):
        raise ValueError("donor source code is outside source_names")

    folds = np.full(source.size, -1, dtype=np.int64)
    for source_code, source_name in enumerate(source_names):
        donors = np.flatnonzero(source == source_code)
        if donors.size < n_folds:
            raise ValueError(f"source {source_name} has fewer donors than folds")
        seed = int.from_bytes(
            hashlib.sha256(f"{namespace}|{source_name}".encode("utf-8")).digest()[:8],
            "big",
        )
        perm = np.random.default_rng(seed).permutation(donors)
        for index, donor in enumerate(perm):
            folds[int(donor)] = index % n_folds
    if np.any(folds < 0):
        raise ValueError("one or more donors were not assigned to a fold")
    return folds


def eligible_targets_all_folds(
    donor_addr_nnz: np.ndarray,
    core: np.ndarray,
    fold_by_donor: np.ndarray,
    *,
    min_nonzero_cells_per_donor: int = 30,
    min_train_donors: int = 20,
    min_validation_donors: int = 5,
) -> tuple[np.ndarray, tuple[int, ...]]:
    """Return strict-core target columns estimable in every outer donor fold."""

    counts = np.asarray(donor_addr_nnz)
    core_cols = np.asarray(core)
    folds = np.asarray(fold_by_donor)
    if counts.ndim != 2 or folds.ndim != 1 or counts.shape[0] != folds.size:
        raise ValueError("donor counts and fold assignment must align")
    if core_cols.ndim != 1 or not np.issubdtype(core_cols.dtype, np.integer):
        raise ValueError("core must be a one-dimensional integer vector")
    if core_cols.min() < 0 or core_cols.max() >= counts.shape[1]:
        raise ValueError("core contains an out-of-range address")
    support = counts[:, core_cols.astype(np.int64, copy=False)] >= int(
        min_nonzero_cells_per_donor
    )
    all_ok = np.ones(core_cols.size, dtype=bool)
    per_fold: list[int] = []
    for fold in sorted(set(map(int, folds))):
        train = folds != fold
        validation = folds == fold
        ok = (
            (support[train].sum(axis=0) >= int(min_train_donors))
            & (support[validation].sum(axis=0) >= int(min_validation_donors))
        )
        all_ok &= ok
        per_fold.append(int(ok.sum()))
    return core_cols[all_ok].astype(np.int64, copy=False), tuple(per_fold)


def kish_ess(counts: np.ndarray) -> float:
    weights = np.asarray(counts, dtype=np.float64).reshape(-1)
    if weights.size == 0 or np.any(weights < 0) or float(weights.sum()) <= 0:
        raise ValueError("counts must be nonnegative with positive total")
    return float(weights.sum() ** 2 / np.dot(weights, weights))


def validate_full104_crosscheck(report: Mapping[str, Any]) -> None:
    """Fail closed unless corrected FULL104 zero accounting is reproduced."""

    expected = {
        "total_core_slots": FULL104_CORE_SLOT_COUNT,
        "core_nonzero_sum_per_cell": FULL104_CORE_NONZERO_COUNT,
        "core_nonzero_sum_donor_address": FULL104_CORE_NONZERO_COUNT,
        "core_measured_zero_count": FULL104_CORE_ZERO_COUNT,
    }
    for key, value in expected.items():
        if int(report.get(key, -1)) != int(value):
            raise ValueError(f"{key} mismatch: {report.get(key)!r} != {value}")
    observed = float(report.get("core_measured_zero_frequency", float("nan")))
    if not np.isfinite(observed) or abs(observed - FULL104_CORE_ZERO_FREQUENCY) > 1e-15:
        raise ValueError(
            "core_measured_zero_frequency does not reproduce corrected int64 total"
        )
