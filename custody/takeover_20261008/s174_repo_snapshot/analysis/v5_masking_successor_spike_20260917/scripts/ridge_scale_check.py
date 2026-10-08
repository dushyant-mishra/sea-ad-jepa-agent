import numpy as np, pandas as pd, scipy.sparse as sp, hashlib, os, time
BASE='/mnt/data/jepa_spike_work'; X=sp.load_npz(BASE+'/X_common6000.npz').tocsr()
meta=pd.read_csv(BASE+'/expression/expression/FOUNDATION_DISCOVERY_SAMPLE_FREEZE.csv',usecols=['source','donor_id'])
donor_ids,dcode=np.unique(meta.donor_id.to_numpy(),return_inverse=True); sources=np.array([meta.source.to_numpy()[dcode==d][0] for d in range(len(donor_ids))])
U={n:np.load(f'{BASE}/universe_{n}_local.npy') for n in [800,2000,6000]}; addr=np.load(BASE+'/selected6000_sorted.npy'); targets=np.load(BASE+'/scale_targets_cols.npy')[:16]
C=np.load(BASE+'/donor_target_abs_corr.npy',mmap_mode='r')
fold=np.full(len(donor_ids),-1,int)
for s in np.unique(sources):
 ds=np.flatnonzero(sources==s); seed=int.from_bytes(hashlib.sha256(f'JEPA_SCALE_FOLD|{s}'.encode()).digest()[:8],'big'); perm=np.random.default_rng(seed).permutation(ds)
 for i,d in enumerate(perm): fold[d]=i%4
def bal_mean(vals, donors):
 outs=[]
 for s in np.unique(sources[donors]): outs.append(np.mean(vals[sources[donors]==s],axis=0))
 return np.mean(outs,axis=0)
def train_score(ti,donors,cols): return bal_mean(np.asarray(C[donors,ti,:])[:,cols],donors)
def val_corr2(ti,donors,col):
 r=np.asarray(C[donors,ti,col]); return float(bal_mean((r*r)[:,None],donors).ravel()[0])
def inner3(train_d):
 groups=[[] for _ in range(3)]
 for s in np.unique(sources[train_d]):
  ds=train_d[sources[train_d]==s]; seed=int.from_bytes(hashlib.sha256(f'JEPA_SCALE_INNER|{s}'.encode()).digest()[:8],'big'); perm=np.random.default_rng(seed).permutation(ds)
  for i,d in enumerate(perm): groups[i%3].append(int(d))
 return [np.array(sorted(g),int) for g in groups]
def combine_sets(sets,evidence,cap=8):
 sup={}
 for ss in sets:
  for a in set(map(int,ss)): sup[a]=sup.get(a,0)+1
 if not sup:return []
 items=np.array(list(sup),int); su=np.array([sup[int(a)] for a in items]); ev=evidence[items]; order=np.lexsort((items,-ev,-su)); return list(items[order[:cap]])
def prefix3(ti,tr,univ,tcol,floor=.02,reduction=.25,cap=8,cand_m=20):
 groups=inner3(tr); sets=[]; univ=np.array(univ,int)
 for rot in range(3):
  A,B,Cg=groups[rot],groups[(rot+1)%3],groups[(rot+2)%3]; sa=train_score(ti,A,univ); cand=univ[np.lexsort((univ,-sa))[:cand_m]]; cand=cand[cand!=tcol]
  def ev(rem):
   if not len(rem): return 0.0
   sb=train_score(ti,B,rem); j=rem[np.lexsort((rem,-sb))[0]]; return val_corr2(ti,Cg,int(j))
  p0=ev(cand)
  if p0<floor: sets.append([]); continue
  ch=[]
  for k in range(1,min(cap,len(cand))+1):
   if ev(np.setdiff1d(cand,cand[:k])) <= (1-reduction)*p0: ch=list(map(int,cand[:k])); break
  if not ch: ch=list(map(int,cand[:min(cap,len(cand))]))
  sets.append(ch)
 evidence=np.zeros(X.shape[1]); evidence[univ]=train_score(ti,tr,univ); return combine_sets(sets,evidence,cap)
def top8(ti,tr,univ,tcol):
 univ=np.array(univ,int); s=train_score(ti,tr,univ).copy(); s[univ==tcol]=-1; return list(map(int,univ[np.lexsort((univ,-s))[:8]]))
