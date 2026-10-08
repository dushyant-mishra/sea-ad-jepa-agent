from __future__ import annotations

import inspect
import sys
from pathlib import Path

import torch

PROJECT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT / "src"))

from sea_ad_jepa.v4 import LatentPredictor, V4AEncoderSkeleton


def predictor() -> LatentPredictor:
    torch.manual_seed(8102)
    return LatentPredictor().eval()


def test_predictor_shape_finiteness_and_small_batches() -> None:
    model = predictor()
    for batch_size in (1, 2, 5):
        result = model(torch.randn(batch_size, 24, 160))
        assert result.shape == (batch_size, 24, 160)
        assert torch.isfinite(result).all()


def test_predictor_cross_slot_interaction() -> None:
    model = predictor()
    context = torch.randn(1, 24, 160)
    changed = context.clone()
    changed[:, 7] += torch.linspace(-5.0, 5.0, 160)
    baseline_output = model(context)
    changed_output = model(changed)
    other_slots = torch.tensor([index for index in range(24) if index != 7])
    assert float((baseline_output[:, other_slots] - changed_output[:, other_slots]).abs().max()) > 1e-6


def test_predictor_gradients_and_narrow_api() -> None:
    model = predictor()
    context = torch.randn(2, 24, 160, requires_grad=True)
    model(context).square().mean().backward()
    assert context.grad is not None and torch.count_nonzero(context.grad) > 0
    assert all(parameter.grad is not None for parameter in model.parameters())
    assert set(inspect.signature(model.forward).parameters) == {"context_latents"}


def test_predictor_is_parameter_subordinate_to_full_encoder() -> None:
    model = predictor()
    encoder = V4AEncoderSkeleton()
    predictor_count = sum(parameter.numel() for parameter in model.parameters())
    encoder_count = sum(parameter.numel() for parameter in encoder.parameters())
    assert predictor_count == 206_560
    assert encoder_count == 730_752
    assert predictor_count < encoder_count
