import numpy as np, pandas as pd, json, pathlib
from scipy.stats import spearmanr
S=pathlib.Path(r'C:/Users/dushy/AppData/Local/Temp/claude/d--Jepa-project/cdf819f6-5db4-4119-9a97-37fef1d27909/scratchpad')
PS=[100,90,75,50,25]
z=np.load(S/'screen_out.npz',allow_pickle=True)
fm=pd.read_csv(S/'final_manifest.csv',usecols=['donor_id','operator_index','source','stratum'])
pp=pd.read_csv(S/'pair_plan.csv')
lib0=z['lib_p100']
bands=np.array(['<100','100-1k','1k-5k','5k-20k','20k-50k','>=50k'])
bi=np.digitize(lib0,[100,1000,5000,20000,50000])
print('=== ZERO-LIBRARY (non-estimable) ACCOUNTING over all %d attempted cells ==='%len(lib0))
for p in PS: print('  p=%.2f  library<=0: %d  (%.5f%%)'%(p/100,int((z['lib_p%d'%p]<=0).sum()),100*(z['lib_p%d'%p]<=0).mean()))
print()
print('=== NESTING OF LIBRARY TOTALS (frozen outputs, ascending p) ===')
v=0
for a,b in zip(PS[1:],PS[:-1]):
    bad=int((z['lib_p%d'%a]>z['lib_p%d'%b]).sum()); v+=bad
    print('  lib_p%-3d <= lib_p%-3d violations: %d'%(a,b,bad))
print('  total violations: %d'%v)

a_i=pp.a.to_numpy(); b_i=pp.b.to_numpy(); strat=pp.stratum.to_numpy()
out={'zero_library':{str(p/100):int((z['lib_p%d'%p]<=0).sum()) for p in PS},
     'lib_nesting_violations':int(v),'pairs_planned':int(len(pp))}
geo={}
for view in (0,1):
    X0=z['p100_v%d'%view]
    n0=np.linalg.norm(X0,axis=1)
    dE0=np.linalg.norm(X0[a_i]-X0[b_i],axis=1)
    den0=n0[a_i]*n0[b_i]
    dC0=1.0-np.einsum('ij,ij->i',X0[a_i],X0[b_i])/np.where(den0>0,den0,np.nan)
    est0=~(np.isnan(X0[a_i,0])|np.isnan(X0[b_i,0]))
    for p in PS:
        if p==100: continue
        X=z['p%d_v%d'%(p,view)]
        n=np.linalg.norm(X,axis=1)
        dE=np.linalg.norm(X[a_i]-X[b_i],axis=1)
        den=n[a_i]*n[b_i]
        dC=1.0-np.einsum('ij,ij->i',X[a_i],X[b_i])/np.where(den>0,den,np.nan)
        est=~(np.isnan(X[a_i,0])|np.isnan(X[b_i,0]))
        ok=est0&est&np.isfinite(dC0)&np.isfinite(dC)
        rec={}
        for nm,mask in (('ALL',np.ones(len(pp),bool)),('BASE_MECHANICS',strat=='BASE_MECHANICS'),
                        ('STRESS',strat!='BASE_MECHANICS')):
            m=mask&ok; mE=mask&est0&est
            rec[nm]=dict(pairs_planned=int(mask.sum()),
                pairs_estimable=int(mE.sum()),
                pairs_not_estimable_after_intervention=int((mask&est0&~est).sum()),
                spearman_euclidean=float(spearmanr(dE0[mE],dE[mE]).statistic) if mE.sum()>2 else None,
                spearman_cosine=float(spearmanr(dC0[m],dC[m]).statistic) if m.sum()>2 else None,
                zero_dist_baseline=int((dE0[mE]==0).sum()),
                zero_dist_created=int(((dE0[mE]>0)&(dE[mE]==0)).sum()),
                zero_dist_released=int(((dE0[mE]==0)&(dE[mE]>0)).sum()))
        geo['V%d|p%.2f'%(view,p/100)]=rec
    # displacement of the cell itself vs p=1, by source and depth band
    for p in PS:
        if p==100: continue
        X=z['p%d_v%d'%(p,view)]
        good=~(np.isnan(X0[:,0])|np.isnan(X[:,0]))
        dsp=np.full(len(X0),np.nan); nn=np.full(len(X0),np.nan)
        dsp[good]=np.linalg.norm(X[good]-X0[good],axis=1)
        d0=np.linalg.norm(X0[good],axis=1); d1=np.linalg.norm(X[good],axis=1)
        cs=np.full(len(X0),np.nan)
        den=d0*d1
        cs[good]=1.0-np.einsum('ij,ij->i',X0[good],X[good])/np.where(den>0,den,np.nan)
        rel=np.full(len(X0),np.nan); rel[good]=dsp[good]/np.maximum(d0,1e-12)
        bysrc={}
        for s in ['HVS','NPH52','SEA_AD']:
            m=good&(fm.source.values==s)
            bysrc[s]=dict(n=int(m.sum()),median_rel_displacement=float(np.nanmedian(rel[m])),
                          median_cosine_displacement=float(np.nanmedian(cs[m])))
        byband={}
        for k,bname in enumerate(bands):
            m=good&(bi==k)
            byband[str(bname)]=dict(n=int(m.sum()),
                median_rel_displacement=float(np.nanmedian(rel[m])) if m.sum() else None,
                median_cosine_displacement=float(np.nanmedian(cs[m])) if m.sum() else None)
        geo['V%d|p%.2f'%(view,p/100)]['displacement_by_source']=bysrc
        geo['V%d|p%.2f'%(view,p/100)]['displacement_by_baseline_depth_band']=byband
out['geometry']=geo
json.dump(out,open(S/'aud_geometry.json','w'),indent=2,sort_keys=True)
print()
print('=== PAIR-DISTANCE CONCORDANCE vs p=1 (BASE_MECHANICS) ===')
print('%-6s %-6s %10s %10s %12s %12s %10s'%('view','p','spearE','spearC','notEstim','zeroCreated','zeroBase'))
for view in (0,1):
    for p in PS:
        if p==100: continue
        r=geo['V%d|p%.2f'%(view,p/100)]['BASE_MECHANICS']
        print('V%-5d %-6.2f %10.4f %10.4f %12d %12d %10d'%(view,p/100,r['spearman_euclidean'],
          r['spearman_cosine'],r['pairs_not_estimable_after_intervention'],r['zero_dist_created'],r['zero_dist_baseline']))
print()
print('=== STRESS STRATA (source-conditional low-depth) ===')
print('%-6s %-6s %10s %10s %12s'%('view','p','spearE','spearC','notEstim'))
for view in (0,1):
    for p in PS:
        if p==100: continue
        r=geo['V%d|p%.2f'%(view,p/100)]['STRESS']
        print('V%-5d %-6.2f %10.4f %10.4f %12d'%(view,p/100,r['spearman_euclidean'],r['spearman_cosine'],
          r['pairs_not_estimable_after_intervention']))
print('GEO_DONE')
