from __future__ import annotations

import sys
from pathlib import Path

import torch

PROJECT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT / "src"))

from sea_ad_jepa.v4 import construct_context_mask, derive_visibility_masks, keyed_mask_seed


def test_keyed_mask_is_stable_refreshable_and_hash_randomization_independent() -> None:
    measurement = torch.ones(3, 100, dtype=torch.bool)
    cells = torch.tensor([10, 20, 30])
    kwargs = dict(mask_fraction=0.4, production_seed=123, cell_indices=cells, rule="exact_count")
    first = construct_context_mask(measurement, sample_pass=0, view_index=0, **kwargs)
    assert torch.equal(first, construct_context_mask(measurement, sample_pass=0, view_index=0, **kwargs))
    assert not torch.equal(first, construct_context_mask(measurement, sample_pass=1, view_index=0, **kwargs))
    assert not torch.equal(first, construct_context_mask(measurement, sample_pass=0, view_index=1, **kwargs))
    assert keyed_mask_seed(production_seed=123, cell_index=10, sample_pass=0, view_index=0) == keyed_mask_seed(production_seed=123, cell_index=10, sample_pass=0, view_index=0)


def test_only_measured_genes_are_hidden_and_measured_zeros_remain_eligible() -> None:
    measurement = torch.tensor([[True, True, False, True, False, True]])
    expression = torch.tensor([[0.0, 2.0, 999.0, 0.0, 999.0, 3.0]])
    mask = construct_context_mask(
        measurement, mask_fraction=0.5, production_seed=77,
        cell_indices=torch.tensor([5]), sample_pass=0, view_index=0, rule="exact_count",
    )
    visibility = derive_visibility_masks(measurement, mask)
    assert not torch.any(mask & ~measurement)
    assert mask.sum() == 2
    assert torch.equal(visibility.student_valid, measurement & ~mask)
    assert torch.equal(visibility.target_valid, measurement)
    assert expression[0, 0] == 0 and measurement[0, 0]


def test_exact_count_controls_severity_while_bernoulli_adds_count_variability() -> None:
    for measured_genes in (20, 200):
        measurement = torch.ones(500, measured_genes, dtype=torch.bool)
        cells = torch.arange(500)
        exact = construct_context_mask(
            measurement, mask_fraction=0.4, production_seed=9, cell_indices=cells,
            sample_pass=0, view_index=0, rule="exact_count",
        ).sum(dim=1).float()
        bernoulli = construct_context_mask(
            measurement, mask_fraction=0.4, production_seed=9, cell_indices=cells,
            sample_pass=0, view_index=0, rule="bernoulli",
        ).sum(dim=1).float()
        assert exact.std(unbiased=False) == 0
        assert bernoulli.std(unbiased=False) > 0
        assert abs(float(bernoulli.mean() / measured_genes) - 0.4) < 0.03
        assert torch.any((bernoulli - exact).abs() >= 2)
