"""Adversarial synthetic tests of the frozen reader-fit proposal, NOT real training."""
from __future__ import annotations

import numpy as np
import pytest

from scripts.agent.run_v26_reader_fit_development_proposal import _write_synthetic_safe

from sea_ad_jepa.v5.reader_fit_development_sampler_v1 import (
    _propose_structural,
    propose_from_frozen_pass1,
)


def fixture():
    # Tiny entirely synthetic population, deliberately unequal donor sizes.
    counts = {"SYNTH_A": 2, "SYNTH_B": 3, "SYNTH_C": 5}
    ids = np.array(["SYNTH_B", "SYNTH_C", "SYNTH_A"], dtype="U7")
    codes = np.array([0, 1, 2, 1, 0, 1, 1, 2, 1, 0], dtype=np.int64)
    # 0->3;1->5;2->2
    return counts, ids, codes


def large_fixture():
    counts = {"SYNTH_A": 12000, "SYNTH_B": 15000, "SYNTH_C": 20000}
    ids = np.array(["SYNTH_B", "SYNTH_C", "SYNTH_A"], dtype="U7")
    codes = np.concatenate([
        np.full(15000, 0, dtype=np.int64),
        np.full(20000, 1, dtype=np.int64),
        np.full(12000, 2, dtype=np.int64),
    ])
    return counts, ids, codes


def select(seed=7, index=0, n=100):
    counts, ids, codes = large_fixture()
    return _propose_structural(
        cell_donor=codes, donor_ids=ids, expected_counts=counts,
        run_seed=seed, update_index=index, presentations=n,
        source_digest="a" * 64,
    )


def test_exact_positive_control_and_no_training_authority():
    got = select()
    counts, ids, codes = large_fixture()
    assert len(got.selection_rows) == 100
    assert np.array_equal(codes[got.selection_rows], got.donor_codes)
    expected = np.array([1 / (3 * counts[ids[d]]) for d in got.donor_codes])
    assert np.array_equal(got.proposal_probabilities, expected)
    assert np.array_equal(got.importance_weights, np.ones(100))
    receipt = got.nontraining_report()
    assert receipt["training_authorized"] is False
    assert receipt["raw_level4_lineage_verified_here"] is False
    assert receipt["importance_weights_all_one"] is True


def test_same_seed_index_and_population_replay_bit_identical():
    a, b = select(), select()
    assert np.array_equal(a.selection_rows, b.selection_rows)
    assert np.array_equal(a.donor_codes, b.donor_codes)
    assert a.nontraining_report() == b.nontraining_report()


def test_different_update_index_produces_different_draws():
    assert not np.array_equal(select(index=0).selection_rows, select(index=1).selection_rows)


def test_different_seed_produces_different_draws():
    assert not np.array_equal(select(seed=7).selection_rows, select(seed=8).selection_rows)


def test_exact_donor_uniform_not_cell_uniform_large_draw():
    got = select(n=24000)
    observed = np.bincount(got.donor_codes, minlength=3) / 24000
    assert np.max(np.abs(observed - 1 / 3)) < 0.02


def test_cells_unique_per_update_and_donor_draws_remain_with_replacement():
    got = select(n=100)
    assert len(set(got.selection_rows.tolist())) == len(got.selection_rows)
    assert len(set(got.donor_codes.tolist())) <= 3
    assert got.nontraining_report()["presentations"] == 100
    assert got.nontraining_report()["cells_within_donor_without_replacement_per_update"] is True


@pytest.mark.parametrize("seed,index,presentations", [
    (True, 0, 1), (-1, 0, 1), (7, True, 1), (7, -1, 1),
    (7, 0, 0), (7, 0, False), (7, 0, 1.5),
])
def test_invalid_cursor_seed_and_presentations_stop(seed, index, presentations):
    counts, ids, codes = fixture()
    with pytest.raises(ValueError):
        _propose_structural(
            cell_donor=codes, donor_ids=ids, expected_counts=counts,
            run_seed=seed, update_index=index, presentations=presentations,
            source_digest="a" * 64,
        )


def test_duplicate_donor_identity_fails_closed():
    counts, ids, codes = fixture()
    ids[2] = ids[0]
    with pytest.raises(ValueError, match="unique"):
        _propose_structural(
            cell_donor=codes, donor_ids=ids, expected_counts=counts,
            run_seed=1, update_index=0, presentations=4,
            source_digest="a" * 64,
        )


def test_unchanged_global_total_but_swapped_donor_masses_fails():
    counts, ids, codes = fixture()
    codes = codes.copy()
    codes[0] = 1  # observed 0=2, 1=6, total still 10
    with pytest.raises(ValueError, match="per-donor"):
        _propose_structural(
            cell_donor=codes, donor_ids=ids, expected_counts=counts,
            run_seed=1, update_index=0, presentations=4,
            source_digest="a" * 64,
        )


