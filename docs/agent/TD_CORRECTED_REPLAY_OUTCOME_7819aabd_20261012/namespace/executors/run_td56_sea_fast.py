import hashlib, numpy as np
from pathlib import Path
SRC='SEA_AD'; NP=2048
ARR=Path('/mnt/data/td_matrix_npz/arrays');data=np.load(ARR/'data.npy',mmap_mode='r');indices=np.load(ARR/'indices.npy',mmap_mode='r');indptr=np.load(ARR/'indptr.npy',mmap_mode='r');shape=tuple(np.load(ARR/'shape.npy'))
st=np.load('/mnt/data/td_support_extract/FOUNDATION_CALIBRATION_BUNDLE_20260824/foundation_calibration_bundle_20260824/support/FOUNDATION_OPERATOR_ADDRESS_OBSERVATION_STATE.npz')['states']; common=np.where((st==1).all(0))[0]
def hh(x):return hashlib.sha256(x.encode()).digest()
genes=np.array(sorted(common,key=lambda g:hh(f'TD56S|gene|{int(g)}')),dtype=np.int32);GX,GY=genes[:512],genes[512:1024]
def selpairs(G,L):
 v=[]
 for a in range(511):
  ga=int(G[a])
  for b in range(a+1,512):
   gb=int(G[b]);v.append((hh(f'TD56S|view|{L}|g|{ga}|h|{gb}'),a,b))
 v.sort(key=lambda x:x[0]);return np.array([[x[1],x[2]] for x in v[:NP]],np.int32)
PX=selpairs(GX,'X');PY=selpairs(GY,'Y')
Z=np.load('/mnt/data/td50_SEA_AD.npz',allow_pickle=True);rows=Z['global_row'].astype(np.int64);donor=Z['donor'].astype(str);op=Z['operator'].astype(str);lib=Z['source_library'].astype(float);det=Z['detected'].astype(float)
sel=np.r_[GX,GY];lut=np.full(shape[1],-1,np.int32);lut[sel]=np.arange(1024,dtype=np.int32);V=np.zeros((len(rows),1024),np.float32)
for i,r in enumerate(rows):
 a,b=int(indptr[r]),int(indptr[r+1]);ix=indices[a:b];loc=lut[ix];m=loc>=0
 if m.any():V[i,loc[m]]=data[a:b][m]
SX=np.sign(V[:,PX[:,0]]-V[:,PX[:,1]]).astype(np.int8);Y0=V[:,512:];SY=np.sign(Y0[:,PY[:,0]]-Y0[:,PY[:,1]]).astype(np.int8)
# strata + local distance matrices
strata={}; local={}
for d in sorted(np.unique(donor)):
 for o in sorted(np.unique(op[donor==d])):
  ids=np.where((donor==d)&(op==o))[0]
  if len(ids)>=4:
   key=(d,o);strata[key]=ids;local.update({int(g): (key,k) for k,g in enumerate(ids)})
# exact fast distance matrix from sign categories
def distmat(S):
 p=S.shape[1]; pos=(S==1).astype(np.int16);neg=(S==-1).astype(np.int16);zero=(S==0).astype(np.int16);nz=(S!=0).sum(1).astype(np.int32)
 same=(pos@pos.T + neg@neg.T).astype(np.int32); bothz=(zero@zero.T).astype(np.int32)
 l1=nz[:,None]+nz[None,:]-2*same; inf=p-bothz
 D=np.full((len(S),len(S)),np.nan,np.float64);good=inf>=256;D[good]=l1[good]/(2.0*inf[good]);return D,inf
DX={};DY={}
for key,ids in strata.items():
 DX[key],_=distmat(SX[ids]);DY[key],_=distmat(SY[ids])
# validation fast vs naive on deterministic 128 pairs
checks=[]
for key in sorted(strata)[:20]:
 ids=strata[key]
 for a in range(min(3,len(ids)-1)):
  i,j=int(ids[a]),int(ids[-1-a]);inf=(SY[i]!=0)|(SY[j]!=0);na=np.nan if inf.sum()<256 else float(np.mean(np.abs(SY[i,inf].astype(np.int16)-SY[j,inf].astype(np.int16)))/2)
  fa=DY[key][local[i][1],local[j][1]];checks.append(abs(na-fa) if np.isfinite(na) else 0)
