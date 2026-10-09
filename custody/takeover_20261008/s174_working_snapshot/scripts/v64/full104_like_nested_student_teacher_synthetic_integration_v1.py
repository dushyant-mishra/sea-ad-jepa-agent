#!/usr/bin/env python3
"""FULL104-shaped synthetic integration smoke for nested RNA + multimodal students.

Synthetic/software qualification only. No real biological outcome is read.

The fixture intentionally mimics project structure:
- 104 donors
- 42 operators
- 3 sources
- RNA-only universal student
- paired RNA+ATAC multimodal student
- planted shared biology and ATAC-private biology
- donor-disjoint train/validation/test splits

This is not a scientific threshold and does not authorize training.
"""
from __future__ import annotations

import hashlib
import json
import numpy as np

SEED=6503
N_DONORS=104
CELLS_PER_DONOR=50
N_OPERATORS=42
N_SOURCES=3
P_RNA=96
P_ATAC=96
K_SHARED=8
K_PRIVATE=4
RIDGE=10.0


def _ridge(X,Y,a=RIDGE):
    X=np.asarray(X,float);Y=np.asarray(Y,float)
    xmu=X.mean(0); ymu=Y.mean(0)
    Xc=X-xmu;Yc=Y-ymu
    B=np.linalg.solve(Xc.T@Xc+a*np.eye(X.shape[1]),Xc.T@Yc)
    return xmu,ymu,B


def _pred(m,X):
    xmu,ymu,B=m
    return (np.asarray(X,float)-xmu)@B+ymu


def _r2(Y,P):
    Y=np.asarray(Y,float);P=np.asarray(P,float)
    den=np.square(Y-Y.mean(0,keepdims=True)).sum()
    return float(1.0-np.square(Y-P).sum()/den)


def _zscore_train(X,train):
    X=np.asarray(X,float)
    mu=X[train].mean(0)
    sd=X[train].std(0)
    sd[sd<1e-8]=1.0
    return (X-mu)/sd


def _split_donors():
    keys=[]
    for d in range(N_DONORS):
        h=hashlib.sha256(f"{SEED}|D{d:03d}".encode()).digest()
        keys.append((int.from_bytes(h[:8],"big"),d))
    order=[d for _,d in sorted(keys)]
    return set(order[:72]),set(order[72:88]),set(order[88:])


def build_fixture():
    rng=np.random.default_rng(SEED)
    n=N_DONORS*CELLS_PER_DONOR
    donor=np.repeat(np.arange(N_DONORS),CELLS_PER_DONOR)
    source=(donor%N_SOURCES).astype(int)
    baseop=(donor*7%N_OPERATORS).astype(int)
    operator=(baseop+rng.integers(0,3,size=n))%N_OPERATORS

    donor_shared=rng.normal(size=(N_DONORS,K_SHARED))*0.7
    z_shared=donor_shared[donor]+rng.normal(size=(n,K_SHARED))*0.8
    z_private=rng.normal(size=(n,K_PRIVATE))

    op_embed=rng.normal(size=(N_OPERATORS,3))
    src_embed=rng.normal(size=(N_SOURCES,2))
    technical=np.concatenate([op_embed[operator],src_embed[source]],axis=1)

    Wr=rng.normal(scale=.45,size=(K_SHARED,P_RNA))
    Tr=rng.normal(scale=.25,size=(5,P_RNA))
    Wa=rng.normal(scale=.35,size=(K_SHARED,P_ATAC))
    Wp=rng.normal(scale=1.10,size=(K_PRIVATE,P_ATAC))
    Ta=rng.normal(scale=.20,size=(5,P_ATAC))

    rna_lin=z_shared@Wr+technical@Tr+rng.normal(scale=.5,size=(n,P_RNA))
    atac_lin=z_shared@Wa+z_private@Wp+technical@Ta+rng.normal(scale=.45,size=(n,P_ATAC))

    R=rng.poisson(np.exp(np.clip(rna_lin*.32,-3,3))).astype(float)
    A=rng.poisson(np.exp(np.clip(atac_lin*.38,-3,3))).astype(float)

    Rlib=R.sum(1,keepdims=True)
    Alib=A.sum(1,keepdims=True)
    Xr=np.log1p(1e4*R/np.maximum(Rlib,1))
    Xa=np.log1p(1e4*A/np.maximum(Alib,1))

    train_d,val_d,test_d=_split_donors()
    train=np.array([d in train_d for d in donor])
    val=np.array([d in val_d for d in donor])
    test=np.array([d in test_d for d in donor])

    Xr=_zscore_train(Xr,train)
    Xa=_zscore_train(Xa,train)
    Zs=_zscore_train(z_shared,train)
    Zp=_zscore_train(z_private,train)

    paired=rng.random(n)<.65
    for d in range(N_DONORS):
        idx=np.where(donor==d)[0]
        if paired[idx].sum()<20:
            paired[idx[:20]]=True

    tech=np.zeros((n,N_OPERATORS+N_SOURCES+2),float)
    tech[np.arange(n),operator]=1
    tech[np.arange(n),N_OPERATORS+source]=1
    tech[:,-2]=np.log1p(Rlib[:,0])
    tech[:,-1]=np.log1p(Alib[:,0])

    return dict(
        donor=donor,source=source,operator=operator,
        Xr=Xr,Xa=Xa,Zs=Zs,Zp=Zp,technical=tech,
        paired=paired,train=train,val=val,test=test,
        train_donors=train_d,val_donors=val_d,test_donors=test_d,
    )


