"""Inactive V5 proof encoder with dropout keyed to scientific identity.

This module exists to test dense-versus-packed stochastic equivalence. It is
not imported by the V4 production runtime and carries no training authority.
"""
from __future__ import annotations

import torch
from torch import nn

from sea_ad_jepa.v4.gene_tokenizer import GeneExpressionTokenizer
from sea_ad_jepa.v4.ipb_jepa import EncoderOutput, KernelLinearAttention
from .keyed_rng_v1 import KeyedDropoutSpec, keyed_dropout, keyed_dropout_mask


class KeyedTokenPreservingBlockProofV1(nn.Module):
    def __init__(
        self,
        *,
        width:int=160,
        heads:int=4,
        ffn_width:int=320,
        dropout_numerator:int=1,
        dropout_denominator:int=10,
    )->None:
        super().__init__()
        self.attention_norm=nn.LayerNorm(width)
        self.attention=KernelLinearAttention(width,heads)
        self.attention_dropout=nn.Dropout(dropout_numerator/dropout_denominator)
        self.ffn_norm=nn.LayerNorm(width)
        self.ffn=nn.Sequential(
            nn.Linear(width,ffn_width),
            nn.GELU(),
            nn.Dropout(dropout_numerator/dropout_denominator),
            nn.Linear(ffn_width,width),
            nn.Dropout(dropout_numerator/dropout_denominator),
        )
        self.dropout_spec=KeyedDropoutSpec(dropout_numerator,dropout_denominator)

    def _drop(
        self,
        value:torch.Tensor,
        canonical_token_ids:torch.Tensor,
        cell_keys:torch.Tensor,
        *,
        training_seed:int,
        update_index:int,
        view_index:int,
        site_id:int,
    )->torch.Tensor:
        if not self.training:
            return value
        mask=keyed_dropout_mask(
            canonical_token_ids,
            cell_keys,
            width=value.shape[-1],
            training_seed=training_seed,
            update_index=update_index,
            view_index=view_index,
            site_id=site_id,
            spec=self.dropout_spec,
        )
        return keyed_dropout(value,mask,self.dropout_spec)

    def forward(
        self,
        tokens:torch.Tensor,
        valid_mask:torch.Tensor,
        canonical_token_ids:torch.Tensor,
        cell_keys:torch.Tensor,
        *,
        training_seed:int,
        update_index:int,
        view_index:int,
        layer_index:int,
    )->tuple[torch.Tensor,torch.Tensor]:
        attended,minimum=self.attention(self.attention_norm(tokens),valid_mask)
        attended=self._drop(
            attended,canonical_token_ids,cell_keys,
            training_seed=training_seed,update_index=update_index,view_index=view_index,
            site_id=3*layer_index,
        )
        tokens=tokens+attended
        hidden=self.ffn[1](self.ffn[0](self.ffn_norm(tokens)))
        hidden=self._drop(
            hidden,canonical_token_ids,cell_keys,
            training_seed=training_seed,update_index=update_index,view_index=view_index,
            site_id=3*layer_index+1,
        )
        hidden=self.ffn[3](hidden)
        hidden=self._drop(
            hidden,canonical_token_ids,cell_keys,
            training_seed=training_seed,update_index=update_index,view_index=view_index,
            site_id=3*layer_index+2,
        )
        return tokens+hidden,minimum


class KeyedIPBEncoderProofV1(nn.Module):
    """V4-parameter-compatible encoder for V5 dense/packed proof attacks."""

    def __init__(
        self,
        *,
        vocabulary_size:int,
        width:int=160,
        heads:int=4,
        blocks:int=6,
        ffn_width:int=320,
        dropout_numerator:int=1,
        dropout_denominator:int=10,
    )->None:
        super().__init__()
        self.tokenizer=GeneExpressionTokenizer(vocabulary_size=vocabulary_size,width=width)
        self.cell_token=nn.Parameter(torch.empty(1,1,width))
        nn.init.normal_(self.cell_token,mean=0.0,std=0.02)
        self.blocks=nn.ModuleList([
            KeyedTokenPreservingBlockProofV1(
                width=width,heads=heads,ffn_width=ffn_width,
                dropout_numerator=dropout_numerator,
                dropout_denominator=dropout_denominator,
            )
            for _ in range(blocks)
        ])
        self.final_norm=nn.LayerNorm(width)

    def forward(
        self,
        gene_ids:torch.Tensor,
        expression:torch.Tensor,
        measurement_mask:torch.Tensor,
        hidden_target_mask:torch.Tensor,
        view:str,
        *,
        cell_keys:torch.Tensor,
        training_seed:int,
        update_index:int,
        view_index:int,
    )->EncoderOutput:
        if view=='student':
            gene_valid=measurement_mask & ~hidden_target_mask
        elif view=='target':
            gene_valid=measurement_mask
        else:
            raise ValueError('view must be student or target')
        if torch.any(~gene_valid.any(dim=1)):
            raise ValueError('every cell must have at least one valid gene')
        if cell_keys.ndim!=1 or len(cell_keys)!=len(expression):
            raise ValueError('cell_keys must contain one stable identity per cell')
        safe_expression=expression.masked_fill(~gene_valid,0.0)
        gene_tokens=self.tokenizer(gene_ids,safe_expression)
        cell=self.cell_token.expand(len(expression),-1,-1)
        tokens=torch.cat((cell,gene_tokens),dim=1)
        valid=torch.cat((
            torch.ones(len(expression),1,dtype=torch.bool,device=expression.device),
            gene_valid,
        ),dim=1)
        token_ids=torch.cat((
            torch.full((len(expression),1),-1,dtype=torch.int64,device=expression.device),
            gene_ids.to(torch.int64),
        ),dim=1)
        minima=[]
        for layer_index,block in enumerate(self.blocks):
            tokens,minimum=block(
                tokens,valid,token_ids,cell_keys,
                training_seed=training_seed,
                update_index=update_index,
                view_index=view_index,
                layer_index=layer_index,
            )
            minima.append(minimum)
        tokens=self.final_norm(tokens)
        return EncoderOutput(tokens[:,1:],tokens[:,0],torch.stack(minima).amin())
