"""Adversarial metadata-only tests. Synthetic donors are NOT real population authority."""
from __future__ import annotations

import csv
from fractions import Fraction
import io
import zipfile

import pytest

from sea_ad_jepa.v5.reader_fit_population_preflight_v1 import (
    ARCHIVE_SHA256,
    EXPECTED_TOTAL_FIT_CELLS,
    _structural_audit,
    verify_frozen_calibration_bundle,
    verify_frozen_reader_fit_bytes,
)


def encode(header, rows):
    out = io.StringIO(newline="")
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(header)
    writer.writerows(rows)
    return out.getvalue().encode("utf-8")


def fixture_rows():
    fit = [f"SYNTHETIC_FIT_{i:03d}" for i in range(104)]
    validation = [f"SYNTHETIC_VALIDATION_{i:03d}" for i in range(22)]
    oracle = [f"SYNTHETIC_ORACLE_{i:03d}" for i in range(23)]
    split = [(x, "reader_fit") for x in fit]
    split += [(x, "reader_validation") for x in validation]
    split += [(x, "reader_oracle") for x in oracle]
    base, remainder = divmod(EXPECTED_TOTAL_FIT_CELLS, 104)
    donor = [(x, str(base + (remainder if i == 103 else 0)), "0")
             for i, x in enumerate(fit)]
    return split, donor


def raw(split, donor):
    return (encode(("donor_id", "reader_partition"), split),
            encode(("donor_id", "cell_count", "original_t1_cells"), donor))


def test_structural_synthetic_fixture_proves_exact_donor_mass_not_authority():
    split, donors = fixture_rows()
    result = _structural_audit(*raw(split, donors))
    assert result.partition_counts == {"reader_fit": 104, "reader_validation": 22, "reader_oracle": 23}
    assert result.fit_cell_count == 4_553_407
    assert len(result.donor_counts) == 104
    assert all(
        result.donor_counts[d] * result.provisional_p_for_claimed_donor(d) == Fraction(1, 104)
        for d in result.fit_ids
    )
    assert sum((n * result.provisional_p_for_claimed_donor(d)
                for d, n in result.donor_counts.items()), Fraction()) == 1
    assert result.metadata_receipt()["training_authorized"] is False
    assert result.metadata_receipt()["raw_full104_block_validation"] == "NOT_PERFORMED"


def test_synthetic_data_cannot_claim_exact_frozen_reader_fit_authority():
    split, donors = fixture_rows()
    with pytest.raises(ValueError, match="reader split byte SHA"):
        verify_frozen_reader_fit_bytes(*raw(split, donors))


def test_missing_fit_donor_rejected():
    split, donors = fixture_rows()
    with pytest.raises(ValueError, match="exactly equal"):
        _structural_audit(*raw(split, donors[:-1]))


def test_oracle_donor_substituted_into_fit_metadata_rejected():
    split, donors = fixture_rows()
    donors[0] = (split[-1][0], donors[0][1], "0")
    with pytest.raises(ValueError, match="exactly equal"):
        _structural_audit(*raw(split, donors))


def test_duplicate_id_across_reader_partitions_rejected():
    split, donors = fixture_rows()
    split[104] = (split[0][0], "reader_validation")
    with pytest.raises(ValueError, match="duplicate donor"):
        _structural_audit(*raw(split, donors))


def test_duplicate_metadata_donor_rejected():
    split, donors = fixture_rows()
    donors[-1] = (donors[0][0], donors[-1][1], "0")
    with pytest.raises(ValueError, match="duplicate donor"):
        _structural_audit(*raw(split, donors))


def test_historical_continuation_donor_cannot_enter_fit_metadata():
    split, donors = fixture_rows()
    donors.extend((f"SYNTHETIC_CONTINUATION_{i}", "1", "0") for i in range(17))
    with pytest.raises(ValueError, match="exactly equal"):
        _structural_audit(*raw(split, donors))


def test_unauthorized_partition_change_rejected():
    split, donors = fixture_rows()
    split[0] = (split[0][0], "reader_validation")
    with pytest.raises(ValueError, match="frozen counts"):
        _structural_audit(*raw(split, donors))


def test_wrong_total_cell_count_rejected():
    split, donors = fixture_rows()
    x = donors[0]
    donors[0] = (x[0], str(int(x[1]) + 1), x[2])
    with pytest.raises(ValueError, match="4,553,407"):
        _structural_audit(*raw(split, donors))


@pytest.mark.parametrize("corrupt", ["0", "-1", "1.0", "NaN", "1e4", " 3"])
def test_nonpositive_or_noninteger_donor_counts_rejected(corrupt):
    split, donors = fixture_rows()
    donors[0] = (donors[0][0], corrupt, "0")
    with pytest.raises(ValueError, match="cell_count|malformed"):
        _structural_audit(*raw(split, donors))


def test_unexpected_donor_csv_column_rejected():
    split, donors = fixture_rows()
    split_raw, donor_raw = raw(split, donors)
    with pytest.raises(ValueError, match="CSV header"):
        _structural_audit(split_raw, donor_raw.replace(
            b"donor_id,cell_count,original_t1_cells",
            b"donor_id,cell_count,original_t1_cells,legacy_extra",
            1,
        ))


def test_wrong_reader_column_order_rejected():
    split, donors = fixture_rows()
    split_raw, donor_raw = raw(split, donors)
    with pytest.raises(ValueError, match="CSV header"):
        _structural_audit(split_raw.replace(
            b"donor_id,reader_partition", b"reader_partition,donor_id", 1
        ), donor_raw)


def test_whitespace_padded_donor_identity_rejected():
    split, donors = fixture_rows()
    split[0] = (" " + split[0][0], "reader_fit")
    with pytest.raises(ValueError, match="padded"):
        _structural_audit(*raw(split, donors))


def test_unseen_donor_has_no_scientific_weight():
    split, donors = fixture_rows()
    result = _structural_audit(*raw(split, donors))
    with pytest.raises(ValueError, match="non-reader-fit"):
        result.provisional_p_for_claimed_donor("SYNTHETIC_ORACLE_000")


def test_bad_or_synthetic_zip_is_rejected_before_opening_members(tmp_path):
    split, donors = fixture_rows()
    split_raw, donor_raw = raw(split, donors)
    path = tmp_path / "synthetic.zip"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("frozen/splits/reader_donor_split.csv", split_raw)
        archive.writestr("frozen/metadata/FOUNDATION_METADATA_DONOR.csv", donor_raw)
    assert ARCHIVE_SHA256 != __import__("hashlib").sha256(path.read_bytes()).hexdigest()
    with pytest.raises(ValueError, match="calibration ZIP byte"):
        verify_frozen_calibration_bundle(path)


def test_malformed_csv_row_rejected():
    split, donors = fixture_rows()
    split_raw, donor_raw = raw(split, donors)
    with pytest.raises(ValueError, match="malformed"):
        _structural_audit(split_raw + b"bad,trailing,extra\n", donor_raw)
