from __future__ import annotations
import argparse,json
from pathlib import Path
import numpy as np
from scipy.stats import t as student_t
from t0_studentized_fl_v1 import ols_hc3_last,NotEstimableError

POS=.020;NEG=.005

def nuisance(age,sex):
 c=float(np.mean(age));a=age-c;return np.c_[np.ones(len(age)),a,a*a,sex]
def logistic(x):return 1/(1+np.exp(-x))
def world(rng,sc,n):
 age=rng.uniform(60,95,n);sex=rng.integers(0,2,n).astype(float)
 if len(np.unique(sex))<2:sex[:2]=[0,1]
 z=nuisance(age,sex);az=(age-age.mean())/age.std();state=.75*az+.20*sex+rng.normal(scale=.85,size=n)
 latent=.65*state+.20*az+rng.normal(scale=.85,size=n);mu=logistic(-2.65+.60*latent)
 if sc=='binomial80':tail=rng.binomial(80,mu)/80
 elif sc=='beta_binomial':
  conc=18;pp=rng.beta(np.maximum(mu*conc,.2),np.maximum((1-mu)*conc,.2));tail=rng.binomial(80,pp)/80
 elif sc=='zero_inflated_tail':tail=mu.copy();tail[rng.random(n)<.30]=0
 else:tail=mu
 sz=(state-state.mean())/state.std();my=2+.03*(age-age.mean())+.0018*(age-age.mean())**2+.22*sex+1.25*state
 if sc=='age_cubic':my+=.00045*(age-age.mean())**3
 if sc=='age_sex_interaction':my+=.08*(age-age.mean())*sex
 if sc=='state_quadratic':my+=.65*(sz*sz-np.mean(sz*sz))
 if sc=='state_cubic':my+=.35*(sz**3-np.mean(sz**3))
 if sc=='state_saturating':my+=1.2*np.tanh(1.2*sz)-1.2*sz
 if sc in {'homo_normal','binomial80','beta_binomial','zero_inflated_tail','age_cubic','age_sex_interaction','state_quadratic','state_cubic','state_saturating'}:e=rng.normal(size=n)
 elif sc=='hetero_tail_mild':
  tz=(tail-tail.mean())/(tail.std()+1e-12);e=rng.normal(scale=np.exp(.30*tz),size=n)
 elif sc=='hetero_tail_strong':
  tz=(tail-tail.mean())/(tail.std()+1e-12);e=rng.normal(scale=np.exp(.60*tz),size=n)
 elif sc=='hetero_tail_extreme':
  tz=(tail-tail.mean())/(tail.std()+1e-12);e=rng.normal(scale=np.exp(.85*tz),size=n)
 elif sc=='hetero_tail_inverse':
  tz=(tail-tail.mean())/(tail.std()+1e-12);e=rng.normal(scale=np.exp(-.65*tz),size=n)
 elif sc=='hetero_state':e=rng.normal(scale=np.exp(.40*sz),size=n)
 elif sc=='skew_lognormal':e=rng.lognormal(0,.75,n)-np.exp(.75**2/2)
 elif sc=='heavy_t3':e=rng.standard_t(3,n)/np.sqrt(3)
 elif sc=='leverage_tail':
  e=rng.normal(size=n);tail=tail.copy();tail[np.argmax(age)]=min(1.0,max(.75,float(tail.max()+.35)))
 elif sc=='symmetric_tail_outlier':
  e=rng.normal(size=n);idx=int(np.argmax(tail));e[idx]+=rng.choice([-1.,1.])*5.0
 else:raise ValueError(sc)
 y=my+e;y-=min(0,float(y.min()));return y,np.c_[z,state],tail

def test_one(n,sc,worlds,seed):
 rng=np.random.default_rng(seed);pos=neg=est=0
 for _ in range(worlds):
  y,xr,tail=world(rng,sc,n);xf=np.c_[xr,tail]
  try:b,se,t=ols_hc3_last(y,xf)
  except NotEstimableError:continue
  df=n-xf.shape[1];pu=student_t.sf(t,df);pl=student_t.cdf(t,df);est+=1;pos+=bool(b>0 and pu<=POS);neg+=bool(b<0 and pl<=NEG)
 return {'n':n,'scenario':sc,'worlds':worlds,'estimable':est,'positive_false_support_rate':pos/max(1,est),'negative_false_disqualify_rate':neg/max(1,est),'combined_false_terminal_rate':(pos+neg)/max(1,est)}

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--n',type=int,required=True);ap.add_argument('--scenario',required=True);ap.add_argument('--worlds',type=int,required=True);ap.add_argument('--seed',type=int,required=True);ap.add_argument('--output',required=True);a=ap.parse_args();r=test_one(a.n,a.scenario,a.worlds,a.seed);Path(a.output).write_text(json.dumps(r,sort_keys=True,separators=(',',':'))+'\n');print(r)
