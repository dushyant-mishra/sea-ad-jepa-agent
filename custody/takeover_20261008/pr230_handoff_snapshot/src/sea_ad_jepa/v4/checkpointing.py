"""Minimal deterministic checkpoint state for Stage81A3 synthetic mechanics."""

from __future__ import annotations

import copy
import random
from typing import Any

import numpy as np
import torch
from torch import nn


def _gradient_state(module: nn.Module) -> dict[str, torch.Tensor | None]:
    return {
        name: None if parameter.grad is None else parameter.grad.detach().clone()
        for name, parameter in module.named_parameters()
    }


def _restore_gradients(
    module: nn.Module,
    gradients: dict[str, torch.Tensor | None],
) -> None:
    parameters = dict(module.named_parameters())
    if parameters.keys() != gradients.keys():
        raise ValueError("checkpoint gradient structure does not match module")
    for name, gradient in gradients.items():
        parameters[name].grad = None if gradient is None else gradient.clone().to(parameters[name])


def capture_synthetic_checkpoint(
    *,
    online_encoder: nn.Module,
    target_encoder: nn.Module,
    predictor: nn.Module,
    optimizer: torch.optim.Optimizer,
    global_update_step: int,
    ema_update_count: int,
    accumulation_position: int,
    masking_generator: torch.Generator | None = None,
) -> dict[str, Any]:
    """Capture all state required for exact synthetic continuation."""
    if min(global_update_step, ema_update_count, accumulation_position) < 0:
        raise ValueError("checkpoint counters must be non-negative")
    state: dict[str, Any] = {
        "online_encoder": copy.deepcopy(online_encoder.state_dict()),
        "target_encoder": copy.deepcopy(target_encoder.state_dict()),
        "predictor": copy.deepcopy(predictor.state_dict()),
        "optimizer": copy.deepcopy(optimizer.state_dict()),
        "online_gradients": _gradient_state(online_encoder),
        "predictor_gradients": _gradient_state(predictor),
        "global_update_step": int(global_update_step),
        "ema_update_count": int(ema_update_count),
        "accumulation_position": int(accumulation_position),
        "python_rng_state": random.getstate(),
        "numpy_rng_state": np.random.get_state(),
        "torch_cpu_rng_state": torch.get_rng_state().clone(),
        "torch_cuda_rng_states": (
            [item.clone() for item in torch.cuda.get_rng_state_all()]
            if torch.cuda.is_available()
            else None
        ),
        "masking_rng_state": (
            masking_generator.get_state().clone()
            if masking_generator is not None
            else None
        ),
    }
    return state


def restore_synthetic_checkpoint(
    state: dict[str, Any],
    *,
    online_encoder: nn.Module,
    target_encoder: nn.Module,
    predictor: nn.Module,
    optimizer: torch.optim.Optimizer,
    masking_generator: torch.Generator | None = None,
) -> dict[str, int]:
    """Restore model, optimizer, accumulated gradients, RNG, and counters."""
    online_encoder.load_state_dict(state["online_encoder"])
    target_encoder.load_state_dict(state["target_encoder"])
    predictor.load_state_dict(state["predictor"])
    optimizer.load_state_dict(state["optimizer"])
    _restore_gradients(online_encoder, state["online_gradients"])
    _restore_gradients(predictor, state["predictor_gradients"])
    random.setstate(state["python_rng_state"])
    np.random.set_state(state["numpy_rng_state"])
    torch.set_rng_state(state["torch_cpu_rng_state"])
    if torch.cuda.is_available() and state["torch_cuda_rng_states"] is not None:
        torch.cuda.set_rng_state_all(state["torch_cuda_rng_states"])
    if state["masking_rng_state"] is not None:
        if masking_generator is None:
            raise ValueError("checkpoint contains masking RNG state but no generator was supplied")
        masking_generator.set_state(state["masking_rng_state"])
    return {
        "global_update_step": int(state["global_update_step"]),
        "ema_update_count": int(state["ema_update_count"]),
        "accumulation_position": int(state["accumulation_position"]),
    }
