import hashlib, glob, itertools, numpy as np, pandas as pd
from pathlib import Path
ARR=Path('/mnt/data/td_matrix_npz/arrays')
data=np.load(ARR/'data.npy',mmap_mode='r'); indices=np.load(ARR/'indices.npy',mmap_mode='r'); indptr=np.load(ARR/'indptr.npy',mmap_mode='r'); shape=tuple(np.load(ARR/'shape.npy'))
meta=pd.read_csv('/mnt/data/td_expr_meta/FOUNDATION_DISCOVERY_SAMPLE_FREEZE.csv'); meta['global_row']=np.arange(len(meta),dtype=np.int64); B=meta[meta['sample'].eq('B_COVERAGE_DISCOVERY')].copy()
parts=[pd.read_csv(p,usecols=['stable_key','source_library']) for p in glob.glob('/mnt/data/td_expr_meta/operator/*.meta.csv')]
lib=pd.concat(parts,ignore_index=True).drop_duplicates('stable_key'); B=B.merge(lib,on='stable_key',how='left',validate='one_to_one',sort=False)
assert B.global_row.min()==25000 and B.global_row.max()==49999
B['detected_genes']=(indptr[B.global_row.to_numpy()+1]-indptr[B.global_row.to_numpy()]).astype(int)
states=np.load('/mnt/data/td_support_extract/FOUNDATION_CALIBRATION_BUNDLE_20260824/foundation_calibration_bundle_20260824/support/FOUNDATION_OPERATOR_ADDRESS_OBSERVATION_STATE.npz',allow_pickle=False)['states']; common=np.where((states==1).all(0))[0]; assert len(common)==17186
ordered=np.array(sorted(common,key=lambda x:hashlib.sha256(f'TD25|{int(x)}'.encode()).digest()),dtype=np.int32); panels=[ordered[i*512:(i+1)*512] for i in range(4)]
shared=sorted(set(B[B.source.eq('HVS')].native_class.dropna()) & set(B[B.source.eq('SEA_AD')].native_class.dropna()))
sel=[c for c in shared if min(B[(B.source=='HVS')&(B.native_class==c)].donor_id.nunique(),B[(B.source=='SEA_AD')&(B.native_class==c)].donor_id.nunique())>=20]; assert len(sel)==19
family={}
for c in sel:
    fam=[]
    for src in ['HVS','SEA_AD']:
        s=B[(B.source==src)&(B.native_class==c)]; fam.append(s.broad_class.dropna().mode().iloc[0])
    family[c]=fam[0] if fam[0]==fam[1] else 'MISMATCH'

def extract(rows,genes):
    rows=np.asarray(rows,dtype=np.int64); genes=np.asarray(genes,dtype=np.int32); lut=np.full(shape[1],-1,dtype=np.int32); lut[genes]=np.arange(len(genes),dtype=np.int32)
    X=np.zeros((len(rows),len(genes)),dtype=np.float32)
    for i,r in enumerate(rows):
        a,b=int(indptr[r]),int(indptr[r+1]); ix=indices[a:b]; loc=lut[ix]; m=loc>=0
        if m.any(): X[i,loc[m]]=data[a:b][m]
    return X

def pair_indices(panel,pi,n=4096):
    pairs=[]
    for a in range(len(panel)):
        ga=int(panel[a])
        for b in range(a+1,len(panel)):
            gb=int(panel[b])
            g,h=sorted((ga,gb))
            dig=hashlib.sha256(f'TD41S|panel|{pi}|g|{g}|h|{h}'.encode()).digest()
            pairs.append((dig,a,b,g,h))
    pairs.sort(key=lambda z:z[0]); return np.array([(a,b) for _,a,b,_,_ in pairs[:n]],dtype=np.int32)

def donor_balanced_pair_centroids(sub,X,pairs):
    S=np.sign(X[:,pairs[:,0]]-X[:,pairs[:,1]]).astype(np.float32)
    C=[];Q=[]
    sc=sub.native_class.to_numpy(); dons=sub.donor_id.to_numpy()
    for c in sel:
        mask=sc==c; uds=np.unique(dons[mask]); sm=S[mask]
        dm=np.vstack([sm[dons[mask]==u].mean(0) for u in uds]); C.append(dm.mean(0))
        ss=sub.loc[mask]; Q.append([np.median(np.log1p(ss.source_library.to_numpy())),np.median(np.log1p(ss.detected_genes.to_numpy()))])
    return np.vstack(C).astype(float),np.asarray(Q,float)

def residualize(C,Q):
    Z=np.c_[np.ones(len(Q)),(Q-Q.mean(0))/Q.std(0)]; coef=np.linalg.lstsq(Z,C,rcond=None)[0]; return C-Z@coef

def distvec(C,ids):
    X=C[ids]; sd=X.std(0); keep=sd>1e-12; Z=X[:,keep]; Z=(Z-Z.mean(0))/Z.std(0); D=np.sqrt(((Z[:,None,:]-Z[None,:,:])**2).sum(2)); iu=np.triu_indices(len(ids),1); return D[iu]

ids=[i for i,c in enumerate(sel) if family[c]=='Neuronal: Glutamatergic']
for pi,panel in enumerate(panels):
    pairs=pair_indices(panel,pi)
    source={}
    for src in ['HVS','SEA_AD']:
        sub=B[(B.source==src)&B.native_class.isin(sel)].copy().sort_values('global_row')
        X=extract(sub.global_row.to_numpy(),panel)
        source[src]=donor_balanced_pair_centroids(sub,X,pairs)
    vals=[]
    for prep in ['RAW','RESID']:
        CC={s:(residualize(C,Q) if prep=='RESID' else C) for s,(C,Q) in source.items()}
        r=float(np.corrcoef(distvec(CC['HVS'],ids),distvec(CC['SEA_AD'],ids))[0,1]); vals.append(r)
    print(pi,*vals, flush=True)
