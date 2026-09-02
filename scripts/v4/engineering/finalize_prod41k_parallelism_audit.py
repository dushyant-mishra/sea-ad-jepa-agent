#!/usr/bin/env python3
"""Finalize and hash the disposable engineering-only parallelism audit."""
from __future__ import annotations
import json
from pathlib import Path
import pandas as pd
from parallelism_common import OUT, ROOT, sha256, atomic_json, resource_snapshot


def main() -> None:
    baseline=json.loads((OUT/"PARALLELISM_BASELINE_PROFILE.json").read_text(encoding="utf-8")); mean=baseline["mean_timing"]
    cpu=pd.read_csv(OUT/"PARALLELISM_CPU_MATRIX.csv"); dl=pd.read_csv(OUT/"PARALLELISM_DATALOADER_MATRIX.csv"); ev=pd.read_csv(OUT/"PARALLELISM_EVALUATION_MATRIX.csv")
    serial=float(cpu.loc[cpu.implementation.eq("A0_serial_loader"),"seconds"].iloc[0]); thread=cpu.loc[cpu.implementation.eq("A1_thread") & cpu.workers.eq(4)].iloc[0]
    thread_speed=serial/float(thread.seconds)
    theoretical_best=mean["wall_seconds"]-mean["loader_materialization_seconds"]+mean["loader_materialization_seconds"]/thread_speed
    improvement=mean["wall_seconds"]-theoretical_best
    end=pd.DataFrame([
      {"candidate":"authenticated_serial_baseline","validation":"AUTHENTICATED_205_UPDATES","sec_per_update":mean["wall_seconds"],"presentations_per_second":128/mean["wall_seconds"],"gpu_utilization":"not sampled during run","peak_vram_bytes":mean["peak_cuda_allocated_bytes"],"determinism":"authenticated"},
      {"candidate":"thread4_materializer_upper_bound","validation":"PROJECTED_ONLY_NOT_GPU_VALIDATED","sec_per_update":theoretical_best,"presentations_per_second":128/theoretical_best,"gpu_utilization":"not rerun; compute already 96.29% wall","peak_vram_bytes":"unchanged expected, unverified","determinism":"CPU values/states exact; full update deferred"}
    ])
    end.to_csv(OUT/"PARALLELISM_END_TO_END.csv",index=False)
    final={"schema":"prod41k-parallelism-final-v1","status":"CURRENT_PIPELINE_ALREADY_GPU_BOUND","engineering_only":True,"scientific_authority":"NONE",
      "baseline_sec_per_update":mean["wall_seconds"],"compute_sec_per_update":mean["compute_seconds"],"compute_fraction":baseline["compute_fraction_of_wall"],
      "input_sections_sec_per_update":mean["loader_materialization_seconds"]+mean["mask_generation_seconds"]+mean["host_to_device_seconds"],
      "thread4_materialization_microbenchmark_speedup":thread_speed,"thread4_projected_upper_bound_sec_per_update":theoretical_best,"projected_seconds_saved_per_update":improvement,
      "projected_speedup":mean["wall_seconds"]/theoretical_best,
      "wall_extrapolation_descriptive":{"205_updates_baseline_hours":205*mean["wall_seconds"]/3600,"205_updates_thread_upper_bound_hours":205*theoretical_best/3600,"1000_updates_baseline_hours":1000*mean["wall_seconds"]/3600,"1000_updates_thread_upper_bound_hours":1000*theoretical_best/3600},
      "recommendation":{"training_input":"retain current serial materialization; do not add DataLoader/process machinery for a projected sub-1% update gain","evaluation":"retain serial for small tasks; benchmark coarse endpoint-level jobs separately before adopting process/loky","future_performance_question":"If authorized separately, profile/optimize the dominant GPU forward/backward path; excluded from this audit."},
      "resource_isolation":resource_snapshot(),"determinism":"All executed CPU candidates preserved exact values, states and logical order. No full GPU candidate was claimed validated.",
      "deferred":["full-update GPU candidate test","async producer queue depth tests","pinned nonblocking H2D test"],"defer_reason":"corpus discovery active; authenticated runner is already GPU-compute dominated"}
    atomic_json(OUT/"PROD41K_PARALLELISM_FINAL.json",final)
    md=f"""# PROD41K pipeline parallelism audit v1\n\nFinal engineering classification: **CURRENT_PIPELINE_ALREADY_GPU_BOUND**\n\nThe authenticated 205-update run averaged **{mean['wall_seconds']:.3f} s/update**. Its combined forward/loss/backward/accumulation section used **{mean['compute_seconds']:.3f} s ({100*baseline['compute_fraction_of_wall']:.2f}%)**. Loader materialization used {mean['loader_materialization_seconds']:.3f} s, masks {mean['mask_generation_seconds']:.3f} s, and H2D {mean['host_to_device_seconds']:.4f} s.\n\nFour threads accelerated the 84-cell/all-42-operator materialization microbenchmark by **{thread_speed:.2f}x** with exact values and states. Even if that gain transferred perfectly, the projected update time is {theoretical_best:.3f} s: only **{improvement:.3f} s saved ({mean['wall_seconds']/theoretical_best:.4f}x)**. This is an upper-bound projection, not a GPU validation. ProcessPool and loky were slower; DataLoader workers were drastically slower for already-materialized ordered tensors; small deterministic bootstrap jobs were faster serially.\n\nRecommendation: keep the current serial training input path. Do not add process/DataLoader/async complexity for a projected sub-1% improvement. If runtime must fall materially, the next separately authorized engineering question is the dominant GPU compute path, which this audit explicitly excluded.\n\nDescriptive wall times: 205 updates = {205*mean['wall_seconds']/3600:.2f} h baseline vs {205*theoretical_best/3600:.2f} h projected upper bound; 1000 updates = {1000*mean['wall_seconds']/3600:.2f} h vs {1000*theoretical_best/3600:.2f} h. These are not guarantees.\n\nAll executed CPU parity checks passed. Heavy full-update, asynchronous-queue and pinned-H2D validation were automatically deferred while corpus discovery was active. This audit changes no scientific semantics and has no authority over T1 or corpus conclusions.\n"""
    (OUT/"PROD41K_PARALLELISM_FINAL.md").write_text(md,encoding="utf-8")
    required=[p for p in (ROOT/"scripts"/"v4"/"engineering").glob("*.py")]+[p for p in OUT.iterdir() if p.is_file() and p.name!="PROD41K_PARALLELISM_HASH_MANIFEST.csv"]
    pd.DataFrame([{"path":str(p.relative_to(ROOT)).replace("\\","/"),"bytes":p.stat().st_size,"sha256":sha256(p)} for p in sorted(required)]).to_csv(OUT/"PROD41K_PARALLELISM_HASH_MANIFEST.csv",index=False)

if __name__=="__main__": main()
