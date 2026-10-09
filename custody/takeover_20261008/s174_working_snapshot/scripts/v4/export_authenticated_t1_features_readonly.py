#!/usr/bin/env python3
"""Read-only authenticated u205 feature export for teacher discovery."""
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path
import numpy as np, pandas as pd, torch
ROOT=Path(__file__).resolve().parents[2]; OUT=ROOT/'exports/foundation_corpus_discovery_v1'; T1=ROOT/'exports/prod41k_teacher_t1_20260823'; RUN=T1/'t1_run'
sys.path.insert(0,str(ROOT/'scripts/v4')); sys.path.insert(0,str(ROOT/'exports/static_context_decomposition_v4_20260821'))
import stage81a3_prod41k_teacher_t1 as t1
from production_train_loader import ProductionTrainLoader

def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''): h.update(b)
 return h.hexdigest()

def main():
 manifest=json.loads((RUN/'checkpoint_manifest.json').read_text()); rec=[x for x in manifest['checkpoints'] if int(x['update'])==205]
 if len(rec)!=1: raise RuntimeError('authenticated u205 absent')
 ck=RUN/'t1_checkpoint_u0205.pt'
 if sha(ck)!=rec[0]['sha256']: raise RuntimeError('u205 checkpoint hash mismatch')
 device=torch.device('cuda' if torch.cuda.is_available() else 'cpu'); components=t1.phase_e.build_components(t1.SEED,device); online,target=components[:2]
 state=torch.load(ck,map_location=device,weights_only=False); online.load_state_dict(state['online_encoder']); target.load_state_dict(state['target_encoder']); online.eval(); target.eval()
 loader=ProductionTrainLoader(); evaluation=t1.load_evaluation(loader); meta,values,measured,weights,continuous,evidence,control,reader_spec,panel,partial_masks=evaluation
 rich_h,rich_cell,_=t1.representation_features(target,values,measured,weights,device,role='target',panel=None,partial_masks=None)
 partial_h,partial_cell,_=t1.representation_features(online,values,measured,weights,device,role='student',panel=panel,partial_masks=partial_masks)
 p=OUT/'FOUNDATION_AUTHENTICATED_T1_U205_FEATURES.npz'; np.savez_compressed(p,rich_H=rich_h,rich_CELL=rich_cell,partial_H=partial_h,partial_CELL=partial_cell)
 m=meta.copy(); m.to_csv(OUT/'FOUNDATION_AUTHENTICATED_T1_EVALUATION_META.csv',index=False,lineterminator='\n')
 np.savez_compressed(OUT/'FOUNDATION_AUTHENTICATED_T1_EVALUATION_AUX.npz',continuous_targets=continuous,evidence=evidence,control=control,panel=panel,partial_masks=partial_masks)
 audit={'checkpoint':str(ck.relative_to(ROOT)),'checkpoint_sha256':sha(ck),'u0_features_sha256':sha(RUN/'u0_evaluation_features.npz'),'u205_features_sha256':sha(p),'rows':len(meta),'device':str(device),'neural_updates':0,'firewall':'existing frozen T1 evaluation only'}
 (OUT/'FOUNDATION_AUTHENTICATED_T1_FEATURE_EXPORT.json').write_text(json.dumps(audit,indent=2)+'\n'); print(json.dumps(audit,indent=2))
if __name__=='__main__': main()
