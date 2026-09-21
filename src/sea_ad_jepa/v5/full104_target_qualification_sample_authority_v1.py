"""Expression-blind FULL104 target-qualification sample authority V1.

Purpose
-------
Make FULL104 learned-teacher / rare-tail qualification computationally tractable
without letting SEA_AD's ~90% cell mass dominate the evaluation.

Sampling law
------------
- scientific unit remains donor-uniform;
- retain all cells when a donor has <=1024 cells;
- otherwise retain exactly 1024 cells with the smallest deterministic
  stable-identity hashes;
- selection may use donor code + authenticated global selection_row + frozen namespace only;
- expression values, library size, nnz, class, operator, region, pathology and
  outcomes are forbidden selection inputs.

The current FULL104 geometry implies 103 donors at cap and one 81-cell donor,
for exactly 105,553 qualification cells.

This is a NEW role-specific sample authority. It does not reuse or repurpose the
control-calibration cache and cannot authorize masking or training.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import heapq
import json
from typing import Any, Mapping

import numpy as np


FULL104_READER_FIT_CELLS = 4_553_407
FULL104_READER_FIT_DONORS = 104
PER_DONOR_CAP = 1024
EXPECTED_DONORS_AT_CAP = 103
EXPECTED_SHORT_DONOR_CELLS = 81
EXPECTED_SAMPLE_CELLS = EXPECTED_DONORS_AT_CAP * PER_DONOR_CAP + EXPECTED_SHORT_DONOR_CELLS

SAMPLE_ROLE_ID = (
    "FULL104_TARGET_QUALIFICATION_ONLY__NOT_MASKING__NOT_TRAINING_V1"
)
SELECTION_NAMESPACE_ID = "V5_FULL104_TARGET_QUALIFICATION_STABLE_ID_HASH_V1"
WEIGHTING_ID = "DONOR_UNIFORM__CELL_UNIFORM_WITHIN_DONOR_V1"


def _sha(value: object, name: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or value != value.lower():
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{name} must be a lowercase SHA-256 digest") from exc
    return value


def _canonical_sha(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


@dataclass(frozen=True)
class Full104TargetQualificationSampleAuthorityV1:
    authority_id: str
    population_authority_sha256: str
    full104_block_manifest_sha256: str
    dataset_etl_atlas_sha256: str
    outer_split_receipt_sha256: str

    sample_role_id: str = SAMPLE_ROLE_ID
    selection_namespace_id: str = SELECTION_NAMESPACE_ID
    weighting_id: str = WEIGHTING_ID

    reader_fit_cells: int = FULL104_READER_FIT_CELLS
    reader_fit_donors: int = FULL104_READER_FIT_DONORS
    per_donor_cap: int = PER_DONOR_CAP
    expected_donors_at_cap: int = EXPECTED_DONORS_AT_CAP
    expected_short_donor_cells: int = EXPECTED_SHORT_DONOR_CELLS
    expected_sample_cells: int = EXPECTED_SAMPLE_CELLS

    expression_used_for_selection: bool = False
    library_size_used_for_selection: bool = False
    nnz_used_for_selection: bool = False
    operator_used_for_selection: bool = False
    region_used_for_selection: bool = False
    class_used_for_selection: bool = False
    pathology_used_for_selection: bool = False

    masking_authorized: bool = False
    training_authorized: bool = False

    def validate(self) -> None:
        if not isinstance(self.authority_id, str) or not self.authority_id.strip():
            raise ValueError("authority_id must be nonempty")
        for name in (
            "population_authority_sha256",
            "full104_block_manifest_sha256",
            "dataset_etl_atlas_sha256",
            "outer_split_receipt_sha256",
        ):
            _sha(getattr(self, name), name)

        if self.sample_role_id != SAMPLE_ROLE_ID:
            raise ValueError("sample_role_id mismatch")
        if self.selection_namespace_id != SELECTION_NAMESPACE_ID:
            raise ValueError("selection_namespace_id mismatch")
        if self.weighting_id != WEIGHTING_ID:
            raise ValueError("weighting_id mismatch")

        expected = {
            "reader_fit_cells": FULL104_READER_FIT_CELLS,
            "reader_fit_donors": FULL104_READER_FIT_DONORS,
            "per_donor_cap": PER_DONOR_CAP,
            "expected_donors_at_cap": EXPECTED_DONORS_AT_CAP,
            "expected_short_donor_cells": EXPECTED_SHORT_DONOR_CELLS,
            "expected_sample_cells": EXPECTED_SAMPLE_CELLS,
        }
        for name, value in expected.items():
            if getattr(self, name) != value:
                raise ValueError(f"{name} drifted from frozen qualification-sample geometry")

        for name in (
            "expression_used_for_selection",
            "library_size_used_for_selection",
            "nnz_used_for_selection",
            "operator_used_for_selection",
            "region_used_for_selection",
            "class_used_for_selection",
            "pathology_used_for_selection",
            "masking_authorized",
            "training_authorized",
        ):
            if getattr(self, name) is not False:
                raise ValueError(f"{name} must remain false")

    def canonical_digest(self) -> str:
        self.validate()
        return _canonical_sha(
            {
                "schema": "V5_FULL104_TARGET_QUALIFICATION_SAMPLE_AUTHORITY_V1",
                **asdict(self),
                "masking_authorized": False,
                "training_authorized": False,
            }
        )

    def selection_priority(self, *, donor_code: int, selection_row: int) -> int:
        """Deterministic identity-only within-donor ordering key."""
        self.validate()
        return _selection_priority_unchecked(
            self,
            donor_code=donor_code,
            selection_row=selection_row,
        )


def _selection_priority_unchecked(
    authority: Full104TargetQualificationSampleAuthorityV1,
    *,
    donor_code: int,
    selection_row: int,
) -> int:
    """Hot-path priority after the authority itself has already been validated."""
    if isinstance(donor_code, bool) or not isinstance(donor_code, int) or donor_code < 0:
        raise ValueError("donor_code must be a nonnegative integer")
    if (
        isinstance(selection_row, bool)
        or not isinstance(selection_row, int)
        or selection_row < 0
        or selection_row >= FULL104_READER_FIT_CELLS
    ):
        raise ValueError("selection_row must be a valid global FULL104 row")
    payload = (
        f"{authority.selection_namespace_id}|"
        f"{authority.population_authority_sha256}|"
        f"donor|{donor_code}|selection_row|{selection_row}"
    ).encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest(), "big", signed=False)


class RetainedQualificationRowSelectorV1:
    """Streaming bottom-k selector for the target-qualification sample."""

    def __init__(self, authority: Full104TargetQualificationSampleAuthorityV1) -> None:
        authority.validate()
        self.authority = authority
        self._heaps: list[list[tuple[int, int]]] = [
            [] for _ in range(authority.reader_fit_donors)
        ]
        self._observed = np.zeros(authority.reader_fit_donors, dtype=np.int64)

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
        if np.any(rows < 0) or np.any(rows >= self.authority.reader_fit_cells):
            raise ValueError("selection_rows contain invalid global FULL104 rows")
        if np.any(donors < 0) or np.any(donors >= self.authority.reader_fit_donors):
            raise ValueError("donor_code is outside the current FULL104 donor registry")

        for raw_row, raw_donor in zip(rows, donors):
            row = int(raw_row)
            donor = int(raw_donor)
            self._observed[donor] += 1
            priority = _selection_priority_unchecked(
                self.authority,
                donor_code=donor,
                selection_row=row,
            )
            # max-priority item sits at heap[0] through negation; replace it when
            # a lower-priority row arrives.
            item = (-priority, -row)
            heap = self._heaps[donor]
            if len(heap) < self.authority.per_donor_cap:
                heapq.heappush(heap, item)
            elif item > heap[0]:
                heapq.heapreplace(heap, item)

    def finalize(self) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        if np.any(self._observed <= 0):
            raise ValueError("qualification selector did not observe all 104 donors")

        rows: list[int] = []
        donors: list[int] = []
        ranks: list[int] = []
        retained = np.zeros(self.authority.reader_fit_donors, dtype=np.int64)

        for donor, heap in enumerate(self._heaps):
            selected = sorted(
                [(-neg_priority, -neg_row) for neg_priority, neg_row in heap],
                key=lambda pair: (pair[0], pair[1]),
            )
            expected = min(int(self._observed[donor]), self.authority.per_donor_cap)
            if len(selected) != expected:
                raise ValueError("retained donor rows do not equal min(cap, donor cells)")
            retained[donor] = len(selected)
            for rank, (_, row) in enumerate(selected):
                rows.append(row)
                donors.append(donor)
                ranks.append(rank)

        out_rows = np.asarray(rows, dtype=np.int64)
        out_donors = np.asarray(donors, dtype=np.int64)
        out_ranks = np.asarray(ranks, dtype=np.int64)
        if np.unique(out_rows).size != out_rows.size:
            raise ValueError("retained qualification rows are not globally unique")
        if out_rows.size != self.authority.expected_sample_cells:
            raise ValueError(
                f"qualification sample row count {out_rows.size} != "
                f"expected {self.authority.expected_sample_cells}"
            )
        if int(np.sum(retained == self.authority.per_donor_cap)) != (
            self.authority.expected_donors_at_cap
        ):
            raise ValueError("donors-at-cap geometry does not match authenticated FULL104")
        short = retained[retained < self.authority.per_donor_cap]
        if short.tolist() != [self.authority.expected_short_donor_cells]:
            raise ValueError("short-donor geometry does not match authenticated FULL104")
        return out_rows, out_donors, out_ranks, retained


@dataclass(frozen=True)
class Full104TargetQualificationSampleReceiptV1:
    sample_authority_sha256: str
    full104_block_manifest_sha256: str
    population_authority_sha256: str
    dataset_etl_atlas_sha256: str
    outer_split_receipt_sha256: str

    retained_cells: int
    retained_donors: int
    donors_at_cap: int
    min_retained_per_donor: int
    max_retained_per_donor: int

    selection_rows_file_sha256: str
    donor_code_file_sha256: str
    row_rank_file_sha256: str
    retained_count_by_donor_file_sha256: str
    full_donor_n_file_sha256: str
    fold_by_donor_file_sha256: str
    donor_source_code_file_sha256: str
    builder_source_sha256: str

    expression_opened_by_builder: bool = False
    masking_authorized: bool = False
    training_authorized: bool = False

    def validate(self) -> None:
        for name in (
            "sample_authority_sha256",
            "full104_block_manifest_sha256",
            "population_authority_sha256",
            "dataset_etl_atlas_sha256",
            "outer_split_receipt_sha256",
            "selection_rows_file_sha256",
            "donor_code_file_sha256",
            "row_rank_file_sha256",
            "retained_count_by_donor_file_sha256",
            "full_donor_n_file_sha256",
            "fold_by_donor_file_sha256",
            "donor_source_code_file_sha256",
            "builder_source_sha256",
        ):
            _sha(getattr(self, name), name)

        if self.retained_cells != EXPECTED_SAMPLE_CELLS:
            raise ValueError("retained_cells mismatch")
        if self.retained_donors != FULL104_READER_FIT_DONORS:
            raise ValueError("retained_donors mismatch")
        if self.donors_at_cap != EXPECTED_DONORS_AT_CAP:
            raise ValueError("donors_at_cap mismatch")
        if self.min_retained_per_donor != EXPECTED_SHORT_DONOR_CELLS:
            raise ValueError("min_retained_per_donor mismatch")
        if self.max_retained_per_donor != PER_DONOR_CAP:
            raise ValueError("max_retained_per_donor mismatch")
        for name in (
            "expression_opened_by_builder",
            "masking_authorized",
            "training_authorized",
        ):
            if getattr(self, name) is not False:
                raise ValueError(f"{name} must remain false")

    def validate_against_authority(
        self,
        authority: Full104TargetQualificationSampleAuthorityV1,
    ) -> None:
        self.validate()
        authority.validate()
        if self.sample_authority_sha256 != authority.canonical_digest():
            raise ValueError("sample authority digest mismatch")
        if self.full104_block_manifest_sha256 != authority.full104_block_manifest_sha256:
            raise ValueError("FULL104 block manifest root mismatch")
        if self.population_authority_sha256 != authority.population_authority_sha256:
            raise ValueError("population authority root mismatch")
        if self.dataset_etl_atlas_sha256 != authority.dataset_etl_atlas_sha256:
            raise ValueError("ETL atlas root mismatch")
        if self.outer_split_receipt_sha256 != authority.outer_split_receipt_sha256:
            raise ValueError("outer split root mismatch")

    def canonical_digest(self) -> str:
        self.validate()
        return _canonical_sha(
            {
                "schema": "V5_FULL104_TARGET_QUALIFICATION_SAMPLE_RECEIPT_V1",
                **asdict(self),
                "expression_opened_by_builder": False,
                "masking_authorized": False,
                "training_authorized": False,
            }
        )
