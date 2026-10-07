from __future__ import annotations
import hashlib,json,glob
from pathlib import Path
import numpy as np,pandas as pd
ROOT=Path('/mnt/data'); OUT=ROOT/'td_iteration34_state_geometry_globalrow'; OUT.mkdir(exist_ok=True)
ARR=ROOT/'td_matrix_npz'/'arrays'; META=ROOT/'td_expr_meta'/'FOUNDATION_DISCOVERY_SAMPLE_FREEZE.csv'; SUP=ROOT/'td_support_extract'/'FOUNDATION_CALIBRATION_BUNDLE_20260824'/'foundation_calibration_bundle_20260824'/'support'/'FOUNDATION_OPERATOR_ADDRESS_OBSERVATION_STATE.npz'
data=np.load(ARR/'data.npy',mmap_mode='r'); indices=np.load(ARR/'indices.npy',mmap_mode='r'); indptr=np.load(ARR/'indptr.npy',mmap_mode='r'); shape=tuple(np.load(ARR/'shape.npy'))
meta=pd.read_csv(META); meta['global_row']=np.arange(len(meta),dtype=np.int64); B=meta[meta['sample'].eq('B_COVERAGE_DISCOVERY')].copy()
parts=[pd.read_csv(p,usecols=['stable_key','source_library']) for p in glob.glob('/mnt/data/td_expr_meta/operator/**/op*.meta.csv',recursive=True)]
lib=pd.concat(parts,ignore_index=True).drop_duplicates('stable_key'); B=B.merge(lib,on='stable_key',how='left',validate='one_to_one',sort=False); assert B.source_library.notna().all(); assert B.global_row.min()==25000 and B.global_row.max()==49999
B['detected_genes']=(indptr[B.global_row.to_numpy()+1]-indptr[B.global_row.to_numpy()]).astype(int)
states=np.load(SUP,allow_pickle=False)['states']; common=np.where((states==1).all(0))[0]
ordered=np.array(sorted(common,key=lambda x:hashlib.sha256(f'TD25|{int(x)}'.encode()).digest()),dtype=np.int32); panels=[ordered[i*512:(i+1)*512] for i in range(4)]
# outcome-blind state rule: native class present in both sources with >=20 B-sample donors each
shared=sorted(set(B[B.source.eq('HVS')].native_class.dropna()) & set(B[B.source.eq('SEA_AD')].native_class.dropna()))
sel=[]
for c in shared:
    dh=B[(B.source.eq('HVS'))&(B.native_class.eq(c))].donor_id.nunique(); ds=B[(B.source.eq('SEA_AD'))&(B.native_class.eq(c))].donor_id.nunique()
    if min(dh,ds)>=20: sel.append(c)
assert len(sel)==19, sel
# Broad family for subgeometry requires agreement across HVS/SEA metadata; derive mode and require same
family={}
state_rows=[]
for c in sel:
    rec={'native_class':c}
    fams=[]
    for src in ['HVS','SEA_AD']:
        s=B[(B.source.eq(src))&(B.native_class.eq(c))]
        rec[f'{src}_cells']=len(s); rec[f'{src}_donors']=s.donor_id.nunique(); rec[f'{src}_operators']=s.operator_index.nunique()
        m=s.broad_class.dropna(); mode=m.mode().iloc[0] if len(m) else ''
        rec[f'{src}_broad']=mode; fams.append(mode)
    family[c]=fams[0] if fams[0]==fams[1] else 'MISMATCH'
    state_rows.append(rec)
pd.DataFrame(state_rows).to_csv(OUT/'TD25_STATE_SELECTION.csv',index=False)

def extract(rows,genes):
    rows=np.asarray(rows,dtype=np.int64); genes=np.asarray(genes,dtype=np.int32); lut=np.full(shape[1],-1,dtype=np.int32); lut[genes]=np.arange(len(genes),dtype=np.int32)
    X=np.zeros((len(rows),len(genes)),dtype=np.float32)
    for i,r in enumerate(rows):
        a,b=int(indptr[r]),int(indptr[r+1]); ix=indices[a:b]; loc=lut[ix]; m=loc>=0
        if m.any(): X[i,loc[m]]=data[a:b][m]
    return X

