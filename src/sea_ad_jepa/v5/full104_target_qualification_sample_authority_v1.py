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
- selection may use donor identity + stable cell identity + frozen namespace only;
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
import json
from typing import Any, Mapping


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

    def selection_priority(self, *, donor_id: str, stable_cell_key: str) -> bytes:
        """Deterministic expression-blind within-donor ordering key."""
        self.validate()
        if not isinstance(donor_id, str) or not donor_id:
            raise ValueError("donor_id must be nonempty")
        if not isinstance(stable_cell_key, str) or not stable_cell_key:
            raise ValueError("stable_cell_key must be nonempty")
        payload = (
            f"{self.selection_namespace_id}|"
            f"{self.population_authority_sha256}|"
            f"donor|{donor_id}|cell|{stable_cell_key}"
        ).encode("utf-8")
        return hashlib.sha256(payload).digest()
