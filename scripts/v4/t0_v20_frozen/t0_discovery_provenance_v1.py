from __future__ import annotations
import hashlib, json, struct
from pathlib import Path
from typing import Sequence
import numpy as np
import pandas as pd
try:
    import scipy.sparse as sp
except Exception:  # pragma: no cover
    sp=None

from t0_feature_authority_v1 import load_feature_authority, ordered_addresses, validate_declared_order, EXPECTED_SPLIT_SHA256
from t0_primary_membership_v1 import load_membership, validate_cells_against_membership, EXPECTED_CSV_SHA256
from t0_stable_cell_key_v1 import parse_stable_key_exact

SCHEMA='JEPA_T0_DISCOVERY_INPUT_PROVENANCE_V2'


def _put_bytes(h, b: bytes) -> None:
    h.update(struct.pack('>Q',len(b))); h.update(b)


def _put_str(h, s: str) -> None:
    _put_bytes(h,s.encode('utf-8'))


def _row_nonzero_int64(counts, i: int, g: int) -> tuple[np.ndarray,np.ndarray]:
    """Canonical lossless sparse row: sorted uint32-capable indices + int64 counts."""
    if sp is not None and sp.issparse(counts):
        row=counts.getrow(i).copy(); row.sum_duplicates(); row.sort_indices()
        idx=np.asarray(row.indices,dtype=np.int64); data=np.asarray(row.data)
        if np.any(idx<0) or np.any(idx>=g): raise ValueError('sparse index outside feature range')
        if not np.isfinite(data).all() or np.any(data<0) or np.any(np.floor(data)!=data): raise ValueError('raw counts must be finite nonnegative integers')
        vals=np.asarray(data,dtype=np.int64)
        nz=vals!=0
        return idx[nz],vals[nz]
    a=np.asarray(counts)
    if a.ndim!=2 or a.shape[1]!=g: raise ValueError('raw_counts must be 2-D with scoring features')
    row=np.asarray(a[i])
    if not np.isfinite(row).all() or np.any(row<0) or np.any(np.floor(row)!=row): raise ValueError('raw counts must be finite nonnegative integers')
    idx=np.flatnonzero(row).astype(np.int64); vals=np.asarray(row[idx],dtype=np.int64)
    return idx,vals


def canonical_discovery_input_provenance(
    *, raw_counts, feature_ids: Sequence[str], matrix_id, local_row, cell_id, donor_id, stable_key,
    source_library, donor_metadata: pd.DataFrame, feature_split_csv: str|Path, membership_csv: str|Path,
) -> dict:
    feature=load_feature_authority(feature_split_csv)
    validate_declared_order(feature,'SCORING',feature_ids)
    expected_ids=ordered_addresses(feature,'SCORING'); g=len(expected_ids)
    n=len(list(stable_key)) if not isinstance(stable_key,np.ndarray) else len(stable_key)
    # Materialize identity arrays exactly once.
    matrix_id=list(matrix_id); local_row=list(local_row); cell_id=list(cell_id); donor_id=list(donor_id); stable_key=list(stable_key)
    source_library=np.asarray(source_library,dtype=np.float64)
    if not all(len(x)==n for x in [matrix_id,local_row,cell_id,donor_id,stable_key]) or len(source_library)!=n:
        raise ValueError('cell input length mismatch')
    if n==0: raise ValueError('empty discovery cell set')
    if source_library.ndim!=1 or not np.isfinite(source_library).all() or np.any(source_library<=0): raise ValueError('invalid source_library')
    if getattr(raw_counts,'shape',None)!=(n,g): raise ValueError('raw_counts shape mismatch')

    membership=load_membership(membership_csv)
    validate_cells_against_membership(membership,matrix_id=matrix_id,local_row=local_row,cell_id=cell_id,donor_id=donor_id,stable_key=stable_key)
    keys=np.asarray([parse_stable_key_exact(x) for x in stable_key],dtype=np.int64)
    if len(np.unique(keys))!=n: raise ValueError('duplicate stable keys')

    req=['donor_id','AT8','age','sex']
    if list(donor_metadata.columns)!=req: raise ValueError(f'donor metadata schema must be exactly {req}')
    if donor_metadata['donor_id'].duplicated().any() or donor_metadata['donor_id'].isna().any(): raise ValueError('donor metadata IDs invalid')
    dm=donor_metadata.copy()
    dm['donor_id']=dm['donor_id'].astype(str)
    if (dm['donor_id']=='').any(): raise ValueError('empty donor metadata ID')
    for c in ['AT8','age']:
        dm[c]=pd.to_numeric(dm[c],errors='raise')
        if not np.isfinite(dm[c].to_numpy(float)).all(): raise ValueError(f'nonfinite {c}')
    if (dm['AT8']<0).any(): raise ValueError('AT8 must be nonnegative')
    if dm['sex'].isna().any() or (dm['sex'].astype(str)=='').any(): raise ValueError('invalid sex labels')
    observed=set(map(str,donor_id)); meta=set(dm['donor_id'])
    if observed!=meta: raise ValueError('donor metadata set must exactly equal discovery cell donor set')

    # Canonical row order is exact stable-key integer order, independent of file row order/storage.
    order=np.argsort(keys,kind='mergesort')
    cell_encoding='sparse_nonzero_index_u32be_count_i64be_v1'
    cell_h=hashlib.sha256(); _put_str(cell_h,SCHEMA); _put_str(cell_h,'CELLS'); _put_str(cell_h,cell_encoding)
    for i in order:
        idx,vals=_row_nonzero_int64(raw_counts,int(i),g)
        if int(vals.sum(dtype=np.int64))>source_library[i]+1e-9: raise ValueError('scoring counts exceed source_library')
        cell_h.update(struct.pack('>Q',int(keys[i])))
        _put_str(cell_h,str(donor_id[i]))
        cell_h.update(np.asarray([source_library[i]],dtype='<f8').tobytes())
        cell_h.update(struct.pack('>I',len(idx)))
        for j,v in zip(idx,vals):
            cell_h.update(struct.pack('>I',int(j))); cell_h.update(struct.pack('>q',int(v)))

    dm=dm.sort_values('donor_id',key=lambda s:s.map(lambda x:x.encode('utf-8'))).reset_index(drop=True)
    meta_h=hashlib.sha256(); _put_str(meta_h,SCHEMA); _put_str(meta_h,'DONORS')
    for r in dm.itertuples(index=False):
        _put_str(meta_h,str(r.donor_id))
        meta_h.update(np.asarray([float(r.AT8),float(r.age)],dtype='<f8').tobytes())
        _put_str(meta_h,str(r.sex))

    root_h=hashlib.sha256(); _put_str(root_h,SCHEMA)
    _put_str(root_h,EXPECTED_SPLIT_SHA256); _put_str(root_h,EXPECTED_CSV_SHA256)
    _put_str(root_h,cell_h.hexdigest()); _put_str(root_h,meta_h.hexdigest())
    _put_str(root_h,str(n)); _put_str(root_h,str(g))
    return {
        'schema':SCHEMA,
        'root_sha256':root_h.hexdigest(),
        'cell_payload_sha256':cell_h.hexdigest(),
        'donor_metadata_sha256':meta_h.hexdigest(),
        'feature_authority_sha256':EXPECTED_SPLIT_SHA256,
        'membership_authority_sha256':EXPECTED_CSV_SHA256,
        'cells':n,'scoring_features':g,'cell_encoding':cell_encoding,
        'canonical_discovery_donors':dm['donor_id'].tolist(),
    }
