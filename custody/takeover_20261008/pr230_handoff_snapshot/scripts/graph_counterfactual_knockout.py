from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import anndata as ad
import numpy as np
import pandas as pd
import torch
from scipy import sparse
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from torch_geometric.loader import DataLoader

from sea_ad_jepa.data import load_pathology_targets, normalize_donor_id
from sea_ad_jepa.evaluation_utils import inverse_transform_prediction, transform_target
from sea_ad_jepa.gene_sets import MICROGLIA_GENE_MODULES
from sea_ad_jepa.graph_data import GraphExpressionDataset, load_consensus_edge_index, node_annotation_tensor
from sea_ad_jepa.graph_jepa import GraphGeneJEPA


def choose_device(requested: str) -> torch.device:
    if requested == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    return torch.device(requested)


def to_dense_float32(matrix) -> np.ndarray:
    if sparse.issparse(matrix):
        matrix = matrix.toarray()
    return np.asarray(matrix, dtype=np.float32)


def sample_rows_by_donor(donors: pd.Series, max_cells: int, seed: int) -> np.ndarray:
    if max_cells <= 0 or max_cells >= len(donors):
        return np.arange(len(donors), dtype=np.int64)
    rng = np.random.default_rng(seed)
    per_donor = max(1, int(np.ceil(max_cells / donors.nunique())))
    sampled = []
    for _, idx in donors.groupby(donors).indices.items():
        idx = np.asarray(idx, dtype=np.int64)
        take = min(per_donor, idx.size)
        sampled.extend(rng.choice(idx, size=take, replace=False).tolist())
    sampled = np.asarray(sorted(sampled), dtype=np.int64)
    if sampled.size > max_cells:
        sampled = np.asarray(sorted(rng.choice(sampled, size=max_cells, replace=False)), dtype=np.int64)
    return sampled


def load_graph_model(checkpoint_path: str, adata: ad.AnnData, edge_csv: str, annotation_csv: str, device: torch.device):
    checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
    args = checkpoint.get("args", {})
    gene_names = adata.var_names.astype(str).tolist()
    use_annotations = bool(args.get("use_node_annotations", False))
    node_annotations = node_annotation_tensor(annotation_csv, gene_names) if use_annotations else None
    node_feature_dim = 1 + (int(node_annotations.shape[1]) if node_annotations is not None else 0)
    model = GraphGeneJEPA(
        n_genes=adata.n_vars,
        node_feature_dim=node_feature_dim,
        gene_embed_dim=int(args.get("gene_embed_dim", 32)),
        hidden_dim=int(args.get("hidden_dim", 128)),
        latent_dim=int(args.get("latent_dim", 128)),
        n_layers=int(args.get("n_layers", 2)),
        dropout=float(args.get("dropout", 0.1)),
        conv=str(args.get("conv", "sage")),
        ema_decay=float(args.get("ema_decay", 0.996)),
        use_projection_head=bool(args.get("use_projection_head", False)),
        projection_hidden_dim=int(args.get("projection_hidden_dim", 0)) or None,
    ).to(device)
    model.load_state_dict(checkpoint["model_state"], strict=False)
    model.eval()
    edge_index = load_consensus_edge_index(edge_csv)
    return model, checkpoint, edge_index, node_annotations


def encode_cells(
    model: GraphGeneJEPA,
    matrix: np.ndarray,
    edge_index: torch.Tensor,
    node_annotations: torch.Tensor | None,
    embedding_space: str,
    device: torch.device,
    batch_size: int,
    seed: int,
) -> np.ndarray:
    dataset = GraphExpressionDataset(
        matrix,
        edge_index=edge_index,
        node_annotations=node_annotations,
        mask_fraction=0.0,
        seed=seed,
        return_pyg_data=True,
    )
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=False)
    chunks = []
    with torch.no_grad():
        for _, target in loader:
            target = target.to(device)
            chunks.append(model.encode_raw(target, space=embedding_space).cpu().numpy())
    return np.vstack(chunks).astype(np.float32)


def aggregate_by_donor(z: np.ndarray, donors: pd.Series) -> pd.DataFrame:
    df = pd.DataFrame(z, columns=[f"z_{i}" for i in range(z.shape[1])])
    df.insert(0, "Donor ID", donors.to_numpy())
    return df.groupby("Donor ID", as_index=False).mean()


