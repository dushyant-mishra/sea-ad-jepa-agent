#!/usr/bin/env python3
"""Synthetic-only smoke for the V65 nested RNA + multimodal student interface.

No real biological data are read. This qualifies architecture semantics only.
"""
from __future__ import annotations

import json
import numpy as np


def fit_linear(X,Y):
    X=np.asarray(X,float); Y=np.asarray(Y,float)
    X1=np.column_stack([np.ones(len(X)),X])
    B,*_=np.linalg.lstsq(X1,Y,rcond=None)
    return B


def predict_linear(X,B):
    X=np.asarray(X,float)
    return np.column_stack([np.ones(len(X)),X])@B


def r2(Y,P):
    Y=np.asarray(Y,float); P=np.asarray(P,float)
    den=np.square(Y-Y.mean(0,keepdims=True)).sum()
    return float(1-np.square(Y-P).sum()/den)


def pairwise_geometry_corr(X,Y):
    X=np.asarray(X,float); Y=np.asarray(Y,float)
    ix=np.triu_indices(len(X),1)
    dx=np.square(X[:,None,:]-X[None,:,:]).sum(2)[ix]
    dy=np.square(Y[:,None,:]-Y[None,:,:]).sum(2)[ix]
    if dx.std()==0 or dy.std()==0:
        return float("nan")
    return float(np.corrcoef(dx,dy)[0,1])


def synthetic(seed=6502,n_train=1600,n_test=800):
    rng=np.random.default_rng(seed)
    p_rna=12; p_atac=10; k_shared=4; k_private=3

    xr_tr=rng.normal(size=(n_train,p_rna))
    xr_te=rng.normal(size=(n_test,p_rna))
    xa_tr=rng.normal(size=(n_train,p_atac))
    xa_te=rng.normal(size=(n_test,p_atac))

    wr=rng.normal(size=(p_rna,k_shared))
    wa_shared=.25*rng.normal(size=(p_atac,k_shared))
    wa_private=rng.normal(size=(p_atac,k_private))

    zshared_tr=xr_tr@wr+xa_tr@wa_shared+.03*rng.normal(size=(n_train,k_shared))
    zshared_te=xr_te@wr+xa_te@wa_shared+.03*rng.normal(size=(n_test,k_shared))
    zprivate_tr=xa_tr@wa_private+.03*rng.normal(size=(n_train,k_private))
    zprivate_te=xa_te@wa_private+.03*rng.normal(size=(n_test,k_private))

    # RNA student may learn only from lawful RNA.
    br=fit_linear(xr_tr,zshared_tr)
    shared_rna=predict_linear(xr_te,br)

    # Multimodal student receives measured RNA+ATAC.
    xm_tr=np.column_stack([xr_tr,xa_tr])
    xm_te=np.column_stack([xr_te,xa_te])
    bm_shared=fit_linear(xm_tr,zshared_tr)
    bm_private=fit_linear(xm_tr,zprivate_tr)
    shared_multi=predict_linear(xm_te,bm_shared)
    private_multi=predict_linear(xm_te,bm_private)

    # Deliberately test forbidden RNA-only imitation of private state.
    br_private=fit_linear(xr_tr,zprivate_tr)
    private_from_rna=predict_linear(xr_te,br_private)

    # Shared geometry comparison must tolerate a basis rotation.
    q,_=np.linalg.qr(rng.normal(size=(k_shared,k_shared)))
    shared_multi_rot=shared_multi@q
    zshared_rot=zshared_te@q

    # Missing ATAC means private state is absent, not zero.
    atac_measured=np.zeros(n_test,dtype=bool)
    private_storage=np.full((n_test,k_private),np.nan)
    private_storage[atac_measured]=private_multi[atac_measured]

    return {
        "schema":"V65_NESTED_RNA_MULTIMODAL_STUDENT_SYNTHETIC_SMOKE_V1",
        "real_biology_used":False,
        "metrics":{
            "rna_shared_r2":r2(zshared_te,shared_rna),
            "multimodal_shared_r2":r2(zshared_te,shared_multi),
            "multimodal_private_r2":r2(zprivate_te,private_multi),
            "rna_private_r2":r2(zprivate_te,private_from_rna),
            "rotated_multimodal_shared_geometry_corr":pairwise_geometry_corr(zshared_rot,shared_multi_rot),
            "unrotated_multimodal_shared_geometry_corr":pairwise_geometry_corr(zshared_te,shared_multi),
        },
        "missing_private_is_nan":bool(np.isnan(private_storage).all()),
        "private_zero_filled":bool(np.array_equal(np.nan_to_num(private_storage),np.zeros_like(private_storage))),
        "training_authorized":False,
    }


def run_smoke():
    out=synthetic()
    m=out["metrics"]
    out["pass"]=bool(
        m["rna_shared_r2"]>0.70
        and m["multimodal_shared_r2"]>m["rna_shared_r2"]
        and m["multimodal_private_r2"]>0.95
        and m["rna_private_r2"]<0.05
        and abs(m["rotated_multimodal_shared_geometry_corr"]-m["unrotated_multimodal_shared_geometry_corr"])<1e-12
        and m["rotated_multimodal_shared_geometry_corr"]>0.95
        and out["missing_private_is_nan"]
    )
    return out


def main():
    out=run_smoke()
    print(json.dumps(out,indent=2,sort_keys=True))
    return 0 if out["pass"] else 1


if __name__=="__main__":
    raise SystemExit(main())
