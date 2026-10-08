"""The candidate search harness must observe EXACTLY as the inline/real observer does.

An earlier version of the harness omitted the registry-derived abundance prior that the real
observer carries. The same candidate then scored median |corr| 0.1396 through the harness and
0.3427 inline, and a whole calibration round was measured against the wrong object. It was
caught only because the two numbers disagreed obviously; a smaller discrepancy would have
passed unnoticed and silently mis-calibrated the generator.

These tests pin the equivalence so it cannot regress.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
V77 = ROOT / "scripts" / "v77"
sys.path.insert(0, str(V77))
sys.path.insert(0, str(ROOT / "scripts" / "v64"))


def _mod(name):
    spec = importlib.util.spec_from_file_location(name, V77 / f"{name}.py")
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


def test_harness_includes_the_abundance_prior():
    """The harness must apply the abundance prior; its absence was the original defect."""
    src = (V77 / "run_v77_background_search.py").read_text(encoding="utf-8")
    assert "ABUNDANCE" in src, "harness must define the abundance prior"
    assert "eta + ABUNDANCE" in src, (
        "harness must ADD the abundance prior to eta before observation, as the real observer does")


def test_harness_abundance_is_the_same_object_the_real_observer_uses():
    search = _mod("run_v77_background_search")
    AU = _mod("v77_address_universe")
    uni = AU.AddressUniverse(seed=7302)
    assert search.ABUNDANCE.shape == uni.log_abundance.shape
    assert np.allclose(search.ABUNDANCE, uni.log_abundance), (
        "the harness abundance prior must be the registry-derived one, not a substitute")


def test_harness_observation_equals_inline_observation_for_the_same_seed():
    """Same candidate, same seed, same abundance: harness and inline must agree exactly."""
    search = _mod("run_v77_background_search")
    CAND = _mod("v77_background_candidates")
    AU = _mod("v77_address_universe")

    n_cells, n_addr, seed = 40, 3000, 4242
    cfg = dict(note="t", layers=[dict(n=2, frac=0.6, scale=0.8)],
               coherent=True, sign_balance=0.5, mag_jitter=0.2,
               substitute_frac=0.0, substitute_size=1)
    eta, cls, _ = CAND.build_eta(cfg, n_cells, n_addr, seed)

    ab = AU.AddressUniverse(seed=7302).log_abundance.astype(np.float32)[:n_addr]
    inline = CAND.observe_counts(eta + ab[None, :], seed, k_detect=300)
    harness = CAND.observe_counts(eta + search.ABUNDANCE[:n_addr][None, :], seed, k_detect=300)
    assert np.array_equal(inline, harness), (
        "harness and inline observation diverged for identical seed and config")


def test_abundance_prior_is_load_bearing_not_decorative():
    """Removing the prior must measurably change the result, or the test above proves nothing."""
    CAND = _mod("v77_background_candidates")
    AU = _mod("v77_address_universe")
    n_cells, n_addr, seed = 60, 4000, 99
    cfg = dict(note="t", layers=[dict(n=2, frac=0.7, scale=0.9)],
               coherent=True, sign_balance=0.5, mag_jitter=0.2,
               substitute_frac=0.0, substitute_size=1)
    eta, _, _ = CAND.build_eta(cfg, n_cells, n_addr, seed)
    ab = AU.AddressUniverse(seed=7302).log_abundance.astype(np.float32)[:n_addr]
    with_ab = CAND.observe_counts(eta + ab[None, :], seed, k_detect=400)
    without = CAND.observe_counts(eta, seed, k_detect=400)
    assert not np.array_equal(with_ab, without), (
        "the abundance prior must change the observation; if it does not, the equivalence "
        "test above would pass vacuously")
