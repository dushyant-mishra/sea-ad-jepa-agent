"""Transparent representation-health telemetry for synthetic Stage81A3 tests."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

import torch
import torch.nn.functional as F
from torch import nn

from .ema import ema_target_module


@dataclass(frozen=True)
class RepresentationHealth:
    cross_cell_std_mean: float
    cross_cell_std_min: float
    cross_cell_std_max: float
    effective_rank: float
    singular_values: tuple[float, ...]
    top_singular_l1_fraction: float
    top_singular_energy_fraction: float
    latent_norm_mean: float
    latent_norm_std: float
    latent_norm_min: float
    latent_norm_max: float
    pairwise_distance_mean: float
    pairwise_distance_median: float
    pairwise_distance_p05: float
    pairwise_distance_p95: float
    slot_variance_mean: float
    slot_cosine_similarity_mean: float


@dataclass(frozen=True)
class EMAParameterHealth:
    online_target_parameter_l2_distance: float
    online_parameter_l2_norm: float
    target_parameter_l2_norm: float
    normalized_online_target_distance: float
    parameter_count: int


@dataclass(frozen=True)
class EMAUpdateTelemetry:
    target_update_l2_norm: float
    online_step_l2_norm: float
    pre_update_online_target_gap: float
    target_follow_fraction: float
    post_update_online_target_gap: float


@dataclass(frozen=True)
class TargetLatentHealth:
    variance_mean: float
    variance_min: float
    variance_max: float
    std_mean: float
    std_min: float
    std_max: float


def singular_spectrum_metrics(
    singular_values: torch.Tensor,
    *,
    zero_tolerance: float | None = None,
) -> dict[str, float]:
    """Return effective rank and two explicitly distinct concentration metrics."""
    if singular_values.ndim != 1 or singular_values.numel() == 0:
        raise ValueError("singular_values must be a non-empty one-dimensional tensor")
    if not singular_values.is_floating_point() or not torch.isfinite(singular_values).all():
        raise ValueError("singular_values must be finite floating-point values")
    if torch.any(singular_values < 0):
        raise ValueError("singular_values must be non-negative")
    singular_sum = singular_values.sum()
    squared_sum = singular_values.square().sum()
    if zero_tolerance is None:
        zero_tolerance = torch.finfo(singular_values.dtype).eps * singular_values.numel()
    if float(singular_sum) <= float(zero_tolerance):
        return {
            "effective_rank": 0.0,
            "top_singular_l1_fraction": 1.0,
            "top_singular_energy_fraction": 1.0,
        }
    probabilities = singular_values / singular_sum
    nonzero = probabilities > 0
    entropy = -(probabilities[nonzero] * probabilities[nonzero].log()).sum()
    return {
        "effective_rank": float(entropy.exp()),
        "top_singular_l1_fraction": float(singular_values[0] / singular_sum),
        "top_singular_energy_fraction": float(singular_values[0].square() / squared_sum),
    }


def _bounded_cells(
    flattened: torch.Tensor,
    max_cells: int,
    subsample_seed: int,
) -> torch.Tensor:
    if max_cells < 2:
        raise ValueError("max_cells must be at least two")
    if flattened.shape[0] <= max_cells:
        return flattened
    generator = torch.Generator(device="cpu").manual_seed(subsample_seed)
    indices = torch.randperm(flattened.shape[0], generator=generator)[:max_cells]
    return flattened[indices.to(flattened.device)]


def representation_health(
    latents: torch.Tensor,
    *,
    max_pairwise_cells: int = 256,
    subsample_seed: int = 0,
) -> RepresentationHealth:
    """Measure distinct cell- and slot-collapse modes.

    Effective rank is ``exp(-sum(p_i log(p_i)))``, where ``p_i`` are singular
    values normalized by their sum after centering flattened representations
    across cells. It is zero when all centered singular values are zero.

    Historical continuity is reported as ``s_1 / sum_i(s_i)``. Energy
    concentration is reported separately as ``s_1^2 / sum_i(s_i^2)``. Neither
    is aliased to the historical generic ``top_sv_ratio`` name. Both use 1.0
    for a zero-energy, completely collapsed centered matrix.
    """
    if latents.ndim != 3 or latents.shape[0] < 2:
        raise ValueError("latents must have shape [cells, slots, width] with at least two cells")
    if not latents.is_floating_point() or not torch.isfinite(latents).all():
        raise ValueError("latents must be finite floating-point values")
    flattened = latents.reshape(latents.shape[0], -1)
    centered = flattened - flattened.mean(dim=0, keepdim=True)
    singular_values = torch.linalg.svdvals(centered)
    scale = max(1.0, float(torch.linalg.vector_norm(flattened)))
    tolerance = torch.finfo(singular_values.dtype).eps * scale * singular_values.numel()
    spectrum = singular_spectrum_metrics(singular_values, zero_tolerance=tolerance)
    cross_cell_std = latents.std(dim=0, unbiased=False)
    norms = torch.linalg.vector_norm(flattened, dim=1)
    bounded = _bounded_cells(flattened, max_pairwise_cells, subsample_seed)
    pairwise = torch.pdist(bounded, p=2)
    normalized_slots = F.normalize(latents, dim=-1)
    slot_cosines = torch.matmul(normalized_slots, normalized_slots.transpose(1, 2))
    slots = latents.shape[1]
    off_diagonal = ~torch.eye(slots, dtype=torch.bool, device=latents.device)
    slot_cosine_mean = slot_cosines[:, off_diagonal].mean()
    slot_variance = latents.var(dim=1, unbiased=False).mean()
    return RepresentationHealth(
        cross_cell_std_mean=float(cross_cell_std.mean()),
        cross_cell_std_min=float(cross_cell_std.min()),
        cross_cell_std_max=float(cross_cell_std.max()),
        effective_rank=spectrum["effective_rank"],
        singular_values=tuple(float(value) for value in singular_values),
        top_singular_l1_fraction=spectrum["top_singular_l1_fraction"],
        top_singular_energy_fraction=spectrum["top_singular_energy_fraction"],
        latent_norm_mean=float(norms.mean()),
        latent_norm_std=float(norms.std(unbiased=False)),
        latent_norm_min=float(norms.min()),
        latent_norm_max=float(norms.max()),
        pairwise_distance_mean=float(pairwise.mean()),
        pairwise_distance_median=float(pairwise.median()),
        pairwise_distance_p05=float(torch.quantile(pairwise, 0.05)),
        pairwise_distance_p95=float(torch.quantile(pairwise, 0.95)),
        slot_variance_mean=float(slot_variance),
        slot_cosine_similarity_mean=float(slot_cosine_mean),
    )


def context_target_agreement(
    context_latents: torch.Tensor,
    target_latents: torch.Tensor,
) -> dict[str, float]:
    if context_latents.shape != target_latents.shape:
        raise ValueError("context and target latent shapes must match")
    context_flat = context_latents.reshape(context_latents.shape[0], -1)
    target_flat = target_latents.reshape(target_latents.shape[0], -1)
    return {
        "mse": float(F.mse_loss(context_flat, target_flat)),
        "mean_cosine_similarity": float(F.cosine_similarity(context_flat, target_flat).mean()),
    }


def online_target_parameter_distance(
    online_encoder: nn.Module,
    target_encoder: nn.Module,
) -> dict[str, float]:
    online = dict(online_encoder.named_parameters())
    target = dict(ema_target_module(target_encoder).named_parameters())
    if online.keys() != target.keys():
        raise ValueError("online and target parameter structures must match")
    differences = [
        (online[name].detach() - target[name].detach()).reshape(-1)
        for name in online
    ]
    vector = torch.cat(differences)
    return {
        "l2_distance": float(torch.linalg.vector_norm(vector)),
        "rms_distance": float(torch.sqrt(vector.square().mean())),
        "max_abs_distance": float(vector.abs().max()),
        "parameter_count": float(vector.numel()),
    }


def module_parameter_snapshot(module: nn.Module) -> dict[str, torch.Tensor]:
    """Detach and clone a module's named parameters for transition telemetry."""
    module = ema_target_module(module)
    return {
        name: parameter.detach().clone()
        for name, parameter in module.named_parameters()
    }


