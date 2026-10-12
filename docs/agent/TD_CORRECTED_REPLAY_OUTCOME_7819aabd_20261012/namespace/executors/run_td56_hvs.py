import hashlib, itertools, numpy as np
from pathlib import Path
SRC='HVS'; NP=2048
ARR=Path('/mnt/data/td_matrix_npz/arrays')
data=np.load(ARR/'data.npy',mmap_mode='r');indices=np.load(ARR/'indices.npy',mmap_mode='r');indptr=np.load(ARR/'indptr.npy',mmap_mode='r');shape=tuple(np.load(ARR/'shape.npy'))
st=np.load('/mnt/data/td_support_extract/FOUNDATION_CALIBRATION_BUNDLE_20260824/foundation_calibration_bundle_20260824/support/FOUNDATION_OPERATOR_ADDRESS_OBSERVATION_STATE.npz')['states']
common=np.where((st==1).all(0))[0]
def h(x):return hashlib.sha256(x.encode()).digest()
genes=np.array(sorted(common,key=lambda g:h(f'TD56S|gene|{int(g)}')),dtype=np.int32)
GX,GY=genes[:512],genes[512:1024]
assert len(set(GX)&set(GY))==0

def select_pairs(G,label):
 pairs=[]
 for a in range(511):
  ga=int(G[a])
  for b in range(a+1,512):
   gb=int(G[b]); pairs.append((h(f'TD56S|view|{label}|g|{ga}|h|{gb}'),a,b,ga,gb))
 pairs.sort(key=lambda x:x[0]); p=pairs[:NP]
 return np.array([[x[1],x[2]] for x in p],np.int32), np.array([[x[3],x[4]] for x in p],np.int32)
PX,_=select_pairs(GX,'X'); PY,_=select_pairs(GY,'Y')
print('common',len(common),'pair overlap genes',len(set(GX)&set(GY)),flush=True)
Z=np.load(f'/mnt/data/td50_{SRC}.npz',allow_pickle=True); rows=Z['global_row'].astype(np.int64); donor=Z['donor'].astype(str); op=Z['operator'].astype(str); lib=Z['source_library'].astype(float); det=Z['detected'].astype(float)
sel=np.r_[GX,GY];lut=np.full(shape[1],-1,np.int32);lut[sel]=np.arange(1024,dtype=np.int32);X=np.zeros((len(rows),1024),np.float32)
for i,r in enumerate(rows):
 a,b=int(indptr[r]),int(indptr[r+1]); ix=indices[a:b]; loc=lut[ix];m=loc>=0
 if m.any():X[i,loc[m]]=data[a:b][m]
SX=np.sign(X[:,PX[:,0]]-X[:,PX[:,1]]).astype(np.int8)
Yv=X[:,512:]
SY=np.sign(Yv[:,PY[:,0]]-Yv[:,PY[:,1]]).astype(np.int8)
# sample cell pairs
samples=[]
for d in sorted(np.unique(donor)):
 for o in sorted(np.unique(op[donor==d])):
  ids=np.where((donor==d)&(op==o))[0]
  if len(ids)<4:continue
  cand=[]
  for aa in range(len(ids)-1):
   i=int(ids[aa]);ga=int(rows[i])
   for bb in range(aa+1,len(ids)):
    j=int(ids[bb]);gb=int(rows[j]); a0,b0=sorted((ga,gb)); cand.append((h(f'TD56S|cellpair|source|{SRC}|donor|{d}|operator|{o}|global_row_a|{a0}|global_row_b|{b0}'),i,j,d,o))
  cand.sort(key=lambda x:x[0]); samples.extend(cand[:64])
print('sampled cellpairs',len(samples),'strata',len(set((x[3],x[4]) for x in samples)),flush=True)

def dist(S,a,b):
 inf=(S[a]!=0)|(S[b]!=0); n=int(inf.sum())
 if n<256:return np.nan
 return float(np.mean(np.abs(S[a,inf].astype(np.int16)-S[b,inf].astype(np.int16)))/2.0)
# observed cached X dist and donor structures
obs_by={}
for _,i,j,d,o in samples:
 dx=dist(SX,i,j);dy=dist(SY,i,j)
 if np.isfinite(dx) and np.isfinite(dy):obs_by.setdefault(d,[]).append((i,j,dx,dy))

def source_stat(by, perm=None):
 rs=[]; ds=[]
 for d,vals in by.items():
  xs=[];ys=[]
  for i,j,dx,dy0 in vals:
   dy=dy0 if perm is None else dist(SY,int(perm[i]),int(perm[j]))
   if np.isfinite(dy): xs.append(dx);ys.append(dy)
  if len(xs)>=20 and np.var(xs)>1e-12 and np.var(ys)>1e-12:
   r=float(np.corrcoef(xs,ys)[0,1]);r=float(np.clip(r,-0.999999,0.999999));rs.append(r);ds.append(d)
 if len(rs)<8:return np.nan,len(rs),rs,ds
 return float(np.tanh(np.median(np.arctanh(rs)))),len(rs),rs,ds
obs,nD,rs,ds=source_stat(obs_by)
print('OBS',obs,'meas donors',nD,'donor r med/min/max',float(np.median(rs)),float(np.min(rs)),float(np.max(rs)),flush=True)
# null blocks exact TD37A
blocks=[]
for d in sorted(np.unique(donor)):
 for o in sorted(np.unique(op[donor==d])):
  ids=np.where((donor==d)&(op==o))[0];n=len(ids)
  if n==1:blocks.append((d,o,0,ids.copy()));continue
  pos={int(x):k for k,x in enumerate(ids)}
  rd=np.empty(n,int);oo=ids[np.lexsort((rows[ids],det[ids]))]
  for k,x in enumerate(oo):rd[pos[int(x)]]=k
  rl=np.empty(n,int);oo=ids[np.lexsort((rows[ids],lib[ids]))]
  for k,x in enumerate(oo):rl[pos[int(x)]]=k
  rdf=rd/n;rlf=rl/n;octv=np.floor(8*rdf).astype(int);ids2=ids[np.lexsort((rows[ids],rdf,rlf,octv))];chunks=[ids2[a:a+8] for a in range(0,n,8)]
  if len(chunks)>1 and len(chunks[-1])==1:chunks[-2]=np.r_[chunks[-2],chunks[-1]];chunks=chunks[:-1]
  for b,bb in enumerate(chunks):blocks.append((d,o,b,bb))
def u64(t):return int.from_bytes(h(t)[:8],'big')
null=[];nd=[]
for q in range(64):
 perm=np.arange(len(rows))
 for d,o,b,ids in blocks:
  m=len(ids)
  if m<2:continue
  sh=1+(u64(f'TD56S|null|{q}|source|{SRC}|donor|{d}|operator|{o}|block|{b}')%(m-1));perm[ids]=np.roll(ids,-sh)
 s,n,_,_=source_stat(obs_by,perm);null.append(s);nd.append(n)
null=np.array(null,float); sn=np.sort(null[np.isfinite(null)]);p95=sn[60] if len(sn)==64 else np.nan
print('NULL finite',np.isfinite(null).sum(),'med',float(np.nanmedian(null)),'p95',float(p95),'max',float(np.nanmax(null)),'PASS',bool(obs>p95 and obs>0),flush=True)
np.savez('/mnt/data/td56_HVS_result.npz',obs=obs,null=null,p95=p95,donor_rs=np.array(rs),donors=np.array(ds,dtype=object),null_donors=np.array(nd))
