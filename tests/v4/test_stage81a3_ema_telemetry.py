from __future__ import annotations

import sys
from pathlib import Path

import torch
from torch import nn

PROJECT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT / "src"))

from sea_ad_jepa.v4 import (
    create_ema_target,
    ema_parameter_health,
    ema_target_module,
    ema_update_telemetry,
    module_parameter_snapshot,
    target_latent_health,
    update_ema_target,
)


def test_ema_health_and_follow_fraction_match_formula() -> None:
    online = nn.Linear(2, 1, bias=False)
    with torch.no_grad():
        online.weight.zero_()
    target = create_ema_target(online)
    online_before = module_parameter_snapshot(online)
    target_before = module_parameter_snapshot(target)
    initial = ema_parameter_health(online, target)
    assert initial.online_target_parameter_l2_distance == 0.0
    with torch.no_grad():
        online.weight.copy_(torch.tensor([[3.0, 4.0]]))
    online_after = module_parameter_snapshot(online)
    update_ema_target(online, target, momentum=0.75)
    target_after = module_parameter_snapshot(target)
    telemetry = ema_update_telemetry(
        online_before=online_before,
        online_after=online_after,
        target_before=target_before,
        target_after=target_after,
    )
    assert abs(telemetry.online_step_l2_norm - 5.0) < 1e-7
    assert abs(telemetry.pre_update_online_target_gap - 5.0) < 1e-7
    assert abs(telemetry.target_update_l2_norm - 1.25) < 1e-7
    assert abs(telemetry.target_follow_fraction - 0.25) < 1e-7
    assert abs(telemetry.post_update_online_target_gap - 3.75) < 1e-7
    health = ema_parameter_health(online, target)
    assert abs(health.online_target_parameter_l2_distance - 3.75) < 1e-7
    assert abs(health.normalized_online_target_distance - 0.75) < 1e-7


def test_noisy_online_trajectory_is_followed_and_larger_momentum_is_smoother() -> None:
    perturbations = [1.0, -0.6, 1.2, -0.4, 0.9]
    traces = {}
    for momentum in (0.2, 0.8):
        online = nn.Linear(1, 1, bias=False)
        with torch.no_grad():
            online.weight.zero_()
        target = create_ema_target(online)
        online_trace = [0.0]
        target_trace = [0.0]
        for perturbation in perturbations:
            with torch.no_grad():
                online.weight.add_(perturbation)
            update_ema_target(online, target, momentum=momentum)
            online_trace.append(float(online.weight))
            target_trace.append(float(ema_target_module(target).weight))
        traces[momentum] = (online_trace, target_trace)
    fast_online, fast_target = traces[0.2]
    slow_online, slow_target = traces[0.8]
    assert fast_online == slow_online
    fast_movements = torch.diff(torch.tensor(fast_target)).abs()
    slow_movements = torch.diff(torch.tensor(slow_target)).abs()
    assert float(slow_movements.max()) < float(fast_movements.max())
    assert slow_target[-1] > 0
    assert fast_target[-1] > 0
    assert all(parameter.grad is None for parameter in ema_target_module(target).parameters())


def test_target_latent_variance_is_detached_and_cross_cell() -> None:
    latents = torch.tensor([
        [[0.0, 1.0], [2.0, 3.0]],
        [[2.0, 3.0], [4.0, 5.0]],
    ], requires_grad=True)
    health = target_latent_health(latents)
    assert health.variance_mean == 1.0
    assert health.std_mean == 1.0
