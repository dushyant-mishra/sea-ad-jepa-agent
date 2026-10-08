#!/usr/bin/env python3
"""Shared, read-only utilities for PROD41K_PIPELINE_PARALLELISM_AUDIT_V1."""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import psutil

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "exports" / "prod41k_parallelism_audit_v1"
T1 = ROOT / "exports" / "prod41k_teacher_t1_20260823"
sys.path.insert(0, str(ROOT / "exports" / "static_context_decomposition_v4_20260821"))
sys.path.insert(0, str(ROOT / "scripts" / "v4"))
from production_train_loader import ProductionTrainLoader  # noqa: E402
import stage81a3_prod41k_engineering_smoke as phase_e  # noqa: E402

SEED = 8_113_002
CPU_CAP = min(4, max(1, int((os.cpu_count() or 1) * 0.25)))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(8 << 20), b""):
            h.update(block)
    return h.hexdigest()


def atomic_json(path: Path, payload: object) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")
    tmp.replace(path)


def resource_snapshot() -> dict:
    vm = psutil.virtual_memory()
    active = []
    for proc in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            command = " ".join(proc.info["cmdline"] or [])
            if "foundation_expression_discovery.py" in command:
                active.append({"pid": proc.info["pid"], "name": proc.info["name"], "command": command})
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return {
        "physical_cpu_cores": psutil.cpu_count(logical=False),
        "logical_cpu_cores": psutil.cpu_count(logical=True),
        "audit_cpu_worker_cap": CPU_CAP,
        "cpu_cap_fraction_logical": CPU_CAP / (psutil.cpu_count(logical=True) or 1),
        "cpu_utilization_percent": psutil.cpu_percent(interval=0.5),
        "ram_total_bytes": vm.total,
        "ram_available_bytes": vm.available,
        "ram_percent_used": vm.percent,
        "corpus_discovery_active": bool(active),
        "corpus_discovery_processes": active,
        "data_paths": [str(ROOT / "data"), str(T1), str(OUT)],
    }


def load_inventory_and_schedule() -> tuple[pd.DataFrame, pd.DataFrame]:
    inv = pd.read_csv(T1 / "t1_encoder_fit_inventory.csv")
    inv.insert(0, "inventory_row", np.arange(len(inv), dtype=np.int64))
    schedule = pd.read_csv(T1 / "t1_training_schedule.csv")
    if inv.stable_mask_key.duplicated().any() or schedule.groupby("update").size().min() != 128:
        raise RuntimeError("frozen inventory/schedule integrity failure")
    return inv, schedule


def freeze_panel() -> pd.DataFrame:
    OUT.mkdir(parents=True, exist_ok=True)
    csv_path = OUT / "PARALLELISM_BENCHMARK_PANEL.csv"
    json_path = OUT / "PARALLELISM_BENCHMARK_PANEL.json"
    if csv_path.exists() and json_path.exists():
        panel = pd.read_csv(csv_path)
        frozen = json.loads(json_path.read_text(encoding="utf-8"))
        if frozen["panel_csv_sha256"] != sha256(csv_path):
            raise RuntimeError("benchmark panel hash drift")
        return panel
    inv, schedule = load_inventory_and_schedule()
    # Two lawful fit-donor cells per operator for I/O plus four exact scheduled updates.
    io = inv.sort_values(["operator_index", "accepted_inventory_row"], kind="stable").groupby("operator_index", sort=True).head(2).copy()
    io["panel_type"] = "all_operator_io"
    io["update"] = -1
    io["slot"] = io.groupby("operator_index").cumcount()
    scheduled = schedule.loc[schedule["update"].isin([1, 2, 3, 4])].sort_values(["update", "slot"], kind="stable").copy()
    scheduled = scheduled.merge(inv.drop(columns=[c for c in ["update", "slot"] if c in inv]), on="inventory_row", how="left", suffixes=("", "_inventory"), validate="many_to_one")
    scheduled["panel_type"] = "gpu_exact_schedule"
    common = sorted(set(io.columns) & set(scheduled.columns))
    panel = pd.concat([io[common], scheduled[common]], ignore_index=True)
    panel.insert(0, "logical_order", np.arange(len(panel), dtype=np.int64))
    panel.to_csv(csv_path, index=False)
    payload = {
        "schema": "prod41k-parallelism-panel-v1",
        "created_before_candidate_benchmarks": True,
        "selection_rule": "first two accepted fit-inventory rows per operator plus exact frozen updates 1-4",
        "rows": len(panel), "operators": int(panel.operator_index.nunique()),
        "scheduled_updates": [1, 2, 3, 4], "seed": SEED,
        "panel_csv_sha256": sha256(csv_path),
    }
    atomic_json(json_path, payload)
    return panel


def loader_rows(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy().reset_index(drop=True)
    out["loader_row"] = np.arange(len(out), dtype=np.int64)
    return out


def time_call(fn, repeats: int = 1):
    elapsed, result = [], None
    for _ in range(repeats):
        start = time.perf_counter(); result = fn(); elapsed.append(time.perf_counter() - start)
    return result, elapsed
