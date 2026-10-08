#!/usr/bin/env python3
"""Corrected Command-15A3 incremental full-design rank diagnostic."""
from __future__ import annotations
import argparse,csv,hashlib,json
from itertools import product
from pathlib import Path
import numpy as np
from scipy import linalg
ROOT=Path(__file__).resolve().parents[2];UP=ROOT/'outputs/contextual_teacher_target_v1_f1_nuisance_authority_recovery_20260902';A15=ROOT/'outputs/contextual_teacher_target_v1_f1_hc3_geometry_diagnostic_20260902';A152=ROOT/'outputs/contextual_teacher_target_v1_f1_hc3_geometry_diagnostic_numrank_repair_20260902';A153STOP=ROOT/'outputs/contextual_teacher_target_v1_f1_hc3_incremental_rank_diagnostic_20260902';ENGINE=ROOT/'scripts/v4/contextual_target_f1_decision_v1.py';EPS=np.finfo(np.float64).eps;BOUND=float(np.sqrt(EPS));BASIS_TOL=100*104*EPS
SRC=['source_HVS','source_NPH52','source_SEA_AD'];CONT=['recipient_physical_support','recipient_depth','correct_minus_null_visible_depth','correct_minus_null_measured_zero_rate'];OPS=[f'operator_mix_{i:03d}' for i in range(42)];BLOCKS={'HVS':list(range(24)),'NPH52':list(range(35,42)),'SEA_AD':list(range(24,35))}
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()
def dump(p,x):p.write_text(json.dumps(x,indent=2,sort_keys=True,allow_nan=False)+'\n',encoding='utf-8')
def rank(x):
 x=np.asarray(x,np.float64);s=np.linalg.svd(x,compute_uv=False);return int(np.sum(s>max(x.shape)*EPS*s[0])) if s.size else 0
def rank_detail(x):
 s=np.linalg.svd(x,compute_uv=False);t=float(max(x.shape)*EPS*s[0]);return {'shape':list(x.shape),'rank':rank(x),'tau':t,'singular_values':s.tolist(),'s_over_tau':(s/t).tolist()}
def select(mp,names):
 x=np.ones((len(next(iter(mp.values()))),1));kept=[]
 for q in sorted(names):
  v=mp[q];c=np.column_stack([x,v-v.mean()])
  if rank(c)>rank(x):x=c;kept.append(q)
 return x,kept
def hdiag(x):return np.einsum('ij,jk,ik->i',x,np.linalg.inv(x.T@x),x)
def orient(u,v):
 u=u.copy();v=v.copy()
 for j in range(v.shape[0]):
  m=int(np.flatnonzero(np.abs(v[j])==np.max(np.abs(v[j])))[0])
  if v[j,m]<0:u[:,j]*=-1;v[j]*=-1
 return u,v
def geom(x,donors,sources):
 k=rank(x);h=hdiag(x);s=np.linalg.svd(x,compute_uv=False);loss=[k-rank(np.delete(x,i,axis=0)) for i in range(len(x))]
 return {'rank':k,'constructed_columns':x.shape[1],'df':len(x)-k,'n_over_k':len(x)/k,'max_leverage':float(h.max()),'max_leverage_donor':str(donors[int(np.argmax(h))]),'max_leverage_by_source':{q:float(h[sources==q].max()) for q in ['HVS','NPH52','SEA_AD']},'min_one_minus_h':float((1-h).min()),'hc3_estimable':bool(k==x.shape[1] and len(x)-k>0 and np.isfinite(h).all() and np.all(1-h>BOUND)),'above_2k_over_n_count':int(np.sum(h>2*k/len(x))),'above_3k_over_n_count':int(np.sum(h>3*k/len(x))),'loo_rank_stable':max(loss)==0,'worst_loo_rank_loss':int(max(loss)),'loo_rank_loss':dict(zip(map(str,donors),map(int,loss))),'condition_number':float(s[0]/s[k-1]),'smallest_design_singular_value':float(s[k-1])}
