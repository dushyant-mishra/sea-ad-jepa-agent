#!/usr/bin/env python3
"""Read-only teacher-shortcut probes and H address/operator decomposition."""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np, pandas as pd
from sklearn.linear_model import Ridge, RidgeClassifier, LogisticRegression
from sklearn.metrics import average_precision_score, balanced_accuracy_score, r2_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT=Path(__file__).resolve().parents[2]; OUT=ROOT/'exports/foundation_corpus_discovery_v1'; T1=ROOT/'exports/prod41k_teacher_t1_20260823'; RUN=T1/'t1_run'
CONTINUOUS=('broad_common','weak_distributed','local','local_core','local_halo','core_halo','sparse_marker_like','innovation_tail')

def fit_eval(kind,x,y,fit,test):
 if kind=='continuous':
  model=make_pipeline(StandardScaler(),Ridge(alpha=10.0)).fit(x[fit],y[fit]); pred=model.predict(x[test]); return r2_score(y[test],pred)
 if kind=='rare':
  if np.unique(y[fit]).size<2 or np.unique(y[test]).size<2:return np.nan
  model=make_pipeline(StandardScaler(),LogisticRegression(C=1,class_weight='balanced',solver='liblinear',max_iter=2000,random_state=20260824)).fit(x[fit],y[fit]); return average_precision_score(y[test],model.predict_proba(x[test])[:,1])
 model=make_pipeline(StandardScaler(),RidgeClassifier(alpha=10)).fit(x[fit],y[fit]); return balanced_accuracy_score(y[test],model.predict(x[test]))

def decomposition(checkpoint,variant,h,operators):
 x=np.asarray(h,float); global_mean=x.mean(axis=(0,1),keepdims=True); sst=np.square(x-global_mean).sum()
 b=x.mean(axis=0,keepdims=True); sse_b=np.square(x-b).sum(); bo=np.empty_like(x)
 for op in np.unique(operators):
  take=operators==op; bo[take]=x[take].mean(axis=0,keepdims=True)
 sse_bo=np.square(x-bo).sum()
 return {'checkpoint':checkpoint,'representation':variant,'cells':len(x),'addresses_or_program_slots':x.shape[1],
  'address_only_explained_variance':1-sse_b/sst,'operator_incremental_explained_variance':(sse_b-sse_bo)/sst,
  'address_plus_operator_explained_variance':1-sse_bo/sst,'residual_variance_fraction':sse_bo/sst}

