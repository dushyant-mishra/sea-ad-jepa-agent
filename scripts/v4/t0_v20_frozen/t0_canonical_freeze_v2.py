from __future__ import annotations
from t0_execution_input_authority_v1 import verify_pretarget_execution_authority
from t0_canonical_freeze_v1 import freeze_target_after_role, freeze_tail_after_discovery_authority
STOP='STOP_T0_V19_EXTERNAL_INPUT_AUTHORITY_NOT_MATERIALIZED'

def _verified(pretarget_authority_dir,role_metadata,kwargs,allow_synthetic_test_fixture):
    a=verify_pretarget_execution_authority(pretarget_authority_dir,role_dir=kwargs['role_dir'],role_metadata=role_metadata,discovery_scalar_raw_counts=kwargs['scalar_raw_counts'],scalar_feature_ids=kwargs['scalar_feature_ids'],discovery_matrix_id=kwargs['matrix_id'],discovery_local_row=kwargs['local_row'],discovery_cell_id=kwargs['cell_id'],discovery_donor_id=kwargs['donor_id'],discovery_stable_key=kwargs['stable_key'],discovery_source_library=kwargs['source_library'],discovery_metadata=kwargs['donor_metadata'],feature_split_csv=kwargs['feature_split_csv'],membership_csv=kwargs['membership_csv'])
    if a['authority']['real_execution_ready'] is not True and not allow_synthetic_test_fixture: raise ValueError(STOP)
    return a

def _freeze_target(pretarget_authority_dir,role_metadata,kwargs,allow):
    a=_verified(pretarget_authority_dir,role_metadata,kwargs,allow); r=freeze_target_after_role(**kwargs); r['pretarget_execution_input_package_root_sha256']=a['package_root_sha256']; r['external_input_authority_enforced']=True; return r

def freeze_target_after_role_v2(*,pretarget_authority_dir,role_metadata,**kwargs):
    """Production V19 target freeze. Synthetic/test authority can never satisfy this entrypoint."""
    return _freeze_target(pretarget_authority_dir,role_metadata,kwargs,False)

def freeze_target_after_role_v2_for_test(*,pretarget_authority_dir,role_metadata,**kwargs):
    """Explicit synthetic regression entrypoint; never production authority."""
    return _freeze_target(pretarget_authority_dir,role_metadata,kwargs,True)

def _freeze_tail(pretarget_authority_dir,role_metadata,kwargs,allow):
    a=_verified(pretarget_authority_dir,role_metadata,kwargs,allow); r=freeze_tail_after_discovery_authority(**kwargs); r['pretarget_execution_input_package_root_sha256']=a['package_root_sha256']; r['external_input_authority_enforced']=True; return r

def freeze_tail_after_discovery_authority_v2(*,pretarget_authority_dir,role_metadata,**kwargs):
    """Production V19 tail freeze. Synthetic/test authority can never satisfy this entrypoint."""
    return _freeze_tail(pretarget_authority_dir,role_metadata,kwargs,False)

def freeze_tail_after_discovery_authority_v2_for_test(*,pretarget_authority_dir,role_metadata,**kwargs):
    return _freeze_tail(pretarget_authority_dir,role_metadata,kwargs,True)
