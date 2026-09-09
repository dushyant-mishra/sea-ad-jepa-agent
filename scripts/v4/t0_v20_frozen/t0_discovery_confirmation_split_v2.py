from __future__ import annotations
import hashlib
import numpy as np
import pandas as pd

NAMESPACE='T0-DISCOVERY-CONFIRM-V2'
TAIL_MIN_CELLS=80
N_CONFIRM=18
MIN_DISCOVERY=18


def _digest(donor_id: str, namespace: str=NAMESPACE) -> str:
    if not isinstance(donor_id,str) or not donor_id:
        raise ValueError('donor_id must be nonempty string')
    return hashlib.sha256(f'{namespace}|{donor_id}'.encode('utf-8')).hexdigest()


def _exact_cells(values) -> np.ndarray:
    x=pd.to_numeric(values,errors='raise').to_numpy(np.float64)
    if not np.isfinite(x).all() or np.any(x<0) or np.any(np.floor(x)!=x):
        raise ValueError('cells must be finite nonnegative integers')
    return x.astype(np.int64)


def generate(support: pd.DataFrame) -> pd.DataFrame:
    req={'source','donor_id','operator_index','cells'}
    miss=req-set(support.columns)
    if miss: raise ValueError(f'missing columns: {sorted(miss)}')
    x=support[(support.source=='SEA_AD') & (support.operator_index==31)][['donor_id','cells']].copy()
    if x.empty: raise ValueError('no SEA_AD op31 rows')
    x['donor_id']=x.donor_id.astype(str)
    if x.donor_id.duplicated().any() or x.donor_id.eq('').any(): raise ValueError('invalid donor rows')
    x['cells']=_exact_cells(x.cells)
    if len(x)<N_CONFIRM+MIN_DISCOVERY: raise ValueError('too few donors for frozen 18 confirmation + >=18 discovery design')
    x['split_hash']=x.donor_id.map(_digest)
    x['tail_measurable']=x.cells.ge(TAIL_MIN_CELLS)
    # Primary state confirmation is selected from all eligible donors. Tail measurability
    # is a downstream property and must not influence the parent-state donor roles.
    ordered=x.sort_values(['split_hash','donor_id'])
    confirm=set(ordered.head(N_CONFIRM).donor_id)
    x['role']=x.donor_id.map(lambda d:'CONFIRMATION' if d in confirm else 'DISCOVERY')
    x['namespace']=NAMESPACE
    return x[['donor_id','cells','split_hash','role','tail_measurable','namespace']].sort_values(['role','split_hash','donor_id']).reset_index(drop=True)
