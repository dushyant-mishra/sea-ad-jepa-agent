"""Uniform finite singleton target-query sampling from an already-hidden V5 target set.

The full hidden target mask is scientific evidence geometry. Query budget is a
separate Monte Carlo/compute quantity. Unqueried targets remain hidden.
"""
from __future__ import annotations
import hashlib
from numbers import Integral
import torch
_DOMAIN=b'SEA_AD_JEPA_V5_SINGLETON_TARGET_QUERY_V2\0'
_U64=(1<<64)-1

def _u64(x:object,name:str)->int:
    if isinstance(x,bool) or not isinstance(x,Integral): raise ValueError(f'{name} must be exact integer')
    y=int(x)
    if y<0 or y>_U64: raise ValueError(f'{name} outside uint64')
    return y

def _sample_ranks(population:int,count:int,material:bytes)->tuple[int,...]:
    if not (1<=count<=population): raise ValueError('sample count outside population')
    seed=hashlib.sha256(_DOMAIN+material).digest(); selected:set[int]=set(); counter=0
    for j in range(population-count,population):
        while True:
            x=int.from_bytes(hashlib.sha256(seed+counter.to_bytes(16,'little')).digest(),'little'); counter+=1; mod=1<<256; limit=mod-(mod%(j+1))
            if x<limit: t=x%(j+1); break
        selected.add(j if t in selected else t)
    if len(selected)!=count: raise RuntimeError('query sampler uniqueness failure')
    return tuple(sorted(selected))

def sample_singleton_target_queries(
    hidden_target_mask:torch.Tensor,
    *,query_budget:int,authority_seed:int,presentation_indices:torch.Tensor,stable_cell_keys:torch.Tensor,draw_index:int,family_id:str,
)->torch.Tensor:
    if hidden_target_mask.dtype!=torch.bool or hidden_target_mask.ndim!=2: raise ValueError('hidden_target_mask must be boolean [cells,genes]')
    if stable_cell_keys.dtype!=torch.int64 or stable_cell_keys.ndim!=1 or len(stable_cell_keys)!=len(hidden_target_mask): raise ValueError('stable_cell_keys must be int64 [cells]')
    if presentation_indices.dtype!=torch.int64 or presentation_indices.ndim!=1 or len(presentation_indices)!=len(hidden_target_mask): raise ValueError('presentation_indices must be int64 [cells]')
    if presentation_indices.device!=stable_cell_keys.device: raise ValueError('presentation_indices and stable_cell_keys must share a device')
    if bool((presentation_indices<0).any()): raise ValueError('presentation_indices must be nonnegative')
    budget=_u64(query_budget,'query_budget'); seed=_u64(authority_seed,'authority_seed'); draw=_u64(draw_index,'draw_index')
    if budget<1: raise ValueError('query_budget must be positive')
    if not isinstance(family_id,str) or not family_id: raise ValueError('family_id must be nonempty string')
    counts=hidden_target_mask.sum(1)
    if bool((counts<1).any()) or not bool((counts==counts[0]).all()): raise ValueError('hidden target count must be equal and positive within reference batch')
    hidden_count=int(counts[0]); count=min(int(budget),hidden_count); cpu=hidden_target_mask.detach().cpu(); keys=stable_cell_keys.detach().cpu().tolist(); presentations=presentation_indices.detach().cpu().tolist(); out=torch.empty((len(cpu),count),dtype=torch.int64)
    f=family_id.encode()
    for r,(key,presentation_raw) in enumerate(zip(keys,presentations)):
        presentation=_u64(int(presentation_raw),'presentation_index')
        targets=torch.nonzero(cpu[r],as_tuple=False).flatten().tolist()
        if count==hidden_count:
            chosen=targets
        else:
            material=seed.to_bytes(8,'little')+presentation.to_bytes(8,'little')+_u64(int(key),'stable_cell_key').to_bytes(8,'little')+draw.to_bytes(8,'little')+len(f).to_bytes(4,'little')+f
            ranks=_sample_ranks(hidden_count,count,material); chosen=[targets[i] for i in ranks]
        out[r]=torch.tensor(chosen,dtype=torch.int64)
    return out.to(hidden_target_mask.device)
