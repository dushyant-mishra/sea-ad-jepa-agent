import numpy as np, pandas as pd, json, pathlib
from scipy.stats import spearmanr
S=pathlib.Path(r'C:/Users/dushy/AppData/Local/Temp/claude/d--Jepa-project/cdf819f6-5db4-4119-9a97-37fef1d27909/scratchpad')
PS=[100,90,75,50,25]
z=np.load(S/'screen_out.npz',allow_pickle=True)
fm=pd.read_csv(S/'final_manifest.csv',usecols=['donor_id','operator_index','source','stratum','block_key'])
base=(fm.stratum=='BASE_MECHANICS').values
don=pd.factorize(fm.donor_id)[0]; op=pd.factorize(fm.operator_index)[0]; src=pd.factorize(fm.source)[0]
W={'UNIFORM':np.ones(int(base.sum())),'EMPIRICAL_HT':np.load(S/'w_base_A.npy'),'SOURCE_UNIFORM_HT':np.load(S/'w_base_B.npy'),
   'DONOR_PRIMARY':np.load(S/'w_base_C.npy')}
dB,oB,sB=don[base],op[base],src[base]

def spec(X,w,groups):
    sw=w.sum(); mu=(w[:,None]*X).sum(0)/sw
    Xc=X-mu; cov=(Xc*w[:,None]).T@Xc/sw
    ev=np.clip(np.linalg.eigvalsh(cov)[::-1],0,None); tr=ev.sum(); cum=np.cumsum(ev)/tr
    nf=float(np.median(ev[ev>0][-64:])) if (ev>0).sum()>=64 else 0.0
    out=dict(total_variance=float(tr),eig_min=float(ev[-1]),eig_max=float(ev[0]),
      numerical_rank=int((ev>tr*1e-12).sum()),condition_number=float(ev[0]/max(ev[-1],1e-300)),
      participation_ratio=float(tr**2/(ev**2).sum()),
      spectral_entropy_rank=float(np.exp(-((ev/tr)[ev>0]*np.log((ev/tr)[ev>0])).sum())),
      rank90=int(np.searchsorted(cum,.90)+1),rank95=int(np.searchsorted(cum,.95)+1),
      rank99=int(np.searchsorted(cum,.99)+1),noise_floor=nf,rank_above_noise_floor=int((ev>nf).sum()))
    for nm,g in groups.items():
        K=g.max()+1; gs=np.zeros((K,X.shape[1])); gw=np.zeros(K)
        np.add.at(gs,g,Xc*w[:,None]); np.add.at(gw,g,w)
        m=gw>0; gm=gs[m]/gw[m][:,None]
        out['var_frac_'+nm]=float(((gw[m]/sw)[:,None]*gm**2).sum()/tr)
    out['operator_donor_ratio']=out['var_frac_operator']/max(out['var_frac_donor'],1e-300)
    return out

res={}; nonest={}
for v in (0,1):
    for p in PS:
        X=np.asarray(z['p%d_v%d'%(p,v)][base],dtype=np.float64)
        good=~np.isnan(X[:,0])
        nonest['V%d|p%.2f'%(v,p/100)]=dict(attempted=int(base.sum()),estimable=int(good.sum()),
                                            non_estimable=int((~good).sum()))
        Xg=X[good]
        for wn,w in W.items():
            res['V%d|p%.2f|%s'%(v,p/100,wn)]=spec(Xg,w[good],{'donor':dB[good],'operator':oB[good],'source':sB[good]})
        del X,Xg
    print('V%d spectra done'%v,flush=True)

# V0 vs V1 concordance at each p (BASE pairs, frozen plan)
pp=pd.read_csv(S/'pair_plan.csv'); pb=pp[pp.stratum=='BASE_MECHANICS']
a_i,b_i=pb.a.to_numpy(),pb.b.to_numpy()
conc={}
for p in PS:
    X0=z['p%d_v0'%p]; X1=z['p%d_v1'%p]
    e=~(np.isnan(X0[a_i,0])|np.isnan(X0[b_i,0])|np.isnan(X1[a_i,0])|np.isnan(X1[b_i,0]))
    d0=np.linalg.norm(X0[a_i][e]-X0[b_i][e],axis=1); d1=np.linalg.norm(X1[a_i][e]-X1[b_i][e],axis=1)
    conc['p%.2f'%(p/100)]=dict(pairs=int(e.sum()),spearman_V0_vs_V1=float(spearmanr(d0,d1).statistic))
json.dump({'spectra':res,'estimability':nonest,'V0_V1_pair_concordance':conc},
          open(S/'aud_spectra.json','w'),indent=2,sort_keys=True)

print()
print('=== V0/V1 SPECTRUM AND NUISANCE ACROSS p  (BASE_MECHANICS, SOURCE_UNIFORM_HT weighting) ===')
print('%-4s %-6s %7s %8s %8s %8s %8s %8s %8s %8s %8s'%('view','p','rank','cond','partR','entR','r90','r99','vfDon','vfOp','op/don'))
for v in (0,1):
    for p in PS:
        r=res['V%d|p%.2f|SOURCE_UNIFORM_HT'%(v,p/100)]
        print('V%-3d %-6.2f %7d %8.1f %8.2f %8.2f %8d %8d %8.4f %8.4f %8.3f'%(v,p/100,r['numerical_rank'],
          r['condition_number'],r['participation_ratio'],r['spectral_entropy_rank'],r['rank90'],r['rank99'],
          r['var_frac_donor'],r['var_frac_operator'],r['operator_donor_ratio']))
print()
print('=== WEIGHTING SENSITIVITY OF NUISANCE FRACTIONS (V0) ===')
print('%-20s %-6s %8s %8s %8s %8s'%('weighting','p','vfDonor','vfOper','vfSource','op/don'))
for wn in W:
    for p in (100,25):
        r=res['V0|p%.2f|%s'%(p/100,wn)]
        print('%-20s %-6.2f %8.4f %8.4f %8.4f %8.3f'%(wn,p/100,r['var_frac_donor'],r['var_frac_operator'],
          r['var_frac_source'],r['operator_donor_ratio']))
print()
print('=== V0 vs V1 CONCORDANCE (independent molecular halves) ===')
for p in PS: print('  p=%.2f  pairs %d  Spearman(V0,V1) %.4f'%(p/100,conc['p%.2f'%(p/100)]['pairs'],conc['p%.2f'%(p/100)]['spearman_V0_vs_V1']))
print('SPEC_DONE')