def equilibrate(cols):
 out=[]
 for j in range(cols.shape[1]):
  v=cols[:,j]
  if np.all(v==v[0]):out.append(v.copy())
  else:
   z=v-v.mean();n=np.linalg.norm(z);out.append(z/n if n else z)
 return np.column_stack(out)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();o=a.out;o.mkdir(parents=True,exist_ok=False)
 expected={A15/'F1_HC3_MANIFEST.csv':'1bb7010e0268fe99f3c0ea952a05d6818466fa0e54734fc15f3a2c2be5406230',A152/'F1_HC3_NUMRANK_MANIFEST.csv':'9b9434eb5056f80964a49843a1e75d9c85392d2dca230932ae6e4c61a7832973',A153STOP/'F1_HC3_INCREMENTAL_MANIFEST.csv':'4afcf03909dc01ceabef76ef4c7918288d1cc675facf153eebcfec53851b4ed3',UP/'F1_NUISANCE_DONOR_DESIGN_F64LE.bin':'1d8f837d18cedd8d1b8fd6138d1b25f886b8352c097a4723ca06421573334056',UP/'F1_NUISANCE_COLUMN_SCHEMA.json':'9f90c764d0d97b5a10badc03dfcbafc364e0bf40e120a9aed6609e036b5924a7',ENGINE:'204859f48b96d1bb268d9249596b801537f2c911183dc4a20bc30fe5683e2d34'};actual={str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in expected};assert all(sha(p)==h for p,h in expected.items())
 schema=json.loads((UP/'F1_NUISANCE_COLUMN_SCHEMA.json').read_text());auth=json.loads((UP/'F1_NUISANCE_DONOR_DESIGN_AUTHORITY.json').read_text());assert auth['semantic_root_sha256']=='2f0c95b1d9c098f8593827f240f64a0b8e5512ead92fe50540f6e2dc231742ec';M=np.fromfile(UP/'F1_NUISANCE_DONOR_DESIGN_F64LE.bin',dtype='<f8').reshape(104,49);cols=schema['columns'];donors=np.asarray(schema['donor_order']);sources=np.asarray([x.split('::',1)[0] for x in donors]);mp={q:M[:,i] for i,q in enumerate(cols)}
 old,_=select(mp,cols);oh=hdiag(old);bad=[str(donors[i]) for i in np.flatnonzero(1-oh<=BOUND)];B,bkeep=select(mp,SRC+CONT);bg=geom(B,donors,sources)
 if rank(old)!=18 or bad!=['HVS::H20.06.354','NPH52::human_NPH_906'] or bg['rank']!=7 or not bg['hc3_estimable']:raise RuntimeError('STOP_F1_HC3_INCREMENTAL_RANK_REPRODUCTION_MISMATCH')
 amendment={'classification':'COMMAND_15A3_AUTHORITY_TYPO / PREFIX-STATE-CONFLATION','corrected_reproduction':{'mandatory_B_rank':7,'mandatory_B_df':97,'B_plus_NPH_C1_rank':8,'B_plus_NPH_C1_plus_C2_rank':8},'scientific_machinery_changed':False}
 authority={'status':'CORRECTED_AUTHORITY_PASS','input_sha256':actual,'raw_nuisance_root':auth['semantic_root_sha256'],'amendment':amendment,'basis_invariance_tolerance_formula':'100*n*float64_eps','basis_invariance_tolerance':BASIS_TOL,'candidate_only':True,'design_selected_or_frozen':False,'firewall':{'expression':False,'model_checkpoint_or_forward':False,'outcomes':False,'training_or_ema':False}};dump(o/'F1_HC3_INCREMENTAL_RANK_AUTHORITY_CANDIDATE.json',authority)
 centered={q:float(np.linalg.norm(mp[q]-mp[q].mean())) for q in SRC+CONT};dump(o/'F1_HC3_MANDATORY_BASE.json',{'requested_columns':SRC+CONT,'retained_columns':bkeep,'centered_l2_norms':centered,'rank_detail':rank_detail(B),'geometry':bg})
 O=M[:,[cols.index(q) for q in OPS]];blocks={};aug={};BQR=linalg.qr(B,mode='economic')[0]
 for ss,ids in BLOCKS.items():
  e=np.zeros((104,len(ids)));ix=sources==ss;e[ix]=O[ix][:,ids];blocks[ss]=e;aug[ss]={'operator_indices':ids,'raw_augmented_incremental_rank':rank(np.column_stack([B,e]))-rank(B),'augmented_rank_detail':rank_detail(np.column_stack([B,e]))}
 joint=np.column_stack([B,blocks['HVS'],blocks['NPH52'],blocks['SEA_AD']]);aug['ALL']={'raw_augmented_incremental_rank':rank(joint)-rank(B),'augmented_rank_detail':rank_detail(joint),'sum_source_incremental_ranks':sum(aug[q]['raw_augmented_incremental_rank'] for q in BLOCKS)};assert aug['ALL']['raw_augmented_incremental_rank']<=aug['ALL']['sum_source_incremental_ranks'];dump(o/'F1_HC3_RAW_AUGMENTED_RANK.json',aug)
 # Equilibrated comparator only.
 Beq=equilibrate(B);scale={'production_columns_standardized':False,'report_only':True,'sources':{}}
 for ss,e in blocks.items():
  ee=equilibrate(e);raw=aug[ss]['raw_augmented_incremental_rank'];eq=rank(np.column_stack([Beq,ee]))-rank(Beq);scale['sources'][ss]={'raw_incremental_rank':raw,'equilibrated_incremental_rank':eq,'RANK_IS_SCALE_SENSITIVE':raw!=eq,'equilibrated_augmented_rank_detail':rank_detail(np.column_stack([Beq,ee]))}
 scale['RANK_IS_SCALE_SENSITIVE']=any(x['RANK_IS_SCALE_SENSITIVE'] for x in scale['sources'].values());dump(o/'F1_HC3_SCALE_SENSITIVITY.json',scale)
 ordering={};emb={};trace=[];rinc={}
 for ss,e in blocks.items():
  R=e-BQR@(BQR.T@e);u,s,vh=np.linalg.svd(R,full_matrices=False);u,vh=orient(u,vh);local=rank(R);rawaug=aug[ss]['raw_augmented_incremental_rank'];X=B.copy();accepted=[];failed=False;directions=[]
  for j in range(len(s)):
   score=u[:,j]*s[j];before=rank(X);after=rank(np.column_stack([X,score-score.mean()]));inc=after-before;above=bool(s[j]>max(R.shape)*EPS*s[0]);admit=bool(not failed and inc==1 and len(accepted)<rawaug)
   if not failed and inc!=1:failed=True
   if admit:X=np.column_stack([X,score-score.mean()]);accepted.append(j)
   cls='ADMISSIBLE_FULL_DESIGN_INCREMENT' if admit else ('LOCAL_NONZERO__FULL_DESIGN_REDUNDANT' if above else 'LOCAL_NUMERICAL_NULL')
   trace.append({'source':ss,'component':j+1,'singular_value':float(s[j]),'local_tau':float(max(R.shape)*EPS*s[0]),'local_tau_ratio':float(s[j]/(max(R.shape)*EPS*s[0])),'rank_before':before,'rank_after':after,'rank_increment':inc,'classification':cls,'admitted_prefix':admit})
   directions.append({'component':j+1,'singular_value':float(s[j]),'local_tau_ratio':float(s[j]/(max(R.shape)*EPS*s[0])),'loading':vh[j].tolist(),'score_l2_norm':float(np.linalg.norm(score)),'classification':cls})
  rinc[ss]=len(accepted)
  if rinc[ss]!=rawaug:raise RuntimeError('STOP_F1_HC3_SVD_PREFIX_DOES_NOT_SPAN_INCREMENTAL_RANK')
  emb[ss]={'scores':u[:,:rinc[ss]]*s[:rinc[ss]],'unit':u[:,:rinc[ss]],'singular':s,'residual':R}
  ordering[ss]={'operator_indices':BLOCKS[ss],'residual_rank_local':local,'raw_augmented_incremental_rank':rawaug,'admissible_prefix_length':rinc[ss],'residual_rank_detail':rank_detail(R),'B_transpose_R_max_abs':float(np.max(np.abs(BQR.T@R))),'directions':directions}
 dump(o/'F1_HC3_RESIDUAL_SVD_ORDERING.json',ordering)
 with (o/'F1_HC3_PREFIX_INCREMENT_TRACE.csv').open('w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=list(trace[0]));w.writeheader();w.writerows(trace)
 nph2=next(x for x in trace if x['source']=='NPH52' and x['component']==2);nph={'RESIDUAL_LOCAL_RANK':ordering['NPH52']['residual_rank_local'],'RAW_AUGMENTED_INCREMENTAL_RANK':aug['NPH52']['raw_augmented_incremental_rank'],'component2_full_design_rank_increment':nph2['rank_increment'],'NPH52_COMPONENT2':'LOCAL_NUMERICAL_DIRECTION__REDUNDANT_IN_ACTUAL_HC3_DESIGN'};assert nph=={'RESIDUAL_LOCAL_RANK':2,'RAW_AUGMENTED_INCREMENTAL_RANK':1,'component2_full_design_rank_increment':0,'NPH52_COMPONENT2':'LOCAL_NUMERICAL_DIRECTION__REDUNDANT_IN_ACTUAL_HC3_DESIGN'};dump(o/'F1_HC3_NPH_COMPONENT2_FINAL_DIAGNOSTIC.json',nph)
 # Basis/scaling invariance across source and combined prefixes.
 inv={'tolerance':BASIS_TOL,'source_prefixes':[],'combined_frontier':[],'SCALE_SENSITIVE_NUMERICAL_GATE':False};front=[];loo={}
 for ss in BLOCKS:
  for r in range(rinc[ss]+1):
   xa=np.column_stack([B,emb[ss]['scores'][:,:r]]);xb=np.column_stack([B,emb[ss]['unit'][:,:r]]);ra,rb=rank(xa),rank(xb);diff=float(np.max(np.abs(hdiag(xa)-hdiag(xb))));inv['source_prefixes'].append({'source':ss,'r':r,'rank_scores':ra,'rank_unit':rb,'max_hat_abs_difference':diff,'pass':bool(ra==rb==xa.shape[1] and diff<=BASIS_TOL)});inv['SCALE_SENSITIVE_NUMERICAL_GATE']=bool(inv['SCALE_SENSITIVE_NUMERICAL_GATE'] or ra!=rb)
 terminal=None;failure=None
 for rh,rn,rs in product(range(rinc['HVS']+1),range(rinc['NPH52']+1),range(rinc['SEA_AD']+1)):
  xa=np.column_stack([B,emb['HVS']['scores'][:,:rh],emb['NPH52']['scores'][:,:rn],emb['SEA_AD']['scores'][:,:rs]]);xb=np.column_stack([B,emb['HVS']['unit'][:,:rh],emb['NPH52']['unit'][:,:rn],emb['SEA_AD']['unit'][:,:rs]]);g=geom(xa,donors,sources)
  diff=float(np.max(np.abs(hdiag(xa)-hdiag(xb))));rmatch=rank(xa)==rank(xb)==xa.shape[1];inv['combined_frontier'].append({'r_HVS':rh,'r_NPH52':rn,'r_SEAAD':rs,'rank_scores':rank(xa),'rank_unit':rank(xb),'max_hat_abs_difference':diff,'pass':bool(rmatch and diff<=BASIS_TOL)});inv['SCALE_SENSITIVE_NUMERICAL_GATE']=bool(inv['SCALE_SENSITIVE_NUMERICAL_GATE'] or rank(xa)!=rank(xb))
  if diff>BASIS_TOL and rmatch:raise RuntimeError('STOP_F1_HC3_BASIS_INVARIANCE_FAILURE')
  ev=[]
  for q,r in [('HVS',rh),('NPH52',rn),('SEA_AD',rs)]:
   s=emb[q]['singular'];ev.append(float(np.sum(s[:r]**2)/np.sum(s**2)) if r else 0.)
  front.append({'r_HVS':rh,'r_NPH52':rn,'r_SEAAD':rs,'rank':g['rank'],'constructed_columns':g['constructed_columns'],'df':g['df'],'n_over_k':g['n_over_k'],'HVS_variance_explained':ev[0],'NPH52_variance_explained':ev[1],'SEA_AD_variance_explained':ev[2],'equal_source_mean_variance_explained':float(np.mean(ev)),'minimum_source_variance_explained':float(np.min(ev)),'max_leverage':g['max_leverage'],'max_leverage_HVS':g['max_leverage_by_source']['HVS'],'max_leverage_NPH52':g['max_leverage_by_source']['NPH52'],'max_leverage_SEA_AD':g['max_leverage_by_source']['SEA_AD'],'max_leverage_donor':g['max_leverage_donor'],'min_one_minus_h':g['min_one_minus_h'],'hc3_estimable':g['hc3_estimable'],'above_2k_over_n_count':g['above_2k_over_n_count'],'above_3k_over_n_count':g['above_3k_over_n_count'],'loo_rank_stable':g['loo_rank_stable'],'worst_loo_rank_loss':g['worst_loo_rank_loss'],'condition_number':g['condition_number'],'smallest_design_singular_value':g['smallest_design_singular_value']});loo[f'{rh},{rn},{rs}']=g['loo_rank_loss']
  if g['constructed_columns']!=g['rank']:
   terminal='STOP_F1_HC3_REPAIRED_FRONTIER_RANK_DEFICIENT';failure={'triple':[rh,rn,rs],**g};break
  if not g['hc3_estimable']:
   terminal='STOP_F1_HC3_INCREMENTAL_FRONTIER_HC3_NONESTIMABLE';failure={'triple':[rh,rn,rs],**g};break
 dump(o/'F1_HC3_BASIS_SCALING_INVARIANCE.json',inv);dump(o/'F1_HC3_LOO_STABILITY.json',{'diagnostic_only':True,'frontier_rank_loss_by_donor':loo})
 with (o/'F1_HC3_INCREMENTAL_FRONTIER.csv').open('w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=list(front[0]));w.writeheader();w.writerows(front)
 dump(o/'F1_HC3_INCREMENTAL_TERMINAL.json',{'terminal_status':terminal or 'DERIVATION_PASS','first_invalid_frontier_candidate':failure,'frontier_complete':terminal is None,'design_selected_or_frozen':False})
 print(json.dumps({'status':terminal or 'DERIVATION_PASS','base_rank':rank(B),'incremental_ranks':rinc,'frontier_rows_evaluated':len(front),'scale_sensitive':scale['RANK_IS_SCALE_SENSITIVE']}))
 if terminal:raise SystemExit(3)
if __name__=='__main__':main()