def build_perturbations(gene_names: list[str], mode: str, modules: list[str] | None, genes: list[str] | None, min_genes: int):
    gene_to_idx = {gene.upper(): idx for idx, gene in enumerate(gene_names)}
    perturbations = []
    if mode == "module":
        selected = modules or sorted(MICROGLIA_GENE_MODULES)
        for module in selected:
            present = sorted(gene for gene in MICROGLIA_GENE_MODULES[module] if gene.upper() in gene_to_idx)
            idx = [gene_to_idx[gene.upper()] for gene in present]
            if len(idx) >= min_genes:
                perturbations.append((module, module, present, idx))
    else:
        selected_genes = genes or []
        for gene in selected_genes:
            idx = gene_to_idx.get(gene.upper())
            if idx is None:
                continue
            module = ";".join(sorted(name for name, gset in MICROGLIA_GENE_MODULES.items() if gene.upper() in {g.upper() for g in gset}))
            perturbations.append((module or "unannotated", gene, [gene], [idx]))
    return perturbations


def apply_intervention(x: np.ndarray, idx: list[int], intervention: str, global_means: np.ndarray) -> np.ndarray:
    perturbed = x.copy()
    if intervention == "zero":
        perturbed[:, idx] = 0.0
    elif intervention == "global_mean":
        perturbed[:, idx] = global_means[idx]
    elif intervention == "p99":
        perturbed[:, idx] = np.percentile(x[:, idx], 99, axis=0).astype(np.float32)
    else:
        raise ValueError("intervention must be 'zero', 'global_mean', or 'p99'")
    return perturbed


def disease_axis_scores(
    z_base: np.ndarray,
    z_perturbed: np.ndarray,
    donors: pd.Series,
    target: str,
    target_transform: str,
) -> tuple[dict[str, float], pd.DataFrame]:
    """Score perturbations by projection against a donor-level disease axis.

    The axis points from low-pathology donors to high-pathology donors for the
    selected target. Positive reversal means the perturbation moves cells
    backwards along that axis. Orthogonal shift measures off-axis scrambling.
    """

    targets, _ = load_pathology_targets()
    targets["Donor ID"] = normalize_donor_id(targets["Donor ID"])
    donor_targets = pd.DataFrame({"Donor ID": donors.astype(str).to_numpy()}).drop_duplicates()
    donor_targets = donor_targets.merge(targets[["Donor ID", target]], on="Donor ID", how="inner").dropna(subset=[target])
    if donor_targets[target].nunique() < 3:
        empty = pd.DataFrame({"cell_index": np.arange(z_base.shape[0])})
        return {
            "axis_available": 0.0,
            "mean_disease_axis_reversal": np.nan,
            "median_disease_axis_reversal": np.nan,
            "mean_orthogonal_shift": np.nan,
            "mean_total_shift": np.nan,
            "orthogonal_to_axis_ratio": np.nan,
        }, empty

    y = transform_target(donor_targets[target].to_numpy(dtype=np.float32), target_transform)
    low_cut = np.nanquantile(y, 0.25)
    high_cut = np.nanquantile(y, 0.75)
    low_donors = set(donor_targets.loc[y <= low_cut, "Donor ID"].astype(str))
    high_donors = set(donor_targets.loc[y >= high_cut, "Donor ID"].astype(str))
    donor_array = donors.astype(str).to_numpy()
    low_mask = np.asarray([donor in low_donors for donor in donor_array], dtype=bool)
    high_mask = np.asarray([donor in high_donors for donor in donor_array], dtype=bool)
    if low_mask.sum() == 0 or high_mask.sum() == 0:
        empty = pd.DataFrame({"cell_index": np.arange(z_base.shape[0])})
        return {
            "axis_available": 0.0,
            "mean_disease_axis_reversal": np.nan,
            "median_disease_axis_reversal": np.nan,
            "mean_orthogonal_shift": np.nan,
            "mean_total_shift": np.nan,
            "orthogonal_to_axis_ratio": np.nan,
        }, empty

    axis = z_base[high_mask].mean(axis=0) - z_base[low_mask].mean(axis=0)
    axis_norm = float(np.linalg.norm(axis))
    if axis_norm < 1e-8:
        empty = pd.DataFrame({"cell_index": np.arange(z_base.shape[0])})
        return {
            "axis_available": 0.0,
            "mean_disease_axis_reversal": np.nan,
            "median_disease_axis_reversal": np.nan,
            "mean_orthogonal_shift": np.nan,
            "mean_total_shift": np.nan,
            "orthogonal_to_axis_ratio": np.nan,
        }, empty

    axis_unit = axis / axis_norm
    delta = z_perturbed - z_base
    forward_projection = delta @ axis_unit
    reversal = -forward_projection
    orthogonal = delta - np.outer(forward_projection, axis_unit)
    orthogonal_shift = np.linalg.norm(orthogonal, axis=1)
    total_shift = np.linalg.norm(delta, axis=1)
    cell_scores = pd.DataFrame(
        {
            "cell_index": np.arange(z_base.shape[0]),
            "Donor ID": donor_array,
            "disease_axis_reversal": reversal,
            "orthogonal_shift": orthogonal_shift,
            "total_shift": total_shift,
            "forward_disease_projection": forward_projection,
        }
    )
    summary = {
        "axis_available": 1.0,
        "axis_low_donors": len(low_donors),
        "axis_high_donors": len(high_donors),
        "axis_low_cells": int(low_mask.sum()),
        "axis_high_cells": int(high_mask.sum()),
        "axis_norm": axis_norm,
        "mean_disease_axis_reversal": float(np.mean(reversal)),
        "median_disease_axis_reversal": float(np.median(reversal)),
        "mean_orthogonal_shift": float(np.mean(orthogonal_shift)),
        "mean_total_shift": float(np.mean(total_shift)),
        "orthogonal_to_axis_ratio": float(np.mean(orthogonal_shift) / (abs(np.mean(reversal)) + 1e-8)),
    }
    return summary, cell_scores


