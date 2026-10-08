"""One-way, read-only target-to-context attention without message passing."""

from __future__ import annotations

from typing import NamedTuple

import torch
from torch import nn


CONTEXT_EXEMPLARS = 8


def select_context_exemplars(values: torch.Tensor, scores: torch.Tensor, mask: torch.Tensor, k: int = CONTEXT_EXEMPLARS) -> tuple[torch.Tensor, torch.Tensor]:
    """Retain the highest-scoring valid entity tokens without averaging them."""
    ranked = scores.masked_fill(~mask.bool(), float("-inf"))
    count = min(k, values.shape[1])
    indices = ranked.topk(count, dim=1).indices
    selected = torch.gather(values, 1, indices[..., None].expand(-1, -1, values.shape[-1]))
    selected = selected * torch.gather(mask.bool(), 1, indices)[..., None]
    if count < k:
        pad = k - count
        selected = torch.cat((selected, selected.new_zeros(len(selected), pad, values.shape[-1])), 1)
        indices = torch.cat((indices, indices.new_full((len(indices), pad), -1)), 1)
    return selected, indices


class ContextReaderOutput(NamedTuple):
    context_summary: torch.Tensor
    context_exemplars: torch.Tensor
    exemplar_indices: torch.Tensor
    context_evidence_mask: torch.Tensor
    valid_entity_count: torch.Tensor
    missing_context_fraction: torch.Tensor


class ContextReader(nn.Module):
    """Single directional cross-attention block; intrinsic inputs are detached."""

    def __init__(self, width: int = 160, heads: int = 4, ffn_width: int = 320, dropout: float = 0.10, exemplars: int = CONTEXT_EXEMPLARS) -> None:
        super().__init__()
        self.width = width
        self.exemplars = exemplars
        self.query = nn.Linear(width, width)
        self.key = nn.Linear(width + 2, width)
        self.value = nn.Linear(width + 2, width)
        self.attention = nn.MultiheadAttention(width, heads, dropout=dropout, batch_first=True)
        self.norm = nn.LayerNorm(width)
        self.ffn = nn.Sequential(nn.Linear(width, ffn_width), nn.GELU(), nn.Dropout(dropout), nn.Linear(ffn_width, width))

    def forward(self, target_state: torch.Tensor, entity_states: torch.Tensor, distances: torch.Tensor, evidence_mask: torch.Tensor) -> ContextReaderOutput:
        target = target_state.detach()
        entities = entity_states.detach()
        mask = evidence_mask.bool()
        if entities.ndim != 3 or distances.shape != entities.shape[:2] or mask.shape != entities.shape[:2]:
            raise ValueError("context tensors have incompatible shapes")
        relation = torch.stack((torch.log1p(distances.clamp_min(0)).float(), mask.float()), dim=-1)
        joined = torch.cat((entities, relation), dim=-1)
        query, key, value = self.query(target)[:, None], self.key(joined), self.value(joined)
        safe_mask = mask.clone()
        empty = ~safe_mask.any(1)
        safe_mask[empty, 0] = True
        pooled, weights = self.attention(query, key, value, key_padding_mask=~safe_mask, need_weights=True, average_attn_weights=True)
        pooled = pooled[:, 0]
        pooled[empty] = 0
        summary = self.norm(pooled + self.ffn(pooled))
        summary[empty] = 0
        exemplars, indices = select_context_exemplars(value, weights[:, 0], mask, self.exemplars)
        count = mask.sum(1)
        return ContextReaderOutput(summary, exemplars, indices, mask, count, 1.0 - count.float() / mask.shape[1])
