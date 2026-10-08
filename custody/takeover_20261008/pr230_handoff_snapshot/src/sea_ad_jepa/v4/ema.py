"""Policy-free EMA target mechanics for the Stage81A3 synthetic contract."""

from __future__ import annotations

import copy
import math
from dataclasses import dataclass
from typing import Any

import torch
from torch import nn


class EMATargetEncoder(nn.Module):
    """Gradient-frozen, evaluation-only copy of an online encoder."""

    def __init__(self, online_encoder: nn.Module) -> None:
        super().__init__()
        self.encoder = copy.deepcopy(online_encoder)
        self.encoder.eval()
        for parameter in self.encoder.parameters():
            parameter.requires_grad_(False)
        super().train(False)

    def train(self, mode: bool = True) -> "EMATargetEncoder":
        """Keep the teacher deterministic even if a parent module enters train mode."""
        super().train(False)
        self.encoder.eval()
        return self

    @torch.no_grad()
    def forward(self, *args: Any, **kwargs: Any) -> Any:
        self.encoder.eval()
        return self.encoder(*args, **kwargs)


@dataclass(frozen=True)
class EMAUpdateSummary:
    momentum: float
    parameter_count: int
    floating_buffer_count: int
    copied_nonfloating_buffer_count: int


def ema_target_module(target_encoder: nn.Module) -> nn.Module:
    """Return the copied encoder inside an EMA wrapper, or the module itself."""
    if isinstance(target_encoder, EMATargetEncoder):
        return target_encoder.encoder
    return target_encoder


def create_ema_target(online_encoder: nn.Module) -> EMATargetEncoder:
    """Create an exact, frozen target copy without selecting EMA momentum."""
    return EMATargetEncoder(online_encoder)


def validate_momentum(momentum: float) -> float:
    momentum = float(momentum)
    if not 0.0 <= momentum <= 1.0:
        raise ValueError("EMA momentum must be in the closed interval [0, 1]")
    return momentum


def ema_momentum_at_step(
    *,
    optimizer_step: int,
    total_optimizer_steps: int,
    start_momentum: float,
    end_momentum: float,
    schedule_type: str,
) -> float:
    """Return momentum as a pure function of global optimizer-step progress.

    Steps are zero-based update indices in ``[0, total_optimizer_steps - 1]``.
    A one-step linear or cosine schedule uses ``end_momentum`` because that
    update is both its first and last. No momentum values are defaulted.
    """
    start = validate_momentum(start_momentum)
    end = validate_momentum(end_momentum)
    if total_optimizer_steps < 1:
        raise ValueError("total_optimizer_steps must be positive")
    if not 0 <= optimizer_step < total_optimizer_steps:
        raise ValueError("optimizer_step must index a scheduled optimizer update")
    if schedule_type == "fixed":
        if start != end:
            raise ValueError("fixed EMA schedule requires equal start and end momentum")
        return start
    if schedule_type not in {"linear", "cosine"}:
        raise ValueError("schedule_type must be fixed, linear, or cosine")
    progress = 1.0 if total_optimizer_steps == 1 else optimizer_step / (total_optimizer_steps - 1)
    if schedule_type == "cosine":
        progress = 0.5 - 0.5 * math.cos(math.pi * progress)
    return start + (end - start) * progress


@torch.no_grad()
def update_ema_target(
    online_encoder: nn.Module,
    target_encoder: nn.Module,
    *,
    momentum: float,
) -> EMAUpdateSummary:
    """Apply one explicit EMA update to parameters and compatible buffers.

    Floating and complex buffers follow the same EMA rule as parameters.
    Non-floating buffers, such as counters, are copied exactly from online to
    target because arithmetic averaging is not meaningful for them.
    """
    momentum = validate_momentum(momentum)
    target_module = ema_target_module(target_encoder)
    online_parameters = dict(online_encoder.named_parameters())
    target_parameters = dict(target_module.named_parameters())
    if online_parameters.keys() != target_parameters.keys():
        raise ValueError("online and target parameter structures must match")

    parameter_count = 0
    for name, online_parameter in online_parameters.items():
        target_parameter = target_parameters[name]
        if online_parameter.shape != target_parameter.shape:
            raise ValueError(f"parameter shape mismatch for {name}")
        target_parameter.mul_(momentum).add_(online_parameter, alpha=1.0 - momentum)
        parameter_count += online_parameter.numel()

    online_buffers = dict(online_encoder.named_buffers())
    target_buffers = dict(target_module.named_buffers())
    if online_buffers.keys() != target_buffers.keys():
        raise ValueError("online and target buffer structures must match")
    floating_count = 0
    copied_count = 0
    for name, online_buffer in online_buffers.items():
        target_buffer = target_buffers[name]
        if online_buffer.shape != target_buffer.shape:
            raise ValueError(f"buffer shape mismatch for {name}")
        if online_buffer.is_floating_point() or online_buffer.is_complex():
            target_buffer.mul_(momentum).add_(online_buffer, alpha=1.0 - momentum)
            floating_count += 1
        else:
            target_buffer.copy_(online_buffer)
            copied_count += 1

    target_module.eval()
    for parameter in target_module.parameters():
        parameter.requires_grad_(False)
    return EMAUpdateSummary(
        momentum=momentum,
        parameter_count=parameter_count,
        floating_buffer_count=floating_count,
        copied_nonfloating_buffer_count=copied_count,
    )


class EMAOptimizerStepController:
    """Couple exactly one EMA update to each successful optimizer step."""

    def __init__(self, online_encoder: nn.Module, target_encoder: nn.Module) -> None:
        self.online_encoder = online_encoder
        self.target_encoder = target_encoder
        self.global_update_step = 0
        self.ema_update_count = 0

    def optimizer_step(
        self,
        optimizer: torch.optim.Optimizer,
        *,
        momentum: float,
    ) -> EMAUpdateSummary:
        optimizer.step()
        return self.after_successful_optimizer_step(momentum=momentum)

    def after_successful_optimizer_step(self, *, momentum: float) -> EMAUpdateSummary:
        """Apply EMA/bookkeeping after an externally managed successful step.

        This supports mixed-precision scalers, which own ``optimizer.step``.
        Callers must not invoke this method when the scaler skipped the step.
        """
        summary = update_ema_target(
            self.online_encoder,
            self.target_encoder,
            momentum=momentum,
        )
        self.global_update_step += 1
        self.ema_update_count += 1
        return summary

    def load_bookkeeping(self, *, global_update_step: int, ema_update_count: int) -> None:
        if global_update_step < 0 or ema_update_count < 0:
            raise ValueError("EMA bookkeeping counters must be non-negative")
        self.global_update_step = int(global_update_step)
        self.ema_update_count = int(ema_update_count)
