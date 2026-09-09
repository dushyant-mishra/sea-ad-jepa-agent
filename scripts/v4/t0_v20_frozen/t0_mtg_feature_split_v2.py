from __future__ import annotations
import hashlib, math
import pandas as pd
NAMESPACE='T0-MTG-FEATURE-SPLIT-V2'
HOLDOUT_FRACTION=0.20

def _digest(address_id: str, namespace: str=NAMESPACE) -> str:
    return hashlib.sha256(f'{namespace}|{address_id}'.encode('utf-8')).hexdigest()

def generate(universe: pd.DataFrame) -> pd.DataFrame:
    req={'molecular_address_index','molecular_address_id','symbol','biotype'}
    miss=req-set(universe.columns)
    if miss: raise ValueError(f'missing columns: {sorted(miss)}')
    x=universe[list(req)].copy()
    x=x.sort_values('molecular_address_index').reset_index(drop=True)
    if x.molecular_address_index.duplicated().any() or x.molecular_address_id.duplicated().any():
        raise ValueError('duplicate address authority')
    if len(x)<5: raise ValueError('universe too small')
    x['split_hash']=x.molecular_address_id.map(_digest)
    n_hold=math.floor(len(x)*HOLDOUT_FRACTION)
    order=x.sort_values(['split_hash','molecular_address_id','molecular_address_index']).index
    hold=set(order[:n_hold])
    x['feature_role']=['COHERENCE_HOLDOUT' if i in hold else 'SCORING' for i in x.index]
    x['split_namespace']=NAMESPACE
    return x[['molecular_address_index','molecular_address_id','symbol','biotype','feature_role','split_namespace','split_hash']]

if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser(); ap.add_argument('universe_csv'); ap.add_argument('output_csv'); a=ap.parse_args()
    generate(pd.read_csv(a.universe_csv)).to_csv(a.output_csv,index=False)
