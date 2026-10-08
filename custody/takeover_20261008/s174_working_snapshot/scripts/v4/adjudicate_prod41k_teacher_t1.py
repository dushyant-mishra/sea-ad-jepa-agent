#!/usr/bin/env python3
"""Deterministically summarize the frozen PROD41K T1 trajectory for adjudication."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "exports" / "prod41k_teacher_t1_20260823"
RUN = OUT / "t1_run"
UPDATES = (0, 10, 25, 50, 100, 200, 205)
CONTINUOUS = (
    "broad_common", "weak_distributed", "local", "local_core", "local_halo",
    "core_halo", "sparse_marker_like", "innovation_tail",
)
RARE = ("recurrent_5pct", "recurrent_1pct")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def linear_slope(values: np.ndarray) -> float:
    x = np.arange(len(values), dtype=np.float64)
    return float(np.polyfit(x, values.astype(np.float64), 1)[0])


def main() -> None:
    complete = json.loads((RUN / "T1_RUN_COMPLETE.json").read_text(encoding="utf-8"))
    contract = json.loads((OUT / "T1_BIOLOGY_EVALUATION_FREEZE.json").read_text(encoding="utf-8"))
    trajectory = json.loads((RUN / "t1_training_trajectory.json").read_text(encoding="utf-8"))
    manifest = json.loads((RUN / "checkpoint_manifest.json").read_text(encoding="utf-8"))
    if complete["status"] != "COMPLETE_PENDING_ADJUDICATION" or complete["updates"] != 205:
        raise RuntimeError("T1 is not durably complete at u205")
    if complete["contract_sha256"] != sha256(OUT / "T1_BIOLOGY_EVALUATION_FREEZE.json"):
        raise RuntimeError("completion marker contract hash mismatch")
    if [row["update"] for row in manifest["checkpoints"]] != list(UPDATES):
        raise RuntimeError("checkpoint manifest does not contain the exact frozen schedule")
    for row in manifest["checkpoints"]:
        path = ROOT / row["path"]
        if path.stat().st_size != row["bytes"] or sha256(path) != row["sha256"]:
            raise RuntimeError(f"checkpoint hash mismatch at u{row['update']}")
    if len(trajectory["updates"]) != 205 or [row["update"] for row in trajectory["evaluations"]] != list(UPDATES):
        raise RuntimeError("trajectory update/evaluation coverage mismatch")
    if not all(row["rng_neutrality"]["equal"] for row in trajectory["evaluations"]):
        raise RuntimeError("an evaluation was not RNG-neutral")

    biology = pd.concat(
        [pd.read_csv(RUN / f"t1_biology_metrics_u{update:04d}.csv") for update in UPDATES],
        ignore_index=True,
    )
    expected_endpoints = set(CONTINUOUS + RARE)
    if set(biology["endpoint"]) != expected_endpoints:
        raise RuntimeError("endpoint coverage drift")

    key_arms = (
        "source_operator_only", "lawful_RNA_predictive_baseline",
        "u0_rich_H", "trained_rich_H", "u0_partial_H", "trained_partial_H",
        "u0_rich_CELL", "trained_rich_CELL", "u0_partial_CELL", "trained_partial_CELL",
        "trained_rich_H_donor_shuffled", "readout_donor_permutation", "exact_full_RNA_oracle",
    )
    key = biology[biology["arm"].isin(key_arms)].copy()
    values = key.pivot_table(
        index=["update", "evaluation_partition", "endpoint", "endpoint_type", "inferential_role"],
        columns="arm", values="value", aggfunc="first",
    ).reset_index()
    for trained, baseline, label in (
        ("trained_rich_H", "u0_rich_H", "delta_trained_rich_H_minus_u0"),
        ("trained_partial_H", "u0_partial_H", "delta_trained_partial_H_minus_u0"),
        ("trained_rich_CELL", "u0_rich_CELL", "delta_trained_rich_CELL_minus_u0"),
        ("trained_partial_CELL", "u0_partial_CELL", "delta_trained_partial_CELL_minus_u0"),
    ):
        values[label] = values[trained] - values[baseline]
    values.to_csv(OUT / "T1_ENDPOINT_TRAJECTORY_SUMMARY.csv", index=False, lineterminator="\n")

    final_oracle = biology[
        (biology["update"] == 205)
        & (biology["evaluation_partition"] == "reader_oracle")
        & (biology["arm"] == "trained_rich_H")
    ].copy()
    final_oracle = final_oracle[[
        "endpoint", "endpoint_type", "inferential_role", "value",
        "trained_rich_H_minus_u0_rich_H", "donor_bootstrap_delta_lower",
        "donor_bootstrap_delta_upper", "bootstrap_requested", "bootstrap_valid",
        "bootstrap_rejected_single_class", "bootstrap_valid_fraction", "AUROC",
        "positives", "positive_donors",
    ]]
    final_oracle.to_csv(OUT / "T1_FINAL_ORACLE_DELTAS.csv", index=False, lineterminator="\n")

    strata_raw = pd.read_csv(RUN / "t1_source_operator_metrics_u0205.csv")
    strata = strata_raw.pivot_table(
        index=["update", "endpoint", "endpoint_type", "stratum_type", "stratum", "cells", "donors"],
        columns="arm", values="value", aggfunc="first",
    ).reset_index()
    strata["delta_trained_rich_H_minus_u0"] = strata["trained_rich_H"] - strata["u0_rich_H"]
    strata["delta_trained_partial_H_minus_u0"] = strata["trained_partial_H"] - strata["u0_partial_H"]
    strata.to_csv(OUT / "T1_STRATUM_DELTA_SUMMARY.csv", index=False, lineterminator="\n")

    address = pd.concat(
        [pd.read_csv(RUN / f"t1_address_reader_metrics_u{update:04d}.csv") for update in UPDATES],
        ignore_index=True,
    )
    address.to_csv(OUT / "T1_ADDRESS_READER_TRAJECTORY.csv", index=False, lineterminator="\n")
    address_oracle = address[address["evaluation_partition"] == "reader_oracle"].set_index("update")

    loss = np.asarray([row["loss"] for row in trajectory["updates"]], dtype=np.float64)
    final25 = loss[-25:]
    previous25 = loss[-50:-25]
    checkpoint_loss = {str(row["update"]): row["loss"] for row in trajectory["updates"] if row["update"] in UPDATES}
    health = {
        update: json.loads((RUN / f"t1_representation_health_u{update:04d}.json").read_text(encoding="utf-8"))
        for update in UPDATES
    }
    optimization = {
        "updates": 205,
        "initial_loss_u1": float(loss[0]),
        "final_loss_u205": float(loss[-1]),
        "relative_loss_reduction_u1_to_u205": float((loss[0] - loss[-1]) / loss[0]),
        "checkpoint_loss": checkpoint_loss,
        "last_25_update_loss_slope_per_update": linear_slope(final25),
        "previous_25_mean_loss": float(previous25.mean()),
        "last_25_mean_loss": float(final25.mean()),
        "last_25_vs_previous_25_relative_mean_reduction": float((previous25.mean() - final25.mean()) / previous25.mean()),
        "last_update_gradient_components": trajectory["updates"][-1]["gradient_components"],
        "ema_updates": trajectory["updates"][-1]["ema_updates"],
        "online_ema_parameter_l2_u205": health[205]["online_ema_parameter_l2"],
        "all_evaluation_rng_neutral": True,
    }
    (OUT / "T1_OPTIMIZATION_SUMMARY.json").write_text(json.dumps(optimization, indent=2) + "\n", encoding="utf-8")

    continuous_final = final_oracle[final_oracle["endpoint_type"] == "continuous"]
    positive_continuous_ci = int((continuous_final["donor_bootstrap_delta_lower"] > 0).sum())
    rare5 = final_oracle[final_oracle["endpoint"] == "recurrent_5pct"].iloc[0]
    rare1 = final_oracle[final_oracle["endpoint"] == "recurrent_1pct"].iloc[0]
    continuous_strata = strata[strata["endpoint_type"] == "continuous"]
    source_operator_strata = continuous_strata[continuous_strata["stratum_type"].isin(["source", "operator"])]
    support_strata = continuous_strata[continuous_strata["stratum_type"] == "lawful_physical_support_quartile"]
    adjudication = {
        "schema": "prod41k-t1-final-adjudication-v1",
        "experiment_id": contract["experiment_id"],
        "status": "OPTIMIZATION_INCOMPLETE_AND_TEACHER_BIOLOGY_NOT_QUALIFIED_AT_CAP8",
        "run_complete": True,
        "mechanics_valid": True,
        "checkpoint_schedule": list(UPDATES),
        "foundation_updates": 205,
        "positive_continuous_rich_H_donor_CI_count": positive_continuous_ci,
        "continuous_endpoint_count": len(CONTINUOUS),
        "source_operator_continuous_strata_positive_rich_H_delta": int((source_operator_strata["delta_trained_rich_H_minus_u0"] > 0).sum()),
        "source_operator_continuous_strata_total": int(len(source_operator_strata)),
        "physical_support_continuous_quartiles_positive_rich_H_delta": int((support_strata["delta_trained_rich_H_minus_u0"] > 0).sum()),
        "physical_support_continuous_quartiles_total": int(len(support_strata)),
        "rare5_AP_delta": float(rare5["trained_rich_H_minus_u0_rich_H"]),
        "rare5_delta_CI": [float(rare5["donor_bootstrap_delta_lower"]), float(rare5["donor_bootstrap_delta_upper"])],
        "rare1_descriptive_AP_delta": float(rare1["trained_rich_H_minus_u0_rich_H"]),
        "address_reader_oracle_r2_u0": float(address_oracle.loc[0, "r2"]),
        "address_reader_oracle_r2_u205": float(address_oracle.loc[205, "r2"]),
        "optimization": optimization,
        "interpretation": [
            "The exact cap-safe run completed with valid mechanics and strong objective reduction.",
            "No continuous trained-rich-H endpoint has a donor-bootstrap interval wholly above zero versus u0 on the untouched oracle donors.",
            "Innovation and recurrent-5% changes are not separated from zero; recurrent-1% worsens descriptively.",
            "The address-aware molecular reader does not improve over u0.",
            "The final loss segment still trends downward with finite nonzero gradients, so the bounded cache cannot establish an optimized negative result.",
        ],
        "authorized_next_action": "Expand the lawful FOUNDATION TRAIN production inventory, then prospectively freeze a larger donor-primary bounded-exposure trajectory using the same T1 architecture, views, objective, endpoints, and donor firewall. Do not recycle the accepted 3,292-cell fit cache beyond cap 8 and do not open DEV/SEALED or pathology.",
        "not_authorized": [
            "teacher-design T2",
            "all-149-donor production refit",
            "DEV/SEALED or pathology access",
            "architecture, view-count, objective, endpoint, or u0 comparator changes",
            "additional replay of the accepted 3,292-cell fit cache",
        ],
    }
    (OUT / "T1_FINAL_ADJUDICATION.json").write_text(json.dumps(adjudication, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": adjudication["status"],
        "positive_continuous_ci": positive_continuous_ci,
        "rare5_delta": adjudication["rare5_AP_delta"],
        "rare5_ci": adjudication["rare5_delta_CI"],
        "rare1_delta": adjudication["rare1_descriptive_AP_delta"],
        "address_reader_delta": adjudication["address_reader_oracle_r2_u205"] - adjudication["address_reader_oracle_r2_u0"],
        "loss_final25_slope": optimization["last_25_update_loss_slope_per_update"],
    }, indent=2))


if __name__ == "__main__":
    main()
