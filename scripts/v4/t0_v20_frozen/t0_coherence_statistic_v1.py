from __future__ import annotations
import numpy as np

def loo_coherence(vectors: np.ndarray) -> dict:
    V=np.asarray(vectors,dtype=np.float64)
    if V.ndim!=2 or V.shape[0]<3 or V.shape[1]<2 or not np.all(np.isfinite(V)):
        raise ValueError('need finite donor x feature matrix with >=3 donors')
    norms=np.linalg.norm(V,axis=1)
    if np.any(norms<=0): raise ValueError('zero donor coherence vector')
    U=V/norms[:,None]
    cos=[]
    for i in range(len(U)):
        c=U[np.arange(len(U))!=i].mean(axis=0)
        cn=np.linalg.norm(c)
        if cn<=0: raise ValueError('zero leave-one-donor consensus')
        c=c/cn
        cos.append(float(U[i]@c))
    a=np.asarray(cos)
    return {
        'loo_mean_cosine': float(a.mean()),
        'loo_median_cosine': float(np.median(a)),
        'loo_positive_fraction': float(np.mean(a>0)),
        'loo_cosines': a,
    }