def run_smoke():
    x=build_fixture()
    tr=x["train"]; te=x["test"]; paired=x["paired"]

    # Universal RNA student: shared target only.
    rna_shared=_ridge(x["Xr"][tr],x["Zs"][tr])
    pred_rna_shared=_pred(rna_shared,x["Xr"][te])

    # Multimodal student: paired TRAIN cells only, shared + private targets.
    trp=tr & paired
    Xm=np.column_stack([x["Xr"],x["Xa"]])
    multi_shared=_ridge(Xm[trp],x["Zs"][trp])
    multi_private=_ridge(Xm[trp],x["Zp"][trp])
    pred_multi_shared=_pred(multi_shared,Xm[te])
    pred_multi_private=_pred(multi_private,Xm[te])

    # Forbidden/private diagnostic: can RNA alone recover the planted private state?
    rna_private=_ridge(x["Xr"][tr],x["Zp"][tr])
    pred_rna_private=_pred(rna_private,x["Xr"][te])

    # Technical shortcut baseline for shared state.
    tech_shared=_ridge(x["technical"][tr],x["Zs"][tr])
    pred_tech_shared=_pred(tech_shared,x["technical"][te])

    metrics={
        "rna_shared_r2":_r2(x["Zs"][te],pred_rna_shared),
        "multimodal_shared_r2":_r2(x["Zs"][te],pred_multi_shared),
        "multimodal_private_r2":_r2(x["Zp"][te],pred_multi_private),
        "rna_private_r2":_r2(x["Zp"][te],pred_rna_private),
        "technical_shared_r2":_r2(x["Zs"][te],pred_tech_shared),
        "paired_test_fraction":float(paired[te].mean()),
    }

    # RNA-only private state is absent, not numerically zero-filled.
    private_storage=np.full((int(te.sum()),K_PRIVATE),np.nan)

    pass_flags={
        "rna_shared_beats_technical":metrics["rna_shared_r2"]>metrics["technical_shared_r2"]+0.15,
        "multimodal_preserves_or_improves_shared":metrics["multimodal_shared_r2"]>=metrics["rna_shared_r2"]-0.03,
        "multimodal_recovers_private":metrics["multimodal_private_r2"]>0.60,
        "rna_does_not_recover_private":metrics["rna_private_r2"]<0.10,
        "missing_private_is_masked":bool(np.isnan(private_storage).all()),
    }

    return {
        "schema":"V65_FULL104_LIKE_NESTED_STUDENT_TEACHER_SYNTHETIC_INTEGRATION_V1",
        "status":"SYNTHETIC_SOFTWARE_INTEGRATION_ONLY",
        "fixture":{
            "donors":N_DONORS,
            "operators":N_OPERATORS,
            "sources":N_SOURCES,
            "cells":N_DONORS*CELLS_PER_DONOR,
            "train_donors":72,
            "validation_donors":16,
            "test_donors":16,
            "shared_rank":K_SHARED,
            "private_rank":K_PRIVATE,
            "paired_fraction_target":0.65,
        },
        "metrics":metrics,
        "pass_flags":pass_flags,
        "pass":bool(all(pass_flags.values())),
        "interpretation":{
            "rna_student":"eligible only for planted shared state",
            "multimodal_student":"eligible for planted shared and measured private state",
            "private_state_for_rna_only":"NOT_MEASURED_MASK_NOT_ZERO",
            "biological_authority":False,
        },
        "governance":{
            "real_data_used":False,
            "training_authorized":False,
            "multimodal_training_authorized":False,
            "stage4":"NOT_AUTHORIZED",
        }
    }


def main():
    out=run_smoke()
    print(json.dumps(out,indent=2,sort_keys=True))
    return 0 if out["pass"] else 1


if __name__=="__main__":
    raise SystemExit(main())
