import numpy as np,pandas as pd,scipy.sparse as sp,hashlib,time,os
B='/mnt/data/jepa_spike_work'
X=sp.load_npz(B+'/X_common6000.npz').tocsr()
u800=set(np.load(B+'/universe_800_local.npy').tolist()); u6000=np.load(B+'/universe_6000_local.npy')
outer=np.array([c for c in u6000 if int(c) not in u800],dtype=int)
# Eligibility uses only target's own support/variance, not target relationships.
Xs=X[:,outer]
n=X.shape[0]
mean=np.asarray(Xs.mean(axis=0)).ravel(); mean2=np.asarray(Xs.power(2).mean(axis=0)).ravel(); var=mean2-mean**2
nnz=np.diff(Xs.tocsc().indptr)/n
pool=np.flatnonzero(nnz>=0.15); cutoff=np.quantile(var[pool],0.5); elig=pool[var[pool]>=cutoff]
addr=np.load(B+'/selected6000_sorted.npy')
def h(j): return hashlib.sha256(f'JEPA_MASKING_TARGET_OUTER5200_AUDIT_20260917|{int(addr[outer[j]])}'.encode()).digest()
sel=np.array(sorted(elig,key=h)[:32],dtype=int); targets=outer[sel]
np.save('/mnt/data/outer5200_targets32_cols.npy',targets); np.save('/mnt/data/outer5200_targets32_addr.npy',addr[targets])
print('outer',len(outer),'eligible',len(elig),'targets',targets.tolist(),'addr',addr[targets].tolist(),flush=True)
meta=pd.read_csv(B+'/expression/expression/FOUNDATION_DISCOVERY_SAMPLE_FREEZE.csv',usecols=['source','donor_id'])
donor_ids,dcode=np.unique(meta.donor_id.to_numpy(),return_inverse=True)
C=np.lib.format.open_memmap('/mnt/data/outer5200_32_donor_target_abs_corr.npy',mode='w+',dtype=np.float32,shape=(len(donor_ids),len(targets),X.shape[1]))
t0=time.time()
for d in range(len(donor_ids)):
 rows=np.flatnonzero(dcode==d); Xd=X[rows].astype(np.float64); Y=Xd[:,targets].toarray(); Y-=Y.mean(axis=0,keepdims=True); sy=np.sqrt((Y*Y).sum(axis=0))
 num=np.asarray(Xd.T@Y); sx2=np.asarray(Xd.power(2).sum(axis=0)).ravel()-np.asarray(Xd.sum(axis=0)).ravel()**2/max(len(rows),1)
 den=np.sqrt(np.maximum(sx2,0))[:,None]*sy[None,:]; R=np.divide(num,den,out=np.zeros_like(num),where=den>1e-12); C[d]=np.abs(R.T).astype(np.float32)
C.flush(); print('DONE',C.shape,'elapsed',round(time.time()-t0,2),flush=True)
