from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
try:
    import scipy.sparse as sp
except Exception:
    sp=None

from t0_feature_authority_v1 import load_feature_authority, validate_declared_order
from t0_primary_membership_v1 import load_membership, validate_cells_against_membership
from t0_stable_cell_key_v1 import parse_stable_key_exact
from t0_metadata_coding_v1 import encode_binary_utf8
from t0_target_learner_v1 import fit_t0_target
from t0_discovery_provenance_v1 import canonical_discovery_input_provenance
from t0_target_serializer_v2 import serialize_target_v2, load_target_v2

CHUNK_FEATURES=1024


def _normalized_pseudobulk(raw_counts, source_library, donors, stable_keys) -> tuple[np.ndarray,list[str]]:
    n,g=raw_counts.shape
    lib=np.asarray(source_library,dtype=np.float64)
    if lib.shape!=(n,) or not np.isfinite(lib).all() or np.any(lib<=0): raise ValueError('invalid source_library')
    d=np.asarray([str(x) for x in donors]); keys=np.asarray([parse_stable_key_exact(x) for x in stable_keys],dtype=np.int64)
    if len(d)!=n or len(keys)!=n or len(np.unique(keys))!=n or any(not x for x in d): raise ValueError('invalid donor/stable-key arrays')
    row_order=np.argsort(keys,kind='mergesort'); dord=d[row_order]; lord=lib[row_order]
    donor_order=sorted(set(d),key=lambda x:x.encode('utf-8'))
    if sp is None:
        # Dense fallback uses the same stable-key row order.
        A=np.asarray(raw_counts)[row_order]
        if not np.isfinite(A).all() or np.any(A<0) or np.any(np.floor(A)!=A): raise ValueError('raw counts must be finite nonnegative integers')
        if np.any(A.sum(axis=1)>lord+1e-9): raise ValueError('raw counts exceed source_library')
        N=np.log1p(10000.0*A/lord[:,None]); out=np.vstack([N[dord==u].mean(axis=0,dtype=np.float64) for u in donor_order]); return np.asarray(out,dtype=np.float64),donor_order
    if sp.issparse(raw_counts):
        C=raw_counts.tocsr(copy=True)[row_order]
    else:
        A=np.asarray(raw_counts)
        if A.ndim!=2 or A.shape!=(n,g): raise ValueError('raw_counts shape mismatch')
        if not np.isfinite(A).all() or np.any(A<0) or np.any(np.floor(A)!=A): raise ValueError('raw counts must be finite nonnegative integers')
        C=sp.csr_matrix(A[row_order])
    C.sum_duplicates(); C.sort_indices()
    if not np.isfinite(C.data).all() or np.any(C.data<0) or np.any(np.floor(C.data)!=C.data): raise ValueError('raw counts must be finite nonnegative integers')
    rowsum=np.asarray(C.sum(axis=1)).ravel()
    if np.any(rowsum>lord+1e-9): raise ValueError('raw counts exceed source_library')
    N=C.astype(np.float64,copy=True); reps=np.diff(N.indptr)
    N.data=np.log1p(10000.0*N.data*np.repeat(1.0/lord,reps))
    donor_index={u:i for i,u in enumerate(donor_order)}; ridx=np.asarray([donor_index[u] for u in dord],dtype=np.int64)
    counts=np.bincount(ridx,minlength=len(donor_order)).astype(np.float64)
    G=sp.csr_matrix((1.0/counts[ridx],(ridx,np.arange(n,dtype=np.int64))),shape=(len(donor_order),n))
    out=(G@N).toarray()
    return np.asarray(out,dtype=np.float64),donor_order


def fit_discovery_target_v2(*,raw_counts,feature_ids,matrix_id,local_row,cell_id,donor_id,stable_key,source_library,donor_metadata,feature_split_csv,membership_csv):
    """Low-level numerical primitive; canonical use must pass through t0_canonical_freeze_v1."""
    feature=load_feature_authority(feature_split_csv); validate_declared_order(feature,'SCORING',feature_ids)
    membership=load_membership(membership_csv)
    validate_cells_against_membership(membership,matrix_id=matrix_id,local_row=local_row,cell_id=cell_id,donor_id=donor_id,stable_key=stable_key)
    pb,donors=_normalized_pseudobulk(raw_counts,source_library,donor_id,stable_key)
    req=['donor_id','AT8','age','sex']
    if list(donor_metadata.columns)!=req: raise ValueError(f'donor metadata schema must be exactly {req}')
    dm=donor_metadata.copy(); dm['donor_id']=dm.donor_id.astype(str)
    if dm.donor_id.duplicated().any() or set(dm.donor_id)!=set(donors): raise ValueError('donor metadata set mismatch')
    dm=dm.set_index('donor_id').loc[donors].reset_index()
    y=pd.to_numeric(dm.AT8,errors='raise').to_numpy(float); age=pd.to_numeric(dm.age,errors='raise').to_numpy(float)
    if not np.isfinite(y).all() or np.any(y<0) or not np.isfinite(age).all(): raise ValueError('invalid AT8/age')
    sex,mapping=encode_binary_utf8(dm.sex.tolist())
    fit=fit_t0_target(pb,y,age,sex,donors)
    provenance=canonical_discovery_input_provenance(raw_counts=raw_counts,feature_ids=feature_ids,matrix_id=matrix_id,local_row=local_row,cell_id=cell_id,donor_id=donor_id,stable_key=stable_key,source_library=source_library,donor_metadata=donor_metadata,feature_split_csv=feature_split_csv,membership_csv=membership_csv)
    provenance=provenance.copy(); provenance['sex_utf8_mapping']=mapping; provenance['normalization']='log1p(10000*raw_count/source_library)_exactly_once'; provenance['pseudobulk']='equal_cell_mean_by_donor'; provenance['aggregation_feature_chunk']=CHUNK_FEATURES
    return {'fit':fit,'provenance':provenance,'pseudobulk':pb,'donor_order':donors}


def fit_and_serialize_target_v2(outdir,**kwargs):
    r=fit_discovery_target_v2(**kwargs)
    serial=serialize_target_v2(outdir,r['fit'],r['provenance'],kwargs['feature_split_csv'])
    return {**serial,'fit':r['fit'],'provenance':r['provenance']}


def verify_target_v2_against_raw(target_dir,**kwargs) -> dict:
    frozen=load_target_v2(target_dir,kwargs['feature_split_csv'])
    recomputed=fit_discovery_target_v2(**kwargs)
    if frozen['provenance']!=recomputed['provenance']: raise ValueError('frozen provenance does not match canonical raw discovery inputs')
    a=frozen['fit']; b=recomputed['fit']
    for k in ['beta','mu','sigma','decision_gene_mask','cv_mse_by_multiplier','multiplier_exponents','canonical_donor_order']:
        if not np.array_equal(np.asarray(a[k]),np.asarray(b[k])): raise ValueError(f'frozen target {k} mismatch canonical recomputation')
    for k in ['selected_multiplier_index','selected_multiplier_exponent','final_lambda','final_trace_scale','response_residual_sd','discovery_age_center']:
        if a[k]!=b[k]: raise ValueError(f'frozen target scalar {k} mismatch canonical recomputation')
    return {'verified':True,'package_root_sha256':frozen['package_root_sha256'],'discovery_provenance_root':frozen['provenance']['root_sha256']}
