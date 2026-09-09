from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
try:
    import scipy.sparse as sp
except Exception:
    sp=None
from t0_feature_authority_v1 import load_feature_authority
from t0_primary_membership_v1 import load_membership,validate_cells_against_membership,validate_complete_role_cell_set
from t0_stable_cell_key_v1 import parse_stable_key_exact
from t0_target_serializer_v2 import load_target_v2
from t0_tail_authority_v1 import load_tail_authority,score_raw_counts,TAIL_MIN_CELLS

SCALAR_FEATURES=35076
CONFIRMATION_DONORS=18


def _validate_scalar_ids(feature,ids):
    expected=feature.molecular_address_id.astype(str).tolist(); got=[str(x) for x in ids]
    if got!=expected: raise ValueError('scalar-address column order mismatch')


def _select_cols(X,idx):
    if sp is not None and sp.issparse(X): return X[:,idx]
    return np.asarray(X)[:,idx]


def confirmation_summaries_from_raw(*,target_dir,tail_dir,scalar_raw_counts,scalar_feature_ids,matrix_id,local_row,cell_id,donor_id,stable_key,source_library,feature_split_csv,membership_csv,expected_confirmation_donors=None,require_complete_membership=False):
    feature=load_feature_authority(feature_split_csv); _validate_scalar_ids(feature,scalar_feature_ids)
    n=len(donor_id); X=scalar_raw_counts
    if getattr(X,'shape',None)!=(n,SCALAR_FEATURES): raise ValueError('scalar raw-count shape mismatch')
    membership=load_membership(membership_csv)
    validate_cells_against_membership(membership,matrix_id=matrix_id,local_row=local_row,cell_id=cell_id,donor_id=donor_id,stable_key=stable_key)
    d=np.asarray([str(x) for x in donor_id]); keys=np.asarray([parse_stable_key_exact(x) for x in stable_key],dtype=np.int64); lib=np.asarray(source_library,dtype=np.float64)
    if lib.shape!=(n,) or not np.isfinite(lib).all() or np.any(lib<=0): raise ValueError('invalid source_library')
    donors=sorted(set(d),key=lambda x:x.encode('utf-8'))
    if len(donors)!=CONFIRMATION_DONORS: raise ValueError('exactly 18 confirmation donors required')
    if expected_confirmation_donors is not None:
        expected=sorted(map(str,expected_confirmation_donors),key=lambda x:x.encode('utf-8'))
        if donors!=expected: raise ValueError('confirmation donor authority mismatch')
        if require_complete_membership:
            validate_complete_role_cell_set(membership,expected_donors=expected,donor_id=donor_id,stable_key=stable_key)
    if len(np.unique(keys))!=n: raise ValueError('duplicate stable keys')
    counts_by={u:int(np.sum(d==u)) for u in donors}
    tail_measurable_donors=[u for u in donors if counts_by[u]>=TAIL_MIN_CELLS]
    target=load_target_v2(target_dir,feature_split_csv); tail=load_tail_authority(tail_dir,target['package_root_sha256'])
    if set(donors)&set(map(str,target['fit']['canonical_donor_order'])): raise ValueError('confirmation donors overlap target discovery donors')
    scoring_pos=np.flatnonzero(feature.feature_role.to_numpy()=='SCORING')
    scoring=_select_cols(X,scoring_pos)
    cell_scores=score_raw_counts(scoring,lib,target['fit'])
    # Q_DETECT is defined on all 35,076 scalar-measured addresses.
    if sp is not None and sp.issparse(X):
        detect=np.asarray((X!=0).sum(axis=1)).ravel()/SCALAR_FEATURES
    else:
        A=np.asarray(X)
        if not np.isfinite(A).all() or np.any(A<0) or np.any(np.floor(A)!=A): raise ValueError('invalid scalar raw counts')
        detect=np.count_nonzero(A,axis=1)/SCALAR_FEATURES
    qdepth=np.log1p(lib)
    rows=[]; tail_masks_by={}; qc_by={}; keys_by={}; indices_by={}
    for u in donors:
        ix=np.flatnonzero(d==u); ix=ix[np.argsort(keys[ix],kind='mergesort')]
        s=cell_scores[ix]; centered=s-float(np.sum(s,dtype=np.float64)/len(s)); measurable=(u in tail_measurable_donors)
        tm=(centered>tail['threshold']) if measurable else None
        rows.append({'donor_id':u,'cells':len(ix),'STATE_SCORE':float(np.sum(s,dtype=np.float64)/len(s)),'TAIL_MEASURABLE':bool(measurable),'TAIL_PREVALENCE':float(np.mean(tm)) if measurable else np.nan,'Q_DEPTH':float(np.mean(qdepth[ix])),'Q_DETECT':float(np.mean(detect[ix])),'tail_cells':int(tm.sum()) if measurable else pd.NA,'rest_cells':int((~tm).sum()) if measurable else pd.NA})
        if measurable: tail_masks_by[u]=tm.copy()
        qc_by[u]=np.c_[qdepth[ix],detect[ix]]; keys_by[u]=keys[ix].copy(); indices_by[u]=ix.copy()
    table=pd.DataFrame(rows)
    return {'donor_table':table,'tail_masks_by_donor':tail_masks_by,'qc_by_donor':qc_by,'stable_keys_by_donor':keys_by,'cell_indices_by_donor':indices_by,'target_package_root_sha256':target['package_root_sha256'],'tail_package_root_sha256':tail['package_root_sha256'],'threshold':tail['threshold'],'cell_scores':cell_scores,'canonical_confirmation_donors':donors,'tail_measurable_donors':tail_measurable_donors}
