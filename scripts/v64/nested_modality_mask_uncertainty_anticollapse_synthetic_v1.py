#!/usr/bin/env python3
"""Synthetic-only qualification of modality-mask, uncertainty, and anti-collapse mechanics.

No real data are read. Thresholds below are fixture diagnostics only and carry no
production or biological authority.
"""
from __future__ import annotations
import json
import numpy as np

SEED=6701
N_DONORS=64
CELLS_PER_DONOR=40
K_SHARED=4
K_PRIVATE=3

def add_bias(x):
    x=np.asarray(x,float)
    return np.column_stack([np.ones(len(x)),x])

def fit(x,y):
    b,*_=np.linalg.lstsq(add_bias(x),np.asarray(y,float),rcond=None)
    return b

def pred(x,b):
    return add_bias(x)@b

def r2(y,p):
    y=np.asarray(y,float); p=np.asarray(p,float)
    den=np.square(y-y.mean(0,keepdims=True)).sum()
    return float(1-np.square(y-p).sum()/den)

def anti_collapse(z):
    z=np.asarray(z,float)
    sd=z.std(0)
    cov=np.cov(z,rowvar=False)
    ev=np.clip(np.linalg.eigvalsh(cov),0,None)
    if ev.sum()<=0:
        erank=0.0
    else:
        q=ev/ev.sum()
        q=q[q>0]
        erank=float(np.exp(-(q*np.log(q)).sum()))
    return {
        "min_axis_std":float(sd.min()),
        "effective_rank":erank,
        "passes":bool(sd.min()>0.10 and erank>2.5),
    }

def uncertainty_gate(measured,missing):
    measured=float(measured); missing=float(missing)
    return bool(np.isfinite(measured) and np.isfinite(missing)
                and measured>0 and missing>measured*3.0)

def build_fixture():
    rng=np.random.default_rng(SEED)
    n=N_DONORS*CELLS_PER_DONOR
    donor=np.repeat(np.arange(N_DONORS),CELLS_PER_DONOR)
    donor_shared=rng.normal(scale=.35,size=(N_DONORS,K_SHARED))
    zs=rng.normal(size=(n,K_SHARED))+donor_shared[donor]
    zp=rng.normal(size=(n,K_PRIVATE))
    ar=rng.normal(size=(K_SHARED,14))
    aa_s=rng.normal(size=(K_SHARED,11))
    aa_p=rng.normal(size=(K_PRIVATE,11))
    xr=zs@ar+.35*rng.normal(size=(n,14))
    xa=.45*zs@aa_s+zp@aa_p+.20*rng.normal(size=(n,11))

    # Acquisition availability is driven by an independent technical variable,
    # not biology. It is an observation condition, not a biological target.
    acquisition=rng.normal(size=n)
    measured=(acquisition+.25*rng.normal(size=n)>-0.15)

    train_donor=donor<48
    val_donor=donor>=48
    return dict(donor=donor,zs=zs,zp=zp,xr=xr,xa=xa,measured=measured,
                train=train_donor,val=val_donor)

