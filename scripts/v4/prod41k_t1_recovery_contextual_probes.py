#!/usr/bin/env python3
"""Frozen donor-heldout probes for independently frozen T1 recovery features."""
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path
import numpy as np, pandas as pd
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import balanced_accuracy_score, f1_score, r2_score, average_precision_score, roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT=Path(__file__).resolve().parents[2]; OUT=ROOT/'exports/prod41k_t1_contextual_recovery_v1'
sys.path.insert(0,str(ROOT/'scripts/v4'));sys.path.insert(0,str(ROOT/'exports/static_context_decomposition_v4_20260821'))
import stage81a3_prod41k_teacher_t1 as t1
from production_train_loader import ProductionTrainLoader

VARIANTS=('raw','address_residual','source_residual','operator_residual'); MODES=('rich_H','partial_H')
PARTITIONS=('reader_validation','reader_oracle')
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()

def continuous_metrics(y,p,fit_mean):
 mse=float(np.square(y-p).mean()); baseline=float(np.square(y-fit_mean).mean())
 yc=y-fit_mean;pc=p-fit_mean;den=np.linalg.norm(yc,axis=1)*np.linalg.norm(pc,axis=1) if y.ndim==2 else None
 cosine=float(np.mean(np.sum(yc*pc,axis=1)/np.maximum(den,1e-12))) if y.ndim==2 else np.nan
 return {'r2':float(r2_score(y,p)),'mse':mse,'normalized_mse_fit_mean':mse/baseline if baseline>0 else np.nan,'centered_cosine':cosine}

