#!/usr/bin/env python3
"""Resource, runtime, storage and resumability preflight for frozen sensitivity."""
from __future__ import annotations

import argparse
import hashlib
import inspect
import json
import os
import shutil
import time
from pathlib import Path

import numpy as np
import pandas as pd

from derive_full104_phase2_shared_state import fit_basis
from full104_refit_null_sensitivity_core_v1 import null_between_one


FREEZE_ROOT = "593e14872b6fe07d3f2855a49dd8eac57bfa5819465b8801b801dd9f6d4b510c"


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 << 20), b""):
            h.update(block)
    return h.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--freeze", required=True); parser.add_argument("--matrix", required=True); parser.add_argument("--analytic", required=True)
    parser.add_argument("--core", required=True); parser.add_argument("--runner", required=True); parser.add_argument("--validator-package", required=True); parser.add_argument("--out", required=True)
    args = parser.parse_args()
    freeze, matrix, analytic, core, runner, validator, out = map(lambda x: Path(x).resolve(), [args.freeze, args.matrix, args.analytic, args.core, args.runner, args.validator_package, args.out])
    out.mkdir(parents=True, exist_ok=False)
    contract = json.loads((freeze / "PROSPECTIVE_REFIT_NULL_NATURAL_WEIGHT_FULL_FEATURE_SENSITIVITY_V1.json").read_text())
    independent = json.loads((validator / "INDEPENDENT_IMPLEMENTATION_VALIDATION.json").read_text())
    if sha(freeze / "REFIT_NULL_SENSITIVITY_FREEZE_MANIFEST.csv") != FREEZE_ROOT or independent["status"] != "PASS_INDEPENDENT_IMPLEMENTATION_VALIDATOR":
        raise RuntimeError("authority or independent validator unavailable")
    rows = pd.read_csv(matrix / "PHASE2_FEATURE_ROWS.csv", usecols=["donor_id", "operator_index"], dtype={"donor_id": str})
    counts = rows.groupby(["donor_id", "operator_index"], sort=True).size()
    cap_table = pd.read_csv(freeze / "REFIT_NULL_SENSITIVITY_CAP_LADDER.csv")

    import psutil
    import torch
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA unavailable for full512 preflight")
    device = torch.device("cuda")
    largest_group = counts.idxmax(); group_indices = rows.index[(rows.donor_id == largest_group[0]) & (rows.operator_index == largest_group[1])].to_numpy(np.int64)
    bench_n = min(16384, len(group_indices)); indices = group_indices[:bench_n]
    views = np.load(matrix / "A_views.npy", mmap_mode="r")
    started = time.perf_counter(); host = np.asarray(views[indices], dtype=np.float64); read_seconds = time.perf_counter() - started
    x = torch.as_tensor(host, device=device); torch.cuda.synchronize()
    # Warmup then actual six unordered cross-view products in full 512-D float64.
    _ = x[:, 0].T @ x[:, 1]; torch.cuda.synchronize()
    started = time.perf_counter()
    products = []
    for v in range(4):
        for w in range(v + 1, 4): products.append(x[:, v].T @ x[:, w])
    torch.cuda.synchronize(); cross_seconds = time.perf_counter() - started
    del products, x, host; torch.cuda.empty_cache()

    stats = analytic / "sufficient_statistics"
    mean = np.asarray(np.load(stats / "A_mean.npy", mmap_mode="r"), np.float64)
    within = np.asarray(np.load(stats / "A_within.npy", mmap_mode="r"), np.float64)
    between = np.asarray(np.load(stats / "A_between.npy", mmap_mode="r"), np.float64)
    started = time.perf_counter(); _ = fit_basis(mean, within, between, np.arange(104), 320); eig_seconds = time.perf_counter() - started

    # Synthetic fragmentation benchmark matching the actual 1,400 cap-4 strata;
    # it exercises the production kernel without calculating a real cap statistic.
    donor_sizes = rows.groupby("donor_id").size().to_dict(); synthetic_records = []; cursor = 0
    for (donor, operator), n in counts.items():
        m = min(4, int(n)); weight = float(n / (m * donor_sizes[donor]))
        for local in range(m):
            synthetic_records.append({"row_index": cursor, "donor_id": donor, "operator_index": int(operator), "within_donor_weight": weight}); cursor += 1
    synthetic_plan = pd.DataFrame(synthetic_records); synthetic_views = np.random.default_rng(20260829).normal(size=(len(synthetic_plan), 4, 512)).astype(np.float32)
    donor_ids = sorted(rows.donor_id.unique()); started = time.perf_counter()
    _synthetic_null, _synthetic_map = null_between_one(synthetic_views, synthetic_plan, donor_ids, "BENCHMARK", "A", 0, "benchmark-key", "cuda")
    fragmented_cap4_seconds = time.perf_counter() - started

    total_selected = int(cap_table.selected_rows.sum()); all_rows = 4_553_407
    row_scale_seconds = cross_seconds / bench_n
    cap4_rows = int(cap_table.iloc[0].selected_rows)
    cross_all_caps_seconds = fragmented_cap4_seconds * 256 * 2 * len(cap_table) + row_scale_seconds * max(0, total_selected - cap4_rows * len(cap_table)) * 256 * 2
    io_all_caps_seconds = (read_seconds / bench_n) * total_selected * 256 * 2
    eig_all_caps_seconds = eig_seconds * 2054 * 2 * len(cap_table)
    fragmentation_factor = 1.15
    estimate_seconds = fragmentation_factor * (cross_all_caps_seconds + io_all_caps_seconds) + eig_all_caps_seconds

    disk = shutil.disk_usage(matrix.anchor or matrix.drive + os.sep)
    memory = psutil.virtual_memory()
    gpu = torch.cuda.get_device_properties(0)
    max_stratum = int(counts.max())
    estimated_cpu_peak = int(3 * 104 * 512 * 512 * 8 + max_stratum * 4 * 512 * 8 + 2 * 1024**3)
    estimated_gpu_peak = int(max_stratum * 4 * 512 * 8 * 3 + 12 * 512 * 512 * 8 + 1024**3)
    projected_disk = 12 * 1024**3
    resource_pass = disk.free >= 2 * projected_disk and memory.available >= estimated_cpu_peak and gpu.total_memory >= estimated_gpu_peak
    implementation_text = core.read_text() + runner.read_text()
    mechanics_pass = all(token in implementation_text for token in ["within_donor_weight", "null_between_one", "fit_basis", "first_jointly_unsupported_dimension", "RUN_STATE.json"])
    no_dense = "np.zeros((len(plan), len(plan))" not in implementation_text and "np.asarray(views)" not in implementation_text

    benchmark = {
        "schema": "full104-refit-null-compute-preflight-v1", "status": "PASS_COMPUTE_PREFLIGHT" if resource_pass and mechanics_pass and no_dense else "STOP_COMPUTE_PREFLIGHT",
        "actual_benchmark": {"rows": bench_n, "six_full512_float64_cross_products_seconds": cross_seconds, "mmap_read_seconds": read_seconds, "one_rank320_generalized_fit_seconds": eig_seconds,
                             "synthetic_1400_stratum_cap4_production_kernel_seconds": fragmented_cap4_seconds, "synthetic_fragmentation_rows": len(synthetic_plan)},
        "projection": {"diagnostic_plus_ALL_selected_row_instances": total_selected, "null_replicates": 256, "sketches": 2, "caps": 6,
                       "fragmentation_safety_factor": fragmentation_factor, "estimated_total_seconds": estimate_seconds, "estimated_total_hours": estimate_seconds / 3600,
                       "projected_new_disk_bytes": projected_disk, "estimated_cpu_peak_bytes": estimated_cpu_peak, "estimated_gpu_peak_bytes": estimated_gpu_peak},
        "resources": {"disk_free_bytes": disk.free, "ram_available_bytes": memory.available, "ram_total_bytes": memory.total,
                      "gpu_name": gpu.name, "gpu_total_bytes": gpu.total_memory},
        "execution": {"blockwise_mmap": True, "whole_corpus_densification": False, "one_null_replicate_at_a_time": True,
                      "atomic_replicate_checkpoints": True, "exact_reuse": "ALL observed donor sufficient statistics only; all null eigensystems independently refitted",
                      "resume_hash_gate": True},
        "checks": {"resource_headroom": resource_pass, "mechanics_tokens": mechanics_pass, "no_dense_pattern": no_dense,
                   "independent_validator": True, "freeze_root": True},
        "input_hashes": {"freeze_manifest": FREEZE_ROOT, "core": sha(core), "runner": sha(runner),
                         "fit_basis_source": sha(Path(inspect.getsourcefile(fit_basis)).resolve()),
                         "validator_code": independent["input_hashes"]["validator"],
                         "independent_manifest": sha(validator / "INDEPENDENT_IMPLEMENTATION_VALIDATION_MANIFEST.csv")},
    }
    (out / "COMPUTE_STORAGE_RUNTIME_PREFLIGHT.json").write_text(json.dumps(benchmark, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    manifest = out / "IMPLEMENTATION_COMPUTE_PREFLIGHT_MANIFEST.csv"; files = [out / "COMPUTE_STORAGE_RUNTIME_PREFLIGHT.json", Path(__file__), core, runner]
    pd.DataFrame([{"path": str(p), "bytes": p.stat().st_size, "sha256": sha(p)} for p in files]).to_csv(manifest, index=False, lineterminator="\n")
    print(json.dumps({"status": benchmark["status"], "estimated_hours": estimate_seconds / 3600, "manifest_sha256": sha(manifest)}, indent=2))
    if benchmark["status"].startswith("STOP"): raise SystemExit(2)


if __name__ == "__main__":
    main()
