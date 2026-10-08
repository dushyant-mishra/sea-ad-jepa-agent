from __future__ import annotations

import sys
from pathlib import Path

import pytest
import torch
from torch import nn

PROJECT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT / "src"))

from sea_ad_jepa.v4 import (
    EMAOptimizerStepController,
    capture_synthetic_checkpoint,
    create_ema_target,
    ema_momentum_at_step,
    restore_synthetic_checkpoint,
)


def test_fixed_linear_cosine_schedules_are_pure_and_endpoint_exact() -> None:
    assert ema_momentum_at_step(
        optimizer_step=4, total_optimizer_steps=10,
        start_momentum=0.8, end_momentum=0.8, schedule_type="fixed",
    ) == 0.8
    for start, end in ((0.992, 0.9995), (0.996, 1.0), (0.996, 0.9999)):
        linear = [ema_momentum_at_step(
            optimizer_step=step, total_optimizer_steps=5,
            start_momentum=start, end_momentum=end, schedule_type="linear",
        ) for step in range(5)]
        cosine = [ema_momentum_at_step(
            optimizer_step=step, total_optimizer_steps=5,
            start_momentum=start, end_momentum=end, schedule_type="cosine",
        ) for step in range(5)]
        assert linear[0] == cosine[0] == start
        assert linear[-1] == cosine[-1] == end
        assert linear == sorted(linear)
        assert cosine == sorted(cosine)
    with pytest.raises(ValueError):
        ema_momentum_at_step(
            optimizer_step=0, total_optimizer_steps=2,
            start_momentum=0.8, end_momentum=0.9, schedule_type="fixed",
        )


def test_exact_one_only_on_final_update_differs_by_epsilon_times_final_gap() -> None:
    target_before = torch.tensor([2.0])
    online_after = torch.tensor([7.0])
    exact_one = 1.0 * target_before + 0.0 * online_after
    below_one = 0.9999 * target_before + 0.0001 * online_after
    assert torch.allclose((below_one - exact_one).abs(), torch.tensor([0.0005]), atol=1e-7)


def _components(seed: int):
    torch.manual_seed(seed)
    online = nn.Linear(3, 2)
    predictor = nn.Linear(2, 2)
    target = create_ema_target(online)
    optimizer = torch.optim.SGD(list(online.parameters()) + list(predictor.parameters()), lr=0.03)
    controller = EMAOptimizerStepController(online, target)
    return online, target, predictor, optimizer, controller


def _step(online, target, predictor, optimizer, controller, x, total_steps):
    optimizer.zero_grad(set_to_none=True)
    loss = (predictor(online(x)) - target(x)).square().mean()
    loss.backward()
    momentum = ema_momentum_at_step(
        optimizer_step=controller.global_update_step,
        total_optimizer_steps=total_steps,
        start_momentum=0.6,
        end_momentum=0.9,
        schedule_type="linear",
    )
    controller.optimizer_step(optimizer, momentum=momentum)
    return momentum


def test_schedule_resume_uses_restored_global_optimizer_step_exactly() -> None:
    inputs = [torch.full((4, 3), float(i + 1) / 10) for i in range(6)]
    online_a, target_a, predictor_a, optimizer_a, controller_a = _components(91)
    momentum_a = []
    for x in inputs[:3]:
        momentum_a.append(_step(online_a, target_a, predictor_a, optimizer_a, controller_a, x, len(inputs)))
    state = capture_synthetic_checkpoint(
        online_encoder=online_a, target_encoder=target_a, predictor=predictor_a,
        optimizer=optimizer_a, global_update_step=controller_a.global_update_step,
        ema_update_count=controller_a.ema_update_count, accumulation_position=0,
    )
    for x in inputs[3:]:
        momentum_a.append(_step(online_a, target_a, predictor_a, optimizer_a, controller_a, x, len(inputs)))

    online_b, target_b, predictor_b, optimizer_b, controller_b = _components(999)
    counters = restore_synthetic_checkpoint(
        state, online_encoder=online_b, target_encoder=target_b,
        predictor=predictor_b, optimizer=optimizer_b,
    )
    controller_b.load_bookkeeping(
        global_update_step=counters["global_update_step"],
        ema_update_count=counters["ema_update_count"],
    )
    momentum_b = []
    for x in inputs[3:]:
        momentum_b.append(_step(online_b, target_b, predictor_b, optimizer_b, controller_b, x, len(inputs)))
    assert momentum_b == momentum_a[3:]
    for left, right in ((online_a, online_b), (target_a, target_b), (predictor_a, predictor_b)):
        assert all(torch.equal(a, b) for a, b in zip(left.state_dict().values(), right.state_dict().values()))
    assert optimizer_a.state_dict() == optimizer_b.state_dict()
    assert controller_a.global_update_step == controller_b.global_update_step == 6
