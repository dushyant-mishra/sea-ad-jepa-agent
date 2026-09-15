# Nuisance-only cross-view baseline: how much of the FULL-DEPTH cross-view signal
# is reachable from permissible technical covariates alone, with no molecular
# cross-view information? Same folds, same metric, same model class.
import numpy as np, pandas as pd, json, pathlib
S=pathlib.Path(r'C:/Users/dushy/AppData/Local/Temp/claude/d--Jepa-project/cdf819f6-5db4-4119-9a97-37fef1d27909/scratchpad')
LAM=1e-2; NF=5
z=np.load(S/'screen_out.npz'); q=np.load(S/'qc_post.npz')
fm=pd.read_csv(S/'final_manifest.csv',usecols=['donor_id','operator_index','source','stratum'])
base=(fm.stratum=='BASE_MECHANICS').values
don=pd.factorize(fm.donor_id)[0]; fold=(don[base]%NF).astype(np.int8); n=int(base.sum())
L1=np.log1p(q['lib_p100'][base].astype(np.float64)); D1=np.log1p(q['det_p100'][base].astype(np.float64))
src=pd.get_dummies(fm.source[base]).to_numpy(float); op=pd.get_dummies(fm.operator_index[base]).to_numpy(float)
V0=np.asarray(z['p100_v0'][base],dtype=np.float64); V1=np.asarray(z['p100_v1'][base],dtype=np.float64)
def r2(A,Y):
    gm=Y.mean(0); sse=sst=0.0
    for f in range(NF):
        m=fold==f; tr=~m
        At,Yt=A[tr],Y[tr]; mu,sd=At.mean(0),np.maximum(At.std(0),1e-12)
        As=(At-mu)/sd; muB=Yt.mean(0)
        G=As.T@As+LAM*len(As)*np.eye(A.shape[1])
        w=np.linalg.solve(G,As.T@(Yt-muB))
        r=Y[m]-(((A[m]-mu)/sd)@w+muB)
        sse+=float((r*r).sum()); d=Y[m]-gm; sst+=float((d*d).sum())
    return 1.0-sse/sst
QC=np.column_stack([L1,D1])
QC2=np.column_stack([L1,D1,L1**2,D1**2,L1*D1])
QCS=np.column_stack([QC2,src,op])
res={}
print('=== NUISANCE-ONLY CROSS-VIEW BASELINE (target V1 at full depth, donor-held-out) ===')
print('%-46s %10s %10s'%('predictor','R2','% of V0'))
ref=r2(V0,V1); res['V0_molecular_full']=ref
for nm,A in [('Q_DEPTH,Q_DETECT (linear, 2 cols)',QC),
             ('Q_DEPTH,Q_DETECT (+squares,interaction, 5)',QC2),
             ('Q + source + operator one-hot (%d cols)'%QCS.shape[1],QCS)]:
    v=r2(A,V1); res[nm]=v
    print('%-46s %10.4f %9.1f%%'%(nm,v,100*v/ref))
print('%-46s %10.4f %9.1f%%'%('V0 (256-dim molecular, reference)',ref,100.0))
print()
resid=r2(np.column_stack([QCS,V0]),V1); res['QCS_plus_V0']=resid
print('%-46s %10.4f'%('Q+source+operator+V0 (combined)',resid))
print('%-46s %+10.4f'%('  incremental gain of V0 over nuisance alone',resid-res['Q + source + operator one-hot (%d cols)'%QCS.shape[1]]))
print('%-46s %+10.4f'%('  incremental gain of nuisance over V0 alone',resid-ref))
json.dump(res,open(S/'x_nuisance.json','w'),indent=2,sort_keys=True)
print('NUIS_DONE')
