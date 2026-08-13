"""Closed-form belief-distribution geometry for the bounded Stage81A3 audit."""

from __future__ import annotations

import math

import torch


def covariance(values: torch.Tensor) -> torch.Tensor:
    centered = values.double() - values.double().mean(0, keepdim=True)
    result = centered.T @ centered / (len(centered) - 1)
    return 0.5 * (result + result.T)


def measurement_noise_covariance(r_a: torch.Tensor, r_b: torch.Tensor) -> torch.Tensor:
    return 0.5 * covariance(r_a - r_b)


def fixed_stabilizer(matrix: torch.Tensor) -> float:
    return 1.0e-4 * float(torch.diag(matrix).mean())


def offdiag_energy_fraction(matrix: torch.Tensor) -> float:
    diagonal = torch.diag(torch.diag(matrix))
    return float((matrix - diagonal).square().sum() / matrix.square().sum().clamp_min(1e-30))


def correlation_matrix(matrix: torch.Tensor) -> torch.Tensor:
    scale = torch.sqrt(torch.diag(matrix).clamp_min(1e-30))
    return matrix / (scale[:, None] * scale[None, :])


def eigenspectrum_summary(matrix: torch.Tensor) -> dict[str, float]:
    values = torch.linalg.eigvalsh(matrix.double()).flip(0).clamp_min(0)
    total = values.sum().clamp_min(1e-30)
    probabilities = values / total
    positive = probabilities > 0
    effective_rank = torch.exp(-(probabilities[positive] * probabilities[positive].log()).sum())
    output = {
        "effective_rank": float(effective_rank),
        "top_1_fraction": float(values[:1].sum() / total),
    }
    for count in (4, 8, 16, 32, 64):
        output[f"top_{count}_cumulative_fraction"] = float(values[:count].sum() / total)
    return output


def diagonal_gaussian_nll(values: torch.Tensor, variance: torch.Tensor) -> torch.Tensor:
    variance = variance.double().clamp_min(1e-30)
    return 0.5 * (math.log(2 * math.pi) + variance.log() + values.double().square() / variance).sum(1)


def full_gaussian_nll(values: torch.Tensor, matrix: torch.Tensor) -> tuple[torch.Tensor, float]:
    ridge = fixed_stabilizer(matrix)
    stabilized = matrix.double() + ridge * torch.eye(matrix.shape[0], device=matrix.device, dtype=torch.float64)
    cholesky = torch.linalg.cholesky(stabilized)
    solution = torch.cholesky_solve(values.double().T, cholesky).T
    quadratic = (values.double() * solution).sum(1)
    logdet = 2.0 * torch.log(torch.diag(cholesky)).sum()
    nll = 0.5 * (matrix.shape[0] * math.log(2 * math.pi) + logdet + quadratic)
    return nll, ridge


def mahalanobis_diagonal(values: torch.Tensor, variance: torch.Tensor) -> torch.Tensor:
    return (values.double().square() / variance.double().clamp_min(1e-30)).sum(1)


def mahalanobis_full(values: torch.Tensor, matrix: torch.Tensor) -> torch.Tensor:
    ridge = fixed_stabilizer(matrix)
    stabilized = matrix.double() + ridge * torch.eye(matrix.shape[0], device=matrix.device, dtype=torch.float64)
    cholesky = torch.linalg.cholesky(stabilized)
    solution = torch.cholesky_solve(values.double().T, cholesky).T
    return (values.double() * solution).sum(1)


def marginal_shape(values: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
    centered = values.double() - values.double().mean(0, keepdim=True)
    std = centered.std(0, unbiased=False).clamp_min(1e-30)
    standardized = centered / std
    return standardized.pow(3).mean(0), standardized.pow(4).mean(0) - 3.0
