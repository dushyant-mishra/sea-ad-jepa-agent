from __future__ import annotations
import argparse,json
from pathlib import Path
from t0_tail_n17_engine_comparison_v2 import run_null
ap=argparse.ArgumentParser(); ap.add_argument('--scenario',required=True); ap.add_argument('--worlds',type=int,default=240); ap.add_argument('--seed',type=int,required=True); ap.add_argument('--output',required=True); a=ap.parse_args()
r=run_null([a.scenario],a.worlds,.02,.005,a.seed)[0]
Path(a.output).write_text(json.dumps(r,sort_keys=True,separators=(',',':'))+'\n')
print(a.scenario,r['fl_combined_rate'],r['wild_combined_rate'])
