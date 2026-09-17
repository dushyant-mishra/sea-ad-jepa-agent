import numpy as np,pandas as pd,hashlib
BASE='/mnt/data/jepa_spike_work'; C=np.load(BASE+'/donor_target_abs_corr.npy',mmap_mode='r'); U={n:np.load(f'{BASE}/universe_{n}_local.npy') for n in [800,2000,6000]}; targets=np.load(BASE+'/scale_targets_cols.npy'); addr=np.load(BASE+'/selected6000_sorted.npy')
meta=pd.read_csv(BASE+'/expression/expression/FOUNDATION_DISCOVERY_SAMPLE_FREEZE.csv',usecols=['source','donor_id']); donor_ids,dcode=np.unique(meta.donor_id.to_numpy(),return_inverse=True);sources=np.array([meta.source.to_numpy()[dcode==d][0] for d in range(len(donor_ids))])
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
def top8(ti,don,univ,tcol):
 s=ts(ti,don,univ).copy();s[univ==tcol]=-1;return list(map(int,univ[np.lexsort((univ,-s))[:8]]))
def attack(ti,train,val,univ,tcol,masked):
 vis=np.array([c for c in univ if c not in masked and c!=tcol],int);s=ts(ti,train,vis);j=vis[np.lexsort((vis,-s))[0]];return vs(ti,val,int(j))
def gate(ti,tr,univ,tcol,thr=0.0):
 gs=inner3(tr);drops=[]
 for rot in range(3):
  A,B,Cg=gs[rot],gs[(rot+1)%3],gs[(rot+2)%3];tg=set(top8(ti,A,univ,tcol));before=attack(ti,B,Cg,univ,tcol,set([tcol]));after=attack(ti,B,Cg,univ,tcol,tg|{int(tcol)});drops.append(before-after)
 ok=(np.mean(drops)>=thr) and (np.sum(np.array(drops)>0)>=2)
 return ok,drops
def base_mask(univ,tcol,fi,ti,tg):
 burden=int(round(.15*len(univ)));pool=univ[univ!=tcol];seed=int.from_bytes(hashlib.sha256(f'JEPA_SCALE_MASK|{len(univ)}|{fi}|{ti}'.encode()).digest()[:8],'big');base=list(map(int,np.random.default_rng(seed).choice(pool,burden-1,False)));M=set(base+[int(tcol)]);add=[a for a in tg if a not in M];rem=sorted([a for a in base if a not in tg],key=lambda a:hashlib.sha256(f'REMOVE|{fi}|{ti}|{a}'.encode()).digest());
 for a,r in zip(add,rem):M.discard(r);M.add(a)
 return M
rows=[]
for nu in [800,2000,6000]:
 univ=U[nu]
 for fi in range(4):
  va=np.flatnonzero(fold==fi);tr=np.flatnonzero(fold!=fi)
  for ti,tcol in enumerate(targets):
   bm=base_mask(univ,tcol,fi,ti,[]);u=attack(ti,tr,va,univ,tcol,bm); full=top8(ti,tr,univ,tcol)
   for name,thr in [('GATE015',0.015),('GATE020',0.020),('GATE030',0.030),('GATE040',0.040)]:
    ok,drops=gate(ti,tr,univ,tcol,thr);tg=full if ok else [];m=base_mask(univ,tcol,fi,ti,tg);sc=attack(ti,tr,va,univ,tcol,m);rows.append(dict(universe=nu,fold=fi,target=ti,method=name,threshold=thr,score=sc,U=u,delta=u-sc,targeted_n=len(tg),inner_mean=float(np.mean(drops)),inner_pos=int(np.sum(np.array(drops)>0))))
d=pd.DataFrame(rows);d.to_csv(BASE+'/gated_top8_high_pairs.csv',index=False)
for (u,m),g in d.groupby(['universe','method']):
 gt=g.groupby('target').delta.mean();act=g[g.targeted_n>0]
 print(u,m,'actions',int((g.targeted_n>0).sum()),'targets',int(g[g.targeted_n>0].target.nunique()),'mean',round(g.delta.mean(),6),'acted',round(act.delta.mean(),6) if len(act) else 0,'actedwin',round((act.delta>0).mean(),3) if len(act) else 0,'tgtwin',round((gt>0).mean(),3))
