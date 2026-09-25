"""Read-only frozen-pass1 donor histogram adversaries: SYNTHETIC FIXTURES ONLY."""
from __future__ import annotations

from collections import Counter
import hashlib
import os
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

import sea_ad_jepa.v5.frozen_pass1_reader_fit_count_bridge_v1 as bridge


def case():
    counts = {"A": 2, "B": 1, "C": 3, "D": 2}
    ids = np.asarray(["A", "B", "C", "D"], dtype="U1")
    codes = np.asarray([0, 0, 1, 2, 2, 2, 3, 3], dtype=np.int16)
    return codes, ids, counts


def test_structural_exact_per_donor_counts_and_total_match():
    codes, ids, counts = case()
    report = bridge._compare_structural(codes, ids, counts)
    assert report.matched and report.donor_count == 4 and report.total_cells == 8
    assert report.structural_report()["status"] == "STRUCTURAL_ONLY_UNBOUND"
    assert report.structural_report()["training_authorized"] is False
    assert "frozen_pass1_sha256" not in report.structural_report()


def test_permuted_donor_order_and_corresponding_codes_preserve_mass():
    codes, ids, counts = case()
    new_ids = np.asarray(["D", "A", "C", "B"], dtype="U1")
    mapping = np.asarray([1, 3, 2, 0], dtype=np.int16)
    assert bridge._compare_structural(mapping[codes], new_ids, counts).matched


def test_donor_count_swap_with_unchanged_total_is_rejected():
    codes, ids, counts = case()
    changed = codes.copy()
    changed[1] = 1
    assert len(changed) == sum(counts.values())
    with pytest.raises(ValueError, match="per-donor cell counts"):
        bridge._compare_structural(changed, ids, counts)


def test_unknown_heldout_donor_replacing_fit_donor_rejected():
    codes, ids, counts = case()
    ids[0] = "O"
    with pytest.raises(ValueError, match="roster"):
        bridge._compare_structural(codes, ids, counts)


def test_duplicate_donor_ids_fail_closed():
    codes, ids, counts = case()
    ids[2] = "A"
    with pytest.raises(ValueError, match="unique"):
        bridge._compare_structural(codes, ids, counts)


@pytest.mark.parametrize("value", [-1, 4, 2**31])
def test_out_of_range_cell_to_donor_codes_rejected(value):
    codes, ids, counts = case()
    bad = codes.astype(np.int64)
    bad[-1] = value
    with pytest.raises(ValueError, match="out-of-range"):
        bridge._compare_structural(bad, ids, counts)


@pytest.mark.parametrize("dtype", [np.float32, np.float64, np.bool_])
def test_noninteger_cell_to_donor_dtype_rejected(dtype):
    codes, ids, counts = case()
    with pytest.raises(ValueError, match="exact integer"):
        bridge._compare_structural(codes.astype(dtype), ids, counts)


def test_object_array_donor_id_rejected_without_pickle():
    codes, ids, counts = case()
    with pytest.raises(ValueError, match="non-object"):
        bridge._compare_structural(codes, ids.astype(object), counts)


def test_shorter_historical_run_not_accepted_as_full_population():
    codes, ids, counts = case()
    with pytest.raises(ValueError, match="total cell count"):
        bridge._compare_structural(codes[:-1], ids, counts)


def test_extra_continuation_donor_not_permitted():
    codes, ids, counts = case()
    with pytest.raises(ValueError, match="roster"):
        bridge._compare_structural(codes, ids, {**counts, "CONTINUATION": 1})


def test_padded_donor_name_rejected():
    codes, ids, counts = case()
    padded = ids.astype("U6")
    padded[1] = " B "
    with pytest.raises(ValueError, match="unpadded"):
        bridge._compare_structural(codes, padded, counts)


@pytest.mark.parametrize("bad", [0, -2, 1.1, True])
def test_invalid_frozen_expected_donor_count_rejected(bad):
    codes, ids, counts = case()
    bad_counts = {**counts, "B": bad}
    with pytest.raises(ValueError, match="positive exact"):
        bridge._compare_structural(codes, ids, bad_counts)


