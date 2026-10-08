from __future__ import annotations

import sys
from pathlib import Path

import torch

PROJECT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT / "src"))

from sea_ad_jepa.v4 import (
    LatentPredictor,
    V4AEncoderSkeleton,
    capture_synthetic_checkpoint,
    construct_context_mask,
    create_ema_target,
    ema_parameter_health,
    jepa_prediction_loss,
    representation_health,
    restore_synthetic_checkpoint,
    update_ema_target,
)


TEST_SEEDS = (101, 211, 307, 401, 503)


def parameter_count(module: torch.nn.Module) -> int:
    return sum(parameter.numel() for parameter in module.parameters())


def test_mechanics_are_consistent_across_five_explicit_synthetic_seeds() -> None:
    counts = set()
    for seed in TEST_SEEDS:
        torch.manual_seed(seed)
        online = V4AEncoderSkeleton()
        predictor = LatentPredictor()
        target = create_ema_target(online)
        counts.add((parameter_count(online), parameter_count(predictor)))
        gene_ids = torch.arange(16).repeat(3, 1)
        expression = torch.rand(3, 16)
        measurement = torch.ones(3, 16, dtype=torch.bool)
        context = construct_context_mask(
            measurement, mask_fraction=0.25, production_seed=seed,
            cell_indices=torch.arange(3), sample_pass=0, view_index=0,
            rule="exact_count",
        )
        online_latents = online(gene_ids, expression, measurement, context, "student")
        prediction = predictor(online_latents)
        target_latents = target(gene_ids, expression, measurement, context, "target")
        loss = jepa_prediction_loss(prediction, target_latents)
        loss.backward()
        assert torch.isfinite(loss)
        assert all(parameter.grad is None for parameter in target.parameters())
        update_ema_target(online, target, momentum=0.5)
        assert torch.isfinite(torch.tensor(ema_parameter_health(online, target).online_target_parameter_l2_distance))

        healthy = torch.randn(20, 4, 16)
        collapsed = healthy[:1].repeat(20, 1, 1)
        assert representation_health(healthy).effective_rank > representation_health(collapsed).effective_rank

        optimizer = torch.optim.SGD(list(online.parameters()) + list(predictor.parameters()), lr=0.01)
        state = capture_synthetic_checkpoint(
            online_encoder=online, target_encoder=target, predictor=predictor,
            optimizer=optimizer, global_update_step=1, ema_update_count=1,
            accumulation_position=0,
        )
        replacement_online = V4AEncoderSkeleton()
        replacement_predictor = LatentPredictor()
        replacement_target = create_ema_target(replacement_online)
        replacement_optimizer = torch.optim.SGD(
            list(replacement_online.parameters()) + list(replacement_predictor.parameters()), lr=0.01
        )
        counters = restore_synthetic_checkpoint(
            state, online_encoder=replacement_online, target_encoder=replacement_target,
            predictor=replacement_predictor, optimizer=replacement_optimizer,
        )
        assert counters["global_update_step"] == 1
        assert all(torch.equal(a, b) for a, b in zip(online.state_dict().values(), replacement_online.state_dict().values()))
    assert counts == {(730752, 206560)}
