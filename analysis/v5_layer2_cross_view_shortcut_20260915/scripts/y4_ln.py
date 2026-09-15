# PART 2 (doable portion): does the JEPA-style loss GEOMETRY change the context/molecular split?
# Layer-normalised targets + MSE, matching the loss geometry only.
# MECHANICS_ALIGNED_PROXY_ONLY - the real objective operates on trained encoder hidden
# states, which do not exist under TRAINING_OFF, and V5 target semantics are NOT frozen.
import numpy as np, pandas as pd, json, pathlib
S=pathlib.Path(r'C:/Users/dushy/AppData/Local/Temp/claude/d--Jepa-project/cdf819f6-5db4-4119-9a97-37fef1d27909/scratchpad')
LAM=1e-2; NF=5
z=np.load(S/'screen_out.npz'); q=np.load(S/'qc_post.npz')
fm=pd.read_csv(S/'final_manifest.csv',usecols=['donor_id','operator_index','source','stratum'])
base=(fm.stratum=='BASE_MECHANICS').values
def LN(X):
    m=X.mean(1,keepdims=True); s=np.maximum(X.std(1,keepdims=True),1e-9); return (X-m)/s
V0r=np.asarray(z['p100_v0'][base],dtype=np.float64); V1r=np.asarray(z['p100_v1'][base],dtype=np.float64)
V0n,V1n=LN(V0r),LN(V1r)
L=np.log1p(q['lib_p100'][base].astype(np.float64)); Dt=np.log1p(q['det_p100'][base].astype(np.float64))
QC=np.column_stack([L,Dt,L**2,Dt**2,L*Dt])
src=pd.get_dummies(fm.source[base]).to_numpy(float); op=pd.get_dummies(fm.operator_index[base]).to_numpy(float)
CTX=np.column_stack([QC,src,op])
dser=fm.donor_id[base].to_numpy(); dc=pd.factorize(dser)[0]
def cr2(A,Y,lv,fold):
    K=1 if lv is None else int(lv.max())+1; sse=0.0; Ys=[]
    for f in range(NF):
        te=fold==f; tr=~te
        if lv is None: A_tr,A_te,Y_tr,Y_te=A[tr],A[te],Y[tr],Y[te]
        else:
            def bm(X):
                s_=np.zeros((K,X.shape[1])); c=np.zeros(K)
                np.add.at(s_,lv[tr],X[tr]); np.add.at(c,lv[tr],1)
                g=X[tr].mean(0); return np.where(c[:,None]>0,s_/np.maximum(c,1)[:,None],g)
            m0,m1=bm(A),bm(Y)
            A_tr=A[tr]-m0[lv[tr]]; A_te=A[te]-m0[lv[te]]; Y_tr=Y[tr]-m1[lv[tr]]; Y_te=Y[te]-m1[lv[te]]
        mu=A_tr.mean(0); sd=np.maximum(A_tr.std(0),1e-12); As=(A_tr-mu)/sd; muB=Y_tr.mean(0)
        w=np.linalg.solve(As.T@As+LAM*len(As)*np.eye(As.shape[1]),As.T@(Y_tr-muB))
        r=Y_te-(((A_te-mu)/sd)@w+muB); sse+=float((r*r).sum()); Ys.append(Y_te)
    Yv=np.vstack(Ys); d=Yv-Yv.mean(0); return 1.0-sse/float((d*d).sum())
fold_d=(dc%NF).astype(np.int8); rng=np.random.default_rng(7); fold_c=rng.integers(0,NF,len(dc)).astype(np.int8)
res={}
print('=== LOSS-GEOMETRY SENSITIVITY: raw target vs LAYER-NORMALISED target ===')
print('    MECHANICS_ALIGNED_PROXY_ONLY (not the frozen V5 objective)')
print()
for gname,(P,T) in [('raw',(V0r,V1r)),('layer-normalised',(V0n,V1n))]:
    print('  target geometry: %s'%gname)
    a=cr2(CTX,T,None,fold_d); b=cr2(P,T,None,fold_d); c=cr2(np.column_stack([CTX,P]),T,None,fold_d)
    d=cr2(P,T,dc,fold_c); e=cr2(QC,T,dc,fold_c)
    res[gname]=dict(ctx_only_donor_heldout=a,mol_only_donor_heldout=b,both_donor_heldout=c,
                    mol_increment_over_ctx=c-a,within_donor_mol=d,within_donor_qc=e)
    print('    context only (Q+source+operator), donor-held-out   %.4f'%a)
    print('    molecular V0 only, donor-held-out                  %.4f'%b)
    print('    both                                               %.4f'%c)
    print('    MOLECULAR INCREMENT over strongest context         %+.4f'%(c-a))
    print('    within-donor molecular (cell-held-out)             %.4f'%d)
    print('    within-donor QC only                               %.4f'%e)
    print()
json.dump(res,open(S/'y_ln.json','w'),indent=2,sort_keys=True)
print('LN_DONE')
