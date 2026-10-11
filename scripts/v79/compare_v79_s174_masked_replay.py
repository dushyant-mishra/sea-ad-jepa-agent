#!/usr/bin/env python3
"""Compare historical S174 replay V3 with structural-support-corrected V4.

Reporting only: this tool does not decide whether V2_CORE remains frozen. It fails closed unless both replay
objects use the same compact cache, replay/support panels, folds, seed and permutation count.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

SCHEMA = "V79_S174_V3_VS_V4_MASKED_COMPARISON_V1"


def _require_equal(old: dict, new: dict, key: str) -> None:
    if old.get(key) != new.get(key):
        raise SystemExit(f"STOP: replay comparison mismatch for {key}")


def _gene_map(rows: list[dict]) -> dict[int, dict]:
    out = {int(r["gene_position"]): r for r in rows}
    if len(out) != len(rows):
        raise SystemExit("STOP: duplicate gene_position in replay results")
    return out


def _increment(rows: list[dict], richer: str, base: str, metric: str, higher_is_better: bool) -> dict:
    vals = []
    for g in rows:
        a = g["models"][base].get(metric)
        b = g["models"][richer].get(metric)
        if a is None or b is None or not (np.isfinite(a) and np.isfinite(b)):
            continue
        vals.append((b - a) if higher_is_better else (a - b))
    x = np.asarray(vals, dtype=float)
    return {
        "n_evaluable": int(x.size),
        "median_increment": float(np.median(x)) if x.size else None,
        "mean_increment": float(np.mean(x)) if x.size else None,
        "fraction_improved": float(np.mean(x > 0)) if x.size else None,
    }


def _paired_step(old_rows: list[dict], new_rows: list[dict], richer: str, base: str,
                 metric: str, higher_is_better: bool) -> dict:
    old = _increment(old_rows, richer, base, metric, higher_is_better)
    new = _increment(new_rows, richer, base, metric, higher_is_better)
    return {
        "old_median_increment": old["median_increment"],
        "masked_median_increment": new["median_increment"],
        "median_increment_delta_masked_minus_old": (
            None if old["median_increment"] is None or new["median_increment"] is None
            else float(new["median_increment"] - old["median_increment"])),
        "old_fraction_improved": old["fraction_improved"],
        "masked_fraction_improved": new["fraction_improved"],
        "old_n_evaluable": old["n_evaluable"],
        "masked_n_evaluable": new["n_evaluable"],
    }


def _support_delta(old: dict, new: dict, component: str) -> dict:
    a, b = old[component], new[component]
    return {
        "old_supported_genes": int(a["supported_genes"]),
        "masked_supported_genes": int(b["supported_genes"]),
        "supported_gene_delta": int(b["supported_genes"] - a["supported_genes"]),
        "old_eligible_genes": int(a["eligible_genes"]),
        "masked_eligible_genes": int(b["eligible_genes"]),
    }


def compare_replays(old: dict, new: dict) -> dict:
    if old.get("schema") != "V79_S174_STRUCTURE_REPLAY_DEVELOPMENT_V3":
        raise SystemExit("STOP: historical replay is not V3")
    if new.get("schema") != "V79_S174_STRUCTURE_REPLAY_DEVELOPMENT_V4_MASKED":
        raise SystemExit("STOP: corrected replay is not masked V4")
    for key in ("cache_sha256", "panel_positions_internal", "support_panel_positions_internal",
                "folds", "seed", "permutations"):
        _require_equal(old, new, key)

    # Enforce same per-gene identities/order, not just same panel arrays.
    for part in ("per_gene_detection", "per_gene_positive"):
        if [int(x["gene_position"]) for x in old[part]] != [int(x["gene_position"]) for x in new[part]]:
            raise SystemExit(f"STOP: per-gene order mismatch for {part}")

    A = {
        "detection": _paired_step(old["per_gene_detection"], new["per_gene_detection"],
                                  "depth_quad", "depth_linear", "mean_logloss", False),
        "positive": _paired_step(old["per_gene_positive"], new["per_gene_positive"],
                                 "depth_quad", "depth_linear", "mean_lpd", True),
    }
    B = {
        "detection": _paired_step(old["per_gene_detection"], new["per_gene_detection"],
                                  "depth_class", "depth_quad", "mean_logloss", False),
        "positive": _paired_step(old["per_gene_positive"], new["per_gene_positive"],
                                 "depth_class", "depth_quad", "mean_lpd", True),
    }
    C = {
        "detection": _paired_step(old["per_gene_detection"], new["per_gene_detection"],
                                  "depth_class_source", "depth_class", "mean_logloss", False),
        "positive": _paired_step(old["per_gene_positive"], new["per_gene_positive"],
                                 "depth_class_source", "depth_class", "mean_lpd", True),
    }

    old_sup, new_sup = old["random_effect_support"], new["random_effect_support"]
    D = {
        "detection_ruling_old": old["operator_increment_robustness"]["detection"]["ruling"],
        "detection_ruling_masked": new["operator_increment_robustness"]["detection"]["ruling"],
        "positive_ruling_old": old["operator_increment_robustness"]["positive_lognormal"]["ruling"],
        "positive_ruling_masked": new["operator_increment_robustness"]["positive_lognormal"]["ruling"],
        "detection_by_lambda_old": old["operator_increment_robustness"]["detection"].get("by_lambda"),
        "detection_by_lambda_masked": new["operator_increment_robustness"]["detection"].get("by_lambda"),
        "positive_by_lambda_old": old["operator_increment_robustness"]["positive_lognormal"].get("by_lambda"),
        "positive_by_lambda_masked": new["operator_increment_robustness"]["positive_lognormal"].get("by_lambda"),
    }
    E = {part: _support_delta(old_sup[part], new_sup[part], "donor") for part in ("detection", "positive")}
    F = {part: _support_delta(old_sup[part], new_sup[part], "operator") for part in ("detection", "positive")}
    G = {part: _support_delta(old_sup[part], new_sup[part], "donor_class_increment")
         for part in ("detection", "positive")}

    old_pos = _gene_map(old["per_gene_positive"])
    new_pos = _gene_map(new["per_gene_positive"])
    def n_pos_evaluable(m):
        return sum(1 for g in m.values()
                   if g["models"]["depth_class_source"].get("mean_lpd") is not None
                   and np.isfinite(g["models"]["depth_class_source"]["mean_lpd"]))
    H = {
        "old_positive_genes_evaluable": int(n_pos_evaluable(old_pos)),
        "masked_positive_genes_evaluable": int(n_pos_evaluable(new_pos)),
        "old_positive_numerical_failure_count": int(len(old_pos) - n_pos_evaluable(old_pos)),
        "masked_positive_numerical_failure_count": int(len(new_pos) - n_pos_evaluable(new_pos)),
        "interpretation": "NUMERICAL_STABILITY_ONLY__ZTNB_NOT_ADJUDICATED",
    }

    structural = new.get("structural_support")
    if not isinstance(structural, dict):
        raise SystemExit("STOP: masked V4 replay lacks structural_support record")

    return {
        "schema": SCHEMA,
        "panel_identity": "MATCH",
        "frozen_settings_identity": "MATCH",
        "cache_sha256": old["cache_sha256"],
        "structural_support": structural,
        "A_quadratic_depth": A,
        "B_broad_class": B,
        "C_source": C,
        "D_operator": D,
        "E_donor": E,
        "F_operator_beyond_donor": F,
        "G_donor_class": G,
        "H_lognormal": H,
        "controller_ruling": "NOT_AUTOMATED__CONTROLLER_REVIEW_REQUIRED",
        "boundaries": {
            "model_freeze_decision_automated": False,
            "qualification_world_generation_authorized": False,
            "real_train_posterior_inference_authorized": False,
            "training_authorized": False,
        },
    }


def main(argv=None) -> None:
    p = argparse.ArgumentParser()
    p.add_argument("old_v3")
    p.add_argument("masked_v4")
    p.add_argument("out")
    a = p.parse_args(argv)
    old = json.loads(Path(a.old_v3).read_text(encoding="utf-8"))
    new = json.loads(Path(a.masked_v4).read_text(encoding="utf-8"))
    rec = compare_replays(old, new)
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rec, indent=1, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"out": str(out), "schema": rec["schema"], "panel_identity": rec["panel_identity"]}))


if __name__ == "__main__":
    main()
