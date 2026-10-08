from __future__ import annotations

import sys
from pathlib import Path

import torch

PROJECT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT / "src"))

from sea_ad_jepa.v4 import jepa_prediction_loss, variance_floor_penalty


def test_identical_prediction_and_target_have_zero_loss() -> None:
    values = torch.randn(3, 24, 160)
    assert float(jepa_prediction_loss(values, values)) == 0.0


def test_direct_slot_correspondence_and_exact_raw_mse_geometry() -> None:
    prediction = torch.zeros(1, 24, 160)
    target = torch.zeros_like(prediction)
    prediction[0, 3, 11] = 2.0
    observed = jepa_prediction_loss(prediction, target)
    expected = torch.tensor(4.0 / prediction.numel())
    torch.testing.assert_close(observed, expected)
    prediction[0, 3, 11] = 4.0
    scaled = jepa_prediction_loss(prediction, target)
    torch.testing.assert_close(scaled, observed * 4.0)


def test_target_is_detached_but_prediction_receives_gradient() -> None:
    prediction = torch.randn(2, 24, 160, requires_grad=True)
    target = torch.randn(2, 24, 160, requires_grad=True)
    loss = jepa_prediction_loss(prediction, target)
    assert float(loss) > 0
    loss.backward()
    assert prediction.grad is not None and torch.count_nonzero(prediction.grad) > 0
    assert target.grad is None


def test_variance_floor_is_population_std_hinge_without_epsilon() -> None:
    latents = torch.zeros(2, 24, 160)
    latents[1] = 4.0
    weighted, cross_cell_std = variance_floor_penalty(
        latents,
        gamma=3.0,
        weight=0.5,
    )

    # For each slot and dimension, population std([0, 4]) is exactly 2.
    torch.testing.assert_close(cross_cell_std, torch.full_like(cross_cell_std, 2.0))
    torch.testing.assert_close(weighted, torch.tensor(0.5))

    # A direct variance hinge would be zero because population variance is 4 > 3.
    direct_variance_hinge = torch.relu(
        torch.tensor(3.0) - latents.var(dim=0, unbiased=False)
    ).mean()
    torch.testing.assert_close(direct_variance_hinge, torch.tensor(0.0))
