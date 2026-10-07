from pathlib import Path
import glob,json
import numpy as np,pandas as pd
ROOT=Path('/mnt/data'); OUT=ROOT/'td_iteration33_global_row_binding_guard'; OUT.mkdir(exist_ok=True)
ARR=ROOT/'td_matrix_npz'/'arrays'; data=np.load(ARR/'data.npy',mmap_mode='r'); indices=np.load(ARR/'indices.npy',mmap_mode='r'); indptr=np.load(ARR/'indptr.npy',mmap_mode='r')
meta=pd.read_csv(ROOT/'td_expr_meta'/'FOUNDATION_DISCOVERY_SAMPLE_FREEZE.csv'); meta['global_row']=np.arange(len(meta),dtype=np.int64)
B=meta[meta['sample'].eq('B_COVERAGE_DISCOVERY')].copy()
parts=[pd.read_csv(p,usecols=['stable_key','source_library']) for p in glob.glob('/mnt/data/td_expr_meta/operator/**/op*.meta.csv',recursive=True)]
lib=pd.concat(parts,ignore_index=True).drop_duplicates('stable_key'); B=B.merge(lib,on='stable_key',how='left',validate='one_to_one',sort=False)
assert B.global_row.min()==25000 and B.global_row.max()==49999
assert np.array_equal(B.sample_row.to_numpy(),B.global_row.to_numpy()-25000)
assert B.source_library.notna().all()
errs=[]; alias_errs=[]
for r,sr,L in zip(B.global_row.to_numpy(),B.sample_row.to_numpy(),B.source_library.to_numpy()):
 a,b=int(indptr[r]),int(indptr[r+1]);
 if a<b:
  y=np.expm1(float(data[a]))*float(L)/10000.0; errs.append(abs(y-round(y)))
 aa,bb=int(indptr[sr]),int(indptr[sr+1]);
 if aa<bb:
  y=np.expm1(float(data[aa]))*float(L)/10000.0; alias_errs.append(abs(y-round(y)))
summary={'schema':'td33-global-row-binding-guard-v1','B_rows':len(B),'global_row_range':[int(B.global_row.min()),int(B.global_row.max())],'sample_row_range':[int(B.sample_row.min()),int(B.sample_row.max())],'global_first_nonzero_integer_fraction_lt_1e-8':float(np.mean(np.array(errs)<1e-8)),'global_max_integer_residual':float(np.max(errs)),'alias_first_nonzero_integer_fraction_lt_1e-8':float(np.mean(np.array(alias_errs)<1e-8)),'alias_median_integer_residual':float(np.median(alias_errs)),'decision':'PASS_GLOBAL_ROW_BINDING__RESET_INDEX_FORBIDDEN'}
(OUT/'TD33_SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n'); B[['global_row','sample_row','source','stable_key','source_library']].to_csv(OUT/'TD33_BOUND_B_ROWS.csv',index=False); print(json.dumps(summary,indent=2))
