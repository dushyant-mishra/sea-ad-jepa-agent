import sys, hashlib, glob, numpy as np, pandas as pd
from scipy.stats import rankdata
from pathlib import Path
src=sys.argv[1]
ARR=Path('/mnt/data/td_matrix_npz/arrays'); data=np.load(ARR/'data.npy',mmap_mode='r'); indices=np.load(ARR/'indices.npy',mmap_mode='r'); indptr=np.load(ARR/'indptr.npy',mmap_mode='r'); shape=tuple(np.load(ARR/'shape.npy'))
meta=pd.read_csv('/mnt/data/td_expr_meta/FOUNDATION_DISCOVERY_SAMPLE_FREEZE.csv'); meta['global_row']=np.arange(len(meta)); A=meta[(meta['sample']=='A_NATURAL_MIXTURE')&(meta.source==src)].copy().sort_values('global_row').reset_index(drop=True)
parts=[pd.read_csv(p,usecols=['stable_key','source_library']) for p in glob.glob('/mnt/data/td_expr_meta/operator/*.meta.csv')]; lib=pd.concat(parts).drop_duplicates('stable_key'); A=A.merge(lib,on='stable_key',how='left',validate='one_to_one'); A['detected_genes']=(indptr[A.global_row.to_numpy()+1]-indptr[A.global_row.to_numpy()]).astype(int)
st=np.load('/mnt/data/td_support_extract/FOUNDATION_CALIBRATION_BUNDLE_20260824/foundation_calibration_bundle_20260824/support/FOUNDATION_OPERATOR_ADDRESS_OBSERVATION_STATE.npz')['states']; common=np.where((st==1).all(0))[0]; ordg=np.array(sorted(common,key=lambda x:hashlib.sha256(f'TD48S|gene|{int(x)}'.encode()).digest()),dtype=np.int32); Q=ordg[:64]; Rg=ordg[64:576]; qset=set(map(int,Q)); ctx=np.array([int(g) for g in common if int(g) not in qset],dtype=np.int32); G=len(ctx)
# context map
buckets=np.empty(G,np.int16); signs=np.empty(G,float); bcount=np.zeros(256,int); bsignsum=np.zeros(256,float)
for j,g in enumerate(ctx):
 dig=hashlib.sha256(f'TD48S|ctxgene|{int(g)}'.encode()).digest(); b=int.from_bytes(dig[:8],'big')%256; s=1.0 if (dig[8]&1)==0 else -1.0; buckets[j]=b; signs[j]=s; bcount[b]+=1; bsignsum[b]+=s
ctxpos=np.full(shape[1],-1,np.int32); ctxpos[ctx]=np.arange(G,dtype=np.int32)
# Q/R loc map for tau
qr=np.r_[Q,Rg]; qrpos=np.full(shape[1],-1,np.int32); qrpos[qr]=np.arange(576,dtype=np.int32)
n=len(A); S=np.zeros((n,256),float); tau=np.empty((n,64),float)
for i,r in enumerate(A.global_row.to_numpy()):
 a,b=int(indptr[r]),int(indptr[r+1]); ix=indices[a:b]; vals=np.asarray(data[a:b],float)
 # tau extract sparse into 576
 locq=qrpos[ix]; mq=locq>=0; vqr=np.zeros(576,float); vqr[locq[mq]]=vals[mq]; q=vqr[:64,None]; refs=vqr[64:][None,:]; tau[i]=((refs<q).sum(1)+0.5*(refs==q).sum(1))/512.0
 # context rank sketch
 loc=ctxpos[ix]; m=loc>=0; pos=loc[m]; vv=vals[m]; nn=len(pos); n0=G-nn; r0=(1+n0)/2.0; z0=(r0-1)/(G-1)-0.5; vec=z0*bsignsum.copy()
 if nn:
  rn=rankdata(vv,method='average'); zn=(n0+rn-1)/(G-1)-0.5; np.add.at(vec,buckets[pos],signs[pos]*(zn-z0))
 S[i]=vec/np.sqrt(bcount)
 if (i+1)%5000==0: print(src,i+1,flush=True)
np.savez_compressed(f'/mnt/data/td50_{src}.npz',S=S,tau=tau,global_row=A.global_row.to_numpy(),source_library=A.source_library.to_numpy(),detected=A.detected_genes.to_numpy(),donor=A.donor_id.to_numpy(),operator=A.operator_index.to_numpy())
print(src,'done',n)
