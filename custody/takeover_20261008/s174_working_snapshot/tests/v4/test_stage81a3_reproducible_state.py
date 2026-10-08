from __future__ import annotations

import inspect
import sys
from pathlib import Path

import torch

PROJECT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT / "src"))

from sea_ad_jepa.v4.reproducible_state import (  # noqa: E402
    common_center,
    fit_pairmean_pca,
    fit_reproducible_basis,
    residual_prior,
    shared_cross_covariance,
)


def paired_fixture():
    torch.manual_seed(4)
    state = torch.randn(80, 12) @ torch.randn(12, 40)
    return state + .1 * torch.randn_like(state), state + .1 * torch.randn_like(state)


def test_common_center_is_pair_mean_of_training_means() -> None:
    a, b = paired_fixture()
    torch.testing.assert_close(common_center(a, b), .5 * (a.double().mean(0) + b.double().mean(0)))


def test_shared_covariance_matches_declared_formula() -> None:
    a, b = paired_fixture(); mean, covariance = shared_cross_covariance(a, b)
    cross = (a - mean).T @ (b - mean) / (len(a) - 1)
    torch.testing.assert_close(covariance, .5 * (cross + cross.T), rtol=1e-5, atol=1e-5)


def test_shared_covariance_is_symmetric() -> None:
    _, covariance = shared_cross_covariance(*paired_fixture())
    torch.testing.assert_close(covariance, covariance.T, rtol=0, atol=0)


def test_basis_fit_has_no_factor_label_api() -> None:
    parameters = set(inspect.signature(fit_reproducible_basis).parameters)
    assert "factors" not in parameters and "labels" not in parameters


def test_reppca_rows_are_orthonormal() -> None:
    basis, _ = fit_reproducible_basis(*paired_fixture(), components=8)
    torch.testing.assert_close(
        basis.vectors @ basis.vectors.T,
        torch.eye(8, dtype=basis.vectors.dtype), atol=1e-5, rtol=1e-5,
    )


def test_whitening_is_invertible_rescaling() -> None:
    basis, _ = fit_reproducible_basis(*paired_fixture(), components=8)
    values = torch.randn(5, 40)
    z = basis.transform(values)
    u = basis.transform(values, whiten=True)
    torch.testing.assert_close(u * torch.sqrt(basis.eigenvalues + basis.epsilon), z, atol=1e-5, rtol=1e-5)


def test_visible_plus_hidden_equals_full() -> None:
    basis, _ = fit_reproducible_basis(*paired_fixture(), components=8)
    values = torch.randn(5, 40); visible = torch.tensor([1] * 24 + [0] * 16).bool()
    torch.testing.assert_close(
        basis.transform(values, whiten=True),
        basis.contribution(values, visible) + basis.contribution(values, ~visible),
        atol=1e-5, rtol=1e-5,
    )


def test_pairmean_control_has_no_labels() -> None:
    assert "factors" not in inspect.signature(fit_pairmean_pca).parameters


def test_residual_prior_matches_formula() -> None:
    a, b = torch.randn(20, 6), torch.randn(20, 6)
    result = residual_prior(a, b)
    torch.testing.assert_close(result["prior_variance"], (.5 * (a + b)).var(0, unbiased=True))
    torch.testing.assert_close(result["noise_variance"], .5 * (a - b).var(0, unbiased=True))


def test_no_neural_optimizer_or_pathology_surface() -> None:
    source = (PROJECT / "src/sea_ad_jepa/v4/reproducible_state.py").read_text().lower()
    assert "torch.optim" not in source and "pathology" not in source
    assert "nn.module" not in source and "from torch import nn" not in source


def test_runner_declares_no_real_rna_or_training() -> None:
    source = (PROJECT / "configs/v4/stage81a3_reproducible_state_basis.yaml").read_text()
    assert "real_rna: forbidden" in source and "jepa_training: forbidden" in source
