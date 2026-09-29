#!/usr/bin/env python3
"""Donor-equal + source-equal, trace-normalized target-backbone stress test.

Discovery-only. Fits independent donor-disjoint bases and weights every donor
equally inside each source. Source covariances are normalized to unit trace
instead of per-feature z-scoring, avoiding transport explosions from features
with near-zero training-half variance.
"""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
import numpy as np, pandas as pd
from scipy import sparse
from scipy.linalg import subspace_angles
SOURCES=("HVS","NPH52","SEA_AD")
def stable_split(donors,salt="V62_DONOR_BALANCED"):
    ordered=sorted(map(str,donors),key=lambda x:hashlib.sha256(f"{salt}|{x}".encode()).hexdigest())
    return set(ordered[::2]),set(ordered[1::2])
def canonical_class(meta):
    c=meta.broad_class.astype(object).copy(); n=meta.source.eq("NPH52")
    c.loc[n & meta.native_class.eq("ExN")]="Neuronal: Glutamatergic"; c.loc[n & meta.native_class.eq("InN")]="Neuronal: GABAergic"
    c.loc[n & ~meta.native_class.isin(["ExN","InN"])]="Non-neuronal and Non-neural"
    allowed={"Neuronal: Glutamatergic","Neuronal: GABAergic","Non-neuronal and Non-neural"}; c.loc[~c.isin(allowed)]="Non-neuronal and Non-neural"
    return c.astype(str)
def residualize_group_means(y,g):
    out=np.asarray(y,float).copy(); g=np.asarray(g)
    for v in pd.unique(g):
        m=g==v
        if m.any():out[m]-=out[m].mean(0)
    return out
def eta_trace(y,g):
    y=np.asarray(y,float);g=np.asarray(g);mu=y.mean(0);den=((y-mu)**2).sum();num=0.
    for v in pd.unique(g):
        m=g==v
        if m.any():
            d=y[m].mean(0)-mu;num+=int(m.sum())*float(d@d)
    return float(num/den) if den else 0.
