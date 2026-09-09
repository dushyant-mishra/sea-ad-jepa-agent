from __future__ import annotations
import csv, hashlib, json, struct, tempfile
from pathlib import Path
from typing import Sequence
import numpy as np
import pandas as pd
try:
    import scipy.sparse as sp
except Exception:
    sp=None

from t0_package_integrity_v1 import verify_flat_package, sha256_file, is_hex64
from t0_feature_authority_v1 import load_feature_authority
from t0_primary_membership_v1 import load_membership, validate_cells_against_membership, validate_complete_role_cell_set
from t0_donor_role_authority_v2 import load_role_authority, verify_role_authority_against_inputs
from t0_stable_cell_key_v1 import parse_stable_key_exact
from t0_technical_registry_v2 import load_technical_registry

PRE_SCHEMA='JEPA_T0_PRETARGET_EXECUTION_INPUT_AUTHORITY_V1'
ADJ_SCHEMA='JEPA_T0_PREADJUDICATION_EXECUTION_INPUT_AUTHORITY_V1'
PRE_MEMBER='T0_PRETARGET_EXECUTION_INPUT_AUTHORITY.json'
ADJ_MEMBER='T0_PREADJUDICATION_EXECUTION_INPUT_AUTHORITY.json'
PRE_MANIFEST='T0_PRETARGET_EXECUTION_INPUT_MANIFEST.csv'
PRE_ROOT='T0_PRETARGET_EXECUTION_INPUT_PACKAGE_ROOT_SHA256.txt'
ADJ_MANIFEST='T0_PREADJUDICATION_EXECUTION_INPUT_MANIFEST.csv'
ADJ_ROOT='T0_PREADJUDICATION_EXECUTION_INPUT_PACKAGE_ROOT_SHA256.txt'
ROLE_META_COLUMNS=['donor_id','AT8_available','age','sex','technical_complete']
DISC_META_COLUMNS=['donor_id','AT8','age','sex']
CONF_BASE_COLUMNS=['donor_id','AT8','age','sex','IMMUNE_FRACTION']


def _put_bytes(h,b:bytes): h.update(struct.pack('>Q',len(b))); h.update(b)
def _put_str(h,s:str): _put_bytes(h,str(s).encode('utf-8'))

def _float64(h,x):
    a=np.asarray([float(x)],dtype='<f8')
    if not np.isfinite(a).all(): raise ValueError('nonfinite numeric authority value')
    h.update(a.tobytes())

def _canonical_table_digest(df:pd.DataFrame, columns:list[str], *, bool_columns:Sequence[str]=()) -> str:
    if list(df.columns)!=columns: raise ValueError(f'metadata schema must be exactly {columns}')
    q=df.copy(); q['donor_id']=q['donor_id'].astype(str)
    if q.donor_id.duplicated().any() or q.donor_id.isna().any() or q.donor_id.eq('').any(): raise ValueError('invalid donor IDs')
    q=q.sort_values('donor_id',key=lambda s:s.map(lambda x:x.encode('utf-8'))).reset_index(drop=True)
    h=hashlib.sha256(); _put_str(h,'T0_CANONICAL_DONOR_TABLE_V1');
    for c in columns: _put_str(h,c)
    bool_columns=set(bool_columns)
    for r in q.to_dict(orient='records'):
        _put_str(h,r['donor_id'])
        for c in columns[1:]:
            v=r[c]
            if c in bool_columns:
                if type(v) not in (bool,np.bool_): raise ValueError(f'{c} must be boolean')
                h.update(b'\x01' if bool(v) else b'\x00')
            elif c=='sex':
                if pd.isna(v) or str(v)=='': raise ValueError('invalid sex')
                _put_str(h,str(v))
            else:
                _float64(h,pd.to_numeric(v,errors='raise'))
    return h.hexdigest()


def _row_nonzero(counts,i,g):
    if sp is not None and sp.issparse(counts):
        row=counts.getrow(i).copy(); row.sum_duplicates(); row.sort_indices()
        idx=np.asarray(row.indices,dtype=np.int64); dat=np.asarray(row.data)
    else:
        A=np.asarray(counts)
        if A.ndim!=2 or A.shape[1]!=g: raise ValueError('raw count shape mismatch')
        row=np.asarray(A[i]); idx=np.flatnonzero(row).astype(np.int64); dat=row[idx]
    if np.any(idx<0) or np.any(idx>=g) or not np.isfinite(dat).all() or np.any(dat<0) or np.any(np.floor(dat)!=dat): raise ValueError('raw counts must be finite nonnegative integers')
    vals=np.asarray(dat,dtype=np.int64); nz=vals!=0
    return idx[nz],vals[nz]


