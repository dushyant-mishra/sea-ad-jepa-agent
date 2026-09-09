"""Singleton target-query blocks over an independently frozen hidden evidence set.

The full hidden_target_mask is scientific evidence geometry. queried_target_ids
is a finite compute sample from that already-hidden set. Unqueried hidden genes
remain hidden; query budget therefore cannot silently change student evidence.
"""
from __future__ import annotations
import torch
from sea_ad_jepa.v4.ipb_jepa import TargetBlocks

def singleton_target_blocks(*,hidden_target_mask:torch.Tensor,queried_target_ids:torch.Tensor)->TargetBlocks:
    if hidden_target_mask.ndim!=2 or hidden_target_mask.dtype!=torch.bool: raise ValueError('hidden_target_mask must be boolean [cells,genes]')
    if queried_target_ids.ndim!=2 or queried_target_ids.dtype!=torch.int64: raise ValueError('queried_target_ids must be int64 [cells,queries]')
    cells,genes=hidden_target_mask.shape
    if queried_target_ids.shape[0]!=cells or queried_target_ids.shape[1]<1: raise ValueError('queried targets must contain >=1 query for every cell')
    if bool(((queried_target_ids<0)|(queried_target_ids>=genes)).any()): raise ValueError('queried target ID outside vocabulary')
    if any(len(torch.unique(row))!=len(row) for row in queried_target_ids): raise ValueError('queried targets must be unique within each cell')
    rows=torch.arange(cells,device=hidden_target_mask.device)[:,None]; ids=queried_target_ids.to(hidden_target_mask.device)
    if not bool(hidden_target_mask[rows,ids].all()): raise ValueError('every queried target must already belong to the full hidden target set')
    indices=ids[:,:,None]
    return TargetBlocks(hidden_mask=hidden_target_mask.clone(),indices=indices,member_mask=torch.ones_like(indices,dtype=torch.bool),fallback_counts=torch.zeros(cells,dtype=torch.int64,device=hidden_target_mask.device))
