from __future__ import annotations
import numpy as np
from t0_coherence_exact_v1 import exact_common_direction_test

MIN_DECISION_DONORS=10
MIN_TAIL_CELLS=5
MIN_REST_CELLS=20
COHERENCE_ALPHA=.05


def _exact_count(name,x):
    if isinstance(x,(bool,np.bool_)):
        raise ValueError(f'{name} must be an integer count')
    if isinstance(x,(int,np.integer)):
        v=int(x)
    else:
        raise ValueError(f'{name} must be an integer count')
    if v<0: raise ValueError(f'{name} must be nonnegative')
    return v


def adjudicate_tail_support_coherence(vectors, tail_counts, rest_counts) -> dict:
    V=np.asarray(vectors,dtype=np.float64)
    if V.ndim!=2 or V.shape[0]==0 or V.shape[1]<2:
        raise ValueError('vectors must be donor x feature')
    tc=list(tail_counts); rc=list(rest_counts)
    if len(tc)!=len(V) or len(rc)!=len(V): raise ValueError('count/vector length mismatch')
    decision=[]
    for i in range(len(V)):
        t=_exact_count('tail_count',tc[i]); r=_exact_count('rest_count',rc[i])
        vec=V[i]
        ok=(t>=MIN_TAIL_CELLS and r>=MIN_REST_CELLS and np.isfinite(vec).all() and np.linalg.norm(vec)>0)
        decision.append(ok)
    decision=np.asarray(decision,dtype=bool)
    n=int(decision.sum())
    if n<MIN_DECISION_DONORS:
        return {'support_ok':False,'coherence_ok':False,'decision_donors':n,'p_upper_exact':None,'coherence':None}
    coh=exact_common_direction_test(V[decision])
    return {
        'support_ok':True,
        'coherence_ok':bool(coh['p_upper_exact']<=COHERENCE_ALPHA),
        'decision_donors':n,
        'p_upper_exact':float(coh['p_upper_exact']),
        'coherence':coh,
    }
