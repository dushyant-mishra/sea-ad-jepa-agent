import importlib.util
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "v5" / "run_td_bayesian_synthetic_calibration.py"


def load_module():
    spec = importlib.util.spec_from_file_location("td_bayes_cal", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_frozen_scenario_geometry_and_values():
    m = load_module()
    assert m.BLOCK_KEYS == (
        ("A", "HVS"),
        ("A", "NPH52"),
        ("A", "SEA_AD"),
        ("B", "HVS"),
        ("C", "HVS"),
        ("C", "NPH52"),
        ("C", "SEA_AD"),
    )
    assert np.array_equal(m.SCENARIOS["S0"], np.zeros(7))
    assert np.array_equal(m.SCENARIOS["S1"], np.array([2.0, 0.0, 0.0, 2.0, 2.0, 0.0, 0.0]))
    assert np.array_equal(m.SCENARIOS["S3"], np.array([2.0, -2.0, 2.0, 2.0, 2.0, -2.0, 2.0]))
    assert np.array_equal(m.SCENARIOS["S4"], np.full(7, 2.0))


def test_source_effect_parameterization_is_exactly_zero_sum():
    m = load_module()
    theta = np.array([0.1, -0.2, 0.3, 1.2, -0.4, np.log(0.7), np.log(0.9)])
    state = m.unpack(theta)
    assert state["beta"].sum() == pytest.approx(0.0, abs=1e-14)
    assert state["tau_source"] == pytest.approx(0.7)
    assert state["sigma"] == pytest.approx(0.9)


def test_null_log_posterior_is_sign_symmetric_for_location_effects():
    m = load_module()
    y = m.SCENARIOS["S0"]
    prior = m.PRIOR_REGIMES["reference"]
    theta = np.array([0.2, -0.1, 0.3, 0.25, -0.15, np.log(0.8), np.log(1.1)])
    mirror = theta.copy()
    mirror[:5] *= -1
    assert m.log_posterior(theta, y, prior) == pytest.approx(m.log_posterior(mirror, y, prior), abs=1e-12)


def test_sampler_is_seed_deterministic_and_retains_expected_shape():
    m = load_module()
    y = m.SCENARIOS["S0"]
    prior = m.PRIOR_REGIMES["reference"]
    a = m.run_chain(y, prior, seed=123, draws=800, burn=200, thin=3)
    b = m.run_chain(y, prior, seed=123, draws=800, burn=200, thin=3)
    assert np.array_equal(a["samples"], b["samples"])
    assert a["samples"].shape == (200, 7)
    assert 0.0 <= a["acceptance"] <= 1.0


def test_diagnostics_are_finite_for_well_mixed_synthetic_chains():
    m = load_module()
    rng = np.random.default_rng(7)
    chains = rng.normal(size=(4, 1000, 7))
    diag = m.chain_diagnostics(chains)
    assert len(diag["split_rhat"]) == 7
    assert len(diag["ess"]) == 7
    assert max(diag["split_rhat"]) < 1.05
    assert min(diag["ess"][:3]) > 200


def test_reference_criteria_logic_matches_frozen_contract():
    m = load_module()
    good = {
        "S0": {s: {"p_mu_gt_zero": 0.5, "p_pred_gt_zero": 0.5, "q05": -0.2, "q95": 0.2} for s in "ABC"},
        "S1": {
            "A": {"p_mu_gt_zero": 0.75, "p_pred_gt_zero": 0.65, "q05": -0.1, "q95": 0.5},
            "B": {"p_mu_gt_zero": 0.9, "p_pred_gt_zero": 0.8, "q05": 0.0, "q95": 1.0},
            "C": {"p_mu_gt_zero": 0.8, "p_pred_gt_zero": 0.7, "q05": -0.1, "q95": 0.6},
        },
        "S3": {
            "A": {"p_mu_gt_zero": 0.9, "p_pred_gt_zero": 0.7, "q05": -0.2, "q95": 1.0},
            "B": {"p_mu_gt_zero": 0.9, "p_pred_gt_zero": 0.8, "q05": 0.0, "q95": 1.0},
            "C": {"p_mu_gt_zero": 0.92, "p_pred_gt_zero": 0.75, "q05": -0.1, "q95": 1.1},
        },
        "S4": {
            "A": {"p_mu_gt_zero": 0.99, "p_pred_gt_zero": 0.92, "q05": 0.8, "q95": 2.8},
            "B": {"p_mu_gt_zero": 0.95, "p_pred_gt_zero": 0.85, "q05": 0.2, "q95": 3.0},
            "C": {"p_mu_gt_zero": 0.98, "p_pred_gt_zero": 0.91, "q05": 0.7, "q95": 2.7},
        },
    }
    verdicts = m.evaluate_scientific_criteria(good, duplicate_rejected=True)
    assert all(verdicts.values())
    bad = {k: {s: dict(v) for s, v in stage.items()} for k, stage in good.items()}
    bad["S1"]["A"]["p_pred_gt_zero"] = 0.95
    assert m.evaluate_scientific_criteria(bad, duplicate_rejected=True)["C1_one_source_resistance"] is False
