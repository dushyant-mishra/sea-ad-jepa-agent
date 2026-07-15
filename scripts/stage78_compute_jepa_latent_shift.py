#!/usr/bin/env python3
"""Stage78/F12 frozen-JEPA latent displacement for Stage77 perturbations.

This consumes frozen Stage77 input-space deltas and encodes reconstructed inputs
through the frozen epoch-30 GeneJEPA checkpoint. It does not recompute
perturbations, infer rescue, calculate drug matches, or make causal claims.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import h5py
import numpy as np
import pandas as pd
import torch
import yaml

APPROVED_WORDING = "Predicted latent displacement under a bounded input-space perturbation."
FALSE_CLAIMS = {
    "validated_regulation": False,
    "validated_grn_claim": False,
    "causal_validation_pass": False,
    "therapeutic_target_claim": False,
    "biological_rescue_claim": False,
    "drug_match_claim": False,
}


def ensure_src(project: Path) -> None:
    src = str((project / "src").resolve())
    if src not in sys.path:
        sys.path.insert(0, src)


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


def atomic_csv(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="", suffix=".tmp", prefix=f".{path.name}.", dir=path.parent, delete=False) as handle:
        tmp = Path(handle.name)
        frame.to_csv(handle, index=False)
    tmp.replace(path)


def atomic_csv_gz(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("wb", suffix=".tmp", prefix=f".{path.name}.", dir=path.parent, delete=False) as raw:
        tmp = Path(raw.name)
    with gzip.open(tmp, "wt", encoding="utf-8", newline="") as handle:
        frame.to_csv(handle, index=False)
    tmp.replace(path)


def atomic_json(payload: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".tmp", prefix=f".{path.name}.", dir=path.parent, delete=False) as handle:
        tmp = Path(handle.name)
        json.dump(payload, handle, indent=2)
        handle.write("\n")
    tmp.replace(path)


def decode_array(values: Any) -> list[str]:
    return [v.decode("utf-8") if isinstance(v, bytes) else str(v) for v in values]


def read_h5ad_obs_column(obj: Any) -> list[str]:
    if isinstance(obj, h5py.Dataset):
        return decode_array(obj[:])
    if isinstance(obj, h5py.Group) and "categories" in obj and "codes" in obj:
        categories = decode_array(obj["categories"][:])
        codes = obj["codes"][:]
        return [categories[int(code)] if int(code) >= 0 and int(code) < len(categories) else "" for code in codes]
    raise ValueError("Unsupported H5AD obs column encoding")


def read_h5ad_contract(path: Path, obs_columns: list[str]) -> dict[str, Any]:
    with h5py.File(path, "r") as handle:
        genes = decode_array(handle["var"]["_index"][:])
        obs_names = decode_array(handle["obs"]["_index"][:])
        obs = {"cell_id": obs_names}
        for col in obs_columns:
            obs[col] = read_h5ad_obs_column(handle["obs"][col]) if col in handle["obs"] else [""] * len(obs_names)
        x = handle["X"]
        if isinstance(x, h5py.Group):
            shape = [int(v) for v in x.attrs.get("shape", [len(obs_names), len(genes)])]
            storage = str(x.attrs.get("encoding-type", "sparse_group"))
            dtype = str(x["data"].dtype)
        else:
            shape = [int(v) for v in x.shape]
            storage = "dense_dataset"
            dtype = str(x.dtype)
    return {"genes": genes, "obs": pd.DataFrame(obs), "shape": shape, "storage": storage, "dtype": dtype}


def read_h5ad_rows(path: Path, row_indices: list[int]) -> np.ndarray:
    with h5py.File(path, "r") as handle:
        x = handle["X"]
        if isinstance(x, h5py.Group):
            shape = [int(v) for v in x.attrs.get("shape", [0, 0])]
            out = np.zeros((len(row_indices), shape[1]), dtype=np.float32)
            indptr = x["indptr"]
            indices = x["indices"]
            data = x["data"]
            for out_i, row_i in enumerate(row_indices):
                start = int(indptr[row_i])
                stop = int(indptr[row_i + 1])
                out[out_i, indices[start:stop]] = data[start:stop]
            return out
        return np.asarray(x[row_indices, :], dtype=np.float32)


def load_model(checkpoint_path: Path, device: torch.device) -> Any:
    from sea_ad_jepa.jepa import GeneJEPA

    checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
    args = checkpoint.get("args", {})
    model = GeneJEPA(
        input_dim=int(checkpoint["n_genes"]),
        hidden_dim=int(args.get("hidden_dim", 512)),
        latent_dim=int(args.get("latent_dim", 128)),
        ema_decay=float(args.get("ema_decay", 0.996)),
    ).to(device)
    model.load_state_dict(checkpoint["model_state"])
    model.eval()
    return model


def encode_matrix(model: Any, x: np.ndarray, device: torch.device, batch_size: int) -> np.ndarray:
    chunks = []
    with torch.no_grad():
        for start in range(0, x.shape[0], batch_size):
            batch = torch.from_numpy(x[start:start + batch_size]).to(device)
            chunks.append(model.encode(batch).cpu().numpy())
    return np.vstack(chunks).astype(np.float32)


def safe_label(value: str) -> str:
    return "".join(ch.lower() if ch.isalnum() else "_" for ch in value).strip("_") or "unknown"


def cosine_rows(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    denom = np.linalg.norm(a, axis=1) * np.linalg.norm(b, axis=1)
    denom = np.where(denom == 0, np.nan, denom)
    return np.sum(a * b, axis=1) / denom


def build_centroids(archive_path: Path, obs: pd.DataFrame, baseline_cells: list[str], state_column: str) -> tuple[dict[str, np.ndarray], dict[str, Any]]:
    if not archive_path.exists() or state_column not in obs.columns:
        return {}, {"centroids_computed": False, "reason": "missing archived embeddings or state column"}
    emb = pd.read_csv(archive_path)
    cell_col = emb.columns[0]
    emb = emb.rename(columns={cell_col: "cell_id"})
    jepa_cols = [c for c in emb.columns if c.startswith("jepa_")]
    if not jepa_cols:
        return {}, {"centroids_computed": False, "reason": "archived embedding columns not found"}
    merged = emb[["cell_id", *jepa_cols]].merge(obs[["cell_id", state_column]], on="cell_id", how="inner")
    centroids = {}
    for state, group in merged.groupby(state_column, sort=True):
        if str(state) == "" or len(group) == 0:
            continue
        centroids[str(state)] = group[jepa_cols].to_numpy(dtype=np.float32).mean(axis=0)
    return centroids, {
        "centroids_computed": bool(centroids),
        "basis": "archived_epoch30_embeddings_grouped_by_existing_h5ad_state_labels",
        "state_column": state_column,
        "n_reference_cells": int(len(merged)),
        "n_centroids": int(len(centroids)),
        "centroid_labels": sorted(centroids),
        "not_rare_high_or_background_centroids": True,
    }


def reconstruct_inputs(base_x: np.ndarray, deltas: pd.DataFrame, scenarios: pd.DataFrame, cell_order: list[str]) -> dict[str, np.ndarray]:
    cell_pos = {cell: i for i, cell in enumerate(cell_order)}
    matrices: dict[str, np.ndarray] = {}
    for row in scenarios.itertuples(index=False):
        sid = str(row.scenario_id)
        perturbed = base_x.copy()
        if str(row.scenario_type) != "baseline":
            sub = deltas[deltas["scenario_id"].eq(sid)]
            for d in sub.itertuples(index=False):
                perturbed[cell_pos[str(d.cell_id)], int(d.feature_index)] += float(d.clipped_delta)
        matrices[sid] = perturbed.astype(np.float32, copy=False)
    return matrices


def clipping_by_cell(deltas: pd.DataFrame, scenarios: pd.DataFrame, cell_order: list[str]) -> dict[tuple[str, str], dict[str, Any]]:
    out: dict[tuple[str, str], dict[str, Any]] = {}
    grouped = deltas.groupby(["scenario_id", "cell_id"], sort=True)
    for (sid, cell), group in grouped:
        clipped = group["clipped"].astype(bool)
        out[(str(sid), str(cell))] = {
            "f11_delta_gene_rows": int(len(group)),
            "f11_clipping_count": int(clipped.sum()),
            "f11_clipping_fraction": float(clipped.mean()) if len(clipped) else 0.0,
        }
    for sid in scenarios["scenario_id"].astype(str):
        for cell in cell_order:
            out.setdefault((sid, cell), {"f11_delta_gene_rows": 0, "f11_clipping_count": 0, "f11_clipping_fraction": 0.0})
    return out


def run(cfg: dict[str, Any], project: Path) -> dict[str, Any]:
    ensure_src(project)
    stage = cfg["stage78_jepa_latent_shift"]
    sources, jepa_cfg, outputs = stage["sources"], stage["jepa"], stage["outputs"]
    f10 = json.loads((project / sources["stage76_readiness_report"]).read_text(encoding="utf-8"))
    f11 = json.loads((project / sources["stage77_report"]).read_text(encoding="utf-8"))
    scenario_manifest = pd.read_csv(project / sources["stage77_scenario_manifest"])
    deltas = pd.read_csv(project / sources["stage77_predicted_expression_deltas"])
    edge_weights = pd.read_csv(project / sources["stage77_edge_weights"])
    h5ad_path = project / jepa_cfg["feature_h5ad"]
    checkpoint_path = project / jepa_cfg["checkpoint_path"]
    archive_path = project / jepa_cfg["baseline_reference_embeddings"]

    if sha256_file(project / sources["stage77_predicted_expression_deltas"]) != f11["detailed_delta_artifact"]["sha256"]:
        raise RuntimeError("F11 detailed delta SHA256 does not match frozen Stage77 report")
    if sha256_file(checkpoint_path) != f10["checkpoint_audit"]["checkpoint_sha256"]:
        raise RuntimeError("Checkpoint SHA256 does not match frozen Stage76 report")

    obs_columns = jepa_cfg["obs_columns"]
    contract = read_h5ad_contract(h5ad_path, obs_columns)
    genes = contract["genes"]
    if sha256_text(genes) != f10["feature_order"]["feature_order_sha256"]:
        raise RuntimeError("Feature order hash mismatch against F10")
    if set(scenario_manifest["feature_order_hash"].astype(str)) != {f10["feature_order"]["feature_order_sha256"]}:
        raise RuntimeError("Stage77 scenario manifest feature hash mismatch")

    cell_order = list(map(str, f11["baseline_subset"]["cell_ids"]))
    obs = contract["obs"]
    obs_index = {cell: i for i, cell in enumerate(obs["cell_id"].astype(str))}
    missing_cells = [cell for cell in cell_order if cell not in obs_index]
    if missing_cells:
        raise RuntimeError(f"F11 baseline cells missing from H5AD: {missing_cells[:5]}")
    row_indices = [obs_index[cell] for cell in cell_order]
    base_x = read_h5ad_rows(h5ad_path, row_indices)

    delta_cells_by_scenario = deltas.groupby("scenario_id")["cell_id"].apply(lambda s: sorted(map(str, s.unique()))).to_dict()
    for sid in scenario_manifest["scenario_id"].astype(str):
        if sid != "baseline" and delta_cells_by_scenario.get(sid, []) != sorted(cell_order):
            raise RuntimeError(f"F11 delta cell set mismatch for scenario {sid}")

    torch.set_num_threads(int(jepa_cfg.get("torch_num_threads", 1)))
    device = torch.device(jepa_cfg.get("device", "cpu"))
    model = load_model(checkpoint_path, device)
    batch_size = int(jepa_cfg.get("batch_size", 64))
    baseline_z = encode_matrix(model, base_x, device, batch_size)
    baseline_z_repeat = encode_matrix(model, base_x, device, batch_size)

    matrices = reconstruct_inputs(base_x, deltas, scenario_manifest, cell_order)
    scenario_embeddings = {sid: encode_matrix(model, x, device, batch_size) for sid, x in matrices.items()}
    scenario_embeddings_repeat = {sid: encode_matrix(model, x, device, batch_size) for sid, x in matrices.items()}

    archive = pd.read_csv(archive_path).rename(columns={"Unnamed: 0": "cell_id"})
    jepa_cols = [c for c in archive.columns if c.startswith("jepa_")]
    archive_lookup = archive.set_index("cell_id").loc[cell_order, jepa_cols].to_numpy(dtype=np.float32)
    archived_max_abs_diff = float(np.max(np.abs(baseline_z - archive_lookup)))
    archived_min_cos = float(np.nanmin(cosine_rows(baseline_z, archive_lookup)))

    centroids, centroid_report = build_centroids(archive_path, obs, cell_order, jepa_cfg["reference_state_column"])
    clip_lookup = clipping_by_cell(deltas, scenario_manifest, cell_order)
    scenario_meta = scenario_manifest.set_index("scenario_id")
    obs_subset = obs.set_index("cell_id").loc[cell_order].reset_index()

    rows = []
    for sid, z in scenario_embeddings.items():
        meta = scenario_meta.loc[sid]
        repeat_z = scenario_embeddings_repeat[sid]
        for i, cell in enumerate(cell_order):
            base = baseline_z[i]
            pert = z[i]
            row = {
                "scenario_id": sid,
                "cell_id": cell,
                "donor_id": obs_subset.loc[i, "Donor ID"],
                "brain_region": obs_subset.loc[i, "Brain Region"],
                "supertype": obs_subset.loc[i, "Supertype"],
                "class_label": obs_subset.loc[i, "Class"],
                "overall_ad_neuropathological_change": obs_subset.loc[i, "Overall AD neuropathological Change"],
                "regulator": meta["regulator"],
                "direction": meta["direction"],
                "magnitude": float(meta["magnitude"]),
                "scenario_type": meta["scenario_type"],
                "baseline_embedding_norm": float(np.linalg.norm(base)),
                "perturbed_embedding_norm": float(np.linalg.norm(pert)),
                "euclidean_displacement": float(np.linalg.norm(pert - base)),
                "cosine_similarity_baseline_perturbed": float(cosine_rows(base.reshape(1, -1), pert.reshape(1, -1))[0]),
                "repeat_embedding_max_abs_diff": float(np.max(np.abs(pert - repeat_z[i]))),
                **clip_lookup[(sid, cell)],
                **FALSE_CLAIMS,
            }
            for label, centroid in centroids.items():
                col = f"movement_toward_centroid__{safe_label(label)}"
                row[col] = float(np.linalg.norm(base - centroid) - np.linalg.norm(pert - centroid))
            rows.append(row)
    by_cell = pd.DataFrame(rows).sort_values(["scenario_id", "cell_id"]).reset_index(drop=True)

    centroid_cols = [c for c in by_cell.columns if c.startswith("movement_toward_centroid__")]
    summary_rows = []
    for sid, group in by_cell.groupby("scenario_id", sort=True):
        meta = scenario_meta.loc[sid]
        row = {
            "scenario_id": sid,
            "regulator": meta["regulator"],
            "direction": meta["direction"],
            "magnitude": float(meta["magnitude"]),
            "scenario_type": meta["scenario_type"],
            "n_cells": int(group["cell_id"].nunique()),
            "n_donors": int(group["donor_id"].nunique()),
            "mean_euclidean_displacement": float(group["euclidean_displacement"].mean()),
            "median_euclidean_displacement": float(group["euclidean_displacement"].median()),
            "max_euclidean_displacement": float(group["euclidean_displacement"].max()),
            "mean_cosine_similarity": float(group["cosine_similarity_baseline_perturbed"].mean()),
            "total_clipping_count": int(group["f11_clipping_count"].sum()),
            "mean_clipping_fraction": float(group["f11_clipping_fraction"].mean()),
            **FALSE_CLAIMS,
        }
        for col in centroid_cols:
            row[f"mean_{col}"] = float(group[col].mean())
        summary_rows.append(row)
    summary = pd.DataFrame(summary_rows).sort_values(["scenario_type", "regulator", "direction", "magnitude", "scenario_id"]).reset_index(drop=True)

    donor_rows = []
    for (sid, donor), group in by_cell.groupby(["scenario_id", "donor_id"], sort=True):
        meta = scenario_meta.loc[sid]
        donor_rows.append({
            "scenario_id": sid,
            "donor_id": donor,
            "regulator": meta["regulator"],
            "direction": meta["direction"],
            "magnitude": float(meta["magnitude"]),
            "scenario_type": meta["scenario_type"],
            "n_cells": int(len(group)),
            "mean_euclidean_displacement": float(group["euclidean_displacement"].mean()),
            "median_euclidean_displacement": float(group["euclidean_displacement"].median()),
            "max_euclidean_displacement": float(group["euclidean_displacement"].max()),
            "mean_cosine_similarity": float(group["cosine_similarity_baseline_perturbed"].mean()),
            "aggregation_unit": "Donor ID",
            **FALSE_CLAIMS,
        })
    donor = pd.DataFrame(donor_rows).sort_values(["scenario_id", "donor_id"]).reset_index(drop=True)

    qc_rows = []
    tol = f10["baseline_reproduction"]["approved_tolerance"]
    for sid, group in by_cell.groupby("scenario_id", sort=True):
        qc_rows.append({
            "scenario_id": sid,
            "all_baseline_cells_present": int(group["cell_id"].nunique()) == len(cell_order),
            "baseline_to_baseline_zero_within_tolerance": bool(sid != "baseline" or group["euclidean_displacement"].max() <= float(tol["max_abs_diff"])),
            "no_cell_order_mismatch": True,
            "no_feature_order_mismatch": True,
            "deterministic_repeated_inference": bool(group["repeat_embedding_max_abs_diff"].max() <= float(tol["max_abs_diff"])),
            "max_repeat_embedding_abs_diff": float(group["repeat_embedding_max_abs_diff"].max()),
            "n_cells": int(group["cell_id"].nunique()),
            "n_donors": int(group["donor_id"].nunique()),
        })
    qc = pd.DataFrame(qc_rows).sort_values("scenario_id").reset_index(drop=True)

    outputs_paths = {k: project / v for k, v in outputs.items()}
    atomic_csv_gz(by_cell, outputs_paths["cell_latent_shift_csv_gz"])
    atomic_csv(summary, outputs_paths["summary_csv"])
    atomic_csv(donor, outputs_paths["donor_concordance_csv"])
    atomic_csv(qc, outputs_paths["scenario_qc_csv"])

    validation = {
        "checkpoint_hash_matches_f10": True,
        "feature_order_hash_matches_f10": True,
        "f11_delta_hash_matches_report": True,
        "archived_baseline_reference_hash_matches_f10": sha256_file(archive_path) == f10["baseline_reproduction"]["baseline_reference_sha256"],
        "baseline_reference_reproduction_max_abs_diff": archived_max_abs_diff,
        "baseline_reference_reproduction_min_cosine": archived_min_cos,
        "baseline_reference_reproduction_pass": archived_max_abs_diff <= float(tol["max_abs_diff"]) and archived_min_cos >= float(tol["min_cosine_similarity"]),
        "baseline_to_baseline_displacement_pass": bool(qc.loc[qc["scenario_id"].eq("baseline"), "baseline_to_baseline_zero_within_tolerance"].iloc[0]),
        "all_12_perturbation_scenarios_represented": int(scenario_manifest["scenario_type"].eq("perturbation").sum()) == 12,
        "all_baseline_cells_represented_in_every_scenario": bool(qc["all_baseline_cells_present"].all()),
        "deterministic_repeated_inference_pass": bool(qc["deterministic_repeated_inference"].all()),
        "up_down_scenarios_separately_reported": {tf: sorted(scenario_manifest.loc[scenario_manifest["regulator"].eq(tf), "direction"].unique().tolist()) for tf in ["STAT1", "ELF1", "SPI1"]},
        "donor_aggregation_unit": "Donor ID",
        "no_rescue_causal_therapeutic_claim": True,
    }
    required_validation_checks = [
        "checkpoint_hash_matches_f10",
        "feature_order_hash_matches_f10",
        "f11_delta_hash_matches_report",
        "archived_baseline_reference_hash_matches_f10",
        "baseline_reference_reproduction_pass",
        "baseline_to_baseline_displacement_pass",
        "all_12_perturbation_scenarios_represented",
        "all_baseline_cells_represented_in_every_scenario",
        "deterministic_repeated_inference_pass",
        "no_rescue_causal_therapeutic_claim",
    ]
    validation["up_down_scenarios_complete"] = all(
        validation["up_down_scenarios_separately_reported"].get(tf) == ["down", "up"]
        for tf in ["STAT1", "ELF1", "SPI1"]
    )
    validation["donor_aggregation_uses_donor_unit"] = validation["donor_aggregation_unit"] == "Donor ID"
    required_validation_checks.extend(["up_down_scenarios_complete", "donor_aggregation_uses_donor_unit"])
    validation["stage78_pass"] = all(bool(validation[key]) for key in required_validation_checks)

    report = {
        "stage": "stage78_jepa_latent_shift_v1",
        "purpose": APPROVED_WORDING,
        "git_commit": git_head(project),
        "checkpoint": f10["checkpoint_audit"],
        "feature_order": f10["feature_order"],
        "preprocessing": f10["preprocessing"],
        "f11_sources": {
            "stage77_report": sources["stage77_report"],
            "stage77_delta_path": sources["stage77_predicted_expression_deltas"],
            "stage77_delta_sha256": sha256_file(project / sources["stage77_predicted_expression_deltas"]),
            "stage77_scenario_manifest": sources["stage77_scenario_manifest"],
        },
        "baseline_cells": {"n_cells": len(cell_order), "cell_ids": cell_order},
        "reference_centroids": centroid_report,
        "validation": validation,
        "outputs": outputs,
        "claim_boundaries": {**FALSE_CLAIMS, "approved_wording": APPROVED_WORDING},
    }
    atomic_json(report, outputs_paths["report_json"])
    print(json.dumps({
        "stage": report["stage"],
        "stage78_pass": validation["stage78_pass"],
        "scenarios": int(len(scenario_manifest)),
        "cells_per_scenario": len(cell_order),
        "latent_dim": int(baseline_z.shape[1]),
        "baseline_reference_reproduction_max_abs_diff": archived_max_abs_diff,
        "baseline_to_baseline_displacement_pass": validation["baseline_to_baseline_displacement_pass"],
        "reference_centroids": centroid_report,
    }, indent=2))
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/stage75f_out_of_core_v1.yaml")
    parser.add_argument("--project-dir", default=".")
    args = parser.parse_args()
    project = Path(args.project_dir).resolve()
    cfg = load_yaml(project / args.config)
    run(cfg, project)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())