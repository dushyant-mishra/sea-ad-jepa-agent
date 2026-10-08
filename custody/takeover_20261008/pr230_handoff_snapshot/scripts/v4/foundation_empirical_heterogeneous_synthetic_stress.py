#!/usr/bin/env python3
"""Matched balanced-vs-empirical synthetic JEPA mechanism stress (not production training)."""
from __future__ import annotations
import hashlib,json,math,sys,time
from pathlib import Path
import numpy as np,pandas as pd,torch
from sklearn.linear_model import Ridge,RidgeClassifier
from sklearn.metrics import r2_score,balanced_accuracy_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'exports/foundation_corpus_discovery_v1';sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'src'));sys.path.insert(0,str(ROOT/'scripts/v4'));sys.path.insert(0,str(ROOT/'exports/static_context_decomposition_v4_20260821'))
import stage81a3_synthetic_geometry_escape as prior
from production_train_loader import ProductionTrainLoader,MEASURED_SCALAR
from sea_ad_jepa.v4 import V4AEncoderSkeleton,LatentPredictor,create_ema_target,ema_target_module,EMAOptimizerStepController,jepa_prediction_loss,construct_context_mask
SEED=2026082411;CELLS=512;GENES=4096;UPDATES=500;EFFECTIVE=128;MICRO=8
def hval(*p):return int.from_bytes(hashlib.sha256('|'.join(map(str,p)).encode()).digest()[:8],'big')
def readout(z,y,kind):
 tr=np.arange(384,448);te=np.arange(448,512)
 if kind=='continuous':
  m=make_pipeline(StandardScaler(),Ridge(alpha=1)).fit(z[tr],y[tr]);return r2_score(y[te],m.predict(z[te]),multioutput='variance_weighted')
 m=make_pipeline(StandardScaler(),RidgeClassifier(alpha=10)).fit(z[tr],y[tr]);return balanced_accuracy_score(y[te],m.predict(z[te]))
@torch.inference_mode()
def features(model,expr,measured,device):
 out=[];model.eval()
 for b in range(0,CELLS,8):
  e=expr[b:b+8].float().to(device);m=measured[b:b+8].to(device);g=torch.arange(GENES,device=device).expand(len(e),-1);out.append(model(g,e,m,torch.zeros_like(m),'target').mean(1).float().cpu())
 return torch.cat(out).numpy()
def assignment(world,operator_probs,operator_source,conditional,all_donors):
 rng=np.random.default_rng(SEED);universe=np.arange(42)
 if world=='BALANCED_REFERENCE':
  ops=np.resize(universe,CELLS);rng.shuffle(ops);donors=np.resize(np.asarray(all_donors,object),CELLS);rng.shuffle(donors)
  native=np.asarray([conditional[int(op)]['native'][i%len(conditional[int(op)]['native'])] for i,op in enumerate(ops)],object)
 else:
  ops=rng.choice(universe,CELLS,p=operator_probs);donors=[];native=[]
  for op in ops:
   c=conditional[int(op)];donors.append(rng.choice(c['donor'],p=c['donor_p']));native.append(rng.choice(c['native'],p=c['native_p']))
 sources=np.asarray([operator_source[int(op)] for op in ops],object);return ops,np.asarray(donors,object),native,sources
