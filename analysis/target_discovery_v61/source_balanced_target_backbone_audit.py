"""V61 discovery-only source-balanced target-backbone audit.

Requires the authenticated 50k discovery CSR NPZ plus sample freeze, address
namespace, and address-measurement support. This is not training authority.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import sparse
from scipy.linalg import subspace_angles

SOURCES=("HVS","NPH52","SEA_AD")

def eta_trace(Y,g):
    Y=np.asarray(Y,float); g=np.asarray(g); mu=Y.mean(0); den=((Y-mu)**2).sum()
    num=0.0
    for v in pd.unique(g):
        m=g==v
        if m.any():
            d=Y[m].mean(0)-mu; num += int(m.sum())*float(d@d)
    return float(num/den) if den else 0.0

def residualize_group_means(Y,g):
    out=np.asarray(Y,float).copy(); g=np.asarray(g)
    for v in pd.unique(g):
        m=g==v
        if m.any(): out[m]-=out[m].mean(0)
    return out

def canonical_class(meta):
    c=meta.broad_class.copy(); n=meta.source.eq("NPH52")
    c.loc[n & meta.native_class.eq("ExN")]="Neuronal: Glutamatergic"
    c.loc[n & meta.native_class.eq("InN")]="Neuronal: GABAergic"
    c.loc[n & ~meta.native_class.isin(["ExN","InN"]) ]="Non-neuronal and Non-neural"
    allowed={"Neuronal: Glutamatergic","Neuronal: GABAergic","Non-neuronal and Non-neural"}
    c.loc[~c.isin(allowed)]="Non-neuronal and Non-neural"
    return c

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--npz",required=True); ap.add_argument("--sample-freeze",required=True)
    ap.add_argument("--address-namespace",required=True); ap.add_argument("--measurement-support",required=True)
    ap.add_argument("--feature-width",type=int,default=400); ap.add_argument("--out",required=True)
    a=ap.parse_args()
    z=np.load(a.npz,allow_pickle=False)
    X=sparse.csr_matrix((z["data"],z["indices"],z["indptr"]),shape=tuple(z["shape"]))
    meta=pd.read_csv(a.sample_freeze); meta["eval_class"]=canonical_class(meta)
    ns=pd.read_csv(a.address_namespace,usecols=["molecular_address_index","biotype"])
    sup=pd.read_csv(a.measurement_support,usecols=["matrix_id","molecular_address_index","measured_address"])
    measured=sup[sup.measured_address].groupby("molecular_address_index").matrix_id.nunique()
    universe=np.sort(ns[(ns.biotype.eq("protein_coding")) & ns.molecular_address_index.isin(measured[measured.eq(42)].index)].molecular_address_index.to_numpy())
    qc=np.diff(X.indptr).astype(np.float64); qc=(qc-qc.mean())/(qc.std()+1e-12)
    A=np.where(meta["sample"].eq("A_NATURAL_MIXTURE").to_numpy())[0]; B=np.setdiff1d(np.arange(len(meta)),A)
    def var(rows,cols):
        M=X[rows][:,cols]; m=np.asarray(M.mean(0)).ravel(); m2=np.asarray(M.multiply(M).mean(0)).ravel(); return np.maximum(m2-m*m,0)
    score=np.mean(np.vstack([var(A[meta.iloc[A].source.to_numpy()==s],universe) for s in SOURCES]),0)
    features=universe[np.argsort(score)[::-1][:a.feature_width]]
    def fit(rows):
        cov=np.zeros((len(features),len(features))); params={}
        for s in SOURCES:
            rr=rows[meta.iloc[rows].source.to_numpy()==s]; D=X[rr][:,features].toarray().astype(np.float64); q=qc[rr]
            mu=D.mean(0); C=D-mu; beta=(q@C)/(q@q+1e-12); R=C-q[:,None]*beta; sd=R.std(0,ddof=1); sd[sd<1e-8]=1.0; R/=sd
            cov += (R.T@R)/(3*max(len(rr)-1,1)); params[s]=(mu,beta,sd)
        w,V=np.linalg.eigh(cov); ix=np.argsort(w)[::-1]; return w[ix],V[:,ix],params
    def project(rows,V,p):
        out=np.empty((len(rows),V.shape[1])); pos={r:i for i,r in enumerate(rows)}
        for s in SOURCES:
            rr=rows[meta.iloc[rows].source.to_numpy()==s]; D=X[rr][:,features].toarray().astype(np.float64); q=qc[rr]; mu,beta,sd=p[s]
            S=((D-mu-q[:,None]*beta)/sd)@V
            for j,r in enumerate(rr): out[pos[r]]=S[j]
        return out
    wa,Va,pa=fit(A); wb,Vb,pb=fit(B); SA=project(A,Va,pa); SB=project(B,Va,pa)
    def audit(S,rows,k):
        mm=meta.iloc[rows].reset_index(drop=True); Y=S[:,:k]; Rsrc=residualize_group_means(Y,mm.source)
        bio=eta_trace(Rsrc,mm.source.astype(str)+"|"+mm.eval_class.astype(str)); src=eta_trace(Y,mm.source)
        R=residualize_group_means(Y,mm.source.astype(str)+"|"+mm.eval_class.astype(str)); donor=eta_trace(R,mm.donor_id)
        sea=mm.source.eq("SEA_AD").to_numpy(); Rs=residualize_group_means(Y[sea],mm.loc[sea,"eval_class"]); op=eta_trace(Rs,mm.loc[sea,"operator_index"])
        return {"biology_within_source_eta2":bio,"source_eta2":src,"donor_after_source_class_eta2":donor,"seaad_operator_after_class_eta2":op}
    result={"schema":"V61_SOURCE_BALANCED_TARGET_BACKBONE_REPRO_V1","feature_width":a.feature_width,"universe_n":int(len(universe)),"ranks":{}}
    for k in range(1,16):
        c=np.cos(subspace_angles(Va[:,:k],Vb[:,:k])); result["ranks"][str(k)]={"ab_mean_cos":float(c.mean()),"ab_min_cos":float(c.min()),"A":audit(SA,A,k),"B":audit(SB,B,k)}
    Path(a.out).write_text(json.dumps(result,indent=2))

if __name__=="__main__": main()
