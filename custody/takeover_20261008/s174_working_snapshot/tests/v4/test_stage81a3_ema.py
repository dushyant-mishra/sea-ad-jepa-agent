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
    LatentPredictor,
    V4AEncoderSkeleton,
    create_ema_target,
    ema_target_module,
    jepa_prediction_loss,
    update_ema_target,
)


class BufferedEncoder(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.linear = nn.Linear(3, 2)
        self.dropout = nn.Dropout(0.8)
        self.register_buffer("running_value", torch.tensor([2.0]))
        self.register_buffer("counter", torch.tensor([3], dtype=torch.long))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.dropout(self.linear(x))


def test_exact_initial_copy_gradient_freeze_and_deterministic_teacher() -> None:
    torch.manual_seed(81)
    online = BufferedEncoder().train()
    target = create_ema_target(online)
    target_module = ema_target_module(target)
    for online_parameter, target_parameter in zip(online.parameters(), target_module.parameters()):
        assert torch.equal(online_parameter, target_parameter)
        assert not target_parameter.requires_grad
    for online_buffer, target_buffer in zip(online.buffers(), target_module.buffers()):
        assert torch.equal(online_buffer, target_buffer)
    target.train()
    x = torch.randn(4, 3)
    assert torch.equal(target(x), target(x))
    assert not target.training
    assert not target_module.training


def test_exact_ema_formula_buffers_edges_and_momentum_validation() -> None:
    online = BufferedEncoder()
    target = create_ema_target(online)
    target_module = ema_target_module(target)
    target_before = {name: value.detach().clone() for name, value in target_module.named_parameters()}
    with torch.no_grad():
        for parameter in online.parameters():
            parameter.add_(2.0)
        online.running_value.fill_(6.0)
        online.counter.fill_(9)
    summary = update_ema_target(online, target, momentum=0.75)
    for name, parameter in target_module.named_parameters():
        expected = 0.75 * target_before[name] + 0.25 * dict(online.named_parameters())[name]
        assert torch.allclose(parameter, expected)
    assert torch.equal(target_module.running_value, torch.tensor([3.0]))
    assert torch.equal(target_module.counter, torch.tensor([9]))
    assert summary.floating_buffer_count == 1
    assert summary.copied_nonfloating_buffer_count == 1

    update_ema_target(online, target, momentum=0.0)
    for online_parameter, target_parameter in zip(online.parameters(), target_module.parameters()):
        assert torch.equal(online_parameter, target_parameter)
    frozen = [parameter.detach().clone() for parameter in target_module.parameters()]
    with torch.no_grad():
        for parameter in online.parameters():
            parameter.add_(1.0)
    update_ema_target(online, target, momentum=1.0)
    for before, after in zip(frozen, target_module.parameters()):
        assert torch.equal(before, after)
    for invalid in (-0.01, 1.01):
        with pytest.raises(ValueError):
            update_ema_target(online, target, momentum=invalid)


def test_momentum_monotonicity_and_target_moves_without_overshoot() -> None:
    online = nn.Linear(2, 1, bias=False)
    with torch.no_grad():
        online.weight.zero_()
    target_fast = create_ema_target(online)
    target_slow = create_ema_target(online)
    with torch.no_grad():
        online.weight.fill_(4.0)
    update_ema_target(online, target_fast, momentum=0.25)
    update_ema_target(online, target_slow, momentum=0.75)
    fast = ema_target_module(target_fast).weight
    slow = ema_target_module(target_slow).weight
    assert torch.all(fast > slow)
    assert torch.all(slow > 0)
    assert torch.all(fast < online.weight)


def test_microbatches_do_not_update_target_and_optimizer_step_updates_once() -> None:
    torch.manual_seed(82)
    online = nn.Linear(3, 2)
    target = create_ema_target(online)
    predictor = nn.Linear(2, 2)
    optimizer = torch.optim.SGD(
        list(online.parameters()) + list(predictor.parameters()), lr=0.1
    )
    controller = EMAOptimizerStepController(online, target)
    target_before = [parameter.detach().clone() for parameter in target.parameters()]
    for _ in range(3):
        x = torch.randn(4, 3)
        prediction = predictor(online(x))
        with torch.no_grad():
            target_output = target(x)
        ((prediction - target_output).square().mean() / 3.0).backward()
        assert controller.ema_update_count == 0
        assert all(torch.equal(a, b) for a, b in zip(target_before, target.parameters()))
    controller.optimizer_step(optimizer, momentum=0.6)
    assert controller.global_update_step == 1
    assert controller.ema_update_count == 1
    assert any(not torch.equal(a, b) for a, b in zip(target_before, target.parameters()))
    assert all(parameter.grad is None for parameter in target.parameters())
    assert any(parameter.grad is not None for parameter in online.parameters())
    assert any(parameter.grad is not None for parameter in predictor.parameters())


@pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA unavailable")
def test_cuda_mixed_precision_ema_mechanics_are_finite() -> None:
    device = torch.device("cuda")
    online = V4AEncoderSkeleton().to(device).train()
    predictor = LatentPredictor().to(device).train()
    target = create_ema_target(online).to(device)
    gene_ids = torch.tensor([
        [1, 3, 5, 7, 9, 11, 13, 15],
        [2, 4, 6, 8, 10, 12, 14, 16],
    ], device=device)
    expression = torch.rand(2, 8, device=device)
    measurement = torch.ones(2, 8, dtype=torch.bool, device=device)
    context = torch.tensor([
        [False, True, False, False, True, False, False, True],
        [True, False, False, True, False, False, True, False],
    ], device=device)
    with torch.autocast(device_type="cuda", dtype=torch.float16):
        online_output = online(gene_ids, expression, measurement, context, "student")
        predicted = predictor(online_output)
        target_output = target(gene_ids, expression, measurement, context, "target")
        loss = jepa_prediction_loss(predicted, target_output)
    loss.backward()
    update_ema_target(online, target, momentum=0.5)
    assert torch.isfinite(online_output).all()
    assert torch.isfinite(predicted).all()
    assert torch.isfinite(target_output).all()
    assert torch.isfinite(loss)
    assert all(parameter.grad is None or torch.isfinite(parameter.grad).all() for parameter in online.parameters())
    assert all(torch.isfinite(parameter).all() for parameter in target.parameters())
