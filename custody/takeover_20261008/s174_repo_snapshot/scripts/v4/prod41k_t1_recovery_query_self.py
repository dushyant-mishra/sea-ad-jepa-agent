#!/usr/bin/env python3
"""Exact frozen-mask query-scalar-self recovery assay; no representation updates."""
from __future__ import annotations
import hashlib,json,sys,time
from pathlib import Path
import numpy as np,pandas as pd,torch
import torch.nn.functional as F
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import r2_score
ROOT=Path(__file__).resolve().parents[2];T1=ROOT/'exports/prod41k_teacher_t1_20260823';RUN=T1/'t1_run';OUT=ROOT/'exports/prod41k_t1_contextual_recovery_v1'
sys.path.insert(0,str(ROOT/'scripts/v4'));sys.path.insert(0,str(ROOT/'exports/static_context_decomposition_v4_20260821'))
import stage81a3_prod41k_teacher_t1 as t1
from production_train_loader import ProductionTrainLoader
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()
def load(update,device):
 m=json.loads((RUN/'checkpoint_manifest.json').read_text());r=next(x for x in m['checkpoints'] if int(x['update'])==update);p=ROOT/r['path']
 if sha(p)!=r['sha256']:raise RuntimeError('checkpoint hash mismatch')
 s=torch.load(p,map_location=device,weights_only=False);components=t1.phase_e.build_components(t1.SEED,device);online,target,predictor=components[:3]
 online.load_state_dict(s['online_encoder']);target.load_state_dict(s['target_encoder']);predictor.load_state_dict(s['predictor']);online.eval();target.eval();predictor.eval();return online,target,predictor,p
def contextual_blocks(states,blocks,b,opdev,operators):
 safe=blocks.indices.clamp_min(0);batch=torch.arange(len(states),device=states.device)[:,None,None];gathered=states[batch,safe]
 cent=b[safe]+opdev[operators[:,None,None],safe];residual=(gathered-cent)*blocks.member_mask[...,None]
 means=residual.sum(2)/blocks.member_mask.sum(2,keepdim=True).clamp_min(1);return F.layer_norm(means,(means.shape[-1],))
def vector_metrics(y,p,fit_mean):
 yf=y.reshape(-1,y.shape[-1]);pf=p.reshape(-1,p.shape[-1]);mse=float(np.square(yf-pf).mean());base=float(np.square(yf-fit_mean).mean())
 yc=yf-fit_mean;pc=pf-fit_mean;cos=float(np.mean(np.sum(yc*pc,1)/np.maximum(np.linalg.norm(yc,axis=1)*np.linalg.norm(pc,axis=1),1e-12)))
 x=yc-yc.mean(0);q=pc-pc.mean(0);cka=float(np.square(np.linalg.norm(x.T@q,'fro'))/(np.linalg.norm(x.T@x,'fro')*np.linalg.norm(q.T@q,'fro')+1e-30))
 return {'coordinate_r2':float(r2_score(yf,pf)),'mse':mse,'normalized_mse_fit_mean':mse/base if base else np.nan,'centered_cosine':cos,'linear_CKA':cka}
def bootstrap_gain(y0,p0,y1,p1,donors,seed):
 unique=np.unique(donors);pos={d:np.flatnonzero(donors==d) for d in unique};rng=np.random.default_rng(seed);vals=[]
 for _ in range(1000):
  take=np.concatenate([pos[d] for d in rng.choice(unique,len(unique),replace=True)])
  def score(y,p):
   mean=y.mean(axis=(0,1),keepdims=True);return -float(np.square(y-p).mean()/np.square(y-mean).mean())
  vals.append(score(y1[take],p1[take])-score(y0[take],p0[take]))
 return float(np.quantile(vals,.025)),float(np.quantile(vals,.975))
