from __future__ import annotations

import inspect
import sys
from pathlib import Path

import torch

PROJECT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT / "src"))

from sea_ad_jepa.v4 import (
    context_target_agreement,
    representation_health,
    singular_spectrum_metrics,
    variance_floor_penalty,
)


def synthetic_cases() -> dict[str, torch.Tensor]:
    torch.manual_seed(8102)
    cells, slots, width = 48, 24, 160
    healthy = torch.randn(cells, slots, width)
    base = torch.randn(1, slots * width)
    complete = base.repeat(cells, 1).reshape(cells, slots, width)
    basis = torch.randn(2, slots * width)
    coefficients = torch.randn(cells, 2)
    partial = (coefficients @ basis).reshape(cells, slots, width)
    slot_vectors = torch.randn(cells, 1, width)
    slot_collapse = slot_vectors.repeat(1, slots, 1)
    direction = torch.randn(cells, slots * width)
    constant_norm = (
        10.0 * direction / torch.linalg.vector_norm(direction, dim=1, keepdim=True)
    ).reshape(cells, slots, width)
    return {
        "healthy": healthy,
        "complete": complete,
        "partial": partial,
        "slot_collapse": slot_collapse,
        "constant_norm": constant_norm,
    }


def test_healthy_partial_and_complete_cell_collapse_ordering() -> None:
    cases = synthetic_cases()
    healthy = representation_health(cases["healthy"])
    partial = representation_health(cases["partial"])
    complete = representation_health(cases["complete"])
    assert healthy.effective_rank > partial.effective_rank > complete.effective_rank
    assert healthy.top_singular_l1_fraction < partial.top_singular_l1_fraction < complete.top_singular_l1_fraction
    assert healthy.top_singular_energy_fraction < partial.top_singular_energy_fraction < complete.top_singular_energy_fraction
    assert healthy.pairwise_distance_median > 0
    assert partial.pairwise_distance_median > 0
    assert complete.pairwise_distance_mean == 0.0
    assert complete.cross_cell_std_mean == 0.0


def test_slot_collapse_is_distinct_from_cell_collapse() -> None:
    cases = synthetic_cases()
    healthy = representation_health(cases["healthy"])
    slot_collapse = representation_health(cases["slot_collapse"])
    assert slot_collapse.cross_cell_std_mean > 0
    assert slot_collapse.pairwise_distance_mean > 0
    assert slot_collapse.slot_variance_mean == 0.0
    assert slot_collapse.slot_cosine_similarity_mean > 0.999999
    assert healthy.slot_variance_mean > slot_collapse.slot_variance_mean
    assert healthy.slot_cosine_similarity_mean < 0.1


def test_constant_norm_does_not_imply_collapse() -> None:
    health = representation_health(synthetic_cases()["constant_norm"])
    assert health.latent_norm_std < 1e-5
    assert health.pairwise_distance_median > 10.0
    assert health.effective_rank > 20.0


def test_variance_floor_is_across_cells_and_policy_values_are_explicit() -> None:
    cases = synthetic_cases()
    collapsed_penalty, collapsed_std = variance_floor_penalty(
        cases["complete"], gamma=0.5, weight=2.0
    )
    healthy_penalty, healthy_std = variance_floor_penalty(
        cases["healthy"], gamma=0.5, weight=2.0
    )
    slot_penalty, _ = variance_floor_penalty(
        cases["slot_collapse"], gamma=0.5, weight=2.0
    )
    assert float(collapsed_std.max()) == 0.0
    assert float(healthy_std.mean()) > 0.5
    assert float(collapsed_penalty) > float(healthy_penalty) + 0.9
    assert float(slot_penalty) < float(collapsed_penalty)
    signature = inspect.signature(variance_floor_penalty)
    assert signature.parameters["gamma"].default is inspect.Parameter.empty
    assert signature.parameters["weight"].default is inspect.Parameter.empty


def test_context_target_agreement_is_transparent() -> None:
    context = torch.randn(4, 24, 160)
    identical = context_target_agreement(context, context)
    assert identical["mse"] == 0.0
    assert abs(identical["mean_cosine_similarity"] - 1.0) < 1e-6


def test_l1_and_energy_singular_fractions_are_distinct_and_exact() -> None:
    metrics = singular_spectrum_metrics(torch.tensor([4.0, 3.0]))
    assert abs(metrics["top_singular_l1_fraction"] - 4.0 / 7.0) < 1e-7
    assert abs(metrics["top_singular_energy_fraction"] - 16.0 / 25.0) < 1e-7
    assert metrics["top_singular_l1_fraction"] != metrics["top_singular_energy_fraction"]
    assert "top_sv_ratio" not in metrics
    assert "top_singular_value_fraction" not in metrics
    expected_rank = torch.exp(
        -(torch.tensor([4.0 / 7.0, 3.0 / 7.0]) * torch.log(torch.tensor([4.0 / 7.0, 3.0 / 7.0]))).sum()
    )
    assert abs(metrics["effective_rank"] - float(expected_rank)) < 1e-6


def test_rank_one_equal_spectrum_and_zero_energy_conventions() -> None:
    rank_one = singular_spectrum_metrics(torch.tensor([4.0, 0.0, 0.0]))
    assert rank_one["effective_rank"] == 1.0
    assert rank_one["top_singular_l1_fraction"] == 1.0
    assert rank_one["top_singular_energy_fraction"] == 1.0

    equal = singular_spectrum_metrics(torch.ones(4))
    assert abs(equal["effective_rank"] - 4.0) < 1e-6
    assert equal["top_singular_l1_fraction"] == 0.25
    assert equal["top_singular_energy_fraction"] == 0.25

    collapsed = singular_spectrum_metrics(torch.zeros(4))
    assert collapsed == {
        "effective_rank": 0.0,
        "top_singular_l1_fraction": 1.0,
        "top_singular_energy_fraction": 1.0,
    }
