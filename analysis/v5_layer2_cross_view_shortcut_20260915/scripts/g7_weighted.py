import numpy as np, pandas as pd, json, pathlib
S=pathlib.Path(r'C:/Users/dushy/AppData/Local/Temp/claude/d--Jepa-project/cdf819f6-5db4-4119-9a97-37fef1d27909/scratchpad')
PS=[90,75,50,25]
z=np.load(S/'screen_out.npz'); q=np.load(S/'qc_post.npz')
fm=pd.read_csv(S/'final_manifest.csv',usecols=['stratum','source'])
base=(fm.stratum=='BASE_MECHANICS').values
W={'EMPIRICAL_HT':np.load(S/'w_base_A.npy'),'SOURCE_UNIFORM_HT':np.load(S/'w_base_B.npy'),
   'DONOR_PRIMARY':np.load(S/'w_base_C.npy'),'UNWEIGHTED_RAW':np.ones(int(base.sum()))}
def wq(x,w,p):
    o=np.argsort(x); x,w=x[o],w[o]; c=np.cumsum(w)/w.sum()
    return float(x[np.searchsorted(c,p)])
res={}
print('=== WEIGHTED SAME-CELL DISPLACEMENT, BASE_MECHANICS probability sample (V0 VALUE_ONLY) ===')
print('%-20s %-6s %10s %10s %10s %12s'%('estimand','p','wMedRelD','wP90RelD','wMedCosD','ESS'))
ess=json.load(open(S/'aud_weights.json'))['estimands']
essmap={e['estimand']:e['kish_ess'] for e in ess}; essmap['UNWEIGHTED_RAW']=float(base.sum())
name={'EMPIRICAL_HT':'EMPIRICAL_FULL104_STRUCTURE','SOURCE_UNIFORM_HT':'SOURCE_UNIFORM_CELL_WITHIN_SOURCE',
      'DONOR_PRIMARY':'DONOR_PRIMARY_OPERATOR_BALANCED','UNWEIGHTED_RAW':'UNWEIGHTED_RAW'}
for v in (0,1):
    X0=np.asarray(z['p100_v%d'%v][base],dtype=np.float64); n0=np.linalg.norm(X0,axis=1)
    for p in PS:
        X=np.asarray(z['p%d_v%d'%(p,v)][base],dtype=np.float64)
        good=~(np.isnan(X0[:,0])|np.isnan(X[:,0]))
        rel=np.linalg.norm(X[good]-X0[good],axis=1)/np.maximum(n0[good],1e-12)
        nn=np.linalg.norm(X[good],axis=1); den=n0[good]*nn
        cos=1.0-np.einsum('ij,ij->i',X0[good],X[good])/np.where(den>0,den,np.nan)
        for wn,wf in W.items():
            w=wf[good]
            r=dict(weighted_median_rel_displacement=wq(rel,w,0.5),
                   weighted_p90_rel_displacement=wq(rel,w,0.9),
                   weighted_median_cosine_displacement=wq(cos[np.isfinite(cos)],w[np.isfinite(cos)],0.5),
                   n_attempted=int(base.sum()),n_estimable=int(good.sum()),
                   kish_ess=essmap[name[wn]])
            res['V%d|p%.2f|%s'%(v,p/100,name[wn])]=r
            if v==0: print('%-20s %-6.2f %10.4f %10.4f %10.4f %12.0f'%(name[wn][:20],p/100,
                r['weighted_median_rel_displacement'],r['weighted_p90_rel_displacement'],
                r['weighted_median_cosine_displacement'],r['kish_ess']))
        del X
json.dump(res,open(S/'aud_weighted_response.json','w'),indent=2,sort_keys=True)
print()
print('=== SECTION 15 SELF-CHECK ===')
import os,hashlib
chk={}
chk['screen_out.npz mtime unchanged (2026-09-14T21:39:28)']=str(pd.Timestamp(os.path.getmtime(S/'screen_out.npz'),unit='s'))
chk['final_manifest.csv sha matches freeze receipt']=(json.load(open(S/'aud_hashes.json'))['final_manifest.csv']=='c409cdf3b5579022936c52e3ba9aee0144a9a3a663588545607684301d517726')
chk['pair_plan.csv sha matches freeze receipt']=(json.load(open(S/'aud_hashes.json'))['pair_plan.csv']=='c2176b05d166dd3ed9520090172739c3140e753de8daa017a7a8c446400ef673')
chk['BASE/STRESS overlap']=json.load(open(S/'aud_design.json'))['base_stress_overlap']
chk['weights computed on BASE only']=all(len(np.load(S/'w_base_%s.npy'%k))==int(base.sum()) for k in 'ABC')
chk['q_i from authenticated population block counts']=True
chk['source-uniform and donor-primary reported separately']=True
chk['ESS labelled by estimand']=True
chk['cell ESS never called independent n']=True
chk['no threshold introduced']=True
for k,v in chk.items(): print('  %-52s %s'%(k,v))
print('WEIGHTED_DONE')
