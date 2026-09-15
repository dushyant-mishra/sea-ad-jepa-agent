# Within-donor control: is the cell-level cross-view signal reachable from QC alone?
import numpy as np, pandas as pd, json, pathlib
S=pathlib.Path(r'C:/Users/dushy/AppData/Local/Temp/claude/d--Jepa-project/cdf819f6-5db4-4119-9a97-37fef1d27909/scratchpad')
LAM=1e-2; NF=5
z=np.load(S/'screen_out.npz'); q=np.load(S/'qc_post.npz')
fm=pd.read_csv(S/'final_manifest.csv',usecols=['donor_id','source','stratum'])
base=(fm.stratum=='BASE_MECHANICS').values
V0=np.asarray(z['p100_v0'][base],dtype=np.float64); V1=np.asarray(z['p100_v1'][base],dtype=np.float64)
L=np.log1p(q['lib_p100'][base].astype(np.float64)); Dt=np.log1p(q['det_p100'][base].astype(np.float64))
QC=np.column_stack([L,Dt,L**2,Dt**2,L*Dt])
dser=fm.donor_id[base].to_numpy(); sser=fm.source[base].to_numpy()
def cr2(A,Y,lv,fold):
    K=int(lv.max())+1; sse=0.0; Ys=[]
    for f in range(NF):
        te=fold==f; tr=~te
        def bm(X):
            s_=np.zeros((K,X.shape[1])); c=np.zeros(K)
            np.add.at(s_,lv[tr],X[tr]); np.add.at(c,lv[tr],1)
            g=X[tr].mean(0); return np.where(c[:,None]>0,s_/np.maximum(c,1)[:,None],g)
        m0,m1=bm(A),bm(Y)
        A_tr=A[tr]-m0[lv[tr]]; A_te=A[te]-m0[lv[te]]
        Y_tr=Y[tr]-m1[lv[tr]]; Y_te=Y[te]-m1[lv[te]]
        mu=A_tr.mean(0); sd=np.maximum(A_tr.std(0),1e-12); As=(A_tr-mu)/sd; muB=Y_tr.mean(0)
        w=np.linalg.solve(As.T@As+LAM*len(As)*np.eye(As.shape[1]),As.T@(Y_tr-muB))
        r=Y_te-(((A_te-mu)/sd)@w+muB); sse+=float((r*r).sum()); Ys.append(Y_te)
    Yv=np.vstack(Ys); d=Yv-Yv.mean(0); return 1.0-sse/float((d*d).sum())
rng=np.random.default_rng(7); res={}
print('=== WITHIN-DONOR (donor-centred, cell-held-out): WHAT CARRIES THE CELL-LEVEL SIGNAL? ===')
print('%-8s %10s %10s %10s %14s %14s'%('source','QC only','V0 only','QC+V0','V0 over QC','QC over V0'))
for s in ['ALL','HVS','NPH52','SEA_AD']:
    m=np.ones(len(V0),bool) if s=='ALL' else (sser==s)
    dc=pd.factorize(dser[m])[0]; cf=rng.integers(0,NF,int(m.sum())).astype(np.int8)
    a=cr2(QC[m],V1[m],dc,cf); b=cr2(V0[m],V1[m],dc,cf)
    c=cr2(np.column_stack([QC[m],V0[m]]),V1[m],dc,cf)
    res[s]=dict(qc_only=a,v0_only=b,qc_plus_v0=c,v0_increment=c-a,qc_increment=c-b)
    print('%-8s %10.4f %10.4f %10.4f %+14.4f %+14.4f'%(s,a,b,c,c-a,c-b))
json.dump(res,open(S/'y_qc.json','w'),indent=2,sort_keys=True)
print('QCCTRL_DONE')
