from __future__ import annotations
import csv, hashlib, json
from pathlib import Path
from t0_package_integrity_v1 import verify_flat_package, is_hex64, sha256_file
from t0_decision_v1 import STATE_POS_ALPHA,TAIL_POS_ALPHA,NEG_ALPHA,SENS_ALPHA
from t0_tail_hc3_t_v1 import TAIL_ALLOWED_N

SCHEMA='JEPA_T0_TARGET_FAMILY_AUTHORITY_V3'; MEMBER='T0_TARGET_FAMILY_AUTHORITY.json'; ALLOWED_STATUS='NOT_DECISION_CAPABLE_AUTHORITY_MISSING'; TAIL_ENGINE='HC3_T_RESIDUAL_DF'
STATUS_SCHEMA='JEPA_T0_RARE5_DECISION_CAPABILITY_STATUS_V1'
RESERVED_STATUS_KEYS={'schema','historical_rare5_status','decision_capable','reason'}

def _load_status(path):
    p=Path(path); raw=p.read_bytes(); obj=json.loads(raw.decode('utf-8'))
    if set(obj)!=RESERVED_STATUS_KEYS or obj.get('schema')!=STATUS_SCHEMA or obj.get('historical_rare5_status')!=ALLOWED_STATUS or obj.get('decision_capable') is not False or not isinstance(obj.get('reason'),str) or not obj['reason']:
        raise ValueError('rare5 status authority is decision-capable, malformed, or changed; new reviewed family contract required')
    return obj,hashlib.sha256(raw).hexdigest()

def build_primary_only_family_v3(outdir,rare5_status_authority_file,note:str):
    status,status_sha=_load_status(rare5_status_authority_file)
    if not isinstance(note,str) or not note: raise ValueError('note required')
    obj={'schema':SCHEMA,'family_mode':'PRIMARY_ONLY','primary_hypothesis':'BROAD_IMMUNE_EXPRESSION_TARGET','primary_positive_alpha':STATE_POS_ALPHA,'primary_negative_alpha':NEG_ALPHA,'tail_extensions':'HIERARCHICAL_NON_RESCUING','tail_engine':TAIL_ENGINE,'tail_allowed_n':sorted(TAIL_ALLOWED_N),'tail_positive_alpha':TAIL_POS_ALPHA,'tail_negative_alpha':NEG_ALPHA,'sensitivity_directional_alpha':SENS_ALPHA,'tail_order':'PARENT_STATE_SUPPORTED__THEN_PATHOLOGY_BLIND_PREFLIGHT__THEN_TAIL_PRIMARY__THEN_DIRECTION_MATCHED_SENSITIVITIES','historical_rare5_status':status['historical_rare5_status'],'rare5_status_authority_sha256':status_sha,'note':note}
    out=Path(outdir)
    if out.exists() and any(out.iterdir()): raise ValueError('family output must be absent or empty')
    out.mkdir(parents=True,exist_ok=True); (out/MEMBER).write_text(json.dumps(obj,sort_keys=True,separators=(',',':'))+'\n')
    with (out/'T0_TARGET_FAMILY_MANIFEST.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f,lineterminator='\n'); p=out/MEMBER; w.writerow(['filename','bytes','sha256']); w.writerow([MEMBER,p.stat().st_size,sha256_file(p)])
    root=sha256_file(out/'T0_TARGET_FAMILY_MANIFEST.csv'); (out/'T0_TARGET_FAMILY_PACKAGE_ROOT_SHA256.txt').write_text(root+'\n'); return {'package_root_sha256':root,'authority':obj}

def load_primary_only_family_v3(outdir):
    out=Path(outdir); root=verify_flat_package(out,{MEMBER},'T0_TARGET_FAMILY_MANIFEST.csv','T0_TARGET_FAMILY_PACKAGE_ROOT_SHA256.txt',label='target-family-v3 package'); obj=json.loads((out/MEMBER).read_text())
    keys={'schema','family_mode','primary_hypothesis','primary_positive_alpha','primary_negative_alpha','tail_extensions','tail_engine','tail_allowed_n','tail_positive_alpha','tail_negative_alpha','sensitivity_directional_alpha','tail_order','historical_rare5_status','rare5_status_authority_sha256','note'}
    if set(obj)!=keys or obj.get('schema')!=SCHEMA or obj.get('family_mode')!='PRIMARY_ONLY' or obj.get('historical_rare5_status')!=ALLOWED_STATUS or not is_hex64(obj.get('rare5_status_authority_sha256')): raise ValueError('family v3 authority incompatible')
    exact={'primary_hypothesis':'BROAD_IMMUNE_EXPRESSION_TARGET','primary_positive_alpha':STATE_POS_ALPHA,'primary_negative_alpha':NEG_ALPHA,'tail_extensions':'HIERARCHICAL_NON_RESCUING','tail_engine':TAIL_ENGINE,'tail_allowed_n':sorted(TAIL_ALLOWED_N),'tail_positive_alpha':TAIL_POS_ALPHA,'tail_negative_alpha':NEG_ALPHA,'sensitivity_directional_alpha':SENS_ALPHA,'tail_order':'PARENT_STATE_SUPPORTED__THEN_PATHOLOGY_BLIND_PREFLIGHT__THEN_TAIL_PRIMARY__THEN_DIRECTION_MATCHED_SENSITIVITIES'}
    for k,v in exact.items():
        if obj.get(k)!=v: raise ValueError(f'family v3 decision semantic mismatch: {k}')
    if not isinstance(obj.get('note'),str) or not obj['note']: raise ValueError('family v3 note invalid')
    return {'package_root_sha256':root,'authority':obj}
