import numpy as np,pandas as pd,scipy.sparse as sp,hashlib,sys,time
BASE='/mnt/data/jepa_spike_work'; X=sp.load_npz(BASE+'/X_common6000.npz').tocsr(); C=np.load(BASE+'/donor_target_abs_corr.npy',mmap_mode='r'); univ=np.load(BASE+'/universe_6000_local.npy'); targets=np.load(BASE+'/scale_targets_cols.npy')[:8]
meta=pd.read_csv(BASE+'/expression/expression/FOUNDATION_DISCOVERY_SAMPLE_FREEZE.csv',usecols=['source','donor_id']); donor_ids,dcode=np.unique(meta.donor_id.to_numpy(),return_inverse=True); sources=np.array([meta.source.to_numpy()[dcode==d][0] for d in range(len(donor_ids))])
fold=np.full(len(donor_ids),-1,int)
for s in np.unique(sources):
 ds=np.flatnonzero(sources==s);seed=int.from_bytes(hashlib.sha256(f'JEPA_SCALE_FOLD|{s}'.encode()).digest()[:8],'big');p=np.random.default_rng(seed).permutation(ds)
 for i,d in enumerate(p):fold[d]=i%4
def bal(v,don):return np.mean([np.mean(v[sources[don]==s],axis=0) for s in np.unique(sources[don])],axis=0)
def ts(ti,don,cols):return bal(np.asarray(C[don,ti,:])[:,cols],don)
def vs(ti,don,col):r=np.asarray(C[don,ti,col]);return float(bal((r*r)[:,None],don).ravel()[0])
def inner3(tr):
 g=[[] for _ in range(3)]
 for s in np.unique(sources[tr]):
  ds=tr[sources[tr]==s];seed=int.from_bytes(hashlib.sha256(f'JEPA_SCALE_INNER|{s}'.encode()).digest()[:8],'big');p=np.random.default_rng(seed).permutation(ds)
  for i,d in enumerate(p):g[i%3].append(int(d))
 return [np.array(x,int) for x in g]
def top8(ti,don,tcol):
 s=ts(ti,don,univ).copy();s[univ==tcol]=-1;return list(map(int,univ[np.lexsort((univ,-s))[:8]]))
def cheap_attack(ti,train,val,tcol,masked):
 vis=np.array([c for c in univ if c not in masked and c!=tcol],int);s=ts(ti,train,vis);j=vis[np.lexsort((vis,-s))[0]];return vs(ti,val,int(j))
def gate(ti,tr,tcol,thr):
 gs=inner3(tr);drops=[]
 for rot in range(3):
  A,B,Cg=gs[rot],gs[(rot+1)%3],gs[(rot+2)%3];tg=set(top8(ti,A,tcol));before=cheap_attack(ti,B,Cg,tcol,{int(tcol)});after=cheap_attack(ti,B,Cg,tcol,tg|{int(tcol)});drops.append(before-after)
 return (np.mean(drops)>=thr and np.sum(np.array(drops)>0)>=2),drops
def make_mask(tcol,fi,ti,tg):
 burden=900;pool=univ[univ!=tcol];seed=int.from_bytes(hashlib.sha256(f'JEPA_SCALE_MASK|6000|{fi}|{ti}'.encode()).digest()[:8],'big');base=list(map(int,np.random.default_rng(seed).choice(pool,burden-1,False)));M=set(base+[int(tcol)]);add=[a for a in tg if a not in M];rem=sorted([a for a in base if a not in tg],key=lambda a:hashlib.sha256(f'REMOVE|{fi}|{ti}|{a}'.encode()).digest());
 for a,r in zip(add,rem):M.discard(r);M.add(a)
 return M
def std_features(rows,cols):
 A=X[rows,:][:,cols].toarray().astype(np.float64);dd=dcode[rows]
 for d in np.unique(dd):
  ix=dd==d;mu=A[ix].mean(0);sd=A[ix].std(0);A[ix]=(A[ix]-mu)/np.where(sd>1e-8,sd,1)
 return A,dd
def ridge_score(ti,trd,vad,tcol,mask,maxf=32,alpha=.01):
 vis=np.array([c for c in univ if c not in mask and c!=tcol],int);sc=ts(ti,trd,vis);feats=vis[np.lexsort((vis,-sc))[:maxf]];trrows=np.flatnonzero(np.isin(dcode,trd));varows=np.flatnonzero(np.isin(dcode,vad));Atr,dtr=std_features(trrows,feats);Ava,dva=std_features(varows,feats);ytr=X[trrows,tcol].toarray().ravel().astype(float);yva=X[varows,tcol].toarray().ravel().astype(float)
 for d in np.unique(dtr):ytr[dtr==d]-=ytr[dtr==d].mean()
 ys=ytr.std();
 if ys<1e-8:return 0.
 ytr/=ys;G=Atr.T@Atr+alpha*len(trrows)*np.eye(len(feats));w=np.linalg.solve(G,Atr.T@ytr);pr=Ava@w;per=[];ps=[]
 for d in np.unique(dva):
  ix=dva==d;yy=yva[ix]-yva[ix].mean();pp=pr[ix]-pr[ix].mean();den=np.sqrt((yy@yy)*(pp@pp));r=0 if den<1e-12 else (yy@pp)/den;per.append(float(r*r));ps.append(sources[d])
 per=np.array(per);ps=np.array(ps);return float(np.mean([per[ps==s].mean() for s in np.unique(ps)]))
fi=int(sys.argv[1]);va=np.flatnonzero(fold==fi);tr=np.flatnonzero(fold!=fi);rows=[];t0=time.time()
for ti,tcol in enumerate(targets):
 base=make_mask(tcol,fi,ti,[]);u=ridge_score(ti,tr,va,tcol,base);full=top8(ti,tr,tcol)
 for name,thr in [('GATE020',.02),('GATE030',.03)]:
  ok,drops=gate(ti,tr,tcol,thr);tg=full if ok else [];sc=u if not tg else ridge_score(ti,tr,va,tcol,make_mask(tcol,fi,ti,tg));rows.append(dict(fold=fi,target=ti,method=name,U=u,score=sc,delta=u-sc,targeted_n=len(tg),inner_mean=np.mean(drops)))
print('fold',fi,'elapsed',round(time.time()-t0,1));d=pd.DataFrame(rows);d.to_csv(BASE+f'/ridge_gated_6000_{fi}.csv',index=False);print(d.groupby('method').agg(actions=('targeted_n',lambda x:int((x>0).sum())),mean=('delta','mean'),median=('delta','median'),win=('delta',lambda x:float((x>0).mean()))).to_string())
