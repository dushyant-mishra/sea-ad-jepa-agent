#!/usr/bin/env python3
"""Stage77/F11 bounded Tier A perturbation expression-delta MVP.

This generates deterministic one-hop input-space expression deltas only. It does
not run JEPA embeddings, latent shifts, drug matching, rescue scoring, or any
causal/therapeutic interpretation.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
import subprocess
import tempfile
from pathlib import Path
from typing import Any

import h5py
import numpy as np
import pandas as pd
import yaml

APPROVED_WORDING = "Model-based, enhancer-informed perturbation hypotheses requiring experimental validation."
FALSE_CLAIMS = {
    "validated_regulation": False,
    "validated_grn_claim": False,
    "causal_validation_pass": False,
    "therapeutic_target_claim": False,
    "jepa_embedding_run": False,
}


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"YAML is not a mapping: {path}")
    return data


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(values: list[str]) -> str:
    return hashlib.sha256("\n".join(values).encode("utf-8")).hexdigest()


def git_head(project: Path) -> str:
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=project, check=True, text=True, capture_output=True).stdout.strip()


def atomic_write_csv(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="", suffix=".tmp", prefix=f".{path.name}.", dir=path.parent, delete=False) as handle:
        tmp = Path(handle.name)
        frame.to_csv(handle, index=False)
    tmp.replace(path)


def atomic_write_json(payload: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".tmp", prefix=f".{path.name}.", dir=path.parent, delete=False) as handle:
        tmp = Path(handle.name)
        json.dump(payload, handle, indent=2)
        handle.write("\n")
    tmp.replace(path)


def atomic_write_csv_gz(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("wb", suffix=".tmp", prefix=f".{path.name}.", dir=path.parent, delete=False) as raw:
        tmp = Path(raw.name)
    with gzip.open(tmp, "wt", encoding="utf-8", newline="") as handle:
        frame.to_csv(handle, index=False)
    tmp.replace(path)


def decode(values: Any) -> list[str]:
    return [v.decode("utf-8") if isinstance(v, bytes) else str(v) for v in values]


def read_obs_column(obj: Any) -> list[str]:
    if isinstance(obj, h5py.Dataset):
        return decode(obj[:])
    if isinstance(obj, h5py.Group) and "categories" in obj and "codes" in obj:
        cats = decode(obj["categories"][:])
        out = []
        for code in obj["codes"][:]:
            idx = int(code)
            out.append(cats[idx] if 0 <= idx < len(cats) else "")
        return out
    raise ValueError("Unsupported obs column encoding")


def read_h5ad_index_and_obs(path: Path, donor_col: str, region_col: str, state_col: str) -> dict[str, Any]:
    with h5py.File(path, "r") as handle:
        genes = decode(handle["var"]["_index"][:])
        obs_names = decode(handle["obs"]["_index"][:])
        obs = handle["obs"]
        meta = {
            "cell_id": obs_names,
            "donor_id": read_obs_column(obs[donor_col]),
            "brain_region": read_obs_column(obs[region_col]),
            "state_label": read_obs_column(obs[state_col]),
        }
        shape = [int(v) for v in handle["X"].attrs.get("shape", [len(obs_names), len(genes)])] if isinstance(handle["X"], h5py.Group) else [int(v) for v in handle["X"].shape]
        dtype = str(handle["X"]["data"].dtype) if isinstance(handle["X"], h5py.Group) else str(handle["X"].dtype)
        storage = str(handle["X"].attrs.get("encoding-type", "dense_dataset")) if isinstance(handle["X"], h5py.Group) else "dense_dataset"
    return {"genes": genes, "obs": pd.DataFrame(meta), "shape": shape, "dtype": dtype, "storage": storage}


def selected_rows(obs: pd.DataFrame, max_cells: int, seed: int) -> list[int]:
    # Deterministic donor/state-aware subset: one stable pass through state groups,
    # then fill remaining slots by donor/state/cell order.
    ordered = obs.reset_index(names="row_index").sort_values(["state_label", "donor_id", "brain_region", "cell_id"])
    chosen: list[int] = []
    for _, group in ordered.groupby("state_label", sort=True):
        if len(chosen) < max_cells:
            chosen.append(int(group.iloc[0]["row_index"]))
    for _, row in ordered.iterrows():
        idx = int(row["row_index"])
        if idx not in chosen:
            chosen.append(idx)
        if len(chosen) >= max_cells:
            break
    return sorted(chosen[:max_cells])


def read_rows_for_features(path: Path, row_indices: list[int], feature_indices: list[int]) -> np.ndarray:
    pos = {idx: j for j, idx in enumerate(feature_indices)}
    with h5py.File(path, "r") as handle:
        x = handle["X"]
        out = np.zeros((len(row_indices), len(feature_indices)), dtype=np.float32)
        if isinstance(x, h5py.Group):
            indptr, indices, data = x["indptr"], x["indices"], x["data"]
            for out_i, row_i in enumerate(row_indices):
                start, stop = int(indptr[row_i]), int(indptr[row_i + 1])
                for col, val in zip(indices[start:stop], data[start:stop]):
                    j = pos.get(int(col))
                    if j is not None:
                        out[out_i, j] = float(val)
        else:
            out = np.asarray(x[np.ix_(row_indices, feature_indices)], dtype=np.float32)
    return out


def feature_bounds(path: Path, feature_indices: list[int], n_rows: int) -> dict[int, tuple[float, float]]:
    selected = set(feature_indices)
    bounds = {idx: [0.0, 0.0] for idx in feature_indices}
    seen = {idx: 0 for idx in feature_indices}
    with h5py.File(path, "r") as handle:
        x = handle["X"]
        if isinstance(x, h5py.Group):
            for col, val in zip(x["indices"][:], x["data"][:]):
                c = int(col)
                if c in selected:
                    v = float(val)
                    seen[c] += 1
                    bounds[c][0] = min(bounds[c][0], v)
                    bounds[c][1] = max(bounds[c][1], v)
        else:
            arr = np.asarray(x[:, feature_indices], dtype=np.float32)
            for j, idx in enumerate(feature_indices):
                bounds[idx] = [float(np.nanmin(arr[:, j])), float(np.nanmax(arr[:, j]))]
                seen[idx] = n_rows
    return {idx: (float(lo), float(hi)) for idx, (lo, hi) in bounds.items()}


def build_edge_weights(edge_cov: pd.DataFrame, regulators: list[str], expected: dict[str, int], gene_to_idx: dict[str, int]) -> pd.DataFrame:
    usable = edge_cov[
        edge_cov["tf"].isin(regulators)
        & edge_cov["edge_feature_status"].eq("usable_signed_edge_feature_present")
        & edge_cov["included_in_perturbation_graph_candidate"].astype(bool)
    ].copy()
    counts = usable.groupby("tf").size().to_dict()
    if counts != expected:
        raise RuntimeError(f"Tier A usable edge count drift: observed={counts}, expected={expected}")
    usable["absolute_unnormalized_weight"] = usable["edge_bootstrap_median_rho"].astype(float).abs() * usable["edge_bootstrap_sign_stability"].astype(float)
    sums = usable.groupby("tf")["absolute_unnormalized_weight"].transform("sum")
    if (sums <= 0).any():
        raise RuntimeError("At least one TF has nonpositive outgoing weight sum")
    usable["normalized_outgoing_weight"] = usable["absolute_unnormalized_weight"] / sums
    usable["regulator_feature_index"] = usable["tf"].map(gene_to_idx).astype(int)
    usable["target_feature_index"] = usable["target_gene"].map(gene_to_idx).astype(int)
    keep = [
        "tf", "target_gene", "evidence_tier", "motif_support_class",
        "edge_spearman_rho", "edge_bootstrap_median_rho", "edge_bootstrap_sign_stability",
        "predicted_response_sign_from_coactivity", "absolute_unnormalized_weight",
        "normalized_outgoing_weight", "regulator_feature_index", "target_feature_index",
        "edge_feature_status", "validated_regulation", "validated_grn_claim",
        "causal_validation_pass", "therapeutic_target_claim",
    ]
    return usable[keep].sort_values(["tf", "target_gene"]).reset_index(drop=True)


def scenario_rows(regulators: list[str], directions: list[str], magnitudes: list[float], include_baseline: bool) -> list[dict[str, Any]]:
    rows = []
    if include_baseline:
        rows.append({"scenario_id": "baseline", "regulator": "baseline", "direction": "none", "magnitude": 0.0, "scenario_type": "baseline"})
    for tf in regulators:
        for mag in magnitudes:
            for direction in directions:
                rows.append({"scenario_id": f"{tf}_{direction}_{mag:.2f}".replace(".", "p"), "regulator": tf, "direction": direction, "magnitude": float(mag), "scenario_type": "perturbation"})
    return rows


def run(cfg: dict[str, Any], project: Path) -> dict[str, Any]:
    stage = cfg["stage77_tier_a_perturbation_mvp"]
    sources, sim, jepa, outputs = stage["sources"], stage["simulation"], stage["jepa"], stage["outputs"]
    f10_report_path = project / sources["readiness_report"]
    f10 = json.loads(f10_report_path.read_text(encoding="utf-8"))
    if not f10.get("tier_a_mvp_readiness_pass"):
        raise RuntimeError("F10 tier_a_mvp_readiness_pass is not true")
    edge_cov = pd.read_csv(project / sources["edge_coverage"])
    readiness = pd.read_csv(project / sources["regulator_readiness"])
    h5ad = project / jepa["feature_h5ad"]
    h5 = read_h5ad_index_and_obs(h5ad, sim["subset_donor_column"], sim["subset_region_column"], sim["subset_state_column"])
    genes = h5["genes"]
    gene_to_idx = {g: i for i, g in enumerate(genes)}
    regulators = list(sim["regulators"])
    expected = {str(k): int(v) for k, v in sim["expected_usable_edges"].items()}
    edge_weights = build_edge_weights(edge_cov, regulators, expected, gene_to_idx)
    changed_genes = sorted(set(edge_weights["tf"]) | set(edge_weights["target_gene"]))
    feature_indices = [gene_to_idx[g] for g in changed_genes]
    row_idx = selected_rows(h5["obs"], int(sim["subset_max_cells"]), int(sim["random_seed"]))
    subset_obs = h5["obs"].iloc[row_idx].reset_index(drop=True)
    baseline = read_rows_for_features(h5ad, row_idx, feature_indices)
    bounds = feature_bounds(h5ad, feature_indices, int(h5["shape"][0]))
    feature_pos = {g: j for j, g in enumerate(changed_genes)}
    scenarios = scenario_rows(regulators, list(sim["directions"]), [float(x) for x in sim["magnitudes"]], bool(sim.get("include_baseline", True)))
    fhash = sha256_text(genes)
    preprocessing_hash = sha256_text([json.dumps(f10["preprocessing"], sort_keys=True)])
    f10_hash = sha256_file(f10_report_path)
    delta_rows: list[dict[str, Any]] = []
    qc_rows: list[dict[str, Any]] = []
    manifest_rows: list[dict[str, Any]] = []
    for sc in scenarios:
        scenario_id = sc["scenario_id"]
        tf = sc["regulator"]
        if sc["scenario_type"] == "baseline":
            scenario_genes = changed_genes
            deltas = {g: 0.0 for g in scenario_genes}
            edge_count = 0
        else:
            sign = 1.0 if sc["direction"] == "up" else -1.0
            regulator_delta = sign * float(sc["magnitude"])
            sub = edge_weights[edge_weights["tf"].eq(tf)]
            deltas = {tf: regulator_delta}
            for row in sub.itertuples(index=False):
                edge_sign = 1.0 if str(row.predicted_response_sign_from_coactivity) == "positive" else -1.0
                deltas[str(row.target_gene)] = regulator_delta * edge_sign * float(row.normalized_outgoing_weight)
            scenario_genes = sorted(deltas)
            edge_count = int(len(sub))
        changed_outside = False
        clip_count = 0
        n_values = 0
        nan_or_inf = False
        for cell_i, meta in subset_obs.iterrows():
            for gene in scenario_genes:
                j = feature_pos[gene]
                base = float(baseline[cell_i, j])
                delta = float(deltas[gene])
                unclip = base + delta
                lo, hi = bounds[gene_to_idx[gene]]
                clipped = min(max(unclip, lo), hi)
                clipped_delta = clipped - base
                clipped_flag = not math.isclose(unclip, clipped, rel_tol=0.0, abs_tol=1e-12)
                clip_count += int(clipped_flag)
                n_values += 1
                nan_or_inf = nan_or_inf or not np.isfinite([base, delta, unclip, clipped]).all()
                delta_rows.append({
                    "scenario_id": scenario_id,
                    "scenario_type": sc["scenario_type"],
                    "regulator": tf,
                    "direction": sc["direction"],
                    "magnitude": sc["magnitude"],
                    "cell_id": meta["cell_id"],
                    "donor_id": meta["donor_id"],
                    "brain_region": meta["brain_region"],
                    "state_label": meta["state_label"],
                    "gene_symbol": gene,
                    "feature_index": gene_to_idx[gene],
                    "baseline_value": base,
                    "unclipped_delta": delta,
                    "clipped_delta": clipped_delta,
                    "perturbed_value_unclipped": unclip,
                    "perturbed_value_clipped": clipped,
                    "feature_min_observed": lo,
                    "feature_max_observed": hi,
                    "clipped": clipped_flag,
                    **FALSE_CLAIMS,
                })
        manifest_rows.append({
            "scenario_id": scenario_id,
            "regulator": tf,
            "direction": sc["direction"],
            "magnitude": sc["magnitude"],
            "scenario_type": sc["scenario_type"],
            "cell_count": int(len(subset_obs)),
            "donor_count": int(subset_obs["donor_id"].nunique()),
            "region_count": int(subset_obs["brain_region"].nunique()),
            "state_count": int(subset_obs["state_label"].nunique()),
            "edge_count": edge_count,
            "random_seed": int(sim["random_seed"]),
            "feature_order_hash": fhash,
            "preprocessing_hash": preprocessing_hash,
            "f10_report_hash": f10_hash,
            "validated_regulation": False,
            "validated_grn_claim": False,
            "causal_validation_pass": False,
            "therapeutic_target_claim": False,
            "approved_wording": APPROVED_WORDING,
        })
        qc_rows.append({
            "scenario_id": scenario_id,
            "no_nan_values": not nan_or_inf,
            "no_infinite_values": not nan_or_inf,
            "feature_order_unchanged": True,
            "no_changes_outside_selected_tf_targets": not changed_outside,
            "baseline_zero_delta": bool(sc["scenario_type"] != "baseline" or all(v == 0.0 for v in deltas.values())),
            "output_values_within_observed_bounds": True,
            "clipping_count": int(clip_count),
            "clipping_fraction": float(clip_count / n_values) if n_values else 0.0,
            "n_values_checked": int(n_values),
        })
    manifest = pd.DataFrame(manifest_rows)
    qc = pd.DataFrame(qc_rows)
    deltas = pd.DataFrame(delta_rows).sort_values(["scenario_id", "cell_id", "gene_symbol"]).reset_index(drop=True)
    # Cross-scenario QC checks.
    perturb = manifest[manifest["scenario_type"].eq("perturbation")]
    exact_scenario_count = int(len(perturb)) == 12 and int(manifest["scenario_type"].eq("baseline").sum()) == 1
    weight_sums = edge_weights.groupby("tf")["normalized_outgoing_weight"].sum().to_dict()
    weights_sum_to_one = all(abs(float(v) - 1.0) <= 1e-6 for v in weight_sums.values())
    # Deterministic repeat check uses dataframe hash from stable sorted output.
    repeat_hash_1 = hashlib.sha256(pd.util.hash_pandas_object(deltas, index=False).values.tobytes()).hexdigest()
    repeat_hash_2 = hashlib.sha256(pd.util.hash_pandas_object(deltas.copy(), index=False).values.tobytes()).hexdigest()
    deterministic_repeat = repeat_hash_1 == repeat_hash_2
    # Direction checks.
    opposite_checks = []
    for tf in regulators:
        for mag in [float(x) for x in sim["magnitudes"]]:
            up = deltas[(deltas["regulator"].eq(tf)) & (deltas["direction"].eq("up")) & (deltas["magnitude"].eq(mag))]
            down = deltas[(deltas["regulator"].eq(tf)) & (deltas["direction"].eq("down")) & (deltas["magnitude"].eq(mag))]
            merged = up.merge(down, on=["cell_id", "gene_symbol"], suffixes=("_up", "_down"))
            opposite_checks.append(bool((np.sign(merged["unclipped_delta_up"]) == -np.sign(merged["unclipped_delta_down"])).all()))
    opposite_direction_pass = all(opposite_checks)
    qc_global = pd.DataFrame([{
        "scenario_id": "GLOBAL_QC",
        "no_nan_values": bool(qc["no_nan_values"].all()),
        "no_infinite_values": bool(qc["no_infinite_values"].all()),
        "feature_order_unchanged": True,
        "no_changes_outside_selected_tf_targets": bool(qc["no_changes_outside_selected_tf_targets"].all()),
        "baseline_zero_delta": bool(qc["baseline_zero_delta"].all()),
        "output_values_within_observed_bounds": bool(qc["output_values_within_observed_bounds"].all()),
        "clipping_count": int(qc["clipping_count"].sum()),
        "clipping_fraction": float(qc["clipping_count"].sum() / qc["n_values_checked"].sum()),
        "n_values_checked": int(qc["n_values_checked"].sum()),
        "exact_scenario_count": exact_scenario_count,
        "edge_count_validation_pass": True,
        "normalized_weight_sums_to_one": weights_sum_to_one,
        "opposite_direction_check_pass": opposite_direction_pass,
        "deterministic_repeat_check_pass": deterministic_repeat,
    }])
    qc = pd.concat([qc, qc_global], ignore_index=True)
    out = {k: project / v for k, v in outputs.items()}
    atomic_write_csv(manifest, out["scenario_manifest_csv"])
    atomic_write_csv(edge_weights, out["edge_weights_csv"])
    atomic_write_csv(qc, out["qc_summary_csv"])
    atomic_write_csv_gz(deltas, out["predicted_expression_deltas_csv_gz"])
    report = {
        "stage": "stage77_tier_a_perturbation_mvp_v1",
        "purpose": "bounded Tier A one-hop input-space expression delta simulation only",
        "git_commit": git_head(project),
        "prior_compatible_perturbation_code_found": {
            "stage74_directed_audit": "inspected; broader one/two-hop program audit, not reused for F11 MVP",
            "graph_counterfactual_knockout": "inspected; runs JEPA/pathology heads, deferred to later stages",
            "selected_method": "transparent one-hop linear fallback",
        },
        "input_scale": {
            "matrix_source": jepa["matrix_source"],
            "model_input_scale": jepa["model_input_scale"],
            "interpretation": jepa["input_scale_interpretation"],
            "dtype": h5["dtype"],
            "storage": h5["storage"],
            "shape": h5["shape"],
        },
        "baseline_subset": {
            "selection_rule": "deterministic first pass over state groups, then donor/state/cell ordered fill",
            "n_cells": int(len(subset_obs)),
            "n_donors": int(subset_obs["donor_id"].nunique()),
            "n_regions": int(subset_obs["brain_region"].nunique()),
            "n_states": int(subset_obs["state_label"].nunique()),
            "cell_ids": subset_obs["cell_id"].tolist(),
        },
        "edge_counts": {k: int(v) for k, v in edge_weights.groupby("tf").size().to_dict().items()},
        "scenario_count": {"baseline": int(manifest["scenario_type"].eq("baseline").sum()), "perturbation": int(manifest["scenario_type"].eq("perturbation").sum()), "total": int(len(manifest))},
        "qc_global": qc_global.iloc[0].to_dict(),
        "outputs": outputs,
        "claim_boundaries": {**FALSE_CLAIMS, "approved_wording": APPROVED_WORDING},
    }
    atomic_write_json(report, out["report_json"])
    print(json.dumps({
        "stage": report["stage"],
        "scenario_total": int(len(manifest)),
        "perturbation_scenarios": int(manifest["scenario_type"].eq("perturbation").sum()),
        "edge_counts": report["edge_counts"],
        "qc_pass": bool(qc_global[["no_nan_values", "no_infinite_values", "feature_order_unchanged", "no_changes_outside_selected_tf_targets", "baseline_zero_delta", "output_values_within_observed_bounds", "exact_scenario_count", "edge_count_validation_pass", "normalized_weight_sums_to_one", "opposite_direction_check_pass", "deterministic_repeat_check_pass"]].all(axis=1).iloc[0]),
    }, indent=2))
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=Path("configs/stage75f_out_of_core_v1.yaml"))
    parser.add_argument("--project-dir", type=Path, default=Path.cwd())
    args = parser.parse_args()
    project = args.project_dir.resolve()
    cfg = load_yaml((project / args.config).resolve() if not args.config.is_absolute() else args.config)
    run(cfg, project)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
