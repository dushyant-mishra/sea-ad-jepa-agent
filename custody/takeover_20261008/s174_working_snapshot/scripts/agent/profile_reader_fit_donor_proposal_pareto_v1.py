#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, sqlite3
from pathlib import Path
import numpy as np
import pandas as pd

METADATA_SHA='a771f08be31a840b5472448c438a153fbca7de93ba2ed31fe692eaeda02e6913'
ALPHAS=(0.0,0.25,0.5,0.75,0.9,0.95,1.0)

def sha256(p:Path)->str:
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''): h.update(b)
 return h.hexdigest()

def summarize(d:pd.DataFrame,q:np.ndarray,p:np.ndarray,n_total:int)->dict:
 w=p/q
 # Exact ESS fraction for iid proposal draws: (E_q w)^2 / E_q w^2 = 1/E_q w^2.
 eqw2=float(np.sum(d.cells.to_numpy(dtype=float)*q*w*w))
 exposures=n_total*q
 return {
  'importance_weight_min':float(w.min()),
  'importance_weight_median_across_donors':float(np.median(w)),
  'importance_weight_max':float(w.max()),
  'importance_weight_max_to_min_ratio':float(w.max()/w.min()),
  'effective_sample_size_fraction':float(1.0/eqw2),
  'expected_per_cell_exposures_at_total_presentations_equal_reader_fit_cells':{
   'min':float(exposures.min()),'median_across_donors':float(np.median(exposures)),'max':float(exposures.max())
  },
 }

def main()->int:
 ap=argparse.ArgumentParser(); ap.add_argument('--metadata-sqlite',type=Path,required=True); ap.add_argument('--out',type=Path,required=True); a=ap.parse_args()
 if sha256(a.metadata_sqlite)!=METADATA_SHA: raise SystemExit('metadata authority mismatch')
 con=sqlite3.connect(a.metadata_sqlite)
 try:
  d=pd.read_sql_query("select donor_id,source,count(*) cells from cells where partition='reader_fit' group by donor_id,source order by donor_id",con)
  s=pd.read_sql_query("select source,count(*) cells from cells where partition='reader_fit' group by source order by source",con)
 finally: con.close()
 n=int(d.cells.sum()); nd=len(d); ns=len(s); source_cells=dict(zip(s.source,s.cells))
 p=1.0/(nd*d.cells.to_numpy(dtype=float))
 q_cell=np.full(len(d),1.0/n,dtype=float)
 q_source=np.array([1.0/(ns*source_cells[x]) for x in d.source],dtype=float)
 def family(base,name):
  out=[]
  for alpha in ALPHAS:
   q=alpha*p+(1.0-alpha)*base
   out.append({'alpha_donor_uniform':alpha,'alpha_other':1.0-alpha,'other_component':name,**summarize(d,q,p,n)})
  return out
 out={
  'schema':'READER_FIT_DONOR_PROPOSAL_PARETO_V1',
  'population':'reader_fit','cells':n,'donors':nd,'sources':ns,
  'scientific_target_policy_id':'DONOR_UNIFORM__CELL_UNIFORM_WITHIN_DONOR_V1',
  'proposal_families':{
   'donor_plus_cell_uniform':family(q_cell,'CELL_UNIFORM_V1'),
   'donor_plus_source_uniform_cell_within_source':family(q_source,'SOURCE_UNIFORM__CELL_UNIFORM_WITHIN_SOURCE_V1'),
  },
  'interpretation':[
   'alpha=1 samples exactly from the donor-uniform target and needs no importance correction, but repeats cells from small donors most strongly.',
   'alpha=0 avoids donor-target oversampling when the other proposal is cell-like, but requires the largest p/q correction and has the lowest ESS.',
   'Intermediate alpha values are a proposal/variance/repeat tradeoff only; they do not redefine the donor-primary scientific target.',
   'No alpha, presentation horizon, or proposal policy is selected by this descriptive profile.'
  ],
  'selected_proposal_policy':None,'selected_alpha':None,'training_authorized':False,
 }
 a.out.parent.mkdir(parents=True,exist_ok=True); a.out.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
 print(json.dumps({'out':str(a.out),'sha256':sha256(a.out)},sort_keys=True)); return 0
if __name__=='__main__': raise SystemExit(main())
