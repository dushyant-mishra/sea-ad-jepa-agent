from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import anndata as ad
import h5py
import numpy as np
import pandas as pd
import torch
from scipy import sparse

from sea_ad_jepa.evaluation_utils import choose_device, load_jepa


def read_10x_h5_mean_log1p(path: Path, jepa_genes: list[str]) -> tuple[np.ndarray, dict[str, int], int]:
    """Return a JEPA-aligned mean log1p-normalized expression vector from a 10X H5."""
    gene_to_jepa = {gene.upper(): idx for idx, gene in enumerate(jepa_genes)}
    with h5py.File(path, "r") as h5:
        matrix = h5["matrix"]
        shape = tuple(int(x) for x in matrix["shape"][()])
        data = matrix["data"][()]
        indices = matrix["indices"][()]
        indptr = matrix["indptr"][()]
        names = [x.decode("utf-8") if isinstance(x, bytes) else str(x) for x in matrix["features/name"][()]]

    counts_features_by_cells = sparse.csc_matrix((data, indices, indptr), shape=shape, dtype=np.float32)
    cell_totals = np.asarray(counts_features_by_cells.sum(axis=0)).ravel().astype(np.float32)
    cell_totals[cell_totals <= 0] = 1.0

    remote_to_jepa: list[tuple[int, int]] = []
    for remote_idx, gene in enumerate(names):
        jepa_idx = gene_to_jepa.get(gene.upper())
        if jepa_idx is not None:
            remote_to_jepa.append((remote_idx, jepa_idx))

    remote_indices = [remote_idx for remote_idx, _ in remote_to_jepa]
    subset_cells_by_genes = counts_features_by_cells[remote_indices, :].T.tocsr()
    subset_cells_by_genes = subset_cells_by_genes.multiply((10000.0 / cell_totals)[:, None])
    subset_cells_by_genes.data = np.log1p(subset_cells_by_genes.data)
    subset_mean = np.asarray(subset_cells_by_genes.mean(axis=0)).ravel().astype(np.float32)

    mean_vec = np.zeros(len(jepa_genes), dtype=np.float32)
    for local_col, (_, jepa_idx) in enumerate(remote_to_jepa):
        mean_vec[jepa_idx] = subset_mean[local_col]

    return mean_vec, gene_to_jepa, len(remote_to_jepa)


def cosine_similarity(v1: np.ndarray, v2: np.ndarray) -> float:
    denom = float(np.linalg.norm(v1) * np.linalg.norm(v2))
    if denom == 0.0:
        return float("nan")
    return float(np.dot(v1, v2) / denom)


def spearman_correlation(v1: np.ndarray, v2: np.ndarray) -> float:
    r1 = pd.Series(v1).rank(method="average").to_numpy(dtype=np.float32)
    r2 = pd.Series(v2).rank(method="average").to_numpy(dtype=np.float32)
    r1 = r1 - r1.mean()
    r2 = r2 - r2.mean()
    denom = float(np.sqrt(np.sum(r1**2) * np.sum(r2**2)))
    if denom == 0.0:
        return float("nan")
    return float(np.sum(r1 * r2) / denom)


