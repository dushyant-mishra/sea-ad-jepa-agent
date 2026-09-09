from __future__ import annotations
import argparse,csv,json
from pathlib import Path
import numpy as np
from scipy.stats import t as student_t
from t0_studentized_fl_v1 import ols_hc3_last,NotEstimableError
from t0_tail_n17_engine_comparison_v2 import N,nuisance,logistic

POS=.020; NEG=.005
SCENARIOS=[
 'homo_normal','hetero_tail_mild','hetero_tail_strong','hetero_tail_extreme','hetero_tail_inverse',
 'hetero_state','skew_lognormal','heavy_t3','leverage_tail','symmetric_tail_outlier',
 'binomial80','beta_binomial','zero_inflated_tail','age_cubic','age_sex_interaction',
 'state_quadratic','state_cubic','state_saturating'
]

def hc3_t(y,xr,pred):
 xf=np.c_[xr,pred];b,se,t=ols_hc3_last(y,xf);df=len(y)-xf.shape[1]
 return b,float(student_t.sf(t,df)),float(student_t.cdf(t,df))

def world(rng,sc,effect=0.0):
 age=rng.uniform(60,95,N);sex=rng.integers(0,2,N).astype(float)
 if len(np.unique(sex))<2:sex[:2]=[0,1]
 z=nuisance(age,sex);az=(age-age.mean())/age.std();state=.75*az+.20*sex+rng.normal(scale=.85,size=N)
 latent=.65*state+.20*az+rng.normal(scale=.85,size=N);mu=logistic(-2.65+.60*latent)
 if sc=='binomial80':tail=rng.binomial(80,mu)/80
 elif sc=='beta_binomial':
  conc=18;pp=rng.beta(np.maximum(mu*conc,.2),np.maximum((1-mu)*conc,.2));tail=rng.binomial(80,pp)/80
 elif sc=='zero_inflated_tail':
  tail=mu.copy();tail[rng.random(N)<.30]=0
 else:tail=mu
 sz=(state-state.mean())/state.std();my=2+.03*(age-age.mean())+.0018*(age-age.mean())**2+.22*sex+1.25*state
 if sc=='age_cubic':my+=.00045*(age-age.mean())**3
 if sc=='age_sex_interaction':my+=.08*(age-age.mean())*sex
 if sc=='state_quadratic':my+=.65*(sz*sz-np.mean(sz*sz))
 if sc=='state_cubic':my+=.35*(sz**3-np.mean(sz**3))
 if sc=='state_saturating':my+=1.2*np.tanh(1.2*sz)-1.2*sz
 if effect:
  tz=(tail-tail.mean())/(tail.std()+1e-12);my+=effect*tz
 if sc in {'homo_normal','binomial80','beta_binomial','zero_inflated_tail','age_cubic','age_sex_interaction','state_quadratic','state_cubic','state_saturating'}:e=rng.normal(size=N)
 elif sc=='hetero_tail_mild':
  tz=(tail-tail.mean())/(tail.std()+1e-12);e=rng.normal(scale=np.exp(.30*tz),size=N)
 elif sc=='hetero_tail_strong':
  tz=(tail-tail.mean())/(tail.std()+1e-12);e=rng.normal(scale=np.exp(.60*tz),size=N)
 elif sc=='hetero_tail_extreme':
  tz=(tail-tail.mean())/(tail.std()+1e-12);e=rng.normal(scale=np.exp(.85*tz),size=N)
 elif sc=='hetero_tail_inverse':
  tz=(tail-tail.mean())/(tail.std()+1e-12);e=rng.normal(scale=np.exp(-.65*tz),size=N)
 elif sc=='hetero_state':e=rng.normal(scale=np.exp(.40*sz),size=N)
 elif sc=='skew_lognormal':e=rng.lognormal(0,.75,N)-np.exp(.75**2/2)
 elif sc=='heavy_t3':e=rng.standard_t(3,N)/np.sqrt(3)
 elif sc=='leverage_tail':
  e=rng.normal(size=N);tail=tail.copy();tail[np.argmax(age)]=min(1.0,max(.75,float(tail.max()+.35)))
 elif sc=='symmetric_tail_outlier':
  e=rng.normal(size=N);idx=int(np.argmax(tail));e[idx]+=rng.choice([-1.,1.])*5.0
 else:raise ValueError(sc)
 y=my+e;y-=min(0,float(y.min()));return y,np.c_[z,state],tail

def validate(worlds,seed):
 rows=[]
 for si,sc in enumerate(SCENARIOS):
  rng=np.random.default_rng(seed+si*100003);pos=neg=est=0
  for _ in range(worlds):
   y,xr,tail=world(rng,sc)
   try:b,pu,pl=hc3_t(y,xr,tail)
   except NotEstimableError:continue
   est+=1;pos+=bool(b>0 and pu<=POS);neg+=bool(b<0 and pl<=NEG)
  rows.append({'scenario':sc,'worlds':worlds,'estimable':est,'positive_false_support_rate':pos/max(1,est),'negative_false_disqualify_rate':neg/max(1,est),'combined_false_terminal_rate':(pos+neg)/max(1,est)})
 return rows

def power(worlds,seed,effects=(.6,.9,1.2,1.5,2.0)):
 rows=[];scs=['homo_normal','hetero_tail_mild','hetero_tail_strong','skew_lognormal']
 for ei,eff in enumerate(effects):
  for si,sc in enumerate(scs):
   rng=np.random.default_rng(seed+ei*1000003+si*100003);hit=est=0
   for _ in range(worlds):
    y,xr,tail=world(rng,sc,eff)
    try:b,pu,pl=hc3_t(y,xr,tail)
    except NotEstimableError:continue
    est+=1;hit+=bool(b>0 and pu<=POS)
   rows.append({'effect':eff,'scenario':sc,'worlds':worlds,'estimable':est,'power':hit/max(1,est)})
 return rows

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out-prefix',required=True);ap.add_argument('--worlds',type=int,default=5000);ap.add_argument('--power-worlds',type=int,default=2000);ap.add_argument('--seed',type=int,default=99117001);a=ap.parse_args()
 nr=validate(a.worlds,a.seed);pr=power(a.power_worlds,a.seed+70000000)
 for suf,rows in [('null.csv',nr),('power.csv',pr)]:
  p=Path(a.out_prefix+'_'+suf);p.parent.mkdir(parents=True,exist_ok=True)
  with p.open('w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 worst=max(r['combined_false_terminal_rate'] for r in nr);wpos=max(r['positive_false_support_rate'] for r in nr)
 s={'schema':'t0-tail-n17-hc3-t-independent-validation-v2','n':N,'positive_alpha':POS,'negative_alpha':NEG,'seed':a.seed,'worlds_per_null':a.worlds,'power_worlds':a.power_worlds,'acceptance':{'worst_combined_max':.045,'worst_positive_max':.035},'worst_combined':worst,'worst_positive':wpos,'pass':bool(worst<=.045 and wpos<=.035),'null':nr,'power':pr}
 Path(a.out_prefix+'_summary.json').write_text(json.dumps(s,sort_keys=True,separators=(',',':'))+'\n');print(json.dumps(s,indent=2))
if __name__=='__main__':main()
