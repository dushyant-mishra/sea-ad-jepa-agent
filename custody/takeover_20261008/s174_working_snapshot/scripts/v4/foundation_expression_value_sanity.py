#!/usr/bin/env python3
"""Current real-value integrity summaries for the frozen 50k sparse payload."""
from pathlib import Path
import hashlib,json
import numpy as np,pandas as pd
from scipy import sparse
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'exports/foundation_corpus_discovery_v1';SEED=20260824
def main():
 x=sparse.load_npz(OUT/'FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.npz').tocsr();fz=pd.read_csv(OUT/'FOUNDATION_DISCOVERY_SAMPLE_FREEZE.csv');support=pd.read_csv(OUT/'FOUNDATION_SUPPORT_BY_OPERATOR.csv').set_index('matrix_id')
 nnz=x.getnnz(axis=1);sums=np.asarray(x.sum(1)).ravel();sq=np.asarray(x.power(2).sum(1)).ravel();mean=np.divide(sums,nnz,out=np.zeros_like(sums),where=nnz>0);var=np.divide(sq,nnz,out=np.zeros_like(sq),where=nnz>0)-mean**2
 rows=[]
 for i,r in fz.iterrows():
  a,b=x.indptr[i],x.indptr[i+1];h=hashlib.sha256();h.update(np.asarray(x.indices[a:b],dtype='<i4').tobytes());h.update(np.asarray(x.data[a:b],dtype='<f4').tobytes());h.update(str(r.support_fingerprint).encode())
  measured=int(support.loc[r.matrix_id,'measured_scalar_addresses']);rows.append({'sample':r['sample'],'sample_row':r.sample_row,'source':r.source,'matrix_id':r.matrix_id,'donor_id':r.donor_id,'cell_id':r.cell_id,'nonzero_measured_values':int(nnz[i]),'measured_scalar_addresses':measured,'measured_zero_count':measured-int(nnz[i]),'measured_zero_fraction':(measured-int(nnz[i]))/measured,'nonzero_value_mean':mean[i],'nonzero_value_variance':var[i],'normalized_value_sum':sums[i],'sparse_payload_sha256':h.hexdigest()})
 cell=pd.DataFrame(rows);cell.to_csv(OUT/'FOUNDATION_CURRENT_REAL_VALUE_SANITY.csv',index=False,lineterminator='\n')
 mu=np.asarray(x.mean(0)).ravel();mu2=np.asarray(x.power(2).mean(0)).ravel();av=pd.DataFrame({'molecular_address_index':np.arange(x.shape[1]),'mean':mu,'variance':np.maximum(mu2-mu**2,0),'nonzero_cells':np.asarray((x!=0).sum(0)).ravel()});av.to_csv(OUT/'FOUNDATION_ADDRESS_VARIANCE.csv',index=False,lineterminator='\n')
 scores=pd.read_csv(OUT/'FOUNDATION_EXPRESSION_PCA_SCORES.csv');scores=scores[scores.view.eq('raw_common')].sort_values(['sample','sample_row']);z=scores[[c for c in scores if c.startswith('PC')]].to_numpy();z=z/np.maximum(np.linalg.norm(z,axis=1,keepdims=True),1e-12);don=fz.sort_values(['sample','sample_row']).donor_id.astype(str).to_numpy();rng=np.random.default_rng(SEED);within=[];between=[]
 positions={d:np.flatnonzero(don==d) for d in np.unique(don)}
 for _ in range(10_000):
  d=rng.choice(list(positions));p=positions[d]
  if len(p)>1:
   a,b=rng.choice(p,2,replace=False);within.append(float(z[a]@z[b]))
  a=rng.integers(len(z));candidates=np.flatnonzero(don!=don[a]);b=rng.choice(candidates);between.append(float(z[a]@z[b]))
 extreme=pd.concat([cell.nsmallest(20,'nonzero_measured_values').assign(extreme_role='lowest_nonzero_count'),cell.nlargest(20,'nonzero_measured_values').assign(extreme_role='highest_nonzero_count'),cell.nlargest(20,'normalized_value_sum').assign(extreme_role='highest_normalized_sum')]);extreme.to_csv(OUT/'FOUNDATION_CURRENT_REAL_VALUE_EXTREMES.csv',index=False,lineterminator='\n')
 report={'cells':len(cell),'unique_payload_hashes':cell.sparse_payload_sha256.nunique(),'measured_zero_fraction_median':float(cell.measured_zero_fraction.median()),'nonzero_measured_values_median':float(cell.nonzero_measured_values.median()),'within_donor_cosine_median':float(np.median(within)),'between_donor_cosine_median':float(np.median(between)),'extreme_rows':'ranked descriptive tails; no impossibility threshold'}
 (OUT/'FOUNDATION_CURRENT_REAL_VALUE_SANITY.md').write_text('# Current real-value sanity\n\n'+json.dumps(report,indent=2)+'\n',encoding='utf-8');(OUT/'FOUNDATION_CURRENT_REAL_VALUE_SANITY.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