def fit_target_head(donor_embeddings: pd.DataFrame, target: str, target_transform: str):
    targets, _ = load_pathology_targets()
    targets["Donor ID"] = normalize_donor_id(targets["Donor ID"])
    data = donor_embeddings.merge(targets[["Donor ID", target]], on="Donor ID", how="inner").dropna(subset=[target])
    z_cols = [c for c in donor_embeddings.columns if c.startswith("z_")]
    x = data[z_cols].to_numpy(dtype=np.float32)
    y_raw = data[target].to_numpy(dtype=np.float32)
    y = transform_target(y_raw, target_transform)
    scaler = StandardScaler()
    x_scaled = scaler.fit_transform(x)
    head = Ridge(alpha=10.0)
    head.fit(x_scaled, y)
    return head, scaler, data["Donor ID"].astype(str).tolist(), y_raw


def predict_donor(head, scaler, donor_embeddings: pd.DataFrame, donor_order: list[str], target_transform: str) -> pd.DataFrame:
    z_cols = [c for c in donor_embeddings.columns if c.startswith("z_")]
    indexed = donor_embeddings.set_index("Donor ID").loc[donor_order].reset_index()
    pred_model = head.predict(scaler.transform(indexed[z_cols].to_numpy(dtype=np.float32))).astype(np.float32)
    pred_raw = inverse_transform_prediction(pred_model, target_transform)
    return pd.DataFrame({"Donor ID": donor_order, "prediction_model_scale": pred_model, "prediction_raw_scale": pred_raw})


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Graph-JEPA-safe digital knockouts with donor-level pathology heads.")
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--model-label", required=True)
    parser.add_argument("--h5ad", default="data/processed/sea_ad_mtg_microglia_pvm_all_hvg3k_expanded_modules.h5ad")
    parser.add_argument("--edge-csv", default="results/tables/v2_graph_string_edges_t700.csv")
    parser.add_argument("--annotation-csv", default="results/tables/jepa_v2_translational_actionability_matrix.csv")
    parser.add_argument("--embedding-space", choices=["auto", "encoder", "projector"], default="auto")
    parser.add_argument("--mode", choices=["module", "gene"], default="module")
    parser.add_argument("--modules", nargs="*", default=None)
    parser.add_argument("--genes", nargs="*", default=None)
    parser.add_argument("--intervention", choices=["global_mean", "zero", "p99"], default="global_mean")
    parser.add_argument(
        "--perturbation-direction",
        choices=["auto", "suppressor", "agonist"],
        default="auto",
        help="Wet-lab interpretation. suppressor maps to low-expression interventions; agonist maps to high-expression rescue.",
    )
    parser.add_argument("--target", default="percent AT8 positive area_Grey matter")
    parser.add_argument("--target-transform", choices=["raw", "log1p", "rank"], default="log1p")
    parser.add_argument("--donor-column", default="Donor ID")
    parser.add_argument("--min-genes", type=int, default=2)
    parser.add_argument("--max-cells", type=int, default=0, help="Optional donor-balanced cell cap. 0 uses all cells.")
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--out", required=True)
    parser.add_argument("--donor-out", required=True)
    parser.add_argument("--axis-cell-out", default="", help="Optional per-cell disease-axis projection scores.")
    args = parser.parse_args()

    device = choose_device(args.device)
    adata_all = ad.read_h5ad(args.h5ad)
    donors_all = normalize_donor_id(adata_all.obs[args.donor_column]).reset_index(drop=True)
    rows = sample_rows_by_donor(donors_all, args.max_cells, args.seed)
    adata = adata_all[rows].copy()
    donors = normalize_donor_id(adata.obs[args.donor_column]).reset_index(drop=True)
    gene_names = adata.var_names.astype(str).tolist()
    x = to_dense_float32(adata.X)
    global_means = x.mean(axis=0)
    intervention = args.intervention
    perturbation_direction = args.perturbation_direction
    if perturbation_direction == "auto":
        perturbation_direction = "agonist" if intervention == "p99" else "suppressor"
    model, checkpoint, edge_index, node_annotations = load_graph_model(args.checkpoint, adata, args.edge_csv, args.annotation_csv, device)
    model_args = checkpoint.get("args", {})
    embedding_space = args.embedding_space
    if embedding_space == "auto":
        embedding_space = "projector" if bool(model_args.get("use_projection_head", False)) else "encoder"

    perturbations = build_perturbations(gene_names, args.mode, args.modules, args.genes, args.min_genes)
    if not perturbations:
        raise ValueError("No perturbations to run.")
    print(f"Encoding baseline for {args.model_label}: {x.shape[0]:,} cells x {x.shape[1]:,} genes")
    z_base = encode_cells(model, x, edge_index, node_annotations, embedding_space, device, args.batch_size, args.seed)
    donor_base = aggregate_by_donor(z_base, donors)
    head, scaler, donor_order, _ = fit_target_head(donor_base, args.target, args.target_transform)
    baseline_pred = predict_donor(head, scaler, donor_base, donor_order, args.target_transform)

    summary_rows = []
    donor_rows = []
    axis_cell_rows = []
    for module, perturbation, genes, idx in perturbations:
        print(f"Perturbing {perturbation} ({len(idx)} genes)")
        x_perturbed = apply_intervention(x, idx, intervention, global_means)
        z_perturbed = encode_cells(model, x_perturbed, edge_index, node_annotations, embedding_space, device, args.batch_size, args.seed)
        axis_summary, axis_cells = disease_axis_scores(z_base, z_perturbed, donors, args.target, args.target_transform)
        donor_perturbed = aggregate_by_donor(z_perturbed, donors)
        perturbed_pred = predict_donor(head, scaler, donor_perturbed, donor_order, args.target_transform)
        merged = baseline_pred.merge(perturbed_pred, on="Donor ID", suffixes=("_baseline", "_perturbed"))
        merged["delta_model_scale"] = merged["prediction_model_scale_perturbed"] - merged["prediction_model_scale_baseline"]
        merged["delta_raw_scale"] = merged["prediction_raw_scale_perturbed"] - merged["prediction_raw_scale_baseline"]
        merged.insert(0, "model", args.model_label)
        merged.insert(1, "target", args.target)
        merged.insert(2, "module", module)
        merged.insert(3, "perturbation", perturbation)
        merged.insert(4, "intervention", intervention)
        merged.insert(5, "perturbation_direction", perturbation_direction)
        donor_rows.append(merged)
        if args.axis_cell_out:
            axis_cells.insert(0, "model", args.model_label)
            axis_cells.insert(1, "target", args.target)
            axis_cells.insert(2, "module", module)
            axis_cells.insert(3, "perturbation", perturbation)
            axis_cells.insert(4, "intervention", intervention)
            axis_cells.insert(5, "perturbation_direction", perturbation_direction)
            axis_cell_rows.append(axis_cells)
        summary_rows.append(
            {
                "model": args.model_label,
                "target": args.target,
                "module": module,
                "perturbation": perturbation,
                "intervention": intervention,
                "perturbation_direction": perturbation_direction,
                "n_genes_perturbed": len(idx),
                "genes": ";".join(genes),
                "mean_delta_model_scale": float(merged["delta_model_scale"].mean()),
                "mean_delta_raw_scale": float(merged["delta_raw_scale"].mean()),
                "median_delta_raw_scale": float(merged["delta_raw_scale"].median()),
                "abs_mean_delta_raw_scale": float(abs(merged["delta_raw_scale"].mean())),
                "n_donors": int(merged["Donor ID"].nunique()),
                "n_cells": int(x.shape[0]),
                **axis_summary,
            }
        )

    summary = pd.DataFrame(summary_rows).sort_values(
        ["mean_disease_axis_reversal", "mean_orthogonal_shift", "abs_mean_delta_raw_scale"],
        ascending=[False, True, False],
    )
    donor_df = pd.concat([row for row in donor_rows if "delta_raw_scale" in row.columns], ignore_index=True)
    out_path = Path(args.out)
    donor_path = Path(args.donor_out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    donor_path.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(out_path, index=False)
    donor_df.to_csv(donor_path, index=False)
    if args.axis_cell_out:
        if axis_cell_rows:
            axis_path = Path(args.axis_cell_out)
            axis_path.parent.mkdir(parents=True, exist_ok=True)
            pd.concat(axis_cell_rows, ignore_index=True).to_csv(axis_path, index=False)
            print(f"Wrote {axis_path}")
    print(f"Wrote {out_path}")
    print(f"Wrote {donor_path}")
    print(summary.head(20).to_string(index=False))


if __name__ == "__main__":
    main()
