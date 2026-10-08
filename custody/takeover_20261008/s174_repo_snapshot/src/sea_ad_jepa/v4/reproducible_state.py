"""Replicate-shared state-basis mechanics for the bounded Stage81A3 audit."""

from __future__ import annotations

from dataclasses import dataclass

import torch
import torch.nn.functional as F


@dataclass(frozen=True)
class ReproducibleBasis:
    mean: torch.Tensor
    vectors: torch.Tensor
    eigenvalues: torch.Tensor
    epsilon: float

    @property
    def analysis(self) -> torch.Tensor:
        return self.vectors / torch.sqrt(self.eigenvalues + self.epsilon)[:, None]

    def transform(self, values: torch.Tensor, *, whiten: bool = False) -> torch.Tensor:
        basis = self.analysis if whiten else self.vectors
        return (values.to(self.mean.dtype) - self.mean) @ basis.T

    def contribution(self, values: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
        return ((values.to(self.mean.dtype) - self.mean) * mask.to(self.mean.dtype)) @ self.analysis.T


@dataclass(frozen=True)
class PairMeanBasis:
    mean: torch.Tensor
    vectors: torch.Tensor

    def transform(self, values: torch.Tensor) -> torch.Tensor:
        return (values.float() - self.mean) @ self.vectors.T


def common_center(x_a_train: torch.Tensor, x_b_train: torch.Tensor) -> torch.Tensor:
    return 0.5 * (x_a_train.double().mean(0) + x_b_train.double().mean(0))


def shared_cross_covariance(x_a_train: torch.Tensor, x_b_train: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
    """Build the symmetric paired cross-covariance without label inputs."""
    mean = common_center(x_a_train, x_b_train)
    a = x_a_train.float() - mean.float()
    b = x_b_train.float() - mean.float()
    cross = a.T @ b / (len(a) - 1)
    shared = 0.5 * (cross + cross.T)
    return mean.float(), shared


def fit_reproducible_basis(
    x_a_train: torch.Tensor,
    x_b_train: torch.Tensor,
    *,
    components: int = 160,
    relative_threshold: float = 1e-8,
    absolute_floor: float = 1e-10,
) -> tuple[ReproducibleBasis | None, dict[str, torch.Tensor | float | int]]:
    mean, shared = shared_cross_covariance(x_a_train, x_b_train)
    eigenvalues, eigenvectors = torch.linalg.eigh(shared.double())
    order = torch.argsort(eigenvalues, descending=True)
    eigenvalues, eigenvectors = eigenvalues[order], eigenvectors[:, order]
    threshold = max(float(eigenvalues[0]) * relative_threshold, absolute_floor)
    positive = eigenvalues > threshold
    near_zero = eigenvalues.abs() <= threshold
    report: dict[str, torch.Tensor | float | int] = {
        "eigenvalues": eigenvalues,
        "positive_count": int(positive.sum()),
        "near_zero_count": int(near_zero.sum()),
        "negative_count": int((eigenvalues < -threshold).sum()),
        "threshold": threshold,
        "largest_eigenvalue": float(eigenvalues[0]),
    }
    if int(positive.sum()) < components:
        return None, report
    selected_values = eigenvalues[positive][:components]
    selected_vectors = eigenvectors[:, positive][:, :components].T
    basis = ReproducibleBasis(mean.double(), selected_vectors, selected_values, threshold)
    # Float64 Rayleigh parity checks the selected float32 eigensystem without a
    # second basis search or label-dependent adjustment.
    shared64, vectors64 = shared.double(), selected_vectors
    rayleigh = torch.einsum("ki,ij,kj->k", vectors64, shared64, vectors64)
    report["selected_rayleigh_values"] = rayleigh.float()
    report["maximum_relative_rayleigh_difference"] = float(
        ((rayleigh - selected_values.double()).abs() / selected_values.double().abs().clamp_min(1e-12)).max()
    )
    del shared64
    return basis, report


def fit_pairmean_pca(x_a_train: torch.Tensor, x_b_train: torch.Tensor, components: int = 160) -> PairMeanBasis:
    values = 0.5 * (x_a_train.float() + x_b_train.float())
    mean = values.mean(0)
    centered = values - mean
    gram = centered @ centered.T
    eigenvalues, left = torch.linalg.eigh(gram)
    order = torch.argsort(eigenvalues, descending=True)[:components]
    selected = eigenvalues[order].clamp_min(1e-10)
    vectors = (left[:, order].T @ centered) / torch.sqrt(selected)[:, None]
    return PairMeanBasis(mean, F.normalize(vectors, dim=1))


def column_correlation(first: torch.Tensor, second: torch.Tensor) -> torch.Tensor:
    a = first.float() - first.float().mean(0, keepdim=True)
    b = second.float() - second.float().mean(0, keepdim=True)
    denominator = torch.sqrt(a.square().sum(0) * b.square().sum(0))
    return torch.where(denominator > 0, (a * b).sum(0) / denominator, torch.nan)


def residual_prior(u_hidden_a: torch.Tensor, u_hidden_b: torch.Tensor) -> dict[str, torch.Tensor]:
    paired = 0.5 * (u_hidden_a.float() + u_hidden_b.float())
    difference = u_hidden_a.float() - u_hidden_b.float()
    prior_variance = paired.var(0, unbiased=True)
    noise_variance = 0.5 * difference.var(0, unbiased=True)
    return {
        "mean": paired.mean(0), "prior_variance": prior_variance,
        "noise_variance": noise_variance,
        "noise_fraction": noise_variance / (prior_variance + 1e-12),
    }
