from __future__ import annotations
import argparse,csv,hashlib,json
from pathlib import Path
import numpy as np
from t0_studentized_fl_v1 import studentized_freedman_lane
from t0_fl_permutation_authority_v1 import permutation

N=17; B=999; WORLDS=800; POS=.025; NEG=.005; NS=b'T0-TAIL-N17-CAL-V1'
SCENARIOS=['homo_logistic','hetero_state','hetero_tail','skew_response','leverage_tail','binomial80','beta_binomial']

def pmat(donors): return np.asarray([permutation(donors,r,namespace=NS) for r in range(B)],dtype=np.int16)
def nuisance(age,sex):
    c=float(np.mean(age)); a=age-c; return np.c_[np.ones(len(age)),a,a*a,sex]
def logistic(x): return 1/(1+np.exp(-x))

def one_world(rng,scenario,P):
    age=rng.uniform(60,95,N); sex=rng.integers(0,2,N).astype(float)
    if len(np.unique(sex))<2: sex[0]=0;sex[1]=1
    z=nuisance(age,sex); state=.7*(age-age.mean())/age.std()+rng.normal(size=N)
    latent=.55*state+rng.normal(size=N)
    if scenario=='binomial80':
        prob=logistic(-2.8+.35*latent); tail=rng.binomial(80,prob)/80
    elif scenario=='beta_binomial':
        mu=logistic(-2.8+.35*latent); conc=25; p=rng.beta(np.maximum(mu*conc,.2),np.maximum((1-mu)*conc,.2)); tail=rng.binomial(80,p)/80
    else: tail=logistic(-2.8+.55*latent)
    mu_y=2+.025*(age-age.mean())+.002*(age-age.mean())**2+.25*sex+1.4*state
    if scenario=='homo_logistic' or scenario in {'binomial80','beta_binomial'}: e=rng.normal(size=N)
    elif scenario=='hetero_state': e=rng.normal(scale=np.exp(.30*(state-state.mean())/state.std()),size=N)
    elif scenario=='hetero_tail': e=rng.normal(scale=np.exp(.40*(tail-tail.mean())/(tail.std()+1e-12)),size=N)
    elif scenario=='skew_response': e=rng.lognormal(0,.7,N)-np.exp(.7**2/2)
    elif scenario=='leverage_tail':
        e=rng.normal(size=N); tail=tail.copy(); tail[np.argmax(age)]=min(1.0,tail.max()+.5)
    else: raise ValueError
    y=mu_y+e; y-=min(0.0,float(y.min()))
    r=studentized_freedman_lane(y,np.c_[z,state],tail,P)
    pos=bool(r['beta']>0 and r['p_upper']<=POS); neg=bool(r['beta']<0 and r['p_lower']<=NEG)
    return pos,neg

def run(scenarios=None,worlds=WORLDS):
    scenarios=SCENARIOS if scenarios is None else scenarios
    donors=[f'd{i:02d}' for i in range(N)]; P=pmat(donors); rows=[]
    for sc in scenarios:
        j=SCENARIOS.index(sc); rng=np.random.default_rng(918200+j*100003); pos=neg=0
        for _ in range(worlds):
            a,b=one_world(rng,sc,P); pos+=a; neg+=b
        rows.append({'scenario':sc,'worlds':worlds,'permutations':B,'positive_false_support_rate':pos/worlds,'negative_false_disqualify_rate':neg/worlds,'combined_false_terminal_rate':(pos+neg)/worlds})
    return rows

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--output',required=True); ap.add_argument('--scenario',action='append',choices=SCENARIOS); ap.add_argument('--worlds',type=int,default=WORLDS); a=ap.parse_args(); rows=run(a.scenario,a.worlds); out=Path(a.output)
    with out.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    summary={'schema':'t0-tail-n17-null-calibration-v1','n':N,'worlds_per_scenario':a.worlds,'calibration_permutations':B,'decision_positive_alpha':POS,'decision_negative_alpha':NEG,'worst_combined_false_terminal_rate':max(r['combined_false_terminal_rate'] for r in rows),'rows':rows}
    sp=out.with_suffix('.json'); sp.write_text(json.dumps(summary,sort_keys=True,separators=(',',':'))+'\n')
    print(json.dumps(summary,indent=2,sort_keys=True))
if __name__=='__main__': main()
