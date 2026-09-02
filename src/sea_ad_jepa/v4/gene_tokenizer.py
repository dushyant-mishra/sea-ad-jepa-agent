"""Gene identity and continuous-expression token fusion for Stage81A3 mechanics."""

from __future__ import annotations

import torch
from torch import nn

from .contracts import MECHANICS_CONTRACT


class GeneExpressionTokenizer(nn.Module):
    """Fuse trainable gene identity with one shared continuous value encoder."""

    def __init__(
        self,
        vocabulary_size: int = MECHANICS_CONTRACT.vocabulary_size,
        identity_dim: int = MECHANICS_CONTRACT.gene_identity_dim,
        width: int = MECHANICS_CONTRACT.model_width,
        value_hidden_dim: int = 32,
    ) -> None:
        super().__init__()
        self.vocabulary_size = vocabulary_size
        self.identity_dim = identity_dim
        self.width = width
        self.gene_identity = nn.Embedding(vocabulary_size, identity_dim)
        self.identity_projection = nn.Linear(identity_dim, width)
        self.value_encoder = nn.Sequential(
            nn.Linear(1, value_hidden_dim),
            nn.GELU(),
            nn.Linear(value_hidden_dim, width),
        )
        self.output_norm = nn.LayerNorm(width)

    def forward(self, gene_ids: torch.Tensor, expression: torch.Tensor) -> torch.Tensor:
        if gene_ids.dtype is not torch.long:
            raise TypeError("gene_ids must be a torch.long tensor")
        if not expression.is_floating_point():
            raise TypeError("expression must be a floating-point tensor")
        if gene_ids.shape != expression.shape or gene_ids.ndim != 2:
            raise ValueError("gene_ids and expression must share shape [batch, genes]")
        if not torch.isfinite(expression).all():
            raise ValueError("expression must contain only finite values")
        if gene_ids.numel() and (
            int(gene_ids.min()) < 0 or int(gene_ids.max()) >= self.vocabulary_size
        ):
            raise ValueError("gene_ids fall outside the frozen vocabulary")
        identity_component = self.identity_projection(self.gene_identity(gene_ids))
        value_component = self.value_encoder(expression.unsqueeze(-1))
        return self.output_norm(identity_component + value_component)
