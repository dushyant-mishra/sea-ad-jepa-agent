from __future__ import annotations
import hashlib
from pathlib import Path
import pandas as pd
from t0_mtg_feature_split_v2 import generate, NAMESPACE

EXPECTED_SPLIT_SHA256='29116c16e9002329090a5054b6c4bdae1cbff28917cbee85f03b4633b0b29369'
EXPECTED_UNIVERSE_SHA256='3f131b1432d538334953e4c3d4643562161a86a93837565b0a39acd1c9ee08e1'
EXPECTED_ROWS=35076
EXPECTED_SCORING=28061
EXPECTED_HOLDOUT=7015
COLUMNS=['molecular_address_index','molecular_address_id','symbol','biotype','feature_role','split_namespace','split_hash']


def sha256_file(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(8<<20),b''): h.update(b)
    return h.hexdigest()


def load_feature_authority(split_csv: str|Path) -> pd.DataFrame:
    p=Path(split_csv)
    if sha256_file(p)!=EXPECTED_SPLIT_SHA256: raise ValueError('feature-role split hash mismatch')
    x=pd.read_csv(p)
    if list(x.columns)!=COLUMNS: raise ValueError('feature-role schema mismatch')
    if len(x)!=EXPECTED_ROWS: raise ValueError('feature-role row count mismatch')
    if x.molecular_address_index.duplicated().any() or x.molecular_address_id.duplicated().any(): raise ValueError('duplicate address authority')
    if not x.molecular_address_index.is_monotonic_increasing: raise ValueError('feature authority not in canonical address-index order')
    if not x.split_namespace.eq(NAMESPACE).all(): raise ValueError('split namespace mismatch')
    vc=x.feature_role.value_counts().to_dict()
    if vc!={'SCORING':EXPECTED_SCORING,'COHERENCE_HOLDOUT':EXPECTED_HOLDOUT}: raise ValueError(f'feature-role counts mismatch: {vc}')
    allowed={'SCORING','COHERENCE_HOLDOUT'}
    if set(x.feature_role)!=allowed: raise ValueError('unknown feature role')
    # Recheck every deterministic split hash and the actual holdout assignment.
    reg=generate(x[['molecular_address_index','molecular_address_id','symbol','biotype']])
    # Normalize NaN-equivalent CSV fields before exact semantic comparison.
    a=x.fillna(''); b=reg.fillna('')
    if not a.equals(b): raise ValueError('feature-role rows do not match deterministic generator')
    return x


def regenerate_feature_authority(universe_csv: str|Path, output_csv: str|Path) -> pd.DataFrame:
    u=Path(universe_csv); out=Path(output_csv)
    if sha256_file(u)!=EXPECTED_UNIVERSE_SHA256: raise ValueError('scalar-address universe hash mismatch')
    x=generate(pd.read_csv(u))
    out.parent.mkdir(parents=True,exist_ok=True)
    x.to_csv(out,index=False,lineterminator='\n')
    if sha256_file(out)!=EXPECTED_SPLIT_SHA256: raise AssertionError('regenerated split bytes mismatch')
    return x


def ordered_addresses(split: pd.DataFrame, role: str) -> list[str]:
    if role not in {'SCORING','COHERENCE_HOLDOUT'}: raise ValueError('invalid role')
    return split.loc[split.feature_role.eq(role),'molecular_address_id'].astype(str).tolist()


def validate_declared_order(split: pd.DataFrame, role: str, declared_ids) -> None:
    expected=ordered_addresses(split,role)
    got=[str(x) for x in declared_ids]
    if got!=expected: raise ValueError(f'{role} column order does not match frozen feature authority')
