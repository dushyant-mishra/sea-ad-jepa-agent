"""Adversarial CPU-only prepared trajectory fixture; no physical FULL104 opened."""
from __future__ import annotations

import numpy as np
import pytest

from sea_ad_jepa.v5.reader_fit_development_sampler_v1 import _propose_structural
from sea_ad_jepa.v5.prepared_reader_fit_development_schedule_v1 import (
    PreparedReaderFitProposal, prepare_from_frozen_pass1,
)


def tiny():
    counts = {"D0": 4, "D1": 5, "D2": 7}
    names = np.array(["D2", "D0", "D1"], dtype="U2")
    codes = np.array([0, 2, 0, 1, 2, 0, 1, 2, 0, 2, 0, 2, 1, 0, 0, 1])
    # Code order: D2=7, D0=4, D1=5
    return counts, names, codes.astype(np.int64)


def prep():
    counts, names, codes = tiny()
    return PreparedReaderFitProposal.structural_only(
        cell_donor=codes, donor_ids=names,
        expected_counts=counts, source_digest="a" * 64,
    )


@pytest.mark.parametrize("cursor", [0, 1, 7, 99])
def test_prepared_replays_original_pr135_exactly(cursor):
    counts, names, codes = tiny()
    reference = _propose_structural(
        cell_donor=codes, donor_ids=names, expected_counts=counts,
        run_seed=81, update_index=cursor, presentations=4,
        source_digest="a" * 64,
    )
    got = prep().proposal(run_seed=81, update_index=cursor, presentations=4)
    for field in ("selection_rows", "donor_codes", "proposal_probabilities", "importance_weights"):
        assert np.array_equal(getattr(reference, field), getattr(got, field))
    assert reference.seed_sha256 == got.seed_sha256
    assert reference.nontraining_report() == got.nontraining_report()


def test_planned_contiguous_cursors_match_separate_single_update_replay():
    p = prep()
    plan = p.plan(run_seed=42, first_update_index=5, update_count=8, presentations_per_update=3,
        maximum_declared_presentations=24)
    assert [x.update_index for x in plan] == list(range(5, 13))
    for u in plan:
        assert u.nontraining_report() == p.proposal(
            run_seed=42, update_index=u.update_index, presentations=3,
        ).nontraining_report()


def test_prepared_one_time_index_requires_no_per_update_argsort(monkeypatch):
    p = prep()
    def forbidden(*args, **kwargs):
        raise AssertionError("full-dataset index recomputed after prepare")
    monkeypatch.setattr(np, "argsort", forbidden)
    for cursor in range(10):
        assert len(p.proposal(run_seed=42, update_index=cursor, presentations=3).selection_rows) == 3


def test_population_snapshot_is_not_physical_authority():
    p = prep()
    receipt = p.nontraining_report()
    assert receipt["input_authentication"] == "STRUCTURAL_SNAPSHOT_NO_BYTE_AUTHORITY_RECEIPT"
    assert receipt["training_authorized"] is False
    assert receipt["raw_level4_per_cell_binding_here"] is False
    assert receipt["source_mutations_after_snapshot_detected_here"] is False


def test_frozen_synthetic_input_mutation_after_prepare_does_not_change_snapshot():
    counts, names, codes = tiny()
    p = prep()
    first = p.proposal(run_seed=4, update_index=0, presentations=4)
    codes[:] = 0
    names[:] = "X"
    after = p.proposal(run_seed=4, update_index=0, presentations=4)
    assert np.array_equal(first.selection_rows, after.selection_rows)


def test_per_cursor_cell_uniqueness_and_marginal_q():
    p = prep()
    for cursor in range(40):
        got = p.proposal(run_seed=7, update_index=cursor, presentations=4)
        assert len(set(got.selection_rows.tolist())) == 4
        assert np.array_equal(p.donor_codes[got.selection_rows], got.donor_codes)
        assert np.array_equal(
            got.proposal_probabilities,
            1 / (len(p.donor_names) * p.donor_counts[got.donor_codes]),
        )
        assert np.array_equal(got.importance_weights, np.ones(4))


