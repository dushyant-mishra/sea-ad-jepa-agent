#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, sqlite3
from pathlib import Path
import numpy as np
import pandas as pd

METADATA_SHA256='a771f08be31a840b5472448c438a153fbca7de93ba2ed31fe692eaeda02e6913'
CALIBRATION_BUNDLE_SHA256='07748d5bd21fe0857ccad3002fba3946d1791d25898b841d41056a3707117444'
BUNDLE_MEMBER='metadata/foundation_metadata_rows.sqlite'


def sha256(path:Path)->str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(8<<20),b''): h.update(chunk)
    return h.hexdigest()


def qdict(values)->dict[str,int]:
    a=np.asarray(values,dtype=np.float64)
    return {str(q):int(np.quantile(a,q)) for q in (0,.01,.05,.10,.25,.50,.75,.90,.95,.99,1)}


def capacity(n:int)->int:
    return n*((n-1)*(n-2)//2) if n>=3 else 0


def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument('--metadata-sqlite',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    observed=sha256(a.metadata_sqlite)
    if observed != METADATA_SHA256:
        raise SystemExit(f'metadata authority mismatch: {observed}')
    con=sqlite3.connect(a.metadata_sqlite)
    try:
        g=pd.read_sql_query(
            "select source,donor_id,operator_index,count(*) cells from cells where partition='reader_fit' group by source,donor_id,operator_index order by source,donor_id,operator_index",
            con,
        )
    finally:
        con.close()
    g['anchored_triplet_capacity']=g.cells.map(capacity)
    eligible=g[g.cells>=3].copy()
    donor_eligible=eligible.groupby(['source','donor_id']).size().rename('eligible_groups').reset_index()
    by_source=[]
    for src,chunk in g.groupby('source',sort=True):
        e=chunk[chunk.cells>=3]
        de=donor_eligible[donor_eligible.source==src]
        by_source.append({
            'source':src,
            'groups':int(len(chunk)),
            'eligible_groups_ge_3':int(len(e)),
            'donors_with_eligible_group':int(e.donor_id.nunique()),
            'eligible_groups_per_donor_min':int(de.eligible_groups.min()),
            'eligible_groups_per_donor_median':float(de.eligible_groups.median()),
            'eligible_groups_per_donor_max':int(de.eligible_groups.max()),
            'anchored_triplet_capacity_sum':int(sum(int(x) for x in e.anchored_triplet_capacity)),
        })
    out={
        'schema':'READER_FIT_RELATIONAL_SUPPORT_PROFILE_V1',
        'population':'reader_fit',
        'calibration_bundle_sha256':CALIBRATION_BUNDLE_SHA256,
        'metadata_authority':{'bundle_member':BUNDLE_MEMBER,'sha256':observed},
        'donors':int(g.donor_id.nunique()),
        'groups':int(len(g)),
        'eligible_groups_ge_3':int(len(eligible)),
        'ineligible_groups_lt_3':int(len(g)-len(eligible)),
        'donors_with_at_least_one_eligible_group':int(eligible.donor_id.nunique()),
        'eligible_group_fraction':float(len(eligible)/len(g)),
        'eligible_group_cell_fraction':float(eligible.cells.sum()/g.cells.sum()),
        'eligible_group_size_quantiles':qdict(eligible.cells),
        'anchored_triplet_capacity_quantiles':qdict(eligible.anchored_triplet_capacity),
        'anchored_triplet_capacity_total':int(sum(int(x) for x in eligible.anchored_triplet_capacity)),
        'by_source':by_source,
        'implications':[
            'Every reader-fit donor has at least one donor-by-operator group with at least three cells, so a donor-primary relational estimand can remain defined without dropping donors.',
            'Full enumeration is prohibited by scale: the total eligible anchored-triplet space exceeds 6.9e14 relations and the largest single group exceeds 3.75e13.',
            'Relational scientific sampling, finite triplet draw count, and compute coalescing/packing must remain separate authorities.',
        ],
        'training_authorized':False,
        'execution_authorized':False,
    }
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps({'out':str(a.out),'sha256':sha256(a.out),'eligible_groups':len(eligible),'capacity_total':out['anchored_triplet_capacity_total']},sort_keys=True))
    return 0

if __name__=='__main__': raise SystemExit(main())
