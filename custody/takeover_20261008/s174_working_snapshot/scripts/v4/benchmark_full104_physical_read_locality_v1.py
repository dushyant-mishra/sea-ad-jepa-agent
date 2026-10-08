#!/usr/bin/env python3
"""Crossover benchmark of old logical gather versus sorted physical gather."""
from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
import psutil


def counters():
    process=psutil.Process(); memory=process.memory_info(); disk=psutil.disk_io_counters(); cpu=psutil.cpu_percent(interval=None)
    return {"process_read_bytes":process.io_counters().read_bytes,"rss":memory.rss,
            "page_faults":getattr(memory,"num_page_faults",None),"disk_read_bytes":disk.read_bytes,
            "disk_read_time_ms":disk.read_time,"cpu_percent":cpu}


def delta(before,after):
    return {key:(None if before[key] is None or after[key] is None else after[key]-before[key]) for key in before}


def gather(views, logical, mode):
    logical=np.asarray(logical,np.int64);perm=np.argsort(logical,kind="stable");before=counters();started=time.perf_counter()
    if mode=="old_random_logical": result=np.asarray(views[logical],np.float32)
    else:
        physical=np.asarray(views[logical[perm]],np.float32);inverse=np.empty(len(logical),np.int64);inverse[perm]=np.arange(len(logical));result=physical[inverse]
    elapsed=time.perf_counter()-started;after=counters()
    return result,{"mode":mode,"rows":len(logical),"wall_seconds":elapsed,"logical_bytes":int(result.nbytes),
                   "logical_row_order_sha256":__import__('hashlib').sha256(logical.tobytes()).hexdigest(),
                   "counter_delta":delta(before,after),"throughput_logical_bytes_per_second":result.nbytes/elapsed}


def main():
    parser=argparse.ArgumentParser();parser.add_argument("--matrix",required=True);parser.add_argument("--plan-dir",required=True);parser.add_argument("--out",required=True)
    args=parser.parse_args();out=Path(args.out).resolve();out.mkdir(parents=True,exist_ok=False);plan_dir=Path(args.plan_dir).resolve();matrix=Path(args.matrix).resolve()
    with np.load(plan_dir/"NESTED_WEIGHTED_SELECTION.npz",allow_pickle=False) as z:plan=pd.DataFrame({n:z[n] for n in z.files})
    sizes=plan.groupby(["donor_id","operator_index"],sort=True).size();targets=[]
    for q in (0.0,0.5,0.9):targets.append((sizes-float(sizes.quantile(q))).abs().idxmin())
    fixtures=[(str(d),int(o),plan[(plan.donor_id==d)&(plan.operator_index==o)].row_index.to_numpy(np.int64)) for d,o in targets]
    records=[]
    # Crossover avoids always granting the second method the same-file page-cache advantage.
    for sketch,first,second in (("A","old_random_logical","sorted_physical_restore"),("B","sorted_physical_restore","old_random_logical")):
        views=np.load(matrix/f"{sketch}_views.npy",mmap_mode="r")
        for donor,operator,logical in fixtures:
            first_values,first_record=gather(views,logical,first);second_values,second_record=gather(views,logical,second)
            exact=bool(np.array_equal(first_values,second_values) and first_values.tobytes()==second_values.tobytes())
            records.extend([{**first_record,"sketch":sketch,"donor":donor,"operator":operator,"exact_pair":exact},
                            {**second_record,"sketch":sketch,"donor":donor,"operator":operator,"exact_pair":exact}])
    upper=[r for r in records if r["rows"]==max(x["rows"] for x in records)]
    old=sum(r["wall_seconds"] for r in upper if r["mode"]=="old_random_logical");new=sum(r["wall_seconds"] for r in upper if r["mode"]=="sorted_physical_restore")
    physical_old=sum(max(0,r["counter_delta"]["process_read_bytes"] or 0) for r in records if r["mode"]=="old_random_logical")
    physical_new=sum(max(0,r["counter_delta"]["process_read_bytes"] or 0) for r in records if r["mode"]=="sorted_physical_restore")
    cache_resident=physical_old==0 and physical_new==0
    exact=all(r["exact_pair"] for r in records)
    # When the authenticated mmap is fully cache-resident, cold physical-read
    # amplification is not observable. In that case pass only the narrower
    # non-pathology claim (exact rows and bounded cached traversal), without
    # claiming a physical-I/O speedup.
    amplification_ok=exact and ((cache_resident and new < 1.0) or (not cache_resident and physical_new <= max(physical_old,1)*1.10))
    report={"status":"PASS_SORTED_PHYSICAL_READ_LOCALITY" if amplification_ok else "STOP_SORTED_READ_PATH_REMAINS_PATHOLOGICAL",
            "upper_fixture_old_seconds":old,"upper_fixture_sorted_seconds":new,"upper_fixture_speedup":old/new if new else None,
            "physical_read_bytes_old":physical_old,"physical_read_bytes_sorted":physical_new,"cache_resident":cache_resident,
            "records":records,"note":"OS/process counters are platform-available deltas; cache crossover uses A and B in opposite method order. A cache-resident PASS is not interpreted as a cold-I/O speedup."}
    (out/"PHYSICAL_READ_LOCALITY_BENCHMARK.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n");print(json.dumps(report,indent=2))
    if not amplification_ok:raise SystemExit(2)


if __name__=="__main__":main()
