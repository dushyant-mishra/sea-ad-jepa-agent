import numpy as np, pandas as pd, json, pathlib
from scipy.stats import spearmanr
S=pathlib.Path(r'C:/Users/dushy/AppData/Local/Temp/claude/d--Jepa-project/cdf819f6-5db4-4119-9a97-37fef1d27909/scratchpad')
PS=[90,75,50,25]
z=np.load(S/'screen_out.npz',allow_pickle=True); pp=pd.read_csv(S/'pair_plan.csv')
fm=pd.read_csv(S/'final_manifest.csv',usecols=['source','stratum'])
a_i,b_i,strat=pp.a.to_numpy(),pp.b.to_numpy(),pp.stratum.to_numpy()
lib0=z['lib_p100']
res={}
print('=== STRESS STRATA, SOURCE BY SOURCE  (MEASUREMENT_STRESS_CHALLENGE, not prevalence) ===')
print('%-14s %-4s %-6s %8s %10s %10s %10s %9s'%('stratum','view','p','pairs','spearE','spearC','notEstim','medRelDsp'))
for view in (0,1):
    X0=z['p100_v%d'%view]; n0=np.linalg.norm(X0,axis=1)
    dE0=np.linalg.norm(X0[a_i]-X0[b_i],axis=1); den0=n0[a_i]*n0[b_i]
    dC0=1.0-np.einsum('ij,ij->i',X0[a_i],X0[b_i])/np.where(den0>0,den0,np.nan)
    e0=~(np.isnan(X0[a_i,0])|np.isnan(X0[b_i,0]))
    for p in PS:
        X=z['p%d_v%d'%(p,view)]; n=np.linalg.norm(X,axis=1)
        dE=np.linalg.norm(X[a_i]-X[b_i],axis=1); den=n[a_i]*n[b_i]
        dC=1.0-np.einsum('ij,ij->i',X[a_i],X[b_i])/np.where(den>0,den,np.nan)
        e=~(np.isnan(X[a_i,0])|np.isnan(X[b_i,0]))
        good=~(np.isnan(X0[:,0])|np.isnan(X[:,0]))
        dsp=np.full(len(X0),np.nan); d0n=np.linalg.norm(X0,axis=1)
        dsp[good]=np.linalg.norm(X[good]-X0[good],axis=1)/np.maximum(d0n[good],1e-12)
        for st in ['STRESS_HVS','STRESS_NPH52','STRESS_SEA_AD']:
            m=(strat==st)&e0&e; mc=m&np.isfinite(dC0)&np.isfinite(dC)
            cells=(fm.stratum.values==st)
            r=dict(pairs_planned=int((strat==st).sum()),pairs_estimable=int(m.sum()),
                   pairs_not_estimable_after_intervention=int(((strat==st)&e0&~e).sum()),
                   cells_in_stratum=int(cells.sum()),
                   cells_non_estimable=int((cells&~good).sum()),
                   spearman_euclidean=float(spearmanr(dE0[m],dE[m]).statistic),
                   spearman_cosine=float(spearmanr(dC0[mc],dC[mc]).statistic),
                   median_rel_displacement=float(np.nanmedian(dsp[cells])),
                   median_baseline_library=float(np.median(lib0[cells])))
            res['V%d|p%.2f|%s'%(view,p/100,st)]=r
            print('%-14s V%-3d %-6.2f %8d %10.4f %10.4f %10d %9.4f'%(st,view,p/100,r['pairs_estimable'],
              r['spearman_euclidean'],r['spearman_cosine'],r['pairs_not_estimable_after_intervention'],
              r['median_rel_displacement']))
print()
print('=== STRESS STRATUM COMPOSITION (baseline) ===')
for st in ['STRESS_HVS','STRESS_NPH52','STRESS_SEA_AD']:
    c=fm.stratum.values==st
    print('  %-14s cells %5d   baseline library: min %6d  median %8.0f  max %8.0f'%(st,int(c.sum()),
      int(lib0[c].min()),np.median(lib0[c]),lib0[c].max()))
json.dump(res,open(S/'aud_stress.json','w'),indent=2,sort_keys=True)
print('STRESS_DONE')
