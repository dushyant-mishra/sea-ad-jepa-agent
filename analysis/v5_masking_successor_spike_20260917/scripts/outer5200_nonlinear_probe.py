import numpy as np,pandas as pd,scipy.sparse as sp,hashlib,time,sys
from sklearn.ensemble import HistGradientBoostingRegressor
BASE='/mnt/data/jepa_spike_work'
X=sp.load_npz(BASE+'/X_common6000.npz').tocsr(); C=np.load('/mnt/data/outer5200_32_donor_target_abs_corr.npy',mmap_mode='r')
univ=np.load(BASE+'/universe_6000_local.npy'); targets=np.load('/mnt/data/outer5200_targets32_cols.npy')[:8]
meta=pd.read_csv(BASE+'/expression/expression/FOUNDATION_DISCOVERY_SAMPLE_FREEZE.csv',usecols=['source','donor_id'])
donor_ids,dcode=np.unique(meta.donor_id.to_numpy(),return_inverse=True); sources=np.array([meta.source.to_numpy()[dcode==d][0] for d in range(len(donor_ids))])
fold=np.full(len(donor_ids),-1,int)
for s in np.unique(sources):
 ds=np.flatnonzero(sources==s); seed=int.from_bytes(hashlib.sha256(f'JEPA_SCALE_FOLD|{s}'.encode()).digest()[:8],'big'); p=np.random.default_rng(seed).permutation(ds)
 for i,d in enumerate(p): fold[d]=i%4

def bal(v,don): return np.mean([np.mean(v[sources[don]==s],axis=0) for s in np.unique(sources[don])],axis=0)
def ts(ti,don,cols): return bal(np.asarray(C[don,ti,:])[:,cols],don)
def std_features(rows,cols):
 A=X[rows,:][:,cols].toarray().astype(np.float32); dd=dcode[rows]
 for d in np.unique(dd):
  ix=dd==d; mu=A[ix].mean(0); sd=A[ix].std(0); A[ix]=(A[ix]-mu)/np.where(sd>1e-8,sd,1)
 return A,dd

def fit_w(ti,trd,tcol,feats,alpha=.01):
 rows=np.flatnonzero(np.isin(dcode,trd)); A,dd=std_features(rows,feats); y=X[rows,tcol].toarray().ravel().astype(float)
 for d in np.unique(dd): y[dd==d]-=y[dd==d].mean()
 ys=y.std();
 if ys<1e-8:return np.zeros(len(feats))
 y/=ys; G=A.T@A+alpha*len(rows)*np.eye(len(feats)); return np.linalg.solve(G,A.T@y)

def ridge8(ti,trd,tcol):
 s=ts(ti,trd,univ).copy(); s[univ==tcol]=-1; cand=univ[np.lexsort((univ,-s))[:64]]; w=fit_w(ti,trd,tcol,cand); order=np.lexsort((cand,-np.abs(w))); return list(map(int,cand[order[:8]]))
def top8(ti,trd,tcol):
 s=ts(ti,trd,univ).copy(); s[univ==tcol]=-1; return list(map(int,univ[np.lexsort((univ,-s))[:8]]))
def make_mask(tcol,fi,ti,tg):
 burden=int(round(.15*len(univ))); pool=univ[univ!=tcol]; seed=int.from_bytes(hashlib.sha256(f'JEPA_SCALE_MASK|{len(univ)}|{fi}|{ti}'.encode()).digest()[:8],'big'); base=list(map(int,np.random.default_rng(seed).choice(pool,burden-1,False))); M=set(base+[int(tcol)]); add=[a for a in tg if a not in M]; rem=sorted([a for a in base if a not in tg],key=lambda a:hashlib.sha256(f'REMOVE|{fi}|{ti}|{a}'.encode()).digest())
 for a,r in zip(add,rem): M.discard(r); M.add(a)
 return M

def nonlinear_score(ti,trd,vad,tcol,mask,maxf=32):
 vis=np.array([c for c in univ if c not in mask and c!=tcol],int); s=ts(ti,trd,vis); feats=vis[np.lexsort((vis,-s))[:maxf]]
 trrows=np.flatnonzero(np.isin(dcode,trd)); varows=np.flatnonzero(np.isin(dcode,vad)); Atr,dtr=std_features(trrows,feats); Ava,dva=std_features(varows,feats)
 ytr=X[trrows,tcol].toarray().ravel().astype(float); yva=X[varows,tcol].toarray().ravel().astype(float)
 for d in np.unique(dtr): ytr[dtr==d]-=ytr[dtr==d].mean()
 ys=ytr.std();
 if ys<1e-8:return 0.
 ytr/=ys
 model=HistGradientBoostingRegressor(loss='squared_error',learning_rate=.08,max_iter=80,max_leaf_nodes=15,min_samples_leaf=80,l2_regularization=1.0,random_state=20260917,early_stopping=False)
 model.fit(Atr,ytr); pr=model.predict(Ava); per=[]; ps=[]
 for d in np.unique(dva):
  ix=dva==d; yy=yva[ix]-yva[ix].mean(); pp=pr[ix]-pr[ix].mean(); den=np.sqrt((yy@yy)*(pp@pp)); r=0 if den<1e-12 else (yy@pp)/den; per.append(float(r*r)); ps.append(sources[d])
 per=np.array(per);ps=np.array(ps);return float(np.mean([per[ps==s].mean() for s in np.unique(ps)]))

fi=int(sys.argv[1]); n_targets=int(sys.argv[2]) if len(sys.argv)>2 else 8
va=np.flatnonzero(fold==fi); tr=np.flatnonzero(fold!=fi); rows=[]; t0=time.time()
for ti,tcol in enumerate(targets[:n_targets]):
 masks={'U':make_mask(tcol,fi,ti,[]),'TOP8':make_mask(tcol,fi,ti,top8(ti,tr,tcol)),'RIDGE8':make_mask(tcol,fi,ti,ridge8(ti,tr,tcol))}
 scores={m:nonlinear_score(ti,tr,va,tcol,mask) for m,mask in masks.items()}
 for m in ['TOP8','RIDGE8']:
  rows.append(dict(fold=fi,target=ti,method=m,U=scores['U'],score=scores[m],delta=scores['U']-scores[m]))
 print('target',ti,'scores',scores,'elapsed',round(time.time()-t0,1),flush=True)
out=pd.DataFrame(rows); out.to_csv(f'/mnt/data/outer5200_nonlinear_fold{fi}.csv',index=False)
print(out.groupby('method').agg(mean=('delta','mean'),median=('delta','median'),win=('delta',lambda x:float((x>0).mean()))).to_string())
