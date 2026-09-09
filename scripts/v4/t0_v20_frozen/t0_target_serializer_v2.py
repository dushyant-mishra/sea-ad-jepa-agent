from __future__ import annotations
import csv, hashlib, json, math
from pathlib import Path
import numpy as np
import pandas as pd
from t0_feature_authority_v1 import load_feature_authority, ordered_addresses, EXPECTED_SPLIT_SHA256
from t0_primary_membership_v1 import EXPECTED_CSV_SHA256
from t0_target_learner_v1 import MULTIPLIER_EXPONENTS
from t0_discovery_provenance_v1 import SCHEMA as PROVENANCE_SCHEMA
from t0_package_integrity_v1 import verify_flat_package

SCHEMA='JEPA_T0_TARGET_MODEL_V2'
EXPECTED_FEATURES=28061

PROVENANCE_KEYS={'schema','root_sha256','cell_payload_sha256','donor_metadata_sha256','feature_authority_sha256','membership_authority_sha256','cells','scoring_features','canonical_discovery_donors','cell_encoding','sex_utf8_mapping','normalization','pseudobulk','aggregation_feature_chunk'}
PROVENANCE_NORMALIZATION='log1p(10000*raw_count/source_library)_exactly_once'
PROVENANCE_PSEUDOBULK='equal_cell_mean_by_donor'
PROVENANCE_CHUNK=1024
MEMBERS={
'T0_TARGET_BETA_F64LE.bin','T0_TARGET_MU_F64LE.bin','T0_TARGET_SIGMA_F64LE.bin',
'T0_TARGET_DECISION_MASK_U8.bin','T0_TARGET_CV_MSE_F64LE.bin','T0_TARGET_MULTIPLIER_EXPONENTS_F64LE.bin',
'T0_TARGET_ADDRESS_REGISTRY.csv','T0_TARGET_METADATA.json','T0_TARGET_DISCOVERY_PROVENANCE.json',
}

def sha256_file(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(8<<20),b''): h.update(b)
    return h.hexdigest()

def _f64(path,a):
    x=np.asarray(a,dtype='<f8')
    if not np.isfinite(x).all(): raise ValueError(f'nonfinite {path.name}')
    path.write_bytes(np.ascontiguousarray(x).tobytes())

def _canonical_donors(fit):
    d=[str(x) for x in np.asarray(fit['canonical_donor_order']).tolist()]
    if len(d)<18 or len(set(d))!=len(d) or any(not x for x in d): raise ValueError('invalid discovery donor order')
    if d!=sorted(d,key=lambda x:x.encode('utf-8')): raise ValueError('discovery donors must be canonical UTF-8 order')
    return d

