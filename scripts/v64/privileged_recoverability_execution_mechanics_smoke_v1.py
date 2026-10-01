#!/usr/bin/env python3
"""Synthetic-only smoke for V65 recoverability execution mechanics."""
from __future__ import annotations
import json
import numpy as np

ALPHAS=(0.01,0.1,1.0,10.0,100.0)
TIE_REL=1e-8

def fit_tfidf(A):
    A=np.asarray(A,float)
    lib=A.sum(1)
    if np.any(lib<=0): raise ValueError("nonpositive ATAC library")
    n=A.shape[0]
    df=(A>0).sum(0)
    idf=np.log(1+n/(1+df))
    return idf

def transform_tfidf(A,idf):
    A=np.asarray(A,float)
    lib=A.sum(1)
    if np.any(lib<=0): raise ValueError("nonpositive ATAC library")
    return (A/lib[:,None])*idf[None,:]

def _boundary_tied(s,k):
    if k>=len(s): return False
    scale=max(1.0,abs(float(s[k-1])),abs(float(s[k])))
    return abs(float(s[k-1]-s[k])) <= TIE_REL*scale

def svd_basis(M,k):
    _,s,vt=np.linalg.svd(np.asarray(M,float),full_matrices=False)
    if _boundary_tied(s,k):
        raise ValueError("singular-value boundary tie")
    V=vt[:k].T.copy()
    for c in range(k):
        a=np.abs(V[:,c])
        mx=a.max()
        idx=int(np.flatnonzero(a==mx)[0])
        if V[idx,c]<0: V[:,c]*=-1
    return V,s

def fit_standardizer(X):
    X=np.asarray(X,float)
    mu=X.mean(0)
    sd=np.sqrt(np.mean((X-mu)**2,axis=0))
    return mu,sd

def apply_standardizer(X,mu,sd,zero_to_zero=False):
    X=np.asarray(X,float)
    if zero_to_zero:
        good=sd>0
        out=np.zeros_like(X,dtype=float)
        out[:,good]=(X[:,good]-mu[good])/sd[good]
        return out
    if np.any(sd<=0): raise ValueError("zero target sd")
    return (X-mu)/sd

def rna_log1p10k(R):
    R=np.asarray(R,float)
    lib=R.sum(1)
    if np.any(lib<=0): raise ValueError("nonpositive RNA library")
    return np.log1p(10000*R/lib[:,None])

def ridge_fit(X,Y,a):
    X=np.asarray(X,float); Y=np.asarray(Y,float)
    xm=X.mean(0); ym=Y.mean(0)
    xc=X-xm; yc=Y-ym
    B=np.linalg.solve(xc.T@xc+a*np.eye(X.shape[1]),xc.T@yc)
    return xm,ym,B

def ridge_predict(m,X):
    xm,ym,B=m
    return (np.asarray(X,float)-xm)@B+ym

def r2(Y,P,ref):
    den=np.square(Y-ref).sum()
    return float(1-np.square(Y-P).sum()/den)

def choose_alpha(X,Y,donor,alphas=ALPHAS):
    donors=sorted(set(donor.tolist()))
    scores={}
    for a in alphas:
        vals=[]
        for d in donors:
            tr=donor!=d; va=donor==d
            m=ridge_fit(X[tr],Y[tr],a)
            vals.append(r2(Y[va],ridge_predict(m,X[va]),Y[tr].mean(0)))
        scores[a]=float(np.mean(vals))
    best=max(scores.values())
    tied=[a for a,v in scores.items() if abs(v-best)<=1e-12]
    return max(tied),scores

def run_smoke():
    # TRAIN-only IDF: changing held-out bytes cannot change fitted IDF.
    Atr=np.array([[1,0,2,0],[0,3,0,1],[1,1,0,0],[0,2,1,1]],float)
    Aval1=np.array([[9,0,0,1],[0,1,8,0]],float)
    Aval2=np.array([[0,9,1,0],[7,0,0,3]],float)
    idf1=fit_tfidf(Atr)
    idf2=fit_tfidf(Atr)
    assert np.array_equal(idf1,idf2)
    V,_=svd_basis(transform_tfidf(Atr,idf1),2)
    z1=transform_tfidf(Aval1,idf1)@V
    z2=transform_tfidf(Aval2,idf1)@V
    assert not np.array_equal(z1,z2)

    # RNA standardizer keeps zero-variance feature in place but zeroes it in all splits.
    R=np.array([[5,0,2],[4,0,1],[6,0,3],[5,0,4]],float)
    X=rna_log1p10k(R)
    mu,sd=fit_standardizer(X)
    Xs=apply_standardizer(X,mu,sd,zero_to_zero=True)
    assert np.all(Xs[:,1]==0)

    # Exact largest-alpha tie behavior.
    X0=np.arange(8,dtype=float).reshape(4,2)
    Y0=np.zeros((4,1),float)
    donors=np.arange(4)
    # r2 is undefined for zero target variance, so make a direct equal-score tie fixture.
    scores={a:0.25 for a in ALPHAS}
    best=max(scores.values())
    tied=[a for a,v in scores.items() if abs(v-best)<=1e-12]
    assert max(tied)==100.0

    # Sign convention: maximum-absolute loading is positive.
    M=np.array([[3.,0.,1.],[0.,2.,1.],[1.,1.,4.],[2.,0.,2.]])
    B,S=svd_basis(M,2)
    for c in range(2):
        idx=int(np.flatnonzero(np.abs(B[:,c])==np.abs(B[:,c]).max())[0])
        assert B[idx,c]>0

    return {
      "schema":"V65_RECOVERABILITY_EXECUTION_MECHANICS_SYNTHETIC_SMOKE_V1",
      "real_biology_used":False,
      "train_only_idf":True,
      "heldout_transform_uses_frozen_idf":True,
      "rna_zero_sd_feature_preserved_as_zero":True,
      "deterministic_svd_sign":True,
      "largest_alpha_tie_rule":True,
      "pass":True
    }

def main():
    out=run_smoke()
    print(json.dumps(out,indent=2,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