def main():
 meta=pd.read_csv(OUT/'FOUNDATION_AUTHENTICATED_T1_EVALUATION_META.csv'); aux=np.load(OUT/'FOUNDATION_AUTHENTICATED_T1_EVALUATION_AUX.npz',allow_pickle=False)
 u0=np.load(RUN/'u0_evaluation_features.npz',allow_pickle=False); u205=np.load(OUT/'FOUNDATION_AUTHENTICATED_T1_U205_FEATURES.npz',allow_pickle=False)
 fit=meta.reader_partition.astype(str).eq('reader_fit').to_numpy(); test=~fit
 source=meta.study_id.astype(str).to_numpy(); operator=meta.matrix_id.astype(str).to_numpy(); broad=meta.broad_cell_class.astype(str).to_numpy()
 measured_count={r.matrix_id:int(r.measured_scalar_addresses) for r in pd.read_csv(OUT/'FOUNDATION_SUPPORT_BY_OPERATOR.csv').itertuples()} if (OUT/'FOUNDATION_SUPPORT_BY_OPERATOR.csv').exists() else {}
 support=np.asarray([measured_count.get(x,0) for x in operator],float)
 targets=aux['continuous_targets']; rows=[]
 for checkpoint,store in [('u0',u0),('u205',u205)]:
  reps={'rich_H':store['rich_H'].reshape(len(meta),-1),'partial_H':store['partial_H'].reshape(len(meta),-1),'rich_CELL':store['rich_CELL'],'partial_CELL':store['partial_CELL']}
  for rep,x in reps.items():
   for name,kind,y in [('source','class',source),('operator','class',operator),('support_measured_count','continuous',support),('broad_annotation','class',broad)]:
    rows.append({'checkpoint':checkpoint,'representation':rep,'target':name,'target_type':kind,'evaluation':'45 heldout TRAIN donors','metric':'R2' if kind=='continuous' else 'balanced_accuracy','value':fit_eval(kind,x,y,fit,test),'fit_donors':meta.loc[fit,'donor_id'].nunique(),'evaluation_donors':meta.loc[test,'donor_id'].nunique()})
   for j,name in enumerate(CONTINUOUS): rows.append({'checkpoint':checkpoint,'representation':rep,'target':name,'target_type':'continuous','evaluation':'45 heldout TRAIN donors','metric':'R2','value':fit_eval('continuous',x,targets[:,j],fit,test),'fit_donors':meta.loc[fit,'donor_id'].nunique(),'evaluation_donors':meta.loc[test,'donor_id'].nunique()})
   for name,column in (('rare5','recurrent_5pct'),('rare1','recurrent_1pct')):
    if column in meta: rows.append({'checkpoint':checkpoint,'representation':rep,'target':name,'target_type':'rare','evaluation':'45 heldout TRAIN donors; rare1 descriptive','metric':'average_precision','value':fit_eval('rare',x,meta[column].to_numpy(int),fit,test),'fit_donors':meta.loc[fit,'donor_id'].nunique(),'evaluation_donors':meta.loc[test,'donor_id'].nunique()})
 frame=pd.DataFrame(rows); delta=frame.pivot_table(index=['representation','target','target_type','metric'],columns='checkpoint',values='value').reset_index(); delta['u205_minus_u0']=delta.get('u205')-delta.get('u0')
 frame=frame.merge(delta[['representation','target','u205_minus_u0']],on=['representation','target'],how='left')
 frame.to_csv(OUT/'FOUNDATION_TEACHER_SHORTCUT_ATLAS.csv',index=False,lineterminator='\n')
 dec=[]
 for c,s in [('u0',u0),('u205',u205)]:
  for v in ('rich_H','partial_H'): dec.append(decomposition(c,v,s[v],operator))
 pd.DataFrame(dec).to_csv(OUT/'FOUNDATION_H_ADDRESS_OPERATOR_DECOMPOSITION.csv',index=False,lineterminator='\n')
 # Reuse prospectively frozen T1 readouts as ceiling comparators; no new endpoint design.
 bio=pd.read_csv(RUN/'t1_biology_metrics_u0205.csv'); ceiling=bio[bio.arm.isin(['lawful_RNA_predictive_baseline','exact_full_RNA_oracle'])].copy(); ceiling.to_csv(OUT/'FOUNDATION_PARTIAL_EVIDENCE_CEILING.csv',index=False,lineterminator='\n')
 nuisance=delta[delta.target.isin(['source','operator','support_measured_count'])]; biology=delta[delta.target.isin(CONTINUOUS)]
 md=f"""# FOUNDATION teacher shortcut atlas

All probes fit on the frozen 104 encoder-fit TRAIN donors and evaluate only on the existing 45 heldout TRAIN donors. They are fixed-capacity descriptive readers, not success thresholds. Native annotation is not present in the authenticated 4,540-cell T1 evaluation authority and is therefore not invented.

Median u0-to-u205 change for source/operator/support targets was **{nuisance.u205_minus_u0.median():.4g}**; median change across frozen continuous biology was **{biology.u205_minus_u0.median():.4g}**. See the CSV for each rich H, partial H, and CELL arm. Rare1 remains descriptive.

The H decomposition reports static address centroids, operator-conditioned incremental variance, and residual cell-varying variance separately for rich and partial H. These are descriptive variance partitions; they do not modify H or authorize a residual target.

The partial-evidence ceiling table republishes the prospectively frozen u205 lawful-RNA comparator and exact-full-RNA oracle. No model or reader capacity was changed.
"""
 (OUT/'FOUNDATION_TEACHER_SHORTCUT_ATLAS.md').write_text(md,encoding='utf-8')
 print(json.dumps({'probe_rows':len(frame),'decomposition_rows':len(dec),'heldout_donors':int(meta.loc[test,'donor_id'].nunique())},indent=2))
if __name__=='__main__':main()
