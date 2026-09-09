from __future__ import annotations
import csv,hashlib,json
from pathlib import Path
from t0_package_integrity_v1 import verify_flat_package,is_hex64
from t0_decision_v1 import STATE_POS_ALPHA,TAIL_POS_ALPHA,NEG_ALPHA,SENS_ALPHA
from t0_tail_hc3_t_v1 import TAIL_ALLOWED_N

SCHEMA='JEPA_T0_TARGET_FAMILY_AUTHORITY_V2'
MEMBER='T0_TARGET_FAMILY_AUTHORITY.json'
ALLOWED_STATUS='NOT_DECISION_CAPABLE_AUTHORITY_MISSING'
TAIL_ENGINE='HC3_T_RESIDUAL_DF'

def sha(path):
 h=hashlib.sha256()
 with open(path,'rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()

def _hex64(x):return isinstance(x,str) and len(x)==64 and all(c in '0123456789abcdef' for c in x)

def build_primary_only_family(outdir,historical_rare5_status:str,source_authority_hashes:dict[str,str],note:str):
 if historical_rare5_status!=ALLOWED_STATUS: raise ValueError('historical rare5 is decision-capable or status changed; new reviewed family contract required')
 if not isinstance(note,str) or not note:raise ValueError('note required')
 for k,v in source_authority_hashes.items():
  if not isinstance(k,str) or not k or not _hex64(v):raise ValueError('invalid family source hash')
 obj={
  'schema':SCHEMA,'family_mode':'PRIMARY_ONLY','primary_hypothesis':'BROAD_IMMUNE_EXPRESSION_TARGET',
  'primary_positive_alpha':STATE_POS_ALPHA,'primary_negative_alpha':NEG_ALPHA,
  'tail_extensions':'HIERARCHICAL_NON_RESCUING','tail_engine':TAIL_ENGINE,
  'tail_allowed_n':sorted(TAIL_ALLOWED_N),'tail_positive_alpha':TAIL_POS_ALPHA,'tail_negative_alpha':NEG_ALPHA,
  'sensitivity_directional_alpha':SENS_ALPHA,
  'tail_order':'PARENT_STATE_SUPPORTED__THEN_PATHOLOGY_BLIND_PREFLIGHT__THEN_TAIL_PRIMARY__THEN_DIRECTION_MATCHED_SENSITIVITIES',
  'historical_rare5_status':historical_rare5_status,'source_authority_hashes':dict(sorted(source_authority_hashes.items())),'note':note}
 out=Path(outdir)
 if out.exists() and any(out.iterdir()):raise ValueError('family output must be absent or empty')
 out.mkdir(parents=True,exist_ok=True);(out/MEMBER).write_text(json.dumps(obj,sort_keys=True,separators=(',',':'))+'\n')
 with (out/'T0_TARGET_FAMILY_MANIFEST.csv').open('w',newline='',encoding='utf-8') as f:
  w=csv.writer(f,lineterminator='\n');p=out/MEMBER;w.writerow(['filename','bytes','sha256']);w.writerow([MEMBER,p.stat().st_size,sha(p)])
 root=sha(out/'T0_TARGET_FAMILY_MANIFEST.csv');(out/'T0_TARGET_FAMILY_PACKAGE_ROOT_SHA256.txt').write_text(root+'\n');return {'package_root_sha256':root,'authority':obj}

def load_primary_only_family(outdir):
 out=Path(outdir);root=verify_flat_package(out,{MEMBER},'T0_TARGET_FAMILY_MANIFEST.csv','T0_TARGET_FAMILY_PACKAGE_ROOT_SHA256.txt',label='target-family package')
 obj=json.loads((out/MEMBER).read_text(encoding='utf-8'))
 keys={'schema','family_mode','primary_hypothesis','primary_positive_alpha','primary_negative_alpha','tail_extensions','tail_engine','tail_allowed_n','tail_positive_alpha','tail_negative_alpha','sensitivity_directional_alpha','tail_order','historical_rare5_status','source_authority_hashes','note'}
 if set(obj)!=keys or obj.get('schema')!=SCHEMA or obj.get('family_mode')!='PRIMARY_ONLY' or obj.get('primary_hypothesis')!='BROAD_IMMUNE_EXPRESSION_TARGET' or obj.get('historical_rare5_status')!=ALLOWED_STATUS:raise ValueError('family authority incompatible')
 exact={'primary_positive_alpha':STATE_POS_ALPHA,'primary_negative_alpha':NEG_ALPHA,'tail_extensions':'HIERARCHICAL_NON_RESCUING','tail_engine':TAIL_ENGINE,'tail_allowed_n':sorted(TAIL_ALLOWED_N),'tail_positive_alpha':TAIL_POS_ALPHA,'tail_negative_alpha':NEG_ALPHA,'sensitivity_directional_alpha':SENS_ALPHA,'tail_order':'PARENT_STATE_SUPPORTED__THEN_PATHOLOGY_BLIND_PREFLIGHT__THEN_TAIL_PRIMARY__THEN_DIRECTION_MATCHED_SENSITIVITIES'}
 for k,v in exact.items():
  if obj.get(k)!=v:raise ValueError(f'family decision semantic mismatch: {k}')
 hashes=obj.get('source_authority_hashes')
 if not isinstance(hashes,dict) or any(not isinstance(k,str) or not k or not is_hex64(v) for k,v in hashes.items()) or not isinstance(obj.get('note'),str) or not obj['note']:raise ValueError('family provenance invalid')
 return {'package_root_sha256':root,'authority':obj}
