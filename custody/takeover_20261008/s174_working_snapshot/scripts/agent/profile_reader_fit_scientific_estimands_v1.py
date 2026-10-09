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
        donor=pd.read_sql_query(
            "select source,donor_id,count(*) cells from cells where partition='reader_fit' group by source,donor_id order by source,donor_id",
            con,
        )
    finally:
        con.close()
    n=int(donor.cells.sum()); d=int(len(donor)); s=int(donor.source.nunique())
    source_donors=donor.groupby('source').donor_id.transform('count').to_numpy(dtype=float)
    counts=donor.cells.to_numpy(dtype=float)
    modes={
        'cell_uniform':np.ones(d,dtype=float),
        'donor_uniform':n/(d*counts),
        'source_donor_uniform':n/(s*source_donors*counts),
    }
    summaries={}
    source_arr=donor.source.to_numpy()
    for mode,w in modes.items():
        weighted_mass=counts*w
        total=float(weighted_mass.sum())
        mean=float(weighted_mass.sum()/n)
        second=float((counts*w*w).sum()/n)
        ess_fraction=(mean*mean)/second
        source_mass={src:float(weighted_mass[source_arr==src].sum()/total) for src in sorted(donor.source.unique())}
        donor_mass=weighted_mass/total
        expected_exposure_at_n=w.copy()  # because q is raw cell-uniform and T=n.
        summaries[mode]={
            'target_source_mass':source_mass,
            'target_donor_mass_min':float(donor_mass.min()),
            'target_donor_mass_median':float(np.median(donor_mass)),
            'target_donor_mass_max':float(donor_mass.max()),
            'if_proposed_cell_uniform':{
                'importance_weight_min':float(w.min()),
                'importance_weight_median_across_donors':float(np.median(w)),
                'importance_weight_max':float(w.max()),
                'importance_weight_max_to_min_ratio':float(w.max()/w.min()),
                'importance_weight_mean_over_cells':mean,
                'effective_sample_size_fraction':float(ess_fraction),
            },
            'if_sampled_directly_from_target':{
                'expected_per_cell_exposures_at_total_presentations_equal_reader_fit_cells_min':float(expected_exposure_at_n.min()),
                'expected_per_cell_exposures_at_total_presentations_equal_reader_fit_cells_median_across_donors':float(np.median(expected_exposure_at_n)),
                'expected_per_cell_exposures_at_total_presentations_equal_reader_fit_cells_max':float(expected_exposure_at_n.max()),
            },
        }
    by_source=(donor.groupby('source').agg(donors=('donor_id','count'),cells=('cells','sum'),min_cells_per_donor=('cells','min'),median_cells_per_donor=('cells','median'),max_cells_per_donor=('cells','max')).reset_index())
    out={
        'schema':'READER_FIT_SCIENTIFIC_ESTIMAND_ANALYSIS_V1',
        'population':'reader_fit',
        'calibration_bundle_sha256':CALIBRATION_BUNDLE_SHA256,
        'metadata_authority':{'bundle_member':BUNDLE_MEMBER,'sha256':observed},
        'reader_fit_cells':n,
        'reader_fit_donors':d,
        'reader_fit_sources':s,
        'donor_capacity_by_source':by_source.to_dict('records'),
        'candidate_estimands':summaries,
        'selected_estimand':None,
        'selected_proposal_sampler':None,
        'interpretation':[
            'Cell-uniform, donor-uniform, and source-donor-uniform are distinct scientific estimands, not interchangeable batching recipes.',
            'Under a raw cell-uniform proposal, donor-balanced targets require high-variance importance weights; direct target sampling avoids p/q variance but can repeatedly expose cells from very small donors.',
            'Scientific target p(cell), proposal q(cell), and compute packing must be frozen as separate authorities.',
            'No candidate is selected by this descriptive analysis and no training authority is created.',
        ],
        'training_authorized':False,
        'execution_authorized':False,
    }
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps({'out':str(a.out),'sha256':sha256(a.out),'cells':n,'donors':d},sort_keys=True))
    return 0

if __name__=='__main__': raise SystemExit(main())
