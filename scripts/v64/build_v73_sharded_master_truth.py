#!/usr/bin/env python3
"""Build shard-invariant master truth using authenticated FULL104 population geometry."""
from __future__ import annotations
import argparse, hashlib, json, sys
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import v73_full104_population_geometry as G

MASK=np.uint64(0xFFFFFFFFFFFFFFFF); MASK_INT=(1<<64)-1
C1=np.uint64(0x9E3779B97F4A7C15); C2=np.uint64(0xBF58476D1CE4E5B9); C3=np.uint64(0x94D049BB133111EB)
SOURCE_NAMES=G.SOURCE_ORDER


def sha256_file(path:Path,chunk:int=1<<20):
    h=hashlib.sha256()
    with open(path,'rb') as fh:
        for block in iter(lambda:fh.read(chunk),b''): h.update(block)
    return h.hexdigest()


def _mix64(x):
    x=(x+C1)&MASK; x=((x^(x>>np.uint64(30)))*C2)&MASK
    x=((x^(x>>np.uint64(27)))*C3)&MASK
    return x^(x>>np.uint64(31))


def u01(seed:int,idx,stream:int):
    idx=np.asarray(idx,dtype=np.uint64)
    stream_mix=np.uint64(((int(stream)+1)*int(C1))&MASK_INT)
    z=_mix64(idx^np.uint64(seed)^stream_mix)
    return ((z>>np.uint64(11)).astype(np.float64)+0.5)/float(1<<53)


def normal(seed:int,idx,stream:int):
    u1=np.clip(u01(seed,idx,stream*2),1e-15,1-1e-15); u2=u01(seed,idx,stream*2+1)
    return np.sqrt(-2*np.log(u1))*np.cos(2*np.pi*u2)


def latent_block(seed,ids,start_stream,width):
    return np.stack([normal(seed,ids,start_stream+j) for j in range(width)],axis=1).astype(np.float32)


def source_counts_for_n(n_cells:int):
    a,trip,q=G.quotas_for_n(n_cells)
    ops=np.asarray(a['operator_sources'])
    return np.array([q[[ops[int(op)]==s for op in trip[:,1]]].sum() for s in SOURCE_NAMES],dtype=np.int64)


def build(root:Path,n_cells:int,shard_size:int,seed:int)->dict:
    if n_cells<=0: raise ValueError('n_cells must be positive')
    truth=root/'hidden_truth'; truth.mkdir(parents=True,exist_ok=True)
    authority,trip,quotas=G.quotas_for_n(n_cells)
    authority_sha=G.sha256_file(G.AUTHORITY)
    pop_summary=G.summary_from_quotas(authority,trip,quotas)
    source_counts=source_counts_for_n(n_cells)
    shards=[]; realised_sources=np.zeros(3,dtype=np.int64)
    realised_donors=np.zeros(authority['n_donors'],dtype=np.int64)
    realised_ops=np.zeros(authority['n_operators'],dtype=np.int64)
    for start in range(0,n_cells,shard_size):
        stop=min(start+shard_size,n_cells); ids=np.arange(start,stop,dtype=np.uint64)
        donor,operator,source_ix,_,_,_=G.assignments_for_ids(ids.astype(np.int64),n_cells,seed)
        realised_sources+=np.bincount(source_ix,minlength=3)
        realised_donors+=np.bincount(donor,minlength=authority['n_donors'])
        realised_ops+=np.bincount(operator,minlength=authority['n_operators'])
        path=truth/f'TRUTH_{start:09d}_{stop:09d}.npz'
        np.savez(path,global_cell_index=ids.astype(np.int64),cell_id=np.array([f'MASTER_{int(i):09d}' for i in ids]),
                 donor_index=donor,source_index=source_ix,operator_index=operator,
                 z_global=latent_block(seed,ids,10,4),z_query=latent_block(seed,ids,20,2),
                 z_reg_shared=latent_block(seed,ids,30,3),z_reg_private=latent_block(seed,ids,40,2),
                 technical_latents=latent_block(seed,ids,50,3))
        shards.append(dict(start=start,stop=stop,cells=stop-start,file=path.name,sha256=sha256_file(path)))
    if not np.array_equal(realised_sources,source_counts): raise RuntimeError('source counts did not reconcile')
    if realised_donors.tolist()!=pop_summary['donor_counts']: raise RuntimeError('donor counts did not reconcile')
    if realised_ops.tolist()!=pop_summary['operator_counts']: raise RuntimeError('operator counts did not reconcile')
    manifest=dict(
      schema='V73_SHARDED_MASTER_TRUTH_MANIFEST_V3_EMPIRICAL_FULL104_GEOMETRY',seed=seed,n_cells=n_cells,
      n_donors=authority['n_donors'],n_operators=authority['n_operators'],source_names=list(SOURCE_NAMES),
      authoritative_full104_source_counts=authority['source_counts'],source_counts=dict(zip(SOURCE_NAMES,source_counts.tolist())),
      donor_assignment_status='QUALIFIED_EMPIRICAL_READER_FIT_GROUP_APPORTIONMENT',
      operator_assignment_status='QUALIFIED_EMPIRICAL_SOURCE_OPERATOR_NESTING',
      population_assignment='hierarchical largest-remainder source quotas then authenticated donor x operator cells; deterministic bijection of global cell identity',
      source_assignment_is_shard_invariant=True,randomization='stateless SplitMix64 keyed by (seed, global_cell_index, stream)',
      shard_size_requested=shard_size,shard_size_is_non_scientific=True,shards=shards,
      empirical_calibration=dict(authority_path=str(G.AUTHORITY),authority_sha256=authority_sha,
          authority_triplet_payload_sha256=authority['triplets_payload_sha256'],synthetic_population_summary=pop_summary),
      donor_ids=authority['donor_ids'],operator_ids=authority['operator_ids'],operator_sources=authority['operator_sources'],
      truth_firewall='hidden_truth only; observable manifests must never reference this path')
    (truth/'TRUTH_MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return manifest


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--root',required=True); ap.add_argument('--cells',type=int,required=True)
    ap.add_argument('--shard-size',type=int,default=10000); ap.add_argument('--seed',type=int,default=7302); a=ap.parse_args()
    m=build(Path(a.root),a.cells,a.shard_size,a.seed)
    print(json.dumps(dict(status='PASS',cells=m['n_cells'],shards=len(m['shards']),source_counts=m['source_counts'],
                          donor_assignment_status=m['donor_assignment_status'],operator_assignment_status=m['operator_assignment_status']),indent=2))

if __name__=='__main__': main()