def _synthetic_pinned_pass1(monkeypatch, tmp_path: Path):
    codes, ids, counts = case()
    path = tmp_path / "pass1_synthetic_do_not_promote.npz"
    np.savez_compressed(path, cell_donor=codes, duniq=ids, extra_unread_key=np.asarray([7]))
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    monkeypatch.setattr(bridge, "FROZEN_PASS1_SHA256", digest)
    monkeypatch.setattr(bridge, "EXPECTED_FIT_DONORS", 4)
    monkeypatch.setattr(bridge, "EXPECTED_TOTAL_FIT_CELLS", 8)
    # The real production code's pinned ZIP verifier is tested separately in
    # PR130. Only fake census records are supplied inside this toy fixture.
    monkeypatch.setattr(bridge, "load_frozen_reader_fit_from_bundle", lambda _: SimpleNamespace(donor_counts=counts))
    normalized = "".join(f"{d}\t{counts[d]}\n" for d in sorted(counts))
    monkeypatch.setattr(bridge, "FIT_COUNTS_SHA256", hashlib.sha256(normalized.encode()).hexdigest())
    return path


def test_toy_npz_file_descriptor_hash_and_schema_path(monkeypatch, tmp_path):
    path = _synthetic_pinned_pass1(monkeypatch, tmp_path)
    receipt = bridge.verify_frozen_pass1_reader_fit_count_bridge(
        pass1_path=path, calibration_zip=tmp_path / "NOT_A_REAL_CALIBRATION.zip"
    )
    assert receipt["per_donor_exact_count_match"] is True
    assert receipt["pass1_to_raw_level4_binding"] == "NOT_REVALIDATED_BY_THIS_GATE"
    assert receipt["raw_level4_blocks_opened"] == 0
    assert receipt["proposal_q_validation"] == "NOT_PERFORMED"
    assert receipt["training_authorized"] is False


def test_toy_npz_mutation_rejected_by_outer_file_sha(monkeypatch, tmp_path):
    path = _synthetic_pinned_pass1(monkeypatch, tmp_path)
    with path.open("ab") as handle:
        handle.write(b"tamper")
    with pytest.raises(ValueError, match="pass1 file SHA"):
        bridge.verify_frozen_pass1_reader_fit_count_bridge(
            pass1_path=path, calibration_zip=tmp_path / "unused"
        )


def test_toy_npz_missing_keys_rejected_after_matching_test_only_outer_hash(monkeypatch, tmp_path):
    path = _synthetic_pinned_pass1(monkeypatch, tmp_path)
    np.savez_compressed(path, cell_donor=np.asarray([0, 0]))
    monkeypatch.setattr(bridge, "FROZEN_PASS1_SHA256", hashlib.sha256(path.read_bytes()).hexdigest())
    with pytest.raises(ValueError, match="missing exact cell_donor/duniq"):
        bridge.verify_frozen_pass1_reader_fit_count_bridge(
            pass1_path=path, calibration_zip=tmp_path / "unused"
        )


def test_toy_npz_object_metadata_fails_allow_pickle_false(monkeypatch, tmp_path):
    path = _synthetic_pinned_pass1(monkeypatch, tmp_path)
    np.savez_compressed(path, cell_donor=np.arange(8) % 4, duniq=np.asarray(["A", "B", "C", "D"], dtype=object))
    monkeypatch.setattr(bridge, "FROZEN_PASS1_SHA256", hashlib.sha256(path.read_bytes()).hexdigest())
    with pytest.raises(ValueError, match="Object arrays cannot be loaded"):
        bridge.verify_frozen_pass1_reader_fit_count_bridge(
            pass1_path=path, calibration_zip=tmp_path / "unused"
        )


def test_toy_npz_path_replacement_after_hash_still_reads_same_descriptor(monkeypatch, tmp_path):
    path = _synthetic_pinned_pass1(monkeypatch, tmp_path)
    replacement = tmp_path / "replacement.npz"
    np.savez_compressed(replacement, cell_donor=np.zeros(8, dtype=np.int64), duniq=np.array(["X"], dtype="U1"))
    original_sha_function = bridge._sha256_open_file
    def replace_after_hash(open_stream):
        digest = original_sha_function(open_stream)
        os.replace(replacement, path)
        return digest
    monkeypatch.setattr(bridge, "_sha256_open_file", replace_after_hash)
    receipt = bridge.verify_frozen_pass1_reader_fit_count_bridge(
        pass1_path=path, calibration_zip=tmp_path / "unused"
    )
    assert receipt["per_donor_exact_count_match"] is True


def test_unpatched_synthetic_pass1_never_matches_actual_frozen_full104_sha(tmp_path):
    codes, ids, _ = case()
    path = tmp_path / "small_run.npz"
    np.savez_compressed(path, cell_donor=codes, duniq=ids)
    assert hashlib.sha256(path.read_bytes()).hexdigest() != bridge.FROZEN_PASS1_SHA256
    with pytest.raises(ValueError, match="pass1 file SHA"):
        bridge.verify_frozen_pass1_reader_fit_count_bridge(
            pass1_path=path, calibration_zip=tmp_path / "unused"
        )
