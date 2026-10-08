import numpy as np, scipy.sparse as sp, hashlib, os, json, time
base='/mnt/data/jepa_spike_work'
raw=base+'/csr_raw'
indices=np.load(raw+'/indices.npy',mmap_mode='r')
indptr=np.load(raw+'/indptr.npy',mmap_mode='r')
data=np.load(raw+'/data.npy',mmap_mode='r')
shape=tuple(np.load(raw+'/shape.npy'))
print('raw',shape,indices.dtype,data.dtype,len(data),flush=True)
X=sp.csr_matrix((data,indices,indptr),shape=shape,copy=False)
common=np.load(base+'/common_core.npy')
seed=int.from_bytes(hashlib.sha256(b'JEPA_MASKING_SCALE_SPIKE_20260917').digest()[:8],'big')
rng=np.random.default_rng(seed)
perm=rng.permutation(common)
sel_identity=perm[:6000]
# sliced matrix columns sorted original address ids for efficient indexing
sel_sorted=np.sort(sel_identity)
t=time.time(); Y=X[:,sel_sorted].astype(np.float32); Y.sort_indices()
print('slice',Y.shape,Y.nnz,'density',Y.nnz/(Y.shape[0]*Y.shape[1]),'sec',time.time()-t,flush=True)
sp.save_npz(base+'/X_common6000.npz',Y,compressed=True)
np.save(base+'/selected6000_sorted.npy',sel_sorted)
np.save(base+'/selected6000_identity_order.npy',sel_identity)
# nested universes are identity sets first N from deterministic permutation; local indices in sorted 6000 matrix
pos={int(a):i for i,a in enumerate(sel_sorted)}
for n in [800,2000,6000]:
 ids=sel_identity[:n]
 local=np.array(sorted(pos[int(a)] for a in ids),dtype=np.int64)
 np.save(f'{base}/universe_{n}_local.npy',local)
 np.save(f'{base}/universe_{n}_address_ids.npy',np.sort(ids))
 print(n,'local range',local.min(),local.max(),flush=True)
