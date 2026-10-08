from __future__ import annotations

import sys
from pathlib import Path

import torch

PROJECT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT / "src"))

from sea_ad_jepa.v4 import variance_floor_calibration


FORMULATIONS = ("pooled_cell", "per_slot", "flattened_cell_slot", "combined")


def fixtures(seed: int = 101, cells: int = 32, slots: int = 8, width: int = 16):
    generator = torch.Generator().manual_seed(seed)
    healthy = torch.randn(cells, slots, width, generator=generator)
    diverse_slots = torch.randn(1, slots, width, generator=generator)
    cell_collapse = diverse_slots.repeat(cells, 1, 1)
    diverse_cells = torch.randn(cells, 1, width, generator=generator)
    slot_collapse = diverse_cells.repeat(1, slots, 1)
    both = torch.ones(cells, slots, width)
    coefficients = torch.randn(cells, 2, generator=generator)
    basis = torch.randn(2, slots * width, generator=generator)
    low_rank = (coefficients @ basis).reshape(cells, slots, width)
    direction = torch.randn(cells, slots * width, generator=generator)
    constant_norm = (10 * direction / direction.norm(dim=1, keepdim=True)).reshape(cells, slots, width)
    dominant = healthy + 4 * torch.randn(cells, 1, 1, generator=generator)
    return locals()


def penalty(latents, formulation, gamma=0.5):
    return float(variance_floor_calibration(latents, gamma=gamma, formulation=formulation))


def test_flattening_can_hide_complete_cell_collapse_with_diverse_slots() -> None:
    cases = fixtures()
    pooled = penalty(cases["cell_collapse"], "pooled_cell")
    per_slot = penalty(cases["cell_collapse"], "per_slot")
    flattened = penalty(cases["cell_collapse"], "flattened_cell_slot")
    combined = penalty(cases["cell_collapse"], "combined")
    assert pooled > 0.49
    assert per_slot > 0.49
    assert combined > 0.49
    assert flattened < 0.05


def test_cross_cell_variance_losses_do_not_detect_slot_only_collapse() -> None:
    cases = fixtures()
    assert all(penalty(cases["slot_collapse"], formulation) < 0.05 for formulation in FORMULATIONS)
    assert all(penalty(cases["both"], formulation) > 0.49 for formulation in FORMULATIONS)


def test_formulations_are_scale_sensitive_and_do_not_replace_rank_telemetry() -> None:
    cases = fixtures()
    for formulation in FORMULATIONS:
        small = penalty(cases["healthy"] * 0.05, formulation)
        ordinary = penalty(cases["healthy"], formulation)
        assert small > ordinary
        assert torch.isfinite(torch.tensor(penalty(cases["low_rank"], formulation)))
        assert torch.isfinite(torch.tensor(penalty(cases["constant_norm"], formulation)))
        assert torch.isfinite(torch.tensor(penalty(cases["dominant"], formulation)))


def test_batch_gamma_and_gradient_calibration_is_finite_across_seeds() -> None:
    for cells in (4, 8, 16, 32, 64, 256):
        for seed in (101, 211, 307, 401, 503):
            latents = fixtures(seed=seed, cells=cells, slots=4, width=8)["healthy"].requires_grad_()
            for formulation in FORMULATIONS:
                for gamma in (0.05, 0.10, 0.25, 0.50, 1.00):
                    value = variance_floor_calibration(latents, gamma=gamma, formulation=formulation)
                    gradient = torch.autograd.grad(value, latents, retain_graph=True)[0]
                    assert torch.isfinite(value)
                    assert torch.isfinite(gradient).all()


def test_weight_gradient_ratio_scales_linearly_without_freezing_a_weight() -> None:
    generator = torch.Generator().manual_seed(701)
    target = torch.randn(16, 8, 16, generator=generator)
    for scale in (1.0, 0.2, 0.01):
        prediction = (scale * torch.randn(16, 8, 16, generator=generator)).requires_grad_()
        primary = (prediction - target).square().mean()
        primary_gradient = torch.autograd.grad(primary, prediction, retain_graph=True)[0].norm()
        variance = variance_floor_calibration(prediction, gamma=0.5, formulation="combined")
        base_variance_gradient = torch.autograd.grad(variance, prediction, retain_graph=True)[0]
        for weight in (0.001, 0.01, 0.1, 1.0):
            ratio = weight * base_variance_gradient.norm() / primary_gradient
            assert torch.isfinite(ratio)
        assert primary_gradient > 0
