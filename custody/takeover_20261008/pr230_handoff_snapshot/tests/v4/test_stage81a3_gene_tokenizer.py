from __future__ import annotations

import sys
from pathlib import Path

import torch

PROJECT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT / "src"))

from sea_ad_jepa.v4 import GeneExpressionTokenizer, MECHANICS_CONTRACT


def tokenizer() -> GeneExpressionTokenizer:
    torch.manual_seed(8102)
    model = GeneExpressionTokenizer()
    model.eval()
    return model


def test_contract_dimensions_and_no_frozen_mask_percentage() -> None:
    assert MECHANICS_CONTRACT.stage81a2_evidence_commit == "808ce4f170055c5568cc5c1e0e3a56415b52f908"
    assert MECHANICS_CONTRACT.vocabulary_size == 4096
    assert MECHANICS_CONTRACT.vocabulary_semantic_hash == (
        "f2759db27218c7f9e716974bbdb7c6bcdfc2858a6b3e1acca4d7d97eea2abecb"
    )
    assert MECHANICS_CONTRACT.gene_identity_dim == 48
    assert MECHANICS_CONTRACT.model_width == 160
    assert MECHANICS_CONTRACT.latent_slots == 24
    assert MECHANICS_CONTRACT.attention_heads == 4
    assert not hasattr(MECHANICS_CONTRACT, "mask_fraction")


def test_different_genes_remain_distinct_at_equal_expression() -> None:
    model = tokenizer()
    gene_ids = torch.tensor([[3, 17]], dtype=torch.long)
    for value in (0.0, 2.0):
        tokens = model(gene_ids, torch.full((1, 2), value))
        assert not torch.allclose(tokens[:, 0], tokens[:, 1])


def test_same_gene_token_changes_with_continuous_expression() -> None:
    model = tokenizer()
    gene_ids = torch.tensor([[11, 11, 11, 11, 11]], dtype=torch.long)
    values = torch.tensor([[0.0, 0.5, 1.0, 2.0, 4.0]])
    tokens = model(gene_ids, values)[0]
    assert all(not torch.allclose(tokens[left], tokens[right]) for left, right in zip(range(4), range(1, 5)))


def test_measured_zero_token_retains_gene_identity() -> None:
    model = tokenizer()
    tokens = model(torch.tensor([[1, 2]]), torch.zeros(1, 2))
    assert torch.isfinite(tokens).all()
    assert not torch.allclose(tokens[0, 0], tokens[0, 1])


def test_continuous_value_encoder_is_numerically_healthy() -> None:
    model = tokenizer()
    gene_ids = torch.full((1, 4), 7, dtype=torch.long)
    values = torch.tensor([[2.000, 2.001, 2.010, 2.100]])
    tokens = model(gene_ids, values)[0]
    assert torch.isfinite(tokens).all()
    adjacent_jumps = torch.linalg.vector_norm(tokens[1:] - tokens[:-1], dim=-1)
    assert torch.all(adjacent_jumps > 0)
    assert float(adjacent_jumps[0]) < 0.1


def test_gradients_reach_identity_projection_and_shared_value_encoder() -> None:
    model = tokenizer()
    gene_ids = torch.tensor([[5, 9, 12]], dtype=torch.long)
    expression = torch.tensor([[0.0, 0.5, 2.0]])
    tokens = model(gene_ids, expression)
    coefficients = torch.linspace(0.1, 1.0, tokens.shape[-1])
    objective = (tokens * coefficients).sum()
    objective.backward()
    parameters = (
        model.gene_identity.weight,
        model.identity_projection.weight,
        model.value_encoder[0].weight,
        model.value_encoder[2].weight,
    )
    for parameter in parameters:
        assert parameter.grad is not None
        assert torch.isfinite(parameter.grad).all()
        assert torch.count_nonzero(parameter.grad) > 0


def test_tokenizer_parameter_count_and_trainable_identity() -> None:
    model = tokenizer()
    assert model.gene_identity.weight.requires_grad
    assert sum(parameter.numel() for parameter in model.parameters()) == 210_112
