#!/usr/bin/env python3
"""Command 15A3 authority/reproduction gate (outcome blind)."""
from __future__ import annotations
import argparse,csv,hashlib,json
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];UP=ROOT/"outputs/contextual_teacher_target_v1_f1_nuisance_authority_recovery_20260902";A15=ROOT/"outputs/contextual_teacher_target_v1_f1_hc3_geometry_diagnostic_20260902";A152=ROOT/"outputs/contextual_teacher_target_v1_f1_hc3_geometry_diagnostic_numrank_repair_20260902";ENGINE=ROOT/"scripts/v4/contextual_target_f1_decision_v1.py";EPS=np.finfo(np.float64).eps;BOUND=float(np.sqrt(EPS))
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()
def rank(x):
 s=np.linalg.svd(np.asarray(x,np.float64),compute_uv=False);return int(np.sum(s>max(x.shape)*EPS*s[0])) if s.size else 0
def select(mp,names,n):
 x=np.ones((n,1));kept=[]
 for q in sorted(names):
  v=mp[q];y=np.column_stack([x,v-v.mean()])
  if rank(y)>rank(x):x=y;kept.append(q)
 return x,kept
def dump(p,x):p.write_text(json.dumps(x,indent=2,sort_keys=True,allow_nan=False)+'\n',encoding='utf-8')
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();o=a.out;o.mkdir(parents=True,exist_ok=False)
 checks={"15A_manifest":sha(A15/'F1_HC3_MANIFEST.csv'),"15A2_manifest":sha(A152/'F1_HC3_NUMRANK_MANIFEST.csv'),"donor_design":sha(UP/'F1_NUISANCE_DONOR_DESIGN_F64LE.bin'),"schema":sha(UP/'F1_NUISANCE_COLUMN_SCHEMA.json'),"engine":sha(ENGINE)}
 expected={"15A_manifest":"1bb7010e0268fe99f3c0ea952a05d6818466fa0e54734fc15f3a2c2be5406230","15A2_manifest":"9b9434eb5056f80964a49843a1e75d9c85392d2dca230932ae6e4c61a7832973","donor_design":"1d8f837d18cedd8d1b8fd6138d1b25f886b8352c097a4723ca06421573334056","schema":"9f90c764d0d97b5a10badc03dfcbafc364e0bf40e120a9aed6609e036b5924a7","engine":"204859f48b96d1bb268d9249596b801537f2c911183dc4a20bc30fe5683e2d34"};assert checks==expected
 s=json.loads((UP/'F1_NUISANCE_COLUMN_SCHEMA.json').read_text());auth=json.loads((UP/'F1_NUISANCE_DONOR_DESIGN_AUTHORITY.json').read_text());assert auth['semantic_root_sha256']=='2f0c95b1d9c098f8593827f240f64a0b8e5512ead92fe50540f6e2dc231742ec';M=np.fromfile(UP/'F1_NUISANCE_DONOR_DESIGN_F64LE.bin',dtype='<f8').reshape(104,49);cols=s['columns'];mp={q:M[:,i] for i,q in enumerate(cols)};donors=np.asarray(s['donor_order'])
 old,keptold=select(mp,cols,104);h=np.einsum('ij,jk,ik->i',old,np.linalg.inv(old.T@old),old);bad=[str(donors[i]) for i in np.flatnonzero(1-h<=BOUND)];oldok=rank(old)==18 and bad==['HVS::H20.06.354','NPH52::human_NPH_906']
 names=['source_HVS','source_NPH52','source_SEA_AD','recipient_physical_support','recipient_depth','correct_minus_null_visible_depth','correct_minus_null_measured_zero_rate'];B,kept=select(mp,names,104);sv=np.linalg.svd(B,compute_uv=False);bh=np.einsum('ij,jk,ik->i',B,np.linalg.inv(B.T@B),B);centered={q:float(np.linalg.norm(mp[q]-mp[q].mean())) for q in names}
 base={"requested_semantic_columns":names,"retained_centered_columns":kept,"intercept_included":True,"centered_l2_norms":centered,"singular_values":sv.tolist(),"rank":rank(B),"df":104-rank(B),"constructed_column_count":B.shape[1],"full_column_rank":rank(B)==B.shape[1],"max_leverage":float(bh.max()),"min_one_minus_h":float((1-bh).min()),"hc3_estimable":bool(np.all(1-bh>BOUND)),"condition_number":float(sv[0]/sv[rank(B)-1]),"prior_15A_rank":json.loads((A15/'F1_HC3_SOURCE_SVD_SPECTRA.json').read_text())['mandatory_base']['geometry']['rank'],"prior_15A2_rank":json.loads((A152/'F1_HC3_NUMRANK_REPAIR_AUTHORITY.json').read_text())['mandatory_base_rank'],"command_15A3_required_reproduction_rank":8,"reproduction_matches_command":rank(B)==8}
 dump(o/'F1_HC3_MANDATORY_BASE.json',base)
 terminal='STOP_F1_HC3_INCREMENTAL_RANK_REPRODUCTION_MISMATCH'
 authority={"terminal_status":terminal,"input_sha256":checks,"raw_nuisance_root":auth['semantic_root_sha256'],"old_design_reproduced":oldok,"old_rank":rank(old),"old_df":104-rank(old),"old_unit_leverage_donors":bad,"mandatory_base_observed_rank":rank(B),"mandatory_base_required_rank_by_command":8,"mismatch":"Command 15A3 requires mandatory base rank 8, while both hash-bound prior packages and exact reconstruction give rank 7 (intercept + 2 source contrasts + 4 continuous nuisances).","candidate_authority_evaluated":False,"design_selected_or_frozen":False,"firewall":{"expression":False,"model_checkpoint_or_forward":False,"outcome":False,"training_or_ema":False}};dump(o/'F1_HC3_INCREMENTAL_RANK_AUTHORITY_CANDIDATE.json',authority)
 placeholders={
 'F1_HC3_RAW_AUGMENTED_RANK.json':{"status":"NOT_RUN_AFTER_REPRODUCTION_STOP"},'F1_HC3_SCALE_SENSITIVITY.json':{"status":"NOT_RUN_AFTER_REPRODUCTION_STOP"},'F1_HC3_RESIDUAL_SVD_ORDERING.json':{"status":"NOT_RUN_AFTER_REPRODUCTION_STOP"},'F1_HC3_NPH_COMPONENT2_FINAL_DIAGNOSTIC.json':{"status":"NOT_RUN_AFTER_REPRODUCTION_STOP"},'F1_HC3_BASIS_SCALING_INVARIANCE.json':{"status":"NOT_RUN_AFTER_REPRODUCTION_STOP"},'F1_HC3_LOO_STABILITY.json':{"status":"NOT_RUN_AFTER_REPRODUCTION_STOP"}}
 for n,x in placeholders.items():dump(o/n,x)
 (o/'F1_HC3_PREFIX_INCREMENT_TRACE.csv').write_text('status,reason\nNOT_RUN,STOP_F1_HC3_INCREMENTAL_RANK_REPRODUCTION_MISMATCH\n',encoding='utf-8');(o/'F1_HC3_INCREMENTAL_FRONTIER.csv').write_text('status,reason\nNOT_RUN,STOP_F1_HC3_INCREMENTAL_RANK_REPRODUCTION_MISMATCH\n',encoding='utf-8')
 print(json.dumps(authority));raise SystemExit(3)
if __name__=='__main__':main()
