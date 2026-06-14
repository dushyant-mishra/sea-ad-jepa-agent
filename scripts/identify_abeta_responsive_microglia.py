from __future__ import annotations

import argparse
import sys
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import anndata as ad
import numpy as np
import pandas as pd
import scanpy as sc
import torch
from scipy import sparse
from scipy.stats import hypergeom, pearsonr, spearmanr
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import ElasticNet, Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from torch.utils.data import DataLoader, TensorDataset

from sea_ad_jepa.data import load_pathology_targets, normalize_donor_id
from sea_ad_jepa.graph_data import load_consensus_edge_index
from sea_ad_jepa.graph_jepa import FastGraphGeneJEPA
from scripts.train_graph_jepa_stage_a_fast import choose_device, normalized_adjacency


CANONICAL_PLAQUE_MICROGLIA_GENES = [
    "APOE",
    "APOC1",
    "C1QA",
    "C1QB",
    "C1QC",
    "CD9",
    "CST7",
    "CTSD",
    "LPL",
    "SPP1",
    "TREM2",
    "TYROBP",
]


def dense_h5ad(path: str) -> tuple[ad.AnnData, torch.Tensor, list[str], pd.DataFrame]:
    adata = ad.read_h5ad(path)
    x = adata.X
    if sparse.issparse(x):
        x = x.toarray()
    return adata, torch.from_numpy(np.asarray(x, dtype=np.float32)), adata.var_names.astype(str).tolist(), adata.obs.copy()


def infer_fast_model(checkpoint: dict) -> FastGraphGeneJEPA:
    state = checkpoint["model_state"]
    n_genes = int(checkpoint["n_genes"])
    gene_embed_dim = int(state["context_encoder.gene_embedding.weight"].shape[1])
    hidden_dim = int(state["context_encoder.input_proj.0.weight"].shape[0])
    latent_dim = int(state["context_encoder.out.weight"].shape[0])
    n_layers = len([key for key in state if key.startswith("context_encoder.self_linears.") and key.endswith(".weight")])
    model = FastGraphGeneJEPA(
        n_genes=n_genes,
        node_feature_dim=1,
        gene_embed_dim=gene_embed_dim,
        hidden_dim=hidden_dim,
        latent_dim=latent_dim,
        n_layers=n_layers,
        dropout=0.0,
        ema_decay=1.0,
    )
    model.load_state_dict(state)
    for param in model.parameters():
        param.requires_grad = False
    return model


@torch.no_grad()
def encode_matrix(
    model: FastGraphGeneJEPA,
    matrix: torch.Tensor,
    adj: torch.Tensor,
    device: torch.device,
    batch_size: int,
) -> np.ndarray:
    model.eval()
    chunks = []
    loader = DataLoader(TensorDataset(matrix), batch_size=batch_size, shuffle=False)
    for (batch,) in loader:
        z = model.context_encoder(batch.to(device), adj, node_annotations=None)
        chunks.append(z.cpu().numpy())
    return np.concatenate(chunks, axis=0).astype(np.float32)


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


def spearman_safe(x: np.ndarray, y: np.ndarray) -> float:
    valid = np.isfinite(x) & np.isfinite(y)
    if int(valid.sum()) < 3 or np.nanstd(x[valid]) == 0 or np.nanstd(y[valid]) == 0:
        return float("nan")
    rho, _ = spearmanr(x[valid], y[valid])
    return float(rho)


def pearson_safe(x: np.ndarray, y: np.ndarray) -> tuple[float, float]:
    valid = np.isfinite(x) & np.isfinite(y)
    if int(valid.sum()) < 3 or np.nanstd(x[valid]) == 0 or np.nanstd(y[valid]) == 0:
        return float("nan"), float("nan")
    rho, pval = pearsonr(x[valid], y[valid])
    return float(rho), float(pval)


def load_best_abeta_config(path: str, fallback_alpha: float, fallback_l1_ratio: float) -> tuple[str, float, float]:
    if not Path(path).exists():
        return "elasticnet", fallback_alpha, fallback_l1_ratio
    summary = pd.read_csv(path)
    if summary.empty:
        return "elasticnet", fallback_alpha, fallback_l1_ratio
    row = summary.iloc[0]
    score_col = "mean_oof_spearman" if "mean_oof_spearman" in summary.columns else "oof_spearman"
    if score_col in summary.columns:
        row = summary.sort_values(score_col, ascending=False).iloc[0]
    return str(row["model"]), float(row["alpha"]), float(row["l1_ratio"])


