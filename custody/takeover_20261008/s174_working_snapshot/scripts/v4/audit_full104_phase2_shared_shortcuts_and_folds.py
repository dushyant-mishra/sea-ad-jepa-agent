#!/usr/bin/env python3
"""Nonselecting observation-shortcut and donor-fold audit for frozen shared D."""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, math, os
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('shared_impl',ROOT/'scripts/v4/derive_full104_phase2_shared_state.py'); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()
def atomic(p,v):
 t=p.with_suffix(p.suffix+'.tmp'); t.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n',encoding='utf-8'); os.replace(t,p)
def moments(x,donor_slices):
 n=len(donor_slices); d=x.shape[-1]; mean=np.empty((n,d)); within=np.empty((n,d,d)); between=np.empty((n,d,d))
 for i,s in enumerate(donor_slices):
  z=np.asarray(x[s],np.float64); cells=len(z); mean[i]=z.mean(axis=(0,1)); w=np.zeros((d,d)); b=np.zeros((d,d))
  for v in range(4): w+=z[:,v].T@z[:,v]
  for v in range(4):
   for q in range(4):
    if v!=q:b+=z[:,v].T@z[:,q]
  within[i]=w/(cells*4); between[i]=b/(cells*12)
 return mean,within,between
def weighted_group_r2(scores,groups,weights):
 mu=np.average(scores,axis=0,weights=weights); total=float(np.sum(weights[:,None]*(scores-mu)**2)); pred=np.empty_like(scores)
 for g in sorted(set(groups)):
  take=np.asarray(groups)==g; pred[take]=np.average(scores[take],axis=0,weights=weights[take])
 return 1-float(np.sum(weights[:,None]*(scores-pred)**2))/max(total,np.finfo(float).eps)
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--matrix',required=True); ap.add_argument('--analytic',required=True); ap.add_argument('--empirical',required=True); ap.add_argument('--dimension',type=int,required=True); ap.add_argument('--out',required=True); a=ap.parse_args(); matrix=Path(a.matrix).resolve(); analytic=Path(a.analytic).resolve(); empirical=Path(a.empirical).resolve(); out=Path(a.out).resolve(); out.mkdir(parents=True,exist_ok=True); D=a.dimension
 rows=pd.read_csv(matrix/'PHASE2_FEATURE_ROWS.csv',dtype={'donor_id':str}); donors=sorted(rows.donor_id.unique()); slices=[]
 for d in donors:
  ix=np.flatnonzero(rows.donor_id.to_numpy()==d); assert np.array_equal(ix,np.arange(ix[0],ix[-1]+1)); slices.append(slice(ix[0],ix[-1]+1))
 folds=pd.read_csv(matrix.parent/'preexpression_freeze/PHASE2_DONOR_FOLDS.csv',dtype={'donor_id':str}).set_index('donor_id'); donor_folds=np.asarray([int(folds.loc[d,'outer_fold']) for d in donors])
 fold_rows=[]
 for fold in sorted(set(donor_folds)):
  for role,take in [('train',donor_folds!=fold),('held',donor_folds==fold)]:
   subset=set(np.asarray(donors)[take]); r=rows[rows.donor_id.isin(subset)]
   for source,g in r.groupby('source'): fold_rows.append({'fold':fold,'role':role,'scope':'source','key':source,'donors':g.donor_id.nunique(),'cells':len(g)})
   for op,g in r.groupby('operator_index'): fold_rows.append({'fold':fold,'role':role,'scope':'operator','key':str(op),'donors':g.donor_id.nunique(),'cells':len(g)})
 fold_table=pd.DataFrame(fold_rows); fold_table.to_csv(out/'SHARED_DONOR_FOLD_COVERAGE.csv',index=False,lineterminator='\n')
 absent=[]
 for fold in sorted(set(donor_folds)):
  tr=set(rows.loc[rows.donor_id.isin(set(np.asarray(donors)[donor_folds!=fold])),'operator_index']); he=set(rows.loc[rows.donor_id.isin(set(np.asarray(donors)[donor_folds==fold])),'operator_index'])
  for op in sorted(he-tr):absent.append({'fold':fold,'operator_index':op,'classification':'OPERATOR_UNSEEN_TRANSFER_STRESS'})
 pd.DataFrame(absent,columns=['fold','operator_index','classification']).to_csv(out/'SHARED_OPERATOR_UNSEEN_TRANSFER_STRESS.csv',index=False,lineterminator='\n')
 observed=pd.read_csv(analytic/'SHARED_DONOR_HELDOUT_PREDICTABILITY.csv'); full=observed[observed.dimension.eq(D)].pivot(index='donor_index',columns='sketch',values='heldout_predictability').mean(axis=1)
 donor_metrics=[]; bases={}
 for label in 'AB':
  x=np.load(matrix/f'{label}_views.npy',mmap_mode='r')
  for channel,sl in [('VALUE_ONLY',slice(0,256)),('VISIBILITY_OR_SUPPORT_ONLY',slice(256,512))]:
   mean,within,between=moments(x[:,:,sl],slices); basis=mod.fit_basis(mean,within,between,np.arange(len(donors)),D); bases[(label,channel)]=basis
   held=mod.heldout_scores(mean,within,between,between,donor_folds,[D],D)
   for r in held.itertuples(index=False):donor_metrics.append({'donor_index':r.donor_index,'donor_id':donors[r.donor_index],'sketch':label,'channel':channel,'held_donor_predictability':r.heldout_predictability})
 dm=pd.DataFrame(donor_metrics); dm.to_csv(out/'SHARED_OBSERVATION_SHORTCUT_DONOR_METRICS.csv',index=False,lineterminator='\n')
 summary=[]
 for channel,g in dm.groupby('channel'):
  paired=g.pivot(index='donor_index',columns='sketch',values='held_donor_predictability').mean(axis=1); common=full.index.intersection(paired.index); delta=(full.loc[common]-paired.loc[common]).to_numpy(); se=float(delta.std(ddof=1)/math.sqrt(len(delta)))
  summary.append({'channel':channel,'held_donor_predictability_mean':float(paired.mean()),'full_value_plus_visibility_mean':float(full.mean()),'full_minus_channel_paired_donor_mean':float(delta.mean()),'full_minus_channel_paired_donor_se':se,'full_exceeds_channel_by_one_donor_se':bool(delta.mean()-se>0),'selection_role':'NONSELECTING_SHORTCUT_FALSIFICATION'})
 # Descriptive source/operator centroid R2 on donor-equal donor×operator means.
 st=pd.read_csv(analytic/'sufficient_statistics/DONOR_OPERATOR_STRATA.csv',dtype={'donor_id':str}); weights=st.groupby('donor_index').size().map(lambda n:1/(len(donors)*n)); rw=np.asarray([weights[x] for x in st.donor_index]); score={}
 for label in 'AB':
  basis=np.load(analytic/f'SHARED_OVERCOMPLETE_BASIS_{label}.npz'); means=np.load(analytic/f'sufficient_statistics/{label}_stratum_mean.npy',mmap_mode='r'); score[label]=(np.asarray(means)-basis['mean'])@basis['components'][:,:D]
 aw=score['A']*np.sqrt(rw[:,None]); bw=score['B']*np.sqrt(rw[:,None]); u,s,v=np.linalg.svd(bw.T@aw,full_matrices=False); rot=u@v; combined=(score['A']+score['B']@rot)/2
 source_map=rows.groupby('donor_id').source.first().to_dict(); sources=np.asarray([source_map[x] for x in st.donor_id]); shortcut={'source_centroid_weighted_R2':weighted_group_r2(combined,sources,rw),'operator_centroid_weighted_R2':weighted_group_r2(combined,st.operator_index.to_numpy(),rw)}
 status='PASS_SHORTCUT_FALSIFIED' if next(x for x in summary if x['channel']=='VISIBILITY_OR_SUPPORT_ONLY')['full_exceeds_channel_by_one_donor_se'] else 'CONCERN_VISIBILITY_SHORTCUT_NOT_FALSIFIED'
 result={'schema':'full104-shared-observation-shortcut-audit-v1','status':status,'dimension':D,'channels':summary,'descriptive_candidate_coordinate_decodability':shortcut,'operator_unseen_fold_rows':len(absent),'folds':len(set(donor_folds)),'donors':len(donors),'cells':len(rows),'selection_role':'NONSELECTING_DIAGNOSTIC_WITH_CATASTROPHIC_SHORTCUT_VETO_ONLY','no_biology_labels_or_protected_data':True,'input_hashes':{'matrix_manifest':sha(matrix/'PHASE2_FEATURE_MATRIX_MANIFEST.csv'),'analytic_manifest':sha(analytic/f'SHARED_LEVEL1_ANALYTIC_DIAGNOSTIC_MANIFEST.csv'),'empirical_selection':sha(empirical/'SHARED_DIMENSION_SELECTION_LEVEL.json')}}
 atomic(out/'PHASE2_SHARED_OBSERVATION_SHORTCUT_AUDIT.json',result); pd.DataFrame(summary).to_csv(out/'PHASE2_SHARED_OBSERVATION_SHORTCUT_AUDIT.csv',index=False,lineterminator='\n')
 manifest=out/'SHARED_SHORTCUT_FOLD_AUDIT_MANIFEST.csv'; fs=[out/'PHASE2_SHARED_OBSERVATION_SHORTCUT_AUDIT.json',out/'PHASE2_SHARED_OBSERVATION_SHORTCUT_AUDIT.csv',out/'SHARED_OBSERVATION_SHORTCUT_DONOR_METRICS.csv',out/'SHARED_DONOR_FOLD_COVERAGE.csv',out/'SHARED_OPERATOR_UNSEEN_TRANSFER_STRESS.csv',Path(__file__)]; pd.DataFrame([{'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p)} for p in fs]).to_csv(manifest,index=False,lineterminator='\n'); (out.parent/'SHARED_SHORTCUT_FOLD_AUDIT_MANIFEST_SHA256.txt').write_text(sha(manifest)+'\n',encoding='ascii'); print(json.dumps({**result,'manifest_sha256':sha(manifest)},indent=2))
if __name__=='__main__':main()
