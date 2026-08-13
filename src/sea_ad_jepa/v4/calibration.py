"""Synthetic-only Stage81A3 variance and covariance calibration mechanics."""

from __future__ import annotations

from typing import Literal

import torch


VarianceFormulation = Literal["pooled_cell", "per_slot", "flattened_cell_slot", "combined"]
CovarianceFormulation = Literal["pooled_cell", "per_slot", "flattened_cell_slot"]


def _require_latents(latents: torch.Tensor) -> None:
    if latents.ndim != 3 or latents.shape[0] < 2:
        raise ValueError("latents must have shape [cells, slots, width] with at least two cells")
    if not latents.is_floating_point() or not torch.isfinite(latents).all():
        raise ValueError("latents must be finite floating-point values")


def _variance_hinge(values: torch.Tensor, gamma: float) -> torch.Tensor:
    std = values.std(dim=0, unbiased=False)
    return torch.relu(torch.as_tensor(gamma, dtype=values.dtype, device=values.device) - std).mean()


def variance_floor_calibration(
    latents: torch.Tensor,
    *,
    gamma: float,
    formulation: VarianceFormulation,
) -> torch.Tensor:
    """Compare raw-latent variance formulations without selecting production policy."""
    _require_latents(latents)
    if gamma < 0:
        raise ValueError("gamma must be non-negative")
    pooled = _variance_hinge(latents.mean(dim=1), gamma)
    per_slot = torch.relu(
        torch.as_tensor(gamma, dtype=latents.dtype, device=latents.device)
        - latents.std(dim=0, unbiased=False)
    ).mean()
    flattened = _variance_hinge(latents.reshape(-1, latents.shape[-1]), gamma)
    if formulation == "pooled_cell":
        return pooled
    if formulation == "per_slot":
        return per_slot
    if formulation == "flattened_cell_slot":
        return flattened
    if formulation == "combined":
        return 0.5 * (pooled + per_slot)
    raise ValueError(f"unknown variance formulation: {formulation}")


def _correlation_penalty(values: torch.Tensor, eps: float) -> torch.Tensor:
    if values.shape[0] < 2:
        raise ValueError("covariance requires at least two observations")
    centered = values - values.mean(dim=0, keepdim=True)
    covariance = centered.T @ centered / (values.shape[0] - 1)
    std = torch.sqrt(torch.diag(covariance).clamp_min(0) + eps)
    correlation = covariance / (std[:, None] * std[None, :] + eps)
    off_diagonal = correlation - torch.diag(torch.diag(correlation))
    width = values.shape[1]
    return off_diagonal.square().sum() / max(1, width * (width - 1))


def covariance_calibration(
    latents: torch.Tensor,
    *,
    formulation: CovarianceFormulation,
    eps: float = 1e-6,
) -> torch.Tensor:
    """Compare detached/training-capable correlation diagnostics synthetically."""
    _require_latents(latents)
    if eps <= 0:
        raise ValueError("eps must be positive")
    if formulation == "pooled_cell":
        return _correlation_penalty(latents.mean(dim=1), eps)
    if formulation == "per_slot":
        return torch.stack([
            _correlation_penalty(latents[:, slot], eps)
            for slot in range(latents.shape[1])
        ]).mean()
    if formulation == "flattened_cell_slot":
        return _correlation_penalty(latents.reshape(-1, latents.shape[-1]), eps)
    raise ValueError(f"unknown covariance formulation: {formulation}")


def gradient_l2_norm(loss: torch.Tensor, tensor: torch.Tensor) -> float:
    """Return a synthetic calibration gradient norm without retaining a graph."""
    gradient = torch.autograd.grad(loss, tensor, retain_graph=False)[0]
    return float(torch.linalg.vector_norm(gradient))
