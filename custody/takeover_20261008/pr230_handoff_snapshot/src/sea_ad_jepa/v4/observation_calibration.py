"""Explicit post-inference calibration for observation regimes."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable

import torch

from .rbb_adaptive import structured_gaussian_terms


@dataclass(frozen=True)
class CalibratedUncertainty:
    calibration_regime: str
    calibration_scale: float
    raw_conditional_diagonal: torch.Tensor
    raw_conditional_low_rank: torch.Tensor
    measurement_noise_diagonal: torch.Tensor
    raw_total_diagonal: torch.Tensor
    raw_total_low_rank: torch.Tensor
    calibrated_total_diagonal: torch.Tensor
    calibrated_total_low_rank: torch.Tensor


def apply_observation_calibration(
    conditional_diagonal: torch.Tensor,
    conditional_low_rank: torch.Tensor,
    measurement_noise_diagonal: torch.Tensor,
    *,
    regime: str,
    scale: float,
) -> CalibratedUncertainty:
    """Expose raw and calibrated covariance without altering biological means."""
    if not math.isfinite(scale) or scale <= 0:
        raise ValueError("calibration scale must be positive and finite")
    raw_total_diagonal = conditional_diagonal.float() + measurement_noise_diagonal.float()
    raw_total_low_rank = conditional_low_rank.float()
    if regime == "ordinary_raw":
        if scale != 1.0:
            raise ValueError("ordinary regime requires scale 1.0")
        calibrated_diagonal, calibrated_low_rank = raw_total_diagonal, raw_total_low_rank
    elif regime == "historical_total_scalar":
        calibrated_diagonal = scale * raw_total_diagonal
        calibrated_low_rank = math.sqrt(scale) * raw_total_low_rank
    elif regime == "conditional_only_scalar":
        calibrated_diagonal = measurement_noise_diagonal.float() + scale * conditional_diagonal.float()
        calibrated_low_rank = math.sqrt(scale) * raw_total_low_rank
    else:
        raise ValueError(f"unknown calibration regime: {regime}")
    return CalibratedUncertainty(
        regime, float(scale), conditional_diagonal.float(), conditional_low_rank.float(),
        measurement_noise_diagonal.float(), raw_total_diagonal, raw_total_low_rank,
        calibrated_diagonal, calibrated_low_rank,
    )


def conditional_scale_objective(
    log_scale: float,
    batches: Iterable[tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]],
) -> float:
    """Mean Gaussian NLL for one shared conditional-only scale."""
    scale = math.exp(log_scale); total, examples = 0.0, 0
    for residual, conditional_diagonal, conditional_low_rank, noise_diagonal in batches:
        calibrated = apply_observation_calibration(
            conditional_diagonal, conditional_low_rank, noise_diagonal,
            regime="conditional_only_scalar", scale=scale,
        )
        nll, _, _ = structured_gaussian_terms(
            residual, calibrated.calibrated_total_diagonal, calibrated.calibrated_total_low_rank
        )
        total += float(nll.double().sum()); examples += len(nll)
    return total / max(examples, 1)


def fit_conditional_only_scale(
    batches: list[tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]],
    *,
    lower_log_scale: float = -6.0,
    upper_log_scale: float = 3.0,
    iterations: int = 96,
) -> tuple[float, dict[str, float | int | str]]:
    """Deterministic golden-section fit of one positive validation-only scalar."""
    if not batches:
        raise ValueError("at least one validation batch is required")
    ratio = (math.sqrt(5.0) - 1.0) / 2.0
    left, right = float(lower_log_scale), float(upper_log_scale)
    c = right - ratio * (right - left); d = left + ratio * (right - left)
    fc = conditional_scale_objective(c, batches); fd = conditional_scale_objective(d, batches)
    for _ in range(iterations):
        if fc <= fd:
            right, d, fd = d, c, fc
            c = right - ratio * (right - left); fc = conditional_scale_objective(c, batches)
        else:
            left, c, fc = c, d, fd
            d = left + ratio * (right - left); fd = conditional_scale_objective(d, batches)
    optimum = .5 * (left + right); scale = math.exp(optimum)
    return scale, {
        "method": "deterministic_golden_section_log_scale",
        "iterations": iterations,
        "lower_log_scale": lower_log_scale,
        "upper_log_scale": upper_log_scale,
        "validation_objective": conditional_scale_objective(optimum, batches),
    }