def fit_abeta_axis(
    donor_embeddings_path: str,
    targets_path: str,
    target_columns_path: str,
    target: str,
    model_type: str,
    alpha: float,
    l1_ratio: float,
    max_iter: int,
    seed: int,
):
    donor_z = pd.read_csv(donor_embeddings_path)
    donor_z["Donor ID"] = normalize_donor_id(donor_z["Donor ID"])
    targets, _ = load_pathology_targets(targets_path, target_columns_path)
    targets["Donor ID"] = normalize_donor_id(targets["Donor ID"])
    z_cols = [col for col in donor_z.columns if col.startswith("z_")]
    merged = donor_z[["Donor ID", *z_cols]].merge(targets[["Donor ID", target]], on="Donor ID", how="inner")
    merged = merged.dropna(subset=[target]).reset_index(drop=True)
    x = merged[z_cols].to_numpy(dtype=np.float32)
    y = merged[target].to_numpy(dtype=np.float32)

    y_scaler = StandardScaler()
    y_scaled = y_scaler.fit_transform(y.reshape(-1, 1)).ravel()
    if model_type == "ridge":
        model = make_pipeline(StandardScaler(), Ridge(alpha=alpha))
    elif model_type == "elasticnet":
        model = make_pipeline(
            StandardScaler(),
            ElasticNet(alpha=alpha, l1_ratio=l1_ratio, max_iter=max_iter, random_state=seed, selection="cyclic"),
        )
    else:
        raise ValueError(f"Unsupported model type: {model_type}")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", ConvergenceWarning)
        model.fit(x, y_scaled)
    return model, y_scaler, merged, z_cols


def coefficient_table(model, z_cols: list[str]) -> pd.DataFrame:
    reg = model.named_steps[list(model.named_steps.keys())[-1]]
    coef = np.asarray(reg.coef_, dtype=np.float32).ravel()
    scaler = model.named_steps["standardscaler"]
    original_scale_coef = coef / np.asarray(scaler.scale_, dtype=np.float32)
    table = pd.DataFrame(
        {
            "latent_dim": z_cols,
            "coef_scaled_space": coef,
            "coef_original_latent_space": original_scale_coef,
            "abs_coef": np.abs(original_scale_coef),
            "nonzero": np.abs(coef) > 1e-8,
        }
    )
    return table.sort_values("abs_coef", ascending=False)


