from __future__ import annotations
import hashlib
import pandas as pd

NAMESPACE='T0-DISCOVERY-CONFIRM-V1'
TAIL_MIN_CELLS=80
N_CONFIRM=18

def _digest(donor_id: str, namespace: str=NAMESPACE) -> str:
    return hashlib.sha256(f'{namespace}|{donor_id}'.encode('utf-8')).hexdigest()

def generate(support: pd.DataFrame) -> pd.DataFrame:
    req={'source','donor_id','operator_index','cells'}
    miss=req-set(support.columns)
    if miss: raise ValueError(f'missing columns: {sorted(miss)}')
    x=support[(support.source=='SEA_AD') & (support.operator_index==31)].copy()
    if x.empty: raise ValueError('no SEA_AD op31 rows')
    if x.donor_id.duplicated().any(): raise ValueError('duplicate donor rows')
    x=x[['donor_id','cells']].copy()
    x['cells']=x['cells'].astype(int)
    if (x.cells<0).any(): raise ValueError('negative cell count')
    x['split_hash']=x.donor_id.map(_digest)
    x['tail_measurable']=x.cells.ge(TAIL_MIN_CELLS)
    eligible=x[x.tail_measurable].sort_values(['split_hash','donor_id'])
    if len(eligible)<N_CONFIRM: raise ValueError('too few tail-measurable donors for confirmation')
    confirm=set(eligible.head(N_CONFIRM).donor_id)
    x['role']=x.donor_id.map(lambda d:'CONFIRMATION' if d in confirm else 'DISCOVERY')
    x['namespace']=NAMESPACE
    return x[['donor_id','cells','split_hash','role','tail_measurable','namespace']].sort_values(
        ['role','split_hash','donor_id']
    ).reset_index(drop=True)

if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser()
    ap.add_argument('support_csv')
    ap.add_argument('output_csv')
    a=ap.parse_args()
    df=pd.read_csv(a.support_csv)
    generate(df).to_csv(a.output_csv,index=False)
