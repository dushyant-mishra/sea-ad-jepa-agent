#!/usr/bin/env python3
"""Numerical synthetic smoke for V65 privileged-state recoverability.

Synthetic only. No NIH-CARD bytes, donor IDs, or biological outcomes are read.

The fixture deliberately makes the top RNA variance directions technical nuisance while
recoverable privileged signal lives in lower-variance RNA directions. This lets the
full-RNA ridge candidate beat the frozen 16-PC global-RNA baseline when real shared
information exists, while a technical-only target is rejected by the technical baseline.
"""
from __future__ import annotations
import json
import numpy as np

ALPHAS=(0.01,0.1,1.0,10.0,100.0)
RANKS=(2,4,8,16)


def ridge_fit(X,Y,alpha):
    X=np.asarray(X,float); Y=np.asarray(Y,float)
    xm=X.mean(0); ym=Y.mean(0)
    Xc=X-xm; Yc=Y-ym
    B=np.linalg.solve(Xc.T@Xc + alpha*np.eye(X.shape[1]), Xc.T@Yc)
    return xm,ym,B


def ridge_predict(model,X):
    xm,ym,B=model
    return (X-xm)@B+ym


def pca_fit(X,k=16):
    xm=X.mean(0)
    _,_,vt=np.linalg.svd(X-xm,full_matrices=False)
    return xm,vt[:k].T


def pca_transform(model,X):
    xm,V=model
    return (X-xm)@V


def r2_multi(Y,P,train_mean):
    num=np.square(Y-P).sum()
    den=np.square(Y-train_mean).sum()
    return 1.0-num/den


def nested_projectors(Ytrue_train,Ypred_train):
    """Build all nested target-space projectors from ONE TRAIN-only SVD."""
    A=Ytrue_train-Ytrue_train.mean(0)
    B=Ypred_train-Ypred_train.mean(0)
    C=A.T@B
    U,S,_=np.linalg.svd(C,full_matrices=False)
    projs={}
    shells={}
    prev=np.zeros((Ytrue_train.shape[1],Ytrue_train.shape[1]))
    blocked=False
    for k in RANKS:
        if blocked:
            projs[k]=None
            shells[k]=None
            continue
        if k < len(S):
            scale=max(1.0,abs(float(S[k-1])),abs(float(S[k])))
            tied=abs(float(S[k-1]-S[k])) <= 1e-8*scale
        else:
            tied=False
        if tied:
            projs[k]=None
            shells[k]=None
            blocked=True
            continue
        Uk=U[:,:k]
        P=Uk@Uk.T
        projs[k]=P
        shells[k]=P-prev
        prev=P
    return projs,shells,S

def make(seed=1,shared_rank=4,technical_target=False,n_donors=24,n_per=50):
    rng=np.random.default_rng(seed)
    Xs=[]; Ys=[]; Tech=[]; donor=[]
    # Fixed mappings shared across donors.
    A=rng.normal(size=(shared_rank,24))/np.sqrt(max(shared_rank,1))
    B=rng.normal(size=(shared_rank,16))/np.sqrt(max(shared_rank,1))
    for d in range(n_donors):
        n=n_per
        shared=rng.normal(size=(n,shared_rank))
        tech=rng.normal(size=(n,16))
        private=rng.normal(size=(n,16-shared_rank)) if shared_rank<16 else np.zeros((n,0))
        # 48 RNA features. First 16 have huge technical variance, so PCA16 chases nuisance.
        X=np.zeros((n,48))
        # Make the top 16 variance directions overwhelmingly technical, so PCA16
        # is a genuine shortcut baseline rather than an accidental carrier of the
        # lower-variance shared signal.
        X[:,:16]=20.0*tech + .30*rng.normal(size=(n,16))
        X[:,16:40]=0.40*(shared@A) + .12*rng.normal(size=(n,24))
        X[:,40:]=.25*rng.normal(size=(n,8))
        if technical_target:
            # Technical-only target is generated from the same two degrees of freedom
            # available to the frozen technical baseline.
            T=np.tile(tech[:,:2],(1,8)) + .10*rng.normal(size=(n,16))
        else:
            shared_part=shared@B
            if shared_rank<16:
                # private residual is independent of RNA.
                # Give it similar per-coordinate scale to shared signal.
                priv=np.zeros((n,16))
                priv[:,shared_rank:]=private[:,:16-shared_rank]
                T=shared_part + 0.75*priv + .08*rng.normal(size=(n,16))
            else:
                T=shared_part + .08*rng.normal(size=(n,16))
        depth1=tech[:,0] + .02*rng.normal(size=n)
        depth2=tech[:,1] + .02*rng.normal(size=n)
        Xs.append(X); Ys.append(T); Tech.append(np.c_[depth1,depth2])
        donor.extend([d]*n)
    return np.vstack(Xs),np.vstack(Ys),np.vstack(Tech),np.array(donor)


