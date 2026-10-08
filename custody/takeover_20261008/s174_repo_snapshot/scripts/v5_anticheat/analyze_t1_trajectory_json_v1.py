#!/usr/bin/env python3
"""Analyze a prod41k T1 trajectory JSON without promoting it to authority.

The script records loss/aggregate-gradient facts and the key limitation: aggregate
component norms cannot prove the frozen 48 protected attention-routing tensors
were live elementwise or that their Adam moments moved.
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path
from statistics import median

KEY_UPDATES = (1, 10, 25, 40, 50, 100, 150, 200, 205)


def pct_reduction(start: float, end: float) -> float:
    return (start - end) / start if start else 0.0


def analyze(path: Path, out_dir: Path) -> dict:
    payload = path.read_bytes()
    data = json.loads(payload.decode("utf-8"))
    updates = data.get("updates")
    if data.get("schema") != "prod41k-t1-trajectory-v2":
        raise RuntimeError(f"unexpected schema: {data.get('schema')}")
    if not isinstance(updates, list) or len(updates) != 205:
        raise RuntimeError("trajectory must contain exactly 205 updates")
    if [u.get("update") for u in updates] != list(range(1, 206)):
        raise RuntimeError("trajectory updates must be exactly 1..205")

    components = tuple(updates[0]["gradient_components"].keys())
    losses = [float(u["loss"]) for u in updates]
    missing_total = 0
    nonfinite_total = 0
    component_stats = {}
    for comp in components:
        vals = [float(u["gradient_components"][comp]["l2_norm"]) for u in updates]
        component_stats[comp] = {
            "first_l2_norm": vals[0],
            "last_l2_norm": vals[-1],
            "last_over_first": vals[-1] / vals[0] if vals[0] else 0.0,
            "min_l2_norm": min(vals),
            "max_l2_norm": max(vals),
            "median_l2_norm": float(median(vals)),
        }
        for u in updates:
            rec = u["gradient_components"][comp]
            missing_total += int(rec.get("missing_parameter_tensors", 0))
            nonfinite_total += int(rec.get("nonfinite_parameter_tensors", 0))

    by_update = {int(u["update"]): u for u in updates}
    out_dir.mkdir(parents=True, exist_ok=True)
    with (out_dir / "T1_TRAJECTORY_LOSS_GRADIENT_SUMMARY_V1.csv").open("w", newline="", encoding="utf-8") as f:
        fields = ["update", "loss", "ema_updates", "wall_seconds", "peak_cuda_allocated_bytes", "peak_cuda_reserved_bytes"] + [f"{c}_l2_norm" for c in components]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for update in KEY_UPDATES:
            rec = by_update[update]
            row = {"update": update, "loss": float(rec["loss"]), "ema_updates": int(rec.get("ema_updates", -1)), "wall_seconds": float(rec.get("wall_seconds", 0.0)), "peak_cuda_allocated_bytes": int(rec.get("peak_cuda_allocated_bytes", 0)), "peak_cuda_reserved_bytes": int(rec.get("peak_cuda_reserved_bytes", 0))}
            for comp in components:
                row[f"{comp}_l2_norm"] = float(rec["gradient_components"][comp]["l2_norm"])
            writer.writerow(row)

    review = {
        "schema": "T1_TRAJECTORY_JSON_REVIEW_V1",
        "source_sha256": hashlib.sha256(payload).hexdigest(),
        "input_schema": data.get("schema"),
        "update_count": len(updates),
        "first_update": 1,
        "last_update": 205,
        "loss": {
            "u1": losses[0],
            "u205": losses[-1],
            "min": min(losses),
            "min_update": int(updates[losses.index(min(losses))]["update"]),
            "u1_to_u205_pct_reduction": pct_reduction(losses[0], losses[-1]),
            "strict_decrease_steps": sum(losses[i] < losses[i - 1] for i in range(1, len(losses))),
            "strict_increase_steps": sum(losses[i] > losses[i - 1] for i in range(1, len(losses))),
        },
        "gradient_component_surface": {
            "components": list(components),
            "missing_parameter_tensors_total": missing_total,
            "nonfinite_parameter_tensors_total": nonfinite_total,
            "component_stats": component_stats,
            "limitation": "aggregate component l2_norms cannot prove the 48 protected attention-routing tensors were live elementwise",
        },
        "authority_decision": {
            "historical_u10_to_u205_resume_authority": False,
            "historical_u10_to_u205_biological_teacher_authority": False,
            "loss_decrease_is_not_biological_qualification": True,
            "requires_48_tensor_elementwise_gradient_and_moment_gate": True,
            "requires_future_atomic_telemetry": True,
        },
    }
    (out_dir / "T1_TRAJECTORY_JSON_REVIEW_V1.json").write_text(json.dumps(review, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return review


if __name__ == "__main__":
    in_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/mnt/data/04265c6d-285c-45b6-8e17-184d6e8bdd7b.json")
    out_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("results")
    result = analyze(in_path, out_dir)
    print("PASS_T1_TRAJECTORY_JSON_REVIEW_V1")
    print(json.dumps({"sha256": result["source_sha256"], "updates": result["update_count"], "loss_reduction": result["loss"]["u1_to_u205_pct_reduction"]}, indent=2))
