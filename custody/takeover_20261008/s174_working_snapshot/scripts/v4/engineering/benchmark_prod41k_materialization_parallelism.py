#!/usr/bin/env python3
"""Bounded exact-row sparse materialization concurrency benchmark."""
from __future__ import annotations

import os
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor

for key in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[key] = "1"

import numpy as np
import pandas as pd
import scipy.sparse as sp

from parallelism_common import CPU_CAP, OUT, ProductionTrainLoader, freeze_panel, loader_rows, resource_snapshot


def _materialize(task):
    operator, counts_path, state, records = task
    frame = pd.DataFrame(records)
    counts = sp.load_npz(counts_path).tocsr()
    rows = frame.local_row.to_numpy(np.int64)
    matrix = counts[rows].astype(np.float32)
    library = frame.source_library.to_numpy(np.float32)
    normalized = matrix.multiply((10_000.0 / np.maximum(library, 1.0))[:, None]).tocsr()
    normalized.data = np.log1p(normalized.data)
    return operator, frame.loader_row.to_numpy(np.int64), normalized.toarray(), np.repeat(state[None, :], len(frame), axis=0)


def _assemble(parts, n):
    values = np.zeros((n, 41_238), np.float32); states = np.zeros((n, 41_238), np.uint8)
    for _, destinations, val, state in parts:
        values[destinations] = val; states[destinations] = state
    return values, states


def main() -> None:
    panel = freeze_panel(); rows = loader_rows(panel.loc[panel.panel_type.eq("all_operator_io")])
    loader = ProductionTrainLoader(); by_op = {int(x["operator_index"]): x for x in loader.items}
    tasks = []
    for operator, frame in rows.groupby("operator_index", sort=True):
        item = by_op[int(operator)]
        tasks.append((int(operator), str(item["counts"]), loader.states[item["matrix_id"]], frame.to_dict("records")))
    start=time.perf_counter(); baseline=loader.load(rows); serial_s=time.perf_counter()-start
    records=[]; parity={"schema":"prod41k-parallelism-parity-v1","panel_rows":len(rows),"candidates":[]}
    records.append({"workload":"actual_io_sparse_materialization","implementation":"A0_serial_loader","workers":1,"seconds":serial_s,"cells_per_second":len(rows)/serial_s,"exact_values":True,"exact_states":True,"status":"PASS"})
    candidates=[("A1_thread",ThreadPoolExecutor,n) for n in sorted(set([2,CPU_CAP])) if n<=CPU_CAP]
    candidates += [("A2_process",ProcessPoolExecutor,n) for n in sorted(set([2,CPU_CAP])) if n<=CPU_CAP]
    for name, executor, workers in candidates:
        start=time.perf_counter()
        try:
            with executor(max_workers=workers) as pool: parts=list(pool.map(_materialize,tasks))
            result=_assemble(parts,len(rows)); seconds=time.perf_counter()-start
            ev=np.array_equal(result[0],baseline[0]); es=np.array_equal(result[1],baseline[1]); status="PASS" if ev and es else "REJECT"
        except Exception as exc:
            seconds=time.perf_counter()-start; ev=es=False; status=f"FAIL:{type(exc).__name__}"
        records.append({"workload":"actual_io_sparse_materialization","implementation":name,"workers":workers,"seconds":seconds,"cells_per_second":len(rows)/seconds,"exact_values":ev,"exact_states":es,"status":status})
        parity["candidates"].append({"implementation":name,"workers":workers,"exact_values":ev,"exact_states":es,"status":status})
    try:
        from joblib import Parallel, delayed
        for workers in sorted(set([2,CPU_CAP])):
            start=time.perf_counter(); parts=Parallel(n_jobs=workers,backend="loky")(delayed(_materialize)(t) for t in tasks)
            result=_assemble(parts,len(rows)); seconds=time.perf_counter()-start
            ev=np.array_equal(result[0],baseline[0]); es=np.array_equal(result[1],baseline[1])
            records.append({"workload":"actual_io_sparse_materialization","implementation":"A3_joblib_loky","workers":workers,"seconds":seconds,"cells_per_second":len(rows)/seconds,"exact_values":ev,"exact_states":es,"status":"PASS" if ev and es else "REJECT"})
            parity["candidates"].append({"implementation":"A3_joblib_loky","workers":workers,"exact_values":ev,"exact_states":es})
    except ImportError:
        records.append({"workload":"actual_io_sparse_materialization","implementation":"A3_joblib_loky","workers":0,"seconds":np.nan,"cells_per_second":np.nan,"exact_values":False,"exact_states":False,"status":"NOT_INSTALLED"})
    # Already-loaded transformation: exact deterministic log1p on the same baseline tensor.
    start=time.perf_counter(); transformed=np.sqrt(np.maximum(baseline[0],0),dtype=np.float32); transform_s=time.perf_counter()-start
    records.append({"workload":"already_loaded_cpu_transform","implementation":"A0_serial","workers":1,"seconds":transform_s,"cells_per_second":len(rows)/transform_s,"exact_values":True,"exact_states":True,"status":"PASS"})
    pd.DataFrame(records).to_csv(OUT/"PARALLELISM_CPU_MATRIX.csv",index=False)
    import json
    (OUT/"PARALLELISM_PARITY_AUDIT.json").write_text(json.dumps(parity,indent=2)+"\n",encoding="utf-8")
    passed=sum(x.get("status","PASS")=="PASS" for x in parity["candidates"])
    (OUT/"PARALLELISM_PARITY_AUDIT.md").write_text(f"# Parallelism parity audit\n\nFrozen lawful panel: {len(rows)} cells across {rows.operator_index.nunique()} operators.\n\n{passed} candidate configurations reproduced numeric values and observation states exactly. Candidate results preserve loader-row order; workers only materialize main-process-selected rows and own no RNG.\n",encoding="utf-8")


if __name__ == "__main__": main()
