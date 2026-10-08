from __future__ import annotations

import inspect
import math
import sys
from pathlib import Path

import torch

PROJECT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT / "src"))

from sea_ad_jepa.v4.belief_geometry import (  # noqa: E402
    covariance,
    diagonal_gaussian_nll,
    fixed_stabilizer,
    full_gaussian_nll,
    mahalanobis_diagonal,
    measurement_noise_covariance,
    offdiag_energy_fraction,
)


def test_basis_hash_is_locked_in_config() -> None:
    text = (PROJECT / "configs/v4/stage81a3_rbb_belief_geometry_audit.yaml").read_text()
    assert "ea07915a043ed8b8c3e38fe56ba2e3b9095bf4f0db3804773ae9394f3fbeab9c" in text


def test_covariance_accepts_values_only() -> None:
    assert set(inspect.signature(covariance).parameters) == {"values"}


def test_runner_uses_train_slice_for_covariance() -> None:
    text = (PROJECT / "scripts/v4/stage81a3_rbb_belief_geometry_audit.py").read_text()
    assert "[:TRAIN]" in text and "[-TEST:]" in text


def test_covariance_is_symmetric() -> None:
    matrix = covariance(torch.randn(30, 5))
    torch.testing.assert_close(matrix, matrix.T, rtol=0, atol=0)


def test_noise_covariance_has_half_factor() -> None:
    a, b = torch.randn(30, 5), torch.randn(30, 5)
    torch.testing.assert_close(measurement_noise_covariance(a, b), .5 * covariance(a - b))


def test_stabilized_diagonal_is_positive() -> None:
    matrix = covariance(torch.randn(30, 5))
    assert torch.all(torch.diag(matrix) + fixed_stabilizer(matrix) > 0)


def test_offdiag_energy_known_reference() -> None:
    matrix = torch.tensor([[2.0, 1.0], [1.0, 2.0]])
    assert abs(offdiag_energy_fraction(matrix) - .2) < 1e-7


def test_diagonal_nll_known_reference() -> None:
    values = torch.zeros(3, 2); variance = torch.ones(2)
    expected = math.log(2 * math.pi)
    torch.testing.assert_close(diagonal_gaussian_nll(values, variance), torch.full((3,), expected, dtype=torch.float64))


def test_full_nll_matches_diagonal_for_identity_up_to_fixed_ridge() -> None:
    values = torch.zeros(3, 2); matrix = torch.eye(2)
    result, ridge = full_gaussian_nll(values, matrix)
    expected = math.log(2 * math.pi) + math.log1p(ridge)
    torch.testing.assert_close(result, torch.full((3,), expected, dtype=torch.float64), atol=1e-10, rtol=1e-10)


def test_mahalanobis_diagonal_known_reference() -> None:
    values = torch.tensor([[1.0, 2.0]]); variance = torch.tensor([1.0, 4.0])
    torch.testing.assert_close(mahalanobis_diagonal(values, variance), torch.tensor([2.0], dtype=torch.float64))


def test_ridge_target_has_no_factor_api() -> None:
    from sea_ad_jepa.v4.conditional_predictability import ridge_fit
    assert "factors" not in inspect.signature(ridge_fit).parameters


def test_expected_state_is_not_uncertainty_fit_input() -> None:
    text = (PROJECT / "scripts/v4/stage81a3_rbb_belief_geometry_audit.py").read_text()
    assert "r_expected" not in text or "evaluation_only" in text


def test_factor_labels_are_evaluation_only() -> None:
    text = (PROJECT / "configs/v4/stage81a3_rbb_belief_geometry_audit.yaml").read_text()
    assert "factor_labels_in_fitting: forbidden" in text


def test_runner_has_no_real_rna_surface() -> None:
    text = (PROJECT / "scripts/v4/stage81a3_rbb_belief_geometry_audit.py").read_text().lower()
    assert "h5ad" not in text and "real_rna_accessed\": false" in text


def test_runner_has_no_pathology_surface() -> None:
    text = (PROJECT / "scripts/v4/stage81a3_rbb_belief_geometry_audit.py").read_text().lower()
    assert "data/pathology" not in text and "pathology_opened\": false" in text


def test_reporting_separates_geometry_trigger_from_estimator_readiness() -> None:
    text = (PROJECT / "scripts/v4/stage81a3_rbb_belief_geometry_audit.py").read_text()
    assert '"correlation_trigger_pass"' in text
    assert '"full_covariance_nll_trigger_pass"' in text
    assert '"naive_full_covariance_deployment_supported"' in text
    assert "unregularized full-covariance estimator worsens SEALED NLL" in text
    assert '"median_coordinate_standardized_error_variance"' in text
    assert "conditional-reference calibration failure" in text


def test_runner_binds_global_rng_before_fixture_generation() -> None:
    text = (PROJECT / "scripts/v4/stage81a3_rbb_belief_geometry_audit.py").read_text()
    seed_position = text.index("torch.manual_seed(SEED)")
    fixture_position = text.index("fixture = build_fixture(device)")
    assert seed_position < fixture_position
    assert "torch.cuda.manual_seed_all(SEED)" in text
    assert '"global_rng_bound_before_generation": True' in text


def test_prior_nll_absence_is_explicitly_not_applicable() -> None:
    text = (PROJECT / "scripts/v4/stage81a3_rbb_belief_geometry_audit.py").read_text()
    assert '"nll_evaluation_status": "not_applicable_prior" if kind == "prior" else "pending"' in text
    assert text.count('"nll_evaluation_status": "sealed_scored"') == 2