def donor_equal_weights(meta_rows):
    donors=meta_rows.donor_id.astype(str).to_numpy(); vals,counts=np.unique(donors,return_counts=True)
    inv={d:1.0/(len(vals)*n) for d,n in zip(vals,counts)}
    return np.array([inv[d] for d in donors],dtype=np.float64)
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--array-dir',required=True);ap.add_argument('--sample-freeze',required=True);ap.add_argument('--address-namespace',required=True);ap.add_argument('--measurement-support',required=True);ap.add_argument('--feature-width',type=int,default=400);ap.add_argument('--max-rank',type=int,default=8);ap.add_argument('--out',required=True)
    a=ap.parse_args();ad=Path(a.array_dir)
    data=np.load(ad/'data.npy',mmap_mode='r');indices=np.load(ad/'indices.npy',mmap_mode='r');indptr=np.load(ad/'indptr.npy',mmap_mode='r');shape=tuple(np.load(ad/'shape.npy').tolist());X=sparse.csr_matrix((data,indices,indptr),shape=shape,copy=False)
    meta=pd.read_csv(a.sample_freeze);meta['donor_id']=meta.donor_id.astype(str);meta['eval_class']=canonical_class(meta)
    ns=pd.read_csv(a.address_namespace,usecols=['molecular_address_index','biotype']);sup=pd.read_csv(a.measurement_support,usecols=['matrix_id','molecular_address_index','measured_address'])
    nm=sup[sup.measured_address].groupby('molecular_address_index').matrix_id.nunique();universe=np.sort(ns[ns.biotype.eq('protein_coding') & ns.molecular_address_index.isin(nm[nm.eq(42)].index)].molecular_address_index.to_numpy())
    qc=np.diff(X.indptr).astype(float);sets={s:stable_split(meta.loc[meta.source.eq(s),'donor_id'].unique()) for s in SOURCES}
    r1=np.array([i for i,r in meta.iterrows() if r.donor_id in sets[r.source][0]],int);r2=np.array([i for i,r in meta.iterrows() if r.donor_id in sets[r.source][1]],int)
    assert set(meta.iloc[r1].donor_id).isdisjoint(set(meta.iloc[r2].donor_id))
    def weighted_var(rows,cols):
        M=X[rows][:,cols].astype(np.float64);w=donor_equal_weights(meta.iloc[rows]);mu=np.asarray(M.T@w).ravel();m2=np.asarray(M.multiply(M).T@w).ravel();return np.maximum(m2-mu*mu,0.)
    features=universe[np.argsort(np.mean(np.vstack([weighted_var(r1[meta.iloc[r1].source.to_numpy()==s],universe) for s in SOURCES]),0))[::-1][:a.feature_width]]
    def fit(rows):
        C=np.zeros((len(features),len(features)));params={};traces={}
        for s in SOURCES:
            rr=rows[meta.iloc[rows].source.to_numpy()==s];D=X[rr][:,features].toarray().astype(np.float64);w=donor_equal_weights(meta.iloc[rr]);q=qc[rr]
            mu=w@D;qm=float(w@q);qc_c=q-qm;Dc=D-mu;beta=(w*qc_c)@Dc/(float(w@(qc_c*qc_c))+1e-12);R=Dc-qc_c[:,None]*beta
            Cs=(R.T*w)@R;tr=float(np.trace(Cs))
            if not np.isfinite(tr) or tr<=0:raise ValueError(f"nonpositive covariance trace for {s}")
            C+=Cs/tr/3.;traces[s]=tr;params[s]=(mu,qm,beta)
        vals,V=np.linalg.eigh(C);ix=np.argsort(vals)[::-1];return vals[ix],V[:,ix],params,traces
    def project(rows,V,p):
        out=np.empty((len(rows),V.shape[1]));pos={r:i for i,r in enumerate(rows)}
        for s in SOURCES:
            rr=rows[meta.iloc[rows].source.to_numpy()==s];D=X[rr][:,features].toarray().astype(np.float64);q=qc[rr];mu,qm,beta=p[s];S=(D-mu-(q-qm)[:,None]*beta)@V
            for j,r in enumerate(rr):out[pos[r]]=S[j]
        return out
    _,V1,p1,tr1=fit(r1);_,V2,_,tr2=fit(r2);S1=project(r1,V1,p1);S2=project(r2,V1,p1)
    def audit(S,rows,k):
        mm=meta.iloc[rows].reset_index(drop=True);Y=S[:,:k];bio=eta_trace(residualize_group_means(Y,mm.source),mm.source.astype(str)+'|'+mm.eval_class.astype(str));src=eta_trace(Y,mm.source)
        res=residualize_group_means(Y,mm.source.astype(str)+'|'+mm.eval_class.astype(str));don=eta_trace(res,mm.donor_id);sea=mm.source.eq('SEA_AD').to_numpy();op=eta_trace(residualize_group_means(Y[sea],mm.loc[sea,'eval_class']),mm.loc[sea,'operator_index'])
        return {'biology_within_source_eta2':bio,'source_eta2':src,'donor_after_source_class_eta2':don,'seaad_operator_after_class_eta2':op}
    out={'schema':'V62_DONOR_EQUAL_SOURCE_EQUAL_TRACE_NORMALIZED_TARGET_BACKBONE_V1','status':'DISCOVERY_STRESS_TEST_ONLY','feature_width':a.feature_width,'universe_n':len(universe),'split':{s:{'half1':len(sets[s][0]),'half2':len(sets[s][1])} for s in SOURCES},'source_covariance_trace_half1':tr1,'source_covariance_trace_half2':tr2,'ranks':{}}
    for k in range(1,a.max_rank+1):
        co=np.cos(subspace_angles(V1[:,:k],V2[:,:k]));out['ranks'][str(k)]={'mean_cos':float(co.mean()),'min_cos':float(co.min()),'fit_half1':audit(S1,r1,k),'heldout_half2_projected_on_half1_basis':audit(S2,r2,k)}
    out['producer_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest();Path(a.out).write_text(json.dumps(out,indent=2)+'\n')
if __name__=='__main__':main()
