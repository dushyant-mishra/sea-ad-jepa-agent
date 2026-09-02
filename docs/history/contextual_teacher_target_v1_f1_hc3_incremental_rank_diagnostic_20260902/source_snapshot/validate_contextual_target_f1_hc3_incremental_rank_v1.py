#!/usr/bin/env python3
"""Independent validation of the Command-15A3 reproduction mismatch."""
from __future__ import annotations
import argparse,json
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];UP=ROOT/'outputs/contextual_teacher_target_v1_f1_nuisance_authority_recovery_20260902';EPS=np.finfo(np.float64).eps
def rnk(x):
 s=np.linalg.svd(x,compute_uv=False);return int(np.sum(s>max(x.shape)*EPS*s[0]))
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--package',type=Path,required=True);a=ap.parse_args();o=a.package;s=json.loads((UP/'F1_NUISANCE_COLUMN_SCHEMA.json').read_text());M=np.fromfile(UP/'F1_NUISANCE_DONOR_DESIGN_F64LE.bin',dtype='<f8').reshape(104,49);cols=s['columns'];names=['source_HVS','source_NPH52','source_SEA_AD','recipient_physical_support','recipient_depth','correct_minus_null_visible_depth','correct_minus_null_measured_zero_rate'];x=np.ones((104,1));kept=[]
 for q in sorted(names):
  v=M[:,cols.index(q)];c=np.column_stack([x,v-v.mean()])
  if rnk(c)>rnk(x):x=c;kept.append(q)
 prior=json.loads((o/'F1_HC3_MANDATORY_BASE.json').read_text());observed=rnk(x);checks={"independent_rank":observed,"constructed_columns":x.shape[1],"retained_columns":kept,"matches_production":observed==prior['rank'] and x.shape[1]==prior['constructed_column_count'],"matches_15A":observed==prior['prior_15A_rank'],"matches_15A2":observed==prior['prior_15A2_rank'],"matches_command_required_8":observed==8,"production_helpers_imported":False,"forbidden_data_access":False};terminal='STOP_F1_HC3_INCREMENTAL_RANK_REPRODUCTION_MISMATCH' if checks['matches_production'] and checks['matches_15A'] and checks['matches_15A2'] and not checks['matches_command_required_8'] else 'STOP_F1_HC3_INCREMENTAL_INDEPENDENT_MISMATCH';report={"terminal_status":terminal,"checks":checks};(o/'F1_HC3_INCREMENTAL_INDEPENDENT_VALIDATION.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n',encoding='utf-8');print(json.dumps(report));raise SystemExit(3)
if __name__=='__main__':main()
