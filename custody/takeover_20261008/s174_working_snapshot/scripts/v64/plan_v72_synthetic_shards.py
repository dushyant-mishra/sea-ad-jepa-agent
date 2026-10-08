#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path


def shard_seed(master_seed:int, shard_index:int)->int:
    h=hashlib.sha256(f"{master_seed}:{shard_index}".encode()).digest()
    return int.from_bytes(h[:8],"big") & 0x7fffffff


def plan(total_cells:int, shard_cells:int=100_000, master_seed:int=7202):
    if total_cells<=0 or shard_cells<=0:
        raise ValueError("total_cells and shard_cells must be positive")
    n=math.ceil(total_cells/shard_cells)
    shards=[]
    start=0
    for i in range(n):
        end=min(total_cells,start+shard_cells)
        shards.append({
            "shard_index":i,
            "cell_start_inclusive":start,
            "cell_end_exclusive":end,
            "n_cells":end-start,
            "seed":shard_seed(master_seed,i),
            "global_cell_id_rule":f"MASTER_{{global_index:09d}}",
            "truth_partition_rule":"derive shard latent state only from master_seed+shard_index; all modalities in this shard reuse the same latent rows",
        })
        start=end
    digest=hashlib.sha256(json.dumps(shards,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    return {
        "schema":"V72_SYNTHETIC_SHARD_PLAN_V1",
        "total_cells":total_cells,
        "shard_cells_requested":shard_cells,
        "n_shards":n,
        "master_seed_private_to_generator":master_seed,
        "shards":shards,
        "ordered_plan_sha256":digest,
        "invariants":[
            "shards are non-overlapping and exactly cover [0,total_cells)",
            "global cell identity is stable independent of shard size",
            "all modalities for a cell are generated from the same shard truth",
            "shard seeds are deterministic and content-addressable from generator authority only",
            "pipeline-facing manifests must not expose master_seed if blind challenge reconstruction would leak truth"
        ],
        "status":"PASS__DETERMINISTIC_SHARD_PLAN"
    }


def validate(p):
    errors=[]
    shards=p.get("shards",[])
    if p.get("n_shards")!=len(shards): errors.append("N_SHARDS_MISMATCH")
    expected=0
    seen=set()
    for i,s in enumerate(shards):
        if s.get("shard_index")!=i: errors.append(f"SHARD_INDEX_MISMATCH:{i}")
        if s.get("cell_start_inclusive")!=expected: errors.append(f"GAP_OR_OVERLAP_BEFORE:{i}")
        end=s.get("cell_end_exclusive")
        if not isinstance(end,int) or end<=expected: errors.append(f"BAD_END:{i}"); continue
        if s.get("n_cells")!=end-expected: errors.append(f"N_CELLS_MISMATCH:{i}")
        if s.get("seed") in seen: errors.append(f"DUPLICATE_SHARD_SEED:{i}")
        seen.add(s.get("seed")); expected=end
    if expected!=p.get("total_cells"): errors.append("TOTAL_COVERAGE_MISMATCH")
    return errors


def main(argv=None):
    ap=argparse.ArgumentParser()
    ap.add_argument("--cells",type=int,required=True)
    ap.add_argument("--shard-cells",type=int,default=100_000)
    ap.add_argument("--master-seed",type=int,default=7202)
    ap.add_argument("--out")
    a=ap.parse_args(argv)
    r=plan(a.cells,a.shard_cells,a.master_seed)
    errs=validate(r)
    if errs: raise SystemExit("\n".join(errs))
    s=json.dumps(r,indent=2)+"\n"
    if a.out: Path(a.out).write_text(s)
    print(s,end="")


if __name__=="__main__":
    main()
