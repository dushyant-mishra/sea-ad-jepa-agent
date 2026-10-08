#!/usr/bin/env python3
"""Resource-derived batch-size benchmark for the engineering-only ALL executor."""
from __future__ import annotations

import argparse
import gc
import json
import math
import os
import resource
import shutil
import subprocess
import threading
import time
from pathlib import Path

import numpy as np
import pandas as pd
import psutil

import run_full104_refit_null_block_major_v1 as block


def resource_sampler(stop, record):
    process=psutil.Process(); peak=0; gpu=[]
    minimum_available=None; maximum_swap=0
    while not stop.is_set():
        peak=max(peak,process.memory_info().rss)
        memory=psutil.virtual_memory(); swap=psutil.swap_memory()
        minimum_available=memory.available if minimum_available is None else min(minimum_available,memory.available)
        maximum_swap=max(maximum_swap,swap.used)
        try:
            raw=subprocess.check_output(["nvidia-smi","--query-gpu=utilization.gpu","--format=csv,noheader,nounits"],text=True,timeout=2)
            gpu.append(float(raw.strip().splitlines()[0]))
        except Exception: pass
        stop.wait(0.25)
    record.update({"true_peak_rss_bytes":int(peak),"minimum_memavailable_bytes":int(minimum_available or 0),
                   "maximum_swap_used_bytes":int(maximum_swap),"mean_gpu_utilization_percent":float(np.mean(gpu)) if gpu else None,"max_gpu_utilization_percent":float(np.max(gpu)) if gpu else None})


def proc_io_read_bytes() -> int | None:
    try:
        for line in Path("/proc/self/io").read_text().splitlines():
            if line.startswith("read_bytes:"): return int(line.split(":",1)[1])
    except OSError: pass
    return None


def load_plan(directory: Path) -> pd.DataFrame:
    authority = json.loads((directory / "LOSSLESS_PLAN_AUTHORITY.json").read_text())
    if authority["plan_file_sha256"] != block.EXPECTED_ALL_PLAN_SHA256:
        raise RuntimeError("benchmark ALL plan mismatch")
    with np.load(directory / authority["plan_file"], allow_pickle=False) as z:
        return pd.DataFrame({name: z[name] for name in z.files})


