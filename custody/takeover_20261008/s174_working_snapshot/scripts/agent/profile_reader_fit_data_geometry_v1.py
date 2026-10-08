#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, sqlite3
from pathlib import Path
import numpy as np
import pandas as pd

VOCABULARY_SIZE=41238
CALIBRATION_BUNDLE_SHA256='07748d5bd21fe0857ccad3002fba3946d1791d25898b841d41056a3707117444'
AUTHORITY_MEMBER_PATHS={
 'metadata_sqlite':'metadata/foundation_metadata_rows.sqlite',
 'support_by_operator':'support/FOUNDATION_SUPPORT_BY_OPERATOR.csv',
 'mechanics_inventory':'sampler/t1_encoder_fit_inventory.csv',
}
EXPECTED={
 'metadata_sqlite':'a771f08be31a840b5472448c438a153fbca7de93ba2ed31fe692eaeda02e6913',
 'support_by_operator':'1814a22c8ae01ee94a6fe132546a029af01a7d762384d53c152f37cb545787c1',
 'mechanics_inventory':'7ac13973162a46cafa5baa24c5bea14beb64bd5859e8f58900801eee07083a30',
}

def sha256(path:Path)->str:
 h=hashlib.sha256()
 with path.open('rb') as f:
  for chunk in iter(lambda:f.read(8<<20),b''): h.update(chunk)
 return h.hexdigest()

def qdict(values)->dict[str,float]:
 a=np.asarray(values,dtype=float)
 return {str(q):float(np.quantile(a,q)) for q in (0,.01,.05,.10,.25,.50,.75,.90,.95,.99,1)}

def source_from_canonical_donor(value:str)->str:
 if value.startswith('HVS::'): return 'HVS'
 if value.startswith('NPH52::'): return 'NPH52'
 if value.startswith('SEA_AD::'): return 'SEA_AD'
 raise ValueError(f'unknown canonical donor source: {value}')

