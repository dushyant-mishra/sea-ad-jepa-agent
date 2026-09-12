#!/usr/bin/env python3
"""Qualification for the transport estimand's algebra.

The study that evaluates the estimand is only as trustworthy as the arithmetic it
measures with, so the identities are pinned against real fits before any arm is
believed.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pytest

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import t0_v21_selection_and_power_v1 as v21  # noqa: E402
import t0_v21_transport_estimand_v1 as T  # noqa: E402

N = 28


def _design(n=N):
    _, learner = v21._frozen()
    age = np.linspace(66.0, 94.0, n)
    sex = np.array([float(i % 2) for i in range(n)])
    z, _ = learner.nuisance_design(age, sex)
    return z


def test_the_partial_correlation_to_t_identity():
    """t = r sqrt(n - p_Z - 1) / sqrt(1 - r^2), exactly, for a fixed predictor.

    This is the identity the whole null-calibration check rests on. An earlier
    version used sqrt(n - p_Z), which is the population noncentrality's scaling,
    and inflated every implied t by 2.1% at n = 28.
    """
    z = _design()
    rng = np.random.default_rng(0)
    for _ in range(8):
        x = rng.normal(size=N)
        y = z @ np.array([1.0, 0.02, 0.0005, 0.3]) + 0.8 * x + rng.normal(size=N)
        full = np.c_[z, x]
        beta = np.linalg.lstsq(full, y, rcond=None)[0]
        residual = y - full @ beta
        df = N - full.shape[1]
        sigma2 = float(residual @ residual) / df
        se = math.sqrt(sigma2 * float(np.linalg.inv(full.T @ full)[-1, -1]))
        t_ols = float(beta[-1]) / se

        rho = T.partial_correlation(y=y, nuisance=z, score=x)
        assert T.implied_t(rho, N) == pytest.approx(t_ols, rel=1e-9)


def test_implied_t_is_not_the_population_noncentrality():
    """They differ by sqrt((n - p_Z) / (n - p_Z - 1)); conflating them is a bug."""
    rho = 0.4
    assert T.implied_t(rho, N) != pytest.approx(T.noncentrality(rho, N),
                                                rel=1e-6)
    assert T.noncentrality(rho, N) / T.implied_t(rho, N) == pytest.approx(
        math.sqrt((N - 4) / (N - 5)), rel=1e-12)


def test_partial_correlation_is_scale_and_sign_equivariant():
    """Ridge rescales the score freely, so rho must not care."""
    z = _design()
    rng = np.random.default_rng(1)
    x = rng.normal(size=N)
    y = rng.normal(size=N) + 0.5 * x
    base = T.partial_correlation(y=y, nuisance=z, score=x)
    assert T.partial_correlation(y=y, nuisance=z, score=17.0 * x) == (
        pytest.approx(base, rel=1e-12))
    assert T.partial_correlation(y=y, nuisance=z, score=-x) == (
        pytest.approx(-base, rel=1e-12))


def test_partial_correlation_ignores_the_nuisance_span():
    """Adding any nuisance-column multiple to the score changes nothing."""
    z = _design()
    rng = np.random.default_rng(2)
    x = rng.normal(size=N)
    y = rng.normal(size=N) + 0.5 * x
    base = T.partial_correlation(y=y, nuisance=z, score=x)
    polluted = x + 3.0 * z[:, 1] - 2.0 * z[:, 3]
    assert T.partial_correlation(y=y, nuisance=z, score=polluted) == (
        pytest.approx(base, rel=1e-12))


def test_power_is_monotone_in_rho_and_in_n():
    a = T.parametric_power(rho=0.3, n=12, alpha=0.025)["power"]
    b = T.parametric_power(rho=0.6, n=12, alpha=0.025)["power"]
    c = T.parametric_power(rho=0.6, n=28, alpha=0.025)["power"]
    assert a < b < c


def test_rho_for_power_inverts_parametric_power():
    for n in (12, 28):
        rho = T.rho_for_power(target_power=0.80, n=n, alpha=0.025)
        assert T.parametric_power(rho=rho, n=n,
                                  alpha=0.025)["power"] == pytest.approx(
            0.80, abs=0.01)


def test_degenerate_inputs_fail_closed():
    z = _design()
    with pytest.raises(RuntimeError):
        T.partial_correlation(y=np.zeros(N), nuisance=z, score=np.ones(N))
    with pytest.raises(RuntimeError):
        T.noncentrality(1.0, 28)
    with pytest.raises(RuntimeError):
        T.implied_t(0.5, 5)
