"""Bind the frozen FULL104 pass1 cell_donor histogram to the frozen reader-fit roster.

This is the missing *cheap* cross-asset check after the existing 8,915-block
physical pass1 binder. It reads only the exact historical pass1 NPZ and two
allowlisted frozen calibration ZIP metadata CSVs. It MUST NOT certify pass1
against raw Level-4 blocks, infer a proposal q, or authorize training.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Mapping

import numpy as np

from .reader_fit_population_preflight_v1 import (
    ARCHIVE_SHA256,
    EXPECTED_TOTAL_FIT_CELLS,
    FIT_COUNTS_SHA256,
    FIT_MEMBERSHIP_SHA256,
    load_frozen_reader_fit_from_bundle,
)

# Frozen pass1 file, not the larger corrected derivative or any T1 checkpoint.
# Source: PR120 exact N1 read-only physical reaggregation runbook.
FROZEN_PASS1_SHA256 = "37f79e49f11364daa487ad9e5a5680f72378daf338852765d2f52e1e98d90ba1"
EXPECTED_FIT_DONORS = 104


@dataclass(frozen=True)
class StructuralCountComparison:
    """No byte authority: may be constructed from synthetic fixtures."""
    donor_count: int
    total_cells: int
    matched: bool

    def structural_report(self) -> dict[str, object]:
        return {
            "schema": "V26_SYNTHETIC_PASS1_DONOR_COUNTS_STRUCTURAL_V1",
            "status": "STRUCTURAL_ONLY_UNBOUND",
            "donor_count": self.donor_count,
            "total_cells": self.total_cells,
            "matched": self.matched,
            "full104_raw_block_validation": "NOT_PERFORMED",
            "per_cell_donor_lineage_validation": "NOT_PERFORMED",
            "balanced_reciprocal_cell_swaps": "NOT_DETECTABLE_BY_HISTOGRAM",
            "training_authorized": False,
        }


def _compare_structural(
    cell_donor: np.ndarray,
    donor_ids: np.ndarray,
    expected_counts: Mapping[str, int],
) -> StructuralCountComparison:
    """Synthetic/structural helper. Has NO frozen input SHA or training authority."""
    codes = np.asarray(cell_donor)
    ids = np.asarray(donor_ids)
    if codes.ndim != 1 or codes.dtype.kind not in "iu":
        raise ValueError("pass1 cell_donor must be 1D exact integer donor codes")
    if ids.ndim != 1 or ids.dtype.kind not in "US":
        raise ValueError("pass1 duniq must be 1D non-object Unicode/byte strings")
    names = [str(x) for x in ids.astype(str)]
    if not names or len(names) != len(set(names)) or any(not n or n != n.strip() for n in names):
        raise ValueError("pass1 donor IDs must be unique, nonblank and unpadded")
    if any(
        not isinstance(d, str) or not d or isinstance(n, bool)
        or not isinstance(n, int) or n <= 0
        for d, n in expected_counts.items()
    ):
        raise ValueError("expected donor counts must be positive exact integers")
    if set(names) != set(expected_counts):
        raise ValueError("pass1 donor roster differs from frozen reader-fit membership")
    if codes.size != sum(expected_counts.values()):
        raise ValueError("pass1 total cell count does not equal frozen reader-fit count")
    # np.bincount converts to platform native signed int; first guard the exact
    # source dtype/range to avoid unsigned wrap or float coercion.
    if codes.size and (bool(np.any(codes < 0)) or bool(np.any(codes >= len(names)))):
        raise ValueError("pass1 cell_donor contains out-of-range donor code")
    counts = np.bincount(codes.astype(np.int64, copy=False), minlength=len(names))
    if len(counts) != len(names):
        raise ValueError("pass1 donor-code histogram cardinality mismatch")
    if any(int(counts[i]) != expected_counts[donor] for i, donor in enumerate(names)):
        raise ValueError("per-donor cell counts differ from frozen reader-fit metadata")
    return StructuralCountComparison(
        donor_count=len(names), total_cells=int(codes.size), matched=True
    )


def _sha256_open_file(stream) -> str:
    digest = hashlib.sha256()
    for chunk in iter(lambda: stream.read(8 << 20), b""):
        digest.update(chunk)
    return digest.hexdigest()


def verify_frozen_pass1_reader_fit_count_bridge(
    *,
    pass1_path: Path | str,
    calibration_zip: Path | str,
) -> dict[str, object]:
    """Verify TWO independent immutable artifacts. Do not open raw Level-4 blocks.

    A pass here means exactly the named pass1 file has the archived donor-count
    histogram. Existing pass1 physical binding remains a SEPARATE required
    certificate for raw block lineage; neither certificate unlocks training.
    """
    path = Path(pass1_path)
    # Verify and consume pass1 through the SAME open descriptor so a pathname
    # replacement cannot splice different bytes in between hashing and parse.
    with path.open("rb") as stream:
        observed_sha = _sha256_open_file(stream)
        if observed_sha != FROZEN_PASS1_SHA256:
            raise ValueError("wrong frozen FULL104 pass1 file SHA-256")
        stream.seek(0)
        with np.load(stream, allow_pickle=False) as payload:
            if not isinstance(payload, np.lib.npyio.NpzFile):
                raise ValueError("frozen pass1 must be an NPZ file")
            if not {"cell_donor", "duniq"}.issubset(payload.files):
                raise ValueError("frozen pass1 missing exact cell_donor/duniq keys")
            donor_codes = np.asarray(payload["cell_donor"])
            donor_ids = np.asarray(payload["duniq"])

    frozen = load_frozen_reader_fit_from_bundle(calibration_zip)
    comparison = _compare_structural(donor_codes, donor_ids, frozen.donor_counts)
    if comparison.donor_count != EXPECTED_FIT_DONORS:
        raise ValueError("pass1 donor count is not FULL104")
    if comparison.total_cells != EXPECTED_TOTAL_FIT_CELLS:
        raise ValueError("pass1 cell count is not FULL104")
    # The same digest must reproduce independently from the verified frozen
    # donor count map and the hash-pinned pass1 per-donor histogram.
    observed = np.bincount(donor_codes.astype(np.int64, copy=False), minlength=EXPECTED_FIT_DONORS)
    count_map = {str(d): int(observed[i]) for i, d in enumerate(donor_ids.astype(str))}
    normalized = "".join(f"{d}\t{count_map[d]}\n" for d in sorted(count_map))
    count_digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    if count_digest != FIT_COUNTS_SHA256:
        raise ValueError("pass1 per-donor fingerprint differs from frozen authority")
    return {
        "schema": "V26_FROZEN_PASS1_READER_FIT_DONOR_COUNT_BRIDGE_V1",
        "status": "BYTE_BOUND_PASS1_AND_METADATA_COUNTS_ONLY",
        "frozen_pass1_sha256": FROZEN_PASS1_SHA256,
        "frozen_calibration_bundle_sha256": ARCHIVE_SHA256,
        "reader_fit_membership_sha256": FIT_MEMBERSHIP_SHA256,
        "reader_fit_donor_counts_sha256": count_digest,
        "donor_count": comparison.donor_count,
        "cell_count": comparison.total_cells,
        "per_donor_exact_count_match": comparison.matched,
        "per_cell_donor_lineage_validation": "NOT_PERFORMED_BY_THIS_GATE",
        "balanced_reciprocal_cell_swaps": "NOT_DETECTABLE_BY_HISTOGRAM",
        "pass1_to_raw_level4_binding": "NOT_REVALIDATED_BY_THIS_GATE",
        "raw_level4_blocks_opened": 0,
        "source_library_validation": "NOT_PERFORMED",
        "proposal_q_validation": "NOT_PERFORMED",
        "training_authorized": False,
        "protected_outcomes_opened": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pass1", required=True, type=Path)
    parser.add_argument("--calibration-zip", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    receipt = verify_frozen_pass1_reader_fit_count_bridge(
        pass1_path=args.pass1,
        calibration_zip=args.calibration_zip,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x", encoding="utf-8") as handle:
        json.dump(receipt, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps({"status": receipt["status"], "out": str(args.out)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
