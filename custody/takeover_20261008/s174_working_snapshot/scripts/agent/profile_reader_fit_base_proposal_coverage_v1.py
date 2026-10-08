#!/usr/bin/env python3
"""Compare outcome-blind base-cell proposal families for the frozen donor target.

All metrics are descriptive reader_fit geometry. No proposal is selected.
"""
from __future__ import annotations
import argparse, hashlib, json, sqlite3
from pathlib import Path
import numpy as np
import pandas as pd

METADATA_SHA256='a771f08be31a840b5472448c438a153fbca7de93ba2ed31fe692eaeda02e6913'
BUNDLE_MEMBER='metadata/foundation_metadata_rows.sqlite'
GRID=(0.0,0.25,0.5,0.75,0.9,0.95,0.99,1.0)


def sha256(path:Path)->str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(8<<20),b''): h.update(chunk)
    return h.hexdigest()


def weighted_quantile(values, weights, qs):
    v=np.asarray(values,float); w=np.asarray(weights,float)
    order=np.argsort(v,kind='stable'); v=v[order]; w=w[order]
    c=np.cumsum(w)/w.sum()
    return {str(q):float(v[min(np.searchsorted(c,q,side='left'),len(v)-1)]) for q in qs}


def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument('--metadata-sqlite',type=Path,required=True); ap.add_argument('--out',type=Path,required=True); a=ap.parse_args()
    observed=sha256(a.metadata_sqlite)
    if observed!=METADATA_SHA256: raise SystemExit(f'metadata SHA mismatch {observed} != {METADATA_SHA256}')
    con=sqlite3.connect(a.metadata_sqlite)
    try:
        g=pd.read_sql_query("select source,donor_id,operator_index,count(*) cells from cells where partition='reader_fit' group by source,donor_id,operator_index",con)
    finally: con.close()
    N=int(g.cells.sum()); D=int(g.donor_id.nunique()); S=int(g.source.nunique())
    g['donor_cells']=g.groupby('donor_id').cells.transform('sum')
    g['groups_per_donor']=g.groupby('donor_id').operator_index.transform('count')
    source_cells=g.groupby('source').cells.sum().to_dict()
    counts=g.cells.to_numpy(float)
    p=1.0/(D*g.donor_cells.to_numpy(float))
    q_source=np.array([1.0/(S*source_cells[s]) for s in g.source],float)
    q_group=1.0/(D*g.groups_per_donor.to_numpy(float)*counts)

    def metrics(q):
        mass=float(np.sum(counts*q))
        if not np.isclose(mass,1.0,rtol=1e-13,atol=1e-13): raise RuntimeError(f'proposal mass {mass}')
        w=p/q
        second=float(np.sum(counts*(p*p/q)))
        ess=1.0/second
        per_cell=N*q
        group_presentations=N*counts*q
        return {
            'probability_mass':mass,
            'importance_ess_fraction':ess,
            'importance_weight_min':float(w.min()),
            'importance_weight_max':float(w.max()),
            'importance_weight_max_to_min_ratio':float(w.max()/w.min()),
            'expected_per_cell_exposure_at_H_equals_reader_fit_cells':{
                'max':float(per_cell.max()),
                'cell_weighted_quantiles':weighted_quantile(per_cell,counts,(.01,.05,.1,.25,.5,.75,.9,.95,.99)),
            },
            'expected_group_presentations_at_H_equals_reader_fit_cells':{
                'min':float(group_presentations.min()),
                'median':float(np.median(group_presentations)),
                'max':float(group_presentations.max()),
                'cv_across_groups':float(np.std(group_presentations)/np.mean(group_presentations)),
            },
        }

    families={
        'TARGET_DONOR_UNIFORM_CELL_WITHIN_DONOR':metrics(p),
        'SOURCE_UNIFORM_CELL_WITHIN_SOURCE':metrics(q_source),
        'DONOR_UNIFORM_OPERATOR_GROUP_UNIFORM_CELL_WITHIN_GROUP__PROPOSAL_ONLY':metrics(q_group),
        'DONOR_TARGET_PLUS_SOURCE_MIXTURE':[],
        'DONOR_TARGET_PLUS_OPERATOR_COVERAGE_MIXTURE__PROPOSAL_ONLY':[],
    }
    for alpha in GRID:
        families['DONOR_TARGET_PLUS_SOURCE_MIXTURE'].append({'alpha_target':alpha,**metrics(alpha*p+(1-alpha)*q_source)})
        families['DONOR_TARGET_PLUS_OPERATOR_COVERAGE_MIXTURE__PROPOSAL_ONLY'].append({'alpha_target':alpha,**metrics(alpha*p+(1-alpha)*q_group)})
    payload={
        'schema':'READER_FIT_BASE_PROPOSAL_COVERAGE_PROFILE_V1',
        'population':'reader_fit','cells':N,'donors':D,'operators':int(g.operator_index.nunique()),
        'authority_input':{'bundle_member':BUNDLE_MEMBER,'sha256':observed},
        'scientific_target_policy_id':'DONOR_UNIFORM__CELL_UNIFORM_WITHIN_DONOR_V1',
        'operator_role_in_operator_coverage_family':'PROPOSAL_COVERAGE_STRATUM_ONLY__EXACT_P_OVER_Q_REQUIRED__NOT_SCIENTIFIC_TARGET_MASS',
        'descriptive_grid_alpha_target':list(GRID),
        'proposal_families':families,
        'selection':{
            'selected_policy_id':None,'selected_alpha':None,
            'required_future_constraints':['total presentations','maximum expected repeated exposure per cell','required proposal/importance-weight conditioning','required donor-by-operator coverage'],
            'rule':'Do not select q from this profile alone. Freeze constraints prospectively, then derive q without outcome access.'
        },
        'training_authorized':False,'execution_authorized':False,
    }
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(payload,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps({'out':str(a.out),'sha256':sha256(a.out),'terminal':'PASS_READER_FIT_BASE_PROPOSAL_COVERAGE_PROFILE_V1'},sort_keys=True))
    return 0
if __name__=='__main__': raise SystemExit(main())
