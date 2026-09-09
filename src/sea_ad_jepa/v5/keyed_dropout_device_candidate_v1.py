"""Prospective V5 encoder candidate using vectorized V2 keyed dropout.

Parameter names and topology intentionally match the frozen V4-compatible
reference encoder.  The only intended mechanics change is scalar reference mask
generation -> vectorized device mask generation under the same Philox V2
address contract.  This file is not execution or training authority.
"""
from __future__ import annotations
import torch
from torch import nn
from sea_ad_jepa.v4.gene_tokenizer import GeneExpressionTokenizer
from sea_ad_jepa.v4.ipb_jepa import EncoderOutput, KernelLinearAttention
from .keyed_rng_device_v1 import keyed_feature_dropout_device


class KeyedTokenPreservingBlockV2DeviceCandidate(nn.Module):
    def __init__(self,width:int=160,heads:int=4,ffn_width:int=320,dropout:float=.10)->None:
        super().__init__()
        self.attention_norm=nn.LayerNorm(width)
        self.attention=KernelLinearAttention(width,heads)
        self.attention_dropout=nn.Dropout(dropout)
        self.ffn_norm=nn.LayerNorm(width)
        self.ffn=nn.Sequential(nn.Linear(width,ffn_width),nn.GELU(),nn.Dropout(dropout),nn.Linear(ffn_width,width),nn.Dropout(dropout))

    def forward(self,tokens:torch.Tensor,valid_mask:torch.Tensor,*,cell_keys:torch.Tensor,token_keys:torch.Tensor,run_seed:int,update_index:int,view_index:int,layer_index:int)->tuple[torch.Tensor,torch.Tensor]:
        attended,minimum=self.attention(self.attention_norm(tokens),valid_mask)
        attended=keyed_feature_dropout_device(
            attended,cell_keys=cell_keys,token_keys=token_keys,probability=float(self.attention_dropout.p),
            run_seed=run_seed,update_index=update_index,domain_index=0,view_index=view_index,
            layer_index=layer_index,site_index=0,training=self.training,
        )
        tokens=tokens+attended
        hidden=self.ffn[1](self.ffn[0](self.ffn_norm(tokens)))
        hidden=keyed_feature_dropout_device(
            hidden,cell_keys=cell_keys,token_keys=token_keys,probability=float(self.ffn[2].p),
            run_seed=run_seed,update_index=update_index,domain_index=0,view_index=view_index,
            layer_index=layer_index,site_index=1,training=self.training,
        )
        hidden=self.ffn[3](hidden)
        hidden=keyed_feature_dropout_device(
            hidden,cell_keys=cell_keys,token_keys=token_keys,probability=float(self.ffn[4].p),
            run_seed=run_seed,update_index=update_index,domain_index=0,view_index=view_index,
            layer_index=layer_index,site_index=2,training=self.training,
        )
        return tokens+hidden,minimum


class KeyedIPBEncoderV2DeviceCandidate(nn.Module):
    def __init__(self,*,width:int=160,heads:int=4,blocks:int=6,ffn_width:int=320,dropout:float=.10,vocabulary_size:int=41_238)->None:
        super().__init__()
        self.tokenizer=GeneExpressionTokenizer(vocabulary_size=vocabulary_size,width=width)
        self.cell_token=nn.Parameter(torch.empty(1,1,width)); nn.init.normal_(self.cell_token,mean=0.0,std=.02)
        self.blocks=nn.ModuleList([KeyedTokenPreservingBlockV2DeviceCandidate(width,heads,ffn_width,dropout) for _ in range(blocks)])
        self.final_norm=nn.LayerNorm(width)

    def forward(self,gene_ids:torch.Tensor,expression:torch.Tensor,measurement_mask:torch.Tensor,hidden_target_mask:torch.Tensor,view:str,*,cell_keys:torch.Tensor,run_seed:int,update_index:int,view_index:int)->EncoderOutput:
        if view=='student': gene_valid=measurement_mask & ~hidden_target_mask
        elif view=='target': gene_valid=measurement_mask
        else: raise ValueError('view must be student or target')
        if gene_ids.shape!=expression.shape or measurement_mask.shape!=expression.shape or hidden_target_mask.shape!=expression.shape:
            raise ValueError('gene_ids/expression/masks must share [cells,genes] shape')
        if gene_ids.dtype!=torch.int64 or measurement_mask.dtype!=torch.bool or hidden_target_mask.dtype!=torch.bool:
            raise ValueError('gene_ids must be int64 and masks boolean')
        if cell_keys.ndim!=1 or len(cell_keys)!=len(expression) or cell_keys.dtype!=torch.int64:
            raise ValueError('cell_keys must be int64 [cells]')
        if bool((~gene_valid.any(dim=1)).any()): raise ValueError('every cell must have at least one valid gene')
        safe_expression=expression.masked_fill(~gene_valid,0.0)
        gene_tokens=self.tokenizer(gene_ids,safe_expression)
        cell=self.cell_token.expand(len(expression),-1,-1)
        tokens=torch.cat((cell,gene_tokens),dim=1)
        valid=torch.cat((torch.ones(len(expression),1,dtype=torch.bool,device=expression.device),gene_valid),dim=1)
        token_keys=torch.cat((torch.full((len(expression),1),-1,dtype=torch.int64,device=expression.device),gene_ids),dim=1)
        minima=[]
        for layer_index,block in enumerate(self.blocks):
            tokens,minimum=block(tokens,valid,cell_keys=cell_keys,token_keys=token_keys,run_seed=run_seed,update_index=update_index,view_index=view_index,layer_index=layer_index)
            minima.append(minimum)
        tokens=self.final_norm(tokens)
        return EncoderOutput(tokens[:,1:],tokens[:,0],torch.stack(minima).amin())
