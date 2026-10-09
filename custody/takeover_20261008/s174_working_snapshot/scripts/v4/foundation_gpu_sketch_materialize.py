#!/usr/bin/env python3
"""Operator-checkpointed GPU materialization of two frozen sparse sketches."""
from __future__ import annotations
import hashlib,json,time
from pathlib import Path
import numpy as np,pandas as pd,torch
from scipy import sparse
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'exports/foundation_corpus_discovery_v1';SHARDS=OUT/'discovery_expression_shards';BLOCKS=OUT/'dual_sketch_blocks';SEEDS=(2026082409,2026082417);DIM=512;HASHES=4
def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()
def projection_arrays(n,seed):
 rng=np.random.default_rng(seed);col=np.stack([rng.choice(DIM,HASHES,replace=False) for _ in range(n)]).astype(np.int32);sign=rng.choice(np.asarray([-1.,1.],np.float32),size=(n,HASHES))/np.sqrt(HASHES);return col,sign
def scatter(values,rows,positions,maps,nrows,device):
 row=torch.from_numpy(rows.astype(np.int64)).to(device);value=torch.from_numpy(values.astype(np.float32)).to(device);outs=[]
 for columns,signs in maps:
  flat=torch.zeros(nrows*DIM,dtype=torch.float32,device=device)
  for h in range(HASHES):
   bucket=torch.from_numpy(columns[positions,h].astype(np.int64)).to(device);weight=torch.from_numpy(signs[positions,h]).to(device);flat.scatter_add_(0,row*DIM+bucket,value*weight)
  outs.append(flat.view(nrows,DIM).cpu().numpy())
 return outs
def main():
 started=time.time();BLOCKS.mkdir(exist_ok=True);freeze=pd.read_csv(OUT/'FOUNDATION_DISCOVERY_SAMPLE_FREEZE.csv');rec=pd.read_csv(OUT/'FOUNDATION_SUPPORT_ADDRESS_RECURRENCE.csv');addresses=rec.loc[rec.operators_measured_scalar.eq(42),'molecular_address_index'].to_numpy(np.int64);device=torch.device('cuda' if torch.cuda.is_available() else 'cpu');pos=np.full(41_238,-1,np.int32);pos[addresses]=np.arange(len(addresses),dtype=np.int32);maps=[projection_arrays(len(addresses),s) for s in SEEDS]
 contract={'schema':'foundation-dual-sketch-operator-checkpoint-v1','expression_audit_sha256':sha(OUT/'FOUNDATION_DISCOVERY_EXPRESSION_AUDIT.json'),'freeze_sha256':sha(OUT/'FOUNDATION_DISCOVERY_SAMPLE_FREEZE.csv'),'seeds':SEEDS,'dimension':DIM,'hashes':HASHES,'common_addresses':len(addresses),'device_type':device.type};contract_hash=hashlib.sha256(json.dumps(contract,sort_keys=True).encode()).hexdigest();parts=[]
 for op in sorted(freeze.operator_index.unique().astype(int)):
  meta=pd.read_csv(SHARDS/f'op{op:02d}.meta.csv');path=BLOCKS/f'op{op:02d}.npz'
  if path.exists():
   old=np.load(path);valid=str(old['contract_sha256'])==contract_hash and np.array_equal(old['stable_key'],meta.stable_key.to_numpy(np.int64))
   if valid:parts.append(path);print(f'reused op{op:02d}',flush=True);continue
  x=sparse.load_npz(SHARDS/f'op{op:02d}.counts.npz').tocsr().astype(np.float32);scale=10_000/np.maximum(meta.source_library.to_numpy(np.float32),1);x=x.multiply(scale[:,None]).tocsr();x.data=np.log1p(x.data);coo=x.tocoo();selected=pos[coo.col]>=0;out=scatter(coo.data[selected],coo.row[selected],pos[coo.col[selected]],maps,len(meta),device);np.savez_compressed(path,score_A=out[0],score_B=out[1],stable_key=meta.stable_key.to_numpy(np.int64),operator_index=np.asarray(op),contract_sha256=np.asarray(contract_hash));parts.append(path);print(f'checkpoint op{op:02d} rows={len(meta)}',flush=True)
 keyrow=pd.Series(np.arange(len(freeze)),index=freeze.stable_key.astype(np.int64));za=np.empty((len(freeze),DIM),np.float32);zb=np.empty_like(za);seen=np.zeros(len(freeze),bool)
 for path in parts:
  p=np.load(path);rows=keyrow.loc[p['stable_key']].to_numpy(np.int64);za[rows]=p['score_A'];zb[rows]=p['score_B'];seen[rows]=True
 if not seen.all() or not np.isfinite(za).all() or not np.isfinite(zb).all():raise RuntimeError('assembled sketch identity/value mismatch')
 np.savez_compressed(OUT/'FOUNDATION_DUAL_SKETCH_MATERIALIZED.npz',score_A=za,score_B=zb,stable_key=freeze.stable_key.to_numpy(np.int64),contract_sha256=np.asarray(contract_hash));contract.update({'contract_sha256':contract_hash,'operator_checkpoints':len(parts),'wall_seconds':time.time()-started,'training_updates':0});(OUT/'FOUNDATION_DUAL_SKETCH_MATERIALIZATION.json').write_text(json.dumps(contract,indent=2)+'\n');print(json.dumps(contract,indent=2))
if __name__=='__main__':main()
