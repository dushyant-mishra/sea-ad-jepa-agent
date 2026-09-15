"""WITHDRAWN - DEFECTIVE. DO NOT RUN.

This implementation double-centred training data inconsistently across folds. On a
controlled fixture containing ONLY operator-level shared structure and ZERO cell-level
shared signal it reported substantial "within-operator signal". Its outputs were
discarded and never entered the evidence record. Superseded by scripts/x5_within.py,
which is validated in scripts/x6_fixture.py (null fixture -0.0068, recovery 0.233/0.595,
negative control -0.0020). Retained only so the defect claim can be reproduced.
"""

# Within-batch cross-view signal: after removing batch-level mean structure
# (estimated on TRAINING folds only), how much does V0 still predict V1?
import numpy as np, pandas as pd, json, pathlib
S=pathlib.Path(r'C:/Users/dushy/AppData/Local/Temp/claude/d--Jepa-project/cdf819f6-5db4-4119-9a97-37fef1d27909/scratchpad')
LAM=1e-2; NF=5
z=np.load(S/'screen_out.npz')
fm=pd.read_csv(S/'final_manifest.csv',usecols=['donor_id','operator_index','source','stratum'])
base=(fm.stratum=='BASE_MECHANICS').values
don=pd.factorize(fm.donor_id)[0][base]; fold=(don%NF).astype(np.int8)
op=pd.factorize(fm.operator_index[base])[0]; src=pd.factorize(fm.source[base])[0]
res={}
def run(pv,label):
    V0=np.asarray(z['p100_v0'][base],dtype=np.float64); V1=np.asarray(z['p100_v1'][base],dtype=np.float64)
    if pv is not None:
        K=pv.max()+1
        for f in range(NF):
            tr=fold!=f
            for Vx in (V0,V1):
                m0=np.zeros((K,Vx.shape[1])); c0=np.zeros(K)
                np.add.at(m0,pv[tr],Vx[tr]); np.add.at(c0,pv[tr],1)
                gm=Vx[tr].mean(0)
                mm=np.where(c0[:,None]>0,m0/np.maximum(c0,1)[:,None],gm)
                if Vx is V0: V0[fold==f]-=mm[pv[fold==f]]
                else:        V1[fold==f]-=mm[pv[fold==f]]
                Vx_tr_mm=mm
            # also centre training rows with their own (in-fold) means for fitting
        for Vx in (V0,V1):
            pass
    gm=V1.mean(0); sse=sst=0.0
    for f in range(NF):
        m=fold==f; tr=~m
        At,Yt=V0[tr],V1[tr]
        if pv is not None:
            K=pv.max()+1
            for Vx,store in ((At,'a'),(Yt,'b')):
                s=np.zeros((K,Vx.shape[1])); c=np.zeros(K)
                np.add.at(s,pv[tr],Vx); np.add.at(c,pv[tr],1)
                g=Vx.mean(0); mm=np.where(c[:,None]>0,s/np.maximum(c,1)[:,None],g)
                if store=='a': At=At-mm[pv[tr]]
                else: Yt=Yt-mm[pv[tr]]
        mu,sd=At.mean(0),np.maximum(At.std(0),1e-12)
        As=(At-mu)/sd; muB=Yt.mean(0)
        G=As.T@As+LAM*len(As)*np.eye(As.shape[1])
        w=np.linalg.solve(G,As.T@(Yt-muB))
        r=V1[m]-(((V0[m]-mu)/sd)@w+muB)
        sse+=float((r*r).sum()); d=V1[m]-gm; sst+=float((d*d).sum())
    return 1.0-sse/sst
print('=== CROSS-VIEW R2 BEFORE AND AFTER REMOVING BATCH MEAN STRUCTURE ===')
print('    (batch means estimated on TRAINING folds only; donor-held-out throughout)')
print()
for pv,label in [(None,'no centring (raw V0 -> V1)'),
                 (src,'source-centred (3 levels)'),
                 (op,'operator-centred (42 levels)'),
                 (don,'donor-centred (94 levels)')]:
    v=run(pv,label); res[label]=v
    print('  %-34s R2 = %.4f'%(label,v))
json.dump(res,open(S/'x_within.json','w'),indent=2,sort_keys=True)
print('WITHIN_DONE')
