#!/usr/bin/env python3
"""Deterministic CPU evaluation/bootstrap orchestration microbenchmark."""
from __future__ import annotations
import os
for key in ("OMP_NUM_THREADS","MKL_NUM_THREADS","OPENBLAS_NUM_THREADS","NUMEXPR_NUM_THREADS"): os.environ[key]="1"
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/"exports"/"prod41k_parallelism_audit_v1"
SEED=8_113_002
CPU_CAP=min(4,max(1,int((os.cpu_count() or 1)*0.25)))


def one(task):
    index,seed,x,y=task; rng=np.random.default_rng(seed); sample=rng.integers(0,len(y),size=len(y)); xs=x[sample]; ys=y[sample]
    coef=np.linalg.solve(xs.T@xs+np.eye(xs.shape[1],dtype=np.float64)*1e-3,xs.T@ys)
    return index,seed,sample,coef


def main():
    rng=np.random.default_rng(SEED); x=rng.normal(size=(256,32)); y=rng.normal(size=256); seeds=[SEED+10_000+i for i in range(24)]; tasks=[(i,s,x,y) for i,s in enumerate(seeds)]
    start=time.perf_counter(); serial=[one(t) for t in tasks]; serial_s=time.perf_counter()-start; records=[{"implementation":"serial","workers":1,"seconds":serial_s,"draws_per_second":len(tasks)/serial_s,"exact_samples":True,"exact_results":True,"status":"PASS"}]
    for workers in sorted(set([2,CPU_CAP])):
        start=time.perf_counter()
        with ProcessPoolExecutor(max_workers=workers) as pool: result=list(pool.map(one,tasks))
        seconds=time.perf_counter()-start; exact_samples=all(np.array_equal(a[2],b[2]) for a,b in zip(serial,result)); exact_results=all(np.array_equal(a[3],b[3]) for a,b in zip(serial,result))
        records.append({"implementation":"ProcessPoolExecutor","workers":workers,"seconds":seconds,"draws_per_second":len(tasks)/seconds,"exact_samples":exact_samples,"exact_results":exact_results,"status":"PASS" if exact_samples and exact_results else "REJECT"})
    try:
        from joblib import Parallel,delayed
        workers=min(2,CPU_CAP); start=time.perf_counter(); result=Parallel(n_jobs=workers,backend="loky")(delayed(one)(t) for t in tasks); seconds=time.perf_counter()-start
        es=all(np.array_equal(a[2],b[2]) for a,b in zip(serial,result)); er=all(np.array_equal(a[3],b[3]) for a,b in zip(serial,result)); records.append({"implementation":"joblib_loky","workers":workers,"seconds":seconds,"draws_per_second":len(tasks)/seconds,"exact_samples":es,"exact_results":er,"status":"PASS" if es and er else "REJECT"})
    except ImportError: pass
    pd.DataFrame(records).to_csv(OUT/"PARALLELISM_EVALUATION_MATRIX.csv",index=False)

if __name__=="__main__": main()
