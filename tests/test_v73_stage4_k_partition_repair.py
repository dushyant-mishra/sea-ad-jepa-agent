import importlib.util
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "scripts/v64/build_stage4_synthetic_worlds_v1.py"
RUNNER = ROOT / "scripts/v64/run_stage4_g2_sensitivity_curve_v1.py"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_exact_k_partition_occupies_every_requested_factor():
    b = load(BUILDER, "v73_stage4_builder")
    for K in (1, 5, 20, 50, 200):
        labels, sizes = b._balanced_confound_partition(
            K, b.N_EDGES, np.random.default_rng(7300 + K))
        assert len(labels) == b.N_EDGES
        assert len(sizes) == K
        assert np.count_nonzero(sizes) == K
        assert sizes.sum() == b.N_EDGES
        assert int(sizes.max()) - int(sizes.min()) <= 1


def test_k_equals_edge_count_is_exact_singleton_partition():
    b = load(BUILDER, "v73_stage4_builder_singletons")
    labels, sizes = b._balanced_confound_partition(
        b.N_EDGES, b.N_EDGES, np.random.default_rng(73200))
    assert sorted(labels.tolist()) == list(range(b.N_EDGES))
    assert np.all(sizes == 1)


def test_partition_is_seeded_but_block_sizes_are_invariant():
    b = load(BUILDER, "v73_stage4_builder_seeded")
    labels_a, sizes_a = b._balanced_confound_partition(
        20, b.N_EDGES, np.random.default_rng(1))
    labels_b, sizes_b = b._balanced_confound_partition(
        20, b.N_EDGES, np.random.default_rng(2))
    assert np.array_equal(sizes_a, sizes_b)
    assert not np.array_equal(labels_a, labels_b)


def test_runner_fails_closed_on_realised_occupancy_not_just_requested_k():
    text = RUNNER.read_text()
    assert "EXACT_K_OCCUPIED_BALANCED_BLOCKS" in text
    assert 'd["realised_occupied_factors"] != K' in text
    assert "endpoint_singletons_verified" in text
    assert "requested factor-pool size" in text


def test_runner_marks_historical_curve_superseded_for_partition_inference():
    text = RUNNER.read_text()
    assert "V64_STAGE4_G2_SENSITIVITY_CURVE_V2_PARTITION_REPAIRED" in text
    assert "sampling-with-replacement block" in text
    assert "must not support that interpretation" in text