def run_update(update,meta,values,measured,panel,partial_masks,device):
 online,target,predictor,checkpoint=load(update,device);before=sha(checkpoint);n=len(meta);G=t1.phase_e.VOCABULARY_SIZE;D=t1.phase_e.WIDTH
 with np.load(OUT/f'T1_RECOVERY_RICH_CENTROIDS_u{update:04d}.npz',allow_pickle=False) as z:
  raw_b=torch.from_numpy(z['address_mean']).to(device);raw_o=torch.from_numpy(z['operator_deviation']).to(device)
 operators=meta.operator_index.to_numpy(np.int64);fit=meta.reader_partition.astype(str).eq('reader_fit').to_numpy()
 self_sum=np.zeros((G,D),np.float64);self_count=np.zeros(G,np.int64);op_sum=np.zeros((42,G,D),np.float64);op_count=np.zeros((42,G),np.int64)
 arrays={k:np.empty((n,16,D),np.float32) for k in ('raw_target','self_target','partial_prediction','raw_context_target')}
 with torch.inference_mode():
  for begin in range(0,n,t1.EVAL_BATCH):
   end=min(begin+t1.EVAL_BATCH,n);expr=torch.from_numpy(values[begin:end]).to(device);mask=torch.from_numpy(measured[begin:end]).to(device)
   keys=torch.tensor(panel.stable_mask_key.iloc[begin:end].to_numpy(np.int64),dtype=torch.int64,device=device)
   blocks=t1.phase_e.sample_uniform_target_blocks(mask,production_seed=t1.SEED,cell_indices=keys,sample_pass=t1.PARTIAL_SAMPLE_PASS,view_index=t1.PARTIAL_VIEW_INDEX,mask_fraction=.4,block_count=16)
   expected=torch.from_numpy(partial_masks[begin:end]).to(device)
   if not torch.equal(blocks.hidden_mask,expected):raise RuntimeError('reconstructed frozen blocks/mask mismatch')
   gene_ids=torch.arange(G,device=device).expand(end-begin,-1)
   with torch.autocast('cuda',dtype=torch.float16):
    raw=target(gene_ids,expr,mask,torch.zeros_like(mask),'target');selfh=target(gene_ids,expr,mask,blocks.hidden_mask,'student');student=online(gene_ids,expr,mask,blocks.hidden_mask,'student')
    pred=predictor(online.tokenizer.gene_identity,blocks,student.gene_states,student.cell_state,mask&~blocks.hidden_mask)
   arrays['raw_target'][begin:end]=t1.phase_e.gather_block_states(raw.gene_states.float(),blocks).cpu().numpy()
   arrays['self_target'][begin:end]=t1.phase_e.gather_block_states(selfh.gene_states.float(),blocks).cpu().numpy()
   arrays['partial_prediction'][begin:end]=pred.float().cpu().numpy()
   arrays['raw_context_target'][begin:end]=contextual_blocks(raw.gene_states.float(),blocks,raw_b,raw_o,torch.from_numpy(operators[begin:end]).to(device)).cpu().numpy()
   for local,global_i in enumerate(range(begin,end)):
    if not fit[global_i]:continue
    addr=torch.nonzero(blocks.hidden_mask[local],as_tuple=False).flatten().cpu().numpy();x=selfh.gene_states[local,blocks.hidden_mask[local]].float().cpu().numpy();op=operators[global_i]
    self_sum[addr]+=x;self_count[addr]+=1;op_sum[op,addr]+=x;op_count[op,addr]+=1
   if end%512==0 or end==n:print(f'u{update} query-self pass1 {end}/{n}',flush=True)
 raw_b_np=raw_b.cpu().numpy();self_b=raw_b_np.copy();seen=self_count>0;self_b[seen]=self_sum[seen]/self_count[seen,None]
 self_o=np.zeros((42,G,D),np.float32)
 for op in range(42):
  mean=self_b.copy();take=op_count[op]>0;mean[take]=op_sum[op,take]/op_count[op,take,None];self_o[op]=(mean-self_b).astype(np.float32)
 np.savez_compressed(OUT/f'T1_RECOVERY_SELF_MASKED_CENTROIDS_u{update:04d}.npz',address_mean=self_b.astype(np.float32),operator_deviation=self_o,self_count=self_count,operator_count=op_count)
 b=torch.from_numpy(self_b.astype(np.float32)).to(device);o=torch.from_numpy(self_o).to(device);self_context=np.empty((n,16,D),np.float32)
 with torch.inference_mode():
  for begin in range(0,n,t1.EVAL_BATCH):
   end=min(begin+t1.EVAL_BATCH,n);expr=torch.from_numpy(values[begin:end]).to(device);mask=torch.from_numpy(measured[begin:end]).to(device);hidden=torch.from_numpy(partial_masks[begin:end]).to(device)
   keys=torch.tensor(panel.stable_mask_key.iloc[begin:end].to_numpy(np.int64),dtype=torch.int64,device=device);blocks=t1.phase_e.sample_uniform_target_blocks(mask,production_seed=t1.SEED,cell_indices=keys,sample_pass=t1.PARTIAL_SAMPLE_PASS,view_index=t1.PARTIAL_VIEW_INDEX,mask_fraction=.4,block_count=16)
   gene_ids=torch.arange(G,device=device).expand(end-begin,-1)
   with torch.autocast('cuda',dtype=torch.float16):selfh=target(gene_ids,expr,mask,hidden,'student')
   self_context[begin:end]=contextual_blocks(selfh.gene_states.float(),blocks,b,o,torch.from_numpy(operators[begin:end]).to(device)).cpu().numpy()
   if end%512==0 or end==n:print(f'u{update} query-self pass2 {end}/{n}',flush=True)
 arrays['self_context_target']=self_context
 if sha(checkpoint)!=before:raise RuntimeError('checkpoint mutated')
 return arrays,{'update':update,'checkpoint_sha256':before,'fit_hidden_address_coverage':int(seen.sum()),'fit_operator_address_pairs':int((op_count>0).sum()),'self_fallback_addresses':int((~seen).sum()),'representation_updates':0}
