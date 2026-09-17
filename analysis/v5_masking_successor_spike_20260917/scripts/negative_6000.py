import numpy as np,pandas as pd,scipy.sparse as sp,hashlib,os
BASE='/mnt/data/jepa_spike_work';X=sp.load_npz(BASE+'/X_common6000.npz').tocsr();meta=pd.read_csv(BASE+'/expression/expression/FOUNDATION_DISCOVERY_SAMPLE_FREEZE.csv',usecols=['source','donor_id']); donor_ids,dcode=np.unique(meta.donor_id.to_numpy(),return_inverse=True);sources=np.array([meta.source.to_numpy()[dcode==d][0] for d in range(len(donor_ids))]);univ=np.load(BASE+'/universe_6000_local.npy');targets=np.load(BASE+'/scale_targets_cols.npy')[:8]
# folds
fold=np.full(len(donor_ids),-1,int)
for s in np.unique(sources):
 ds=np.flatnonzero(sources==s);seed=int.from_bytes(hashlib.sha256(f'JEPA_SCALE_FOLD|{s}'.encode()).digest()[:8],'big');perm=np.random.default_rng(seed).permutation(ds)
 for i,d in enumerate(perm):fold[d]=i%4
# neg correlations
cp=BASE+'/negative_corr_8x6000.npy'
if os.path.exists(cp):C=np.load(cp,mmap_mode='r')
else:
 C=np.lib.format.open_memmap(cp,mode='w+',dtype=np.float32,shape=(len(donor_ids),len(targets),X.shape[1]))
 for d in range(len(donor_ids)):
  rows=np.flatnonzero(dcode==d);Xd=X[rows,:].astype(np.float64);Y=Xd[:,targets].toarray();
  for ti in range(len(targets)):
   seed=int.from_bytes(hashlib.sha256(f'NEGSHUF|{d}|{ti}'.encode()).digest()[:8],'big');Y[:,ti]=np.random.default_rng(seed).permutation(Y[:,ti])
  Y-=Y.mean(0,keepdims=True);sy=np.sqrt((Y*Y).sum(0));num=np.asarray(Xd.T@Y); sx2=np.asarray(Xd.power(2).sum(axis=0)).ravel()-np.asarray(Xd.sum(axis=0)).ravel()**2/len(rows);den=np.sqrt(np.maximum(sx2,0))[:,None]*sy[None,:];R=np.divide(num,den,out=np.zeros_like(num),where=den>1e-12);C[d]=np.abs(R.T).astype(np.float32)
 C.flush()
def bal(vals,don):return np.mean([np.mean(vals[sources[don]==s],axis=0) for s in np.unique(sources[don])],axis=0)
def ts(ti,don,cols):return bal(np.asarray(C[don,ti,:])[:,cols],don)
def vs(ti,don,col):r=np.asarray(C[don,ti,col]);return float(bal((r*r)[:,None],don).ravel()[0])
def inner3(tr):
 g=[[] for _ in range(3)]
 for s in np.unique(sources[tr]):
  ds=tr[sources[tr]==s];seed=int.from_bytes(hashlib.sha256(f'JEPA_SCALE_INNER|{s}'.encode()).digest()[:8],'big');p=np.random.default_rng(seed).permutation(ds)
  for i,d in enumerate(p):g[i%3].append(int(d))
 return [np.array(x,int) for x in g]
def comb(sets,ev,cap=8):
 su={}
 for ss in sets:
  for a in set(map(int,ss)):su[a]=su.get(a,0)+1
 if not su:return []
 it=np.array(list(su),int);sp=np.array([su[x] for x in it]);o=np.lexsort((it,-ev[it],-sp));return list(it[o[:cap]])
def pref(ti,tr,tcol):
 gs=inner3(tr);sets=[]
 for rot in range(3):
  A,B,Cg=gs[rot],gs[(rot+1)%3],gs[(rot+2)%3];s=ts(ti,A,univ);cand=univ[np.lexsort((univ,-s))[:20]];cand=cand[cand!=tcol]
  def ev(rem):
   if not len(rem):return 0.
   sb=ts(ti,B,rem);j=rem[np.lexsort((rem,-sb))[0]];return vs(ti,Cg,int(j))
  p0=ev(cand)
  if p0<.02:sets.append([]);continue
  ch=[]
  for k in range(1,min(8,len(cand))+1):
   if ev(np.setdiff1d(cand,cand[:k]))<=.75*p0:ch=list(map(int,cand[:k]));break
  if not ch:ch=list(map(int,cand[:8]));sets.append(ch)
 ev=np.zeros(X.shape[1]);ev[univ]=ts(ti,tr,univ);return comb(sets,ev)
def top(ti,tr,tcol):
 s=ts(ti,tr,univ).copy();s[univ==tcol]=-1;return list(map(int,univ[np.lexsort((univ,-s))[:8]]))
def mask(tcol,fi,ti,tg):
 burden=900;pool=univ[univ!=tcol];seed=int.from_bytes(hashlib.sha256(f'JEPA_SCALE_MASK|6000|{fi}|{ti}'.encode()).digest()[:8],'big');base=list(map(int,np.random.default_rng(seed).choice(pool,burden-1,False)));M=set(base+[int(tcol)]);add=[a for a in tg if a not in M];rem=sorted([a for a in base if a not in tg],key=lambda a:hashlib.sha256(f'REMOVE|{fi}|{ti}|{a}'.encode()).digest());
 for a,r in zip(add,rem):M.discard(r);M.add(a)
 return M
def attack(ti,tr,va,tcol,M):
 vis=np.array([c for c in univ if c not in M and c!=tcol]);s=ts(ti,tr,vis);j=vis[np.lexsort((vis,-s))[0]];return vs(ti,va,int(j))
rows=[]
for fi in range(4):
 va=np.flatnonzero(fold==fi);tr=np.flatnonzero(fold!=fi)
 for ti,tcol in enumerate(targets):
  base=mask(tcol,fi,ti,[]);u=attack(ti,tr,va,tcol,base)
  for m,tg in [('TOP8',top(ti,tr,tcol)),('PREFIX3',pref(ti,tr,tcol))]:
   sc=attack(ti,tr,va,tcol,mask(tcol,fi,ti,tg));rows.append(dict(fold=fi,target=ti,method=m,U=u,score=sc,delta=u-sc,targeted_n=len(tg)))
d=pd.DataFrame(rows);d.to_csv(BASE+'/negative_6000_pairs.csv',index=False)
for m,g in d.groupby('method'):
 gt=g.groupby('target').delta.mean();print(m,'mean',g.delta.mean(),'median',g.delta.median(),'targetmean',gt.mean(),'win', (g.delta>0).mean(),'actions',(g.targeted_n>0).sum())
