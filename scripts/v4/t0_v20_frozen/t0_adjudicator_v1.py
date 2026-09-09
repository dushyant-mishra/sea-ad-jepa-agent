from __future__ import annotations
import numpy as np
import pandas as pd
try:
    import scipy.sparse as sp
except Exception:
    sp=None
from t0_feature_authority_v1 import load_feature_authority
from t0_discovery_fit_v2 import verify_target_v2_against_raw
from t0_tail_authority_v1 import verify_tail_authority_against_loaded_target
from t0_confirmation_raw_v1 import confirmation_summaries_from_raw
from t0_tail_preflight_raw_v1 import raw_tail_preflight
from t0_metadata_coding_v1 import encode_binary_utf8
from t0_fl_permutation_authority_v1 import confirmation_permutation_matrix
from t0_inference_safe_v1 import safe_studentized_fl
from t0_tail_hc3_t_v1 import safe_tail_hc3_t
from t0_decision_v1 import decide_state,decide_tail,STATE_POS_ALPHA,TAIL_POS_ALPHA,NEG_ALPHA
from t0_discovery_authority_v1 import load_discovery_authority
from t0_donor_role_authority_v2 import load_role_authority
from t0_technical_registry_v2 import load_technical_registry
from t0_target_family_authority_v2 import load_primary_only_family
from t0_primary_membership_v1 import load_membership,validate_cells_against_membership,validate_complete_role_cell_set


def _nuisance(age,sex_labels):
    age=np.asarray(age,dtype=np.float64)
    if age.ndim!=1 or not np.isfinite(age).all(): raise ValueError('invalid age')
    sex,mapping=encode_binary_utf8(sex_labels)
    c=float(np.mean(age)); ac=age-c; z=np.c_[np.ones(len(age)),ac,ac*ac,sex]
    if np.linalg.matrix_rank(z)!=z.shape[1]: raise ValueError('rank-deficient primary nuisance design')
    return z,mapping,c


def _candidate(r,pos_alpha):
    if not r.get('estimable',False): return None
    if float(r['beta'])>0 and float(r['p_upper'])<=pos_alpha: return 'positive'
    if float(r['beta'])<0 and float(r['p_lower'])<=NEG_ALPHA: return 'negative'
    return None


def _run(y,reduced,pred,P): return safe_studentized_fl(np.asarray(y,float),np.asarray(reduced,float),np.asarray(pred,float),P)


