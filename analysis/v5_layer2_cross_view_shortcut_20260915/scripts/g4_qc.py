import numpy as np, pandas as pd, json, pathlib
S=pathlib.Path(r'C:/Users/dushy/AppData/Local/Temp/claude/d--Jepa-project/cdf819f6-5db4-4119-9a97-37fef1d27909/scratchpad')
PS=[100,90,75,50,25]
z=np.load(S/'screen_out.npz'); q=np.load(S/'qc_post.npz')
fm=pd.read_csv(S/'final_manifest.csv',usecols=['donor_id','source','stratum'])
base=(fm.stratum=='BASE_MECHANICS').values
don=pd.factorize(fm.donor_id)[0]
dgB=don[base]%5
W={'UNWEIGHTED':np.ones(int(base.sum())),'EMPIRICAL_HT':np.load(S/'w_base_A.npy'),
   'SOURCE_UNIFORM_HT':np.load(S/'w_base_B.npy'),'DONOR_PRIMARY':np.load(S/'w_base_C.npy')}
LAM=1e-2   # identical to frozen ablation procedure
res={}
print('=== POST-INTERVENTION QC: DONOR-HELD-OUT CROSS-FITTED PREDICTABILITY FROM VALUE_ONLY ===')
print('    fit is UNWEIGHTED (frozen estimator semantics unchanged); weights applied to EVALUATION only')
print('%-4s %-6s %-10s %9s %9s %9s %9s %9s'%('view','p','target','R2_unw','R2_emp','R2_srcU','R2_donP','maxAbsR'))
for v in (0,1):
    for p in PS:
        X=np.asarray(z['p%d_v%d'%(p,v)][base],dtype=np.float64)
        good=~np.isnan(X[:,0]); Xg=X[good]; dg=dgB[good]
        A=(Xg-Xg.mean(0))/np.maximum(Xg.std(0),1e-9)
        for tname,yraw in (('Q_DETECT',q['det_p%d'%p][base][good].astype(np.float64)),
                           ('Q_DEPTH', q['lib_p%d'%p][base][good].astype(np.float64))):
            yy=(yraw-yraw.mean())/max(yraw.std(),1e-9)
            oof=np.zeros(len(yy))
            for f in range(5):
                tr,te=dg!=f,dg==f
                At=A[tr]; G=At.T@At+LAM*len(At)*np.eye(A.shape[1])
                w_=np.linalg.solve(G,At.T@yy[tr]); oof[te]=A[te]@w_
            # raw marginal correlations (for max |r| in the spectrum table)
            cc=(A*yy[:,None]).mean(0)
            row={'max_abs_marginal_corr':float(np.abs(cc).max()),
                 'n_attempted':int(base.sum()),'n_estimable':int(good.sum())}
            for wn,wfull in W.items():
                ww=wfull[good]; sw=ww.sum(); ybar=(ww*yy).sum()/sw
                row['R2_'+wn]=float(1-(ww*(yy-oof)**2).sum()/(ww*(yy-ybar)**2).sum())
            res['V%d|p%.2f|%s'%(v,p/100,tname)]=row
            print('V%-3d %-6.2f %-10s %9.4f %9.4f %9.4f %9.4f %9.4f'%(v,p/100,tname,row['R2_UNWEIGHTED'],
              row['R2_EMPIRICAL_HT'],row['R2_SOURCE_UNIFORM_HT'],row['R2_DONOR_PRIMARY'],row['max_abs_marginal_corr']))
        del X,Xg,A
json.dump(res,open(S/'aud_qc.json','w'),indent=2,sort_keys=True)
print()
print('=== BASELINE COMPARISON (frozen ablation, full 4.55M population subsample) ===')
ab=json.load(open(S/'ablation.json'))['nuisance_predictability_oof_donor_disjoint']
for k in ('V0|VALUE_ONLY','V1|VALUE_ONLY','V0|VISIBILITY_ONLY','V1|VISIBILITY_ONLY'):
    print('  %-22s Q_DETECT %.4f  Q_DEPTH %.4f'%(k,ab[k]['Q_DETECT'],ab[k]['Q_DEPTH']))
print('QC_DONE')
