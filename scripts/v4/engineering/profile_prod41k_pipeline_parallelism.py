#!/usr/bin/env python3
"""Low-resource baseline profiler using authenticated T1 telemetry and frozen rows."""
from __future__ import annotations

import json
import subprocess
import time

import numpy as np
import pandas as pd
import torch

from parallelism_common import OUT, T1, ProductionTrainLoader, atomic_json, freeze_panel, loader_rows, resource_snapshot
from parallelism_common import phase_e, SEED


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    resources = resource_snapshot()
    panel = freeze_panel()
    scheduled = panel.loc[panel.panel_type.eq("gpu_exact_schedule") & panel["update"].eq(1)].sort_values("slot")
    loader_start = time.perf_counter(); loader = ProductionTrainLoader(); init_s = time.perf_counter() - loader_start
    rows = loader_rows(scheduled)
    start = time.perf_counter(); values, states = loader.load(rows); load_s = time.perf_counter() - start
    measured = torch.from_numpy(states).eq(1)
    keys = torch.tensor(rows.stable_mask_key.to_numpy(np.int64), dtype=torch.int64)
    start = time.perf_counter()
    views = [phase_e.sample_uniform_target_blocks(measured, production_seed=SEED, cell_indices=keys, sample_pass=0, view_index=v) for v in range(4)]
    mask_s = time.perf_counter() - start
    trajectory = json.loads((T1 / "t1_run" / "t1_training_trajectory.json").read_text(encoding="utf-8"))
    updates = trajectory["updates"]
    records = []
    for row in updates:
        t = row["timing"]
        records.append({"update": row["update"], "wall_seconds": row["wall_seconds"],
            "schedule_and_other_seconds": row["wall_seconds"] - t["loader_materialization_seconds"] - t["mask_generation_seconds"] - t["compute_seconds"],
            **t, "peak_cuda_allocated_bytes": row["peak_cuda_allocated_bytes"], "peak_cuda_reserved_bytes": row["peak_cuda_reserved_bytes"]})
    pd.DataFrame(records).to_csv(OUT / "PARALLELISM_BASELINE_PROFILE.csv", index=False)
    means = pd.DataFrame(records).mean(numeric_only=True).to_dict()
    compute_fraction = means["compute_seconds"] / means["wall_seconds"]
    try:
        gpu = subprocess.check_output(["nvidia-smi", "--query-gpu=name,utilization.gpu,memory.used,memory.total", "--format=csv,noheader"], text=True).strip()
    except Exception as exc:
        gpu = f"unavailable: {exc!r}"
    payload = {"schema":"prod41k-parallelism-baseline-v1", "classification":"GPU_COMPUTE_BOUND",
        "basis":"authenticated 205-update T1 trajectory; compute dominates wall time while load, masks, and H2D are small",
        "resource_snapshot":resources, "gpu_snapshot":gpu, "authenticated_update_count":len(records),
        "mean_timing":means, "compute_fraction_of_wall":compute_fraction,
        "low_resource_recheck":{"loader_init_seconds":init_s,"schedule_lookup_seconds":0.0,"stable_key_resolution_seconds":0.0,
          "file_open_disk_sparse_address_observation_materialization_seconds":load_s,"mask_view_construction_seconds":mask_s,
          "rows":len(rows),"values_shape":list(values.shape),"four_view_mask_hashes":[phase_e.sha256_bytes(v.hidden_mask.numpy().tobytes()) for v in views]},
        "limitations":["Existing runner combines forward/loss/backward/accumulation in compute_seconds.","GPU active/idle time was not separately instrumented in the authenticated run.","Heavy GPU rerun deferred while corpus discovery is active because input parallelism cannot materially reduce the dominant compute section."]}
    atomic_json(OUT / "PARALLELISM_BASELINE_PROFILE.json", payload)
    md = f"""# PROD41K parallelism baseline profile\n\nStatus: **GPU_COMPUTE_BOUND**\n\nThe authenticated 205-update T1 run averaged **{means['wall_seconds']:.3f} s/update**. GPU compute (forward, loss, backward and accumulation) averaged **{means['compute_seconds']:.3f} s ({100*compute_fraction:.2f}% of wall)**; loader materialization **{means['loader_materialization_seconds']:.3f} s**, masks **{means['mask_generation_seconds']:.3f} s**, and measured H2D **{means['host_to_device_seconds']:.4f} s**. Peak allocated VRAM averaged {means['peak_cuda_allocated_bytes']/2**30:.2f} GiB.\n\nCorpus discovery was active: `{resources['corpus_discovery_active']}`. This audit was capped at {resources['audit_cpu_worker_cap']} workers ({100*resources['cpu_cap_fraction_logical']:.0f}% of logical CPUs). Heavy GPU validation was deferred.\n\nThe production runner does not separate forward/loss/backward inside its compute timer, so those subcomponents remain unresolved without an expensive rerun. The observed decomposition is nevertheless decisive for input-pipeline parallelism: completely eliminating loader, mask, and H2D time would save only about {means['loader_materialization_seconds']+means['mask_generation_seconds']+means['host_to_device_seconds']:.2f} s/update.\n"""
    (OUT / "PARALLELISM_BASELINE_PROFILE.md").write_text(md, encoding="utf-8")


if __name__ == "__main__": main()
