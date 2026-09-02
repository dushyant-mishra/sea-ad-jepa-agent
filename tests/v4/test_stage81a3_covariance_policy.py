from __future__ import annotations

import sys
from pathlib import Path

import torch

PROJECT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT / "src"))

from sea_ad_jepa.v4 import covariance_calibration


FORMULATIONS = ("pooled_cell", "per_slot", "flattened_cell_slot")


def test_covariance_is_finite_but_small_batch_estimates_are_less_reference_like() -> None:
    deviations = {formulation: {8: [], 64: []} for formulation in FORMULATIONS}
    for seed in (101, 211, 307, 401, 503):
        generator = torch.Generator().manual_seed(seed)
        reference = torch.randn(256, 4, 16, generator=generator)
        reference_values = {
            formulation: float(covariance_calibration(reference, formulation=formulation))
            for formulation in FORMULATIONS
        }
        for cells in (8, 64):
            sample = reference[:cells].clone().requires_grad_()
            for formulation in FORMULATIONS:
                value = covariance_calibration(sample, formulation=formulation)
                gradient = torch.autograd.grad(value, sample, retain_graph=True)[0]
                assert torch.isfinite(value) and torch.isfinite(gradient).all()
                deviations[formulation][cells].append(abs(float(value) - reference_values[formulation]))
    for formulation in FORMULATIONS:
        assert sum(deviations[formulation][8]) / 5 > sum(deviations[formulation][64]) / 5


def test_known_correlated_dimensions_raise_covariance_diagnostic() -> None:
    generator = torch.Generator().manual_seed(812)
    independent = torch.randn(64, 4, 16, generator=generator)
    correlated = independent.clone()
    correlated[..., 1] = correlated[..., 0]
    for formulation in FORMULATIONS:
        assert covariance_calibration(correlated, formulation=formulation) > covariance_calibration(independent, formulation=formulation)
