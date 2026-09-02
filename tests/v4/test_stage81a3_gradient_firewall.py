from __future__ import annotations

import sys
from pathlib import Path

import torch

PROJECT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT / "src"))

from sea_ad_jepa.v4 import (
    LatentPredictor,
    V4AEncoderSkeleton,
    frozen_target_copy,
    jepa_prediction_loss,
    online_target_parameter_distance,
)


def test_online_predictor_gradient_and_target_stop_gradient_firewall() -> None:
    torch.manual_seed(8102)
    online = V4AEncoderSkeleton().train()
    predictor = LatentPredictor().train()
    target = frozen_target_copy(online)
    initial_distance = online_target_parameter_distance(online, target)
    assert initial_distance["max_abs_distance"] == 0.0
    gene_ids = torch.tensor([
        [1, 3, 5, 7, 9, 11, 13, 15],
        [2, 4, 6, 8, 10, 12, 14, 16],
    ])
    expression = torch.tensor([
        [0.0, 0.2, 0.5, 1.0, 1.5, 2.0, 3.0, 4.0],
        [0.1, 0.3, 0.7, 1.2, 1.7, 2.4, 3.5, 4.5],
    ])
    measurement = torch.ones_like(gene_ids, dtype=torch.bool)
    context = torch.tensor([
        [False, True, False, False, True, False, False, True],
        [True, False, False, True, False, False, True, False],
    ])
    context_latents = online(
        gene_ids, expression, measurement, context, "student"
    )
    prediction = predictor(context_latents)
    with torch.no_grad():
        target_latents = target(
            gene_ids, expression, measurement, context, "target"
        )
    loss = jepa_prediction_loss(prediction, target_latents)
    loss.backward()
    assert any(
        parameter.grad is not None and torch.count_nonzero(parameter.grad) > 0
        for parameter in online.parameters()
    )
    assert all(parameter.grad is not None for parameter in predictor.parameters())
    assert all(parameter.grad is None for parameter in target.parameters())
    assert all(not parameter.requires_grad for parameter in target.parameters())
