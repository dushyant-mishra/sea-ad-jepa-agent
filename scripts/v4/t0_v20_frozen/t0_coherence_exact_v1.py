#!/usr/bin/env python3
"""Exact donor sign-flip test for a common T0 holdout-panel direction."""
from __future__ import annotations
import numpy as np


def _stat_from_gram(G, signs):
    # Mean pairwise signed cosine; diagonal excluded.
    d=G.shape[0]
    total=float(signs @ G @ signs)
    return (total-d)/(d*(d-1))


def exact_common_direction_test(vectors: np.ndarray) -> dict:
    V=np.asarray(vectors,dtype=np.float64)
    if V.ndim!=2 or V.shape[0]<3 or V.shape[1]<2 or not np.isfinite(V).all():
        raise ValueError('need finite donor x feature vectors with >=3 donors')
    d=V.shape[0]
    if d>22: raise ValueError('exact sign-flip reference capped at 22 donors')
    norms=np.linalg.norm(V,axis=1)
    if np.any(norms<=0): raise ValueError('zero donor vector')
    U=V/norms[:,None]
    G=U@U.T
    obs=np.ones(d,dtype=np.float64)
    t_obs=_stat_from_gram(G,obs)
    # Global sign inversion leaves the statistic unchanged, so fix sign[0]=+1.
    total=1<<(d-1); ge=0
    null_min=np.inf; null_max=-np.inf
    tol=1e-15*max(1.0,abs(t_obs))
    for mask in range(total):
        s=np.ones(d,dtype=np.float64)
        for j in range(1,d):
            if mask & (1<<(j-1)): s[j]=-1.0
        t=_stat_from_gram(G,s)
        null_min=min(null_min,t); null_max=max(null_max,t)
        if t>=t_obs-tol: ge+=1
    p=ge/total
    return {'mean_pairwise_cosine':float(t_obs),'p_upper_exact':float(p),'sign_configurations':int(total),'null_min':float(null_min),'null_max':float(null_max),'donors':int(d)}
