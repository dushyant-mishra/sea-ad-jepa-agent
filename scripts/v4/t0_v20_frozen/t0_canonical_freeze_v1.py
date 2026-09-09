from __future__ import annotations
import numpy as np
try:
    import scipy.sparse as sp
except Exception:
    sp=None
from t0_donor_role_authority_v2 import load_role_authority
from t0_discovery_fit_v2 import fit_and_serialize_target_v2
from t0_discovery_authority_v1 import build_discovery_authority,load_discovery_authority
from t0_tail_authority_v1 import freeze_tail_authority
from t0_feature_authority_v1 import load_feature_authority
from t0_primary_membership_v1 import load_membership,validate_cells_against_membership,validate_complete_role_cell_set


def _select(X,idx):
    return X[:,idx] if sp is not None and sp.issparse(X) else np.asarray(X)[:,idx]


def _validate_scalar_source(*,scalar_raw_counts,scalar_feature_ids,feature_split_csv):
    f=load_feature_authority(feature_split_csv); expected=f.molecular_address_id.astype(str).tolist()
    if list(map(str,scalar_feature_ids))!=expected: raise ValueError('canonical scalar feature order mismatch')
    if getattr(scalar_raw_counts,'shape',None)!=(getattr(scalar_raw_counts,'shape',(None,None))[0],len(expected)): raise ValueError('canonical scalar matrix feature count mismatch')
    return f


def freeze_target_after_role(*,target_dir,discovery_authority_dir,role_dir,feature_split_csv,membership_csv,scalar_raw_counts,scalar_feature_ids,matrix_id,local_row,cell_id,donor_id,stable_key,source_library,donor_metadata):
    """Canonical conclusion-bearing target freeze from the full 35,076 scalar-address matrix."""
    role=load_role_authority(role_dir); membership=load_membership(membership_csv)
    donors=sorted(set(map(str,donor_id)),key=lambda x:x.encode('utf-8'))
    if donors!=role['discovery_donors']: raise ValueError('raw discovery donor set must equal finalized role authority')
    validate_cells_against_membership(membership,matrix_id=matrix_id,local_row=local_row,cell_id=cell_id,donor_id=donor_id,stable_key=stable_key)
    validate_complete_role_cell_set(membership,expected_donors=role['discovery_donors'],donor_id=donor_id,stable_key=stable_key)
    f=_validate_scalar_source(scalar_raw_counts=scalar_raw_counts,scalar_feature_ids=scalar_feature_ids,feature_split_csv=feature_split_csv)
    score_idx=np.flatnonzero(f.feature_role.to_numpy()=='SCORING')
    kwargs=dict(raw_counts=_select(scalar_raw_counts,score_idx),feature_ids=f.loc[score_idx,'molecular_address_id'].astype(str).tolist(),matrix_id=matrix_id,local_row=local_row,cell_id=cell_id,donor_id=donor_id,stable_key=stable_key,source_library=source_library,donor_metadata=donor_metadata,feature_split_csv=feature_split_csv,membership_csv=membership_csv)
    r=fit_and_serialize_target_v2(target_dir,**kwargs)
    link=build_discovery_authority(discovery_authority_dir,target_dir,role_dir,feature_split_csv)
    return {'target':r,'discovery_authority':link,'donor_role_package_root_sha256':role['package_root_sha256']}


def freeze_tail_after_discovery_authority(*,tail_dir,discovery_authority_dir,target_dir,role_dir,feature_split_csv,membership_csv,scalar_raw_counts,scalar_feature_ids,matrix_id,local_row,cell_id,donor_id,stable_key,source_library,donor_metadata):
    """Canonical conclusion-bearing tail freeze from the same full scalar matrix and role cells."""
    link=load_discovery_authority(discovery_authority_dir,target_dir,role_dir,feature_split_csv); membership=load_membership(membership_csv)
    donors=sorted(set(map(str,donor_id)),key=lambda x:x.encode('utf-8'))
    if donors!=link['discovery_donors']: raise ValueError('tail raw donor set must equal discovery authority')
    validate_cells_against_membership(membership,matrix_id=matrix_id,local_row=local_row,cell_id=cell_id,donor_id=donor_id,stable_key=stable_key)
    validate_complete_role_cell_set(membership,expected_donors=link['discovery_donors'],donor_id=donor_id,stable_key=stable_key)
    f=_validate_scalar_source(scalar_raw_counts=scalar_raw_counts,scalar_feature_ids=scalar_feature_ids,feature_split_csv=feature_split_csv); score_idx=np.flatnonzero(f.feature_role.to_numpy()=='SCORING')
    kwargs=dict(raw_counts=_select(scalar_raw_counts,score_idx),feature_ids=f.loc[score_idx,'molecular_address_id'].astype(str).tolist(),matrix_id=matrix_id,local_row=local_row,cell_id=cell_id,donor_id=donor_id,stable_key=stable_key,source_library=source_library,donor_metadata=donor_metadata,feature_split_csv=feature_split_csv,membership_csv=membership_csv)
    return freeze_tail_authority(tail_dir,target_dir,**kwargs)
