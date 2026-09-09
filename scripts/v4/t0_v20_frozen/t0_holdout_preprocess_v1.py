from __future__ import annotations
import numpy as np

def equal_donor_within_scale(values: np.ndarray, donors: np.ndarray) -> tuple[np.ndarray,np.ndarray]:
    X=np.asarray(values,dtype=np.float64); d=np.asarray(donors)
    if X.ndim!=2 or d.ndim!=1 or len(d)!=len(X) or len(X)==0 or not np.all(np.isfinite(X)):
        raise ValueError('invalid values/donors')
    uniq=np.unique(d)
    if len(uniq)<2: raise ValueError('need >=2 donors')
    vars=[]
    for u in uniq:
        Xi=X[d==u]
        if len(Xi)<2: raise ValueError('every scaling donor needs >=2 cells')
        vars.append(np.var(Xi,axis=0,ddof=1))
    v=np.mean(np.vstack(vars),axis=0)
    scale=np.sqrt(v)
    decision=np.isfinite(scale)&(scale>0)
    return scale,decision

def tail_rest_vector(values: np.ndarray, tail_mask: np.ndarray, scale: np.ndarray, decision_mask: np.ndarray) -> np.ndarray:
    X=np.asarray(values,dtype=np.float64); t=np.asarray(tail_mask,dtype=bool); s=np.asarray(scale,dtype=np.float64); m=np.asarray(decision_mask,dtype=bool)
    if X.ndim!=2 or len(t)!=len(X) or X.shape[1]!=len(s) or len(s)!=len(m) or not np.all(np.isfinite(X)):
        raise ValueError('shape/nonfinite error')
    if t.sum()==0 or (~t).sum()==0: raise ValueError('need tail and rest cells')
    if np.any(s[m]<=0) or not np.any(m): raise ValueError('no decision-capable holdout genes')
    out=np.zeros(X.shape[1],dtype=np.float64)
    out[m]=(X[t][:,m].mean(axis=0)-X[~t][:,m].mean(axis=0))/s[m]
    norm=np.linalg.norm(out[m])
    if not np.isfinite(norm) or norm<=0: raise ValueError('zero/nonfinite corroboration vector')
    out[m]/=norm
    return out
