from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "v4"))

import d1_resampling_engine_v2 as engine  # noqa: E402
from d1_real_data_derivation_core_v1 import INSUFFICIENT_MC, derive_production_D  # noqa: E402


class Source:
    population_class = "PRODUCTION_FULL_FIT"

    def __init__(self, *, donors=12, cells=30, dimension=3, signal=20.0, seed=7):
        rng = np.random.default_rng(seed)
        direction = np.array([1.0, 1.5, -0.5], dtype=float)[:dimension]
        direction /= np.linalg.norm(direction)
        self._blocks = {}
        for d in range(donors):
            latent = rng.normal(size=(cells, 1))
            noise = rng.normal(scale=1.0, size=(cells, dimension))
            block = noise + signal * latent * direction[None, :]
            self._blocks[(f"D{d:02d}", 0)] = block.astype(np.float32)
        self.load_calls = 0

    def strata(self):
        return sorted(self._blocks)

    def donors(self):
        return sorted({d for d, _ in self._blocks})

    def total_cells(self):
        return sum(len(v) for v in self._blocks.values())

    def load(self, donor, operator):
        self.load_calls += 1
        block = self._blocks[(str(donor), int(operator))]
        # one operator per donor, so donor mass is exactly one
        weights = np.full(len(block), 1.0 / len(block), dtype=np.float64)
        return block, weights


def test_moment_bank_and_merge_match_direct_covariance() -> None:
    source = Source(donors=4, cells=20, signal=3.0)
    bank = engine.build_real_donor_moment_bank(source, 3)
    merged = engine.merge_many(list(bank.values()), 3)
    all_states = np.concatenate([source._blocks[k] for k in source.strata()], axis=0)
    weights = np.concatenate([
        np.full(len(source._blocks[k]), 1.0 / len(source._blocks[k]))
        for k in source.strata()
    ])
    direct = engine.summary_from_block(all_states, weights)
    assert np.allclose(merged.mean, direct.mean, atol=1e-12)
    assert np.allclose(merged.covariance(), direct.covariance(), atol=1e-12)


def test_real_bootstrap_never_reloads_cell_states() -> None:
    source = Source(donors=5, cells=12, signal=5.0)
    bank = engine.build_real_donor_moment_bank(source, 3)
    calls_after_bank = source.load_calls
    donors = sorted(bank)
    for r in range(20):
        sample = engine._donor_bootstrap_sample(donors, "test", r)
        engine._eigen_from_bank(bank, 3, sample=sample)
    assert source.load_calls == calls_after_bank


def test_one_expensive_state_pass_per_null_replicate() -> None:
    source = Source(donors=4, cells=10, signal=4.0)
    bank = engine.build_real_donor_moment_bank(source, 3)
    calls_after_real = source.load_calls
    for r in range(7):
        null = engine.build_null_donor_moment_bank(
            source, 3, namespace="null", replicate=r)
        engine._eigen_from_bank(null, 3)
    assert source.load_calls - calls_after_real == 7 * len(source.strata())


def test_precision_measures_monte_carlo_endpoint_error_not_null_spread() -> None:
    # Each interleaved batch sees exactly the same wide empirical distribution.
    pattern = np.array([-100.0, -5.0, 0.0, 2.0, 9.0, 100.0, 1000.0, 5000.0])
    values = np.tile(pattern, 64)[:, None]
    out = engine._batch_endpoint_precision(
        values, quantile=0.95, confidence_level=0.95,
        target_half_width=1e-12, batches=8)
    assert np.ptp(values[:, 0]) > 1000
    assert out["met"] is True
    assert out["max_half_width"] == pytest.approx(0.0)


def test_degeneracy_prefix_cannot_be_rescued_by_later_boundary() -> None:
    # [[0],[1,2]] -> admissible boundaries 1 and 3. Rank 1 failure is terminal.
    with pytest.raises(AssertionError):
        derive_production_D(
            D_PA=3,
            stability_separated_by_rank=[False, False, True],
            degeneracy_blocks=[[0], [1, 2]],
        )
    # If the unresolved block itself is leading, 3 is the first admissible rank.
    out = derive_production_D(
        D_PA=3,
        stability_separated_by_rank=[False, False, True],
        degeneracy_blocks=[[0, 1, 2]],
    )
    assert out["D"] == 3


def test_incremental_engine_recovers_one_very_strong_component(tmp_path: Path) -> None:
    source = Source(donors=16, cells=40, dimension=3, signal=40.0, seed=11)
    out = engine.derive_D_incremental(
        source, 3,
        archive_root_sha256="a" * 64,
        rng_namespace="known-answer",
        confidence_level=0.95,
        minimum_replicates=32,
        maximum_replicates=64,
        # This test is about assembly/decision topology, not calibrating a
        # production precision number.
        precision_target_half_width=1e6,
        state_dir=tmp_path / "state",
    )
    assert out["terminal"] == "PASS_D1_V2_D_DERIVATION"
    assert out["D"] == 1
    assert out["K"] == 1
    assert out["D_PA"] >= 1
    # Real cell states were read once to build the donor bank and once per
    # generated null replicate. No real-bootstrap rereads occur.
    assert source.load_calls == len(source.strata()) * (
        1 + out["monte_carlo_replicates"])


def test_ceiling_without_precision_is_a_hard_stop(tmp_path: Path) -> None:
    source = Source(donors=12, cells=20, dimension=3, signal=20.0, seed=3)
    with pytest.raises(AssertionError, match=INSUFFICIENT_MC):
        engine.derive_D_incremental(
            source, 3,
            archive_root_sha256="b" * 64,
            rng_namespace="precision-stop",
            minimum_replicates=32,
            maximum_replicates=32,
            precision_target_half_width=0.0,
            state_dir=tmp_path / "state",
        )


def test_resampling_state_hash_prevents_resume_under_different_archive(tmp_path: Path) -> None:
    source = Source(donors=12, cells=20, dimension=3, signal=20.0, seed=5)
    state = tmp_path / "state"
    # First call writes its 32-replicate checkpoint even if the zero tolerance
    # forces a terminal precision stop.
    with pytest.raises(AssertionError):
        engine.derive_D_incremental(
            source, 3,
            archive_root_sha256="c" * 64,
            rng_namespace="resume",
            minimum_replicates=32,
            maximum_replicates=32,
            precision_target_half_width=0.0,
            state_dir=state,
        )
    with pytest.raises(ValueError, match=engine.STOP_RESAMPLING_STATE_DRIFT):
        engine.derive_D_incremental(
            source, 3,
            archive_root_sha256="d" * 64,
            rng_namespace="resume",
            minimum_replicates=32,
            maximum_replicates=64,
            precision_target_half_width=0.0,
            state_dir=state,
        )
