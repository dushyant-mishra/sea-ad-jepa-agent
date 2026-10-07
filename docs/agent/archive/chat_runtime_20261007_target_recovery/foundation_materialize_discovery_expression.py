#!/usr/bin/env python3
"""Materialize the prospectively frozen 50k sample as sparse lawful 41K RNA."""
from __future__ import annotations
import hashlib, json, subprocess, sys, time
from pathlib import Path
import h5py, numpy as np, pandas as pd
from scipy import sparse
from scipy.io import mmread

ROOT=Path(__file__).resolve().parents[2]; OUT=ROOT/'exports/foundation_corpus_discovery_v1'; FREEZE=OUT/'FOUNDATION_DISCOVERY_SAMPLE_FREEZE.csv'
AUTH=Path(r'D:\Jepa project-stage81a3r-20260814'); SHARDS=OUT/'discovery_expression_shards'; ADDRESS_N=41_238

def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''): h.update(b)
 return h.hexdigest()

def decode(v): return np.asarray([x.decode() if isinstance(x,(bytes,np.bytes_)) else str(x) for x in v],object)
def hvec(g,k):
 n=g[k]
 if isinstance(n,h5py.Group) and 'codes' in n:
  c=np.asarray(n['codes']); a=decode(np.asarray(n['categories'])); return np.asarray([a[int(x)] if int(x)>=0 else '' for x in c],object)
 return decode(np.asarray(n))