def canonical_expression_digest(*,scalar_raw_counts,scalar_feature_ids,matrix_id,local_row,cell_id,donor_id,stable_key,source_library,feature_split_csv,membership_csv,expected_donors):
    feature=load_feature_authority(feature_split_csv); expected=feature.molecular_address_id.astype(str).tolist()
    if list(map(str,scalar_feature_ids))!=expected: raise ValueError('scalar feature authority mismatch')
    n=len(donor_id); g=len(expected)
    if getattr(scalar_raw_counts,'shape',None)!=(n,g): raise ValueError('scalar raw-count shape mismatch')
    arrays=[list(matrix_id),list(local_row),list(cell_id),list(donor_id),list(stable_key)]
    if any(len(x)!=n for x in arrays): raise ValueError('cell identity length mismatch')
    lib=np.asarray(source_library,dtype=np.float64)
    if lib.shape!=(n,) or not np.isfinite(lib).all() or np.any(lib<=0): raise ValueError('invalid source_library')
    membership=load_membership(membership_csv)
    validate_cells_against_membership(membership,matrix_id=matrix_id,local_row=local_row,cell_id=cell_id,donor_id=donor_id,stable_key=stable_key)
    validate_complete_role_cell_set(membership,expected_donors=expected_donors,donor_id=donor_id,stable_key=stable_key)
    donors=sorted(set(map(str,donor_id)),key=lambda x:x.encode('utf-8'))
    if donors!=sorted(map(str,expected_donors),key=lambda x:x.encode('utf-8')): raise ValueError('role donor set mismatch')
    keys=np.asarray([parse_stable_key_exact(x) for x in stable_key],dtype=np.int64)
    if len(np.unique(keys))!=n: raise ValueError('duplicate stable keys')
    order=np.argsort(keys,kind='mergesort')
    h=hashlib.sha256(); _put_str(h,'T0_FULL_SCALAR_EXECUTION_PAYLOAD_V1'); _put_str(h,str(g));
    for fid in expected: _put_str(h,fid)
    csr=None
    if sp is not None and sp.issparse(scalar_raw_counts):
        csr=scalar_raw_counts.tocsr(copy=True); csr.sum_duplicates(); csr.sort_indices()
        if csr.shape!=(n,g) or not np.isfinite(csr.data).all() or np.any(csr.data<0) or np.any(np.floor(csr.data)!=csr.data): raise ValueError('raw counts must be finite nonnegative integers')
    else:
        dense=np.asarray(scalar_raw_counts)
        if dense.shape!=(n,g) or not np.isfinite(dense).all() or np.any(dense<0) or np.any(np.floor(dense)!=dense): raise ValueError('raw counts must be finite nonnegative integers')
    for i0 in order:
        i=int(i0)
        if csr is not None:
            a,b=int(csr.indptr[i]),int(csr.indptr[i+1]); idx=np.asarray(csr.indices[a:b],dtype=np.int64); vals=np.asarray(csr.data[a:b],dtype=np.int64); nz=vals!=0; idx=idx[nz]; vals=vals[nz]
        else:
            row=dense[i]; idx=np.flatnonzero(row).astype(np.int64); vals=np.asarray(row[idx],dtype=np.int64)
        if int(vals.sum(dtype=np.int64))>lib[i]+1e-9: raise ValueError('raw counts exceed source_library')
        h.update(struct.pack('>q',int(keys[i]))); _put_str(h,str(matrix_id[i])); _put_str(h,str(local_row[i])); _put_str(h,str(cell_id[i])); _put_str(h,str(donor_id[i])); h.update(np.asarray([lib[i]],dtype='<f8').tobytes()); h.update(struct.pack('>I',len(idx)))
        for j,v in zip(idx,vals): h.update(struct.pack('>I',int(j))); h.update(struct.pack('>q',int(v)))
    return {'payload_sha256':h.hexdigest(),'cells':n,'scalar_features':g,'canonical_donors':donors}


def _write_package(outdir,member,manifest_name,root_name,obj):
    out=Path(outdir)
    if out.exists() and any(out.iterdir()): raise ValueError('authority output must be absent or empty')
    out.mkdir(parents=True,exist_ok=True); (out/member).write_text(json.dumps(obj,sort_keys=True,separators=(',',':'))+'\n',encoding='utf-8')
    with (out/manifest_name).open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f,lineterminator='\n'); p=out/member; w.writerow(['filename','bytes','sha256']); w.writerow([member,p.stat().st_size,sha256_file(p)])
    root=sha256_file(out/manifest_name); (out/root_name).write_text(root+'\n',encoding='utf-8')
    return root