def main()->int:
 p=argparse.ArgumentParser()
 p.add_argument('--metadata-sqlite',type=Path,required=True)
 p.add_argument('--support-by-operator',type=Path,required=True)
 p.add_argument('--mechanics-inventory',type=Path,required=True)
 p.add_argument('--out',type=Path,required=True)
 a=p.parse_args()
 inputs={
  'metadata_sqlite':a.metadata_sqlite,
  'support_by_operator':a.support_by_operator,
  'mechanics_inventory':a.mechanics_inventory,
 }
 observed={k:sha256(v) for k,v in inputs.items()}
 if observed!=EXPECTED:
  raise SystemExit(f'input authority mismatch: expected={EXPECTED} observed={observed}')
 con=sqlite3.connect(a.metadata_sqlite)
 try:
  rf_source=pd.read_sql_query("select source,count(*) cells,count(distinct donor_id) donors,count(distinct operator_index) operators from cells where partition='reader_fit' group by source order by source",con)
  donor=pd.read_sql_query("select donor_id,count(*) cells,count(distinct operator_index) operators,count(distinct source) sources from cells where partition='reader_fit' group by donor_id",con)
  operator=pd.read_sql_query("select operator_index,matrix_id,source,count(*) cells,count(distinct donor_id) donors from cells where partition='reader_fit' group by operator_index,matrix_id,source",con)
  groups=pd.read_sql_query("select source,operator_index,donor_id,count(*) cells from cells where partition='reader_fit' group by source,operator_index,donor_id",con)
 finally:
  con.close()
 support=pd.read_csv(a.support_by_operator)
 operator=operator.merge(support[['operator_index','measured_scalar_addresses','measured_scalar_fraction']],on='operator_index',how='left',validate='one_to_one')
 if operator[['measured_scalar_addresses','measured_scalar_fraction']].isna().any().any(): raise RuntimeError('operator support join incomplete')
 operator['hidden_at_historical_40pct']=np.floor(operator.measured_scalar_addresses*0.40).astype(int)
 operator['visible_at_historical_40pct']=operator.measured_scalar_addresses-operator.hidden_at_historical_40pct
 operator['visible_fraction_of_universe_at_historical_40pct']=operator.visible_at_historical_40pct/VOCABULARY_SIZE
 mechanics=pd.read_csv(a.mechanics_inventory)
 mechanics['source']=mechanics['canonical_donor_id'].map(source_from_canonical_donor)
 mg=mechanics.groupby(['source','canonical_donor_id','operator_index']).size().rename('cells').reset_index()
 def group_stats(g):
  total=int(g.cells.sum())
  out={'groups':int(len(g)),'cells':total,'cells_per_group_quantiles':qdict(g.cells)}
  for n in (2,3,4,8,16,32,64,128):
   mask=g.cells>=n
   out[f'groups_ge_{n}']=int(mask.sum())
   out[f'group_fraction_ge_{n}']=float(mask.mean())
   out[f'cells_in_groups_ge_{n}']=int(g.loc[mask,'cells'].sum())
   out[f'cell_fraction_in_groups_ge_{n}']=float(g.loc[mask,'cells'].sum()/total)
  return out
 by_source={src:group_stats(g) for src,g in groups.groupby('source',sort=True)}
 source_support={}
 for src,g in operator.groupby('source',sort=True):
  source_support[src]={
   'operators':int(len(g)),
   'measured_scalar_addresses':{'min':int(g.measured_scalar_addresses.min()),'median':float(g.measured_scalar_addresses.median()),'max':int(g.measured_scalar_addresses.max())},
   'visible_at_historical_40pct':{'min':int(g.visible_at_historical_40pct.min()),'median':float(g.visible_at_historical_40pct.median()),'max':int(g.visible_at_historical_40pct.max())},
   'visible_fraction_of_41238_at_historical_40pct':{'min':float(g.visible_fraction_of_universe_at_historical_40pct.min()),'median':float(g.visible_fraction_of_universe_at_historical_40pct.median()),'max':float(g.visible_fraction_of_universe_at_historical_40pct.max())},
  }
 cell_weighted_measured=float(np.average(operator.measured_scalar_addresses,weights=operator.cells))
 cell_weighted_visible=float(np.average(operator.visible_at_historical_40pct,weights=operator.cells))
 profile={
  'schema':'READER_FIT_DATA_GEOMETRY_PROFILE_V1',
  'calibration_bundle_sha256':CALIBRATION_BUNDLE_SHA256,
  'authority_inputs':{k:{'bundle_member':AUTHORITY_MEMBER_PATHS[k],'sha256':observed[k]} for k in inputs},
  'vocabulary_size':VOCABULARY_SIZE,
  'population':'reader_fit',
  'reader_fit':{
   'cells':int(rf_source.cells.sum()),'donors':int(len(donor)),'operators':int(len(operator)),
   'sources':rf_source.to_dict('records'),
   'donor_cells_quantiles':qdict(donor.cells),
   'donor_operator_count_quantiles':qdict(donor.operators),
   'operator_cells_quantiles':qdict(operator.cells),
   'operator_donor_count_quantiles':qdict(operator.donors),
   'donor_operator_groups':group_stats(groups),
   'donor_operator_groups_by_source':by_source,
   'operator_support_by_source':source_support,
   'cell_weighted_measured_scalar_addresses':cell_weighted_measured,
   'cell_weighted_measured_fraction_of_universe':cell_weighted_measured/VOCABULARY_SIZE,
   'cell_weighted_visible_addresses_at_historical_40pct':cell_weighted_visible,
   'cell_weighted_visible_fraction_of_universe_at_historical_40pct':cell_weighted_visible/VOCABULARY_SIZE,
  },
  'mechanics_3292_comparison':{
   'cells':int(len(mechanics)),'donor_operator_groups':int(len(mg)),
   'cells_per_group_quantiles':qdict(mg.cells),
   'groups_lt_3':int((mg.cells<3).sum()),'group_fraction_lt_3':float((mg.cells<3).mean()),
   'interpretation':'The mechanics inventory spans the same 1,400 donor-by-operator combinations but subsamples only 1-5 cells per combination; its group-size distribution is not production geometry.',
  },
  'data_first_implications':[
   'Do not derive production group size, replay cap, batch geometry, or relational estimability from the 3,292-cell mechanics inventory.',
   'Treat donor-by-operator support as ragged. Equal-size group batches are an execution choice, not a property of reader_fit.',
   'Report evidence both as within-operator visible fraction and as visible fraction of the 41,238-address universe.',
   'Separate scientific cell selection from compute microbatch packing.',
   'Production schedule quantities must be derived from full reader_fit support and separately frozen; this descriptive profile does not authorize training.',
  ],
  'execution_authorized':False,
  'training_authorized':False,
 }
 a.out.parent.mkdir(parents=True,exist_ok=True)
 a.out.write_text(json.dumps(profile,indent=2,sort_keys=True)+'\n',encoding='utf-8')
 print(json.dumps({'out':str(a.out),'sha256':sha256(a.out),'reader_fit_cells':profile['reader_fit']['cells'],'groups':profile['reader_fit']['donor_operator_groups']['groups']},sort_keys=True))
 return 0
if __name__=='__main__': raise SystemExit(main())
