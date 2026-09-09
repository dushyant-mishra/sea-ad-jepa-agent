from __future__ import annotations
import argparse,csv,json
from pathlib import Path
import numpy as np
from scipy.stats import t as student_t
from t0_studentized_fl_v1 import ols_hc3_last,NotEstimableError
from t0_tail_n17_engine_comparison_v2 import N,NULL_SCENARIOS,generate_world

def hc3_t_test(y,xr,pred):
    xf=np.c_[xr,pred]
    b,se,t=ols_hc3_last(y,xf); df=len(y)-xf.shape[1]
    return {'beta':b,'hc3_se':se,'t_observed':t,'df':df,'p_upper':float(student_t.sf(t,df)),'p_lower':float(student_t.cdf(t,df))}

def run(worlds,seed_base,pos=.02,neg=.005):
    rows=[]
    for si,sc in enumerate(NULL_SCENARIOS):
        rng=np.random.default_rng(seed_base+si*100003); posn=negn=est=0
        for _ in range(worlds):
            y,xr,tail=generate_world(rng,sc,0.0)
            try:r=hc3_t_test(y,xr,tail)
            except NotEstimableError:continue
            est+=1;posn+=bool(r['beta']>0 and r['p_upper']<=pos);negn+=bool(r['beta']<0 and r['p_lower']<=neg)
        d=max(1,est);rows.append({'scenario':sc,'worlds':worlds,'estimable':est,'positive_false_support_rate':posn/d,'negative_false_disqualify_rate':negn/d,'combined_false_terminal_rate':(posn+negn)/d})
    return rows

def power(worlds,seed_base,effects=(.35,.6,.9),pos=.02):
    scs=['homo_normal','hetero_tail_mild','hetero_tail_strong','skew_lognormal'];rows=[]
    for ei,effect in enumerate(effects):
      for si,sc in enumerate(scs):
        rng=np.random.default_rng(seed_base+ei*1000003+si*100003);hit=est=0
        for _ in range(worlds):
          y,xr,tail=generate_world(rng,sc,effect)
          try:r=hc3_t_test(y,xr,tail)
          except NotEstimableError:continue
          est+=1;hit+=bool(r['beta']>0 and r['p_upper']<=pos)
        rows.append({'effect':effect,'scenario':sc,'worlds':worlds,'estimable':est,'power':hit/max(1,est)})
    return rows

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out-prefix',required=True);ap.add_argument('--worlds',type=int,default=2000);ap.add_argument('--power-worlds',type=int,default=1000);ap.add_argument('--seed-base',type=int,default=77117001);a=ap.parse_args()
 nr=run(a.worlds,a.seed_base);pr=power(a.power_worlds,a.seed_base+70000000)
 for suf,rows in [('null.csv',nr),('power.csv',pr)]:
  p=Path(a.out_prefix+'_'+suf);p.parent.mkdir(parents=True,exist_ok=True)
  with p.open('w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 s={'schema':'t0-tail-n17-hc3-t-calibration-v1','n':N,'positive_alpha':.02,'negative_alpha':.005,'seed_base':a.seed_base,'worlds_per_null':a.worlds,'power_worlds':a.power_worlds,'worst_false_terminal':max(r['combined_false_terminal_rate'] for r in nr),'null':nr,'power':pr}
 Path(a.out_prefix+'_summary.json').write_text(json.dumps(s,sort_keys=True,separators=(',',':'))+'\n');print(json.dumps(s,indent=2))
if __name__=='__main__':main()