def _require_hash_map(d):
    if not isinstance(d,dict) or not d or any(not isinstance(k,str) or not k or not is_hex64(v) for k,v in d.items()): raise ValueError('external source authority hashes invalid')
    return dict(sorted(d.items()))


def _role_support_from_membership(membership_csv):
    m=load_membership(membership_csv); s=m.groupby('donor_id').size().rename('cells').reset_index(); s.insert(0,'source','SEA_AD'); s.insert(2,'operator_index',31); return s


def _check_discovery_age_sex_against_role(role_metadata,discovery_metadata,role):
    r=role_metadata.copy(); r['donor_id']=r.donor_id.astype(str); d=discovery_metadata.copy(); d['donor_id']=d.donor_id.astype(str)
    rd=r.set_index('donor_id'); dd=d.set_index('donor_id')
    if sorted(dd.index,key=lambda x:x.encode())!=role['discovery_donors']: raise ValueError('discovery metadata donor set mismatch role authority')
    for donor in role['discovery_donors']:
        if float(dd.loc[donor,'age'])!=float(rd.loc[donor,'age']) or str(dd.loc[donor,'sex'])!=str(rd.loc[donor,'sex']): raise ValueError('discovery age/sex mismatch role metadata authority')


def build_pretarget_execution_authority(outdir,*,role_dir,role_metadata,discovery_scalar_raw_counts,scalar_feature_ids,discovery_matrix_id,discovery_local_row,discovery_cell_id,discovery_donor_id,discovery_stable_key,discovery_source_library,discovery_metadata,feature_split_csv,membership_csv,external_source_authority_hashes):
    role=load_role_authority(role_dir)
    if list(role_metadata.columns)!=ROLE_META_COLUMNS: raise ValueError('role metadata schema mismatch')
    # Prove these are the exact values that could have generated the frozen role package.
    verify_role_authority_against_inputs(role_dir,_role_support_from_membership(membership_csv),role_metadata,role['metadata']['input_authority_hashes'])
    if list(discovery_metadata.columns)!=DISC_META_COLUMNS: raise ValueError('discovery metadata schema mismatch')
    _check_discovery_age_sex_against_role(role_metadata,discovery_metadata,role)
    role_meta_sha=_canonical_table_digest(role_metadata,ROLE_META_COLUMNS,bool_columns=['AT8_available','technical_complete'])
    disc_meta_sha=_canonical_table_digest(discovery_metadata,DISC_META_COLUMNS)
    expr=canonical_expression_digest(scalar_raw_counts=discovery_scalar_raw_counts,scalar_feature_ids=scalar_feature_ids,matrix_id=discovery_matrix_id,local_row=discovery_local_row,cell_id=discovery_cell_id,donor_id=discovery_donor_id,stable_key=discovery_stable_key,source_library=discovery_source_library,feature_split_csv=feature_split_csv,membership_csv=membership_csv,expected_donors=role['discovery_donors'])
    obj={'schema':PRE_SCHEMA,'donor_role_package_root_sha256':role['package_root_sha256'],'role_metadata_payload_sha256':role_meta_sha,'discovery_metadata_payload_sha256':disc_meta_sha,'discovery_expression_payload':expr,'external_source_authority_hashes':_require_hash_map(external_source_authority_hashes),'chronology':'BUILT_AFTER_ROLE_FREEZE__BEFORE_TARGET_FIT','real_execution_ready':False}
    root=_write_package(outdir,PRE_MEMBER,PRE_MANIFEST,PRE_ROOT,obj); return {'package_root_sha256':root,'authority':obj}


def load_pretarget_execution_authority(outdir):
    out=Path(outdir); root=verify_flat_package(out,{PRE_MEMBER},PRE_MANIFEST,PRE_ROOT,label='pretarget execution authority'); obj=json.loads((out/PRE_MEMBER).read_text())
    keys={'schema','donor_role_package_root_sha256','role_metadata_payload_sha256','discovery_metadata_payload_sha256','discovery_expression_payload','external_source_authority_hashes','chronology','real_execution_ready'}
    if set(obj)!=keys or obj.get('schema')!=PRE_SCHEMA or obj.get('chronology')!='BUILT_AFTER_ROLE_FREEZE__BEFORE_TARGET_FIT' or obj.get('real_execution_ready') is not False: raise ValueError('pretarget authority metadata mismatch')
    for k in ['donor_role_package_root_sha256','role_metadata_payload_sha256','discovery_metadata_payload_sha256']:
        if not is_hex64(obj.get(k)): raise ValueError('pretarget digest invalid')
    _require_hash_map(obj.get('external_source_authority_hashes'))
    e=obj.get('discovery_expression_payload');
    if not isinstance(e,dict) or not is_hex64(e.get('payload_sha256')): raise ValueError('pretarget expression payload invalid')
    return {'package_root_sha256':root,'authority':obj}


