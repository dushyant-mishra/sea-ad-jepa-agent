#!/usr/bin/env python3
"""Pathology-blind within-donor pseudo-tail QC veto for JEPA T0."""
from __future__ import annotations
import hashlib, struct
import numpy as np

QC_METRICS=2
QC_REPLICATES=999
QC_ALPHA=.05
NAMESPACE=b'T0-TAIL-QC-V1'


def _key(namespace: bytes, replicate: int, donor: str, stable_key: str) -> bytes:
    db=donor.encode(); kb=stable_key.encode()
    return hashlib.sha256(namespace+b'\x00'+struct.pack('>I',replicate)+struct.pack('>H',len(db))+db+struct.pack('>H',len(kb))+kb).digest()


def _as_bool_mask(mask,n):
    m=np.asarray(mask)
    if m.dtype!=np.bool_ or m.ndim!=1 or len(m)!=n:
        raise ValueError('tail mask must be boolean 1-D')
    return m


def _donor_delta(qc, mask):
    X=np.asarray(qc,dtype=np.float64)
    if X.ndim!=2 or X.shape[1]!=QC_METRICS or not np.isfinite(X).all():
        raise ValueError('QC must be finite n_cell x 2 frozen metrics')
    m=_as_bool_mask(mask,len(X))
    if m.sum()==0 or (~m).sum()==0: raise ValueError('need tail and rest cells')
    sd=np.std(X,axis=0,ddof=1)
    tol=64*np.finfo(np.float64).eps*np.maximum(1,np.max(np.abs(X),axis=0))
    good=np.isfinite(sd)&(sd>tol)
    if not np.all(good):
        raise ValueError('both frozen QC metrics must be decision-capable')
    return (X[m].mean(0)-X[~m].mean(0))/sd


def tail_qc_veto_test(qc_by_donor, tail_masks, stable_keys_by_donor, donor_ids) -> dict:
    D=len(donor_ids)
    if not (D==len(qc_by_donor)==len(tail_masks)==len(stable_keys_by_donor)) or D<3:
        raise ValueError('donor list mismatch')
    if len(set(map(str,donor_ids)))!=D: raise ValueError('donor ids must be unique')
    observed=[]
    for X,m,k,d in zip(qc_by_donor,tail_masks,stable_keys_by_donor,donor_ids):
        if len(k)!=len(X) or len(set(map(str,k)))!=len(k): raise ValueError('stable keys invalid')
        observed.append(_donor_delta(X,m))
    O=np.vstack(observed)
    t_obs=float(np.max(np.mean(np.abs(O),axis=0)))
    ge=0
    for r in range(QC_REPLICATES):
        vals=[]
        for X,m,k,d in zip(qc_by_donor,tail_masks,stable_keys_by_donor,donor_ids):
            m=_as_bool_mask(m,len(X)); nt=int(np.sum(m))
            order=sorted(range(len(k)),key=lambda i:(_key(NAMESPACE,r,str(d),str(k[i])),str(k[i]).encode()))
            pm=np.zeros(len(k),bool); pm[order[:nt]]=True
            vals.append(_donor_delta(X,pm))
        t=float(np.max(np.mean(np.abs(np.vstack(vals)),axis=0)))
        if t>=t_obs-1e-15*max(1.0,abs(t_obs)): ge+=1
    p=(1+ge)/(QC_REPLICATES+1)
    return {'max_mean_abs_standardized_qc_contrast':t_obs,'p_upper':float(p),'replicates':QC_REPLICATES,'donors':D,'decision_qc_metrics':QC_METRICS,'veto':bool(p<=QC_ALPHA)}
