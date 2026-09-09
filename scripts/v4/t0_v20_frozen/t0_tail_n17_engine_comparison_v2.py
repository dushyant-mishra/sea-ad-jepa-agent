from __future__ import annotations
import argparse, csv, json
from pathlib import Path
import numpy as np

from t0_studentized_fl_v1 import studentized_freedman_lane, ols_hc3_last, NotEstimableError
from t0_fl_permutation_authority_v1 import permutation

N=17
B=999
NS=b'T0-TAIL-N17-ENGINE-COMPARE-V2'
NULL_SCENARIOS=[
    'homo_normal','hetero_tail_mild','hetero_tail_strong','hetero_state',
    'skew_lognormal','heavy_t3','leverage_tail','binomial80','beta_binomial',
    'zero_inflated_tail','age_cubic','age_sex_interaction'
]


def nuisance(age,sex):
    c=float(np.mean(age)); a=age-c
    return np.c_[np.ones(len(age)),a,a*a,sex]

def logistic(x): return 1/(1+np.exp(-x))

def pmat(donors,b=B):
    base=sorted(donors,key=lambda d:d.encode('utf-8'))
    return np.asarray([permutation(base,r,namespace=NS) for r in range(b)],dtype=np.int16)

def _rank(a):
    s=np.linalg.svd(a,compute_uv=False)
    tol=max(a.shape)*np.finfo(np.float64).eps*(s[0] if len(s) else 0.0)
    return int(np.sum(s>tol))

def wild_hc3_bootstrap_t(y,xr,pred,b,seed):
    y=np.asarray(y,float); xr=np.asarray(xr,float); pred=np.asarray(pred,float)
    n=len(y); xf=np.c_[xr,pred]
    if _rank(xr)!=xr.shape[1] or _rank(xf)!=xf.shape[1] or n<=xf.shape[1]:
        raise NotEstimableError('rank/df')
    bobs,seobs,tobs=ols_hc3_last(y,xf)
    # Reduced-null fit and HC3 adjusted residuals.
    invr=np.linalg.inv(xr.T@xr)
    br=invr@(xr.T@y); fit=xr@br; e=y-fit
    hr=np.einsum('ij,jk,ik->i',xr,invr,xr)
    if np.any(hr>=1-1e-12): raise NotEstimableError('reduced leverage')
    eadj=e/(1-hr)
    # Full-model fixed design precompute.
    invf=np.linalg.inv(xf.T@xf)
    hf=np.einsum('ij,jk,ik->i',xf,invf,xf)
    if np.any(hf>=1-1e-12): raise NotEstimableError('full leverage')
    rng=np.random.default_rng(seed)
    null=np.empty(b,float)
    for i in range(b):
        w=rng.integers(0,2,n,dtype=np.int8)*2-1
        ys=fit+eadj*w
        bv=invf@(xf.T@ys); rv=ys-xf@bv; u=rv/(1-hf)
        meat=xf.T@((u*u)[:,None]*xf); cov=invf@meat@invf
        var=float(cov[-1,-1])
        if not np.isfinite(var) or var<=0: raise NotEstimableError('bootstrap hc3 variance')
        null[i]=float(bv[-1]/np.sqrt(var))
    pu=(1+int(np.sum(null>=tobs)))/(b+1)
    pl=(1+int(np.sum(null<=tobs)))/(b+1)
    return {'beta':bobs,'hc3_se':seobs,'t_observed':tobs,'p_upper':pu,'p_lower':pl,'null_t':null}

def generate_world(rng,scenario,effect=0.0):
    age=rng.uniform(60,95,N); sex=rng.integers(0,2,N).astype(float)
    if len(np.unique(sex))<2: sex[0]=0; sex[1]=1
    z=nuisance(age,sex)
    agez=(age-age.mean())/age.std()
    state=.75*agez+.20*sex+rng.normal(scale=.85,size=N)
    latent=.65*state+.20*agez+rng.normal(scale=.85,size=N)
    mu=logistic(-2.65+.60*latent)
    if scenario=='binomial80':
        tail=rng.binomial(80,mu)/80
    elif scenario=='beta_binomial':
        conc=18; pp=rng.beta(np.maximum(mu*conc,.2),np.maximum((1-mu)*conc,.2)); tail=rng.binomial(80,pp)/80
    elif scenario=='zero_inflated_tail':
        tail=mu.copy(); tail[rng.random(N)<.30]=0.0
    else:
        tail=mu
    # Base null mean: nuisance + real parent state, but no incremental tail effect.
    my=2.0+.03*(age-age.mean())+.0018*(age-age.mean())**2+.22*sex+1.25*state
    if scenario=='age_cubic': my += .00045*(age-age.mean())**3
    if scenario=='age_sex_interaction': my += .08*(age-age.mean())*sex
    if effect:
        tr=(tail-np.mean(tail))/(np.std(tail)+1e-12)
        # Incremental tail effect after state/nuisance.
        my += effect*tr
    if scenario in {'homo_normal','binomial80','beta_binomial','zero_inflated_tail','age_cubic','age_sex_interaction'}:
        e=rng.normal(size=N)
    elif scenario=='hetero_tail_mild':
        tz=(tail-tail.mean())/(tail.std()+1e-12); e=rng.normal(scale=np.exp(.30*tz),size=N)
    elif scenario=='hetero_tail_strong':
        tz=(tail-tail.mean())/(tail.std()+1e-12); e=rng.normal(scale=np.exp(.60*tz),size=N)
    elif scenario=='hetero_state':
        sz=(state-state.mean())/state.std(); e=rng.normal(scale=np.exp(.40*sz),size=N)
    elif scenario=='skew_lognormal':
        e=rng.lognormal(0,.75,N)-np.exp(.75**2/2)
    elif scenario=='heavy_t3':
        e=rng.standard_t(3,N)/np.sqrt(3)
    elif scenario=='leverage_tail':
        e=rng.normal(size=N); tail=tail.copy(); tail[np.argmax(age)]=min(1.0,max(.75,float(tail.max()+.35)))
    else: raise ValueError(scenario)
    y=my+e; y-=min(0.0,float(y.min()))
    return y,np.c_[z,state],tail