def _parameter_vector(
    parameters: Mapping[str, torch.Tensor],
    *,
    expected_keys: set[str] | None = None,
) -> torch.Tensor:
    if not parameters:
        raise ValueError("parameter mapping must not be empty")
    if expected_keys is not None and set(parameters) != expected_keys:
        raise ValueError("parameter mappings must have identical keys")
    return torch.cat([parameters[name].detach().reshape(-1) for name in sorted(parameters)])


def ema_parameter_health(
    online_encoder: nn.Module,
    target_encoder: nn.Module,
    *,
    eps: float = 1e-12,
) -> EMAParameterHealth:
    """Measure the current online-target parameter gap.

    ``normalized_online_target_distance`` is exactly the parameter L2 distance
    divided by ``max(online_parameter_l2_norm, eps)``.
    """
    if eps <= 0:
        raise ValueError("eps must be positive")
    online = module_parameter_snapshot(online_encoder)
    target = module_parameter_snapshot(target_encoder)
    keys = set(online)
    online_vector = _parameter_vector(online)
    target_vector = _parameter_vector(target, expected_keys=keys)
    distance = torch.linalg.vector_norm(online_vector - target_vector)
    online_norm = torch.linalg.vector_norm(online_vector)
    target_norm = torch.linalg.vector_norm(target_vector)
    return EMAParameterHealth(
        online_target_parameter_l2_distance=float(distance),
        online_parameter_l2_norm=float(online_norm),
        target_parameter_l2_norm=float(target_norm),
        normalized_online_target_distance=float(distance / max(float(online_norm), eps)),
        parameter_count=online_vector.numel(),
    )