def select_alpha(X,Y,donor,train_donors=range(16)):
    scores={}
    td=list(train_donors)
    for a in ALPHAS:
        vals=[]
        for held in td:
            tr=np.isin(donor,[x for x in td if x!=held])
            va=donor==held
            m=ridge_fit(X[tr],Y[tr],a)
            vals.append(r2_multi(Y[va],ridge_predict(m,X[va]),Y[tr].mean(0)))
        scores[a]=float(np.mean(vals))
    return max(ALPHAS,key=lambda a:scores[a]),scores


def fit_all(X,Y,Tech,donor):
    tr=donor<16
    alpha,cv=select_alpha(X,Y,donor)
    candidate=ridge_fit(X[tr],Y[tr],alpha)
    technical=ridge_fit(Tech[tr],Y[tr],1.0)
    pca=pca_fit(X[tr],16)
    Xp=pca_transform(pca,X)
    global_rna=ridge_fit(Xp[tr],Y[tr],1.0)
    pred=ridge_predict(candidate,X)
    tpred=ridge_predict(technical,Tech)
    gpred=ridge_predict(global_rna,Xp)
    projs,shells,singular_values=nested_projectors(Y[tr],pred[tr])
    return dict(alpha=alpha,cv=cv,candidate=candidate,technical=technical,pca=pca,
                global_rna=global_rna,pred=pred,tpred=tpred,gpred=gpred,projs=projs,
                shells=shells,singular_values=singular_values,
                train_mean=Y[tr].mean(0))


def projected_donor_metrics(Y,donor,fit,projectors,which=(16,17,18,19)):
    out={}
    for k,P in projectors.items():
        if P is None:
            out[k]=None
            continue
        tm=fit["train_mean"]@P
        ds=[]
        for d in which:
            m=donor==d
            yt=Y[m]@P
            cp=fit["pred"][m]@P
            tp=fit["tpred"][m]@P
            gp=fit["gpred"][m]@P
            cr=r2_multi(yt,cp,tm)
            tr=r2_multi(yt,tp,tm)
            gr=r2_multi(yt,gp,tm)
            ds.append(dict(donor=d,candidate=cr,technical=tr,global_rna=gr,
                           delta=cr-max(tr,gr)))
        out[k]=ds
    return out


def metric_set_summary(ds):
    if ds is None:
        return dict(eligible=False,reason="projection_tie_or_prior_boundary_failure")
    delta=np.array([x["delta"] for x in ds])
    cand=np.array([x["candidate"] for x in ds])
    tech=np.array([x["technical"] for x in ds])
    eligible=bool(np.all(delta>0) and np.median(delta)>=.05 and np.all(cand>0)
                  and np.all(cand-tech>.01))
    return dict(eligible=eligible,median_delta=float(np.median(delta)),
                min_delta=float(delta.min()),min_candidate=float(cand.min()))


def summarize(aggregate_metrics,shell_metrics):
    s={}
    chosen=0
    for k in RANKS:
        agg=metric_set_summary(aggregate_metrics[k])
        shell=metric_set_summary(shell_metrics[k])
        eligible=bool(agg["eligible"] and shell["eligible"])
        s[k]=dict(eligible=eligible,aggregate=agg,shell=shell)
        if not eligible:
            break
        chosen=k
    # Keep later ranks visible diagnostically even after contiguous selection stops.
    for k in RANKS:
        if k in s:
            continue
        agg=metric_set_summary(aggregate_metrics[k])
        shell=metric_set_summary(shell_metrics[k])
        s[k]=dict(eligible=bool(agg["eligible"] and shell["eligible"]),
                  aggregate=agg,shell=shell)
    return s,chosen

def run_case(seed,shared_rank,technical_target=False):
    X,Y,T,d=make(seed=seed,shared_rank=shared_rank,technical_target=technical_target)
    fit=fit_all(X,Y,T,d)
    agg=projected_donor_metrics(Y,d,fit,fit["projs"],(16,17,18,19))
    shell=projected_donor_metrics(Y,d,fit,fit["shells"],(16,17,18,19))
    sm,chosen=summarize(agg,shell)
    return dict(alpha=fit["alpha"],validation=sm,chosen_rank=chosen,
                singular_values=[float(x) for x in fit["singular_values"]])


def main():
    full=run_case(11,16,False)
    partial=run_case(22,4,False)
    technical=run_case(33,4,True)
    out=dict(schema="V65_RECOVERABILITY_NUMERICAL_SYNTHETIC_SMOKE_V1",
             real_biology_used=False,full=full,partial=partial,technical=technical)
    # Fully shared target should reach rank 16.
    assert full["chosen_rank"]==16, full
    # Partial target should recover a nonzero subspace but not full rank.
    assert partial["chosen_rank"] in (2,4), partial
    assert partial["chosen_rank"]<16, partial
    # Technical-only target must not beat the technical shortcut baseline.
    assert technical["chosen_rank"]==0, technical
    print(json.dumps(out,indent=2,sort_keys=True))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
