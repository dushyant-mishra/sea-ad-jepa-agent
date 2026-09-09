"""Comparator-pair sampling conditional on already selected relational anchors."""
from __future__ import annotations
from dataclasses import dataclass
import hashlib
from numbers import Integral
from typing import Sequence
_DOMAIN=b'SEA_AD_JEPA_V5_COMPARATOR_PAIR_GIVEN_ANCHOR_V1\0'; _U64=(1<<64)-1

def _u64(x:object,name:str)->int:
    if isinstance(x,bool) or not isinstance(x,Integral): raise ValueError(f'{name} must be exact integer')
    y=int(x)
    if y<0 or y>_U64: raise ValueError(f'{name} outside uint64')
    return y

def _pair_prefix(a:int,m:int)->int:return a*(2*m-a-1)//2

def _unrank_pair(rank:int,m:int)->tuple[int,int]:
    total=m*(m-1)//2
    if not 0<=rank<total: raise ValueError('pair rank out of range')
    lo,hi=0,m-1
    while lo+1<hi:
        mid=(lo+hi)//2
        if _pair_prefix(mid,m)<=rank:lo=mid
        else:hi=mid
    a=lo
    while a+1<m and _pair_prefix(a+1,m)<=rank:a+=1
    return a,a+1+(rank-_pair_prefix(a,m))

def _randbelow(material:bytes,upper:int)->int:
    seed=hashlib.sha256(_DOMAIN+material).digest();counter=0;mod=1<<256;limit=mod-(mod%upper)
    while True:
        x=int.from_bytes(hashlib.sha256(seed+counter.to_bytes(16,'little')).digest(),'little');counter+=1
        if x<limit:return x%upper
@dataclass(frozen=True)
class AnchorComparatorSample: anchor_key:int; comparator_a_key:int; comparator_b_key:int; pair_rank:int; pair_capacity:int

def sample_comparator_pair_given_anchor(*,group_cell_keys:Sequence[int],anchor_key:int,authority_seed:int,update_index:int,group_key:str,draw_index:int=0)->AnchorComparatorSample:
    seed=_u64(authority_seed,'authority_seed');update=_u64(update_index,'update_index');draw=_u64(draw_index,'draw_index');anchor=_u64(anchor_key,'anchor_key')
    if not isinstance(group_key,str) or not group_key:raise ValueError('group_key must be nonempty string')
    cells=sorted(_u64(x,'group_cell_key') for x in group_cell_keys)
    if len(cells)<3:raise ValueError('group is not relationally estimable')
    if len(cells)!=len(set(cells)):raise ValueError('group_cell_keys must be unique')
    if anchor not in cells:raise ValueError('anchor not in group')
    comparators=[x for x in cells if x!=anchor];m=len(comparators);cap=m*(m-1)//2;g=group_key.encode();material=seed.to_bytes(8,'little')+update.to_bytes(8,'little')+draw.to_bytes(8,'little')+anchor.to_bytes(8,'little')+len(g).to_bytes(4,'little')+g+len(cells).to_bytes(8,'little')+b''.join(x.to_bytes(8,'little') for x in cells);rank=_randbelow(material,cap);i,j=_unrank_pair(rank,m);a,b=comparators[i],comparators[j]
    return AnchorComparatorSample(anchor,a,b,rank,cap)
