import numpy as np, pandas as pd, scipy.sparse as sp, hashlib, sys, time, os
B='/mnt/data/jepa_spike_work'
X=sp.load_npz(B+'/X_common6000.npz').tocsr()
C=np.load('/mnt/data/outer5200_32_donor_target_abs_corr.npy',mmap_mode='r')
U={6000:np.load(f'{B}/universe_6000_local.npy')}
targets=np.load('/mnt/data/outer5200_targets32_cols.npy')
meta=pd.read_csv(B+'/expression/expression/FOUNDATION_DISCOVERY_SAMPLE_FREEZE.csv',usecols=['source','donor_id'])
donor_ids,dcode=np.unique(meta.donor_id.to_numpy(),return_inverse=True)
sources=np.array([meta.source.to_numpy()[dcode==d][0] for d in range(len(donor_ids))])
fold=np.full(len(donor_ids),-1,int)
for s in np.unique(sources):
    ds=np.flatnonzero(sources==s)
    seed=int.from_bytes(hashlib.sha256(f'JEPA_SCALE_FOLD|{s}'.encode()).digest()[:8],'big')
    p=np.random.default_rng(seed).permutation(ds)
    for i,d in enumerate(p): fold[d]=i%4

def bal(v,don):
    return np.mean([np.mean(v[sources[don]==s],axis=0) for s in np.unique(sources[don])],axis=0)
def ts(ti,don,cols): return bal(np.asarray(C[don,ti,:])[:,cols],don)
def val_corr2(ti,don,col):
    r=np.asarray(C[don,ti,col]); return float(bal((r*r)[:,None],don).ravel()[0])
def std_features(rows,cols):
    A=X[rows,:][:,cols].toarray().astype(np.float64); dd=dcode[rows]
    for d in np.unique(dd):
        ix=dd==d; mu=A[ix].mean(0); sd=A[ix].std(0); A[ix]=(A[ix]-mu)/np.where(sd>1e-8,sd,1)
    return A,dd
def fit_w(ti,trd,tcol,feats,alpha=.01):
    rows=np.flatnonzero(np.isin(dcode,trd)); A,dd=std_features(rows,feats); y=X[rows,tcol].toarray().ravel().astype(np.float64)
    for d in np.unique(dd): y[dd==d]-=y[dd==d].mean()
    ys=y.std()
    if ys<1e-8:return np.zeros(len(feats))
    y/=ys; G=A.T@A+alpha*len(rows)*np.eye(len(feats)); return np.linalg.solve(G,A.T@y)
def ridge8(ti,trd,univ,tcol):
    s=ts(ti,trd,univ).copy(); s[univ==tcol]=-1
    cand=univ[np.lexsort((univ,-s))[:64]]
    w=fit_w(ti,trd,tcol,cand)
    order=np.lexsort((cand,-np.abs(w)))
    return list(map(int,cand[order[:8]]))
def top8(ti,trd,univ,tcol):
    s=ts(ti,trd,univ).copy(); s[univ==tcol]=-1
    return list(map(int,univ[np.lexsort((univ,-s))[:8]]))
def inner3(train_d):
    groups=[[] for _ in range(3)]
    for s in np.unique(sources[train_d]):
        ds=train_d[sources[train_d]==s]
        seed=int.from_bytes(hashlib.sha256(f'JEPA_SCALE_INNER|{s}'.encode()).digest()[:8],'big')
        p=np.random.default_rng(seed).permutation(ds)
        for i,d in enumerate(p): groups[i%3].append(int(d))
    return [np.array(sorted(g),int) for g in groups]
def combine_sets(sets,evidence,cap=8):
    sup={}
    for ss in sets:
        for a in set(map(int,ss)): sup[a]=sup.get(a,0)+1
    if not sup:return []
    items=np.array(list(sup),int); su=np.array([sup[int(a)] for a in items]); ev=evidence[items]
    order=np.lexsort((items,-ev,-su)); return list(map(int,items[order[:cap]]))
