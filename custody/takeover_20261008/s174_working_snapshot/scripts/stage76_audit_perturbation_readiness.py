#!/usr/bin/env python3
"""Stage76/F10 frozen-JEPA perturbation readiness audit.

This is a gate, not a simulator. It audits whether the frozen Stage75/76
regulatory evidence can be represented in the current JEPA feature space and
whether the frozen encoder/checkpoint can be loaded and reproduced.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
import sys
import subprocess
import tempfile
from pathlib import Path
from typing import Any

import h5py
import numpy as np
import pandas as pd
import yaml

def ensure_project_src_on_path(project: Path) -> None:
    src = str((project / "src").resolve())
    if src not in sys.path:
        sys.path.insert(0, src)


FALSE_CLAIM_COLUMNS = ["validated_regulation", "validated_grn_claim", "causal_validation_pass", "therapeutic_target_claim"]
APPROVED_WORDING = "Model-based, enhancer-informed perturbation hypotheses requiring experimental validation."


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"YAML is not a mapping: {path}")
    return data


def require(frame: pd.DataFrame, columns: set[str], label: str) -> None:
    missing = columns - set(frame.columns)
    if missing:
        raise ValueError(f"{label} missing columns: {sorted(missing)}")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(lines: list[str]) -> str:
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()


def git_head(project: Path) -> str:
    result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=project, check=True, text=True, capture_output=True)
    return result.stdout.strip()


def atomic_write_csv(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="", suffix=".tmp", prefix=f".{path.name}.", dir=path.parent, delete=False) as handle:
        tmp_path = Path(handle.name)
        frame.to_csv(handle, index=False)
    tmp_path.replace(path)


def atomic_write_json(payload: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", suffix=".tmp", prefix=f".{path.name}.", dir=path.parent, delete=False) as handle:
        tmp_path = Path(handle.name)
        json.dump(payload, handle, indent=2)
        handle.write("\n")
    tmp_path.replace(path)


def decode_array(values: Any) -> list[str]:
    return [v.decode("utf-8") if isinstance(v, bytes) else str(v) for v in values]



def read_h5ad_obs_column(obj: Any) -> list[str]:
    if isinstance(obj, h5py.Dataset):
        return decode_array(obj[:])
    if isinstance(obj, h5py.Group) and "categories" in obj and "codes" in obj:
        categories = decode_array(obj["categories"][:])
        codes = obj["codes"][:]
        values = []
        for code in codes:
            idx = int(code)
            values.append(categories[idx] if idx >= 0 and idx < len(categories) else "")
        return values
    raise ValueError("Unsupported H5AD obs column encoding")

def read_h5ad_contract(path: Path, metadata_columns: list[str]) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Missing H5AD input: {path}")
    with h5py.File(path, "r") as handle:
        genes = decode_array(handle["var"]["_index"][:])
        obs_names = decode_array(handle["obs"]["_index"][:])
        duplicated = pd.Series(genes)[pd.Series(genes).duplicated()].unique().tolist()
        if isinstance(handle["X"], h5py.Group):
            x_shape = [int(v) for v in handle["X"].attrs.get("shape", [len(obs_names), len(genes)])]
            x_storage = str(handle["X"].attrs.get("encoding-type", "sparse_group"))
            x_dtype = str(handle["X"]["data"].dtype)
        else:
            x_shape = [int(v) for v in handle["X"].shape]
            x_storage = "dense_dataset"
            x_dtype = str(handle["X"].dtype)
        metadata = {}
        for column in metadata_columns:
            if column in handle["obs"]:
                vals = read_h5ad_obs_column(handle["obs"][column])
                metadata[column] = {"present": True, "n_non_missing": int(sum(v not in {"", "nan", "None"} for v in vals)), "n_unique": int(pd.Series(vals).nunique(dropna=True))}
            else:
                metadata[column] = {"present": False, "n_non_missing": 0, "n_unique": 0}
    return {"genes": genes, "obs_names": obs_names, "n_vars": len(genes), "x_shape": x_shape, "x_storage": x_storage, "x_dtype": x_dtype, "duplicate_genes": sorted(map(str, duplicated)), "metadata": metadata}


def read_h5ad_rows_dense_float32(path: Path, row_indices: list[int]) -> np.ndarray:
    if not row_indices:
        return np.zeros((0, 0), dtype=np.float32)
    if row_indices != sorted(row_indices):
        raise ValueError("row_indices must be sorted for deterministic H5AD row extraction")
    with h5py.File(path, "r") as handle:
        x = handle["X"]
        if isinstance(x, h5py.Group):
            shape = [int(v) for v in x.attrs.get("shape", [len(handle["obs"]["_index"]), len(handle["var"]["_index"])])]
            out = np.zeros((len(row_indices), shape[1]), dtype=np.float32)
            indptr = x["indptr"]
            indices = x["indices"]
            data = x["data"]
            for out_i, row_i in enumerate(row_indices):
                start = int(indptr[row_i])
                stop = int(indptr[row_i + 1])
                out[out_i, indices[start:stop]] = data[start:stop]
            return out
        arr = np.asarray(x[row_indices, :], dtype=np.float32)
        return arr

def load_gene_jepa_from_checkpoint(checkpoint_path: Path, device: Any) -> tuple[Any, dict[str, Any]]:
    import torch  # type: ignore
    from sea_ad_jepa.jepa import GeneJEPA  # type: ignore

    checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
    model_args = checkpoint.get("args", {})
    model = GeneJEPA(
        input_dim=int(checkpoint["n_genes"]),
        hidden_dim=int(model_args.get("hidden_dim", 512)),
        latent_dim=int(model_args.get("latent_dim", 128)),
        ema_decay=float(model_args.get("ema_decay", 0.996)),
    ).to(device)
    model.load_state_dict(checkpoint["model_state"])
    return model, checkpoint


def choose_torch_device(requested: str) -> Any:
    import torch  # type: ignore
    if requested == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    return torch.device(requested)


def audit_checkpoint(project: Path, cfg: dict[str, Any], n_features: int) -> dict[str, Any]:
    checkpoint_path = project / cfg["checkpoint_path"]
    loader_path = project / cfg["architecture_loader_path"]
    model_path = project / "src" / "sea_ad_jepa" / "jepa.py"
    base = {
        "checkpoint_path": cfg["checkpoint_path"],
        "checkpoint_sha256": sha256_file(checkpoint_path) if checkpoint_path.exists() else "",
        "architecture_loader_path": cfg["architecture_loader_path"],
        "architecture_loader_sha256": sha256_file(loader_path) if loader_path.exists() else "",
        "model_definition_path": "src/sea_ad_jepa/jepa.py",
        "model_definition_sha256": sha256_file(model_path) if model_path.exists() else "",
        "observed_input_dim": int(n_features),
        "encoder_frozen": True,
    }
    if not checkpoint_path.exists():
        return {**base, "checkpoint_load_status": "blocked_missing_checkpoint", "expected_input_dim": None, "device_used_for_validation": "not_available", "blocking_reason": "checkpoint file is missing"}
    if importlib.util.find_spec("torch") is None:
        return {**base, "checkpoint_load_status": "blocked_missing_torch", "expected_input_dim": None, "device_used_for_validation": "not_available_missing_torch", "blocking_reason": "torch is not available in this runtime, so the frozen checkpoint cannot be loaded"}
    import torch  # type: ignore
    device = torch.device("cpu")
    checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
    expected = int(checkpoint["n_genes"])
    status = "loaded" if expected == int(n_features) else "blocked_input_dim_mismatch"
    load_error = ""
    if status == "loaded":
        try:
            model, loaded_checkpoint = load_gene_jepa_from_checkpoint(checkpoint_path, device)
            model.eval()
            load_state = "model_instantiated_and_state_dict_loaded"
            loaded_expected = int(loaded_checkpoint["n_genes"])
            if loaded_expected != expected:
                status = "blocked_loader_checkpoint_mismatch"
                load_state = "loader_checkpoint_n_genes_mismatch"
        except Exception as exc:  # pragma: no cover - report path
            status = "blocked_model_load_error"
            load_state = "model_instantiation_failed"
            load_error = f"{type(exc).__name__}: {exc}"
    else:
        load_state = "not_attempted_input_dim_mismatch"
    return {
        **base,
        "checkpoint_load_status": status,
        "model_load_status": load_state,
        "expected_input_dim": expected,
        "device_used_for_validation": "cpu",
        "checkpoint_args": checkpoint.get("args", {}),
        "blocking_reason": "" if status == "loaded" else (load_error or "checkpoint n_genes does not match feature order length"),
    }

def build_feature_coverage(regulators: pd.DataFrame, edges: pd.DataFrame, feature_set: set[str]) -> pd.DataFrame:
    supported_tfs = set(edges["tf"].astype(str))
    target_genes = set(edges["target_gene"].astype(str))
    all_genes = sorted(set(regulators["tf"].astype(str)) | target_genes)
    rows = []
    for gene in all_genes:
        if gene in supported_tfs and gene in target_genes:
            entity_type = "regulator_and_target"
        elif gene in supported_tfs or gene in set(regulators["tf"].astype(str)):
            entity_type = "regulator"
        else:
            entity_type = "target_gene"
        rows.append({"gene_symbol": gene, "entity_type": entity_type, "present_in_jepa_feature_space": gene in feature_set, "feature_alias_applied": False, "alias_rule": "", "validated_regulation": False, "validated_grn_claim": False, "causal_validation_pass": False, "therapeutic_target_claim": False})
    return pd.DataFrame(rows).sort_values(["entity_type", "gene_symbol"]).reset_index(drop=True)


def build_edge_coverage(edges: pd.DataFrame, feature_set: set[str]) -> pd.DataFrame:
    require(edges, {"tf", "target_gene", "evidence_tier", "desired_tf_change", "direction_resolved"}, "Stage76 signed TF-target hypotheses")
    out = edges.copy()
    out["tf_present_in_jepa_feature_space"] = out["tf"].astype(str).isin(feature_set)
    out["target_present_in_jepa_feature_space"] = out["target_gene"].astype(str).isin(feature_set)
    out["edge_feature_status"] = np.select(
        [out["tf_present_in_jepa_feature_space"] & out["target_present_in_jepa_feature_space"], ~out["tf_present_in_jepa_feature_space"] & out["target_present_in_jepa_feature_space"], out["tf_present_in_jepa_feature_space"] & ~out["target_present_in_jepa_feature_space"]],
        ["usable_signed_edge_feature_present", "missing_tf_feature", "missing_target_feature"],
        default="missing_tf_and_target_features",
    )
    out["included_in_perturbation_graph_candidate"] = out["edge_feature_status"].eq("usable_signed_edge_feature_present")
    return out.sort_values(["evidence_tier", "tf", "target_gene"]).reset_index(drop=True)


def build_regulator_readiness(regulators: pd.DataFrame, edge_coverage: pd.DataFrame, feature_set: set[str], metadata: dict[str, Any], checkpoint_status: dict[str, Any], infra_ready: bool) -> pd.DataFrame:
    rows = []
    edge_groups = {tf: group for tf, group in edge_coverage.groupby("tf")}
    donor_coverage = metadata.get("Donor ID", {}).get("n_unique", 0)
    region_coverage = metadata.get("Brain Region", {}).get("n_unique", 0)
    state_coverage = metadata.get("Supertype", {}).get("n_unique", 0)
    for row in regulators.sort_values(["evidence_tier", "tf"]).itertuples(index=False):
        tf = str(row.tf)
        tier = str(row.evidence_tier)
        is_tier_c = tier == "Tier C"
        group = edge_groups.get(tf, pd.DataFrame(columns=edge_coverage.columns))
        targets = sorted(group["target_gene"].astype(str).unique().tolist()) if not group.empty else []
        present_targets = sorted([gene for gene in targets if gene in feature_set])
        absent_targets = sorted([gene for gene in targets if gene not in feature_set])
        regulator_present = tf in feature_set
        missing_tf_edges = int(group["edge_feature_status"].eq("missing_tf_feature").sum()) if not group.empty else 0
        missing_target_edges = int(group["edge_feature_status"].eq("missing_target_feature").sum()) if not group.empty else 0
        missing_both_edges = int(group["edge_feature_status"].eq("missing_tf_and_target_features").sum()) if not group.empty else 0
        usable_edges = int(group["edge_feature_status"].eq("usable_signed_edge_feature_present").sum()) if not group.empty else 0
        if is_tier_c:
            status = "excluded_negative_motif_gate"
            reason = "Tier C regulator has no TF-annotated enriched motif support at configured thresholds"
        elif checkpoint_status["checkpoint_load_status"] != "loaded":
            status = "blocked_checkpoint_not_loaded"
            reason = checkpoint_status["blocking_reason"]
        elif not infra_ready:
            status = "infrastructure_ready_pending_formal_baseline_tolerance"
            reason = "checkpoint and deterministic inference work, but formal archived-baseline reproduction remains unresolved pending tolerance review"
        elif not regulator_present:
            status = "blocked_regulator_not_in_jepa_feature_space"
            reason = "regulator is absent from JEPA feature order"
        elif usable_edges < 1:
            status = "blocked_no_usable_signed_edges"
            reason = "no signed TF-target edge has both regulator and target in JEPA feature order"
        elif absent_targets:
            status = "feature_ready_with_missing_target_edges_classified"
            reason = "at least one usable signed edge exists; missing target edges are explicitly classified and not imputed"
        else:
            status = "feature_ready_direction_unresolved"
            reason = "features are present; F11 should preserve up and down simulations because desired_tf_change remains unresolved by F9"
        rows.append({
            "tf": tf,
            "evidence_tier": tier,
            "regulator_present_in_jepa_feature_space": regulator_present,
            "total_candidate_edges": int(len(group)),
            "usable_signed_edges": usable_edges,
            "regulator_missing_edges": missing_tf_edges,
            "target_missing_edges": missing_target_edges,
            "both_missing_edges": missing_both_edges,
            "total_candidate_target_genes": int(len(targets)),
            "target_genes_present_in_jepa_feature_space": int(len(present_targets)),
            "target_genes_absent_from_jepa_feature_space": int(len(absent_targets)),
            "target_feature_coverage_fraction": float(len(present_targets) / len(targets)) if targets else 0.0,
            "unresolved_desired_perturbation_direction": True,
            "donor_coverage": int(donor_coverage),
            "region_coverage": int(region_coverage),
            "state_label_coverage": int(state_coverage),
            "per_regulator_readiness_status": status,
            "readiness_status": status,
            "blocking_reason": reason,
            "validated_regulation": False,
            "validated_grn_claim": False,
            "causal_validation_pass": False,
            "therapeutic_target_claim": False,
        })
    return pd.DataFrame(rows).reset_index(drop=True)


def inspect_preprocessing_provenance(project: Path, jepa_cfg: dict[str, Any], checkpoint_status: dict[str, Any], contract: dict[str, Any]) -> dict[str, Any]:
    source_files = [
        "scripts/train_jepa_snrna.py",
        "scripts/embed_jepa_snrna.py",
        "src/sea_ad_jepa/datasets.py",
        "src/sea_ad_jepa/jepa.py",
        "src/sea_ad_jepa/evaluation_utils.py",
        "src/sea_ad_jepa/gene_sets.py",
        "src/sea_ad_jepa/data.py",
        "docs/runbook.md",
        "configs/stage75f_out_of_core_v1.yaml",
    ]
    file_hashes = []
    for rel in source_files:
        path = project / rel
        file_hashes.append({"path": rel, "exists": path.exists(), "sha256": sha256_file(path) if path.exists() else ""})
    args = checkpoint_status.get("checkpoint_args", {}) if isinstance(checkpoint_status.get("checkpoint_args", {}), dict) else {}
    checkpoint_h5ad = str(args.get("h5ad", ""))
    configured_h5ad = str(jepa_cfg["feature_h5ad"])
    source_match = checkpoint_h5ad.replace("\\", "/") == configured_h5ad.replace("\\", "/")
    established = bool(source_match and checkpoint_status.get("checkpoint_load_status") == "loaded" and not contract["duplicate_genes"])
    return {
        "preprocessing_established": established,
        "blocking_reason": "" if established else "checkpoint metadata, configured H5AD, or feature order could not be reconciled",
        "source_h5ad_path_from_checkpoint": checkpoint_h5ad,
        "configured_feature_h5ad": configured_h5ad,
        "source_h5ad_matches_config": source_match,
        "matrix_used": "adata.X",
        "layer_or_raw_used": "X; no raw.X or named layer used by scripts/train_jepa_snrna.py or scripts/embed_jepa_snrna.py",
        "normalization_from_training_script": "none applied in training or embedding scripts after reading H5AD",
        "target_sum_normalization": "not applied by training or embedding scripts",
        "log1p_usage": "not applied by training or embedding scripts",
        "centering_or_scaling": "not applied to model inputs by training or embedding scripts",
        "clipping": "not applied to model inputs by training or embedding scripts",
        "feature_selection": "pre-existing H5AD var_names; no additional selection in training or embedding scripts",
        "feature_order": "adata.var_names / h5ad var/_index",
        "sparse_handling_training": "DenseExpressionDataset converts sparse AnnData X to dense numpy array",
        "sparse_handling_embedding": "embed_jepa_snrna.to_dense_float32 converts sparse AnnData X to dense numpy array",
        "dtype": "float32 model input tensor",
        "missing_value_handling": "no imputation or NaN handling in training/embedding scripts; values are passed through from H5AD X",
        "model_input_tensor_shape": [int(contract["x_shape"][0]), int(contract["x_shape"][1])],
        "training_masking": {"mask_fraction": args.get("mask_fraction"), "mask_mode": args.get("mask_mode"), "min_module_genes": args.get("min_module_genes"), "module_random_fill": not bool(args.get("no_module_random_fill", False))},
        "inference_masks_or_augmentations": "disabled; embedding script calls model.encode on full unmasked batch in model.eval()/torch.no_grad()",
        "embedding_encoder_branch": "context_encoder via GeneJEPA.encode with L2 normalization",
        "ema_vs_non_ema": "archived embeddings and fresh inference use context_encoder, not EMA target_encoder",
        "evaluation_mode": "model.eval() with torch.no_grad()",
        "source_files": file_hashes,
    }


def cosine_rows(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    denom = np.linalg.norm(a, axis=1) * np.linalg.norm(b, axis=1)
    denom = np.where(denom == 0, np.nan, denom)
    return np.sum(a * b, axis=1) / denom


def run_bounded_inference(project: Path, jepa_cfg: dict[str, Any], contract: dict[str, Any], subset_cells: list[str], row_indices: list[int]) -> dict[str, Any]:
    if importlib.util.find_spec("torch") is None:
        return {"status": "blocked_missing_torch"}
    import torch  # type: ignore
    seed = int(jepa_cfg.get("deterministic_inference", {}).get("seed", 7))
    batch_size = int(jepa_cfg.get("deterministic_inference", {}).get("batch_size", 64))
    device_request = str(jepa_cfg.get("deterministic_inference", {}).get("device", "cpu"))
    torch.manual_seed(seed)
    np.random.seed(seed)
    device = choose_torch_device(device_request)
    if device.type == "cuda":
        torch.cuda.manual_seed_all(seed)
    matrix = read_h5ad_rows_dense_float32(project / jepa_cfg["feature_h5ad"], row_indices)
    model, checkpoint = load_gene_jepa_from_checkpoint(project / jepa_cfg["checkpoint_path"], device)
    model.eval()

    def embed_once() -> np.ndarray:
        chunks = []
        with torch.no_grad():
            for start in range(0, matrix.shape[0], batch_size):
                batch = torch.from_numpy(matrix[start:start + batch_size]).to(device)
                chunks.append(model.encode(batch).cpu().numpy())
        return np.vstack(chunks).astype(np.float32)

    first = embed_once()
    second = embed_once()
    diff = np.abs(first - second)
    cos = cosine_rows(first, second)
    return {
        "status": "completed",
        "subset_selection_rule": "first N archived baseline cell IDs that exactly match H5AD obs/_index, preserving H5AD row order",
        "cell_ids": subset_cells,
        "n_cells": int(len(subset_cells)),
        "input_feature_count": int(matrix.shape[1]),
        "device": str(device),
        "dtype": "float32",
        "batch_size": batch_size,
        "random_seed": seed,
        "model_mode": "eval",
        "encoder_branch": "context_encoder via GeneJEPA.encode",
        "checkpoint_epoch_history_last": checkpoint.get("history", [{}])[-1] if checkpoint.get("history") else {},
        "run1_run2_max_absolute_difference": float(np.nanmax(diff)) if diff.size else math.nan,
        "run1_run2_mean_absolute_difference": float(np.nanmean(diff)) if diff.size else math.nan,
        "run1_run2_min_cosine_agreement": float(np.nanmin(cos)) if cos.size else math.nan,
        "run1_run2_mean_cosine_agreement": float(np.nanmean(cos)) if cos.size else math.nan,
        "deterministic_repeated_inference": bool(diff.size and np.nanmax(diff) == 0.0),
        "embeddings": first,
    }


def compare_archived_baseline(project: Path, jepa_cfg: dict[str, Any], inference: dict[str, Any], checkpoint_loaded: bool, preprocessing_verified: bool, feature_order_verified: bool) -> dict[str, Any]:
    baseline_path = project / jepa_cfg["baseline_reference_embeddings"]
    tolerance = jepa_cfg.get("baseline_reproduction_tolerance", {})
    max_abs_tol = float(tolerance.get("max_abs_diff", 0.0))
    min_cos_tol = float(tolerance.get("min_cosine_similarity", 1.0))
    tolerance_payload = {
        "max_abs_diff": max_abs_tol,
        "min_cosine_similarity": min_cos_tol,
        "scope": tolerance.get("tolerance_scope", "project_level_deterministic_inference_reproduction"),
        "not_biological_effect_size_threshold": bool(tolerance.get("not_biological_effect_size_threshold", True)),
        "basis": tolerance.get("basis", "exact_same_runtime_repeated_inference_then_archived_reference_review"),
    }
    base = {
        "baseline_reference_path": jepa_cfg["baseline_reference_embeddings"],
        "baseline_reference_sha256": sha256_file(baseline_path) if baseline_path.exists() else "",
        "approved_tolerance": tolerance_payload,
    }
    if not baseline_path.exists():
        return {**base, "baseline_reference_status": "baseline_reference_unavailable", "baseline_reference_provenance_verified": False, "archived_reference_compatibility": "not_available", "baseline_reproduction_pass": False, "formal_reproduction_pass": False, "blocking_reason": "baseline reference file is missing"}
    if inference.get("status") != "completed":
        return {**base, "baseline_reference_status": "available", "baseline_reference_provenance_verified": False, "archived_reference_compatibility": "not_compared_inference_blocked", "baseline_reproduction_pass": False, "formal_reproduction_pass": False, "blocking_reason": "fresh inference did not complete"}
    cell_ids = list(inference["cell_ids"])
    usecols = ["Unnamed: 0"] + [f"jepa_{i}" for i in range(inference["embeddings"].shape[1])]
    baseline = pd.read_csv(baseline_path, usecols=usecols)
    baseline = baseline[baseline["Unnamed: 0"].astype(str).isin(cell_ids)].copy()
    baseline["_order"] = baseline["Unnamed: 0"].astype(str).map({cell: i for i, cell in enumerate(cell_ids)})
    baseline = baseline.sort_values("_order")
    if baseline["Unnamed: 0"].astype(str).tolist() != cell_ids:
        return {**base, "baseline_reference_status": "provenance_unverified", "baseline_reference_provenance_verified": False, "archived_reference_compatibility": "blocked_cell_order_mismatch", "baseline_reproduction_pass": False, "formal_reproduction_pass": False, "blocking_reason": "baseline cells could not be matched exactly in requested order"}
    cols = [f"jepa_{i}" for i in range(inference["embeddings"].shape[1])]
    archived = baseline[cols].to_numpy(dtype=np.float32)
    fresh = inference["embeddings"]
    diff = np.abs(fresh - archived)
    cos = cosine_rows(fresh, archived)
    max_abs_diff = float(np.nanmax(diff))
    mean_abs_diff = float(np.nanmean(diff))
    min_cos = float(np.nanmin(cos))
    mean_cos = float(np.nanmean(cos))
    provenance_verified = bool(checkpoint_loaded and preprocessing_verified and feature_order_verified)
    tolerance_pass = bool(max_abs_diff <= max_abs_tol and min_cos >= min_cos_tol)
    reproduction_pass = bool(provenance_verified and tolerance_pass)
    return {
        **base,
        "baseline_reference_status": "available_provenance_verified_by_checkpoint_script_feature_order_and_cell_match" if provenance_verified else "available_provenance_unverified",
        "baseline_reference_provenance_verified": provenance_verified,
        "archived_reference_compatibility": "compared_exact_matched_cells_and_embedding_columns",
        "archived_reference_n_cells_compared": int(len(cell_ids)),
        "archived_reference_embedding_dimensions_compared": int(fresh.shape[1]),
        "archived_max_absolute_difference": max_abs_diff,
        "archived_mean_absolute_difference": mean_abs_diff,
        "archived_min_cosine_agreement": min_cos,
        "archived_mean_cosine_agreement": mean_cos,
        "documented_tolerance_source": "configs/stage75f_out_of_core_v1.yaml::stage76_perturbation_readiness.jepa.baseline_reproduction_tolerance",
        "same_runtime_repeated_inference_basis": {
            "max_abs_diff": inference.get("run1_run2_max_absolute_difference"),
            "mean_abs_diff": inference.get("run1_run2_mean_absolute_difference"),
            "min_cosine": inference.get("run1_run2_min_cosine_agreement"),
        },
        "baseline_reproduction_pass": reproduction_pass,
        "formal_reproduction_pass": reproduction_pass,
        "baseline_reproduction_status": "pass_approved_project_level_deterministic_inference_tolerance" if reproduction_pass else "blocked_baseline_reproduction_mismatch_or_unverified_provenance",
        "blocking_reason": "" if reproduction_pass else "archived baseline comparison did not satisfy provenance and approved numerical tolerance requirements",
    }

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--project-dir", type=Path, default=Path.cwd())
    args = parser.parse_args()
    project = args.project_dir.resolve()
    ensure_project_src_on_path(project)
    cfg = load_yaml(args.config.resolve())
    f10 = cfg["stage76_perturbation_readiness"]
    sources, jepa, outputs = f10["sources"], f10["jepa"], f10["outputs"]
    regulators = pd.read_csv(project / sources["integrated_regulator_summary"])
    signed_edges = pd.read_csv(project / sources["signed_tf_target_hypotheses"])
    negative = pd.read_csv(project / sources["integrated_negative_regulator_gate"])
    contract = read_h5ad_contract(project / jepa["feature_h5ad"], jepa["metadata_columns"])
    features = contract["genes"]
    feature_set = set(features)
    checkpoint_status = audit_checkpoint(project, jepa, len(features))
    preprocessing = inspect_preprocessing_provenance(project, jepa, checkpoint_status, contract)
    feature_coverage = build_feature_coverage(regulators, signed_edges, feature_set)
    edge_coverage = build_edge_coverage(signed_edges, feature_set)

    baseline_path = project / jepa["baseline_reference_embeddings"]
    obs_lookup = {cell: i for i, cell in enumerate(contract["obs_names"])}
    subset_n = int(jepa.get("deterministic_inference", {}).get("subset_n_cells", 32))
    if baseline_path.exists():
        baseline_ids = pd.read_csv(baseline_path, usecols=["Unnamed: 0"])["Unnamed: 0"].astype(str).tolist()
        subset_cells = [cell for cell in baseline_ids if cell in obs_lookup][:subset_n]
    else:
        subset_cells = []
    row_indices = sorted([obs_lookup[cell] for cell in subset_cells])
    ordered_cells = [contract["obs_names"][idx] for idx in row_indices]
    inference = run_bounded_inference(project, jepa, contract, ordered_cells, row_indices) if ordered_cells else {"status": "blocked_no_matched_cells", "cell_ids": [], "embeddings": np.zeros((0, 0), dtype=np.float32)}
    baseline_status = compare_archived_baseline(
        project,
        jepa,
        inference,
        checkpoint_loaded=checkpoint_status["checkpoint_load_status"] == "loaded",
        preprocessing_verified=bool(preprocessing["preprocessing_established"]),
        feature_order_verified=not bool(contract["duplicate_genes"]),
    )

    infra_ready = bool(
        checkpoint_status["checkpoint_load_status"] == "loaded"
        and preprocessing["preprocessing_established"]
        and inference.get("status") == "completed"
        and inference.get("deterministic_repeated_inference")
    )
    regulator_readiness = build_regulator_readiness(regulators, edge_coverage, feature_set, contract["metadata"], checkpoint_status, infra_ready)
    baseline_df = pd.DataFrame([{k: v for k, v in baseline_status.items() if not isinstance(v, (dict, list))}])
    if len(signed_edges) != 96:
        raise RuntimeError(f"Expected 96 Stage76 edges, observed {len(signed_edges)}")
    if len(edge_coverage.drop_duplicates(["tf", "target_gene"])) != len(edge_coverage):
        raise RuntimeError("Duplicate TF-target rows detected in Stage76 edge coverage")
    if len(regulators) != 10:
        raise RuntimeError(f"Expected 10 regulators, observed {len(regulators)}")
    if set(negative["tf"].astype(str)) != set(regulators.loc[regulators["evidence_tier"].eq("Tier C"), "tf"].astype(str)):
        raise RuntimeError("Tier C negative gate mismatch")
    output_paths = {name: project / rel for name, rel in outputs.items()}
    atomic_write_csv(feature_coverage, output_paths["feature_coverage_csv"])
    atomic_write_csv(edge_coverage, output_paths["edge_coverage_csv"])
    atomic_write_csv(regulator_readiness, output_paths["regulator_readiness_csv"])
    atomic_write_csv(baseline_df, output_paths["baseline_reproduction_csv"])

    tier_a = regulator_readiness[regulator_readiness["evidence_tier"].eq("Tier A")]
    tier_a_allowed = {"feature_ready_direction_unresolved", "feature_ready_with_missing_target_edges_classified", "infrastructure_ready_pending_formal_baseline_tolerance"}
    tier_a_mvp_ready = bool(
        checkpoint_status["checkpoint_load_status"] == "loaded"
        and preprocessing["preprocessing_established"]
        and inference.get("deterministic_repeated_inference")
        and baseline_status.get("archived_reference_compatibility") == "compared_exact_matched_cells_and_embedding_columns"
        and set(tier_a["tf"].astype(str)) == {"STAT1", "ELF1", "SPI1"}
        and tier_a["regulator_present_in_jepa_feature_space"].all()
        and (tier_a["usable_signed_edges"] >= 1).all()
        and tier_a["per_regulator_readiness_status"].isin(tier_a_allowed).all()
    )
    global_readiness_pass = bool(
        tier_a_mvp_ready
        and baseline_status.get("formal_reproduction_pass") is True
        and regulator_readiness["per_regulator_readiness_status"].isin(["feature_ready_direction_unresolved", "feature_ready_with_missing_target_edges_classified", "excluded_negative_motif_gate"]).all()
    )
    if tier_a_mvp_ready:
        final_status = "tier_a_mvp_ready"
    elif not preprocessing["preprocessing_established"]:
        final_status = "blocked_preprocessing_unverified"
    elif baseline_status.get("baseline_reference_status") == "provenance_unverified":
        final_status = "blocked_baseline_provenance_unverified"
    elif baseline_status.get("archived_reference_compatibility", "").startswith("blocked"):
        final_status = "blocked_baseline_reproduction_mismatch"
    else:
        final_status = "blocked_baseline_reproduction_unresolved_pending_tolerance_review"

    report = {
        "stage": "stage76_perturbation_readiness_v1",
        "purpose": "frozen-JEPA perturbation readiness audit; no simulation",
        "git_commit": git_head(project),
        "runtime": {"python_executable": os.sys.executable, "torch_available": importlib.util.find_spec("torch") is not None},
        "final_status": final_status,
        "global_readiness_pass": global_readiness_pass,
        "tier_a_mvp_readiness_pass": tier_a_mvp_ready,
        "readiness_pass": global_readiness_pass,
        "checkpoint_audit": checkpoint_status,
        "feature_order": {"feature_h5ad": jepa["feature_h5ad"], "feature_order_source": "h5ad var/_index", "feature_order_sha256": sha256_text(features), "n_features": int(len(features)), "duplicate_feature_rule": "blocked_duplicate_features_found" if contract["duplicate_genes"] else "no_duplicate_features_detected", "duplicate_features": contract["duplicate_genes"]},
        "preprocessing": {"configuration": jepa["preprocessing"], "preprocessing_config_sha256": sha256_text([json.dumps(jepa["preprocessing"], sort_keys=True)]), **preprocessing},
        "input_matrix": {"path": jepa["feature_h5ad"], "sha256": sha256_file(project / jepa["feature_h5ad"]), "x_shape": contract["x_shape"], "x_storage": contract["x_storage"], "x_dtype": contract["x_dtype"]},
        "metadata_coverage": contract["metadata"],
        "edge_accounting": {"total_stage76_edges": int(len(signed_edges)), "usable_signed_edge_feature_present": int(edge_coverage["edge_feature_status"].eq("usable_signed_edge_feature_present").sum()), "missing_tf_feature": int(edge_coverage["edge_feature_status"].eq("missing_tf_feature").sum()), "missing_target_feature": int(edge_coverage["edge_feature_status"].eq("missing_target_feature").sum()), "missing_tf_and_target_features": int(edge_coverage["edge_feature_status"].eq("missing_tf_and_target_features").sum())},
        "deterministic_repeated_inference": {k: v for k, v in inference.items() if k != "embeddings"},
        "baseline_reproduction": baseline_status,
        "outputs": outputs,
        "claim_boundaries": {"validated_regulation": False, "validated_grn_claim": False, "causal_validation_pass": False, "therapeutic_target_claim": False, "perturbation_simulation_run": False, "approved_wording": APPROVED_WORDING},
    }
    atomic_write_json(report, output_paths["report_json"])
    print(f"Wrote: {output_paths['feature_coverage_csv']}")
    print(f"Wrote: {output_paths['edge_coverage_csv']}")
    print(f"Wrote: {output_paths['regulator_readiness_csv']}")
    print(f"Wrote: {output_paths['baseline_reproduction_csv']}")
    print(f"Wrote: {output_paths['report_json']}")
    print(json.dumps({"stage": report["stage"], "final_status": final_status, "global_readiness_pass": global_readiness_pass, "tier_a_mvp_readiness_pass": tier_a_mvp_ready, "checkpoint_load_status": checkpoint_status["checkpoint_load_status"], "preprocessing_established": preprocessing["preprocessing_established"], "deterministic_repeated_inference": inference.get("deterministic_repeated_inference"), "baseline_reference_provenance_verified": baseline_status.get("baseline_reference_provenance_verified"), "baseline_reproduction_pass": baseline_status.get("baseline_reproduction_pass"), "archived_mean_cosine_agreement": baseline_status.get("archived_mean_cosine_agreement"), "n_features": len(features), "stage76_edges_accounted": len(edge_coverage), "usable_signed_edges": int(edge_coverage["edge_feature_status"].eq("usable_signed_edge_feature_present").sum()), "regulators": len(regulator_readiness), "tier_c_excluded": int(regulator_readiness["per_regulator_readiness_status"].eq("excluded_negative_motif_gate").sum())}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())