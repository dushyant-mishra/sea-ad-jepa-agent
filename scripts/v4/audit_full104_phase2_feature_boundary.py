#!/usr/bin/env python3
"""Verify complete feature-block identity and hashes before matrix assembly."""
from __future__ import annotations
import argparse, concurrent.futures, hashlib, json
from pathlib import Path
import numpy as np
import pandas as pd

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(8<<20),b''): h.update(b)
    return h.hexdigest()

def main():
    p=argparse.ArgumentParser(); p.add_argument('--features',required=True); p.add_argument('--cells',type=int,required=True); p.add_argument('--out',required=True); p.add_argument('--workers',type=int,default=8); a=p.parse_args()
    features=Path(a.features).resolve(); out=Path(a.out).resolve()
    if out.exists(): raise RuntimeError('feature-boundary output exists')
    out.mkdir(parents=True)
    manifest=pd.read_csv(features/'PHASE2_MULTIVIEW_FEATURE_BLOCK_MANIFEST.csv',dtype=str)
    if len(manifest)!=manifest.block_key.nunique(): raise RuntimeError('duplicate feature block key')
    seen=np.zeros(a.cells,dtype=np.bool_)
    for row in manifest.itertuples(index=False):
        with np.load(features/row.feature_path,allow_pickle=False) as payload:
            index=payload['selection_row'].astype(np.int64)
        if len(index)!=int(row.rows) or np.any(index<0) or np.any(index>=a.cells) or seen[index].any(): raise RuntimeError(f'feature selection identity mismatch: {row.block_key}')
        seen[index]=True
    if not seen.all(): raise RuntimeError('missing feature selection rows')
    jobs=[(row.block_key,features/row.feature_path,row.feature_sha256) for row in manifest.itertuples(index=False)]
    def verify(job): return job[0], sha(job[1])==job[2]
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1,a.workers)) as ex:
        bad=[key for key,ok in ex.map(verify,jobs) if not ok]
    if bad: raise RuntimeError(f'feature hash mismatch: {bad[:8]}')
    report={'schema':'full104-phase2-feature-boundary-audit-v1','status':'PASS_FEATURE_BOUNDARY_INTEGRITY','cells':a.cells,'blocks':len(manifest),'unique_block_keys':True,'duplicate_selection_rows':0,'missing_selection_rows':0,'all_feature_hashes_recomputed':True,'feature_block_manifest_sha256':sha(features/'PHASE2_MULTIVIEW_FEATURE_BLOCK_MANIFEST.csv')}
    rp=out/'FEATURE_BOUNDARY_INTEGRITY_AUDIT.json'; rp.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    mp=out/'FEATURE_BOUNDARY_INTEGRITY_MANIFEST.csv'; pd.DataFrame([{'path':rp.name,'bytes':rp.stat().st_size,'sha256':sha(rp)},{'path':Path(__file__).name,'bytes':Path(__file__).stat().st_size,'sha256':sha(Path(__file__))}]).to_csv(mp,index=False,lineterminator='\n')
    root=sha(mp); (out/'FEATURE_BOUNDARY_INTEGRITY_ROOT_SHA256.txt').write_text(root+'\n'); print(json.dumps({**report,'manifest_sha256':root},indent=2))
if __name__=='__main__': main()
