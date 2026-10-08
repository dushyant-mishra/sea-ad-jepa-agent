"""Validation-calibrated covariance and analytic OAS mechanics."""

from __future__ import annotations

import math

import torch


def oas_covariance(values: torch.Tensor) -> tuple[torch.Tensor, float, float]:
    """Return the analytic Oracle Approximating Shrinkage covariance."""
    centered = values.double() - values.double().mean(0, keepdim=True)
    n_samples, n_features = centered.shape
    empirical = centered.T @ centered / n_samples
    mu = torch.trace(empirical) / n_features
    alpha = empirical.square().mean()
    numerator = alpha + mu.square()
    denominator = (n_samples + 1.0) * (alpha - mu.square() / n_features)
    shrinkage = 1.0 if float(denominator) == 0 else min(float(numerator / denominator), 1.0)
    result = (1.0 - shrinkage) * empirical
    result = result + shrinkage * mu * torch.eye(n_features, dtype=torch.float64, device=values.device)
    return 0.5 * (result + result.T), shrinkage, float(mu)


def dense_gaussian_terms(
    residuals: torch.Tensor,
    covariance: torch.Tensor,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    matrix = covariance.double()
    cholesky = torch.linalg.cholesky(matrix)
    values = residuals.double()
    solution = torch.cholesky_solve(values.T, cholesky).T
    quadratic = (values * solution).sum(1)
    logdet = 2.0 * torch.log(torch.diag(cholesky)).sum()
    nll = 0.5 * (values.shape[1] * math.log(2 * math.pi) + logdet + quadratic)
    return nll, quadratic, logdet