def adjudicate_donor_table_non_authoritative(donor_table:pd.DataFrame,confirmation_metadata:pd.DataFrame,tail_preflight:dict,extra_technical_blocks:dict[str,list[str]]|None=None) -> dict:
    """Statistical primitive. Canonical use is through adjudicate_from_raw()."""
    base_cols=['donor_id','AT8','age','sex','IMMUNE_FRACTION']
    if not all(c in confirmation_metadata.columns for c in base_cols): raise ValueError('confirmation metadata missing mandatory columns')
    dt=donor_table.copy(); md=confirmation_metadata.copy(); dt['donor_id']=dt.donor_id.astype(str); md['donor_id']=md.donor_id.astype(str)
    if dt.donor_id.duplicated().any() or md.donor_id.duplicated().any(): raise ValueError('duplicate donor metadata')
    donors=sorted(dt.donor_id,key=lambda x:x.encode('utf-8'))
    if len(donors)!=18 or set(md.donor_id)!=set(donors): raise ValueError('confirmation donor set mismatch')
    dt=dt.set_index('donor_id').loc[donors].reset_index(); md=md.set_index('donor_id').loc[donors].reset_index()
    y=pd.to_numeric(md.AT8,errors='raise').to_numpy(float); age=pd.to_numeric(md.age,errors='raise').to_numpy(float)
    if not np.isfinite(y).all() or np.any(y<0): raise ValueError('invalid AT8')
    immune=pd.to_numeric(md.IMMUNE_FRACTION,errors='raise').to_numpy(float)
    if not np.isfinite(immune).all() or np.any((immune<0)|(immune>1)): raise ValueError('IMMUNE_FRACTION outside [0,1]')
    z,sexmap,agecenter=_nuisance(age,md.sex.tolist()); P=confirmation_permutation_matrix(donors)
    state=dt.STATE_SCORE.to_numpy(float); qdepth=dt.Q_DEPTH.to_numpy(float); qdetect=dt.Q_DETECT.to_numpy(float)
    if not np.isfinite(np.c_[state,qdepth,qdetect]).all() or np.any((qdetect<0)|(qdetect>1)): raise ValueError('invalid state/measurement donor summaries')
    primary=_run(y,z,state,P); direction=_candidate(primary,STATE_POS_ALPHA)
    if direction is None:
        return {'state_terminal':'TARGET_UNDERDETERMINED_INTERNAL','tail_terminal':'RARE_TAIL_UNDERDETERMINED_INTERNAL','state_primary':primary,'tail_primary':None,'tail_disease_test_run':False,'sex_mapping':sexmap,'age_center':agecenter}
    comp=_run(y,np.c_[z,immune],state,P); measurements=[_run(y,np.c_[z,qdepth,qdetect],state,P)]; measurement_names=['Q_DEPTH+Q_DETECT']
    extra_technical_blocks=extra_technical_blocks or {}
    for name,cols in extra_technical_blocks.items():
        if not isinstance(name,str) or not name or not isinstance(cols,list) or not cols: raise ValueError('invalid technical block registry')
        if any(c not in md.columns for c in cols): raise ValueError(f'missing technical block columns for {name}')
        A=md[cols].apply(pd.to_numeric,errors='raise').to_numpy(float)
        if not np.isfinite(A).all(): raise ValueError(f'nonfinite technical block {name}')
        measurements.append(_run(y,np.c_[z,qdepth,qdetect,A],state,P)); measurement_names.append(name)
    state_terminal=decide_state(primary,comp,measurements)
    if state_terminal!='BROAD_IMMUNE_EXPRESSION_TARGET_SUPPORTED_INTERNAL':
        return {'state_terminal':state_terminal,'tail_terminal':'RARE_TAIL_UNDERDETERMINED_INTERNAL','state_primary':primary,'state_composition':comp,'state_measurements':dict(zip(measurement_names,measurements)),'tail_primary':None,'tail_disease_test_run':False,'sex_mapping':sexmap,'age_center':agecenter}
    # Pathology-blind support/coherence/QC must be decision-capable before any tail disease statistic.
    if not tail_preflight['support']['support_ok'] or not tail_preflight['coherence_ok']:
        return {'state_terminal':state_terminal,'tail_terminal':'RARE_TAIL_UNDERDETERMINED_INTERNAL','state_primary':primary,'tail_primary':None,'tail_disease_test_run':False,'tail_preflight':tail_preflight}
    if not tail_preflight['qc_ok']:
        return {'state_terminal':state_terminal,'tail_terminal':'RARE_TAIL_UNDERDETERMINED_MEASUREMENT','state_primary':primary,'tail_primary':None,'tail_disease_test_run':False,'tail_preflight':tail_preflight}
    # Tail prevalence is estimand-specific. Use only the frozen >=80-cell subset of the
    # 18 parent confirmation donors; with current MTG support this must be 17 or 18.
    tail_donors=tail_preflight.get('tail_measurable_donors')
    if tail_donors is None:
        tail_donors=[d for d,v in zip(donors,pd.to_numeric(dt.TAIL_PREVALENCE,errors='coerce')) if np.isfinite(v)]
    tail_donors=sorted(map(str,tail_donors),key=lambda x:x.encode('utf-8'))
    if not set(tail_donors).issubset(set(donors)) or len(tail_donors) not in {17,18}:
        return {'state_terminal':state_terminal,'tail_terminal':'RARE_TAIL_UNDERDETERMINED_INTERNAL','state_primary':primary,'tail_primary':None,'tail_disease_test_run':False,'tail_preflight':tail_preflight,'tail_inference_donors':tail_donors}
    dtt=dt.set_index('donor_id').loc[tail_donors].reset_index(); mdt=md.set_index('donor_id').loc[tail_donors].reset_index()
    tail=pd.to_numeric(dtt.TAIL_PREVALENCE,errors='raise').to_numpy(float)
    if not np.isfinite(tail).all() or np.any((tail<0)|(tail>1)): raise ValueError('invalid measurable tail prevalence')
    y2=pd.to_numeric(mdt.AT8,errors='raise').to_numpy(float); age2=pd.to_numeric(mdt.age,errors='raise').to_numpy(float); immune2=pd.to_numeric(mdt.IMMUNE_FRACTION,errors='raise').to_numpy(float)
    try:
        z2,tail_sexmap,tail_agecenter=_nuisance(age2,mdt.sex.tolist())
    except ValueError:
        return {'state_terminal':state_terminal,'tail_terminal':'RARE_TAIL_UNDERDETERMINED_INTERNAL','state_primary':primary,'tail_primary':None,'tail_disease_test_run':False,'tail_preflight':tail_preflight,'tail_inference_donors':tail_donors}
    state2=dtt.STATE_SCORE.to_numpy(float); qdepth2=dtt.Q_DEPTH.to_numpy(float); qdetect2=dtt.Q_DETECT.to_numpy(float)
    tail_primary=safe_tail_hc3_t(y2,np.c_[z2,state2],tail); td=_candidate(tail_primary,TAIL_POS_ALPHA)
    if td is None:
        return {'state_terminal':state_terminal,'tail_terminal':'RARE_TAIL_UNDERDETERMINED_INTERNAL','state_primary':primary,'tail_primary':tail_primary,'tail_disease_test_run':True,'tail_preflight':tail_preflight,'tail_inference_donors':tail_donors,'tail_inference_n':len(tail_donors),'tail_sex_mapping':tail_sexmap,'tail_age_center':tail_agecenter}
    tail_comp=safe_tail_hc3_t(y2,np.c_[z2,state2,immune2],tail); tail_meas=[safe_tail_hc3_t(y2,np.c_[z2,state2,qdepth2,qdetect2],tail)]; tail_names=['Q_DEPTH+Q_DETECT']
    for name,cols in extra_technical_blocks.items():
        A=mdt[cols].apply(pd.to_numeric,errors='raise').to_numpy(float); tail_meas.append(safe_tail_hc3_t(y2,np.c_[z2,state2,qdepth2,qdetect2,A],tail)); tail_names.append(name)
    tail_terminal=decide_tail(state_terminal,tail_primary,tail_comp,tail_meas,True,True,True)
    return {'state_terminal':state_terminal,'tail_terminal':tail_terminal,'state_primary':primary,'state_composition':comp,'state_measurements':dict(zip(measurement_names,measurements)),'tail_primary':tail_primary,'tail_composition':tail_comp,'tail_measurements':dict(zip(tail_names,tail_meas)),'tail_disease_test_run':True,'tail_preflight':tail_preflight,'sex_mapping':sexmap,'age_center':agecenter,'tail_inference_donors':tail_donors,'tail_inference_n':len(tail_donors),'tail_sex_mapping':tail_sexmap,'tail_age_center':tail_agecenter}