def ema_update_telemetry(
    *,
    online_before: Mapping[str, torch.Tensor],
    online_after: Mapping[str, torch.Tensor],
    target_before: Mapping[str, torch.Tensor],
    target_after: Mapping[str, torch.Tensor],
    eps: float = 1e-12,
) -> EMAUpdateTelemetry:
    """Describe one optimizer transition followed by one EMA target update.

    ``target_follow_fraction`` is the target-update L2 norm divided by
    ``max(pre_update_online_target_gap, eps)``.
    """
    if eps <= 0:
        raise ValueError("eps must be positive")
    keys = set(online_before)
    before_online = _parameter_vector(online_before)
    after_online = _parameter_vector(online_after, expected_keys=keys)
    before_target = _parameter_vector(target_before, expected_keys=keys)
    after_target = _parameter_vector(target_after, expected_keys=keys)
    target_update = torch.linalg.vector_norm(after_target - before_target)
    online_step = torch.linalg.vector_norm(after_online - before_online)
    pre_gap = torch.linalg.vector_norm(after_online - before_target)
    post_gap = torch.linalg.vector_norm(after_online - after_target)
    return EMAUpdateTelemetry(
        target_update_l2_norm=float(target_update),
        online_step_l2_norm=float(online_step),
        pre_update_online_target_gap=float(pre_gap),
        target_follow_fraction=float(target_update / max(float(pre_gap), eps)),
        post_update_online_target_gap=float(post_gap),
    )


def target_latent_health(target_latents: torch.Tensor) -> TargetLatentHealth:
    """Report detached cross-cell target variance without any downstream labels."""
    if target_latents.ndim < 2 or target_latents.shape[0] < 2:
        raise ValueError("target_latents must contain at least two cells")
    detached = target_latents.detach()
    if not detached.is_floating_point() or not torch.isfinite(detached).all():
        raise ValueError("target_latents must be finite floating-point values")
    variance = detached.var(dim=0, unbiased=False)
    std = torch.sqrt(variance)
    return TargetLatentHealth(
        variance_mean=float(variance.mean()),
        variance_min=float(variance.min()),
        variance_max=float(variance.max()),
        std_mean=float(std.mean()),
        std_min=float(std.min()),
        std_max=float(std.max()),
    )
