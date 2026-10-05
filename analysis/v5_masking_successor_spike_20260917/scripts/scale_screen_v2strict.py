import numpy as np, pandas as pd, scipy.sparse as sp, hashlib, json, time, os
BASE='/mnt/data/jepa_spike_work'
X=sp.load_npz(BASE+'/X_common6000.npz').tocsr()
meta=pd.read_csv(BASE+'/expression/expression/FOUNDATION_DISCOVERY_SAMPLE_FREEZE.csv',usecols=['source','donor_id'])
donor_ids, dcode=np.unique(meta.donor_id.to_numpy(),return_inverse=True)
sources=np.array([meta.source.to_numpy()[dcode==d][0] for d in range(len(donor_ids))])
U={n:np.load(f'{BASE}/universe_{n}_local.npy') for n in [800,2000,6000]}
addr=np.load(BASE+'/selected6000_sorted.npy')
Xu=X[:,U[800]]; n=X.shape[0]
mean=np.asarray(Xu.mean(axis=0)).ravel(); mean2=np.asarray(Xu.power(2).mean(axis=0)).ravel(); var=mean2-mean**2
nnz=np.diff(Xu.tocsc().indptr)/n
pool=np.flatnonzero(nnz>=0.15); cutoff=np.quantile(var[pool],0.5); eligible=np.flatnonzero((nnz>=0.15)&(var>=cutoff))
def h(x): return hashlib.sha256(f'JEPA_SCALE_TARGET|{int(x)}'.encode()).digest()
eligible=sorted(eligible,key=lambda j:h(addr[U[800][j]]))
target_u800=np.array(eligible[:32],dtype=int); target_cols=U[800][target_u800]; target_addr=addr[target_cols]
np.save(BASE+'/scale_targets_cols.npy',target_cols); np.save(BASE+'/scale_targets_addr.npy',target_addr)
print('targets',len(target_cols),'nnz',float(nnz[target_u800].min()),float(nnz[target_u800].max()),flush=True)
fold=np.full(len(donor_ids),-1,int)
for s in np.unique(sources):
    ds=np.flatnonzero(sources==s); seed=int.from_bytes(hashlib.sha256(f'JEPA_SCALE_FOLD|{s}'.encode()).digest()[:8],'big'); perm=np.random.default_rng(seed).permutation(ds)
    for i,d in enumerate(perm): fold[d]=i%4
cache_path=BASE+'/donor_target_abs_corr.npy'
if os.path.exists(cache_path): C=np.load(cache_path,mmap_mode='r'); print('cache exists',C.shape,flush=True)
else:
    C=np.lib.format.open_memmap(cache_path,mode='w+',dtype=np.float32,shape=(len(donor_ids),len(target_cols),X.shape[1]))
    for d in range(len(donor_ids)):
        rows=np.flatnonzero(dcode==d); Xd=X[rows].astype(np.float64); Y=Xd[:,target_cols].toarray(); Y-=Y.mean(axis=0,keepdims=True); sy=np.sqrt((Y*Y).sum(axis=0))
        num=np.asarray(Xd.T@Y); sx2=np.asarray(Xd.power(2).sum(axis=0)).ravel()-np.asarray(Xd.sum(axis=0)).ravel()**2/max(len(rows),1)
        den=np.sqrt(np.maximum(sx2,0))[:,None]*sy[None,:]; R=np.divide(num,den,out=np.zeros_like(num),where=den>1e-12); C[d]=np.abs(R.T).astype(np.float32)
        if d%10==0: print('corr donor',d,'rows',len(rows),flush=True)
    C.flush()
def bal_mean(vals, donors):
    outs=[]
    for s in np.unique(sources[donors]):
        ix=np.flatnonzero(sources[donors]==s); outs.append(np.mean(vals[ix],axis=0))
    return np.mean(outs,axis=0)
def train_score(ti, donors, cols): return bal_mean(np.asarray(C[donors,ti,:])[:,cols],donors)
def val_score_single(ti, donors, col):
    r=np.asarray(C[donors,ti,col]); return float(bal_mean((r*r)[:,None],donors).ravel()[0])
def inner3(train_d):
    groups=[[] for _ in range(3)]
    for s in np.unique(sources[train_d]):
        ds=train_d[sources[train_d]==s]; seed=int.from_bytes(hashlib.sha256(f'JEPA_SCALE_INNER|{s}'.encode()).digest()[:8],'big'); perm=np.random.default_rng(seed).permutation(ds)
        for i,d in enumerate(perm): groups[i%3].append(int(d))
    return [np.array(sorted(g),int) for g in groups]
def combine_sets(sets, evidence, cap=8):
    sup={}
    for ss in sets:
        for a in set(map(int,ss)): sup[a]=sup.get(a,0)+1
    if not sup: return []
    items=np.array(list(sup),int); su=np.array([sup[int(a)] for a in items]); ev=evidence[items]; order=np.lexsort((items,-ev,-su)); return list(items[order[:cap]])