def hypergeom_overlap(discovered: set[str], canonical: set[str], universe: set[str]) -> tuple[int, float]:
    discovered = {gene.upper() for gene in discovered if gene.upper() in universe}
    canonical = {gene.upper() for gene in canonical if gene.upper() in universe}
    overlap = len(discovered & canonical)
    pval = hypergeom.sf(overlap - 1, len(universe), len(canonical), len(discovered)) if discovered and canonical else float("nan")
    return overlap, float(pval)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Identify SEA-AD microglia enriched along the frozen Graph-JEPA A-beta axis."
    )
    parser.add_argument("--h5ad", default="data/processed/sea_ad_mtg_microglia_pvm_all_hvg3k_expanded_modules.h5ad")
    parser.add_argument("--encoder-checkpoint", default="results/models/v2_2_stage_b_adversarial/stage_b_adversarial.pt")
    parser.add_argument("--edge-csv", default="results/tables/v2_graph_consensus_edge_index.csv")
    parser.add_argument("--donor-embeddings", default="results/tables/pathology_head_stage_b_frozen_donor_embeddings.csv")
    parser.add_argument("--sweep-summary", default="results/tables/v2_2_abeta_frozen_embedding_elasticnet_sweep.csv")
    parser.add_argument("--targets-path", default="data/processed/metadata/sea_ad_mtg_donor_pathology_targets.csv")
    parser.add_argument("--target-columns-path", default="data/processed/metadata/pathology_target_columns.csv")
    parser.add_argument("--target", default="percent 6e10 positive area_Grey matter")
    parser.add_argument("--donor-column", default="Donor ID")
    parser.add_argument("--top-quantile", type=float, default=0.95)
    parser.add_argument("--max-cells", type=int, default=0, help="0 means use all cells.")
    parser.add_argument("--batch-size", type=int, default=512)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--fallback-alpha", type=float, default=0.01)
    parser.add_argument("--fallback-l1-ratio", type=float, default=0.95)
    parser.add_argument("--max-iter", type=int, default=50000)
    parser.add_argument("--out-prefix", default="results/tables/v2_2_abeta_responsive_microglia")
    args = parser.parse_args()

    model_type, alpha, l1_ratio = load_best_abeta_config(args.sweep_summary, args.fallback_alpha, args.fallback_l1_ratio)
    print(f"Using A-beta axis model: {model_type} alpha={alpha} l1_ratio={l1_ratio}")
    abeta_model, y_scaler, donor_fit, z_cols = fit_abeta_axis(
        args.donor_embeddings,
        args.targets_path,
        args.target_columns_path,
        args.target,
        model_type,
        alpha,
        l1_ratio,
        args.max_iter,
        args.seed,
    )
    coef_df = coefficient_table(abeta_model, z_cols)

    device = choose_device(args.device)
    print(f"Loading AnnData: {args.h5ad}")
    adata, x_tensor, gene_names, obs = dense_h5ad(args.h5ad)
    donors_all = normalize_donor_id(obs[args.donor_column]).reset_index(drop=True)
    rows = sample_rows_by_donor(donors_all, args.max_cells, args.seed)
    if rows.size != adata.n_obs:
        adata = adata[rows].copy()
        x_tensor = torch.from_numpy(x_tensor.numpy()[rows].astype(np.float32, copy=True))
        obs = obs.iloc[rows].copy()
        donors_all = donors_all.iloc[rows].reset_index(drop=True)
    print(f"Scoring {adata.n_obs:,} cells across {donors_all.nunique():,} donors")

    checkpoint = torch.load(args.encoder_checkpoint, map_location="cpu", weights_only=False)
    encoder = infer_fast_model(checkpoint).to(device)
    edge_index = load_consensus_edge_index(args.edge_csv)
    adj = normalized_adjacency(edge_index, len(gene_names), 0.0, device)
    z_cells = encode_matrix(encoder, x_tensor, adj, device, args.batch_size)

    scaled_scores = abeta_model.predict(z_cells).astype(np.float32)
    predicted_6e10 = y_scaler.inverse_transform(scaled_scores.reshape(-1, 1)).ravel().astype(np.float32)
    adata.obs["abeta_axis_score_z"] = scaled_scores
    adata.obs["predicted_6e10_from_abeta_axis"] = predicted_6e10
    threshold = float(np.quantile(scaled_scores, args.top_quantile))
    adata.obs["abeta_responder_group"] = np.where(
        scaled_scores >= threshold,
        "A_beta_axis_high",
        "bystander",
    )
    responder_count = int((adata.obs["abeta_responder_group"] == "A_beta_axis_high").sum())
    print(f"Selected {responder_count:,} cells at top {100 * (1 - args.top_quantile):.1f}% of A-beta axis")

    targets, _ = load_pathology_targets(args.targets_path, args.target_columns_path)
    targets["Donor ID"] = normalize_donor_id(targets["Donor ID"])
    cell_scores = pd.DataFrame(
        {
            "cell_id": adata.obs_names.astype(str),
            "Donor ID": donors_all.to_numpy(),
            "abeta_axis_score_z": scaled_scores,
            "predicted_6e10_from_abeta_axis": predicted_6e10,
            "abeta_responder_group": adata.obs["abeta_responder_group"].astype(str).to_numpy(),
        }
    )
    donor_scores = (
        cell_scores.groupby("Donor ID", as_index=False)
        .agg(
            mean_abeta_axis_score_z=("abeta_axis_score_z", "mean"),
            median_abeta_axis_score_z=("abeta_axis_score_z", "median"),
            responder_fraction=("abeta_responder_group", lambda s: float(np.mean(s == "A_beta_axis_high"))),
            n_cells=("cell_id", "size"),
        )
        .merge(targets[["Donor ID", args.target]], on="Donor ID", how="inner")
        .dropna(subset=[args.target])
    )
    y_true = donor_scores[args.target].to_numpy(dtype=np.float32)
    mean_score = donor_scores["mean_abeta_axis_score_z"].to_numpy(dtype=np.float32)
    frac_score = donor_scores["responder_fraction"].to_numpy(dtype=np.float32)
    mean_pearson, mean_pearson_p = pearson_safe(mean_score, y_true)
    frac_pearson, frac_pearson_p = pearson_safe(frac_score, y_true)

    print("Running Wilcoxon DGE on original expression matrix")
    sc.tl.rank_genes_groups(
        adata,
        groupby="abeta_responder_group",
        groups=["A_beta_axis_high"],
        reference="bystander",
        method="wilcoxon",
    )
    dge = sc.get.rank_genes_groups_df(adata, group="A_beta_axis_high")
    dge = dge.sort_values(["pvals_adj", "logfoldchanges"], ascending=[True, False])
    up = dge[(dge["pvals_adj"] < 0.05) & (dge["logfoldchanges"] > 0)].copy()
    universe = {gene.upper() for gene in gene_names}
    top_up_50 = set(up.head(50)["names"].astype(str).str.upper())
    canonical = {gene.upper() for gene in CANONICAL_PLAQUE_MICROGLIA_GENES}
    overlap_n, overlap_p = hypergeom_overlap(top_up_50, canonical, universe)

    canonical_present = [gene for gene in CANONICAL_PLAQUE_MICROGLIA_GENES if gene in adata.var_names]
    canonical_score_rho = float("nan")
    canonical_score_p = float("nan")
    if len(canonical_present) >= 2:
        sc.tl.score_genes(adata, gene_list=canonical_present, score_name="canonical_plaque_microglia_score")
        cell_scores["canonical_plaque_microglia_score"] = adata.obs["canonical_plaque_microglia_score"].to_numpy()
        donor_canonical = (
            cell_scores.groupby("Donor ID", as_index=False)["canonical_plaque_microglia_score"]
            .mean()
            .merge(targets[["Donor ID", args.target]], on="Donor ID", how="inner")
            .dropna(subset=[args.target])
        )
        canonical_score_rho, canonical_score_p = pearson_safe(
            donor_canonical["canonical_plaque_microglia_score"].to_numpy(dtype=np.float32),
            donor_canonical[args.target].to_numpy(dtype=np.float32),
        )

    summary = pd.DataFrame(
        [
            {
                "analysis": "abeta_axis_responder_cells",
                "axis_model": model_type,
                "alpha": alpha,
                "l1_ratio": l1_ratio,
                "n_donors_axis_fit": int(donor_fit.shape[0]),
                "n_cells_scored": int(adata.n_obs),
                "n_donors_scored": int(donors_all.nunique()),
                "top_quantile": args.top_quantile,
                "n_responder_cells": responder_count,
                "donor_mean_score_6e10_spearman": spearman_safe(mean_score, y_true),
                "donor_mean_score_6e10_pearson": mean_pearson,
                "donor_mean_score_6e10_pearson_p": mean_pearson_p,
                "donor_responder_fraction_6e10_spearman": spearman_safe(frac_score, y_true),
                "donor_responder_fraction_6e10_pearson": frac_pearson,
                "donor_responder_fraction_6e10_pearson_p": frac_pearson_p,
                "canonical_genes_present": ";".join(canonical_present),
                "canonical_top50_overlap_n": overlap_n,
                "canonical_top50_overlap_p_hypergeom": overlap_p,
                "canonical_score_6e10_pearson": canonical_score_rho,
                "canonical_score_6e10_pearson_p": canonical_score_p,
            }
        ]
    )

    out_prefix = Path(args.out_prefix)
    out_prefix.parent.mkdir(parents=True, exist_ok=True)
    coef_df.to_csv(f"{out_prefix}_axis_coefficients_summary.csv", index=False)
    cell_scores.to_csv(f"{out_prefix}_cell_scores_summary.csv", index=False)
    donor_scores.to_csv(f"{out_prefix}_donor_validation_summary.csv", index=False)
    dge.to_csv(f"{out_prefix}_dge_all_summary.csv", index=False)
    up.to_csv(f"{out_prefix}_dge_upregulated_summary.csv", index=False)
    summary.to_csv(f"{out_prefix}_validation_metrics_summary.csv", index=False)

    print("\nValidation summary")
    print(summary.to_string(index=False))
    print("\nTop upregulated genes in A-beta-axis-high cells")
    print(up.head(20)[["names", "scores", "logfoldchanges", "pvals_adj"]].to_string(index=False))
    print(f"\nWrote outputs with prefix: {out_prefix}")


if __name__ == "__main__":
    main()
