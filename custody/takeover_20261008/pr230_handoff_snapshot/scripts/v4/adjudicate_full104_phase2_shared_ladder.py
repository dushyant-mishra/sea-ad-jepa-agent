#!/usr/bin/env python3
"""Prospective successive-level/shared-ladder convergence adjudicator."""
from __future__ import annotations
import argparse, hashlib, json, math, os
from pathlib import Path
import numpy as np
import pandas as pd

def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(8<<20),b''): h.update(b)
 return h.hexdigest()
def atomic(p,v):
 t=p.with_suffix(p.suffix+'.tmp'); t.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n',encoding='utf-8'); os.replace(t,p)
def basis_overlap(pa,pb,d):
 a=np.load(pa)['components'][:,:d]; b=np.load(pb)['components'][:,:d]; qa=np.linalg.qr(a,mode='reduced')[0]; qb=np.linalg.qr(b,mode='reduced')[0]
 return float(np.square(qa.T@qb).sum()/d)
def paired_curve(analytic):
 x=pd.read_csv(analytic/'SHARED_DONOR_HELDOUT_PREDICTABILITY.csv'); p=x.pivot_table(index=['donor_index','dimension'],columns='sketch',values='heldout_predictability').reset_index(); p['paired']=(p.A+p.B)/2; return p
def main():
 raise RuntimeError("SUPERSEDED_DO_NOT_USE: use adjudicate_full104_phase2_shared_ladder_refit.py with the repaired contiguous-prefix selection chain")
 ap=argparse.ArgumentParser(); ap.add_argument('--previous-empirical'); ap.add_argument('--previous-analytic'); ap.add_argument('--current-empirical',required=True); ap.add_argument('--current-analytic',required=True); ap.add_argument('--out',required=True); a=ap.parse_args()
 ce=Path(a.current_empirical).resolve(); ca=Path(a.current_analytic).resolve(); out=Path(a.out).resolve(); out.mkdir(parents=True,exist_ok=True)
 current=json.loads((ce/'SHARED_DIMENSION_SELECTION_LEVEL.json').read_text()); level=int(current['sample_level']); candidate=current['candidate_D_shared']; boundary=bool(current['search_boundary_supported']); final_level=level==4
 comparison=None; stable=False
 if a.previous_empirical and a.previous_analytic:
  pe=Path(a.previous_empirical).resolve(); pa=Path(a.previous_analytic).resolve(); previous=json.loads((pe/'SHARED_DIMENSION_SELECTION_LEVEL.json').read_text()); pc=previous['candidate_D_shared']
  if pc is not None and candidate is not None and not boundary and not previous['search_boundary_supported']:
   pi=previous['one_se_dimension_interval']; ci=current['one_se_dimension_interval']; intervals_overlap=max(pi[0],ci[0])<=min(pi[1],ci[1]); d=max(int(pc),int(candidate))
   overlaps={}; no_subspace_loss=True
   for label in 'AB':
    overlaps[label]=basis_overlap(pa/f'SHARED_OVERCOMPLETE_BASIS_{label}.npz',ca/f'SHARED_OVERCOMPLETE_BASIS_{label}.npz',d)
    pb=np.load(pa/f'SHARED_BOOTSTRAP_{label}.npz'); cb=np.load(ca/f'SHARED_BOOTSTRAP_{label}.npz'); ps=pb['observed_stability'][:,d-1]; cs=cb['observed_stability'][:,d-1]
    floor=min(float(ps.mean()-ps.std(ddof=1)/math.sqrt(len(ps))),float(cs.mean()-cs.std(ddof=1)/math.sqrt(len(cs))))
    no_subspace_loss &= overlaps[label]>=floor; overlaps[label+'_one_se_floor']=floor
   pp=paired_curve(pa); cp=paired_curve(ca); pv=pp[pp.dimension.eq(int(pc))].set_index('donor_index').paired; cv=cp[cp.dimension.eq(int(candidate))].set_index('donor_index').paired; common=pv.index.intersection(cv.index); delta=(cv.loc[common]-pv.loc[common]).to_numpy(); current_mean=float(cv.loc[common].mean()); current_se=float(cv.loc[common].std(ddof=1)/math.sqrt(len(common))); previous_mean=float(pv.loc[common].mean()); predictability_saturated=previous_mean>=current_mean-current_se
   stable=bool(intervals_overlap and no_subspace_loss and predictability_saturated)
   comparison={'previous_level':int(previous['sample_level']),'current_level':level,'previous_candidate_D':int(pc),'current_candidate_D':int(candidate),'dimension_intervals_overlap':bool(intervals_overlap),'comparison_dimension':d,'principal_angle_subspace_overlap':overlaps,'no_material_subspace_loss':bool(no_subspace_loss),'previous_paired_heldout_predictability':previous_mean,'current_paired_heldout_predictability':current_mean,'current_donor_se':current_se,'previous_within_one_current_donor_se':bool(predictability_saturated),'paired_donor_delta_mean':float(delta.mean()),'paired_donor_delta_se':float(delta.std(ddof=1)/math.sqrt(len(delta))),'successive_level_stable':stable}
 if final_level:
  if candidate is None: status='TEACHER_BIOLOGY_LIMIT'
  elif boundary: status='STOP_PHASE2_AUDIT_REQUIRED'
  else: status='SHARED_STATE_CANDIDATE_FINAL_AT_FULL104'
 elif stable: status='SHARED_STATE_CANDIDATE_CONVERGED'
 else: status='ADVANCE_LADDER'
 result={'schema':'full104-shared-ladder-adjudication-v1','status':status,'current_level':level,'candidate_D_shared':candidate,'successive_level_converged':stable,'reached_full104':final_level,'next_level_required':status=='ADVANCE_LADDER','terminal_shared_candidate_available':status in {'SHARED_STATE_CANDIDATE_CONVERGED','SHARED_STATE_CANDIDATE_FINAL_AT_FULL104'},'comparison':comparison,'selection_input_sha256':sha(ce/'SHARED_DIMENSION_SELECTION_LEVEL.json'),'code_sha256':sha(Path(__file__)),'no_private_or_training_work':True}
 atomic(out/'PHASE2_SHARED_SAMPLE_LADDER_ADJUDICATION.json',result)
 pd.DataFrame([{'level':level,'cells':current['cells'],'donors':current['donors'],'operators':current['operators'],'candidate_D_shared':candidate,'one_se_interval':str(current['one_se_dimension_interval']),'boundary':boundary,'status':status,'next_level_required':result['next_level_required']}]).to_csv(out/'PHASE2_SHARED_SAMPLE_LADDER_ADJUDICATION.csv',index=False,lineterminator='\n')
 manifest=out/'PHASE2_SHARED_LADDER_ADJUDICATION_MANIFEST.csv'; fs=[out/'PHASE2_SHARED_SAMPLE_LADDER_ADJUDICATION.json',out/'PHASE2_SHARED_SAMPLE_LADDER_ADJUDICATION.csv',Path(__file__)]; pd.DataFrame([{'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p)} for p in fs]).to_csv(manifest,index=False,lineterminator='\n'); (out.parent/f'SHARED_LEVEL{level}_LADDER_ADJUDICATION_MANIFEST_SHA256.txt').write_text(sha(manifest)+'\n',encoding='ascii')
 print(json.dumps({**result,'manifest_sha256':sha(manifest)},indent=2))
if __name__=='__main__': main()