def prefix3(ti, train_d, universe_cols, target_col, floor=.05, reduction=.50, cap=8, cand_m=20):
    groups=inner3(train_d); sets=[]; universe_cols=np.array(universe_cols,int)
    for rot in range(3):
        A,B,Cg=groups[rot],groups[(rot+1)%3],groups[(rot+2)%3]; sa=train_score(ti,A,universe_cols); order=np.lexsort((universe_cols,-sa)); cand=universe_cols[order[:min(cand_m,len(order))]]; cand=cand[cand!=target_col]
        if not len(cand): sets.append([]); continue
        def eval_remaining(rem):
            if not len(rem): return 0.0
            scb=train_score(ti,B,rem); j=rem[np.lexsort((rem,-scb))[0]]; return val_score_single(ti,Cg,int(j))
        p0=eval_remaining(cand)
        if p0<floor: sets.append([]); continue
        chosen=[]
        for k in range(1,min(cap,len(cand))+1):
            rem=np.setdiff1d(cand,cand[:k],assume_unique=False); p=eval_remaining(rem)
            if p <= (1-reduction)*p0: chosen=list(map(int,cand[:k])); break
        if not chosen: chosen=[]
        sets.append(chosen)
    ev=np.zeros(X.shape[1],float); ev[universe_cols]=train_score(ti,train_d,universe_cols); return combine_sets(sets,ev,cap)
def stable8(ti,train_d,universe_cols,target_col,thr=.10,cap=8):
    cols=np.array(universe_cols,int); allsc=train_score(ti,train_d,cols); by=[]
    for s in np.unique(sources[train_d]):
        ds=train_d[sources[train_d]==s]; by.append(np.mean(np.asarray(C[ds,ti,:])[:,cols],axis=0))
    mins=np.min(np.vstack(by),axis=0); ok=(mins>=thr)&(cols!=target_col); cand=cols[ok]
    if not len(cand): return []
    m=mins[ok]; a=allsc[ok]; order=np.lexsort((cand,-a,-m)); return list(map(int,cand[order[:cap]]))
def top8(ti,train_d,universe_cols,target_col,cap=8):
    cols=np.array(universe_cols,int); sc=train_score(ti,train_d,cols).copy(); sc[cols==target_col]=-1; order=np.lexsort((cols,-sc)); return list(map(int,cols[order[:cap]]))
def make_mask(universe_cols,target_col,foldi,ti,burden_frac,targeted):
    cols=np.array(universe_cols,int); burden=max(2,int(round(burden_frac*len(cols)))); pool=cols[cols!=target_col]; seed=int.from_bytes(hashlib.sha256(f'JEPA_SCALE_MASK|{len(cols)}|{foldi}|{ti}'.encode()).digest()[:8],'big'); rng=np.random.default_rng(seed); base=list(map(int,rng.choice(pool,size=burden-1,replace=False))); mask=set(base+[int(target_col)])
    add=[int(a) for a in targeted if a!=target_col and a not in mask]
    if add:
        removable=[a for a in base if a not in targeted]; removable=sorted(removable,key=lambda a:hashlib.sha256(f'REMOVE|{foldi}|{ti}|{a}'.encode()).digest())
        for a,r in zip(add,removable): mask.discard(r); mask.add(a)
    assert len(mask)==burden; return mask
def attack_score(ti,train_d,val_d,universe_cols,target_col,mask):
    visible=np.array([c for c in universe_cols if c not in mask and c!=target_col],int)
    if not len(visible): return 0.0
    st=train_score(ti,train_d,visible); best=visible[np.lexsort((visible,-st))[0]]; return val_score_single(ti,val_d,int(best))
rows=[]
for nuni in [800,2000,6000]:
    univ=U[nuni]; uset=set(map(int,univ)); print('UNIVERSE',nuni,flush=True)
    for fi in range(4):
        val=np.flatnonzero(fold==fi); tr=np.flatnonzero(fold!=fi)
        for ti,tcol in enumerate(target_cols):
            assert int(tcol) in uset
            methods={'U':[], 'TOP8':top8(ti,tr,univ,tcol,8), 'PREFIX3':prefix3(ti,tr,univ,tcol), 'STABLE05':stable8(ti,tr,univ,tcol,.05), 'STABLE10':stable8(ti,tr,univ,tcol,.10), 'STABLE15':stable8(ti,tr,univ,tcol,.15)}
            base=make_mask(univ,tcol,fi,ti,.15,[]); Uscore=attack_score(ti,tr,val,univ,tcol,base)
            for m,tg in methods.items():
                mask=base if m=='U' else make_mask(univ,tcol,fi,ti,.15,tg); score=Uscore if m=='U' else attack_score(ti,tr,val,univ,tcol,mask); rows.append(dict(universe=nuni,fold=fi,target=ti,address=int(addr[tcol]),method=m,score=score,U=Uscore,delta=Uscore-score,targeted_n=len(tg)))
        print(' fold',fi,'done',flush=True)
out=pd.DataFrame(rows); out.to_csv(BASE+'/scale_screen_v2strict_pairs.csv',index=False)
summary=[]
for (u,m),g in out[out.method!='U'].groupby(['universe','method']):
    gt=g.groupby('target').agg(delta=('delta','mean'),U=('U','mean'),acted=('targeted_n',lambda x:int(np.any(np.array(x)>0))))
    acted=g[g.targeted_n>0]
    summary.append(dict(universe=u,method=m,n=len(g),targets=g.target.nunique(),action_rows=int((g.targeted_n>0).sum()),action_targets=int(gt.acted.sum()),mean_delta=g.delta.mean(),median_delta=g.delta.median(),win=(g.delta>0).mean(),target_mean_delta=gt.delta.mean(),target_median_delta=gt.delta.median(),target_win=(gt.delta>0).mean(),acted_mean_delta=acted.delta.mean() if len(acted) else 0,acted_win=(acted.delta>0).mean() if len(acted) else 0))
s=pd.DataFrame(summary); s.to_csv(BASE+'/scale_screen_v2strict_summary.csv',index=False); print(s.to_string(index=False),flush=True)
