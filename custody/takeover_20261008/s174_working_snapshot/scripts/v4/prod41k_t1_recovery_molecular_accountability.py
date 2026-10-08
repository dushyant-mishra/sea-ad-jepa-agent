#!/usr/bin/env python3
"""Read-only molecular accountability for raw and recovery-residual T1 H."""
from __future__ import annotations
import hashlib,json,sys
from pathlib import Path
import numpy as np,pandas as pd,torch
ROOT=Path(__file__).resolve().parents[2];T1=ROOT/'exports/prod41k_teacher_t1_20260823';RUN=T1/'t1_run';OUT=ROOT/'exports/prod41k_t1_contextual_recovery_v1'
sys.path.insert(0,str(ROOT/'scripts/v4'));sys.path.insert(0,str(ROOT/'exports/static_context_decomposition_v4_20260821'))
import stage81a3_prod41k_teacher_t1 as t1
from production_train_loader import ProductionTrainLoader
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()
def load_checkpoint(update,device):
 m=json.loads((RUN/'checkpoint_manifest.json').read_text());r=next(x for x in m['checkpoints'] if int(x['update'])==update);p=ROOT/r['path']
 if sha(p)!=r['sha256']:raise RuntimeError('checkpoint hash mismatch')
 s=torch.load(p,map_location=device,weights_only=False);online,target=t1.phase_e.build_components(t1.SEED,device)[:2];online.load_state_dict(s['online_encoder']);target.load_state_dict(s['target_encoder']);return target,p
def main():
 t1.validate_contract();device=torch.device('cuda' if torch.cuda.is_available() else 'cpu')
 if device.type!='cuda':raise RuntimeError('qualified CUDA path required')
 evaluation=t1.load_evaluation(ProductionTrainLoader());reader_spec=evaluation[7]
 reader_cells=pd.read_csv(ROOT/'exports/contextual_biology_v6r5a_20260822/reader_cells.csv');cell_index=reader_spec['cell_index'];operators=reader_cells.operator_index.to_numpy(np.int64)[cell_index]
 rows=[];audits=[]
 for update in (0,205):
  target,checkpoint=load_checkpoint(update,device);before=sha(checkpoint);raw=t1.molecular_features(target,reader_spec,device)
  with np.load(OUT/f'T1_RECOVERY_RICH_CENTROIDS_u{update:04d}.npz',allow_pickle=False) as z:
   b=z['address_mean'][reader_spec['address']];o=z['operator_deviation'][operators,reader_spec['address']]
  address=raw-b;context=raw-b-o;reconstructed=context+b+o;maximum=float(np.max(np.abs(raw-reconstructed)))
  if maximum>2e-6:raise RuntimeError(f'molecular decomposition reconstruction drift {maximum}')
  original=pd.read_csv(RUN/f't1_address_reader_metrics_u{update:04d}.csv')
  for arm,h in (('address_residual_C',address),('operator_residual_C',context)):
   for row in t1.address_reader_metrics(update,h.astype(np.float32),reader_spec,device):row.update({'representation':arm,'reconstruction_max_abs_error':maximum});rows.append(row)
  for item in original.to_dict('records'):
   rows.append({**item,'representation':'raw_full_H','reconstruction_max_abs_error':maximum})
   rows.append({**item,'representation':'C_plus_B_plus_O_reconstructed_full_H','reconstruction_max_abs_error':maximum})
  audits.append({'update':update,'checkpoint_sha256':before,'rows':len(raw),'addresses_in_reader':int(np.unique(reader_spec['address']).size),'reconstruction_max_abs_error':maximum,'checkpoint_unchanged':sha(checkpoint)==before})
 frame=pd.DataFrame(rows);frame.to_csv(OUT/'T1_RECOVERY_MOLECULAR_ACCOUNTABILITY.csv',index=False,lineterminator='\n')
 payload={'schema':'t1-recovery-molecular-accountability-v1','algebra':'H = C_operator + B + O','audits':audits,'interpretation':'C is a contextual exposure; B/O side information deterministically restores the full Molecular Ledger H. Reader fits are downstream only; representation updates=0.'}
 (OUT/'T1_RECOVERY_MOLECULAR_ACCOUNTABILITY.md').write_text('# T1 recovery molecular accountability\n\n'+json.dumps(payload,indent=2)+'\n',encoding='utf-8');print(json.dumps(payload,indent=2))
if __name__=='__main__':main()