def verify_pretarget_execution_authority(outdir,*,role_dir,role_metadata,discovery_scalar_raw_counts,scalar_feature_ids,discovery_matrix_id,discovery_local_row,discovery_cell_id,discovery_donor_id,discovery_stable_key,discovery_source_library,discovery_metadata,feature_split_csv,membership_csv):
    a=load_pretarget_execution_authority(outdir); role=load_role_authority(role_dir); obj=a['authority']
    if obj['donor_role_package_root_sha256']!=role['package_root_sha256']: raise ValueError('pretarget authority role root mismatch')
    verify_role_authority_against_inputs(role_dir,_role_support_from_membership(membership_csv),role_metadata,role['metadata']['input_authority_hashes'])
    _check_discovery_age_sex_against_role(role_metadata,discovery_metadata,role)
    if _canonical_table_digest(role_metadata,ROLE_META_COLUMNS,bool_columns=['AT8_available','technical_complete'])!=obj['role_metadata_payload_sha256']: raise ValueError('role metadata payload mismatch')
    if _canonical_table_digest(discovery_metadata,DISC_META_COLUMNS)!=obj['discovery_metadata_payload_sha256']: raise ValueError('discovery metadata payload mismatch')
    expr=canonical_expression_digest(scalar_raw_counts=discovery_scalar_raw_counts,scalar_feature_ids=scalar_feature_ids,matrix_id=discovery_matrix_id,local_row=discovery_local_row,cell_id=discovery_cell_id,donor_id=discovery_donor_id,stable_key=discovery_stable_key,source_library=discovery_source_library,feature_split_csv=feature_split_csv,membership_csv=membership_csv,expected_donors=role['discovery_donors'])
    if expr!=obj['discovery_expression_payload']: raise ValueError('discovery expression payload mismatch')
    return a


def build_preadjudication_execution_authority(outdir,*,pretarget_authority_dir,role_dir,target_root_sha256,tail_root_sha256,discovery_authority_root_sha256,technical_registry_dir,family_registry_dir,confirmation_scalar_raw_counts,scalar_feature_ids,confirmation_matrix_id,confirmation_local_row,confirmation_cell_id,confirmation_donor_id,confirmation_stable_key,confirmation_source_library,confirmation_metadata,feature_split_csv,membership_csv,external_source_authority_hashes):
    pre=load_pretarget_execution_authority(pretarget_authority_dir); role=load_role_authority(role_dir); tech=load_technical_registry(technical_registry_dir)
    from t0_target_family_authority_v3 import load_primary_only_family_v3
    family=load_primary_only_family_v3(family_registry_dir)
    required=CONF_BASE_COLUMNS+sum((cols for cols in tech['blocks'].values()),[])
    if list(confirmation_metadata.columns)!=required: raise ValueError(f'confirmation metadata schema must be exactly {required}')
    cm=confirmation_metadata.copy(); cm['donor_id']=cm.donor_id.astype(str)
    if sorted(cm.donor_id,key=lambda x:x.encode())!=role['confirmation_donors']: raise ValueError('confirmation metadata donor set mismatch')
    conf_meta_sha=_canonical_table_digest(cm,required)
    expr=canonical_expression_digest(scalar_raw_counts=confirmation_scalar_raw_counts,scalar_feature_ids=scalar_feature_ids,matrix_id=confirmation_matrix_id,local_row=confirmation_local_row,cell_id=confirmation_cell_id,donor_id=confirmation_donor_id,stable_key=confirmation_stable_key,source_library=confirmation_source_library,feature_split_csv=feature_split_csv,membership_csv=membership_csv,expected_donors=role['confirmation_donors'])
    roots={'pretarget_execution_input':pre['package_root_sha256'],'donor_role':role['package_root_sha256'],'target':target_root_sha256,'tail':tail_root_sha256,'discovery_authority':discovery_authority_root_sha256,'technical_registry':tech['package_root_sha256'],'target_family':family['package_root_sha256']}
    if any(not is_hex64(v) for v in roots.values()): raise ValueError('upstream root invalid')
    obj={'schema':ADJ_SCHEMA,'upstream_package_roots':roots,'confirmation_metadata_columns':required,'confirmation_metadata_payload_sha256':conf_meta_sha,'confirmation_expression_payload':expr,'technical_blocks':tech['blocks'],'family_status_authority_sha256':family['authority']['rare5_status_authority_sha256'],'family_historical_rare5_status':family['authority']['historical_rare5_status'],'external_source_authority_hashes':_require_hash_map(external_source_authority_hashes),'chronology':'BUILT_AFTER_TARGET_TAIL_TECHNICAL_FAMILY_FREEZE__BEFORE_CONFIRMATION_INFERENCE','real_execution_ready':False}
    root=_write_package(outdir,ADJ_MEMBER,ADJ_MANIFEST,ADJ_ROOT,obj); return {'package_root_sha256':root,'authority':obj}


