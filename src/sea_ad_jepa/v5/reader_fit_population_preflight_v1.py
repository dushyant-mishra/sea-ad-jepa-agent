"""Read-only, byte-bound reader-fit population preflight for the V26 diagnostic.

This verifies ONLY the two small frozen metadata CSVs in the authenticated
August 24 calibration archive; no expression, labels, or held-out outcomes
are opened. It cannot authorize training or certify cell-to-donor assignments
against the >30 GB FULL104 raw blocks.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
from dataclasses import dataclass
from fractions import Fraction
import hashlib
import io
import json
from pathlib import Path
import re
import zipfile

ARCHIVE_SHA256 = "07748d5bd21fe0857ccad3002fba3946d1791d25898b841d41056a3707117444"
READER_SPLIT_SHA256 = "efe43e63bfd580085f115f74dd00fdf3051f2c2a77674c99cee5c9ce43322511"
DONOR_METADATA_SHA256 = "c9cbe47d4727aabec8a0c3fed5474c2dab4f9f2b8848357e08b0cec6ef044508"
FIT_MEMBERSHIP_SHA256 = "9332e77c71769f5084e6c94afc9c1aa825f369fe08c8b25bb70682d981d8e977"
FIT_COUNTS_SHA256 = "b2da4aa99c66df435497cf52059c35c11f548b0c7771cb101eee9a6ff14de875"
READER_SUFFIX = "/splits/reader_donor_split.csv"
DONOR_SUFFIX = "/metadata/FOUNDATION_METADATA_DONOR.csv"
EXPECTED_PARTITIONS = {"reader_fit": 104, "reader_validation": 22, "reader_oracle": 23}
EXPECTED_TOTAL_FIT_CELLS = 4_553_407


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _csv_exact(raw: bytes, expected_header: tuple[str, ...], name: str) -> list[tuple[str, ...]]:
    try:
        decoded = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError(f"{name}: invalid UTF-8") from exc
    reader = csv.reader(io.StringIO(decoded, newline=""), strict=True)
    header = next(reader, None)
    if header != list(expected_header):
        raise ValueError(f"{name}: wrong or duplicate CSV header")
    rows = []
    for index, row in enumerate(reader, start=2):
        if len(row) != len(expected_header) or any(not field or field != field.strip() for field in row):
            raise ValueError(f"{name}: missing, padded, or malformed row {index}")
        rows.append(tuple(row))
    return rows


def _strict_count(value: str, name: str) -> int:
    if re.fullmatch(r"[0-9]+", value) is None:
        raise ValueError(f"{name}: count must be an unsigned decimal integer")
    count = int(value)
    if count < 1:
        raise ValueError(f"{name}: count must be positive")
    return count


@dataclass(frozen=True)
class StructuralReaderFitAudit:
    """STRUCTURAL ONLY: this class is NOT an authenticated FULL104 input."""
    partition_counts: dict[str, int]
    fit_membership_digest: str
    fit_count_map_digest: str
    fit_cell_count: int
    fit_ids: frozenset[str]
    donor_counts: dict[str, int]

    def provisional_p_for_claimed_donor(self, donor_id: str) -> Fraction:
        """Exact p=1/(104*n_d), conditional on separately verified cell lineage.

        The claimed donor-to-cell linkage and the sampling proposal q are NOT
        authenticated here. This number must not be passed to production
        optimization without a separate FULL104 reader/proposal attestation.
        """
        if donor_id not in self.donor_counts:
            raise ValueError("unknown or non-reader-fit donor")
        return Fraction(1, 104 * self.donor_counts[donor_id])

    def metadata_receipt(self) -> dict[str, object]:
        return {
            "schema": "V26_READER_FIT_METADATA_PREFLIGHT_V1",
            "scope": "FROZEN_AUG24_METADATA_ONLY",
            "reader_split_sha256": READER_SPLIT_SHA256,
            "donor_metadata_sha256": DONOR_METADATA_SHA256,
            "fit_membership_digest": self.fit_membership_digest,
            "fit_count_map_digest": self.fit_count_map_digest,
            "partition_counts": dict(sorted(self.partition_counts.items())),
            "reader_fit_cell_count": self.fit_cell_count,
            "raw_full104_block_validation": "NOT_PERFORMED",
            "cell_to_donor_lineage_validation": "NOT_PERFORMED",
            "proposal_q_validation": "NOT_PERFORMED",
            "training_authorized": False,
            "protected_outcomes_opened": False,
        }


def _structural_audit(reader_raw: bytes, donor_raw: bytes) -> StructuralReaderFitAudit:
    """Separated from SHA authority for adversarial synthetic unit tests."""
    split_rows = _csv_exact(reader_raw, ("donor_id", "reader_partition"), "reader split")
    donor_rows = _csv_exact(
        donor_raw, ("donor_id", "cell_count", "original_t1_cells"), "donor metadata"
    )
    partition_counts = Counter(part for _, part in split_rows)
    if dict(partition_counts) != EXPECTED_PARTITIONS:
        raise ValueError("reader partitions differ from 104/22/23 frozen counts")
    split_ids = [donor for donor, _ in split_rows]
    if len(split_ids) != len(set(split_ids)):
        raise ValueError("duplicate donor across reader partitions")
    fit_ids = frozenset(donor for donor, part in split_rows if part == "reader_fit")
    metadata_ids = [donor for donor, _, _ in donor_rows]
    if len(metadata_ids) != len(set(metadata_ids)):
        raise ValueError("duplicate donor in metadata")
    if set(metadata_ids) != fit_ids:
        raise ValueError("donor metadata does not exactly equal reader_fit membership")
    counts: dict[str, int] = {}
    for donor, count_string, original_t1_string in donor_rows:
        counts[donor] = _strict_count(count_string, "cell_count")
        if re.fullmatch(r"[0-9]+", original_t1_string) is None:
            raise ValueError("original_t1_cells must be a nonnegative decimal integer")
    total = sum(counts.values())
    if total != EXPECTED_TOTAL_FIT_CELLS:
        raise ValueError("metadata cells do not equal the frozen 4,553,407")
    membership_digest = _sha(("\n".join(sorted(fit_ids)) + "\n").encode())
    count_digest = _sha(("".join(f"{donor}\t{counts[donor]}\n" for donor in sorted(counts))).encode())
    audit = StructuralReaderFitAudit(
        partition_counts=dict(partition_counts),
        fit_membership_digest=membership_digest,
        fit_count_map_digest=count_digest,
        fit_cell_count=total,
        fit_ids=fit_ids,
        donor_counts=counts,
    )
    # Each donor has EXACT mass 1/104; do not sample 4.5 million cells.
    if any(n * audit.provisional_p_for_claimed_donor(d) != Fraction(1, 104)
           for d, n in counts.items()):
        raise RuntimeError("donor scientific mass identity failed")
    return audit


def verify_frozen_reader_fit_bytes(reader_raw: bytes, donor_raw: bytes) -> StructuralReaderFitAudit:
    """Only this exact-SHA entrypoint qualifies the frozen metadata identity."""
    if _sha(reader_raw) != READER_SPLIT_SHA256:
        raise ValueError("reader split byte SHA-256 mismatch")
    if _sha(donor_raw) != DONOR_METADATA_SHA256:
        raise ValueError("donor metadata byte SHA-256 mismatch")
    result = _structural_audit(reader_raw, donor_raw)
    if result.fit_membership_digest != FIT_MEMBERSHIP_SHA256:
        raise ValueError("reader_fit membership fingerprint mismatch")
    if result.fit_count_map_digest != FIT_COUNTS_SHA256:
        raise ValueError("reader_fit donor-count fingerprint mismatch")
    return result


def verify_frozen_calibration_bundle(archive_path: str | Path) -> dict[str, object]:
    """Read only two explicitly allowlisted CSV members after whole-ZIP hashing."""
    path = Path(archive_path)
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 << 20), b""):
            digest.update(chunk)
    if digest.hexdigest() != ARCHIVE_SHA256:
        raise ValueError("calibration ZIP byte SHA-256 mismatch")
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise ValueError("ZIP duplicate member name")
        values = []
        for suffix in (READER_SUFFIX, DONOR_SUFFIX):
            matching = [name for name in names if name.endswith(suffix)]
            if len(matching) != 1:
                raise ValueError("frozen metadata ZIP member missing or ambiguous")
            info = archive.getinfo(matching[0])
            if info.file_size > 1_000_000:
                raise ValueError("metadata ZIP member exceeds one-megabyte bound")
            values.append(archive.read(info))
    result = verify_frozen_reader_fit_bytes(*values)
    return {"source_bundle_sha256": ARCHIVE_SHA256, **result.metadata_receipt()}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--calibration-zip", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(verify_frozen_calibration_bundle(args.calibration_zip), sort_keys=True))


if __name__ == "__main__":
    main()
