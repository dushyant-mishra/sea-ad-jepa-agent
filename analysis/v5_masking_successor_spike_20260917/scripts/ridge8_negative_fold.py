import numpy as np,pandas as pd,scipy.sparse as sp,hashlib,sys,time
BASE='/mnt/data/jepa_spike_work';X=sp.load_npz(BASE+'/X_common6000.npz').tocsr();C=np.load(BASE+'/negative_corr_8x6000.npy',mmap_mode='r');univ=np.load(BASE+'/universe_6000_local.npy');targets=np.load(BASE+'/scale_targets_cols.npy')[:8]
meta=pd.read_csv(BASE+'/expression/expression/FOUNDATION_DISCOVERY_SAMPLE_FREEZE.csv',usecols=['source','donor_id']);donor_ids,dcode=np.unique(meta.donor_id.to_numpy(),return_inverse=True);sources=np.array([meta.source.to_numpy()[dcode==d][0] for d in range(len(donor_ids))])
# build deterministic within-donor shuffled target matrix exactly matching negative corr cache
Y=X[:,targets].toarray().astype(float)
for d in range(len(donor_ids)):
 rows=np.flatnonzero(dcode==d)
 for ti in range(len(targets)):
  seed=int.from_bytes(hashlib.sha256(f'NEGSHUF|{d}|{ti}'.encode()).digest()[:8],'big');Y[rows,ti]=np.random.default_rng(seed).permutation(Y[rows,ti])
fold=np.full(len(donor_ids),-1,int)
for s in np.unique(sources):
 ds=np.flatnonzero(sources==s);seed=int.from_bytes(hashlib.sha256(f'JEPA_SCALE_FOLD|{s}'.encode()).digest()[:8],'big');p=np.random.default_rng(seed).permutation(ds)
 for i,d in enumerate(p):fold[d]=i%4
def bal(v,don):return np.mean([np.mean(v[sources[don]==s],axis=0) for s in np.unique(sources[don])],axis=0)
def ts(ti,don,cols):return bal(np.asarray(C[don,ti,:])[:,cols],don)
def std_features(rows,cols):
 A=X[rows,:][:,cols].toarray().astype(float);dd=dcode[rows]
 for d in np.unique(dd):
  ix=dd==d;mu=A[ix].mean(0);sd=A[ix].std(0);A[ix]=(A[ix]-mu)/np.where(sd>1e-8,sd,1)
 return A,dd
def fit_w(ti,trd,feats,alpha=.01):
 rows=np.flatnonzero(np.isin(dcode,trd));A,dd=std_features(rows,feats);y=Y[rows,ti].copy()
 for d in np.unique(dd):y[dd==d]-=y[dd==d].mean()
 ys=y.std();
 if ys<1e-8:return np.zeros(len(feats))
 y/=ys;G=A.T@A+alpha*len(rows)*np.eye(len(feats));return np.linalg.solve(G,A.T@y)
def ridge8(ti,trd,tcol):
 s=ts(ti,trd,univ).copy();s[univ==tcol]=-1;cand=univ[np.lexsort((univ,-s))[:64]];w=fit_w(ti,trd,cand);o=np.lexsort((cand,-np.abs(w)));return list(map(int,cand[o[:8]]))
def mask(tcol,fi,ti,tg):
 burden=900;pool=univ[univ!=tcol];seed=int.from_bytes(hashlib.sha256(f'JEPA_SCALE_MASK|6000|{fi}|{ti}'.encode()).digest()[:8],'big');base=list(map(int,np.random.default_rng(seed).choice(pool,burden-1,False)));M=set(base+[int(tcol)]);add=[a for a in tg if a not in M];rem=sorted([a for a in base if a not in tg],key=lambda a:hashlib.sha256(f'REMOVE|{fi}|{ti}|{a}'.encode()).digest());
 for a,r in zip(add,rem):M.discard(r);M.add(a)
 return M
def score(ti,trd,vad,tcol,M,maxf=32,alpha=.01):
 vis=np.array([c for c in univ if c not in M and c!=tcol],int);s=ts(ti,trd,vis);feats=vis[np.lexsort((vis,-s))[:maxf]];tr=np.flatnonzero(np.isin(dcode,trd));va=np.flatnonzero(np.isin(dcode,vad));Atr,dtr=std_features(tr,feats);Ava,dva=std_features(va,feats);ytr=Y[tr,ti].copy();yva=Y[va,ti].copy()
 for d in np.unique(dtr):ytr[dtr==d]-=ytr[dtr==d].mean()
 ys=ytr.std();
 if ys<1e-8:return 0.
 ytr/=ys;G=Atr.T@Atr+alpha*len(tr)*np.eye(len(feats));w=np.linalg.solve(G,Atr.T@ytr);pr=Ava@w;per=[];ps=[]
 for d in np.unique(dva):
  ix=dva==d;yy=yva[ix]-yva[ix].mean();pp=pr[ix]-pr[ix].mean();den=np.sqrt((yy@yy)*(pp@pp));r=0 if den<1e-12 else (yy@pp)/den;per.append(float(r*r));ps.append(sources[d])
 per=np.array(per);ps=np.array(ps);return float(np.mean([per[ps==s].mean() for s in np.unique(ps)]))
fi=int(sys.argv[1]);va=np.flatnonzero(fold==fi);trd=np.flatnonzero(fold!=fi);rows=[];t0=time.time()
for ti,tcol in enumerate(targets):
 bm=mask(tcol,fi,ti,[]);u=score(ti,trd,va,tcol,bm);tg=ridge8(ti,trd,tcol);s=score(ti,trd,va,tcol,mask(tcol,fi,ti,tg));rows.append(dict(fold=fi,target=ti,U=u,score=s,delta=u-s))
d=pd.DataFrame(rows);d.to_csv(BASE+f'/ridge8_negative_6000_{fi}.csv',index=False);print('fold',fi,'elapsed',round(time.time()-t0,1),'mean',d.delta.mean(),'median',d.delta.median(),'win',(d.delta>0).mean())