def project(model, x_np: np.ndarray, device: torch.device, mode: str) -> np.ndarray:
    x = torch.from_numpy(x_np[None, :]).to(device)
    with torch.no_grad():
        z = model.context_encoder(x)
        if mode == "predictive":
            z = model.predictor(z)
    return z.squeeze(0).cpu().numpy()


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Benchmark SEA-AD JEPA digital CRISPRi predictions against Drager/Kampmann "
            "iPSC-microglia CROP-seq DEG vectors."
        )
    )
    parser.add_argument("--supplementary-xlsx", default="data/raw/kampmann_gse178317/drager_2022_supplementary_tables.xlsx")
    parser.add_argument("--expression-h5", default="data/raw/kampmann_gse178317/GSM5387652_iTF_Microglia_10X_Lane1_filtered_feature_bc_matrix.h5")
    parser.add_argument("--local-h5ad", default="data/processed/sea_ad_mtg_microglia_pvm_all_hvg3k_expanded_modules.h5ad")
    parser.add_argument("--checkpoint", default="results/models/microglia_pvm_jepa_ema_var_expanded_balanced_e40/gene_jepa_epoch_030.pt")
    parser.add_argument("--targets", nargs="+", default=["CSF1R", "INPP5D", "TGFBR2", "CDK8", "CDK12", "MED1", "NDUFA8", "NDUFS5"])
    parser.add_argument("--counterfactual-mode", choices=["input_erasure", "predictive"], default="input_erasure")
    parser.add_argument("--knockdown-fraction", type=float, default=0.1)
    parser.add_argument("--fdr-threshold", type=float, default=0.05)
    parser.add_argument("--out", default="results/tables/kampmann_deg_jepa_alignment.csv")
    parser.add_argument("--device", default="auto")
    args = parser.parse_args()

    device = choose_device(args.device)
    local_adata = ad.read_h5ad(args.local_h5ad, backed="r")
    jepa_genes = local_adata.var_names.astype(str).tolist()
    local_adata.file.close()

    baseline_expr, gene_to_jepa, n_matched_expression_genes = read_10x_h5_mean_log1p(Path(args.expression_h5), jepa_genes)
    deg = pd.read_excel(args.supplementary_xlsx, sheet_name="Supplementary Table 9")
    deg["TargetGene"] = deg["TargetGene"].astype(str)
    deg["Gene"] = deg["Gene"].astype(str)

    model, _ = load_jepa(args.checkpoint, device)
    model.eval()

    z_base_observed = project(model, baseline_expr, device, mode="input_erasure")
    z_base_pred = project(model, baseline_expr, device, mode="predictive")

    rows = []
    for target in args.targets:
        target_rows = deg[deg["TargetGene"].str.upper() == target.upper()].copy()
        if target_rows.empty:
            print(f"Skipping {target}: no DEG rows in Supplementary Table 9.")
            continue

        observed_expr = baseline_expr.copy()
        n_deg_overlap = 0
        n_sig_overlap = 0
        for row in target_rows.itertuples(index=False):
            gene_idx = gene_to_jepa.get(str(row.Gene).upper())
            if gene_idx is None:
                continue
            n_deg_overlap += 1
            if np.isfinite(row.FDR) and float(row.FDR) <= args.fdr_threshold:
                n_sig_overlap += 1
            observed_expr[gene_idx] = baseline_expr[gene_idx] * float(2.0 ** row.log2FC)

        if n_deg_overlap == 0:
            print(f"Skipping {target}: no DEG genes overlap JEPA input genes.")
            continue

        predicted_expr = baseline_expr.copy()
        target_idx = gene_to_jepa.get(target.upper())
        target_in_jepa = target_idx is not None
        if target_in_jepa:
            predicted_expr[target_idx] = baseline_expr[target_idx] * args.knockdown_fraction

        z_observed = project(model, observed_expr, device, mode="input_erasure")
        z_pred = project(model, predicted_expr, device, mode=args.counterfactual_mode)

        observed_shift = z_observed - z_base_observed
        if args.counterfactual_mode == "predictive":
            predicted_shift = z_pred - z_base_pred
        else:
            predicted_shift = z_pred - z_base_observed

        rows.append(
            {
                "target_gene": target,
                "counterfactual_mode": args.counterfactual_mode,
                "knockdown_fraction": args.knockdown_fraction,
                "target_in_jepa_input": target_in_jepa,
                "n_matched_expression_genes": n_matched_expression_genes,
                "n_deg_rows": int(target_rows.shape[0]),
                "n_deg_overlap_jepa": n_deg_overlap,
                "n_significant_deg_overlap_jepa": n_sig_overlap,
                "cosine_similarity": cosine_similarity(observed_shift, predicted_shift),
                "spearman_r": spearman_correlation(observed_shift, predicted_shift),
                "observed_shift_norm": float(np.linalg.norm(observed_shift)),
                "predicted_shift_norm": float(np.linalg.norm(predicted_shift)),
            }
        )

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    result = pd.DataFrame(rows)
    result.to_csv(out_path, index=False)
    print(result.to_string(index=False))
    print(f"Wrote Kampmann DEG alignment results to: {out_path}")


if __name__ == "__main__":
    main()
