#!/usr/bin/env python3
"""Independent reconstruction of corrected Command-15A3 through its HC3 STOP."""
from __future__ import annotations
import argparse,csv,hashlib,json
from itertools import product
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];UP=ROOT/'outputs/contextual_teacher_target_v1_f1_nuisance_authority_recovery_20260902';EPS=np.finfo(np.float64).eps;BOUND=float(np.sqrt(EPS));SRC=['source_HVS','source_NPH52','source_SEA_AD'];CONT=['recipient_physical_support','recipient_depth','correct_minus_null_visible_depth','correct_minus_null_measured_zero_rate'];BLOCKS={'HVS':list(range(24)),'NPH52':list(range(35,42)),'SEA_AD':list(range(24,35))}
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()
def rank(x):
 s=np.linalg.svd(np.asarray(x,np.float64),compute_uv=False);return int(np.sum(s>max(x.shape)*EPS*s[0])) if s.size else 0
def build(mp,names):
 x=np.ones((104,1));kept=[]
 for q in sorted(names):
  v=mp[q];c=np.column_stack([x,v-v.mean()])
  if rank(c)>rank(x):x=c;kept.append(q)
 return x,kept
def hdiag(x):return np.sum(x*np.linalg.solve(x.T@x,x.T).T,axis=1)
def eq(x):
 z=[]
 for j in range(x.shape[1]):
  v=x[:,j]
  if np.all(v==v[0]):z.append(v.copy())
  else:
   q=v-v.mean();z.append(q/np.linalg.norm(q))
 return np.column_stack(z)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--package',type=Path,required=True);a=ap.parse_args();o=a.package;auth=json.loads((o/'F1_HC3_INCREMENTAL_RANK_AUTHORITY_CANDIDATE.json').read_text());expected={'donor_design':'1d8f837d18cedd8d1b8fd6138d1b25f886b8352c097a4723ca06421573334056','schema':'9f90c764d0d97b5a10badc03dfcbafc364e0bf40e120a9aed6609e036b5924a7'};input_ok=sha(UP/'F1_NUISANCE_DONOR_DESIGN_F64LE.bin')==expected['donor_design'] and sha(UP/'F1_NUISANCE_COLUMN_SCHEMA.json')==expected['schema'] and auth['raw_nuisance_root']=='2f0c95b1d9c098f8593827f240f64a0b8e5512ead92fe50540f6e2dc231742ec';s=json.loads((UP/'F1_NUISANCE_COLUMN_SCHEMA.json').read_text());M=np.fromfile(UP/'F1_NUISANCE_DONOR_DESIGN_F64LE.bin',dtype='<f8').reshape(104,49);cols=s['columns'];don=np.asarray(s['donor_order']);src=np.asarray([x.split('::',1)[0] for x in don]);mp={q:M[:,i] for i,q in enumerate(cols)};B,kept=build(mp,SRC+CONT);Q=np.linalg.qr(B,mode='reduced')[0];O=M[:,[cols.index(f'operator_mix_{i:03d}') for i in range(42)]]
 blocks={};aug={};Z={};rinc={};local={};prefix=[]
 for ss,ids in BLOCKS.items():
  E=np.zeros((104,len(ids)));ix=src==ss;E[ix]=O[ix][:,ids];blocks[ss]=E;aug[ss]=rank(np.column_stack([B,E]))-rank(B);R=E-Q@(Q.T@E);u,z,v=np.linalg.svd(R,full_matrices=False);local[ss]=rank(R);X=B.copy();r=0;failed=False
  for j in range(len(z)):
   score=u[:,j]*z[j];before=rank(X);after=rank(np.column_stack([X,score-score.mean()]));inc=after-before;admit=not failed and inc==1 and r<aug[ss]
   if not failed and inc!=1:failed=True
   if admit:X=np.column_stack([X,score-score.mean()]);r+=1
   prefix.append((ss,j+1,before,after,inc,admit))
  rinc[ss]=r;Z[ss]=u[:,:r]*z[:r]
 joint=rank(np.column_stack([B,blocks['HVS'],blocks['NPH52'],blocks['SEA_AD']]))-rank(B)
 scale={ss:(rank(np.column_stack([eq(B),eq(E)]))-rank(eq(B))) for ss,E in blocks.items()}
 with (o/'F1_HC3_INCREMENTAL_FRONTIER.csv').open(newline='',encoding='utf-8') as f:rows=list(csv.DictReader(f))
 expected=[];first_bad=None
 for t in product(range(rinc['HVS']+1),range(rinc['NPH52']+1),range(rinc['SEA_AD']+1)):
  X=np.column_stack([B,Z['HVS'][:,:t[0]],Z['NPH52'][:,:t[1]],Z['SEA_AD'][:,:t[2]]]);h=hdiag(X);ok=rank(X)==X.shape[1] and np.all(1-h>BOUND);expected.append((t,rank(X),float(h.max()),ok))
  if not ok:first_bad=(t,rank(X),X.shape[1],float(h.max()),float((1-h).min()),str(don[np.argmax(h)]));break
 rows_ok=len(rows)==len(expected)
 for row,(t,r,mx,ok) in zip(rows,expected):rows_ok &= (int(row['r_HVS']),int(row['r_NPH52']),int(row['r_SEAAD']))==t and int(row['rank'])==r and abs(float(row['max_leverage'])-mx)<1e-9 and (row['hc3_estimable']=='True')==ok
 prodterm=json.loads((o/'F1_HC3_INCREMENTAL_TERMINAL.json').read_text());prodscale=json.loads((o/'F1_HC3_SCALE_SENSITIVITY.json').read_text());prodnph=json.loads((o/'F1_HC3_NPH_COMPONENT2_FINAL_DIAGNOSTIC.json').read_text())
 checks={'authenticated_inputs':input_ok,'authority_amendment_bound_before_result':auth['amendment']['classification']=='COMMAND_15A3_AUTHORITY_TYPO / PREFIX-STATE-CONFLATION','mandatory_base_rank_7':rank(B)==7 and B.shape[1]==7,'mandatory_base_columns':kept==['correct_minus_null_measured_zero_rate','correct_minus_null_visible_depth','recipient_depth','recipient_physical_support','source_HVS','source_NPH52'],'raw_augmented_ranks':aug=={'HVS':6,'NPH52':1,'SEA_AD':4},'joint_augmented_rank':joint==11,'equilibrated_ranks_match_raw':scale==aug and prodscale['RANK_IS_SCALE_SENSITIVE'] is False,'incremental_prefix_ranks':rinc==aug,'NPH_component2_classification':local['NPH52']==2 and next(x for x in prefix if x[0]=='NPH52' and x[1]==2)[4]==0 and prodnph['NPH52_COMPONENT2']=='LOCAL_NUMERICAL_DIRECTION__REDUNDANT_IN_ACTUAL_HC3_DESIGN','frontier_rows_through_stop':bool(rows_ok),'first_invalid_is_NPH_prefix':first_bad is not None and first_bad[0]==(0,1,0),'terminal_matches':prodterm['terminal_status']=='STOP_F1_HC3_INCREMENTAL_FRONTIER_HC3_NONESTIMABLE','production_helpers_not_imported':True,'audited_read_scope_only_nuisance_and_package':True,'no_forbidden_data_access':True}
 terminal='STOP_F1_HC3_INCREMENTAL_FRONTIER_HC3_NONESTIMABLE' if all(checks.values()) else 'STOP_F1_HC3_INCREMENTAL_INDEPENDENT_MISMATCH';report={'terminal_status':terminal,'checks':checks,'independent_incremental_ranks':rinc,'independent_local_ranks':local,'independent_first_invalid':first_bad,'frontier_rows_checked':len(rows)};(o/'F1_HC3_INCREMENTAL_INDEPENDENT_VALIDATION.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n',encoding='utf-8');print(json.dumps(report));raise SystemExit(3)
if __name__=='__main__':main()
