#!/usr/bin/env python3
"""Synthetic-only qualification of V65 recoverability permutation/geometry gates.

No real NIH-CARD values are read. This tests:
- deterministic donor seed derivation;
- within-donor pairing permutation;
- canonical-correlation geometry;
- relational pairwise-distance geometry;
- null calibration;
- failure when pairing is broken.
"""
from __future__ import annotations
import hashlib
import json
import numpy as np


def donor_seed(donor_id: str) -> int:
    h=hashlib.sha256(f"V65_RECOVERABILITY_PERMUTATION|{donor_id}".encode()).digest()
    return int.from_bytes(h[:8],"big",signed=False)


def _center(X):
    X=np.asarray(X,float)
    return X-X.mean(axis=0,keepdims=True)


def canonical_correlations(X,Y,tol=1e-10):
    X=_center(X); Y=_center(Y)
    qx,rx=np.linalg.qr(X,mode="reduced")
    qy,ry=np.linalg.qr(Y,mode="reduced")
    # Remove numerically null columns using R diagonal support.
    sx=np.abs(np.diag(rx))>tol
    sy=np.abs(np.diag(ry))>tol
    qx=qx[:,sx]; qy=qy[:,sy]
    if qx.shape[1]==0 or qy.shape[1]==0:
        return np.array([],dtype=float)
    s=np.linalg.svd(qx.T@qy,compute_uv=False)
    return np.clip(s,0.0,1.0)


def relational_geometry_corr(X,Y):
    X=np.asarray(X,float); Y=np.asarray(Y,float)
    n=X.shape[0]
    if Y.shape[0]!=n or n<3:
        raise ValueError("aligned matrices with >=3 rows required")
    ix=np.triu_indices(n,1)
    dx=np.square(X[:,None,:]-X[None,:,:]).sum(2)[ix]
    dy=np.square(Y[:,None,:]-Y[None,:,:]).sum(2)[ix]
    if dx.std()==0 or dy.std()==0:
        return np.nan
    return float(np.corrcoef(dx,dy)[0,1])


def r2_multi(Y,P,train_mean):
    Y=np.asarray(Y,float); P=np.asarray(P,float); train_mean=np.asarray(train_mean,float)
    den=np.square(Y-train_mean).sum()
    return float(1.0-np.square(Y-P).sum()/den)


def permutation_metrics(Ytrue,Ypred,train_mean,donor_id,n_perm=10_000):
    Ytrue=np.asarray(Ytrue,float); Ypred=np.asarray(Ypred,float)
    rng=np.random.default_rng(donor_seed(donor_id))
    obs_r2=r2_multi(Ytrue,Ypred,train_mean)
    cc=canonical_correlations(Ytrue,Ypred)
    obs_cc=float(np.median(cc)) if cc.size else float("nan")
    obs_rel=relational_geometry_corr(Ytrue,Ypred)
    null_r2=np.empty(n_perm)
    null_cc=np.empty(n_perm)
    null_rel=np.empty(n_perm)
    for i in range(n_perm):
        perm=rng.permutation(Ytrue.shape[0])
        yp=Ytrue[perm]
        null_r2[i]=r2_multi(yp,Ypred,train_mean)
        c=canonical_correlations(yp,Ypred)
        null_cc[i]=float(np.median(c)) if c.size else np.nan
        null_rel[i]=relational_geometry_corr(yp,Ypred)
    return dict(
        observed_r2=obs_r2,
        observed_median_canonical=obs_cc,
        observed_relational=obs_rel,
        r2_q99=float(np.quantile(null_r2,.99,method="higher")),
        canonical_q99=float(np.quantile(null_cc,.99,method="higher")),
        relational_q99=float(np.quantile(null_rel,.99,method="higher")),
        pairing_pass=bool(obs_r2>np.quantile(null_r2,.99,method="higher")),
        geometry_pass=bool(
            obs_cc>np.quantile(null_cc,.99,method="higher")
            and obs_rel>np.quantile(null_rel,.99,method="higher")
        ),
    )


def synthetic(seed=41,n=40,k=4):
    rng=np.random.default_rng(seed)
    Z=rng.normal(size=(n,k))
    # Recoverable prediction: small noise plus a mild invertible mixing.
    M=np.eye(k)+.05*rng.normal(size=(k,k))
    P=Z@M+.05*rng.normal(size=(n,k))
    return Z,P


def run_smoke():
    Y,P=synthetic()
    tm=np.zeros(Y.shape[1])
    good=permutation_metrics(Y,P,tm,"SYNTH_DONOR",n_perm=10_000)

    # Broken pairing: permute true rows once, then evaluate as if aligned.
    rng=np.random.default_rng(9)
    brokenY=Y[rng.permutation(Y.shape[0])]
    broken=permutation_metrics(brokenY,P,tm,"SYNTH_DONOR_BROKEN",n_perm=2_000)

    # Determinism check uses a smaller repeated null for speed.
    d1=permutation_metrics(Y,P,tm,"DETERMINISM",n_perm=500)
    d2=permutation_metrics(Y,P,tm,"DETERMINISM",n_perm=500)

    # Canonical correlation equals principal-angle cosines for the same centered
    # sample-space column spans. Verify numerically so we don't count it twice.
    Xc=_center(Y); Pc=_center(P)
    qx=np.linalg.qr(Xc,mode="reduced")[0]
    qp=np.linalg.qr(Pc,mode="reduced")[0]
    principal=np.linalg.svd(qx.T@qp,compute_uv=False)
    canonical=canonical_correlations(Y,P)

    out=dict(
        schema="V65_RECOVERABILITY_PERMUTATION_GEOMETRY_SYNTHETIC_SMOKE_V1",
        real_biology_used=False,
        good=good,
        broken=broken,
        deterministic=(d1==d2),
        canonical_equals_principal_angles=bool(np.allclose(canonical,principal,atol=1e-10)),
        pass_=bool(
            good["pairing_pass"]
            and good["geometry_pass"]
            and not broken["geometry_pass"]
            and d1==d2
            and np.allclose(canonical,principal,atol=1e-10)
        )
    )
    return out


def main():
    out=run_smoke()
    print(json.dumps(out,indent=2,sort_keys=True))
    return 0 if out["pass_"] else 1


if __name__=="__main__":
    raise SystemExit(main())
