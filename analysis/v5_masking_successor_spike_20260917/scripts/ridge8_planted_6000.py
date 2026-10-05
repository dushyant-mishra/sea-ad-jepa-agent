import numpy as np,pandas as pd,scipy.sparse as sp,hashlib,time
BASE='/mnt/data/jepa_spike_work';X=sp.load_npz(BASE+'/X_common6000.npz').tocsr();univ=np.load(BASE+'/universe_6000_local.npy'); targets=np.load(BASE+'/scale_targets_cols.npy'); tcol=int(targets[0]); src=int(univ[123] if univ[123]!=tcol else univ[124])
meta=pd.read_csv(BASE+'/expression/expression/FOUNDATION_DISCOVERY_SAMPLE_FREEZE.csv',usecols=['source','donor_id']); donor_ids,dcode=np.unique(meta.donor_id.to_numpy(),return_inverse=True);sources=np.array([meta.source.to_numpy()[dcode==d][0] for d in range(len(donor_ids))])
# virtual planted target = real source feature + small Gaussian noise scaled to source sd
basey=X[:,src].toarray().ravel().astype(float); rng=np.random.default_rng(12345); y=basey+0.10*basey.std()*rng.normal(size=len(basey))
# donor correlations to all features
C=np.zeros((len(donor_ids),X.shape[1]),np.float32)
for d in range(len(donor_ids)):
 rows=np.flatnonzero(dcode==d);Xd=X[rows,:].astype(np.float64);yy=y[rows]-y[rows].mean();sy=np.sqrt(yy@yy);num=np.asarray(Xd.T@yy).ravel();sx2=np.asarray(Xd.power(2).sum(axis=0)).ravel()-np.asarray(Xd.sum(axis=0)).ravel()**2/len(rows);den=np.sqrt(np.maximum(sx2,0))*sy;C[d]=np.abs(np.divide(num,den,out=np.zeros_like(num),where=den>1e-12)).astype(np.float32)
fold=np.full(len(donor_ids),-1,int)
for s in np.unique(sources):
 ds=np.flatnonzero(sources==s);seed=int.from_bytes(hashlib.sha256(f'JEPA_SCALE_FOLD|{s}'.encode()).digest()[:8],'big');p=np.random.default_rng(seed).permutation(ds)
 for i,d in enumerate(p):fold[d]=i%4
def bal(v,don):return np.mean([np.mean(v[sources[don]==s],axis=0) for s in np.unique(sources[don])],axis=0)
def ts(don,cols):return bal(C[don][:,cols],don)
def stdf(rows,cols):
 A=X[rows,:][:,cols].toarray().astype(float);dd=dcode[rows]
 for d in np.unique(dd):
  ix=dd==d;mu=A[ix].mean(0);sd=A[ix].std(0);A[ix]=(A[ix]-mu)/np.where(sd>1e-8,sd,1)
 return A,dd
def fitw(trd,feats):
 rows=np.flatnonzero(np.isin(dcode,trd));A,dd=stdf(rows,feats);yy=y[rows].copy()
 for d in np.unique(dd):yy[dd==d]-=yy[dd==d].mean()
 yy/=max(yy.std(),1e-8);G=A.T@A+.01*len(rows)*np.eye(len(feats));return np.linalg.solve(G,A.T@yy)
def select(trd):
 s=ts(trd,univ).copy();s[univ==tcol]=-1;cand=univ[np.lexsort((univ,-s))[:64]];w=fitw(trd,cand);o=np.lexsort((cand,-np.abs(w)));return list(map(int,cand[o[:8]]))
def mask(fi,tg):
 burden=900;pool=univ[univ!=tcol];seed=int.from_bytes(hashlib.sha256(f'JEPA_SCALE_MASK|6000|{fi}|0'.encode()).digest()[:8],'big');base=list(map(int,np.random.default_rng(seed).choice(pool,burden-1,False)));M=set(base+[tcol]);add=[a for a in tg if a not in M];rem=sorted([a for a in base if a not in tg],key=lambda a:hashlib.sha256(f'REMOVE|{fi}|0|{a}'.encode()).digest());
 for a,r in zip(add,rem):M.discard(r);M.add(a)
 return M
def score(trd,vad,M):
 vis=np.array([c for c in univ if c not in M and c!=tcol]);s=ts(trd,vis);feats=vis[np.lexsort((vis,-s))[:32]];tr=np.flatnonzero(np.isin(dcode,trd));va=np.flatnonzero(np.isin(dcode,vad));Atr,dtr=stdf(tr,feats);Ava,dva=stdf(va,feats);yy=y[tr].copy()
 for d in np.unique(dtr):yy[dtr==d]-=yy[dtr==d].mean()
 yy/=max(yy.std(),1e-8);G=Atr.T@Atr+.01*len(tr)*np.eye(len(feats));w=np.linalg.solve(G,Atr.T@yy);pr=Ava@w;per=[];ps=[]
 for d in np.unique(dva):
  ix=dva==d;yt=y[va][ix];yt=yt-yt.mean();pp=pr[ix]-pr[ix].mean();den=np.sqrt((yt@yt)*(pp@pp));r=0 if den<1e-12 else (yt@pp)/den;per.append(float(r*r));ps.append(sources[d])
 per=np.array(per);ps=np.array(ps);return float(np.mean([per[ps==s].mean() for s in np.unique(ps)]))
rows=[]
for fi in range(4):
 va=np.flatnonzero(fold==fi);tr=np.flatnonzero(fold!=fi);tg=select(tr);u=score(tr,va,mask(fi,[]));v=score(tr,va,mask(fi,tg));rows.append(dict(fold=fi,U=u,RIDGE8=v,delta=u-v,source_in_set=int(src in tg),source_rank=tg.index(src)+1 if src in tg else 0))
d=pd.DataFrame(rows);d.to_csv(BASE+'/ridge8_planted_6000.csv',index=False);print('target',tcol,'source',src);print(d.to_string(index=False));print('mean drop',d.delta.mean(),'source in',d.source_in_set.sum(),'/4')
