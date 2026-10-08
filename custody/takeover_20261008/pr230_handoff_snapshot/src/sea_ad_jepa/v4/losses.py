"""Synthetic JEPA loss and explicit, unresolved variance safeguard mechanics."""

from __future__ import annotations

import copy

import torch
from torch import nn
import torch.nn.functional as F

from .contracts import MECHANICS_CONTRACT


def jepa_prediction_loss(
    predicted_target: torch.Tensor,
    target_latents: torch.Tensor,
) -> torch.Tensor:
    """Direct-slot raw-latent MSE against a detached target tensor."""
    expected = (MECHANICS_CONTRACT.latent_slots, MECHANICS_CONTRACT.model_width)
    if predicted_target.shape != target_latents.shape:
        raise ValueError("prediction and target latent shapes must match")
    if predicted_target.ndim != 3 or tuple(predicted_target.shape[1:]) != expected:
        raise ValueError("prediction and target must have shape [batch, 24, 160]")
    return F.mse_loss(predicted_target, target_latents.detach())


def variance_floor_penalty(
    latents: torch.Tensor,
    *,
    gamma: float,
    weight: float,
) -> tuple[torch.Tensor, torch.Tensor]:
    """Penalize low raw-latent standard deviation across cells.

    ``gamma`` and ``weight`` are required call-site policy values. Neither has
    a production default or frozen Stage81A3 setting.
    """
    if latents.ndim != 3 or tuple(latents.shape[1:]) != (
        MECHANICS_CONTRACT.latent_slots,
        MECHANICS_CONTRACT.model_width,
    ):
        raise ValueError("latents must have shape [batch, 24, 160]")
    if latents.shape[0] < 2:
        raise ValueError("cross-cell variance requires at least two cells")
    if gamma < 0 or weight < 0:
        raise ValueError("gamma and weight must be non-negative")
    cross_cell_std = latents.std(dim=0, unbiased=False)
    unweighted = torch.relu(torch.as_tensor(gamma, device=latents.device) - cross_cell_std).mean()
    return unweighted * weight, cross_cell_std


def frozen_target_copy(online_encoder: nn.Module) -> nn.Module:
    """Create a gradient-frozen target copy without defining an EMA policy."""
    target_encoder = copy.deepcopy(online_encoder)
    target_encoder.eval()
    for parameter in target_encoder.parameters():
        parameter.requires_grad_(False)
    return target_encoder