def _validate_fit(fit, provenance):
    beta=np.asarray(fit['beta'],dtype=np.float64); mu=np.asarray(fit['mu'],dtype=np.float64); sigma=np.asarray(fit['sigma'],dtype=np.float64); mask=np.asarray(fit['decision_gene_mask'])
    cv=np.asarray(fit['cv_mse_by_multiplier'],dtype=np.float64); exps=np.asarray(fit['multiplier_exponents'],dtype=np.float64)
    if beta.shape!=(EXPECTED_FEATURES,) or mu.shape!=beta.shape or sigma.shape!=beta.shape or mask.shape!=beta.shape: raise ValueError('target vector shape mismatch')
    if not np.isfinite(beta).all() or not np.isfinite(mu).all() or not np.isfinite(sigma).all() or np.any(sigma<=0): raise ValueError('invalid target vectors')
    if mask.dtype!=np.bool_: raise ValueError('decision mask must be boolean')
    if not np.array_equal(exps,MULTIPLIER_EXPONENTS): raise ValueError('multiplier grid mismatch')
    if cv.shape!=exps.shape or not np.isfinite(cv).all(): raise ValueError('CV grid invalid')
    j=fit['selected_multiplier_index']
    if isinstance(j,bool) or not isinstance(j,(int,np.integer)) or not (0<=int(j)<len(exps)): raise ValueError('selected multiplier index invalid')
    j=int(j)
    if float(fit['selected_multiplier_exponent'])!=float(exps[j]): raise ValueError('selected exponent/index mismatch')
    for k in ['final_lambda','final_trace_scale','response_residual_sd']:
        v=float(fit[k]);
        if not math.isfinite(v) or v<=0: raise ValueError(f'{k} must be finite positive')
    if not math.isfinite(float(fit['discovery_age_center'])): raise ValueError('invalid discovery age center')
    donors=_canonical_donors(fit)
    if not isinstance(provenance,dict) or set(provenance)!=PROVENANCE_KEYS or provenance.get('schema')!=PROVENANCE_SCHEMA: raise ValueError('invalid discovery provenance')
    for k in ['root_sha256','cell_payload_sha256','donor_metadata_sha256','feature_authority_sha256','membership_authority_sha256']:
        v=provenance.get(k)
        if not isinstance(v,str) or len(v)!=64 or any(c not in '0123456789abcdef' for c in v): raise ValueError(f'invalid provenance {k}')
    if provenance['feature_authority_sha256']!=EXPECTED_SPLIT_SHA256 or provenance['membership_authority_sha256']!=EXPECTED_CSV_SHA256: raise ValueError('provenance authority mismatch')
    if isinstance(provenance.get('cells'),bool) or not isinstance(provenance.get('cells'),(int,np.integer)) or int(provenance['cells'])<=0: raise ValueError('provenance cells invalid')
    if provenance.get('scoring_features')!=EXPECTED_FEATURES: raise ValueError('provenance feature count mismatch')
    if provenance.get('canonical_discovery_donors')!=donors: raise ValueError('provenance donor order mismatch')
    mapping=provenance.get('sex_utf8_mapping')
    if not isinstance(mapping,dict) or len(mapping)!=2 or sorted(mapping.values())!=[0,1] or any(not isinstance(k,str) or not k for k in mapping): raise ValueError('provenance sex mapping invalid')
    if provenance.get('cell_encoding')!='sparse_nonzero_index_u32be_count_i64be_v1': raise ValueError('provenance cell encoding mismatch')
    if provenance.get('normalization')!=PROVENANCE_NORMALIZATION or provenance.get('pseudobulk')!=PROVENANCE_PSEUDOBULK or provenance.get('aggregation_feature_chunk')!=PROVENANCE_CHUNK: raise ValueError('provenance mechanics mismatch')
    return beta,mu,sigma,mask,cv,exps,donors

