from __future__ import annotations
import hashlib
from numbers import Integral
from typing import Sequence


def _int(v: object,name: str,minimum: int=0)->int:
    if isinstance(v,bool) or not isinstance(v,Integral):
        raise ValueError(f'{name} must be an exact integer')
    out=int(v)
    if out<minimum:
        raise ValueError(f'{name} must be >= {minimum}')
    return out


def anchored_triplet_capacity(n:int)->int:
    n=_int(n,'n')
    return 0 if n<3 else n*((n-1)*(n-2)//2)


def _unrank_pair(m:int,r:int)->tuple[int,int]:
    lo,hi=0,m-2
    while lo<=hi:
        a=(lo+hi)//2
        before=a*(2*m-a-1)//2
        count=m-a-1
        if r < before:
            hi=a-1
        elif r >= before+count:
            lo=a+1
        else:
            return a,a+1+(r-before)
    raise RuntimeError('pair rank out of range')


def unrank_anchored_triplet(sorted_cell_ids: Sequence[int], rank:int)->tuple[int,int,int]:
    ids=tuple(int(x) for x in sorted_cell_ids)
    n=len(ids)
    cap=anchored_triplet_capacity(n)
    rank=_int(rank,'rank')
    if rank>=cap:
        raise ValueError('rank exceeds triplet capacity')
    per_anchor=(n-1)*(n-2)//2
    ai,pr=divmod(rank,per_anchor)
    a,b=_unrank_pair(n-1,pr)
    ji=a if a<ai else a+1
    ki=b if b<ai else b+1
    j,k=ids[ji],ids[ki]
    if j>k:
        j,k=k,j
    return ids[ai],j,k


def _uniform_rank(cap:int, *, seed:int, group_key:str, counter:int)->int:
    limit=(1<<64)-((1<<64)%cap)
    nonce=0
    while True:
        payload=f'V5_TRIPLET_V1|{seed}|{group_key}|{counter}|{nonce}'.encode('utf-8')
        x=int.from_bytes(hashlib.blake2b(payload,digest_size=8).digest(),'little')
        if x<limit:
            return x%cap
        nonce+=1


def sample_finite_anchored_triplets(
    cell_ids: Sequence[int],
    *,
    max_triplets:int,
    seed:int,
    group_key:str,
)->tuple[tuple[int,int,int],...]:
    """Deterministic finite canonical triplets without exhaustive enumeration.

    max_triplets has no default. Input order is irrelevant. Duplicate cell IDs
    fail closed. If complete capacity is <= budget, every triplet is returned.
    Otherwise Floyd's exact sample-without-replacement algorithm selects ranks.
    """
    budget=_int(max_triplets,'max_triplets',1)
    seed=_int(seed,'seed')
    if not isinstance(group_key,str) or not group_key:
        raise ValueError('group_key must be a nonempty frozen string')
    ids=tuple(sorted(_int(x,'cell_id') for x in cell_ids))
    if len(ids)!=len(set(ids)):
        raise ValueError('cell_ids must be unique')
    cap=anchored_triplet_capacity(len(ids))
    if cap==0:
        return ()
    take=min(cap,budget)
    if cap<=take:
        ranks=range(cap)
    else:
        chosen=set()
        for counter,j in enumerate(range(cap-take,cap)):
            t=_uniform_rank(j+1,seed=seed,group_key=group_key,counter=counter)
            chosen.add(j if t in chosen else t)
        if len(chosen)!=take:
            raise RuntimeError('Floyd sampler cardinality invariant failed')
        ranks=sorted(chosen)
    return tuple(unrank_anchored_triplet(ids,r) for r in ranks)
