from __future__ import annotations
import numpy as np
try:
    import scipy.sparse as sp
except Exception:
    sp=None
from t0_execution_input_authority_v1 import verify_pretarget_execution_authority, verify_preadjudication_execution_authority
from t0_feature_authority_v1 import load_feature_authority
from t0_primary_membership_v1 import load_membership,validate_cells_against_membership,validate_complete_role_cell_set
from t0_discovery_fit_v2 import verify_target_v2_against_raw
from t0_target_serializer_v2 import load_target_v2
from t0_tail_authority_v1 import verify_tail_authority_against_loaded_target,load_tail_authority
from t0_confirmation_raw_v1 import confirmation_summaries_from_raw
from t0_tail_preflight_raw_v1 import raw_tail_preflight
from t0_discovery_authority_v1 import load_discovery_authority
from t0_donor_role_authority_v2 import load_role_authority
from t0_technical_registry_v3 import load_technical_registry_v3
from t0_target_family_authority_v3 import load_primary_only_family_v3,STATUS_SCHEMA,ALLOWED_STATUS
from t0_adjudicator_v1 import adjudicate_donor_table_non_authoritative
import hashlib,json
from pathlib import Path


def _verify_status_file(path,expected_sha):
    raw=Path(path).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=expected_sha: raise ValueError('rare5 status authority bytes changed after family freeze')
    obj=json.loads(raw.decode('utf-8'))
    if obj.get('schema')!=STATUS_SCHEMA or obj.get('historical_rare5_status')!=ALLOWED_STATUS or obj.get('decision_capable') is not False: raise ValueError('rare5 status is no longer non-decision-capable')


