from __future__ import annotations

import sys
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from sea_ad_jepa.v4.context_reader import CONTEXT_EXEMPLARS, ContextReader, select_context_exemplars


def fixture() -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
    torch.manual_seed(8116101)
    return torch.randn(2, 160), torch.randn(2, 12, 160), torch.rand(2, 12), torch.ones(2, 12, dtype=torch.bool)


def test_context_dimensions_and_exemplars_are_fixed() -> None:
    assert CONTEXT_EXEMPLARS == 8
    reader = ContextReader().eval()
    target, entities, distance, mask = fixture()
    output = reader(target, entities, distance, mask)
    assert output.context_summary.shape == (2, 160)
    assert output.context_exemplars.shape == (2, 8, 160)


def test_context_reader_does_not_mutate_or_backpropagate_to_intrinsic_state() -> None:
    reader = ContextReader().eval()
    target, entities, distance, mask = fixture()
    target.requires_grad_(); entities.requires_grad_()
    before_target, before_entities = target.detach().clone(), entities.detach().clone()
    reader(target, entities, distance, mask).context_summary.sum().backward()
    assert target.grad is None and entities.grad is None
    assert torch.equal(target.detach(), before_target)
    assert torch.equal(entities.detach(), before_entities)


def test_null_context_is_finite_and_zero() -> None:
    reader = ContextReader().eval()
    target, entities, distance, mask = fixture(); mask[:] = False
    output = reader(target, entities, distance, mask)
    assert torch.isfinite(output.context_summary).all()
    assert torch.equal(output.context_summary, torch.zeros_like(output.context_summary))


def test_directional_context_is_not_forced_symmetric() -> None:
    reader = ContextReader().eval()
    a, b = torch.randn(1, 160), torch.randn(1, 160)
    mask = torch.ones(1, 1, dtype=torch.bool); distance = torch.ones(1, 1)
    assert not torch.equal(reader(a, b[:, None], distance, mask).context_summary, reader(b, a[:, None], distance, mask).context_summary)


def test_high_relevance_rare_entity_survives_many_irrelevant_neighbors() -> None:
    values = torch.arange(20.0).reshape(1, 20, 1)
    scores = torch.zeros(1, 20); scores[0, 17] = 100
    selected, indices = select_context_exemplars(values, scores, torch.ones(1, 20, dtype=torch.bool))
    assert 17 in indices[0].tolist()
    assert 17.0 in selected[0, :, 0].tolist()
