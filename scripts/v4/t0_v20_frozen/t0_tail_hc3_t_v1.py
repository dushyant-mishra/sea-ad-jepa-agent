from __future__ import annotations
import numpy as np
from scipy.stats import t as student_t
from t0_studentized_fl_v1 import ols_hc3_last, NotEstimableError

TAIL_ALLOWED_N={17,18}


def tail_hc3_t(y,x_reduced,predictor):
    y=np.asarray(y,dtype=np.float64)
    xr=np.asarray(x_reduced,dtype=np.float64)
    pred=np.asarray(predictor,dtype=np.float64)
    if y.ndim!=1 or len(y) not in TAIL_ALLOWED_N or not np.isfinite(y).all():
        raise ValueError('tail HC3-t requires finite y with n=17 or 18')
    if xr.ndim!=2 or len(xr)!=len(y) or not np.isfinite(xr).all(): raise ValueError('invalid reduced design')
    if pred.ndim!=1 or len(pred)!=len(y) or not np.isfinite(pred).all(): raise ValueError('invalid predictor')
    xf=np.c_[xr,pred]
    b,se,t=ols_hc3_last(y,xf)
    df=int(len(y)-xf.shape[1])
    if df<=0: raise NotEstimableError('no residual degrees of freedom')
    pu=float(student_t.sf(t,df)); pl=float(student_t.cdf(t,df))
    if not (np.isfinite(pu) and np.isfinite(pl)): raise ValueError('nonfinite p-value')
    return {'beta':float(b),'hc3_se':float(se),'t_observed':float(t),'p_upper':pu,'p_lower':pl,'residual_df':df,'n':int(len(y)),'p_reduced':int(xr.shape[1]),'p_full':int(xf.shape[1]),'engine':'HC3_T_RESIDUAL_DF'}


def safe_tail_hc3_t(y,x_reduced,predictor):
    try:r=tail_hc3_t(y,x_reduced,predictor)
    except NotEstimableError as e:return {'estimable':False,'reason':str(e),'engine':'HC3_T_RESIDUAL_DF'}
    r=dict(r);r['estimable']=True;return r