def main():
 started=time.time(); meta=json.loads((OUT/'FOUNDATION_DISCOVERY_SAMPLE_FREEZE.json').read_text())
 if sha(FREEZE)!=meta['manifest']['sha256'] or not meta['frozen_before_selected_expression_read']: raise RuntimeError('freeze hash/ordering gate failed')
 fz=pd.read_csv(FREEZE,dtype={'stable_key':str});
 if len(fz)!=50_000 or fz.stable_key.nunique()!=50_000 or fz.in_original_t1.sum()!=0: raise RuntimeError('frozen sample integrity failed')
 SHARDS.mkdir(exist_ok=True)
 assets=pd.read_csv(ROOT/'results/v4/stage81a2_canonical_asset_registry.csv').set_index('dataset_id')
 contracts=pd.read_csv(ROOT/'results/v4/stage81a2_matrix_semantics_contract.csv').set_index('dataset_id')
 prov=pd.read_csv(ROOT/'results/v4/stage81a2r_foundation_molecular_address_source_provenance_candidate.csv.gz',low_memory=False)
 coll=pd.read_csv(AUTH/'results/v4/stage81a3r_expression_materialization_collision_ledger.csv.gz',low_memory=False)
 supp=pd.read_csv(AUTH/'results/v4/stage81a3r_scalar_mapping_unregistered_collisions.csv')
 shard_audit=[]
 for matrix_id,g in fz[~fz.source.eq('NPH52')].groupby('matrix_id',sort=True):
  op=int(g.operator_index.iloc[0]); out=SHARDS/f'op{op:02d}.counts.npz'; mp=SHARDS/f'op{op:02d}.meta.csv'
  expected=g.sort_values('sample_row').stable_key.astype(str).tolist()
  if out.exists() and mp.exists():
   existing=pd.read_csv(mp,dtype={'stable_key':str}); matrix=sparse.load_npz(out)
   if existing.stable_key.tolist()!=expected or matrix.shape!=(len(g),ADDRESS_N): raise RuntimeError(f'existing shard identity mismatch op={op}')
   shard_audit.append({'matrix_id':matrix_id,'operator_index':op,'cells':len(g),'nnz':int(matrix.nnz),'counts_sha256':sha(out),'meta_sha256':sha(mp),'reused_after_nph_dependency_repair':True});print('reuse H5 shard',op,len(g),matrix.nnz,flush=True);continue
  study=str(g.source.iloc[0]); source_key='HVS_COMMON' if study=='HVS' else 'SEA_AD_COMMON'
  mapping=prov[prov.source_dataset_id.eq(source_key)][['source_feature_index','molecular_address_index']].copy()
  blocked=set(coll.loc[coll.matrix_id.astype(str).eq(matrix_id),'source_feature_index'].astype(int))
  for s in supp.loc[supp.matrix_id.astype(str).eq(matrix_id),'source_feature_indices'].astype(str): blocked.update(map(int,s.split('|')))
  mapping=mapping[~mapping.source_feature_index.astype(int).isin(blocked)]
  if mapping.source_feature_index.duplicated().any() or mapping.molecular_address_index.duplicated().any(): raise RuntimeError('noninjective mapping '+matrix_id)
  source_to_address=dict(zip(mapping.source_feature_index.astype(int),mapping.molecular_address_index.astype(int)))
  asset=assets.loc[matrix_id]; contract=contracts.loc[matrix_id]; rows=[]; cols=[]; data=[]; libs=[]
  order=g.sort_values('sample_row').reset_index(drop=True)
  with h5py.File(ROOT/str(asset.matrix_path_or_object),'r') as h:
   donor_key='donor_id' if study=='HVS' else 'Donor ID'; donors=hvec(h['obs'],donor_key); cells=hvec(h['obs'],'exp_component_name'); node=h[str(contract.matrix_slot)]
   for dest,r in enumerate(order.itertuples(index=False)):
    sr=int(r.local_row)
    if str(cells[sr])!=str(r.cell_id) or str(donors[sr])!=str(r.donor_id): raise RuntimeError('selected identity mismatch '+matrix_id)
    a,b=int(node['indptr'][sr]),int(node['indptr'][sr+1]); ci=np.asarray(node['indices'][a:b],np.int64); x=np.asarray(node['data'][a:b])
    if np.any(x<0) or not np.allclose(x,np.rint(x)): raise RuntimeError('noninteger raw counts')
    libs.append(int(np.rint(x).sum()))
    for c,v in zip(ci,x):
     target=source_to_address.get(int(c))
     if target is not None and v: rows.append(dest); cols.append(target); data.append(int(round(float(v))))
  mat=sparse.csr_matrix((data,(rows,cols)),shape=(len(order),ADDRESS_N),dtype=np.int32); sparse.save_npz(out,mat,compressed=True)
  order[['stable_key','cell_id','donor_id']].assign(source_library=libs).to_csv(mp,index=False,lineterminator='\n')
  shard_audit.append({'matrix_id':matrix_id,'operator_index':op,'cells':len(order),'nnz':int(mat.nnz),'counts_sha256':sha(out),'meta_sha256':sha(mp)})
  print('H5 shard',op,len(order),mat.nnz,flush=True)

 # NPH uses exact physical TRAIN-only derivatives and the same collision authorities.
 rscript=Path(r'C:\Program Files\R\R-4.1.2\bin\Rscript.exe')
 subprocess.run([str(rscript),str(ROOT/'scripts/v4/foundation_materialize_nph_discovery_sample.R'),str(ROOT),str(FREEZE),str(AUTH),str(SHARDS)],check=True)
 # The R helper emits MatrixMarket shards; convert them deterministically to the
 # same compressed CSR format used by the HDF5-backed operators.
 for op in sorted(fz.loc[fz.source.eq('NPH52'),'operator_index'].unique()):
  stem=SHARDS/f'op{int(op):02d}'; mtx=stem.with_suffix('.mtx'); out=SHARDS/f'op{int(op):02d}.counts.npz'
  if not mtx.exists(): raise RuntimeError(f'missing NPH MatrixMarket shard op={op}')
  matrix=mmread(mtx).tocsr().astype(np.int32)
  if matrix.shape!=(int((fz.operator_index==op).sum()),ADDRESS_N): raise RuntimeError(f'NPH shard shape mismatch op={op}')
  sparse.save_npz(out,matrix,compressed=True)
 # Merge shards in immutable manifest order and normalize once: log1p(10000*raw/library).
 positions={str(k):i for i,k in enumerate(fz.stable_key)}; blocks=[]; meta_blocks=[]
 for op in sorted(fz.operator_index.unique()):
  cp=SHARDS/f'op{int(op):02d}.counts.npz'; mp=SHARDS/f'op{int(op):02d}.meta.csv'; m=pd.read_csv(mp,dtype={'stable_key':str}); x=sparse.load_npz(cp).tocsr()
  if len(m)!=x.shape[0]: raise RuntimeError('shard metadata mismatch')
  dest=np.asarray([positions[k] for k in m.stable_key],np.int64); scale=10_000/np.maximum(m.source_library.to_numpy(float),1)
  y=x.astype(np.float32).multiply(scale[:,None]).tocsr(); y.data=np.log1p(y.data)
  blocks.append((dest,y)); meta_blocks.append(m.assign(operator_index=int(op)))
 order=np.concatenate([d for d,_ in blocks]); stacked=sparse.vstack([x for _,x in blocks],format='csr'); inv=np.argsort(order); final=stacked[inv]
 if not np.array_equal(np.sort(order),np.arange(len(fz))) or final.shape!=(50_000,ADDRESS_N) or not np.isfinite(final.data).all(): raise RuntimeError('global sparse merge failed')
 final_path=OUT/'FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.npz'; sparse.save_npz(final_path,final,compressed=True)
 audit={'schema':'foundation-discovery-expression-v1','freeze_sha256':sha(FREEZE),'cells':len(fz),'addresses':ADDRESS_N,'nnz':int(final.nnz),'density':float(final.nnz/(len(fz)*ADDRESS_N)),'normalization':'log1p(raw_count*10000/full_source_library) exactly once','output_sha256':sha(final_path),'shards':shard_audit,'wall_seconds':time.time()-started,'firewalls':meta['firewalls']}
 (OUT/'FOUNDATION_DISCOVERY_EXPRESSION_AUDIT.json').write_text(json.dumps(audit,indent=2)+'\n')
 print(json.dumps({k:audit[k] for k in ('cells','addresses','nnz','density','wall_seconds')},indent=2))
if __name__=='__main__': main()
