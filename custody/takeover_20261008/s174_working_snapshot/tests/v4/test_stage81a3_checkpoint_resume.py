from __future__ import annotations

import io
import random
import sys
from pathlib import Path
from typing import Any

import numpy as np
import torch
from torch import nn

PROJECT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT / "src"))

from sea_ad_jepa.v4 import (
    EMAOptimizerStepController,
    capture_synthetic_checkpoint,
    create_ema_target,
    restore_synthetic_checkpoint,
)


def make_components(seed: int = 8103):
    torch.manual_seed(seed)
    online = nn.Sequential(nn.Linear(4, 5), nn.Tanh(), nn.Linear(5, 3))
    predictor = nn.Linear(3, 3)
    target = create_ema_target(online)
    optimizer = torch.optim.AdamW(
        list(online.parameters()) + list(predictor.parameters()),
        lr=0.01,
        weight_decay=0.001,
    )
    controller = EMAOptimizerStepController(online, target)
    return online, target, predictor, optimizer, controller


def microbatch(
    online: nn.Module,
    target: nn.Module,
    predictor: nn.Module,
    x: torch.Tensor,
) -> None:
    predicted = predictor(online(x))
    target_output = target(x)
    ((predicted - target_output).square().mean() / 2.0).backward()


def finish_step(
    optimizer: torch.optim.Optimizer,
    controller: EMAOptimizerStepController,
) -> None:
    controller.optimizer_step(optimizer, momentum=0.7)
    optimizer.zero_grad(set_to_none=True)


def state_difference(left: nn.Module, right: nn.Module) -> float:
    return max(
        float((a - b).abs().max())
        for a, b in zip(left.state_dict().values(), right.state_dict().values())
    )


def assert_nested_equal(left: Any, right: Any) -> None:
    if isinstance(left, torch.Tensor):
        assert torch.equal(left, right)
    elif isinstance(left, dict):
        assert left.keys() == right.keys()
        for key in left:
            assert_nested_equal(left[key], right[key])
    elif isinstance(left, (list, tuple)):
        assert len(left) == len(right)
        for a, b in zip(left, right):
            assert_nested_equal(a, b)
    else:
        assert left == right


def test_exact_resume_restores_accumulated_gradients_rng_masks_and_ema_state() -> None:
    input_generator = torch.Generator().manual_seed(9103)
    inputs = [torch.randn(3, 4, generator=input_generator) for _ in range(8)]
    online_a, target_a, predictor_a, optimizer_a, controller_a = make_components()
    optimizer_a.zero_grad(set_to_none=True)

    for step in range(2):
        microbatch(online_a, target_a, predictor_a, inputs[2 * step])
        microbatch(online_a, target_a, predictor_a, inputs[2 * step + 1])
        finish_step(optimizer_a, controller_a)

    microbatch(online_a, target_a, predictor_a, inputs[4])
    random.seed(8104)
    np.random.seed(8104)
    torch.manual_seed(8104)
    mask_generator_a = torch.Generator().manual_seed(8105)
    checkpoint = capture_synthetic_checkpoint(
        online_encoder=online_a,
        target_encoder=target_a,
        predictor=predictor_a,
        optimizer=optimizer_a,
        global_update_step=controller_a.global_update_step,
        ema_update_count=controller_a.ema_update_count,
        accumulation_position=1,
        masking_generator=mask_generator_a,
    )
    buffer = io.BytesIO()
    torch.save(checkpoint, buffer)

    rng_a = (random.random(), float(np.random.random()), float(torch.rand(())))
    masks_a = [torch.rand(3, generator=mask_generator_a) < 0.4 for _ in range(3)]
    microbatch(online_a, target_a, predictor_a, inputs[5])
    finish_step(optimizer_a, controller_a)
    microbatch(online_a, target_a, predictor_a, inputs[6])
    microbatch(online_a, target_a, predictor_a, inputs[7])
    finish_step(optimizer_a, controller_a)

    online_b, target_b, predictor_b, optimizer_b, controller_b = make_components(seed=9999)
    mask_generator_b = torch.Generator().manual_seed(1)
    buffer.seek(0)
    restored_state = torch.load(buffer, weights_only=False)
    counters = restore_synthetic_checkpoint(
        restored_state,
        online_encoder=online_b,
        target_encoder=target_b,
        predictor=predictor_b,
        optimizer=optimizer_b,
        masking_generator=mask_generator_b,
    )
    controller_b.load_bookkeeping(
        global_update_step=counters["global_update_step"],
        ema_update_count=counters["ema_update_count"],
    )
    assert counters["accumulation_position"] == 1

    rng_b = (random.random(), float(np.random.random()), float(torch.rand(())))
    masks_b = [torch.rand(3, generator=mask_generator_b) < 0.4 for _ in range(3)]
    assert rng_a == rng_b
    assert all(torch.equal(a, b) for a, b in zip(masks_a, masks_b))

    microbatch(online_b, target_b, predictor_b, inputs[5])
    finish_step(optimizer_b, controller_b)
    microbatch(online_b, target_b, predictor_b, inputs[6])
    microbatch(online_b, target_b, predictor_b, inputs[7])
    finish_step(optimizer_b, controller_b)

    assert state_difference(online_a, online_b) == 0.0
    assert state_difference(target_a, target_b) == 0.0
    assert state_difference(predictor_a, predictor_b) == 0.0
    assert_nested_equal(optimizer_a.state_dict(), optimizer_b.state_dict())
    assert controller_a.global_update_step == controller_b.global_update_step == 4
    assert controller_a.ema_update_count == controller_b.ema_update_count == 4
