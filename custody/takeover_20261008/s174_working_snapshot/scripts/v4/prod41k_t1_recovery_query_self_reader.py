#!/usr/bin/env python3
"""Forced query-self molecular-reader sensitivity on exact matched frozen cells."""
from __future__ import annotations
import hashlib,json,sys
from pathlib import Path
import numpy as np,pandas as pd,torch
ROOT=Path(__file__).resolve().parents[2];T1=ROOT/'exports/prod41k_teacher_t1_20260823';RUN=T1/'t1_run';V5A=ROOT/'exports/contextual_biology_v6r5a_20260822';OUT=ROOT/'exports/prod41k_t1_contextual_recovery_v1'
sys.path.insert(0,str(ROOT/'scripts/v4'));sys.path.insert(0,str(ROOT/'exports/static_context_decomposition_v4_20260821'))
import stage81a3_prod41k_teacher_t1 as t1
from production_train_loader import ProductionTrainLoader
MASK_SEED=2026082205
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()
def hs(*parts):return hashlib.sha256('|'.join(map(str,parts)).encode()).hexdigest()
def forced_hidden(base,physical,forced,cell_id):
 count=int(base.sum())
 if len(forced)>count or not np.all(physical[forced]):raise RuntimeError('forced SELF-MASK contract failed')
 result=np.zeros_like(base,dtype=bool);result[forced]=True
 candidates=sorted(np.flatnonzero(base&physical&~result),key=lambda a:hs(MASK_SEED,'mask',cell_id,int(a)));result[np.asarray(candidates[:count-len(forced)],np.int64)]=True
 if result.sum()<count:
  extra=sorted(np.flatnonzero(physical&~result),key=lambda a:hs(MASK_SEED,'extra',cell_id,int(a)));result[np.asarray(extra[:count-int(result.sum())],np.int64)]=True
 if result.sum()!=count or not result[forced].all():raise RuntimeError('forced hidden count changed')
 return result
def load(update,device):
 m=json.loads((RUN/'checkpoint_manifest.json').read_text());r=next(x for x in m['checkpoints'] if int(x['update'])==update);p=ROOT/r['path']
 if sha(p)!=r['sha256']:raise RuntimeError('checkpoint hash mismatch')
 s=torch.load(p,map_location=device,weights_only=False);target=t1.phase_e.build_components(t1.SEED,device)[1];target.load_state_dict(s['target_encoder']);target.eval();return target,p
def extract(target,spec,forced,device):
 raw=np.empty((len(spec['address']),160),np.float32);selfh=np.empty_like(raw);positions={int(c):np.flatnonzero(spec['cell_index']==c) for c in np.unique(spec['cell_index'])}
 with torch.inference_mode():
  for begin in range(0,len(spec['values']),t1.EVAL_BATCH):
   end=min(begin+t1.EVAL_BATCH,len(spec['values']));expr=torch.from_numpy(spec['values'][begin:end]).to(device);measured=torch.from_numpy(spec['measured'][begin:end]).to(device);hidden=torch.from_numpy(forced[begin:end]).to(device);ids=torch.arange(t1.phase_e.VOCABULARY_SIZE,device=device).expand(end-begin,-1)
   with torch.autocast('cuda',dtype=torch.float16):a=target(ids,expr,measured,torch.zeros_like(measured),'target');b=target(ids,expr,measured,hidden,'student')
   for cell in range(begin,end):
    take=positions[cell];addr=torch.from_numpy(spec['address'][take]).to(device);raw[take]=a.gene_states[cell-begin,addr].float().cpu().numpy();selfh[take]=b.gene_states[cell-begin,addr].float().cpu().numpy()
 return raw,selfh
