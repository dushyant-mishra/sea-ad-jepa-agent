"""Lightweight latent-only predictor mechanics for Stage81A3 Decision 5."""

from __future__ import annotations

import torch
from torch import nn

from .contracts import MECHANICS_CONTRACT


class LatentPredictor(nn.Module):
    """One PreNorm Transformer-style block over corresponding latent slots."""

    def __init__(
        self,
        width: int = MECHANICS_CONTRACT.model_width,
        attention_heads: int = MECHANICS_CONTRACT.attention_heads,
        ffn_width: int = 320,
    ) -> None:
        super().__init__()
        self.width = width
        self.attention_norm = nn.LayerNorm(width)
        self.self_attention = nn.MultiheadAttention(
            embed_dim=width,
            num_heads=attention_heads,
            dropout=0.0,
            batch_first=True,
        )
        self.feed_forward_norm = nn.LayerNorm(width)
        self.feed_forward = nn.Sequential(
            nn.Linear(width, ffn_width),
            nn.GELU(),
            nn.Linear(ffn_width, width),
        )

    def forward(self, context_latents: torch.Tensor) -> torch.Tensor:
        expected = (MECHANICS_CONTRACT.latent_slots, self.width)
        if context_latents.ndim != 3 or tuple(context_latents.shape[1:]) != expected:
            raise ValueError(
                "context_latents must have shape [batch, 24, 160]"
            )
        if not context_latents.is_floating_point() or not torch.isfinite(context_latents).all():
            raise ValueError("context_latents must be finite floating-point values")
        normalized = self.attention_norm(context_latents)
        attended, _ = self.self_attention(
            normalized,
            normalized,
            normalized,
            need_weights=False,
        )
        predicted = context_latents + attended
        return predicted + self.feed_forward(self.feed_forward_norm(predicted))