def run_smoke():
    x=build_fixture()
    tr=x["train"]; va=x["val"]; m=x["measured"]
    # Universal shared path: lawful RNA only.
    br=fit(x["xr"][tr],x["zs"][tr])
    pr=pred(x["xr"][va],br)

    # Multimodal interface: ATAC is zero-filled only at the numeric transport
    # layer and accompanied by a mask. Zero is never interpreted as measured
    # private state. The mask is allowed to describe observation availability.
    xa_gated=x["xa"]*m[:,None]
    xm=np.column_stack([x["xr"],xa_gated,m.astype(float)])
    bm=fit(xm[tr],x["zs"][tr])
    pm=pred(xm[va],bm)

    # Private state exists only where ATAC is measured.
    trm=tr&m; vam=va&m
    bp=fit(np.column_stack([x["xr"][trm],x["xa"][trm]]),x["zp"][trm])
    pp=pred(np.column_stack([x["xr"][vam],x["xa"][vam]]),bp)
    private_store=np.full((va.sum(),K_PRIVATE),np.nan)
    val_measured=m[va]
    private_store[val_measured]=pp

    # Missing-modality uncertainty: measured residual variance versus lawful
    # RNA-only uncertainty for private state. RNA cannot identify the planted
    # private factor, so missing evidence must widen uncertainty.
    train_private_pred=pred(np.column_stack([x["xr"][trm],x["xa"][trm]]),bp)
    measured_u=float(np.mean(np.square(x["zp"][trm]-train_private_pred)))
    brp=fit(x["xr"][tr],x["zp"][tr])
    missing_pred=pred(x["xr"][tr],brp)
    missing_u=float(np.mean(np.square(x["zp"][tr]-missing_pred)))

    # Mask-only shortcut diagnostic on donor-held-out rows.
    bmask=fit(m[tr,None].astype(float),x["zs"][tr])
    mask_only=pred(m[va,None].astype(float),bmask)

    ac_shared=anti_collapse(pm)
    ac_rna=anti_collapse(pr)
    ac_constant=anti_collapse(np.zeros_like(pm))

    metrics={
        "rna_shared_r2":r2(x["zs"][va],pr),
        "multimodal_shared_r2":r2(x["zs"][va],pm),
        "multimodal_private_r2_measured":r2(x["zp"][vam],pp),
        "mask_only_shared_r2":r2(x["zs"][va],mask_only),
        "measured_private_uncertainty_mse":measured_u,
        "missing_private_uncertainty_mse":missing_u,
        "uncertainty_ratio_missing_over_measured":missing_u/measured_u,
    }
    gates={
        "shared_rna_noncollapsed":ac_rna["passes"],
        "shared_multimodal_noncollapsed":ac_shared["passes"],
        "constant_representation_is_rejected":not ac_constant["passes"],
        "mask_alone_does_not_explain_shared_biology":metrics["mask_only_shared_r2"]<0.03,
        "rna_shared_is_predictive":metrics["rna_shared_r2"]>0.70,
        "multimodal_shared_is_predictive":metrics["multimodal_shared_r2"]>0.75,
        "measured_private_is_identifiable":metrics["multimodal_private_r2_measured"]>0.90,
        "missing_private_is_not_zero_filled":bool(np.isnan(private_store[~val_measured]).all()),
        "measured_private_is_finite":bool(np.isfinite(private_store[val_measured]).all()),
        "missing_private_uncertainty_is_higher":uncertainty_gate(measured_u,missing_u),
    }
    return {
        "schema":"V67_NESTED_MODALITY_MASK_UNCERTAINTY_ANTICOLLAPSE_SYNTHETIC_V1",
        "status":"SYNTHETIC_SOFTWARE_SEMANTICS_ONLY",
        "fixture":{"donors":N_DONORS,"cells_per_donor":CELLS_PER_DONOR,
                   "train_donors":48,"validation_donors":16,"seed":SEED},
        "metrics":metrics,
        "anti_collapse":{"rna":ac_rna,"multimodal":ac_shared,"constant_negative":ac_constant},
        "gates":gates,
        "pass":bool(all(gates.values())),
        "interpretation":{
            "qualified":"synthetic modality-mask, missing-private uncertainty, and anti-collapse mechanics",
            "not_qualified":"real biology, real uncertainty calibration, production thresholds, model width, shared rank, or training authority"
        },
        "governance":{"real_data_used":False,"training":"OFF","multimodal_training":"OFF",
                      "stage4":"NOT_AUTHORIZED","Morabito":"PROTECTED","TD60":"BLOCKED"}
    }

def main():
    out=run_smoke()
    print(json.dumps(out,indent=2,sort_keys=True))
    return 0 if out["pass"] else 1

if __name__=="__main__":
    raise SystemExit(main())
