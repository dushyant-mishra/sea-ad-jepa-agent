#!/usr/bin/env python3
"""Deterministic fixed-target HC3-studentized Freedman-Lane inference for JEPA T0."""
from __future__ import annotations
import numpy as np

class NotEstimableError(ValueError):
    """Valid numeric inputs whose requested coefficient is not estimable."""



def _check_matrix(name: str, x: np.ndarray, n: int | None = None) -> np.ndarray:
    a=np.asarray(x,dtype=np.float64)
    if a.ndim!=2: raise ValueError(f"{name} must be 2-D")
    if n is not None and len(a)!=n: raise ValueError(f"{name} row mismatch")
    if not np.isfinite(a).all(): raise ValueError(f"{name} contains nonfinite values")
    return a


def _rank(a: np.ndarray) -> int:
    s=np.linalg.svd(a,compute_uv=False)
    tol=max(a.shape)*np.finfo(np.float64).eps*(s[0] if len(s) else 0.0)
    return int(np.sum(s>tol))


def ols_hc3_last(y: np.ndarray, x: np.ndarray) -> tuple[float,float,float]:
    """Return (beta_last, hc3_se_last, t_last), failing closed on degeneracy."""
    y=np.asarray(y,dtype=np.float64)
    x=_check_matrix("x",x,len(y))
    if y.ndim!=1 or not np.isfinite(y).all(): raise ValueError("y must be finite 1-D")
    n,p=x.shape
    if n<=p: raise NotEstimableError("no residual degrees of freedom")
    if _rank(x)!=p: raise NotEstimableError("rank-deficient full design")
    xtx_inv=np.linalg.inv(x.T@x)
    beta=xtx_inv@(x.T@y)
    resid=y-x@beta
    # diag H without constructing full H
    h=np.einsum('ij,jk,ik->i',x,xtx_inv,x)
    if np.any(h>=1.0-1e-12): raise NotEstimableError("HC3 leverage degeneracy")
    u=resid/(1.0-h)
    meat=x.T@((u*u)[:,None]*x)
    cov=xtx_inv@meat@xtx_inv
    var=float(cov[-1,-1])
    if not np.isfinite(var) or var<=0: raise NotEstimableError("nonpositive/nonfinite HC3 variance")
    se=float(np.sqrt(var)); b=float(beta[-1]); t=b/se
    if not np.isfinite(t): raise ValueError("nonfinite t statistic")
    return b,se,float(t)


def studentized_freedman_lane(
    y: np.ndarray,
    x_reduced: np.ndarray,
    predictor: np.ndarray,
    permutations: np.ndarray,
) -> dict:
    """Fixed-predictor Freedman-Lane test.

    permutations: integer array [B,n], each row a permutation of 0..n-1.
    Full design = [x_reduced, predictor]. The reduced-model residuals are permuted;
    predictors and reduced fitted values remain fixed.
    """
    y=np.asarray(y,dtype=np.float64)
    if y.ndim!=1 or not np.isfinite(y).all(): raise ValueError("y must be finite 1-D")
    n=len(y)
    xr=_check_matrix("x_reduced",x_reduced,n)
    pred=np.asarray(predictor,dtype=np.float64)
    if pred.ndim!=1 or len(pred)!=n or not np.isfinite(pred).all(): raise ValueError("predictor must be finite 1-D")

    # Structural input integrity must outrank scientific estimability.  Validate
    # the complete permutation object before rank, leverage, or HC3 calculations
    # so malformed input can never be absorbed into a NOT_ESTIMABLE verdict.
    P=np.asarray(permutations)
    if P.ndim!=2 or P.shape[1]!=n or P.shape[0]<1 or P.dtype.kind not in 'iu':
        raise ValueError("permutations must be integer [B,n]")
    target=np.arange(n)
    if not np.all(np.sort(P,axis=1)==target[None,:]):
        raise ValueError("invalid permutation row")

    if _rank(xr)!=xr.shape[1]: raise NotEstimableError("rank-deficient reduced design")
    if n<=xr.shape[1]: raise NotEstimableError("no reduced-model residual degrees of freedom")
    xf=np.column_stack([xr,pred])
    if _rank(xf)!=xf.shape[1]: raise NotEstimableError("predictor aliased with reduced design")

    # Reduced fit defines the FL exchangeable residual object.
    coef0=np.linalg.lstsq(xr,y,rcond=None)[0]
    fitted=xr@coef0
    resid=y-fitted
    if not np.isfinite(resid).all(): raise ValueError("nonfinite reduced residuals")

    # Full design is fixed across all Freedman-Lane responses. Validate and
    # factor it once; recomputing SVD/inverse/leverage 9,999 times is redundant.
    nfull,pfull=xf.shape
    if nfull<=pfull: raise NotEstimableError("no residual degrees of freedom")
    if _rank(xf)!=pfull: raise NotEstimableError("rank-deficient full design")
    xtx_inv=np.linalg.inv(xf.T@xf)
    h=np.einsum('ij,jk,ik->i',xf,xtx_inv,xf)
    if np.any(h>=1.0-1e-12): raise NotEstimableError("HC3 leverage degeneracy")

    def fixed_hc3_last(yv):
        beta_v=xtx_inv@(xf.T@yv)
        resid_v=yv-xf@beta_v
        u=resid_v/(1.0-h)
        meat=xf.T@((u*u)[:,None]*xf)
        cov=xtx_inv@meat@xtx_inv
        var=float(cov[-1,-1])
        if not np.isfinite(var) or var<=0: raise NotEstimableError("nonpositive/nonfinite HC3 variance")
        se_v=float(np.sqrt(var)); b_v=float(beta_v[-1]); t_v=b_v/se_v
        if not np.isfinite(t_v): raise ValueError("nonfinite t statistic")
        return b_v,se_v,float(t_v)

    beta,se,tobs=fixed_hc3_last(y)
    null=np.empty(P.shape[0],dtype=np.float64)
    for i,p in enumerate(P):
        ystar=fitted+resid[p]
        null[i]=fixed_hc3_last(ystar)[2]
    upper=(1+int(np.sum(null>=tobs)))/(len(null)+1)
    lower=(1+int(np.sum(null<=tobs)))/(len(null)+1)
    return {
        "beta":beta,"hc3_se":se,"t_observed":tobs,
        "p_upper":float(upper),"p_lower":float(lower),
        "null_t":null,
        "n":n,"p_reduced":int(xr.shape[1]),"p_full":int(xf.shape[1]),
        "residual_df":int(n-xf.shape[1]),"permutations":int(len(null)),
    }
