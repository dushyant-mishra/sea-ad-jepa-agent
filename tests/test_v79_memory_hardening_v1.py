import hashlib

import numpy as np
from scipy import sparse

from scripts.v79.v79_hierarchical_biology import generate_latent_biology
from scripts.v79.v79_observation_operator import observe_latent_biology
from scripts.v79.score_v79_factorial_worlds import (
    _sparse_hvg_material,
    _sparse_legacy_score,
    _sparse_l0_l2,
)
from scripts.v79 import v79_detection_localization as LOC
from scripts.v77 import build_v77_topology_calibration as TC
from scripts.v77 import v77_matched_scoring as V77


def _bio_authority():
    return {
        "class_frequencies": [0.4, 0.6],
        "substates_per_class": [2, 3],
        "substate_prevalence": [1.0, 1.0],
        "module_size_distribution": [5, 8],
        "n_modules_per_substate": 2,
        "n_continuous_factors": 3,
        "substate_effect_scale": 1.0,
        "continuous_factor_scale": 0.05,
        "donor_effect_scale": 0.05,
        "baseline_log_mean": -0.2,
        "baseline_log_sd": 0.2,
    }


def _obs_authority(n_genes=48, family="independent_thinning"):
    support = np.ones((2, n_genes), dtype=bool)
    support[1, ::4] = False
    return {
        "regime_ids": ["OBS_A", "OBS_B"],
        "structural_support": support.tolist(),
        "capture_log_mean": [-0.2, -0.8],
        "capture_log_sd": [0.15, 0.20],
        "gene_propensity": np.linspace(0.6, 1.4, n_genes).tolist(),
        "realization_family": family,
        "molecule_scale": 6.0,
    }


def _hash_array(x):
    return hashlib.sha256(np.ascontiguousarray(x).view(np.uint8)).hexdigest()


def _assert_nested_equivalent(a, b, *, path="root", atol=1e-12):
    if isinstance(a, dict):
        assert isinstance(b, dict), path
        assert set(a) == set(b), path
        for key in a:
            _assert_nested_equivalent(a[key], b[key], path=f"{path}.{key}", atol=atol)
        return
    if isinstance(a, (list, tuple)):
        assert isinstance(b, (list, tuple)), path
        assert len(a) == len(b), path
        for i, (x, y) in enumerate(zip(a, b)):
            _assert_nested_equivalent(x, y, path=f"{path}[{i}]", atol=atol)
        return
    if isinstance(a, np.ndarray):
        assert isinstance(b, np.ndarray), path
        assert a.shape == b.shape, path
        if np.issubdtype(a.dtype, np.number):
            assert np.allclose(a, b, rtol=0.0, atol=atol, equal_nan=True), path
        else:
            assert np.array_equal(a, b), path
        return
    if isinstance(a, (float, np.floating)):
        if np.isnan(a):
            assert np.isnan(b), path
        else:
            assert np.isclose(a, b, rtol=0.0, atol=atol), path
        return
    assert a == b, path


def test_streamed_biology_is_bit_exact_to_pre_hardening_fixture():
    z = generate_latent_biology(_bio_authority(), 160, 48, 8, seed=41)
    assert z.truth_hashes == {
        "broad_class": "987065942ff0ebd15a7ad43338b058f4584b3fab402a59d595408055814bc8cd",
        "substate": "1a70050b9a54ece91cb01bd64e6757ebe760e42b0c446895dfe4aad1d7226107",
        "donor": "764659a869deb30ccb2f7295a0d5d8874001d21a12dbee2239c1341712f7fb70",
        "continuous_factors": "191625ab8091b21bbb08883b29e622b2351776b5446646ff74bb5a4581493513",
        "latent_abundance": "710f4d4f80373fe57c7437c4b62bde9ed0ed0d3c8faf8e1ae133e28dafad23bb",
        "biological_total_scale": "0cfee6e945d4c44c249283faaa106a9b9c6a626725afc40e2eb196d350d3a1c5",
    }


def test_streamed_observer_is_bit_exact_to_pre_hardening_independent_thinning():
    z = generate_latent_biology(_bio_authority(), 160, 48, 8, seed=41)
    labels = np.resize(np.array(["OBS_A", "OBS_B"]), 160)
    out = observe_latent_biology(z, _obs_authority(family="independent_thinning"), labels, seed=77)
    assert out.counts_hash == "3d1f4e7a710d96d2328a5deea8fb1919a122aa7902206594a0609a9d53b59afa"
    regime_index = np.arange(160, dtype=np.int64) % 2
    cap_mean = np.asarray([-0.2, -0.8], dtype=np.float64)[regime_index]
    cap_sd = np.asarray([0.15, 0.20], dtype=np.float64)[regime_index]
    expected_capture = np.exp(np.random.default_rng(77).normal(cap_mean, cap_sd))
    assert np.array_equal(out.capture_efficiency, expected_capture)


def test_streamed_observer_is_bit_exact_to_pre_hardening_conditional_multinomial():
    z = generate_latent_biology(_bio_authority(), 160, 48, 8, seed=41)
    labels = np.resize(np.array(["OBS_A", "OBS_B"]), 160)
    out = observe_latent_biology(z, _obs_authority(family="conditional_multinomial"), labels, seed=77)
    assert out.counts_hash == "188bb6027eaf0ea41213c36f1988f4201b545c6f5ade866f8be61bce74ee4b9d"


def test_sparse_hvg_selection_matches_frozen_dense_rule_exactly_on_fixture():
    rng = np.random.default_rng(901)
    counts = sparse.csr_matrix(rng.poisson(0.25, size=(240, 180)).astype(np.int64))
    universe = np.arange(160, dtype=np.int64)
    lib = np.asarray(counts.sum(1)).ravel()
    C, hvg_idx, Ld, sel = TC.hvg_correlation(counts, lib, universe, 48)
    got = _sparse_hvg_material(counts, universe, 48)
    assert np.array_equal(got["sel"], sel)
    assert np.array_equal(got["hvg_idx"], hvg_idx)
    assert np.array_equal(got["Ld"], Ld[:, sel])
    assert np.allclose(got["C"], C, rtol=0.0, atol=1e-12)


def test_sparse_scoring_matches_pre_hardening_v77_and_l0_l2_endpoints():
    rng = np.random.default_rng(1901)
    counts = sparse.csr_matrix(rng.poisson(0.30, size=(480, 180)).astype(np.int64))
    universe = np.arange(160, dtype=np.int64)
    broad = np.repeat(np.array(["A", "B"]), 240)
    n_hvg = 48

    old_legacy = V77.score_matched(counts.toarray(), universe, broad, n_hvg=n_hvg)
    prepared = _sparse_hvg_material(counts, universe, n_hvg)
    new_legacy = _sparse_legacy_score(counts, universe, broad, n_hvg, prepared)
    _assert_nested_equivalent(old_legacy, new_legacy, path="legacy")

    old_loc = LOC.build_l0_l2(counts, universe, broad, n_hvg=n_hvg, retain_stratum_corr=True)
    new_loc = _sparse_l0_l2(LOC, counts, universe, broad, n_hvg, prepared)
    _assert_nested_equivalent(old_loc, new_loc, path="localization")