def main():
 t1.validate_contract();device=torch.device('cuda' if torch.cuda.is_available() else 'cpu')
 if device.type!='cuda':raise RuntimeError('qualified CUDA path required')
 evaluation=t1.load_evaluation(ProductionTrainLoader());meta,_,measured,*rest=evaluation;reader_spec=rest[4];partial_masks=rest[-1]
 reader_cells=pd.read_csv(V5A/'reader_cells.csv');reader_data=np.load(V5A/'real_reader_rows.npz',allow_pickle=False)
 cols=['operator_index','matrix_id','local_row','donor_id','cell_id'];lookup={tuple(r):i for i,r in enumerate(meta[cols].itertuples(index=False,name=None))}
 matched=[];excluded=[]
 for old,row in enumerate(reader_cells.itertuples(index=False)):
  key=(int(row.operator_index),str(row.matrix_id),int(row.local_row),str(row.donor_id),str(row.cell_id));idx=lookup.get(key)
  (matched if idx is not None else excluded).append((old,idx) if idx is not None else old)
 if len(matched)!=437 or len(excluded)!=9:raise RuntimeError(f'exact reader/T1 overlap drift {len(matched)}/{len(excluded)}')
 old_cells=np.asarray([x[0] for x in matched],np.int64);bio=np.asarray([x[1] for x in matched],np.int64);remap={old:new for new,old in enumerate(old_cells)}
 keep=np.isin(reader_data['cell_index'],old_cells);old_row_cell=reader_data['cell_index'][keep].astype(np.int64);new_cell=np.asarray([remap[int(x)] for x in old_row_cell],np.int64)
 addresses=reader_data['address'][keep].astype(np.int64);values=reader_spec['values'][old_cells];physical=reader_spec['measured'][old_cells]
 if not np.array_equal(physical,measured[bio]):raise RuntimeError('matched-cell physical masks differ')
 forced=np.empty_like(physical);audit=[]
 for new,(old,bi) in enumerate(matched):
  q=np.unique(addresses[new_cell==new]);base=partial_masks[bi];forced[new]=forced_hidden(base,physical[new],q,str(reader_cells.iloc[old].cell_id))
  audit.append({'reader_cell_index':old,'matched_t1_biology_cell_index':int(meta.iloc[bi].biology_cell_index),'reader_partition':str(reader_cells.iloc[old].reader_partition),'donor_id':str(reader_cells.iloc[old].donor_id),'operator_index':int(reader_cells.iloc[old].operator_index),'base_hidden':int(base.sum()),'forced_queries':len(q),'already_hidden':int(base[q].sum()),'newly_forced':int((~base[q]).sum()),'swapped_out':int((base&~forced[new]).sum()),'mask_sha256':hashlib.sha256(forced[new].tobytes()).hexdigest()})
 mask_path=OUT/'T1_RECOVERY_FORCED_READER_MASKS.npz';np.savez_compressed(mask_path,masks=np.packbits(forced,axis=1,bitorder='little'),bitorder=np.asarray('little'),reader_cell_index=old_cells,t1_biology_row=bio)
 pd.DataFrame(audit).to_csv(OUT/'T1_RECOVERY_FORCED_READER_MASK_MANIFEST.csv',index=False,lineterminator='\n')
 spec={'values':values,'measured':physical,'cell_index':new_cell,'address':addresses,'target':reader_data['value'][keep].astype(np.float32),'query':reader_data['frozen_identity'][addresses].astype(np.float32),
       'partition':reader_cells.reader_partition.astype(str).to_numpy()[old_row_cell],'donor':reader_cells.donor_id.astype(str).to_numpy()[old_row_cell]}
 operators=reader_cells.operator_index.to_numpy(np.int64)[old_row_cell];rows=[];run_audits=[]
 for update in (0,205):
  target,checkpoint=load(update,device);before=sha(checkpoint);raw,selfh=extract(target,spec,forced,device)
  with np.load(OUT/f'T1_RECOVERY_RICH_CENTROIDS_u{update:04d}.npz',allow_pickle=False) as z:raw_c=raw-z['address_mean'][addresses]-z['operator_deviation'][operators,addresses]
  with np.load(OUT/f'T1_RECOVERY_SELF_MASKED_CENTROIDS_u{update:04d}.npz',allow_pickle=False) as z:self_c=selfh-z['address_mean'][addresses]-z['operator_deviation'][operators,addresses]
  for arm,h in (('raw_same_address_H',raw),('operator_residual_same_address_H',raw_c),('forced_query_scalar_self_ablated_H',selfh),('forced_query_scalar_self_ablated_operator_residual_H',self_c)):
   for row in t1.address_reader_metrics(update,h.astype(np.float32),spec,device):row.update({'assay_type':'molecular_reader','representation':arm});rows.append(row)
  run_audits.append({'update':update,'checkpoint_sha256':before,'checkpoint_unchanged':sha(checkpoint)==before,'rows':len(raw)})
 reader_frame=pd.DataFrame(rows);reader_frame.to_csv(OUT/'T1_RECOVERY_QUERY_SELF_MOLECULAR_READER.csv',index=False,lineterminator='\n')
 block=pd.read_csv(OUT/'T1_RECOVERY_QUERY_SELF_PRIVILEGE.csv');block['assay_type']='block_target_predictability';pd.concat([block,reader_frame],ignore_index=True,sort=False).to_csv(OUT/'T1_RECOVERY_QUERY_SELF_PRIVILEGE.csv',index=False,lineterminator='\n')
 payload={'schema':'t1-recovery-forced-reader-self-ablation-v1','matched_cells':437,'excluded_unmatched_cells':9,'fit_donors':int(reader_cells.iloc[old_cells].loc[lambda x:x.reader_partition.eq('reader_fit'),'donor_id'].nunique()),'fit_operators':int(reader_cells.iloc[old_cells].loc[lambda x:x.reader_partition.eq('reader_fit'),'operator_index'].nunique()),'mask_sha256':sha(mask_path),'historical_forced_hidden_source_sha256':sha(ROOT/'exports/contextual_biology_v6r5b_20260822/run_frozen_predictions.py'),'audits':run_audits,'representation_updates':0}
 with (OUT/'T1_RECOVERY_QUERY_SELF_PRIVILEGE.md').open('a',encoding='utf-8') as f:f.write('\n## Forced reader sensitivity\n\n'+json.dumps(payload,indent=2)+'\n')
 print(json.dumps(payload,indent=2))
if __name__=='__main__':main()
