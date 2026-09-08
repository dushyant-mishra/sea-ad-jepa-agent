"""Exposure-based schedule primitives for prospective V5.

No half-life or training horizon is chosen here.  These helpers prevent a
batch-size change from silently changing EMA time semantics.
"""
from __future__ import annotations
from numbers import Integral
import math


def _positive_int(value:object,name:str)->int:
    if isinstance(value,bool) or not isinstance(value,Integral) or int(value)<1:
        raise ValueError(f'{name} must be an explicit positive integer')
    return int(value)


def ema_momentum_for_presentations(*,half_life_presentations:int,presentations_this_update:int)->float:
    """Return m so cumulative EMA decay is 1/2 after the declared presentations."""
    half=_positive_int(half_life_presentations,'half_life_presentations')
    current=_positive_int(presentations_this_update,'presentations_this_update')
    return math.exp(math.log(0.5)*current/half)


def cumulative_ema_decay_for_presentations(*,half_life_presentations:int,update_presentations:list[int])->float:
    half=_positive_int(half_life_presentations,'half_life_presentations')
    if not update_presentations: raise ValueError('update_presentations cannot be empty')
    out=1.0
    for n in update_presentations:
        out*=ema_momentum_for_presentations(half_life_presentations=half,presentations_this_update=_positive_int(n,'update_presentations item'))
    return out