@pytest.mark.parametrize("bad", [5, 6, 100])
def test_capacity_violation_rejected_before_rng_draw(bad, monkeypatch):
    p = prep()
    def forbidden_rng(*args, **kwargs):
        raise AssertionError("RNG used before capacity preflight")
    monkeypatch.setattr(np.random, "PCG64", forbidden_rng)
    with pytest.raises(ValueError, match="smallest donor"):
        p.proposal(run_seed=0, update_index=0, presentations=bad)


@pytest.mark.parametrize("kwargs", [
    {"run_seed": True, "update_index": 0, "presentations": 1},
    {"run_seed": 0, "update_index": True, "presentations": 1},
    {"run_seed": 0, "update_index": 0, "presentations": 0},
    {"run_seed": 0, "update_index": -1, "presentations": 1},
])
def test_invalid_single_update_arguments_fail(kwargs):
    with pytest.raises(ValueError):
        prep().proposal(**kwargs)


def test_overflowing_schedule_and_zero_horizon_fail():
    p = prep()
    for args in (
        dict(run_seed=1, first_update_index=0, update_count=0, presentations_per_update=2,
             maximum_declared_presentations=100),
        dict(run_seed=1, first_update_index=0, update_count=1, presentations_per_update=5,
             maximum_declared_presentations=100),
        dict(run_seed=1, first_update_index=(1 << 63)-1, update_count=1, presentations_per_update=1,
             maximum_declared_presentations=100),
    ):
        with pytest.raises(ValueError):
            p.plan(**args)


def test_prepared_rejects_different_total_with_same_donor_names():
    counts, names, codes = tiny()
    with pytest.raises(ValueError):
        PreparedReaderFitProposal.structural_only(
            cell_donor=codes[:-1], donor_ids=names, expected_counts=counts,
            source_digest="a" * 64,
        )


def test_prepared_cannot_use_wrong_source_digest():
    counts, names, codes = tiny()
    with pytest.raises(ValueError, match="canonical lowercase"):
        PreparedReaderFitProposal.structural_only(
            cell_donor=codes, donor_ids=names, expected_counts=counts,
            source_digest="A" * 64,
        )


def test_real_factory_requires_actual_frozen_sources(tmp_path):
    with pytest.raises(FileNotFoundError):
        prepare_from_frozen_pass1(
            pass1_path=tmp_path / "historical_94donor.npz",
            calibration_zip=tmp_path / "fake_aug24_bundle.zip",
        )


def test_prepared_arrays_cannot_be_reopened_for_writing():
    p=prep()
    for field in ("donor_codes", "donor_counts", "ordered_rows", "offsets"):
        array=getattr(p,field)
        assert not array.flags.writeable
        with pytest.raises(ValueError):
            array.setflags(write=True)


def test_explicit_schedule_materialization_cap_enforced_before_rng(monkeypatch):
    p=prep()
    def forbidden_rng(*args, **kwargs):
        raise AssertionError("schedule allocated RNG before budget preflight")
    monkeypatch.setattr(np.random, "PCG64", forbidden_rng)
    with pytest.raises(ValueError, match="declared materialization limit"):
        p.plan(run_seed=1, first_update_index=0, update_count=10,
               presentations_per_update=4, maximum_declared_presentations=39)


def test_public_constructor_cannot_forge_physical_byte_binding():
    p=prep()
    with pytest.raises(TypeError):
        PreparedReaderFitProposal(
            p.donor_codes, p.donor_names, p.donor_counts,
            p.ordered_rows, p.offsets, p.source_digest,
            frozen_inputs_authenticated=True,
        )
    # Even this object carrying the exact-looking frozen SHA still cannot
    # issue an authenticated receipt without independent PR132 evidence.
    assert p.nontraining_report()["input_authentication"] == "STRUCTURAL_SNAPSHOT_NO_BYTE_AUTHORITY_RECEIPT"