def test_heldout_or_continuation_donor_identity_fails():
    counts, ids, codes = fixture()
    ids[2] = "ORACLE"
    with pytest.raises(ValueError, match="roster"):
        _propose_structural(
            cell_donor=codes, donor_ids=ids, expected_counts=counts,
            run_seed=1, update_index=0, presentations=4,
            source_digest="a" * 64,
        )


@pytest.mark.parametrize("bad", [np.array([-1,1,2,1,0,1,1,2,1,0]),
                                  np.array([9,1,2,1,0,1,1,2,1,0]),
                                  np.array([0.,1,2,1,0,1,1,2,1,0])])
def test_bad_pass1_donor_code_or_type_fails(bad):
    counts, ids, _ = fixture()
    with pytest.raises(ValueError):
        _propose_structural(
            cell_donor=bad, donor_ids=ids, expected_counts=counts,
            run_seed=1, update_index=0, presentations=4,
            source_digest="a" * 64,
        )


def test_change_in_source_root_changes_rng_stream():
    counts, ids, codes = large_fixture()
    a = select(n=100)
    b = _propose_structural(
        cell_donor=codes, donor_ids=ids, expected_counts=counts,
        run_seed=7, update_index=0, presentations=100,
        source_digest="b" * 64,
    )
    assert a.seed_sha256 != b.seed_sha256
    assert not np.array_equal(a.selection_rows, b.selection_rows)


def test_oversubscribed_donor_slots_stop_before_returning_selection():
    counts, ids, codes = fixture()
    with pytest.raises(ValueError, match="exceed unique frozen donor cells"):
        _propose_structural(
            cell_donor=codes, donor_ids=ids, expected_counts=counts,
            run_seed=7, update_index=0, presentations=11,
            source_digest="a" * 64,
        )


def test_no_real_file_implies_no_real_selection(tmp_path):
    with pytest.raises(FileNotFoundError):
        propose_from_frozen_pass1(
            pass1_path=tmp_path / "missing_full104_pass1.npz",
            calibration_zip=tmp_path / "missing_archive.zip",
            run_seed=7, update_index=0, presentations=4,
        )


def test_synthetic_helper_does_not_emit_frozen_pass1_or_calibration_roots():
    report = select().nontraining_report()
    assert "frozen_pass1_sha256" not in report
    assert "frozen_calibration_zip_sha256" not in report
    assert report["status"] == "DETERMINISTIC_PROPOSAL_ONLY"
    assert report["training_authorized"] is False


def test_synthetic_output_writer_records_npz_hash_without_training(tmp_path):
    """File-writing fixture ONLY; not a physical frozen-pass1 execution."""
    update = select(n=100)
    out = tmp_path / "new_versioned"
    receipt = _write_synthetic_safe(
        out_dir=out, proposal=update, receipt=update.nontraining_report(),
    )
    assert receipt["training_authorized"] is False
    assert receipt["selection_npz_sha256"]
    with np.load(out / "development_update_selection.npz", allow_pickle=False) as data:
        assert set(data.files) == {
            "selection_rows", "donor_codes",
            "proposal_probabilities", "importance_weights",
        }
        assert np.array_equal(data["selection_rows"], update.selection_rows)
    assert (out / "development_update_receipt.json").is_file()
    assert "frozen_pass1_sha256" not in receipt


def test_synthetic_output_writer_refuses_existing_output_dir(tmp_path):
    out = tmp_path / "existing"
    out.mkdir()
    u = select(n=10)
    with pytest.raises(FileExistsError, match="existing result directory"):
        _write_synthetic_safe(out_dir=out, proposal=u, receipt=u.nontraining_report())


def test_synthetic_output_writer_rejects_forged_training_receipt(tmp_path):
    u = select(n=10)
    bad = {**u.nontraining_report(), "training_authorized": True}
    with pytest.raises(ValueError, match="training-authorized"):
        _write_synthetic_safe(out_dir=tmp_path / "forged", proposal=u, receipt=bad)
    assert not (tmp_path / "forged").exists()


def test_synthetic_output_writer_rejects_selection_digest_mismatch(tmp_path):
    u = select(n=10)
    bad = {**u.nontraining_report(), "selection_rows_sha256": "f" * 64}
    with pytest.raises(ValueError, match="selection rows differ"):
        _write_synthetic_safe(out_dir=tmp_path / "forged", proposal=u, receipt=bad)
    assert not (tmp_path / "forged").exists()