def serialize_target_v2(outdir, fit:dict, provenance:dict, feature_split_csv) -> dict:
    out=Path(outdir)
    if out.exists() and any(out.iterdir()): raise ValueError('output directory must be absent or empty')
    out.mkdir(parents=True,exist_ok=True)
    beta,mu,sigma,mask,cv,exps,donors=_validate_fit(fit,provenance)
    feature=load_feature_authority(feature_split_csv); score=feature[feature.feature_role.eq('SCORING')].reset_index(drop=True)
    if len(score)!=EXPECTED_FEATURES: raise ValueError('scoring feature authority mismatch')
    _f64(out/'T0_TARGET_BETA_F64LE.bin',beta); _f64(out/'T0_TARGET_MU_F64LE.bin',mu); _f64(out/'T0_TARGET_SIGMA_F64LE.bin',sigma)
    (out/'T0_TARGET_DECISION_MASK_U8.bin').write_bytes(mask.astype(np.uint8).tobytes())
    _f64(out/'T0_TARGET_CV_MSE_F64LE.bin',cv); _f64(out/'T0_TARGET_MULTIPLIER_EXPONENTS_F64LE.bin',exps)
    score[['molecular_address_index','molecular_address_id','symbol','biotype']].to_csv(out/'T0_TARGET_ADDRESS_REGISTRY.csv',index=False,lineterminator='\n')
    meta={'schema':SCHEMA,'features':EXPECTED_FEATURES,'numeric_dtype':'float64_little_endian','selected_multiplier_index':int(fit['selected_multiplier_index']),'selected_multiplier_exponent':float(fit['selected_multiplier_exponent']),'final_lambda':float(fit['final_lambda']),'final_trace_scale':float(fit['final_trace_scale']),'response_residual_sd':float(fit['response_residual_sd']),'discovery_age_center':float(fit['discovery_age_center']),'canonical_donor_order':donors,'nuisance':'intercept + centered_age + centered_age_squared + binary_sex_utf8_0_1','learner':'donor_pseudobulk_nuisance_partialled_dual_ridge_LOODO_multiplier_v1'}
    (out/'T0_TARGET_METADATA.json').write_text(json.dumps(meta,sort_keys=True,separators=(',',':'))+'\n')
    (out/'T0_TARGET_DISCOVERY_PROVENANCE.json').write_text(json.dumps(provenance,sort_keys=True,separators=(',',':'))+'\n')
    with (out/'T0_TARGET_MANIFEST.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f,lineterminator='\n'); w.writerow(['filename','bytes','sha256'])
        for name in sorted(MEMBERS,key=lambda x:x.encode()):
            p=out/name; w.writerow([name,p.stat().st_size,sha256_file(p)])
    root=sha256_file(out/'T0_TARGET_MANIFEST.csv'); (out/'T0_TARGET_PACKAGE_ROOT_SHA256.txt').write_text(root+'\n')
    return {'schema':SCHEMA,'package_root_sha256':root,'files':len(MEMBERS),'discovery_provenance_root':provenance['root_sha256']}

def load_target_v2(outdir, feature_split_csv) -> dict:
    out=Path(outdir)
    root=verify_flat_package(out,MEMBERS,'T0_TARGET_MANIFEST.csv','T0_TARGET_PACKAGE_ROOT_SHA256.txt',label='target package')
    meta=json.loads((out/'T0_TARGET_METADATA.json').read_text(encoding='utf-8')); prov=json.loads((out/'T0_TARGET_DISCOVERY_PROVENANCE.json').read_text(encoding='utf-8'))
    meta_keys={'schema','features','numeric_dtype','selected_multiplier_index','selected_multiplier_exponent','final_lambda','final_trace_scale','response_residual_sd','discovery_age_center','canonical_donor_order','nuisance','learner'}
    if set(meta)!=meta_keys or meta.get('schema')!=SCHEMA or meta.get('features')!=EXPECTED_FEATURES or meta.get('numeric_dtype')!='float64_little_endian' or meta.get('nuisance')!='intercept + centered_age + centered_age_squared + binary_sex_utf8_0_1' or meta.get('learner')!='donor_pseudobulk_nuisance_partialled_dual_ridge_LOODO_multiplier_v1': raise ValueError('target metadata mismatch')
    g=EXPECTED_FEATURES
    def rd(name): return np.fromfile(out/name,dtype='<f8')
    mask_raw=np.fromfile(out/'T0_TARGET_DECISION_MASK_U8.bin',dtype=np.uint8)
    if mask_raw.shape!=(g,) or not np.isin(mask_raw,[0,1]).all(): raise ValueError('target decision mask bytes must be exactly 0/1')
    fit={'beta':rd('T0_TARGET_BETA_F64LE.bin'),'mu':rd('T0_TARGET_MU_F64LE.bin'),'sigma':rd('T0_TARGET_SIGMA_F64LE.bin'),'decision_gene_mask':mask_raw.astype(bool),'cv_mse_by_multiplier':rd('T0_TARGET_CV_MSE_F64LE.bin'),'multiplier_exponents':rd('T0_TARGET_MULTIPLIER_EXPONENTS_F64LE.bin'),'selected_multiplier_index':int(meta['selected_multiplier_index']),'selected_multiplier_exponent':float(meta['selected_multiplier_exponent']),'final_lambda':float(meta['final_lambda']),'final_trace_scale':float(meta['final_trace_scale']),'response_residual_sd':float(meta['response_residual_sd']),'discovery_age_center':float(meta['discovery_age_center']),'canonical_donor_order':np.asarray(meta['canonical_donor_order'])}
    _validate_fit(fit,prov)
    feature=load_feature_authority(feature_split_csv); expected_reg=feature.loc[feature.feature_role.eq('SCORING'),['molecular_address_index','molecular_address_id','symbol','biotype']].reset_index(drop=True).fillna('')
    got_reg=pd.read_csv(out/'T0_TARGET_ADDRESS_REGISTRY.csv').fillna('')
    if not got_reg.equals(expected_reg): raise ValueError('target address registry mismatch')
    return {'package_root_sha256':root,'fit':fit,'provenance':prov,'metadata':meta}
