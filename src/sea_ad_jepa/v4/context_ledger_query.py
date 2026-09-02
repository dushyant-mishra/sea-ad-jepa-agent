"""Read-only fine molecular queries over selected context exemplars."""

from __future__ import annotations

import torch
from torch import nn


class LedgerQuery(nn.Module):
    def __init__(self, width: int = 160, heads: int = 4) -> None:
        super().__init__()
        self.attention = nn.MultiheadAttention(width, heads, batch_first=True)

    def forward(self, target_query: torch.Tensor, neighbor_ledgers: torch.Tensor, token_mask: torch.Tensor | None = None) -> torch.Tensor:
        if neighbor_ledgers.ndim != 4:
            raise ValueError("neighbor_ledgers must be [batch, exemplars, genes, width]")
        batch, exemplars, genes, width = neighbor_ledgers.shape
        query = target_query.detach()[:, None, :].expand(batch, exemplars, width).reshape(batch * exemplars, 1, width)
        ledger = neighbor_ledgers.detach().reshape(batch * exemplars, genes, width)
        padding = None if token_mask is None else ~token_mask.reshape(batch * exemplars, genes).bool()
        output, _ = self.attention(query, ledger, ledger, key_padding_mask=padding, need_weights=False)
        return output.reshape(batch, exemplars, width)