def make_mask(univ,tcol,fi,ti,targeted):
 burden=max(2,int(round(.15*len(univ)))); pool=np.array(univ)[np.array(univ)!=tcol]; seed=int.from_bytes(hashlib.sha256(f'JEPA_SCALE_MASK|{len(univ)}|{fi}|{ti}'.encode()).digest()[:8],'big'); rng=np.random.default_rng(seed); base=list(map(int,rng.choice(pool,size=burden-1,replace=False))); mask=set(base+[int(tcol)])
 add=[a for a in targeted if a not in mask and a!=tcol]; rem=sorted([a for a in base if a not in targeted],key=lambda a:hashlib.sha256(f'REMOVE|{fi}|{ti}|{a}'.encode()).digest())
 for a,r in zip(add,rem): mask.discard(r);mask.add(a)
 return mask
def std_features(rows,cols):
 A=X[rows,:][:,cols].toarray().astype(np.float64); dd=dcode[rows]
 for d in np.unique(dd):
  ix=dd==d; mu=A[ix].mean(0); sd=A[ix].std(0); A[ix]=(A[ix]-mu)/np.where(sd>1e-8,sd,1)
 return A,dd
def ridge_score(ti,trd,vad,univ,tcol,mask,maxf=32,alpha=.01):
 vis=np.array([c for c in univ if c not in mask and c!=tcol],int); sc=train_score(ti,trd,vis); feats=vis[np.lexsort((vis,-sc))[:min(maxf,len(vis))]]
 trrows=np.flatnonzero(np.isin(dcode,trd)); varows=np.flatnonzero(np.isin(dcode,vad)); Atr,dtr=std_features(trrows,feats); Ava,dva=std_features(varows,feats)
 ytr=X[trrows,tcol].toarray().ravel().astype(np.float64); yva=X[varows,tcol].toarray().ravel().astype(np.float64)
 for d in np.unique(dtr): ytr[dtr==d]-=ytr[dtr==d].mean()
 ys=ytr.std();
 if ys<1e-8:return 0.0
 ytr/=ys; G=Atr.T@Atr+alpha*len(trrows)*np.eye(len(feats)); w=np.linalg.solve(G,Atr.T@ytr); pred=Ava@w
 per=[]; psrc=[]
 for d in np.unique(dva):
  ix=dva==d; yy=yva[ix]; pp=pred[ix]
  yy=yy-yy.mean();pp=pp-pp.mean(); den=np.sqrt((yy@yy)*(pp@pp)); r=0.0 if den<1e-12 else float((yy@pp)/den); per.append(r*r); psrc.append(sources[d])
 per=np.array(per);psrc=np.array(psrc); return float(np.mean([per[psrc==s].mean() for s in np.unique(psrc)]))
rows=[]; t0=time.time()
for nu in [800,2000,6000]:
 univ=U[nu]; print('UNIV',nu,flush=True)
 for fi in range(4):
  va=np.flatnonzero(fold==fi);tr=np.flatnonzero(fold!=fi)
  for ti,tcol in enumerate(targets):
   sets={'TOP8':top8(ti,tr,univ,tcol),'PREFIX3':prefix3(ti,tr,univ,tcol)}; base=make_mask(univ,tcol,fi,ti,[]); us=ridge_score(ti,tr,va,univ,tcol,base)
   rows.append(dict(universe=nu,fold=fi,target=ti,method='U',U=us,score=us,delta=0,targeted_n=0))
   for m,tg in sets.items():
    mask=make_mask(univ,tcol,fi,ti,tg); ss=ridge_score(ti,tr,va,univ,tcol,mask); rows.append(dict(universe=nu,fold=fi,target=ti,method=m,U=us,score=ss,delta=us-ss,targeted_n=len(tg)))
  print(' fold',fi,'elapsed',round(time.time()-t0,1),flush=True)
out=pd.DataFrame(rows);out.to_csv(BASE+'/ridge_scale_pairs.csv',index=False)
ss=[]
for (u,m),g in out[out.method!='U'].groupby(['universe','method']):
 gt=g.groupby('target').delta.mean(); act=g[g.targeted_n>0]
 ss.append(dict(universe=u,method=m,n=len(g),targets=g.target.nunique(),action_rows=int((g.targeted_n>0).sum()),mean_delta=g.delta.mean(),median_delta=g.delta.median(),win=(g.delta>0).mean(),target_mean_delta=gt.mean(),target_median_delta=gt.median(),target_win=(gt>0).mean(),acted_mean_delta=act.delta.mean() if len(act) else 0,acted_win=(act.delta>0).mean() if len(act) else 0,U_mean=g.U.mean()))
s=pd.DataFrame(ss);s.to_csv(BASE+'/ridge_scale_summary.csv',index=False);print(s.to_string(index=False),flush=True)