def adjudicate_from_raw(*,target_dir,tail_dir,role_dir,discovery_authority_dir,technical_registry_dir,family_registry_dir,discovery_scalar_raw_counts,scalar_feature_ids,discovery_matrix_id,discovery_local_row,discovery_cell_id,discovery_donor_id,discovery_stable_key,discovery_source_library,discovery_metadata,confirmation_scalar_raw_counts,confirmation_matrix_id,confirmation_local_row,confirmation_cell_id,confirmation_donor_id,confirmation_stable_key,confirmation_source_library,confirmation_metadata,feature_split_csv,membership_csv):
    """Canonical conclusion-bearing T0 adjudication from one full scalar matrix per role."""
    role=load_role_authority(role_dir)
    link=load_discovery_authority(discovery_authority_dir,target_dir,role_dir,feature_split_csv)
    tech=load_technical_registry(technical_registry_dir)
    family=load_primary_only_family(family_registry_dir)
    feature=load_feature_authority(feature_split_csv)
    expected_scalar=feature.molecular_address_id.astype(str).tolist()
    if list(map(str,scalar_feature_ids))!=expected_scalar: raise ValueError('scalar feature authority mismatch')
    if getattr(discovery_scalar_raw_counts,'shape',None)!=(len(discovery_donor_id),len(expected_scalar)) or getattr(confirmation_scalar_raw_counts,'shape',None)!=(len(confirmation_donor_id),len(expected_scalar)): raise ValueError('canonical scalar matrix shape mismatch')
    membership=load_membership(membership_csv)
    validate_cells_against_membership(membership,matrix_id=discovery_matrix_id,local_row=discovery_local_row,cell_id=discovery_cell_id,donor_id=discovery_donor_id,stable_key=discovery_stable_key)
    validate_complete_role_cell_set(membership,expected_donors=role['discovery_donors'],donor_id=discovery_donor_id,stable_key=discovery_stable_key)
    validate_cells_against_membership(membership,matrix_id=confirmation_matrix_id,local_row=confirmation_local_row,cell_id=confirmation_cell_id,donor_id=confirmation_donor_id,stable_key=confirmation_stable_key)
    validate_complete_role_cell_set(membership,expected_donors=role['confirmation_donors'],donor_id=confirmation_donor_id,stable_key=confirmation_stable_key)
    score_idx=np.flatnonzero(feature.feature_role.to_numpy()=='SCORING')
    def sel(X,idx): return X[:,idx] if sp is not None and sp.issparse(X) else np.asarray(X)[:,idx]
    dkw=dict(raw_counts=sel(discovery_scalar_raw_counts,score_idx),feature_ids=feature.loc[score_idx,'molecular_address_id'].astype(str).tolist(),matrix_id=discovery_matrix_id,local_row=discovery_local_row,cell_id=discovery_cell_id,donor_id=discovery_donor_id,stable_key=discovery_stable_key,source_library=discovery_source_library,donor_metadata=discovery_metadata,feature_split_csv=feature_split_csv,membership_csv=membership_csv)
    verify_target_v2_against_raw(target_dir,**dkw)
    from t0_target_serializer_v2 import load_target_v2
    loaded_target=load_target_v2(target_dir,feature_split_csv)
    verify_tail_authority_against_loaded_target(tail_dir,loaded_target,raw_counts=dkw['raw_counts'],donor_id=discovery_donor_id,stable_key=discovery_stable_key,source_library=discovery_source_library)
    cs=confirmation_summaries_from_raw(target_dir=target_dir,tail_dir=tail_dir,scalar_raw_counts=confirmation_scalar_raw_counts,scalar_feature_ids=scalar_feature_ids,matrix_id=confirmation_matrix_id,local_row=confirmation_local_row,cell_id=confirmation_cell_id,donor_id=confirmation_donor_id,stable_key=confirmation_stable_key,source_library=confirmation_source_library,feature_split_csv=feature_split_csv,membership_csv=membership_csv,expected_confirmation_donors=role['confirmation_donors'],require_complete_membership=True)
    hold=np.flatnonzero(feature.feature_role.to_numpy()=='COHERENCE_HOLDOUT')
    pre=raw_tail_preflight(discovery_holdout_raw_counts=sel(discovery_scalar_raw_counts,hold),discovery_donor_id=discovery_donor_id,discovery_stable_key=discovery_stable_key,discovery_source_library=discovery_source_library,confirmation_holdout_raw_counts=sel(confirmation_scalar_raw_counts,hold),confirmation_donor_id=confirmation_donor_id,confirmation_stable_key=confirmation_stable_key,confirmation_source_library=confirmation_source_library,confirmation_summaries=cs)
    out=adjudicate_donor_table_non_authoritative(cs['donor_table'],confirmation_metadata,pre,tech['blocks'])
    out['target_package_root_sha256']=cs['target_package_root_sha256']; out['tail_package_root_sha256']=cs['tail_package_root_sha256']; out['canonical_confirmation_donors']=cs['canonical_confirmation_donors']; out['donor_role_package_root_sha256']=role['package_root_sha256']; out['discovery_authority_package_root_sha256']=link['package_root_sha256']; out['technical_registry_package_root_sha256']=tech['package_root_sha256']; out['target_family_package_root_sha256']=family['package_root_sha256']
    return out
