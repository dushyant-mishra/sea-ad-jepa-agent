"""Minimal permutation-invariant gene-set cross-attention mechanics."""

from __future__ import annotations

from typing import Literal

import torch
import torch.nn.functional as F
from torch import nn

from .contracts import MECHANICS_CONTRACT, derive_visibility_masks
from .gene_tokenizer import GeneExpressionTokenizer


def _normalize_valid_gene_logits(
    raw_logits: torch.Tensor,
    valid_mask: torch.Tensor,
) -> torch.Tensor:
    """Normalize each cell/head/slot over valid genes in float32."""
    raw_logits = raw_logits.float()
    valid = valid_mask[:, None, None, :]
    count = valid.sum(dim=-1, keepdim=True).clamp_min(1)
    masked_logits = torch.where(valid, raw_logits, torch.zeros_like(raw_logits))
    mean = masked_logits.sum(dim=-1, keepdim=True) / count
    centered = torch.where(valid, raw_logits - mean, torch.zeros_like(raw_logits))
    variance = centered.square().sum(dim=-1, keepdim=True) / count
    standard_deviation = variance.sqrt().clamp_min(1e-6)
    return ((raw_logits - mean) / standard_deviation).masked_fill(~valid, -torch.inf)


class PerceiverCrossAttention(nn.Module):
    """Apply one masked gene-token to learned-latent cross-attention operation."""

    def __init__(
        self,
        latent_slots: int = MECHANICS_CONTRACT.latent_slots,
        width: int = MECHANICS_CONTRACT.model_width,
        attention_heads: int = MECHANICS_CONTRACT.attention_heads,
        routing_mode: Literal["native", "variance_normalized"] = "native",
    ) -> None:
        super().__init__()
        if routing_mode not in ("native", "variance_normalized"):
            raise ValueError("routing_mode must be 'native' or 'variance_normalized'")
        self.latent_slots = latent_slots
        self.width = width
        self.routing_mode = routing_mode
        self.latents = nn.Parameter(torch.empty(latent_slots, width))
        nn.init.normal_(self.latents, mean=0.0, std=0.02)
        self.cross_attention = nn.MultiheadAttention(
            embed_dim=width,
            num_heads=attention_heads,
            dropout=0.0,
            batch_first=True,
        )
        self.output_norm = nn.LayerNorm(width)

    def _variance_normalized_forward(
        self,
        gene_tokens: torch.Tensor,
        valid_mask: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        module = self.cross_attention
        width = module.embed_dim
        heads = module.num_heads
        head_width = width // heads
        queries = self.latents.unsqueeze(0).expand(gene_tokens.shape[0], -1, -1)
        q = F.linear(
            queries.float(),
            module.in_proj_weight[:width].float(),
            module.in_proj_bias[:width].float(),
        )
        k = F.linear(
            gene_tokens.float(),
            module.in_proj_weight[width:2 * width].float(),
            module.in_proj_bias[width:2 * width].float(),
        )
        v = F.linear(
            gene_tokens.float(),
            module.in_proj_weight[2 * width:].float(),
            module.in_proj_bias[2 * width:].float(),
        )
        q = q.reshape(len(gene_tokens), self.latent_slots, heads, head_width).permute(0, 2, 1, 3)
        k = k.reshape(len(gene_tokens), gene_tokens.shape[1], heads, head_width).permute(0, 2, 1, 3)
        v = v.reshape(len(gene_tokens), gene_tokens.shape[1], heads, head_width).permute(0, 2, 1, 3)
        raw_logits = torch.matmul(q, k.transpose(-1, -2)) / (head_width**0.5)
        normalized_logits = _normalize_valid_gene_logits(raw_logits, valid_mask)
        attention = torch.softmax(normalized_logits, dim=-1)
        attended = torch.matmul(attention, v)
        attended = attended.permute(0, 2, 1, 3).reshape(
            len(gene_tokens), self.latent_slots, width
        )
        attended = F.linear(
            attended,
            module.out_proj.weight.float(),
            module.out_proj.bias.float(),
        )
        representation = self.output_norm(queries.float() + attended)
        return representation, attention, raw_logits, normalized_logits

    def routing_diagnostics(
        self,
        gene_tokens: torch.Tensor,
        valid_mask: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        """Return candidate representation, attention, and raw/normalized logits."""
        if self.routing_mode != "variance_normalized":
            raise RuntimeError("routing diagnostics require variance_normalized mode")
        return self._variance_normalized_forward(gene_tokens, valid_mask)

    def forward(
        self,
        gene_tokens: torch.Tensor,
        valid_mask: torch.Tensor,
        return_attention: bool = False,
    ) -> torch.Tensor | tuple[torch.Tensor, torch.Tensor]:
        if gene_tokens.ndim != 3:
            raise ValueError("gene_tokens must have shape [batch, genes, width]")
        if valid_mask.dtype is not torch.bool or valid_mask.shape != gene_tokens.shape[:2]:
            raise ValueError("valid_mask must be boolean with shape [batch, genes]")
        if gene_tokens.shape[-1] != self.width:
            raise ValueError("gene token width does not match the mechanics contract")
        if torch.any(~valid_mask.any(dim=1)):
            raise ValueError("each cell view must contain at least one attention-valid gene")
        queries = self.latents.unsqueeze(0).expand(gene_tokens.shape[0], -1, -1)
        if self.routing_mode == "variance_normalized":
            representation, attention, _, _ = self._variance_normalized_forward(
                gene_tokens, valid_mask
            )
        else:
            attended, attention = self.cross_attention(
                query=queries,
                key=gene_tokens,
                value=gene_tokens,
                key_padding_mask=~valid_mask,
                need_weights=return_attention,
                average_attn_weights=False,
            )
            representation = self.output_norm(queries + attended)
        if return_attention:
            return representation, attention
        return representation


class GeneSetMechanicsEncoder(nn.Module):
    """Synthetic-only tokenizer plus one Perceiver cross-attention operation."""

    def __init__(self) -> None:
        super().__init__()
        self.tokenizer = GeneExpressionTokenizer()
        self.encoder = PerceiverCrossAttention()

    def forward(
        self,
        gene_ids: torch.Tensor,
        expression: torch.Tensor,
        measurement_mask: torch.Tensor,
        context_mask: torch.Tensor,
        view: Literal["student", "target"],
        return_attention: bool = False,
    ) -> torch.Tensor | tuple[torch.Tensor, torch.Tensor]:
        visibility = derive_visibility_masks(measurement_mask, context_mask)
        if view == "student":
            valid_mask = visibility.student_valid
        elif view == "target":
            valid_mask = visibility.target_valid
        else:
            raise ValueError("view must be 'student' or 'target'")
        gene_tokens = self.tokenizer(gene_ids, expression)
        return self.encoder(gene_tokens, valid_mask, return_attention=return_attention)


class LatentTransformerBlock(nn.Module):
    """PreNorm latent self-attention and feed-forward residual block."""

    def __init__(
        self,
        width: int = MECHANICS_CONTRACT.model_width,
        attention_heads: int = MECHANICS_CONTRACT.attention_heads,
        ffn_width: int = 320,
        dropout: float = 0.10,
    ) -> None:
        super().__init__()
        self.attention_norm = nn.LayerNorm(width)
        self.self_attention = nn.MultiheadAttention(
            embed_dim=width,
            num_heads=attention_heads,
            dropout=dropout,
            batch_first=True,
        )
        self.feed_forward_norm = nn.LayerNorm(width)
        self.feed_forward = nn.Sequential(
            nn.Linear(width, ffn_width),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(ffn_width, width),
            nn.Dropout(dropout),
        )

    def forward(self, latents: torch.Tensor) -> torch.Tensor:
        normalized = self.attention_norm(latents)
        attended, _ = self.self_attention(
            normalized,
            normalized,
            normalized,
            need_weights=False,
        )
        latents = latents + attended
        return latents + self.feed_forward(self.feed_forward_norm(latents))


class V4AEncoderSkeleton(nn.Module):
    """Locked v4A encoder mechanics without predictor, target updates, or loss."""

    def __init__(
        self,
        gene_attention_mode: Literal["native", "variance_normalized"] = "native",
    ) -> None:
        super().__init__()
        self.tokenizer = GeneExpressionTokenizer()
        self.cross_attention = PerceiverCrossAttention(routing_mode=gene_attention_mode)
        self.latent_blocks = nn.ModuleList(
            [LatentTransformerBlock(), LatentTransformerBlock()]
        )
        self.final_norm = nn.LayerNorm(MECHANICS_CONTRACT.model_width)

    def forward(
        self,
        gene_ids: torch.Tensor,
        expression: torch.Tensor,
        measurement_mask: torch.Tensor,
        context_mask: torch.Tensor,
        view: Literal["student", "target"],
    ) -> torch.Tensor:
        visibility = derive_visibility_masks(measurement_mask, context_mask)
        if view == "student":
            valid_mask = visibility.student_valid
        elif view == "target":
            valid_mask = visibility.target_valid
        else:
            raise ValueError("view must be 'student' or 'target'")
        latents = self.cross_attention(self.tokenizer(gene_ids, expression), valid_mask)
        for block in self.latent_blocks:
            latents = block(latents)
        return self.final_norm(latents)
