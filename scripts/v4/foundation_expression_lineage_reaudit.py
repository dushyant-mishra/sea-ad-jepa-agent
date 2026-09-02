#!/usr/bin/env python3
"""Fail-closed 42-operator lineage re-audit of the frozen discovery matrix."""
from __future__ import annotations
import hashlib,json
from pathlib import Path
import numpy as np,pandas as pd
from scipy import sparse

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'exports/foundation_corpus_discovery_v1'
SHARDS=OUT/'discovery_expression_shards'
AUTH=Path(r'D:\Jepa project-stage81a3r-20260814')

def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()
def label(path):
 try:return str(Path(path).relative_to(ROOT))
 except ValueError:return str(path)

def main():
 freeze_path=OUT/'FOUNDATION_DISCOVERY_SAMPLE_FREEZE.csv';freeze_meta=OUT/'FOUNDATION_DISCOVERY_SAMPLE_FREEZE.json'
 fz=pd.read_csv(freeze_path,dtype={'stable_key':str});meta=json.loads(freeze_meta.read_text())
 if sha(freeze_path)!=meta['manifest']['sha256'] or len(fz)!=50_000 or fz.stable_key.nunique()!=50_000:raise RuntimeError('freeze mismatch')
 final_path=OUT/'FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.npz';final=sparse.load_npz(final_path).tocsr();positions={str(k):i for i,k in enumerate(fz.stable_key)}
 if final.shape!=(50_000,41_238) or not np.isfinite(final.data).all():raise RuntimeError('final matrix contract mismatch')
 shards=[]
 for op in sorted(fz.operator_index.unique()):
  g=fz[fz.operator_index.eq(op)].sort_values('sample_row');cp=SHARDS/f'op{int(op):02d}.counts.npz';mp=SHARDS/f'op{int(op):02d}.meta.csv'
  if not cp.exists() or not mp.exists():raise RuntimeError(f'missing shard op={op}')
  m=pd.read_csv(mp,dtype={'stable_key':str});x=sparse.load_npz(cp).tocsr();x.sum_duplicates();x.sort_indices()
  if x.shape!=(len(g),41_238) or len(m)!=len(g) or set(m.stable_key)!=set(g.stable_key) or m.stable_key.duplicated().any():raise RuntimeError(f'shard identity mismatch op={op}')
  gm=g.set_index('stable_key');mm=m.set_index('stable_key')
  if not np.array_equal(mm.cell_id.astype(str).to_numpy(),gm.loc[mm.index,'cell_id'].astype(str).to_numpy()) or not np.array_equal(mm.donor_id.astype(str).to_numpy(),gm.loc[mm.index,'donor_id'].astype(str).to_numpy()):raise RuntimeError(f'shard cell/donor mismatch op={op}')
  if np.any(x.data<0) or not np.array_equal(x.data,np.rint(x.data)):raise RuntimeError(f'raw-count contract mismatch op={op}')
  dest=np.asarray([positions[k] for k in m.stable_key],np.int64);scale=10_000/np.maximum(m.source_library.to_numpy(float),1);y=x.astype(np.float32).multiply(scale[:,None]).tocsr();y.data=np.log1p(y.data);y.sum_duplicates();y.sort_indices();ref=final[dest].tocsr();ref.sum_duplicates();ref.sort_indices()
  if not (np.array_equal(y.indptr,ref.indptr) and np.array_equal(y.indices,ref.indices) and np.array_equal(y.data,ref.data)):raise RuntimeError(f'final payload mismatch op={op}')
  shards.append({'operator_index':int(op),'matrix_id':str(g.matrix_id.iloc[0]),'source':str(g.source.iloc[0]),'cells':len(g),'nnz':int(x.nnz),'counts_sha256':sha(cp),'meta_sha256':sha(mp),'identity_exact':True,'normalized_payload_exact_in_final':True})
 if len(shards)!=42 or {x['operator_index'] for x in shards}!=set(range(42)):raise RuntimeError('operator completeness failed')
 controls=[
  freeze_path,freeze_meta,
  ROOT/'results/v4/stage81a2_canonical_asset_registry.csv',ROOT/'results/v4/stage81a2_matrix_semantics_contract.csv',
  ROOT/'results/v4/stage81a2r_foundation_molecular_address_registry_candidate.csv',ROOT/'results/v4/stage81a2r_foundation_molecular_address_source_provenance_candidate.csv.gz',
  ROOT/'results/v4/stage81a2r_foundation_molecular_address_measurement_support_candidate.csv.gz',ROOT/'results/v4/stage81a2r_foundation_molecular_address_injectivity_audit.json',
  AUTH/'results/v4/stage81a3r_expression_materialization_collision_ledger.csv.gz',AUTH/'results/v4/stage81a3r_scalar_mapping_unregistered_collisions.csv',
  ROOT/'scripts/v4/foundation_materialize_discovery_expression.py',ROOT/'scripts/v4/foundation_materialize_nph_discovery_sample.R',ROOT/'scripts/v4/foundation_metadata_atlas_and_freeze.py',
  ROOT/'exports/static_context_decomposition_v4_20260821/production_train_loader.py',ROOT/'scripts/v4/stage81a3_prod41k_engineering_smoke.py']
 missing=[str(p) for p in controls if not p.exists()]
 if missing:raise RuntimeError('missing controlling inputs: '+repr(missing))
 audit={'schema':'foundation-discovery-expression-lineage-v2','status':'PASS','freeze_sha256':sha(freeze_path),'cells':len(fz),'addresses':final.shape[1],'nnz':int(final.nnz),'output_sha256':sha(final_path),'operator_count':42,'operator_indices':list(range(42)),'all_shard_identities_exact':True,'all_normalized_payloads_exact_in_final':True,'shards':shards,'controlling_inputs':[{'path':label(p),'sha256':sha(p)} for p in controls],'firewalls':meta['firewalls'],'neural_updates':0}
 out=OUT/'FOUNDATION_DISCOVERY_EXPRESSION_LINEAGE_V2.json';out.write_text(json.dumps(audit,indent=2)+'\n',encoding='utf-8');print(json.dumps({'status':'PASS','operators':42,'output_sha256':audit['output_sha256'],'audit_sha256':sha(out)},indent=2))

if __name__=='__main__':main()