def representative_plan(plan: pd.DataFrame) -> pd.DataFrame:
    groups = [(key, group) for key, group in plan.groupby(["donor_id", "operator_index"], sort=True)]
    sizes = np.asarray([len(group) for _, group in groups])
    chosen = set()
    for quantile in (0.0, 0.25, 0.5, 0.75, 0.9, 1.0):
        target = float(np.quantile(sizes, quantile))
        chosen.add(int(np.argmin(np.abs(sizes - target))))
    # Touch every donor accumulator while keeping the benchmark bounded.
    first_by_donor = {}
    for index, ((donor, _operator), _group) in enumerate(groups):
        first_by_donor.setdefault(str(donor), index)
    chosen.update(first_by_donor.values())
    largest = int(np.argmax(sizes))
    return pd.concat([groups[index][1] if index == largest else groups[index][1].head(256)
                      for index in sorted(chosen)], ignore_index=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--matrix", required=True)
    parser.add_argument("--plan-dir", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--candidates", default="1,8,32,64,128,256")
    parser.add_argument("--gold-report")
    args = parser.parse_args()
    out = Path(args.out).resolve(); out.mkdir(parents=True, exist_ok=False)
    matrix = Path(args.matrix).resolve(); plan = load_plan(Path(args.plan_dir).resolve())
    sample = representative_plan(plan); donors = sorted(plan.donor_id.astype(str).unique())
    views = np.load(matrix / "A_views.npy", mmap_mode="r")
    key = "engineering-throughput-benchmark-v1"
    candidates = [int(x) for x in args.candidates.split(",")]; records = []
    # One nonselecting warm pass removes first-touch page-cache privilege.
    warm,_,_=block.block_major_null_between_batch(views,sample,donors,"A",[255],key,args.device);del warm;gc.collect()
    for k in candidates:
        available = int(psutil.virtual_memory().available)
        accumulator = int(k * block.ACCUMULATOR_BYTES_PER_REPLICATE)
        largest_block = int(sample.groupby(["donor_id", "operator_index"]).size().max() * 4 * views.shape[-1] * 8)
        reserve = 4 * 1024**3
        safe = accumulator + largest_block + reserve <= available
        if not safe:
            records.append({"K": k, "status": "SKIPPED_MEMORY_UNSAFE", "available_bytes": available,
                            "accumulator_bytes": accumulator, "largest_float64_block_bytes": largest_block,
                            "required_including_reserve_bytes": accumulator + largest_block + reserve})
            continue
        before_swap = psutil.swap_memory(); process = psutil.Process(); io0 = process.io_counters(); proc_read0=proc_io_read_bytes(); rss0 = process.memory_info().rss
        faults0=resource.getrusage(resource.RUSAGE_SELF)
        between = np.empty((k, len(donors), views.shape[-1], views.shape[-1]), np.float64); between.fill(0.0)
        compensation = np.empty_like(between); compensation.fill(0.0)
        touched_rss = process.memory_info().rss
        import torch
        cuda_free_before=None;cuda_total=None
        if str(args.device).startswith("cuda"):
            torch.cuda.reset_peak_memory_stats(args.device);cuda_free_before,cuda_total=torch.cuda.mem_get_info(args.device)
        stop=threading.Event();sampled={};thread=threading.Thread(target=resource_sampler,args=(stop,sampled),daemon=True);thread.start();started = time.perf_counter()
        result, _maps, metrics = block.block_major_null_between_batch(
            views, sample, donors, "A", list(range(k)), key, args.device,
            between=between, compensation=compensation)
        elapsed = time.perf_counter() - started;stop.set();thread.join(); io1 = process.io_counters();proc_read1=proc_io_read_bytes(); after_swap = psutil.swap_memory();faults1=resource.getrusage(resource.RUSAGE_SELF)
        finite = bool(np.isfinite(result).all())
        snapshot_seconds=None;snapshot_bytes=None
        if after_swap.used <= before_swap.used:
            snap=out/f"snapshot_K{k}";identity=block.batch_identity("benchmark","benchmark","benchmark","A",list(range(k)),k,100,{"plan_sha256":"benchmark","plan_semantic_sha256":"benchmark"});identity["accumulator_shape"]=[k,len(donors),views.shape[-1],views.shape[-1]];maps={r:f"benchmark-map-{r}" for r in range(k)};snap_started=time.perf_counter();block.save_batch_checkpoint(snap,identity,100,between,compensation,maps);snapshot_seconds=time.perf_counter()-snap_started;snapshot_bytes=sum(p.stat().st_size for p in snap.rglob("*") if p.is_file());
            if snap.resolve().parent!=out.resolve():raise RuntimeError("unsafe benchmark snapshot cleanup")
            shutil.rmtree(snap)
        records.append({"K": k, "status": "PASS" if finite else "STOP_NONFINITE", "rows": int(len(sample)),
                        "strata": int(sample.groupby(["donor_id", "operator_index"]).ngroups),
                        "wall_seconds": elapsed, "replicates_per_second": k / elapsed,
                        "logical_bytes_read": int(metrics["logical_matrix_bytes_read"]),
                        "physical_read_bytes_delta": int(io1.read_bytes - io0.read_bytes),
                        "proc_physical_read_bytes_delta":None if proc_read0 is None or proc_read1 is None else int(proc_read1-proc_read0),
                        "minor_page_faults_delta":int(faults1.ru_minflt-faults0.ru_minflt),"major_page_faults_delta":int(faults1.ru_majflt-faults0.ru_majflt),
                        "rss_before_bytes": int(rss0), "rss_after_touch_bytes": int(touched_rss),
                        "rss_peak_proxy_bytes": int(process.memory_info().rss),
                        "swap_used_before_bytes": int(before_swap.used), "swap_used_after_bytes": int(after_swap.used),
                        "available_before_bytes": available, "accumulator_bytes": accumulator, "finite": finite,
                        "cuda_peak_allocated_bytes":int(torch.cuda.max_memory_allocated(args.device)) if str(args.device).startswith("cuda") else None,
                        "cuda_peak_reserved_bytes":int(torch.cuda.max_memory_reserved(args.device)) if str(args.device).startswith("cuda") else None,
                        "cuda_free_before_bytes":None if cuda_free_before is None else int(cuda_free_before),"cuda_total_bytes":None if cuda_total is None else int(cuda_total),
                        "snapshot_write_seconds":snapshot_seconds,"snapshot_bytes":snapshot_bytes,**sampled,**metrics})
        del result, between, compensation; gc.collect()
    passed = [r for r in records if r["status"] == "PASS" and r["swap_used_after_bytes"] <= r["swap_used_before_bytes"]]
    if not passed:
        status, selected = "STOP_NO_SAFE_BATCH_SIZE", None
    else:
        best = max(passed, key=lambda r: r["replicates_per_second"])
        selected = int(best["K"]); status = "PASS_BLOCK_MAJOR_BATCH_SIZE_DERIVED"
    selected_record=next((r for r in records if r.get("K")==selected),None);full_rows=4553407;full_strata=1400
    projected_batch_seconds=None;cadence=None;cadence_rows=[]
    if selected_record:
        projected_batch_seconds=selected_record["wall_seconds"]*full_rows/selected_record["rows"]
        for interval in (100,200,350,700,1400):
            snapshots=max(0,int(np.ceil(full_strata/interval))-1);io_seconds=snapshots*selected_record["snapshot_write_seconds"];io_pct=100*io_seconds/(projected_batch_seconds+io_seconds);lost=projected_batch_seconds*interval/full_strata;eligible=io_pct<=5 and lost<=7200
            cadence_rows.append({"interval_strata":interval,"projected_snapshot_count":snapshots,"projected_checkpoint_io_percent":io_pct,"maximum_lost_work_seconds":lost,"eligible":eligible})
        eligible=[x for x in cadence_rows if x["eligible"]];cadence=min(eligible,key=lambda x:x["maximum_lost_work_seconds"])["interval_strata"] if eligible else None
        if cadence is None:status="STOP_NO_ACCEPTABLE_CHECKPOINT_CADENCE"
    projection={}
    if selected_record and args.gold_report:
        gold=json.loads(Path(args.gold_report).read_text());gm=gold["executor_metrics"];k=selected
        fixed=float(gm["T_read_seconds"]+gm["T_host_restore_seconds"]+gm["T_host_to_device_seconds"])
        per_rep=float(gm["T_null_compute_seconds"]+gm["T_finalize_seconds"])
        snapshot=float(selected_record.get("snapshot_write_seconds") or 0.0)
        a_passes=math.ceil(256/k);b_passes=math.ceil(256/k);total_passes=a_passes+b_passes
        projected_seconds=total_passes*(fixed+k*per_rep+snapshot)
        projection={"K_selected_WSL":k,"number_of_A_passes":a_passes,"number_of_B_passes":b_passes,
                    "measured_replicates_per_hour":float(selected_record["replicates_per_second"]*3600),
                    "projected_ALL_wall_seconds":projected_seconds,"projected_ALL_wall_hours":projected_seconds/3600,
                    "projection_basis":"measured FULL104 WSL K1 fixed/per-replicate phases plus selected-K WSL snapshot cost",
                    "effective_matrix_passes_total":total_passes,"effective_matrix_passes_per_replicate":1/k}
    report = {"status": status, "selected_K": selected, "selected_checkpoint_every_strata":cadence,
              "selection_rule": "highest measured replicates_per_second among memory-safe candidates with no swap-use increase after common warm pass",
              "checkpoint_rule":"smallest lost-work interval with projected checkpoint I/O <=5% and maximum lost work <=2 hours",
              "projected_selected_batch_seconds":projected_batch_seconds,"checkpoint_candidates":cadence_rows,
              "projection":projection,"candidates": records}
    (out / "BLOCK_MAJOR_BATCH_BENCHMARK.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2))
    if selected is None: raise SystemExit(2)


if __name__ == "__main__":
    main()