def run_world(world,base,factors,states,operator_probs,operator_source,conditional,all_donors,detection,device):
 ops,donors,native,sources=assignment(world,operator_probs,operator_source,conditional,all_donors);measured=torch.from_numpy(states[ops]==1);expr=base.clone();expr[~measured]=0
 # Production-like donor depth and source-confounded technical axes; biology factors are unchanged.
 donor_scale=torch.tensor([.85+.30*((hval('donor',d)%10_000)/10_000) for d in donors],dtype=expr.dtype)[:,None];expr*=donor_scale
 source_code={'HVS':0,'NPH52':1,'SEA_AD':2};axis=torch.ones_like(expr); 
 for s,code in source_code.items():axis[np.asarray(sources)==s,:64]*=(.85+.15*code)
 expr*=axis
 for s,sl,factor in [('HVS',slice(128,192),30),('NPH52',slice(192,256),31)]:
  take=torch.from_numpy(np.asarray(sources)==s);expr[take,sl]+=torch.relu(factors[take,factor,None]).to(expr.dtype)*.15
 keep=torch.tensor([detection[s] for s in sources],dtype=torch.float32)[:,None];rand=torch.rand(expr.shape,generator=torch.Generator().manual_seed(SEED+777));expr[(rand>keep)&(expr>0)]=0
 torch.manual_seed(SEED+99);torch.cuda.manual_seed_all(SEED+99);online=V4AEncoderSkeleton().to(device);predictor=LatentPredictor().to(device);target=create_ema_target(online).to(device);optimizer=torch.optim.AdamW(list(online.parameters())+list(predictor.parameters()),lr=prior.LEARNING_RATE,weight_decay=prior.WEIGHT_DECAY);scaler=torch.amp.GradScaler('cuda');controller=EMAOptimizerStepController(online,target)
 trajectory=[]
 def assess(step,loss=np.nan):
  z=features(ema_target_module(target),expr,measured,device);trajectory.append({'world':world,'update':step,'jepa_loss':loss,'biology_factor_R2':readout(z,factors.numpy(),'continuous'),'source_balanced_accuracy':readout(z,sources,'class'),'operator_balanced_accuracy':readout(z,ops,'class'),'support_count_R2':readout(z,measured.sum(1).numpy()[:,None],'continuous')})
 assess(0);generator=torch.Generator().manual_seed(SEED+123);orders=[]
 for pass_id in range(math.ceil(UPDATES*EFFECTIVE/CELLS)):orders.append(torch.randperm(CELLS,generator=generator));sequence=torch.cat(orders)[:UPDATES*EFFECTIVE]
 for update in range(1,UPDATES+1):
  optimizer.zero_grad(set_to_none=True);take=sequence[(update-1)*EFFECTIVE:update*EFFECTIVE];loss_sum=0
  for b in range(0,EFFECTIVE,MICRO):
   idx=take[b:b+MICRO];e=expr[idx].to(device);m=measured[idx].to(device);hidden=construct_context_mask(m.cpu(),mask_fraction=.4,production_seed=SEED,cell_indices=idx,sample_pass=update,view_index=0,rule='exact_count').to(device);g=torch.arange(GENES,device=device).expand(MICRO,-1)
   with torch.autocast('cuda',dtype=torch.float16):
    context=online(g,e,m,hidden,'student');pred=predictor(context)
    with torch.no_grad():truth=target(g,e,m,hidden,'target')
    loss=jepa_prediction_loss(pred,truth);scaled=loss/(EFFECTIVE/MICRO)
   scaler.scale(scaled).backward();loss_sum+=float(loss)/(EFFECTIVE/MICRO)
  scaler.step(optimizer);scaler.update();controller.after_successful_optimizer_step(momentum=prior.EMA_MOMENTUM)
  if update in (100,300,500):assess(update,loss_sum)
 return trajectory,ops,donors,native,sources,measured,sequence
