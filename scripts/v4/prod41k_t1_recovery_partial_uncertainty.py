#!/usr/bin/env python3
"""Add paired donor uncertainty to frozen partial-to-context readouts."""
from pathlib import Path
import sys,numpy as np,pandas as pd
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'exports/prod41k_t1_contextual_recovery_v1';sys.path.insert(0,str(ROOT/'scripts/v4'));sys.path.insert(0,str(ROOT/'exports/static_context_decomposition_v4_20260821'))
import stage81a3_prod41k_teacher_t1 as t1
from production_train_loader import ProductionTrainLoader
evaluation=t1.load_evaluation(ProductionTrainLoader());meta=evaluation[0];partitions=meta.reader_partition.astype(str).to_numpy();donors=meta.donor_id.astype(str).to_numpy();fit=partitions=='reader_fit';z=np.load(OUT/'T1_RECOVERY_RESIDUAL_FEATURES.npz',allow_pickle=False);frame=pd.read_csv(OUT/'T1_RECOVERY_PARTIAL_CONTEXT_PREDICTABILITY.csv')
for target_variant in ('address_residual','operator_residual'):
 for input_variant in ('raw',target_variant):
  for ei,endpoint in enumerate(t1.CONTINUOUS):
   pred={};target={};means={}
   for u in (0,205):
    x=z[f'u{u:04d}__partial_H__{input_variant}'][:,ei];target[u]=z[f'u{u:04d}__rich_H__{target_variant}'][:,ei];model=make_pipeline(StandardScaler(),Ridge(alpha=10.)).fit(x[fit],target[u][fit]);pred[u]=model.predict(x);means[u]=target[u][fit].mean(0)
   for partition in ('reader_validation','reader_oracle'):
    ds=np.unique(donors[partitions==partition]);delta=[]
    for d in ds:
     take=(partitions==partition)&(donors==d);scores=[]
     for u in (0,205):
      mse=np.square(target[u][take]-pred[u][take]).mean();base=np.square(target[u][take]-means[u]).mean();scores.append(-mse/base if base>0 else np.nan)
     delta.append(scores[1]-scores[0])
    delta=np.asarray(delta,float);rng=np.random.default_rng(t1.EVALUATION_SEED+ei);boot=np.asarray([np.nanmean(rng.choice(delta,len(delta),replace=True)) for _ in range(1000)])
    take=(frame['update'].eq(205)&frame.evaluation_partition.eq(partition)&frame.target_representation.eq(target_variant)&frame.partial_input_representation.eq(input_variant)&frame.endpoint.eq(endpoint))
    frame.loc[take,'u205_minus_u0_donor_mean_negative_nmse']=float(np.nanmean(delta));frame.loc[take,'donor_bootstrap_delta_lower']=float(np.nanquantile(boot,.025));frame.loc[take,'donor_bootstrap_delta_upper']=float(np.nanquantile(boot,.975));frame.loc[take,'bootstrap_requested']=1000;frame.loc[take,'bootstrap_valid']=int(np.isfinite(boot).sum())
frame.to_csv(OUT/'T1_RECOVERY_PARTIAL_CONTEXT_PREDICTABILITY.csv',index=False,lineterminator='\n')
print('paired donor uncertainty added')
