"""Adversarial synthetic tests of the frozen reader-fit proposal, NOT real training."""
from __future__ import annotations

import numpy as np
import pytest

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


def select(seed=7, index=0, n=100):
    counts, ids, codes = fixture()
    return _propose_structural(
        cell_donor=codes, donor_ids=ids, expected_counts=counts,
        run_seed=seed, update_index=index, presentations=n,
        source_digest="a" * 64,
    )


def test_exact_positive_control_and_no_training_authority():
    got = select()
    counts, ids, codes = fixture()
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


def test_repeated_cells_allowed_and_counted_as_presentations():
    got = select(n=100)
    assert len(set(got.selection_rows.tolist())) < len(got.selection_rows)
    assert got.nontraining_report()["presentations"] == 100


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
    counts, ids, codes = fixture()
    a = select(n=100)
    b = _propose_structural(
        cell_donor=codes, donor_ids=ids, expected_counts=counts,
        run_seed=7, update_index=0, presentations=100,
        source_digest="b" * 64,
    )
    assert a.seed_sha256 != b.seed_sha256
    assert not np.array_equal(a.selection_rows, b.selection_rows)


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