def main():
 freeze=OUT/'T1_RECOVERY_ANALYSIS_FREEZE.json'; seal=(OUT/'T1_RECOVERY_ANALYSIS_FREEZE_SHA256.txt').read_text()
 if sha(freeze).upper() not in seal:raise RuntimeError('analysis freeze hash seal mismatch')
 residual_path=OUT/'T1_RECOVERY_RESIDUAL_FEATURES.npz'; decomposition=OUT/'T1_RECOVERY_ADDRESS_OPERATOR_DECOMPOSITION.json'
 if not residual_path.exists() or not decomposition.exists():raise RuntimeError('frozen streamed decomposition absent')
 evaluation=t1.load_evaluation(ProductionTrainLoader());meta,values,measured,weights,targets,evidence,control,*_=evaluation
 partitions=meta.reader_partition.astype(str).to_numpy();donors=meta.donor_id.astype(str).to_numpy(); fit=partitions=='reader_fit'
 if fit.sum()!=3163 or np.unique(donors[fit]).size!=104:raise RuntimeError('fit donor firewall drift')
 z=np.load(residual_path,allow_pickle=False); predictions={}; biology=[]
 endpoints=t1.CONTINUOUS+t1.RARE
 for mode in MODES:
  for variant in VARIANTS:
   for endpoint_index,endpoint in enumerate(endpoints):
    kind='continuous' if endpoint in t1.CONTINUOUS else 'rare'; h_index=endpoint_index if kind=='continuous' else t1.CONTINUOUS.index('innovation_tail')
    y=targets[:,endpoint_index] if kind=='continuous' else meta[endpoint].to_numpy(np.int64)
    for update in (0,205):
     h=z[f'u{update:04d}__{mode}__{variant}'][:,h_index]
     x=np.concatenate([h,control],axis=1); p=t1.fit_predictions(kind,x,y,partitions);predictions[(mode,variant,endpoint,update)]=p
    for partition in PARTITIONS:
     take=np.flatnonzero(partitions==partition); p0=predictions[(mode,variant,endpoint,0)][take];p205=predictions[(mode,variant,endpoint,205)][take];yy=y[take]
     estimable=kind=='continuous' or np.unique(yy).size==2
     if endpoint=='recurrent_1pct':ci={'lower':np.nan,'upper':np.nan,'requested':0,'valid':0,'rejected_single_class':0,'valid_fraction':np.nan,'estimable':False,'reason':'descriptive_only'}
     elif estimable:ci=t1.donor_delta_ci(kind,yy,p205,p0,donors[take],t1.EVALUATION_SEED+205+endpoint_index)
     else:ci={'lower':np.nan,'upper':np.nan,'requested':1000,'valid':0,'rejected_single_class':1000,'valid_fraction':0.,'estimable':False,'reason':'single_class'}
     for update,p in ((0,p0),(205,p205)):
      row={'update':update,'evaluation_partition':partition,'evidence_mode':mode,'representation':variant,'endpoint':endpoint,'endpoint_type':kind,
           'scientific_role':'retention_control_only' if mode=='rich_H' and variant=='raw' else ('primary_contextual_teacher_evidence' if mode=='rich_H' and variant in ('address_residual','operator_residual') else 'partial_recovery_or_diagnostic'),
           'cells':len(take),'donors':np.unique(donors[take]).size,'metric':'R2' if kind=='continuous' else 'AP','value':t1.metric(kind,yy,p),
           'u205_minus_u0':t1.metric(kind,yy,p205)-t1.metric(kind,yy,p0) if update==205 else np.nan,
           'donor_bootstrap_delta_lower':ci['lower'] if update==205 else np.nan,'donor_bootstrap_delta_upper':ci['upper'] if update==205 else np.nan,
           'bootstrap_requested':ci['requested'] if update==205 else np.nan,'bootstrap_valid':ci['valid'] if update==205 else np.nan,
           'bootstrap_rejected_single_class':ci['rejected_single_class'] if update==205 else np.nan,'bootstrap_reason':ci['reason'] if update==205 else 'not_applicable'}
      if kind=='rare':
       row.update({'AUROC':float(roc_auc_score(yy,p)) if estimable else np.nan,'positives':int(yy.sum()),'positive_donors':int(np.unique(donors[take][yy==1]).size)})
      biology.append(row)
 biology_frame=pd.DataFrame(biology);biology_frame.to_csv(OUT/'T1_RECOVERY_CONTEXTUAL_BIOLOGY.csv',index=False,lineterminator='\n')

 # Primary partial-H -> contextual-rich-H donor-heldout predictability.
 partial_rows=[]; perm,_=t1.donor_permutation(meta)
 for target_variant in ('address_residual','operator_residual'):
  for input_variant in ('raw',target_variant):
   for endpoint_index,endpoint in enumerate(t1.CONTINUOUS):
    for update in (0,205):
     x=z[f'u{update:04d}__partial_H__{input_variant}'][:,endpoint_index];y=z[f'u{update:04d}__rich_H__{target_variant}'][:,endpoint_index]
     model=make_pipeline(StandardScaler(),Ridge(alpha=10.0)).fit(x[fit],y[fit]);p=model.predict(x);p_shuf=model.predict(x[perm]);fit_mean=y[fit].mean(axis=0)
     for partition in PARTITIONS:
      take=np.flatnonzero(partitions==partition);metrics=continuous_metrics(y[take],p[take],fit_mean);shuf=continuous_metrics(y[take],p_shuf[take],fit_mean)
      partial_rows.append({'update':update,'evaluation_partition':partition,'target_representation':target_variant,'partial_input_representation':input_variant,'endpoint':endpoint,
                           'cells':len(take),'donors':np.unique(donors[take]).size,**metrics,'donor_shuffled_r2':shuf['r2'],'donor_shuffled_normalized_mse':shuf['normalized_mse_fit_mean']})
 partial=pd.DataFrame(partial_rows);partial.to_csv(OUT/'T1_RECOVERY_PARTIAL_CONTEXT_PREDICTABILITY.csv',index=False,lineterminator='\n')

 # Shortcut diagnostics only; frozen 1280-D program-H sensitivity view.
 nuisance=[]
 nuisance_targets={'source':('categorical',meta.study_id.astype(str).to_numpy()),'exact_operator':('categorical',meta.matrix_id.astype(str).to_numpy()),
                   'broad_cell_class':('categorical',meta.broad_cell_class.astype(str).to_numpy()),'measured_scalar_count':('continuous',measured.sum(axis=1).astype(float))}
 for mode in MODES:
  for variant in VARIANTS:
   for update in (0,205):
    x=z[f'u{update:04d}__{mode}__{variant}'].reshape(len(meta),-1)
    for target_name,(kind,y) in nuisance_targets.items():
     if kind=='categorical':model=make_pipeline(StandardScaler(),LogisticRegression(C=1.,class_weight='balanced',max_iter=1000,random_state=t1.EVALUATION_SEED)).fit(x[fit],y[fit])
     else:model=make_pipeline(StandardScaler(),Ridge(alpha=10.)).fit(x[fit],y[fit])
     p=model.predict(x)
     for partition in PARTITIONS:
      take=partitions==partition
      row={'update':update,'evaluation_partition':partition,'evidence_mode':mode,'representation':variant,'target':target_name,'target_type':kind,'cells':int(take.sum()),'donors':np.unique(donors[take]).size,'scientific_role':'shortcut_diagnostic_only'}
      if kind=='categorical':row.update({'metric':'balanced_accuracy','value':float(balanced_accuracy_score(y[take],p[take])),'macro_f1':float(f1_score(y[take],p[take],average='macro'))})
      else:row.update({'metric':'R2','value':float(r2_score(y[take],p[take])),'macro_f1':np.nan})
      nuisance.append(row)
 nuisance_frame=pd.DataFrame(nuisance);nuisance_frame.to_csv(OUT/'T1_RECOVERY_NUISANCE_DECODABILITY.csv',index=False,lineterminator='\n')

 # Frozen primary oracle contextual gain matrix.
 primary=biology_frame[(biology_frame['update']==205)&(biology_frame.evaluation_partition=='reader_oracle')&(biology_frame.evidence_mode=='rich_H')]
 matrix=[]
 for endpoint in endpoints:
  row={'endpoint':endpoint}
  for variant,label in (('raw','RAW'),('address_residual','ADDRESS_RESIDUAL'),('source_residual','SOURCE_RESIDUAL'),('operator_residual','OPERATOR_RESIDUAL')):
   q=primary[(primary.endpoint==endpoint)&(primary.representation==variant)].iloc[0]
   row.update({f'{label}_u0':float(q.value-q.u205_minus_u0),f'{label}_u205':float(q.value),f'{label}_delta':float(q.u205_minus_u0),f'{label}_delta_lower':float(q.donor_bootstrap_delta_lower),f'{label}_delta_upper':float(q.donor_bootstrap_delta_upper)})
  matrix.append(row)
 pd.DataFrame(matrix).to_csv(OUT/'T1_RECOVERY_MASTER_CONTEXTUAL_GAIN_MATRIX.csv',index=False,lineterminator='\n')
 summary={'schema':'t1-recovery-contextual-probes-v1','analysis_freeze_sha256':sha(freeze),'residual_features_sha256':sha(residual_path),'fit_cells':int(fit.sum()),'fit_donors':int(np.unique(donors[fit]).size),'native_class':'NOT_ESTIMABLE_ABSENT_FROM_FROZEN_META','raw_rich_role':'retention_control_only','representation_updates':0}
 (OUT/'T1_RECOVERY_CONTEXTUAL_BIOLOGY.md').write_text('# T1 recovery contextual biology\n\n'+json.dumps(summary,indent=2)+'\n',encoding='utf-8')
 (OUT/'T1_RECOVERY_NUISANCE_DECODABILITY.md').write_text('# T1 recovery nuisance decodability\n\nShortcut diagnostic only. Native class is not estimable from the frozen metadata.\n\n'+json.dumps(summary,indent=2)+'\n',encoding='utf-8')
 (OUT/'T1_RECOVERY_PARTIAL_CONTEXT_PREDICTABILITY.md').write_text('# T1 partial-to-contextual-target predictability\n\nPrimary donor-heldout target-interface evidence under the frozen analysis specification.\n\n'+json.dumps(summary,indent=2)+'\n',encoding='utf-8')
 print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