def prefix3(ti,tr,univ,tcol,floor=.05,reduction=.50,cap=8,cand_m=20):
    groups=inner3(tr); sets=[]; univ=np.array(univ,int)
    for rot in range(3):
        A,B,Cg=groups[rot],groups[(rot+1)%3],groups[(rot+2)%3]
        sa=ts(ti,A,univ); cand=univ[np.lexsort((univ,-sa))[:min(cand_m,len(univ))]]; cand=cand[cand!=tcol]
        if not len(cand): sets.append([]); continue
        def ev(rem):
            if not len(rem): return 0.0
            sb=ts(ti,B,rem); j=rem[np.lexsort((rem,-sb))[0]]; return val_corr2(ti,Cg,int(j))
        p0=ev(cand)
        if p0<floor: sets.append([]); continue
        chosen=[]
        for k in range(1,min(cap,len(cand))+1):
            rem=np.setdiff1d(cand,cand[:k],assume_unique=False)
            if ev(rem) <= (1-reduction)*p0:
                chosen=list(map(int,cand[:k])); break
        sets.append(chosen)
    evidence=np.zeros(X.shape[1]); evidence[univ]=ts(ti,tr,univ)
    return combine_sets(sets,evidence,cap)
def make_mask(univ,tcol,fi,ti,tg):
    burden=max(2,int(round(.15*len(univ))))
    pool=univ[univ!=tcol]
    seed=int.from_bytes(hashlib.sha256(f'JEPA_SCALE_MASK|{len(univ)}|{fi}|{ti}'.encode()).digest()[:8],'big')
    base=list(map(int,np.random.default_rng(seed).choice(pool,size=burden-1,replace=False)))
    M=set(base+[int(tcol)])
    add=[a for a in tg if a not in M and a!=tcol]
    rem=sorted([a for a in base if a not in tg],key=lambda a:hashlib.sha256(f'REMOVE|{fi}|{ti}|{a}'.encode()).digest())
    for a,r in zip(add,rem): M.discard(r); M.add(a)
    assert len(M)==burden
    return M,len(add)
def ridge_score(ti,trd,vad,univ,tcol,mask,maxf=32,alpha=.01):
    vis=np.array([c for c in univ if c not in mask and c!=tcol],int)
    s=ts(ti,trd,vis); feats=vis[np.lexsort((vis,-s))[:min(maxf,len(vis))]]
    trrows=np.flatnonzero(np.isin(dcode,trd)); varows=np.flatnonzero(np.isin(dcode,vad))
    Atr,dtr=std_features(trrows,feats); Ava,dva=std_features(varows,feats)
    ytr=X[trrows,tcol].toarray().ravel().astype(np.float64); yva=X[varows,tcol].toarray().ravel().astype(np.float64)
    for d in np.unique(dtr): ytr[dtr==d]-=ytr[dtr==d].mean()
    ys=ytr.std()
    if ys<1e-8:return 0.0
    ytr/=ys; G=Atr.T@Atr+alpha*len(trrows)*np.eye(len(feats)); w=np.linalg.solve(G,Atr.T@ytr); pred=Ava@w
    per=[]; ps=[]
    for d in np.unique(dva):
        ix=dva==d; yy=yva[ix]-yva[ix].mean(); pp=pred[ix]-pred[ix].mean(); den=np.sqrt((yy@yy)*(pp@pp)); r=0.0 if den<1e-12 else float((yy@pp)/den); per.append(r*r); ps.append(sources[d])
    per=np.array(per); ps=np.array(ps)
    return float(np.mean([per[ps==s].mean() for s in np.unique(ps)]))

fi=int(sys.argv[1]); va=np.flatnonzero(fold==fi); tr=np.flatnonzero(fold!=fi); rows=[]; t0=time.time()
for nu in [6000]:
    univ=U[nu]
    for ti,tcol in enumerate(targets):
        base, _=make_mask(univ,tcol,fi,ti,[]); us=ridge_score(ti,tr,va,univ,tcol,base)
        methods={'TOP8':top8(ti,tr,univ,tcol),'PREFIX3':prefix3(ti,tr,univ,tcol),'RIDGE8':ridge8(ti,tr,univ,tcol)}
        for name,tg in methods.items():
            mask, effective_n=make_mask(univ,tcol,fi,ti,tg); ss=ridge_score(ti,tr,va,univ,tcol,mask)
            rows.append(dict(universe=nu,fold=fi,target=ti,method=name,U=us,score=ss,delta=us-ss,targeted_n=len(tg),effective_n=effective_n))
        if ti%8==7: print('fold',fi,'univ',nu,'target',ti,'elapsed',round(time.time()-t0,1),flush=True)
out=pd.DataFrame(rows); path=f'/mnt/data/outer5200_32_unified_ridge_fold{fi}.csv'; out.to_csv(path,index=False)
print('SAVED',path,flush=True)
print(out.groupby(['universe','method']).agg(mean=('delta','mean'),median=('delta','median'),win=('delta',lambda x:float((x>0).mean())),actions=('effective_n',lambda x:int((x>0).sum()))).to_string(),flush=True)
