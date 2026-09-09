#!/usr/bin/env python3
"""Exact donor-pseudobulk nuisance-partialled dual-ridge learner for JEPA T0."""
from __future__ import annotations
import numpy as np

MULTIPLIER_EXPONENTS = np.arange(-6.0, 2.0000001, 0.5, dtype=np.float64)


def _as_finite_1d(name, x, n=None):
    a=np.asarray(x,dtype=np.float64)
    if a.ndim!=1 or (n is not None and len(a)!=n) or not np.isfinite(a).all():
        raise ValueError(f"{name} must be finite 1-D")
    return a


def _as_finite_2d(name, x, n=None):
    a=np.asarray(x,dtype=np.float64)
    if a.ndim!=2 or (n is not None and len(a)!=n) or not np.isfinite(a).all():
        raise ValueError(f"{name} must be finite 2-D")
    return a


def _rank(a):
    s=np.linalg.svd(a,compute_uv=False)
    tol=max(a.shape)*np.finfo(np.float64).eps*(s[0] if len(s) else 0.0)
    return int(np.sum(s>tol))


def nuisance_design(age, sex, age_center=None):
    age=_as_finite_1d("age",age); sex=_as_finite_1d("sex",sex,len(age))
    uniq=np.unique(sex)
    if len(uniq)!=2 or not np.array_equal(uniq,np.array([0.0,1.0])):
        raise ValueError("sex must be complete binary 0/1 under V1 authority")
    center=float(np.mean(age) if age_center is None else age_center)
    ac=age-center
    z=np.c_[np.ones(len(age)),ac,ac*ac,sex]
    if _rank(z)!=z.shape[1]:
        raise ValueError("rank-deficient nuisance design")
    return z,center


def _fit_nuisance(train_z, train_y, train_x):
    if _rank(train_z)!=train_z.shape[1]:
        raise ValueError("rank-deficient nuisance design")
    by=np.linalg.lstsq(train_z,train_y,rcond=None)[0]
    bx=np.linalg.lstsq(train_z,train_x,rcond=None)[0]
    yr=train_y-train_z@by
    xr=train_x-train_z@bx
    ysd=float(np.std(yr,ddof=1))
    xsd=np.std(xr,axis=0,ddof=1)
    eps=np.finfo(np.float64).eps
    y_scale=max(1.0,float(np.max(np.abs(train_y))))
    y_tol=64.0*eps*y_scale
    if not np.isfinite(ysd) or ysd<=y_tol:
        raise ValueError("numerically zero/nonfinite residual response SD")
    x_scale=np.maximum(1.0,np.max(np.abs(train_x),axis=0))
    x_tol=64.0*eps*x_scale
    good=np.isfinite(xsd)&(xsd>x_tol)
    xs=np.zeros_like(xr)
    xs[:,good]=xr[:,good]/xsd[good]
    ys=yr/ysd
    return by,bx,ysd,xsd,good,xs,ys


def _dual_beta(xs, ys, multiplier_exp):
    n=xs.shape[0]
    gram=xs@xs.T
    s=float(np.trace(gram)/n)
    if not np.isfinite(s) or s<=0:
        raise ValueError("nonpositive ridge trace scale")
    lam=float((10.0**float(multiplier_exp))*s)
    a=np.linalg.solve(gram+lam*np.eye(n,dtype=np.float64),ys)
    beta=xs.T@a
    if not np.isfinite(beta).all():
        raise ValueError("nonfinite beta")
    return beta,lam,s