def decision(result,pos_alpha,neg_alpha):
    b=float(result['beta']); pu=float(result['p_upper']); pl=float(result['p_lower'])
    return (b>0 and pu<=pos_alpha),(b<0 and pl<=neg_alpha)

def run_null(scenarios,worlds,pos_alpha,neg_alpha,seed_base):
    donors=[f'd{i:02d}' for i in range(N)]; P=pmat(donors)
    rows=[]
    for si,sc in enumerate(scenarios):
        rng=np.random.default_rng(seed_base+si*100003)
        counts={'fl_pos':0,'fl_neg':0,'wild_pos':0,'wild_neg':0,'estimable':0}
        for wi in range(worlds):
            y,xr,tail=generate_world(rng,sc,0.0)
            try:
                fl=studentized_freedman_lane(y,xr,tail,P)
                wb=wild_hc3_bootstrap_t(y,xr,tail,B,seed_base+si*100003+wi*7919+17)
            except NotEstimableError:
                continue
            counts['estimable']+=1
            a,b=decision(fl,pos_alpha,neg_alpha); counts['fl_pos']+=a; counts['fl_neg']+=b
            a,b=decision(wb,pos_alpha,neg_alpha); counts['wild_pos']+=a; counts['wild_neg']+=b
        d=max(1,counts['estimable'])
        rows.append({
            'scenario':sc,'worlds':worlds,'estimable':counts['estimable'],'resamples':B,
            'fl_pos_rate':counts['fl_pos']/d,'fl_neg_rate':counts['fl_neg']/d,'fl_combined_rate':(counts['fl_pos']+counts['fl_neg'])/d,
            'wild_pos_rate':counts['wild_pos']/d,'wild_neg_rate':counts['wild_neg']/d,'wild_combined_rate':(counts['wild_pos']+counts['wild_neg'])/d,
        })
    return rows

def run_power(effects,worlds,pos_alpha,seed_base):
    donors=[f'd{i:02d}' for i in range(N)]; P=pmat(donors); rows=[]
    # Use four distinct error structures for power, none with nuisance misspecification.
    scenarios=['homo_normal','hetero_tail_mild','hetero_tail_strong','skew_lognormal']
    for ei,effect in enumerate(effects):
        for si,sc in enumerate(scenarios):
            rng=np.random.default_rng(seed_base+ei*1000003+si*100003)
            fl=wb=est=0
            for wi in range(worlds):
                y,xr,tail=generate_world(rng,sc,effect)
                try:
                    rf=studentized_freedman_lane(y,xr,tail,P)
                    rw=wild_hc3_bootstrap_t(y,xr,tail,B,seed_base+ei*1000003+si*100003+wi*7919+31)
                except NotEstimableError: continue
                est+=1; fl+=bool(rf['beta']>0 and rf['p_upper']<=pos_alpha); wb+=bool(rw['beta']>0 and rw['p_upper']<=pos_alpha)
            d=max(1,est)
            rows.append({'effect':effect,'scenario':sc,'worlds':worlds,'estimable':est,'fl_power':fl/d,'wild_power':wb/d})
    return rows

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--out-prefix',required=True); ap.add_argument('--worlds',type=int,default=200); ap.add_argument('--power-worlds',type=int,default=150); ap.add_argument('--pos-alpha',type=float,default=.020); ap.add_argument('--neg-alpha',type=float,default=.005); ap.add_argument('--seed-base',type=int,default=11092026); a=ap.parse_args()
    null=run_null(NULL_SCENARIOS,a.worlds,a.pos_alpha,a.neg_alpha,a.seed_base)
    power=run_power([.35,.60,.90],a.power_worlds,a.pos_alpha,a.seed_base+70000000)
    prefix=Path(a.out_prefix)
    for suffix,rows in [('null.csv',null),('power.csv',power)]:
        p=Path(str(prefix)+'_'+suffix); p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('w',newline='',encoding='utf-8') as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    summary={
        'schema':'t0-tail-n17-engine-comparison-v2','n':N,'resamples':B,'fresh_seed_base':a.seed_base,
        'positive_alpha_candidate':a.pos_alpha,'negative_alpha_candidate':a.neg_alpha,
        'null_worlds_per_scenario':a.worlds,'power_worlds_per_cell':a.power_worlds,
        'fl_worst_false_terminal':max(r['fl_combined_rate'] for r in null),
        'wild_worst_false_terminal':max(r['wild_combined_rate'] for r in null),
        'null_rows':null,'power_rows':power,
    }
    p=Path(str(prefix)+'_summary.json');p.write_text(json.dumps(summary,sort_keys=True,separators=(',',':'))+'\n')
    print(json.dumps(summary,indent=2,sort_keys=True))
if __name__=='__main__': main()
