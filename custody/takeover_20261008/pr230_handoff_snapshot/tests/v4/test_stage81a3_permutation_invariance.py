from __future__ import annotations

import sys
from pathlib import Path

import pytest
import torch

PROJECT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT / "src"))

from sea_ad_jepa.v4 import GeneSetMechanicsEncoder


PERMUTATION_RTOL = 1e-6
PERMUTATION_ATOL = 1e-6


@pytest.mark.parametrize("view", ["student", "target"])
def test_gene_order_permutation_invariance(view: str) -> None:
    torch.manual_seed(8102)
    model = GeneSetMechanicsEncoder().eval()
    gene_ids = torch.tensor([[2, 5, 11, 23, 41, 89]])
    expression = torch.tensor([[0.0, 0.2, 0.5, 1.0, 2.0, 4.0]])
    measurement = torch.tensor([[True, True, False, True, True, True]])
    context = torch.tensor([[False, True, False, False, False, True]])
    reference = model(gene_ids, expression, measurement, context, view)
    permutation = torch.tensor([4, 1, 5, 0, 3, 2])
    permuted = model(
        gene_ids[:, permutation],
        expression[:, permutation],
        measurement[:, permutation],
        context[:, permutation],
        view,
    )
    torch.testing.assert_close(
        permuted,
        reference,
        rtol=PERMUTATION_RTOL,
        atol=PERMUTATION_ATOL,
    )


def test_minimal_encoder_parameter_count() -> None:
    torch.manual_seed(8102)
    model = GeneSetMechanicsEncoder()
    tokenizer_count = sum(parameter.numel() for parameter in model.tokenizer.parameters())
    encoder_count = sum(parameter.numel() for parameter in model.encoder.parameters())
    assert tokenizer_count == 210_112
    assert encoder_count == 107_200
    assert tokenizer_count + encoder_count == 317_312
