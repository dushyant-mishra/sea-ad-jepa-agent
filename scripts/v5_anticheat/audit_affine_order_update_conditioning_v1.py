#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, sqlite3
from pathlib import Path
import numpy as np

def sha256_file(p:Path)->str:
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(8<<20),b""): h.update(b)
    return h.hexdigest()

def run(*,metadata:Path,ledger:Path,H:int,a:int,b:int,update_sizes:list[int])->dict:
    raw=np.memmap(ledger,dtype=np.uint8,mode="r")
    if raw.size%9: raise RuntimeError("ledger byte length not divisible by 9")
    rec=raw.reshape(-1,9)
    keys=rec[:,:8].copy().view("<i8").reshape(-1)
    mult=rec[:,8].astype(np.int16)
    if len(keys)!=4_553_407 or int(mult.sum())!=H:
        raise RuntimeError("ledger geometry mismatch")
    con=sqlite3.connect(f"file:{metadata}?mode=ro&immutable=1",uri=True)
    rows=con.execute("select stable_key,donor_id from cells where partition='reader_fit' order by stable_key").fetchall()
    ds=dict(con.execute("select donor_id,count(*) from cells where partition='reader_fit' group by donor_id").fetchall())
    con.close()
    mk=np.fromiter((r[0] for r in rows),dtype=np.int64,count=len(rows))
    if not np.array_equal(mk,keys): raise RuntimeError("metadata/ledger stable-key mismatch")
    dsize=np.fromiter((ds[r[1]] for r in rows),dtype=np.int32,count=len(rows))
    wcell=H/(len(ds)*dsize.astype(np.float64)*mult.astype(np.float64))
    cum=np.cumsum(mult,dtype=np.int64)
    t=np.arange(H,dtype=np.int64)
    slots=(a*t+b)%H
    idx=np.searchsorted(cum,slots,side="right")
    w=wcell[idx]
    global_ess=float(w.sum()**2/(len(w)*np.dot(w,w)))
    out=[]
    for U in update_sizes:
        n=H//U
        ww=w[:n*U].reshape(n,U)
        sums=ww.sum(1); sq=(ww*ww).sum(1)
        ess=sums*sums/sq/U
        share=ww.max(1)/sums
        out.append({
            "base_cells_per_scientific_update":U,
            "complete_updates":int(n),
            "tail_presentations":int(H-n*U),
            "local_ess_fraction_min":float(ess.min()),
            "local_ess_fraction_p01":float(np.quantile(ess,.01)),
            "local_ess_fraction_median":float(np.median(ess)),
            "maximum_single_presentation_weight_share":float(share.max()),
            "p99_single_presentation_weight_share":float(np.quantile(share,.99)),
        })
    return {
        "schema":"JEPA_V5_AFFINE_ORDER_UPDATE_CONDITIONING_DIAGNOSTIC_V1",
        "status":"REAL_SCHEDULE_DIAGNOSTIC__CURRENT_AFFINE_ORDER_NOT_UPDATE_CONDITIONED",
        "inputs":{
            "metadata_sha256":sha256_file(metadata),
            "ledger_raw_sha256":sha256_file(ledger),
            "H":H,"a":a,"b":b,"cells":len(keys),"donors":len(ds),
            "synthetic_data_used":False,"pathology_used":False,"checkpoint_outcomes_used":False,
        },
        "global_importance_geometry":{
            "weight_min":float(w.min()),"weight_max":float(w.max()),
            "weight_mean":float(w.mean()),"ess_fraction":global_ess,
        },
        "update_diagnostics":out,
        "interpretation":[
            "Global ESS near 0.50 does not guarantee per-update conditioning.",
            "The current affine scientific order is a deterministic permutation but was not constructed to control update-local importance-weight geometry.",
            "Final scientific update membership must be frozen after hardware capacity is known and before optimizer execution; microbatch packing may not change that membership.",
            "This diagnostic does not select an update size, repeat cap, optimizer hyperparameter, or training outcome."
        ],
        "scientific_order_authorized":False,
        "training_authorized":False,
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--metadata",type=Path,required=True)
    p.add_argument("--ledger",type=Path,required=True)
    p.add_argument("--H",type=int,required=True)
    p.add_argument("--a",type=int,required=True)
    p.add_argument("--b",type=int,required=True)
    p.add_argument("--update-sizes",required=True)
    p.add_argument("--output",type=Path,required=True)
    x=p.parse_args()
    o=run(metadata=x.metadata,ledger=x.ledger,H=x.H,a=x.a,b=x.b,update_sizes=[int(v) for v in x.update_sizes.split(",")])
    x.output.parent.mkdir(parents=True,exist_ok=True)
    x.output.write_text(json.dumps(o,indent=2,sort_keys=True)+"\n")
    print(json.dumps(o,indent=2,sort_keys=True))

if __name__=="__main__": main()
