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


def _proposal_diagnostic(*, donor:pd.DataFrame, target_p:np.ndarray, proposal_q:np.ndarray)->dict[str,float]:
    counts=donor.cells.to_numpy(dtype=float)
    if not np.isclose(float((counts*target_p).sum()),1.0,atol=1e-12): raise RuntimeError('target probability does not normalize')
    if not np.isclose(float((counts*proposal_q).sum()),1.0,atol=1e-12): raise RuntimeError('proposal probability does not normalize')
    w=target_p/proposal_q
    mean=float((counts*proposal_q*w).sum())
    second=float((counts*proposal_q*w*w).sum())
    return {
        'importance_weight_min':float(w.min()),
        'importance_weight_median_across_donors':float(np.median(w)),
        'importance_weight_max':float(w.max()),
        'importance_weight_max_to_min_ratio':float(w.max()/w.min()),
        'importance_weight_mean_under_proposal':mean,
        'effective_sample_size_fraction':float((mean*mean)/second),
    }


def _target_summary(*, donor:pd.DataFrame, target_p:np.ndarray,total_cells:int)->dict[str,object]:
    counts=donor.cells.to_numpy(dtype=float); source_arr=donor.source.to_numpy()
    donor_mass=counts*target_p
    total=float(donor_mass.sum())
    return {
        'target_source_mass':{src:float(donor_mass[source_arr==src].sum()/total) for src in sorted(donor.source.unique())},
        'target_donor_mass_min':float(donor_mass.min()/total),
        'target_donor_mass_median':float(np.median(donor_mass/total)),
        'target_donor_mass_max':float(donor_mass.max()/total),
        'expected_per_cell_exposures_at_total_presentations_equal_reader_fit_cells':{
            'min':float((total_cells*target_p).min()),
            'median_across_donors':float(np.median(total_cells*target_p)),
            'max':float((total_cells*target_p).max()),
        },
    }


def main()->int:
    p=argparse.ArgumentParser(); p.add_argument('--metadata-sqlite',type=Path,required=True); p.add_argument('--out',type=Path,required=True); a=p.parse_args()
    observed=sha256(a.metadata_sqlite)
    if observed != METADATA_SHA256: raise SystemExit(f'metadata authority mismatch: {observed}')
    con=sqlite3.connect(a.metadata_sqlite)
    try:
        donor=pd.read_sql_query("select source,donor_id,count(*) cells from cells where partition='reader_fit' group by source,donor_id order by source,donor_id",con)
    finally: con.close()
    n=int(donor.cells.sum()); d=int(len(donor)); s=int(donor.source.nunique())
    counts=donor.cells.to_numpy(dtype=float)
    source_counts=donor.groupby('source').cells.transform('sum').to_numpy(dtype=float)
    source_donors=donor.groupby('source').donor_id.transform('count').to_numpy(dtype=float)
    targets={
        'cell_uniform':np.full(d,1.0/n),
        'source_uniform_cell_within_source':1.0/(s*source_counts),
        'donor_uniform':1.0/(d*counts),
        'source_donor_uniform':1.0/(s*source_donors*counts),
    }
    proposals={
        'cell_uniform':np.full(d,1.0/n),
        'source_uniform_cell_within_source':1.0/(s*source_counts),
    }
    summaries={}
    for name,p_target in targets.items():
        item=_target_summary(donor=donor,target_p=p_target,total_cells=n)
        item['proposal_diagnostics']={qname:_proposal_diagnostic(donor=donor,target_p=p_target,proposal_q=q) for qname,q in proposals.items()}
        summaries[name]=item
    by_source=(donor.groupby('source').agg(donors=('donor_id','count'),cells=('cells','sum'),min_cells_per_donor=('cells','min'),median_cells_per_donor=('cells','median'),max_cells_per_donor=('cells','max')).reset_index())
    out={
        'schema':'READER_FIT_SCIENTIFIC_ESTIMAND_ANALYSIS_V2','population':'reader_fit','calibration_bundle_sha256':CALIBRATION_BUNDLE_SHA256,
        'metadata_authority':{'bundle_member':BUNDLE_MEMBER,'sha256':observed},'reader_fit_cells':n,'reader_fit_donors':d,'reader_fit_sources':s,
        'donor_capacity_by_source':by_source.to_dict('records'),'candidate_estimands':summaries,
        'candidate_proposals':list(proposals),'selected_base_jepa_estimand':None,'selected_base_jepa_proposal_sampler':None,'selected_relational_estimand':None,
        'interpretation':[
            'Base-JEPA and donor-recurrent relational supervision are different scientific objectives and need not share one estimand.',
            'A source-uniform/cell-within-source proposal prevents raw SEA_AD cell-count dominance at sampling time and materially improves importance-weight efficiency for donor-balanced targets compared with a raw cell-uniform proposal.',
            'Donor-uniform target with source-uniform/cell-within-source proposal has ~40.6% importance-sampling ESS in this frozen reader-fit population, versus ~9.7% under raw cell-uniform proposal.',
            'Source-donor-uniform target with that source-balanced proposal has ~21.2% ESS, versus ~3.7% under raw cell-uniform proposal.',
            'Scientific target p, proposal q, relational hierarchy, and compute packing remain separate authorities; this profile selects none and creates no training authority.',
        ],'training_authorized':False,'execution_authorized':False,
    }
    a.out.parent.mkdir(parents=True,exist_ok=True); a.out.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps({'out':str(a.out),'sha256':sha256(a.out),'cells':n,'donors':d},sort_keys=True)); return 0
if __name__=='__main__': raise SystemExit(main())
