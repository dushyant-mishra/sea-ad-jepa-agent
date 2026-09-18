"""Calibration-only cache contract for current FULL104 masking qualification.

This module deliberately creates a *non-terminal* acceleration substrate.  The
cache may be used only to calibrate design capacity (target-panel size and the
secondary nonlinear row cap).  It is forbidden as input to terminal FULL104
masking qualification or training.

All identities are derived from current FULL104 authorities.  No historical
target list, Stage81 cache, T1 checkpoint, EMA setting, or discovery matrix is
accepted here.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import heapq
import json
from typing import Any, Mapping, Sequence

import numpy as np

from .masking_control_executor_v1 import select_planted_proxy

CACHE_ROLE_ID = "CONTROL_CALIBRATION_ONLY__FORBIDDEN_FOR_TERMINAL_MASKING_QUALIFICATION_V1"
SOURCE_SUBSTRATE_ROLE_ID = "AUTHENTICATED_FULL104_LEVEL4_RAW_COUNTS_V1"
NORMALIZATION_ID = "EXACT_LOG1P_10000_FROM_RAW_COUNTS_ONCE_V1"
ROW_SELECTION_NAMESPACE = "JEPA_V5_FULL104_CONTROL_CACHE_ROW_PRIORITY_V1"
DISTRACTOR_NAMESPACE = "JEPA_V5_FULL104_CONTROL_CACHE_DISTRACTOR_V1"
MAX_ROWS_PER_DONOR = 1024
MAX_TARGET_COUNT = 1024
DISTRACTOR_COUNT = 31
EXPECTED_DONOR_COUNT = 104
X_DTYPE_ID = "FLOAT32_CALIBRATION_CACHE_NOT_TERMINAL_PRECISION_V1"


def _sha(value: object, name: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or value != value.lower():
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{name} must be a lowercase SHA-256 digest") from exc
    return value


def canonical_sha(payload: Mapping[str, Any]) -> str:
    raw = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def vector_digest(values: Sequence[Any]) -> str:
    return canonical_sha({"values": list(values)})


def row_priority(*, full104_manifest_sha256: str, donor_code: int, selection_row: int) -> int:
    _sha(full104_manifest_sha256, "full104_manifest_sha256")
    if isinstance(donor_code, bool) or not isinstance(donor_code, (int, np.integer)) or int(donor_code) < 0:
        raise ValueError("donor_code must be a nonnegative integer")
    if isinstance(selection_row, bool) or not isinstance(selection_row, (int, np.integer)) or int(selection_row) < 0:
        raise ValueError("selection_row must be a nonnegative integer")
    raw = (
        f"{ROW_SELECTION_NAMESPACE}|{full104_manifest_sha256}|"
        f"{int(donor_code)}|{int(selection_row)}"
    ).encode("utf-8")
    return int.from_bytes(hashlib.sha256(raw).digest()[:8], "big", signed=False)


class RetainedRowSelectorV1:
    """Streaming bottom-k row selector, independently within each donor."""

    def __init__(
        self,
        *,
        full104_manifest_sha256: str,
        donor_count: int = EXPECTED_DONOR_COUNT,
        max_rows_per_donor: int = MAX_ROWS_PER_DONOR,
    ) -> None:
        self.full104_manifest_sha256 = _sha(
            full104_manifest_sha256, "full104_manifest_sha256"
        )
        if donor_count != EXPECTED_DONOR_COUNT:
            raise ValueError("donor_count must equal current FULL104 value 104")
        if max_rows_per_donor != MAX_ROWS_PER_DONOR:
            raise ValueError("max_rows_per_donor must remain the frozen calibration envelope 1024")
        self.donor_count = donor_count
        self.max_rows_per_donor = max_rows_per_donor
        self._heaps: list[list[tuple[int, int]]] = [[] for _ in range(donor_count)]
        self._observed_counts = np.zeros(donor_count, dtype=np.int64)

    def update(self, selection_rows: np.ndarray, donor_code: np.ndarray) -> None:
        rows = np.asarray(selection_rows)
        donors = np.asarray(donor_code)
        if (
            rows.ndim != 1
            or donors.ndim != 1
            or rows.size != donors.size
            or not np.issubdtype(rows.dtype, np.integer)
            or not np.issubdtype(donors.dtype, np.integer)
        ):
            raise ValueError("selection_rows and donor_code must be aligned integer vectors")
        if rows.size == 0:
            return
        if np.any(rows < 0):
            raise ValueError("selection_rows cannot be negative")
        if np.any(donors < 0) or np.any(donors >= self.donor_count):
            raise ValueError("donor_code is outside the current FULL104 donor registry")
        for raw_row, raw_donor in zip(rows, donors):
            row = int(raw_row)
            donor = int(raw_donor)
            self._observed_counts[donor] += 1
            priority = row_priority(
                full104_manifest_sha256=self.full104_manifest_sha256,
                donor_code=donor,
                selection_row=row,
            )
            item = (-priority, -row)
            heap = self._heaps[donor]
            if len(heap) < self.max_rows_per_donor:
                heapq.heappush(heap, item)
            elif item > heap[0]:
                heapq.heapreplace(heap, item)

    def finalize(self) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        if np.any(self._observed_counts <= 0):
            raise ValueError("row selector did not observe all 104 authorized donors")
        rows: list[int] = []
        donors: list[int] = []
        ranks: list[int] = []
        retained_counts = np.zeros(self.donor_count, dtype=np.int64)
        for donor, heap in enumerate(self._heaps):
            selected = sorted(
                [(-neg_priority, -neg_row) for neg_priority, neg_row in heap],
                key=lambda pair: (pair[0], pair[1]),
            )
            retained_counts[donor] = len(selected)
            expected = min(int(self._observed_counts[donor]), self.max_rows_per_donor)
            if len(selected) != expected:
                raise ValueError("retained row count does not match min(cap, donor cells)")
            for rank, (_, row) in enumerate(selected):
                rows.append(int(row))
                donors.append(donor)
                ranks.append(rank)
        out_rows = np.asarray(rows, dtype=np.int64)
        if np.unique(out_rows).size != out_rows.size:
            raise ValueError("retained selection rows are not globally unique")
        return (
            out_rows,
            np.asarray(donors, dtype=np.int64),
            np.asarray(ranks, dtype=np.int64),
            retained_counts,
        )


def select_calibration_columns(
    *,
    eligible_cols: Sequence[int],
    target_cols: Sequence[int],
    target_ids: Sequence[object],
    target_eligibility_receipt_sha256: str,
) -> dict[str, tuple[int, ...]]:
    """Choose target proxies and fixed distractors without reading expression values."""

    _sha(target_eligibility_receipt_sha256, "target_eligibility_receipt_sha256")
    eligible = np.asarray(list(eligible_cols))
    targets = np.asarray(list(target_cols))
    ids = list(target_ids)
    if (
        eligible.ndim != 1
        or targets.ndim != 1
        or not np.issubdtype(eligible.dtype, np.integer)
        or not np.issubdtype(targets.dtype, np.integer)
    ):
        raise ValueError("eligible_cols and target_cols must be integer vectors")
    eligible = eligible.astype(np.int64, copy=False)
    targets = targets.astype(np.int64, copy=False)
    if targets.size != MAX_TARGET_COUNT:
        raise ValueError("calibration cache must bind the full nested 1024-target envelope")
    if len(ids) != targets.size or len(set(map(str, ids))) != len(ids):
        raise ValueError("target_ids must be unique and align one-to-one with target_cols")
    if np.unique(eligible).size != eligible.size or np.unique(targets).size != targets.size:
        raise ValueError("eligible_cols and target_cols must be unique")
    eligible_set = set(map(int, eligible))
    if not set(map(int, targets)).issubset(eligible_set):
        raise ValueError("every calibration target must belong to current target eligibility")

    proxies = tuple(
        int(
            select_planted_proxy(
                eligible_cols=eligible,
                target_col=int(target),
                target_id=target_id,
            )
        )
        for target, target_id in zip(targets, ids)
    )
    for target, proxy in zip(targets, proxies):
        if int(target) == int(proxy):
            raise ValueError("planted proxy cannot equal its own target")

    excluded = set(map(int, targets)) | set(proxies)
    candidates = [int(col) for col in eligible if int(col) not in excluded]
    if len(candidates) < DISTRACTOR_COUNT:
        raise ValueError("not enough current eligible addresses for calibration distractors")
    distractors = tuple(
        sorted(
            candidates,
            key=lambda col: (
                hashlib.sha256(
                    (
                        f"{DISTRACTOR_NAMESPACE}|{target_eligibility_receipt_sha256}|{col}"
                    ).encode("utf-8")
                ).digest(),
                col,
            ),
        )[:DISTRACTOR_COUNT]
    )
    if len(set(distractors)) != DISTRACTOR_COUNT:
        raise ValueError("calibration distractors must be unique")
    if set(distractors) & excluded:
        raise ValueError("calibration distractors must be disjoint from targets and proxies")

    cache_cols = tuple(sorted(set(map(int, targets)) | set(proxies) | set(distractors)))
    return {
        "target_cols": tuple(map(int, targets)),
        "proxy_cols": proxies,
        "distractor_cols": distractors,
        "cache_cols": cache_cols,
    }


@dataclass(frozen=True)
class Full104ControlCalibrationCacheManifestV1:
    authority_id: str
    cache_role_id: str
    source_substrate_role_id: str
    normalization_id: str
    x_dtype_id: str

    full104_block_manifest_sha256: str
    canonical_registry_sha256: str
    census_authority_sha256: str
    support_estimability_authority_sha256: str
    split_receipt_sha256: str
    target_eligibility_receipt_sha256: str

    row_selection_namespace: str
    distractor_namespace: str
    max_rows_per_donor: int
    max_target_count: int
    distractor_count: int

    retained_row_count: int
    retained_donor_count: int
    min_retained_rows_per_donor: int
    max_retained_rows_observed_per_donor: int
    cache_column_count: int
    x_shape_rows: int
    x_shape_cols: int

    target_cols_semantic_sha256: str
    target_ids_semantic_sha256: str
    proxy_cols_semantic_sha256: str
    distractor_cols_semantic_sha256: str
    cache_cols_semantic_sha256: str

    x_file_sha256: str
    selection_rows_file_sha256: str
    donor_code_file_sha256: str
    row_rank_file_sha256: str
    retained_count_by_donor_file_sha256: str
    fold_by_donor_file_sha256: str
    donor_source_code_file_sha256: str
    full_donor_n_file_sha256: str
    full_donor_sum_file_sha256: str
    full_donor_sumsq_file_sha256: str
    target_cols_file_sha256: str
    proxy_cols_file_sha256: str
    distractor_cols_file_sha256: str
    cache_cols_file_sha256: str
    target_ids_file_sha256: str

    terminal_masking_qualification_authorized: bool = False
    protected_outcomes_authorized: bool = False
    training_authorized: bool = False

    def validate(self) -> None:
        if not isinstance(self.authority_id, str) or not self.authority_id.strip():
            raise ValueError("authority_id must be nonempty")
        if self.cache_role_id != CACHE_ROLE_ID:
            raise ValueError("cache_role_id mismatch")
        if self.source_substrate_role_id != SOURCE_SUBSTRATE_ROLE_ID:
            raise ValueError("source_substrate_role_id mismatch")
        if self.normalization_id != NORMALIZATION_ID:
            raise ValueError("normalization_id mismatch")
        if self.x_dtype_id != X_DTYPE_ID:
            raise ValueError("x_dtype_id mismatch")

        roots = (
            _sha(self.full104_block_manifest_sha256, "full104_block_manifest_sha256"),
            _sha(self.canonical_registry_sha256, "canonical_registry_sha256"),
            _sha(self.census_authority_sha256, "census_authority_sha256"),
            _sha(self.support_estimability_authority_sha256, "support_estimability_authority_sha256"),
            _sha(self.split_receipt_sha256, "split_receipt_sha256"),
            _sha(self.target_eligibility_receipt_sha256, "target_eligibility_receipt_sha256"),
        )
        if len(set(roots)) != len(roots):
            raise ValueError("calibration-cache authority roots must be role-distinct")

        if self.row_selection_namespace != ROW_SELECTION_NAMESPACE:
            raise ValueError("row_selection_namespace mismatch")
        if self.distractor_namespace != DISTRACTOR_NAMESPACE:
            raise ValueError("distractor_namespace mismatch")
        if self.max_rows_per_donor != MAX_ROWS_PER_DONOR:
            raise ValueError("max_rows_per_donor must remain 1024")
        if self.max_target_count != MAX_TARGET_COUNT:
            raise ValueError("max_target_count must remain 1024")
        if self.distractor_count != DISTRACTOR_COUNT:
            raise ValueError("distractor_count must remain 31")
        if self.retained_donor_count != EXPECTED_DONOR_COUNT:
            raise ValueError("retained_donor_count must remain 104")
        if self.retained_row_count < EXPECTED_DONOR_COUNT:
            raise ValueError("retained_row_count is too small to cover all donors")
        if not (1 <= self.min_retained_rows_per_donor <= MAX_ROWS_PER_DONOR):
            raise ValueError("minimum retained donor rows are invalid")
        if not (self.min_retained_rows_per_donor <= self.max_retained_rows_observed_per_donor <= MAX_ROWS_PER_DONOR):
            raise ValueError("maximum retained donor rows are invalid")
        if self.cache_column_count < MAX_TARGET_COUNT + DISTRACTOR_COUNT:
            raise ValueError("cache_column_count is unexpectedly small")
        if (self.x_shape_rows, self.x_shape_cols) != (
            self.retained_row_count,
            self.cache_column_count,
        ):
            raise ValueError("cached matrix shape does not match manifest counts")

        semantic_roots = (
            self.target_cols_semantic_sha256,
            self.target_ids_semantic_sha256,
            self.proxy_cols_semantic_sha256,
            self.distractor_cols_semantic_sha256,
            self.cache_cols_semantic_sha256,
        )
        file_roots = (
            self.x_file_sha256,
            self.selection_rows_file_sha256,
            self.donor_code_file_sha256,
            self.row_rank_file_sha256,
            self.retained_count_by_donor_file_sha256,
            self.fold_by_donor_file_sha256,
            self.donor_source_code_file_sha256,
            self.full_donor_n_file_sha256,
            self.full_donor_sum_file_sha256,
            self.full_donor_sumsq_file_sha256,
            self.target_cols_file_sha256,
            self.proxy_cols_file_sha256,
            self.distractor_cols_file_sha256,
            self.cache_cols_file_sha256,
            self.target_ids_file_sha256,
        )
        for i, digest in enumerate((*semantic_roots, *file_roots)):
            _sha(digest, f"cache_digest_{i}")

        if self.terminal_masking_qualification_authorized is not False:
            raise ValueError("calibration cache is forbidden for terminal masking qualification")
        if self.protected_outcomes_authorized is not False:
            raise ValueError("calibration cache cannot authorize protected outcomes")
        if self.training_authorized is not False:
            raise ValueError("calibration cache cannot authorize training")

    def canonical_digest(self) -> str:
        self.validate()
        return canonical_sha(
            {"schema": "V5_FULL104_CONTROL_CALIBRATION_CACHE_MANIFEST_V1", **asdict(self)}
        )

    def assert_calibration_only(self) -> None:
        self.validate()
        if self.cache_role_id != CACHE_ROLE_ID:
            raise ValueError("cache is not calibration-only")