print('FAST_VALIDATE maxdiff',max(checks),flush=True)
# sampled pairs
samples=[]
for key,ids in strata.items():
 d,o=key;c=[]
 for a in range(len(ids)-1):
  i=int(ids[a]);ga=int(rows[i])
  for b in range(a+1,len(ids)):
   j=int(ids[b]);gb=int(rows[j]);x,y=sorted((ga,gb));c.append((hh(f'TD56S|cellpair|source|{SRC}|donor|{d}|operator|{o}|global_row_a|{x}|global_row_b|{y}'),i,j))
 c.sort(key=lambda z:z[0])
 for _,i,j in c[:64]:
  li=local[i][1];lj=local[j][1];dx=DX[key][li,lj];dy=DY[key][li,lj]
  if np.isfinite(dx) and np.isfinite(dy):samples.append((d,o,i,j,dx,dy))
by={}
for d,o,i,j,dx,dy in samples:by.setdefault(d,[]).append((o,i,j,dx,dy))
def stat(perm=None):
 rs=[];ds=[]
 for d,vals in by.items():
  x=[];y=[]
  for o,i,j,dx,dy0 in vals:
   if perm is None:dy=dy0
   else:
    pi,pj=int(perm[i]),int(perm[j]);key=(d,o);dy=DY[key][local[pi][1],local[pj][1]]
   if np.isfinite(dy):x.append(dx);y.append(dy)
  if len(x)>=20 and np.var(x)>1e-12 and np.var(y)>1e-12:
   r=float(np.clip(np.corrcoef(x,y)[0,1],-0.999999,0.999999));rs.append(r);ds.append(d)
 if len(rs)<8:return np.nan,len(rs),rs,ds
 return float(np.tanh(np.median(np.arctanh(rs)))),len(rs),rs,ds
obs,nD,rs,ds=stat();print('OBS',obs,'donors',nD,'samples',len(samples),flush=True)
# null blocks for all rows in strata incl small? contract every donor×operator. build all
blocks=[]
for d in sorted(np.unique(donor)):
 for o in sorted(np.unique(op[donor==d])):
  ids=np.where((donor==d)&(op==o))[0];n=len(ids)
  if n==1:blocks.append((d,o,0,ids.copy()));continue
  pos={int(x):k for k,x in enumerate(ids)};rd=np.empty(n,int);oo=ids[np.lexsort((rows[ids],det[ids]))]
  for k,x in enumerate(oo):rd[pos[int(x)]]=k
  rl=np.empty(n,int);oo=ids[np.lexsort((rows[ids],lib[ids]))]
  for k,x in enumerate(oo):rl[pos[int(x)]]=k
  rdf=rd/n;rlf=rl/n;octv=np.floor(8*rdf).astype(int);ids2=ids[np.lexsort((rows[ids],rdf,rlf,octv))];chunks=[ids2[a:a+8] for a in range(0,n,8)]
  if len(chunks)>1 and len(chunks[-1])==1:chunks[-2]=np.r_[chunks[-2],chunks[-1]];chunks=chunks[:-1]
  for b,bb in enumerate(chunks):blocks.append((d,o,b,bb))
def u64(t):return int.from_bytes(hh(t)[:8],'big')
null=[]
for q in range(64):
 perm=np.arange(len(rows))
 for d,o,b,ids in blocks:
  if len(ids)<2:continue
  sh=1+(u64(f'TD56S|null|{q}|source|{SRC}|donor|{d}|operator|{o}|block|{b}')%(len(ids)-1));perm[ids]=np.roll(ids,-sh)
 s,_,_,_=stat(perm);null.append(s)
null=np.array(null);p95=np.sort(null)[60];print('NULL med',float(np.median(null)),'p95',float(p95),'max',float(np.max(null)),'PASS',bool(obs>p95 and obs>0),flush=True)
np.savez('/mnt/data/td56_SEA_AD_result.npz',obs=obs,null=null,p95=p95,donor_rs=np.array(rs),donors=np.array(ds,dtype=object))
