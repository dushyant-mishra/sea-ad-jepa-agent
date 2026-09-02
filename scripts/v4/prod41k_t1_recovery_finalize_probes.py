#!/usr/bin/env python3
import hashlib,json
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'exports/prod41k_t1_contextual_recovery_v1'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()
b=pd.read_csv(OUT/'T1_RECOVERY_CONTEXTUAL_BIOLOGY.csv'); endpoints=('broad_common','weak_distributed','local','local_core','local_halo','core_halo','sparse_marker_like','innovation_tail','recurrent_5pct','recurrent_1pct')
primary=b[(b['update']==205)&(b.evaluation_partition=='reader_oracle')&(b.evidence_mode=='rich_H')];matrix=[]
for endpoint in endpoints:
 row={'endpoint':endpoint}
 for variant,label in (('raw','RAW'),('address_residual','ADDRESS_RESIDUAL'),('source_residual','SOURCE_RESIDUAL'),('operator_residual','OPERATOR_RESIDUAL')):
  q=primary[(primary.endpoint==endpoint)&(primary.representation==variant)].iloc[0]
  row.update({f'{label}_u0':q.value-q.u205_minus_u0,f'{label}_u205':q.value,f'{label}_delta':q.u205_minus_u0,f'{label}_delta_lower':q.donor_bootstrap_delta_lower,f'{label}_delta_upper':q.donor_bootstrap_delta_upper})
 matrix.append(row)
pd.DataFrame(matrix).to_csv(OUT/'T1_RECOVERY_MASTER_CONTEXTUAL_GAIN_MATRIX.csv',index=False,lineterminator='\n')
summary={'schema':'t1-recovery-contextual-probes-v1','analysis_freeze_sha256':sha(OUT/'T1_RECOVERY_ANALYSIS_FREEZE.json'),'residual_features_sha256':sha(OUT/'T1_RECOVERY_RESIDUAL_FEATURES.npz'),'fit_cells':3163,'fit_donors':104,'native_class':'NOT_ESTIMABLE_ABSENT_FROM_FROZEN_META','raw_rich_role':'retention_control_only','representation_updates':0}
(OUT/'T1_RECOVERY_CONTEXTUAL_BIOLOGY.md').write_text('# T1 recovery contextual biology\n\n'+json.dumps(summary,indent=2)+'\n')
(OUT/'T1_RECOVERY_NUISANCE_DECODABILITY.md').write_text('# T1 recovery nuisance decodability\n\nShortcut diagnostic only. Native class is not estimable from the frozen metadata.\n\n'+json.dumps(summary,indent=2)+'\n')
(OUT/'T1_RECOVERY_PARTIAL_CONTEXT_PREDICTABILITY.md').write_text('# T1 partial-to-contextual-target predictability\n\nPrimary donor-heldout target-interface evidence under the frozen analysis specification.\n\n'+json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2))
