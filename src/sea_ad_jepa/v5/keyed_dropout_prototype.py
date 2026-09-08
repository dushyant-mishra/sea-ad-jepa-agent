"""Proof-only keyed-dropout encoder for V5 packing equivalence.

This module is deliberately not wired into production_update.  It preserves the
V4 encoder parameterization while replacing position/shape-dependent nn.Dropout
sampling with a stateless identity-keyed proof primitive.  The hash/PRNG used by
the proof is not itself production RNG authority; a production implementation
must separately bind a reviewed counter-based RNG algorithm and device behavior.
"""
from __future__ import annotations

import torch
from torch import nn

from sea_ad_jepa.v4.gene_tokenizer import GeneExpressionTokenizer
from sea_ad_jepa.v4.ipb_jepa import EncoderOutput, KernelLinearAttention
from .data_first_geometry import keyed_feature_dropout


class KeyedTokenPreservingBlockPrototype(nn.Module):
    """V4-parameter-compatible block with identity-keyed dropout calls."""

    def __init__(self, width: int = 160, heads: int = 4, ffn_width: int = 320, dropout: float = 0.10) -> None:
        super().__init__()
        self.attention_norm = nn.LayerNorm(width)
        self.attention = KernelLinearAttention(width, heads)
        # Retained under the exact V4 module name so state_dict structure stays compatible.
        self.attention_dropout = nn.Dropout(dropout)
        self.ffn_norm = nn.LayerNorm(width)
        self.ffn = nn.Sequential(
            nn.Linear(width, ffn_width), nn.GELU(), nn.Dropout(dropout),
            nn.Linear(ffn_width, width), nn.Dropout(dropout),
        )

    def forward(
        self,
        tokens: torch.Tensor,
        valid_mask: torch.Tensor,
        *,
        cell_keys: torch.Tensor,
        token_keys: torch.Tensor,
        update_index: int,
        view_index: int,
        layer_index: int,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        attended, minimum = self.attention(self.attention_norm(tokens), valid_mask)
        attended = keyed_feature_dropout(
            attended,
            cell_keys=cell_keys,
            token_keys=token_keys,
            probability=float(self.attention_dropout.p),
            update_index=update_index,
            view_index=view_index,
            layer_index=layer_index,
            site_index=0,
            training=self.training,
        )
        tokens = tokens + attended
        hidden = self.ffn[1](self.ffn[0](self.ffn_norm(tokens)))
        hidden = keyed_feature_dropout(
            hidden,
            cell_keys=cell_keys,
            token_keys=token_keys,
            probability=float(self.ffn[2].p),
            update_index=update_index,
            view_index=view_index,
            layer_index=layer_index,
            site_index=1,
            training=self.training,
        )
        hidden = self.ffn[3](hidden)
        hidden = keyed_feature_dropout(
            hidden,
            cell_keys=cell_keys,
            token_keys=token_keys,
            probability=float(self.ffn[4].p),
            update_index=update_index,
            view_index=view_index,
            layer_index=layer_index,
            site_index=2,
            training=self.training,
        )
        return tokens + hidden, minimum


class KeyedIPBEncoderPrototype(nn.Module):
    """V4-parameter-compatible encoder proving train-mode packing invariance."""

    def __init__(
        self,
        *,
        width: int = 160,
        heads: int = 4,
        blocks: int = 6,
        ffn_width: int = 320,
        dropout: float = 0.10,
        vocabulary_size: int = 41_238,
    ) -> None:
        super().__init__()
        self.tokenizer = GeneExpressionTokenizer(vocabulary_size=vocabulary_size, width=width)
        self.cell_token = nn.Parameter(torch.empty(1, 1, width))
        nn.init.normal_(self.cell_token, mean=0.0, std=0.02)
        self.blocks = nn.ModuleList([
            KeyedTokenPreservingBlockPrototype(width, heads, ffn_width, dropout)
            for _ in range(blocks)
        ])
        self.final_norm = nn.LayerNorm(width)

    def forward(
        self,
        gene_ids: torch.Tensor,
        expression: torch.Tensor,
        measurement_mask: torch.Tensor,
        hidden_target_mask: torch.Tensor,
        view: str,
        *,
        cell_keys: torch.Tensor,
        update_index: int,
        view_index: int,
    ) -> EncoderOutput:
        if view == 'student':
            gene_valid = measurement_mask & ~hidden_target_mask
        elif view == 'target':
            gene_valid = measurement_mask
        else:
            raise ValueError('view must be student or target')
        if gene_ids.shape != expression.shape or measurement_mask.shape != expression.shape or hidden_target_mask.shape != expression.shape:
            raise ValueError('gene_ids/expression/masks must share [cells,genes] shape')
        if gene_ids.dtype != torch.int64 or measurement_mask.dtype != torch.bool or hidden_target_mask.dtype != torch.bool:
            raise ValueError('gene_ids must be int64 and masks boolean')
        if cell_keys.ndim != 1 or len(cell_keys) != len(expression) or cell_keys.dtype != torch.int64:
            raise ValueError('cell_keys must be int64 [cells]')
        if torch.any(~gene_valid.any(dim=1)):
            raise ValueError('every cell must have at least one valid gene')
        safe_expression = expression.masked_fill(~gene_valid, 0.0)
        gene_tokens = self.tokenizer(gene_ids, safe_expression)
        cell = self.cell_token.expand(len(expression), -1, -1)
        tokens = torch.cat((cell, gene_tokens), dim=1)
        valid = torch.cat((torch.ones(len(expression), 1, dtype=torch.bool, device=expression.device), gene_valid), dim=1)
        # -1 is a reserved identity key for the cell token; gene identities remain canonical.
        cell_token_key = torch.full((len(expression), 1), -1, dtype=torch.int64, device=expression.device)
        token_keys = torch.cat((cell_token_key, gene_ids), dim=1)
        minima=[]
        for layer_index, block in enumerate(self.blocks):
            tokens, minimum = block(
                tokens, valid,
                cell_keys=cell_keys,
                token_keys=token_keys,
                update_index=update_index,
                view_index=view_index,
                layer_index=layer_index,
            )
            minima.append(minimum)
        tokens=self.final_norm(tokens)
        return EncoderOutput(tokens[:,1:], tokens[:,0], torch.stack(minima).amin())