def main():
 t1.validate_contract();device=torch.device('cuda' if torch.cuda.is_available() else 'cpu')
 if device.type!='cuda':raise RuntimeError('qualified CUDA path required')
 evaluation=t1.load_evaluation(ProductionTrainLoader());meta,values,measured,*rest=evaluation;panel=rest[-2];partial_masks=rest[-1]
 results={};audits=[]
 for u in (0,205):results[u],audit=run_update(u,meta,values,measured,panel,partial_masks,device);audits.append(audit)
 partitions=meta.reader_partition.astype(str).to_numpy();donors=meta.donor_id.astype(str).to_numpy();fit=partitions=='reader_fit';rows=[];stored={}
 for target_name in ('raw_target','self_target','raw_context_target','self_context_target'):
  for u in (0,205):
   x=results[u]['partial_prediction'].reshape(len(meta)*16,-1);y=results[u][target_name].reshape(len(meta)*16,-1);fit_rows=np.repeat(fit,16)
   model=make_pipeline(StandardScaler(),Ridge(alpha=10.)).fit(x[fit_rows],y[fit_rows]);p=model.predict(x).reshape(len(meta),16,-1);stored[(target_name,u)]=p
   fit_mean=results[u][target_name][fit].reshape(-1,160).mean(0)
   for part in ('reader_validation','reader_oracle'):
    take=partitions==part;m=vector_metrics(results[u][target_name][take],p[take],fit_mean);rows.append({'update':u,'evaluation_partition':part,'target':target_name,'cells':int(take.sum()),'donors':np.unique(donors[take]).size,**m})
 for target_name in ('raw_target','self_target','raw_context_target','self_context_target'):
  for part in ('reader_validation','reader_oracle'):
   take=partitions==part;lo,hi=bootstrap_gain(results[0][target_name][take],stored[(target_name,0)][take],results[205][target_name][take],stored[(target_name,205)][take],donors[take],t1.EVALUATION_SEED+700)
   for row in rows:
    if row['update']==205 and row['evaluation_partition']==part and row['target']==target_name:row['u205_minus_u0_negative_normalized_mse_lower']=lo;row['u205_minus_u0_negative_normalized_mse_upper']=hi
 frame=pd.DataFrame(rows);frame.to_csv(OUT/'T1_RECOVERY_QUERY_SELF_PRIVILEGE.csv',index=False,lineterminator='\n')
 payload={'schema':'t1-recovery-query-scalar-self-v1','semantics':'exact frozen 40% multiquery mask; scalar self removed, gene identity retained','audits':audits,'direct_reader_panel_biology':'NOT_ESTIMABLE','representation_updates':0}
 (OUT/'T1_RECOVERY_QUERY_SELF_PRIVILEGE.md').write_text('# T1 query-self privilege\n\n'+json.dumps(payload,indent=2)+'\n',encoding='utf-8');print(json.dumps(payload,indent=2))
if __name__=='__main__':main()