def fit_t0_target(pseudobulk, pathology, age, sex, donor_ids):
    """Fit V1 target with exact LOODO selection of a dimensionless ridge multiplier.

    Each LOODO fold recomputes the age center, nuisance design, nuisance fits, feature
    scales, response scale, trace scale, and lambda from training donors only. The
    selected object is the multiplier exponent; final lambda is recomputed from the
    complete discovery set.
    """
    X=_as_finite_2d("pseudobulk",pseudobulk)
    n,g=X.shape
    y=_as_finite_1d("pathology",pathology,n)
    age=_as_finite_1d("age",age,n); sex=_as_finite_1d("sex",sex,n)
    d=np.asarray(donor_ids).astype(str)
    if d.ndim!=1 or len(d)!=n or len(np.unique(d))!=n:
        raise ValueError("donor_ids must be unique 1-D")
    if n<=6:
        raise ValueError("insufficient donors")
    # Canonicalize donor order before all floating-point operations.
    order=np.asarray(sorted(range(n), key=lambda i: d[i].encode("utf-8")),dtype=int)
    X=X[order]; y=y[order]; age=age[order]; sex=sex[order]; d=d[order]
    # Full-set nuisance is checked now; folds are independently checked below.
    nuisance_design(age,sex)

    losses=np.zeros(len(MULTIPLIER_EXPONENTS),dtype=np.float64)
    for i in range(n):
        tr=np.arange(n)!=i
        age_tr=age[tr]; sex_tr=sex[tr]
        Ztr,center=nuisance_design(age_tr,sex_tr)
        # A one-row heldout set cannot itself have both sex categories, so build it
        # directly using the training center and the already-authorized 0/1 coding.
        ac_te=age[~tr]-center
        Zte=np.c_[np.ones(1),ac_te,ac_te*ac_te,sex[~tr]]
        by,bx,ysd,xsd,good,xs,ys=_fit_nuisance(Ztr,y[tr],X[tr])
        if not np.any(good):
            raise ValueError("no residual-variance genes")
        yte=(y[~tr]-Zte@by)/ysd
        xr_te=X[~tr]-Zte@bx
        xte=np.zeros_like(xr_te)
        xte[:,good]=xr_te[:,good]/xsd[good]
        for j,e in enumerate(MULTIPLIER_EXPONENTS):
            beta,_,_=_dual_beta(xs,ys,e)
            pred=float((xte@beta).item())
            losses[j]+=(float(yte[0])-pred)**2
    losses/=n
    if not np.isfinite(losses).all():
        raise ValueError("nonfinite CV loss")
    minloss=float(np.min(losses)); tol=1e-12*max(1.0,abs(minloss))
    choices=np.flatnonzero(losses<=minloss+tol)
    jstar=int(choices[-1]); estar=float(MULTIPLIER_EXPONENTS[jstar])

    Z,age_center=nuisance_design(age,sex)
    by,bx,ysd,xsd,good,xs,ys=_fit_nuisance(Z,y,X)
    beta,lam,s=_dual_beta(xs,ys,estar); beta[~good]=0.0
    mu=np.mean(X,axis=0)
    sigma=np.ones(g,dtype=np.float64); sigma[good]=xsd[good]
    return {
        "beta":beta,"mu":mu,"sigma":sigma,"decision_gene_mask":good,
        "selected_multiplier_exponent":estar,"selected_multiplier_index":jstar,
        "final_lambda":lam,"final_trace_scale":s,"cv_mse_by_multiplier":losses,
        "multiplier_exponents":MULTIPLIER_EXPONENTS.copy(),
        "response_residual_sd":ysd,"discovery_age_center":age_center,
        "canonical_donor_order":d.copy(),
    }


def score_expression(expression, fit):
    X=_as_finite_2d("expression",expression)
    beta=np.asarray(fit["beta"],dtype=np.float64); mu=np.asarray(fit["mu"],dtype=np.float64); sigma=np.asarray(fit["sigma"],dtype=np.float64)
    if X.shape[1]!=len(beta) or len(mu)!=len(beta) or len(sigma)!=len(beta): raise ValueError("feature mismatch")
    if np.any(sigma<=0) or not np.isfinite(sigma).all(): raise ValueError("invalid sigma")
    out=((X-mu)/sigma)@beta
    if not np.isfinite(out).all(): raise ValueError("nonfinite score")
    return out