def donor_balanced_centroids(sub,X):
    C=[]; Q=[]
    for c in sel:
        mask=sub.native_class.to_numpy()==c; d=sub.loc[mask,'donor_id'].to_numpy(); xx=X[mask]
        uds=np.unique(d); dm=np.vstack([xx[d==u].mean(0) for u in uds]); C.append(dm.mean(0))
        ss=sub.loc[mask]; Q.append([np.median(np.log1p(ss.source_library.to_numpy())),np.median(np.log1p(ss.detected_genes.to_numpy()))])
    return np.vstack(C).astype(float),np.asarray(Q,float)

def residualize(C,Q):
    Z=np.c_[np.ones(len(Q)),(Q-Q.mean(0))/Q.std(0)]
    coef=np.linalg.lstsq(Z,C,rcond=None)[0]
    return C-Z@coef

def std_gene(C):
    sd=C.std(0); keep=sd>1e-12; Z=C[:,keep]; return (Z-Z.mean(0))/Z.std(0)

def distvec(C,ids):
    Z=std_gene(C[ids]); D=np.sqrt(np.sum((Z[:,None,:]-Z[None,:,:])**2,axis=2)); iu=np.triu_indices(len(ids),1); return D[iu]

def corr(x,y): return float(np.corrcoef(x,y)[0,1]) if len(x)>=4 else np.nan
rng=np.random.default_rng(250907)
records=[]
for pi,panel in enumerate(panels):
    source={}
    for src in ['HVS','SEA_AD']:
        sub=B[(B.source.eq(src))&(B.native_class.isin(sel))].copy().sort_index(); X=extract(sub.global_row.to_numpy(),panel); C,Q=donor_balanced_centroids(sub,X); source[src]=(C,Q)
    for prep in ['RAW','STATE_DEPTH_DET_RESID']:
        CC={src:(residualize(C,Q) if prep!='RAW' else C) for src,(C,Q) in source.items()}
        subsets={'ALL19':list(range(len(sel))),
                 'GLUT':[i for i,c in enumerate(sel) if family[c]=='Neuronal: Glutamatergic'],
                 'GABA':[i for i,c in enumerate(sel) if family[c]=='Neuronal: GABAergic'],
                 'NONNEUR':[i for i,c in enumerate(sel) if family[c]=='Non-neuronal and Non-neural']}
        for name,ids in subsets.items():
            if len(ids)<4: continue
            x=distvec(CC['HVS'],ids); y=distvec(CC['SEA_AD'],ids); obs=corr(x,y)
            null=[]
            for _ in range(1000):
                p=rng.permutation(ids)
                yp=distvec(CC['SEA_AD'],list(p)); null.append(corr(x,yp))
            records.append({'panel':pi,'preprocess':prep,'subset':name,'n_states':len(ids),'n_distances':len(x),'graph_r':obs,'null_median':float(np.nanmedian(null)),'null_p95':float(np.nanquantile(null,.95)),'null_max':float(np.nanmax(null)),'empirical_p':float((1+sum(v>=obs for v in null))/(1+len(null)))})

df=pd.DataFrame(records); df.to_csv(OUT/'TD25_CORRECTED_STATE_RELATIONAL_GEOMETRY.csv',index=False)
summary=df.groupby(['preprocess','subset']).agg(n_panels=('panel','count'),median_r=('graph_r','median'),min_r=('graph_r','min'),max_r=('graph_r','max'),median_null_p95=('null_p95','median'),max_empirical_p=('empirical_p','max')).reset_index(); summary.to_csv(OUT/'TD25_SUMMARY.csv',index=False)
s={'schema':'td34-global-row-guarded-state-relational-geometry-v1','status':'FALSIFICATION_ONLY__LABELS_USED_FOR_VALIDATION__NOT_TARGET_AUTHORITY','historical_predecessor':'TD17/18 non-durable relational scaffold plus TD23 row-alias discovery','what_is_materially_new':'independent correct-global-row regeneration; outcome-blind >=20 donors/source native-state rule; 17,186 common-scalar panels; donor-balanced centroids; state depth/detection residual attack; fixed label correspondence only','selected_states':sel,'state_count':len(sel),'panel_size':512,'panels':4,'null_permutations':1000,'promotion_status':'FALSIFICATION_ONLY','pathology_accessed':False,'protected_expression_accessed':False}
(OUT/'TD25_SUMMARY.json').write_text(json.dumps(s,indent=2)+'\n')
print(pd.DataFrame(state_rows).to_string(index=False)); print('\n',summary.to_string(index=False)); print(json.dumps(s,indent=2))