def load_preadjudication_execution_authority(outdir):
    out=Path(outdir); root=verify_flat_package(out,{ADJ_MEMBER},ADJ_MANIFEST,ADJ_ROOT,label='preadjudication execution authority'); obj=json.loads((out/ADJ_MEMBER).read_text())
    keys={'schema','upstream_package_roots','confirmation_metadata_columns','confirmation_metadata_payload_sha256','confirmation_expression_payload','technical_blocks','family_status_authority_sha256','family_historical_rare5_status','external_source_authority_hashes','chronology','real_execution_ready'}
    if set(obj)!=keys or obj.get('schema')!=ADJ_SCHEMA or obj.get('chronology')!='BUILT_AFTER_TARGET_TAIL_TECHNICAL_FAMILY_FREEZE__BEFORE_CONFIRMATION_INFERENCE' or obj.get('real_execution_ready') is not False: raise ValueError('preadjudication authority metadata mismatch')
    if any(not is_hex64(v) for v in obj.get('upstream_package_roots',{}).values()) or not is_hex64(obj.get('confirmation_metadata_payload_sha256')) or not is_hex64(obj.get('family_status_authority_sha256')): raise ValueError('preadjudication digest invalid')
    _require_hash_map(obj.get('external_source_authority_hashes'))
    return {'package_root_sha256':root,'authority':obj}


def verify_preadjudication_execution_authority(outdir,*,pretarget_authority_dir,role_dir,target_root_sha256,tail_root_sha256,discovery_authority_root_sha256,technical_registry_dir,family_registry_dir,confirmation_scalar_raw_counts,scalar_feature_ids,confirmation_matrix_id,confirmation_local_row,confirmation_cell_id,confirmation_donor_id,confirmation_stable_key,confirmation_source_library,confirmation_metadata,feature_split_csv,membership_csv):
    a=load_preadjudication_execution_authority(outdir); pre=load_pretarget_execution_authority(pretarget_authority_dir); role=load_role_authority(role_dir); tech=load_technical_registry(technical_registry_dir)
    from t0_target_family_authority_v3 import load_primary_only_family_v3
    family=load_primary_only_family_v3(family_registry_dir); obj=a['authority']
    expected_roots={'pretarget_execution_input':pre['package_root_sha256'],'donor_role':role['package_root_sha256'],'target':target_root_sha256,'tail':tail_root_sha256,'discovery_authority':discovery_authority_root_sha256,'technical_registry':tech['package_root_sha256'],'target_family':family['package_root_sha256']}
    if obj['upstream_package_roots']!=expected_roots: raise ValueError('preadjudication upstream root mismatch')
    if obj['technical_blocks']!=tech['blocks']: raise ValueError('technical block authority mismatch')
    if obj['family_status_authority_sha256']!=family['authority']['rare5_status_authority_sha256'] or obj['family_historical_rare5_status']!=family['authority']['historical_rare5_status']: raise ValueError('family freshness authority mismatch')
    required=CONF_BASE_COLUMNS+sum((cols for cols in tech['blocks'].values()),[])
    if list(confirmation_metadata.columns)!=required or required!=obj['confirmation_metadata_columns']: raise ValueError('confirmation metadata schema mismatch')
    if _canonical_table_digest(confirmation_metadata,required)!=obj['confirmation_metadata_payload_sha256']: raise ValueError('confirmation metadata payload mismatch')
    expr=canonical_expression_digest(scalar_raw_counts=confirmation_scalar_raw_counts,scalar_feature_ids=scalar_feature_ids,matrix_id=confirmation_matrix_id,local_row=confirmation_local_row,cell_id=confirmation_cell_id,donor_id=confirmation_donor_id,stable_key=confirmation_stable_key,source_library=confirmation_source_library,feature_split_csv=feature_split_csv,membership_csv=membership_csv,expected_donors=role['confirmation_donors'])
    if expr!=obj['confirmation_expression_payload']: raise ValueError('confirmation expression payload mismatch')
    return a