def main():
 started=time.time();loader=ProductionTrainLoader();support=pd.read_csv(OUT/'FOUNDATION_SUPPORT_BY_OPERATOR.csv').sort_values('operator_index');probs=support.fit104_cells.to_numpy(float);probs/=probs.sum();chosen=np.linspace(0,41_237,GENES,dtype=int);states=np.stack([loader.states[i['matrix_id']][chosen] for i in loader.items]).astype(np.uint8)
 import sqlite3
 con=sqlite3.connect(OUT/'foundation_metadata_rows.sqlite');meta=pd.read_sql_query("select operator_index,source,donor_id,native_class,count(*) n from cells where partition='reader_fit' group by operator_index,source,donor_id,native_class",con);operator_source=dict(zip(support.operator_index,support.source));conditional={}
 for op,g in meta.groupby('operator_index'):
  dc=g.groupby('donor_id').n.sum();nc=g.groupby('native_class').n.sum();conditional[int(op)]={'donor':dc.index.to_numpy(object),'donor_p':(dc/dc.sum()).to_numpy(float),'native':nc.index.to_numpy(object),'native_p':(nc/nc.sum()).to_numpy(float)}
 all_donors=sorted(meta.donor_id.unique());spot=pd.read_csv(OUT/'FOUNDATION_ACTUAL_EXPRESSION_SPOTCHECK.csv');rates=(spot.nonzero_measured_scalar_count/spot.measured_scalar_count).groupby(spot.source).median();detection={s:float(rates[s]/rates.max()) for s in rates.index}
 base,factors,_=prior.synthetic_fixture('balanced_multifactor',smoke=True);device=torch.device('cuda');all_rows=[];world_audits=[]
 for world in ('BALANCED_REFERENCE','EMPIRICAL_HETEROGENEOUS'):
  rows,ops,donors,native,sources,measured,seq=run_world(world,base,factors,states,probs,operator_source,conditional,all_donors,detection,device);all_rows.extend(rows);world_audits.append({'world':world,'source_counts':pd.Series(sources).value_counts().to_dict(),'operator_counts':pd.Series(ops).value_counts().sort_index().to_dict(),'donor_count':int(pd.Series(donors).nunique()),'native_class_count_source_native':int(pd.Series(native).nunique()),'unique_first_first_512':len(np.unique(seq[:512].numpy()))==512,'maximum_exposure':int(pd.Series(seq.numpy()).value_counts().max()),'mean_measured_fraction':float(measured.float().mean())})
 result=pd.DataFrame(all_rows);result.to_csv(OUT/'SYNTH_BALANCED_VS_EMPIRICAL_RESULTS.csv',index=False,lineterminator='\n')
 # Bounded full-41K observation/masking smoke, including repeated fresh masks.
 full_states=np.stack([loader.states[i['matrix_id']] for i in loader.items]);measurement=torch.from_numpy(full_states==MEASURED_SCALAR);ids=torch.arange(42,dtype=torch.int64);h0=construct_context_mask(measurement,mask_fraction=.4,production_seed=SEED,cell_indices=ids,sample_pass=0,view_index=0,rule='exact_count');h1=construct_context_mask(measurement,mask_fraction=.4,production_seed=SEED,cell_indices=ids,sample_pass=1,view_index=0,rule='exact_count')
 smoke={'addresses':41_238,'operators':42,'three_state_codes':sorted(np.unique(full_states).tolist()),'hidden_only_measured':bool(not torch.any(h0&~measurement)),'exact_floor_40pct':bool(all(int(h0[i].sum())==math.floor(.4*int(measurement[i].sum())) for i in range(42))),'fresh_mask_later_sample_pass':bool(torch.any(h0!=h1)),'measured_zero_preserved_by_separate_state':True}
 contract={'schema':'foundation-empirical-heterogeneous-synthetic-v1','label':'MECHANISM_STRESS_ONLY_NOT_PRODUCTION_TRAINING','same_underlying_biology':True,'cells':CELLS,'mechanism_genes':GENES,'production_address_smoke':41_238,'updates_per_world':UPDATES,'architecture':'previously qualified V4AEncoderSkeleton + LatentPredictor unchanged','objective':'raw latent JEPA MSE unchanged','mask_fraction':.4,'worlds':world_audits,'operator_probabilities_exact_fit104':dict(zip(support.matrix_id,probs)),'conditional_donor_and_native_class_distributions':'exact fit-104 metadata counts within operator; source-native labels never merged','source_detection_scalars_from_frozen_spotcheck':detection,'program_semantics':{'broad':'factors 0-3','weak_distributed':'factors 4-7','local':'factors 8-11','core_halo':'factors 12-15','sparse':'factors 16-19','innovation':'factors 20-23','rare5':'deterministic upper 5% factor role','rare1':'deterministic upper 1% factor role','source_specific':'factors 30-31 expressed only in HVS/NPH52','cross_source_shared':'factors 0-29'},'supports_three_states':True,'rare_programs':'underlying historical 32-factor fixture; deterministic 5% and 1% roles audited descriptively','real_expression_used_for_parameterization':True,'real_expression_used_for_neural_training':False,'pathology':False,'dev_or_sealed_expression':False,'full41k_smoke':smoke}
 (OUT/'SYNTH_HETEROGENEOUS_GENERATOR_CONTRACT.json').write_text(json.dumps(contract,indent=2)+'\n')
 a=result[result['update'].eq(500)].set_index('world');delta={m:float(a.loc['EMPIRICAL_HETEROGENEOUS',m]-a.loc['BALANCED_REFERENCE',m]) for m in ('biology_factor_R2','source_balanced_accuracy','operator_balanced_accuracy','support_count_R2')}
 adjud={'classification':'MECHANISM_STRESS_ONLY_NOT_PRODUCTION_TRAINING','u500_empirical_minus_balanced':delta,'interpretation':'Direct matched evidence at the frozen 500-update checkpoint; no production-transfer claim and no teacher authorization.','wall_seconds':time.time()-started}
 (OUT/'SYNTH_HETEROGENEOUS_GENERATOR_AUDIT.md').write_text('# Heterogeneous synthetic generator audit\n\n'+json.dumps({'full41k_smoke':smoke,'worlds':world_audits},indent=2)+'\n',encoding='utf-8');(OUT/'SYNTH_BALANCED_VS_EMPIRICAL_ADJUDICATION.md').write_text('# Balanced versus empirical synthetic adjudication\n\n'+json.dumps(adjud,indent=2)+'\n',encoding='utf-8');print(json.dumps(adjud,indent=2))
if __name__=='__main__':main()
