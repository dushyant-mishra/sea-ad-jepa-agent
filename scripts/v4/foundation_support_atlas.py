#!/usr/bin/env python3
"""Observation-state/support atlas over the frozen 41,238-address authority."""
from pathlib import Path
import json,sqlite3,sys
import numpy as np,pandas as pd
ROOT=Path(__file__).resolve().parents[2]; OUT=ROOT/'exports/foundation_corpus_discovery_v1'; sys.path.insert(0,str(ROOT/'exports/static_context_decomposition_v4_20260821'))
from production_train_loader import ProductionTrainLoader,MEASURED_SCALAR,STRUCTURALLY_UNMEASURED,MEASURED_COLLISION_UNRESOLVED
def source(m): return 'HVS' if m.startswith('HVS::') else ('NPH52' if m.startswith('NPH52::') else 'SEA_AD')
def main():
 l=ProductionTrainLoader(); con=sqlite3.connect(OUT/'foundation_metadata_rows.sqlite'); counts=pd.read_sql_query("select matrix_id,count(*) cell_count,sum(in_original_t1) original_t1_cells from cells where partition='reader_fit' group by matrix_id",con).set_index('matrix_id')
 rows=[]
 ordered=[]
 for op,item in enumerate(l.items):
  m=item['matrix_id']; s=l.states[m]; c=counts.loc[m]
  rows.append({'operator_index':op,'matrix_id':m,'source':source(m),'fit104_cells':int(c.cell_count),'original_t1_cells':int(c.original_t1_cells),'measured_scalar_addresses':int((s==MEASURED_SCALAR).sum()),'structurally_unmeasured_addresses':int((s==STRUCTURALLY_UNMEASURED).sum()),'collision_unresolved_addresses':int((s==MEASURED_COLLISION_UNRESOLVED).sum()),'measured_scalar_fraction':float((s==MEASURED_SCALAR).mean()),'structurally_unmeasured_fraction':float((s==STRUCTURALLY_UNMEASURED).mean()),'collision_unresolved_fraction':float((s==MEASURED_COLLISION_UNRESOLVED).mean())}); ordered.append(s)
 opf=pd.DataFrame(rows); opf.to_csv(OUT/'FOUNDATION_SUPPORT_BY_OPERATOR.csv',index=False,lineterminator='\n')
 src=[]
 for name,g in opf.groupby('source'):
  w=g.fit104_cells.to_numpy(float); src.append({'source':name,'fit104_cells':int(w.sum()),'operators':len(g),'cell_weighted_measured_scalar_fraction':float(np.average(g.measured_scalar_fraction,weights=w)),'cell_weighted_structurally_unmeasured_fraction':float(np.average(g.structurally_unmeasured_fraction,weights=w)),'cell_weighted_collision_unresolved_fraction':float(np.average(g.collision_unresolved_fraction,weights=w)),'original_t1_cells':int(g.original_t1_cells.sum())})
 pd.DataFrame(src).to_csv(OUT/'FOUNDATION_SUPPORT_BY_SOURCE.csv',index=False,lineterminator='\n')
 cls=pd.read_sql_query("select matrix_id,native_class,broad_class,count(*) cell_count,sum(in_original_t1) original_t1_cells from cells where partition='reader_fit' group by matrix_id,native_class,broad_class",con).merge(opf,on='matrix_id',how='left')
 cls.to_csv(OUT/'FOUNDATION_SUPPORT_BY_CELL_CLASS.csv',index=False,lineterminator='\n')
 states=np.stack(ordered); reg=l.registry[['molecular_address_index','molecular_address_id','symbol','identity_class']].copy(); reg['operators_measured_scalar']=(states==MEASURED_SCALAR).sum(0); reg['operators_structurally_unmeasured']=(states==STRUCTURALLY_UNMEASURED).sum(0); reg['operators_collision_unresolved']=(states==MEASURED_COLLISION_UNRESOLVED).sum(0)
 for name in ('HVS','NPH52','SEA_AD'):
  take=np.asarray([source(x['matrix_id'])==name for x in l.items]); reg[f'{name}_operators_measured_scalar']=(states[take]==MEASURED_SCALAR).sum(0)
 reg['source_families_measuring']=sum((reg[f'{n}_operators_measured_scalar']>0).astype(int) for n in ('HVS','NPH52','SEA_AD'))
 reg.to_csv(OUT/'FOUNDATION_SUPPORT_ADDRESS_RECURRENCE.csv',index=False,lineterminator='\n')
 report={'addresses':len(reg),'operators':42,'fit104_cells':int(opf.fit104_cells.sum()),'scalar_observable_any_operator':int((reg.operators_measured_scalar>0).sum()),'collision_only_or_unobserved_all_operators':int((reg.operators_measured_scalar==0).sum()),'original_t1_cells':int(opf.original_t1_cells.sum()),'measured_zero_frequency':'PENDING_FROZEN_EXPRESSION_SAMPLE_VALUE_READ'}
 (OUT/'FOUNDATION_SUPPORT_ATLAS.md').write_text(f"# FOUNDATION support atlas\n\nAcross 42 operators and 41,238 addresses, {report['scalar_observable_any_operator']:,} addresses are scalar-observable in at least one operator and {report['collision_only_or_unobserved_all_operators']:,} are never scalar-observable. Three states are reported separately; measured zero is not missing. Operator/source/class tables retain physical-support and old-cache counts. Measured-zero frequency is filled only after the frozen expression sample is read.\n")
 (OUT/'FOUNDATION_SUPPORT_ATLAS.json').write_text(json.dumps(report,indent=2)+'\n'); print(json.dumps(report,indent=2))
if __name__=='__main__':main()