def _adjudicate_from_raw_v2(*,allow_synthetic_test_fixture,pretarget_authority_dir,preadjudication_authority_dir,role_metadata,rare5_status_authority_file,target_dir,tail_dir,role_dir,discovery_authority_dir,technical_registry_dir,family_registry_dir,discovery_scalar_raw_counts,scalar_feature_ids,discovery_matrix_id,discovery_local_row,discovery_cell_id,discovery_donor_id,discovery_stable_key,discovery_source_library,discovery_metadata,confirmation_scalar_raw_counts,confirmation_matrix_id,confirmation_local_row,confirmation_cell_id,confirmation_donor_id,confirmation_stable_key,confirmation_source_library,confirmation_metadata,feature_split_csv,membership_csv):
    """V19 conclusion-bearing adjudication. Every external input must reproduce frozen execution-input authorities."""
    pre=verify_pretarget_execution_authority(pretarget_authority_dir,role_dir=role_dir,role_metadata=role_metadata,discovery_scalar_raw_counts=discovery_scalar_raw_counts,scalar_feature_ids=scalar_feature_ids,discovery_matrix_id=discovery_matrix_id,discovery_local_row=discovery_local_row,discovery_cell_id=discovery_cell_id,discovery_donor_id=discovery_donor_id,discovery_stable_key=discovery_stable_key,discovery_source_library=discovery_source_library,discovery_metadata=discovery_metadata,feature_split_csv=feature_split_csv,membership_csv=membership_csv)
    if pre['authority']['real_execution_ready'] is not True and not allow_synthetic_test_fixture: raise ValueError('STOP_T0_V19_EXTERNAL_INPUT_AUTHORITY_NOT_MATERIALIZED')
    role=load_role_authority(role_dir); link=load_discovery_authority(discovery_authority_dir,target_dir,role_dir,feature_split_csv); tech=load_technical_registry_v3(technical_registry_dir); family=load_primary_only_family_v3(family_registry_dir); _verify_status_file(rare5_status_authority_file,family['authority']['rare5_status_authority_sha256'])
    feature=load_feature_authority(feature_split_csv); expected_scalar=feature.molecular_address_id.astype(str).tolist()
    if list(map(str,scalar_feature_ids))!=expected_scalar: raise ValueError('scalar feature authority mismatch')
    if getattr(discovery_scalar_raw_counts,'shape',None)!=(len(discovery_donor_id),len(expected_scalar)) or getattr(confirmation_scalar_raw_counts,'shape',None)!=(len(confirmation_donor_id),len(expected_scalar)): raise ValueError('canonical scalar matrix shape mismatch')
    membership=load_membership(membership_csv)
    validate_cells_against_membership(membership,matrix_id=discovery_matrix_id,local_row=discovery_local_row,cell_id=discovery_cell_id,donor_id=discovery_donor_id,stable_key=discovery_stable_key); validate_complete_role_cell_set(membership,expected_donors=role['discovery_donors'],donor_id=discovery_donor_id,stable_key=discovery_stable_key)
    validate_cells_against_membership(membership,matrix_id=confirmation_matrix_id,local_row=confirmation_local_row,cell_id=confirmation_cell_id,donor_id=confirmation_donor_id,stable_key=confirmation_stable_key); validate_complete_role_cell_set(membership,expected_donors=role['confirmation_donors'],donor_id=confirmation_donor_id,stable_key=confirmation_stable_key)
    score_idx=np.flatnonzero(feature.feature_role.to_numpy()=='SCORING')
    def sel(X,idx): return X[:,idx] if sp is not None and sp.issparse(X) else np.asarray(X)[:,idx]
    dkw=dict(raw_counts=sel(discovery_scalar_raw_counts,score_idx),feature_ids=feature.loc[score_idx,'molecular_address_id'].astype(str).tolist(),matrix_id=discovery_matrix_id,local_row=discovery_local_row,cell_id=discovery_cell_id,donor_id=discovery_donor_id,stable_key=discovery_stable_key,source_library=discovery_source_library,donor_metadata=discovery_metadata,feature_split_csv=feature_split_csv,membership_csv=membership_csv)
    verify_target_v2_against_raw(target_dir,**dkw); loaded_target=load_target_v2(target_dir,feature_split_csv); verify_tail_authority_against_loaded_target(tail_dir,loaded_target,raw_counts=dkw['raw_counts'],donor_id=discovery_donor_id,stable_key=discovery_stable_key,source_library=discovery_source_library)
    tail=load_tail_authority(tail_dir,loaded_target['package_root_sha256'])
    adj=verify_preadjudication_execution_authority(preadjudication_authority_dir,pretarget_authority_dir=pretarget_authority_dir,role_dir=role_dir,target_root_sha256=loaded_target['package_root_sha256'],tail_root_sha256=tail['package_root_sha256'],discovery_authority_root_sha256=link['package_root_sha256'],technical_registry_dir=technical_registry_dir,family_registry_dir=family_registry_dir,confirmation_scalar_raw_counts=confirmation_scalar_raw_counts,scalar_feature_ids=scalar_feature_ids,confirmation_matrix_id=confirmation_matrix_id,confirmation_local_row=confirmation_local_row,confirmation_cell_id=confirmation_cell_id,confirmation_donor_id=confirmation_donor_id,confirmation_stable_key=confirmation_stable_key,confirmation_source_library=confirmation_source_library,confirmation_metadata=confirmation_metadata,feature_split_csv=feature_split_csv,membership_csv=membership_csv)
    if adj['authority']['real_execution_ready'] is not True and not allow_synthetic_test_fixture: raise ValueError('STOP_T0_V19_EXTERNAL_INPUT_AUTHORITY_NOT_MATERIALIZED')
    cs=confirmation_summaries_from_raw(target_dir=target_dir,tail_dir=tail_dir,scalar_raw_counts=confirmation_scalar_raw_counts,scalar_feature_ids=scalar_feature_ids,matrix_id=confirmation_matrix_id,local_row=confirmation_local_row,cell_id=confirmation_cell_id,donor_id=confirmation_donor_id,stable_key=confirmation_stable_key,source_library=confirmation_source_library,feature_split_csv=feature_split_csv,membership_csv=membership_csv,expected_confirmation_donors=role['confirmation_donors'],require_complete_membership=True)
    hold=np.flatnonzero(feature.feature_role.to_numpy()=='COHERENCE_HOLDOUT')
    preflight=raw_tail_preflight(discovery_holdout_raw_counts=sel(discovery_scalar_raw_counts,hold),discovery_donor_id=discovery_donor_id,discovery_stable_key=discovery_stable_key,discovery_source_library=discovery_source_library,confirmation_holdout_raw_counts=sel(confirmation_scalar_raw_counts,hold),confirmation_donor_id=confirmation_donor_id,confirmation_stable_key=confirmation_stable_key,confirmation_source_library=confirmation_source_library,confirmation_summaries=cs)
    out=adjudicate_donor_table_non_authoritative(cs['donor_table'],confirmation_metadata,preflight,tech['blocks'])
    out.update({'target_package_root_sha256':cs['target_package_root_sha256'],'tail_package_root_sha256':cs['tail_package_root_sha256'],'canonical_confirmation_donors':cs['canonical_confirmation_donors'],'donor_role_package_root_sha256':role['package_root_sha256'],'discovery_authority_package_root_sha256':link['package_root_sha256'],'technical_registry_package_root_sha256':tech['package_root_sha256'],'target_family_package_root_sha256':family['package_root_sha256'],'pretarget_execution_input_package_root_sha256':pre['package_root_sha256'],'preadjudication_execution_input_package_root_sha256':adj['package_root_sha256'],'rare5_status_authority_sha256':family['authority']['rare5_status_authority_sha256'],'external_input_authority_enforced':True})
    return out


def adjudicate_from_raw_v2(**kwargs):
    """Production V19 adjudicator. No caller override for synthetic authority."""
    return _adjudicate_from_raw_v2(allow_synthetic_test_fixture=False,**kwargs)

def adjudicate_from_raw_v2_for_test(**kwargs):
    """Explicit synthetic regression entrypoint; never production authority."""
    return _adjudicate_from_raw_v2(allow_synthetic_test_fixture=True,**kwargs)
