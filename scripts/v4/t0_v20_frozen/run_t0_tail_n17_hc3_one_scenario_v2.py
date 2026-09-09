from __future__ import annotations
import argparse,json
from pathlib import Path
import numpy as np
from t0_tail_n17_hc3_t_independent_validation_v2 import world,hc3_t,POS,NEG
from t0_studentized_fl_v1 import NotEstimableError
ap=argparse.ArgumentParser();ap.add_argument('--scenario',required=True);ap.add_argument('--worlds',type=int,required=True);ap.add_argument('--seed',type=int,required=True);ap.add_argument('--output',required=True);a=ap.parse_args()
rng=np.random.default_rng(a.seed);pos=neg=est=0
for _ in range(a.worlds):
    y,xr,tail=world(rng,a.scenario)
    try:b,pu,pl=hc3_t(y,xr,tail)
    except NotEstimableError:continue
    est+=1;pos+=bool(b>0 and pu<=POS);neg+=bool(b<0 and pl<=NEG)
r={'scenario':a.scenario,'worlds':a.worlds,'estimable':est,'positive_false_support_rate':pos/max(1,est),'negative_false_disqualify_rate':neg/max(1,est),'combined_false_terminal_rate':(pos+neg)/max(1,est)}
Path(a.output).write_text(json.dumps(r,sort_keys=True,separators=(',',':'))+'\n');print(r)
