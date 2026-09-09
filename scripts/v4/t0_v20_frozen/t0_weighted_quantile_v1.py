from __future__ import annotations
import numpy as np

def equal_donor_cell_quantile(values_by_donor: list[np.ndarray], q: float) -> float:
    if not (0.0 <= q <= 1.0): raise ValueError('q must be in [0,1]')
    if not values_by_donor: raise ValueError('no donors')
    vals=[]; w=[]; D=len(values_by_donor)
    for a in values_by_donor:
        a=np.asarray(a,dtype=np.float64)
        if a.ndim!=1 or len(a)==0 or not np.all(np.isfinite(a)):
            raise ValueError('each donor must provide finite 1d values')
        vals.append(a)
        w.append(np.full(len(a),1.0/(D*len(a)),dtype=np.float64))
    x=np.concatenate(vals); ww=np.concatenate(w)
    order=np.argsort(x,kind='mergesort'); x=x[order]; ww=ww[order]
    c=np.cumsum(ww)
    # inverse empirical CDF, no interpolation
    idx=int(np.searchsorted(c,q,side='left'))
    if idx>=len(x): idx=len(x)-1
    return float(x[idx])
