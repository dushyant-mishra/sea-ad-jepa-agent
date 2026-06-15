from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import anndata as ad
import numpy as np
import pandas as pd
from scipy import sparse
from scipy.stats import mannwhitneyu, spearmanr

from sea_ad_jepa.data import load_pathology_targets, normalize_donor_id


TECHNICAL_PATTERNS = [
    "pmi",
    "post",
    "rin",
    "rna integrity",
    "batch",
    "total_counts",
    "n_genes",
    "ngenes",
    "ncounts",
    "umi",
]


def spearman_safe(x: np.ndarray, y: np.ndarray) -> tuple[float, float]:
    valid = np.isfinite(x) & np.isfinite(y)
    if int(valid.sum()) < 3 or np.nanstd(x[valid]) == 0 or np.nanstd(y[valid]) == 0:
        return float("nan"), float("nan")
    rho, pval = spearmanr(x[valid], y[valid])
    return float(rho), float(pval)


def rank_biserial_from_mannwhitney(values: np.ndarray, groups: pd.Series) -> tuple[float, float]:
    valid = np.isfinite(values) & groups.notna().to_numpy()
    values = values[valid]
    groups = groups.loc[valid].astype(str)
    levels = sorted(groups.unique())
    if len(levels) != 2:
        return float("nan"), float("nan")
    x = values[groups == levels[0]]
    y = values[groups == levels[1]]
    if len(x) < 2 or len(y) < 2:
        return float("nan"), float("nan")
    stat, pval = mannwhitneyu(x, y, alternative="two-sided")
    rank_biserial = (2.0 * stat / (len(x) * len(y))) - 1.0
    return float(rank_biserial), float(pval)


def find_first_column(columns: list[str], patterns: list[str]) -> str | None:
    lower = {col.lower(): col for col in columns}
    for pattern in patterns:
        for lower_col, col in lower.items():
            if pattern.lower() in lower_col:
                return col
    return None


def choose_targets(summary: pd.DataFrame, at8_col: str, neun_col: str) -> pd.DataFrame:
    hits = summary.copy()
    hits = hits[(hits["perturbation_type"] == "gene") & (hits[at8_col] < 0) & (hits[neun_col] > 0)]
    hits = hits.sort_values([at8_col, neun_col], ascending=[True, False]).reset_index(drop=True)
    return hits


def donor_expression_from_h5ad(
    h5ad_path: str,
    genes: list[str],
    donor_column: str,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    adata = ad.read_h5ad(h5ad_path)
    if donor_column not in adata.obs.columns:
        raise KeyError(f"Donor column not found in AnnData obs: {donor_column}")
    var_upper = {str(gene).upper(): str(gene) for gene in adata.var_names}
    present = [var_upper[gene.upper()] for gene in genes if gene.upper() in var_upper]
    missing = sorted(set(gene.upper() for gene in genes) - set(gene.upper() for gene in present))
    if not present:
        raise ValueError("None of the requested target genes were found in AnnData var_names")

    x = adata.X
    if sparse.issparse(x):
        target_x = x[:, [adata.var_names.get_loc(gene) for gene in present]].toarray()
        total_counts = np.asarray(x.sum(axis=1)).ravel()
        n_detected = np.asarray((x > 0).sum(axis=1)).ravel()
    else:
        x_arr = np.asarray(x)
        target_x = x_arr[:, [adata.var_names.get_loc(gene) for gene in present]]
        total_counts = x_arr.sum(axis=1)
        n_detected = (x_arr > 0).sum(axis=1)

    donors = normalize_donor_id(adata.obs[donor_column]).reset_index(drop=True)
    expr = pd.DataFrame(target_x, columns=[gene.upper() for gene in present])
    expr.insert(0, "Donor ID", donors.to_numpy())
    donor_expr = expr.groupby("Donor ID", as_index=False).mean()

    qc = pd.DataFrame(
        {
            "Donor ID": donors.to_numpy(),
            "cell_total_counts_proxy": total_counts.astype(float),
            "cell_n_genes_detected_proxy": n_detected.astype(float),
        }
    )
    donor_qc = qc.groupby("Donor ID", as_index=False).agg(
        donor_mean_total_counts_proxy=("cell_total_counts_proxy", "mean"),
        donor_median_total_counts_proxy=("cell_total_counts_proxy", "median"),
        donor_mean_n_genes_detected_proxy=("cell_n_genes_detected_proxy", "mean"),
        donor_median_n_genes_detected_proxy=("cell_n_genes_detected_proxy", "median"),
        n_cells=("cell_total_counts_proxy", "size"),
    )

    if missing:
        print(f"Missing target genes in H5AD and skipped: {', '.join(missing)}")
    return donor_expr, donor_qc


def build_covariates(targets: pd.DataFrame, donor_qc: pd.DataFrame) -> tuple[pd.DataFrame, list[str], list[str], list[str]]:
    targets = targets.copy()
    targets["Donor ID"] = normalize_donor_id(targets["Donor ID"])
    donor_meta = targets.merge(donor_qc, on="Donor ID", how="left")
    continuous = []
    categorical = []
    for col in donor_meta.columns:
        if col == "Donor ID":
            continue
        if col.lower() == "sex":
            categorical.append(col)
            continue
        if pd.api.types.is_numeric_dtype(donor_meta[col]):
            if any(pattern in col.lower() for pattern in TECHNICAL_PATTERNS) or col.lower() in {"age at death", "age"}:
                continuous.append(col)
    for col in donor_qc.columns:
        if col != "Donor ID" and col not in continuous:
            continuous.append(col)
    technical = [col for col in continuous if any(pattern in col.lower() for pattern in TECHNICAL_PATTERNS)]
    return donor_meta, continuous, categorical, technical


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit Golden Quadrant counterfactual genes against donor covariates.")
    parser.add_argument("--counterfactual-summary", default="results/tables/pathology_head_gene_counterfactual_summary.csv")
    parser.add_argument("--h5ad", default="data/processed/sea_ad_mtg_microglia_pvm_all_hvg3k_expanded_modules.h5ad")
    parser.add_argument("--targets-path", default="data/processed/metadata/sea_ad_mtg_donor_pathology_targets.csv")
    parser.add_argument("--target-columns-path", default="data/processed/metadata/pathology_target_columns.csv")
    parser.add_argument("--donor-column", default="Donor ID")
    parser.add_argument("--correlation-threshold", type=float, default=0.3)
    parser.add_argument("--p-threshold", type=float, default=0.05)
    parser.add_argument("--out", default="results/tables/v2_2_target_covariate_audit.csv")
    parser.add_argument("--long-out", default="results/tables/v2_2_target_covariate_audit_long.csv")
    args = parser.parse_args()

    summary = pd.read_csv(args.counterfactual_summary)
    at8_col = find_first_column(summary.columns.tolist(), ["mean_delta_percent AT8 positive area"])
    neun_col = find_first_column(summary.columns.tolist(), ["mean_delta_percent NeuN positive area"])
    if at8_col is None or neun_col is None:
        raise KeyError("Could not find mean AT8 and NeuN delta columns in counterfactual summary")
    hits = choose_targets(summary, at8_col, neun_col)
    if hits.empty:
        raise ValueError("No Golden Quadrant genes found: required AT8 delta < 0 and NeuN delta > 0")
    genes = hits["perturbation"].astype(str).str.upper().tolist()
    print(f"Golden Quadrant genes: {', '.join(genes)}")

    donor_expr, donor_qc = donor_expression_from_h5ad(args.h5ad, genes, args.donor_column)
    targets, _ = load_pathology_targets(args.targets_path, args.target_columns_path)
    donor_meta, continuous_covariates, categorical_covariates, technical_covariates = build_covariates(targets, donor_qc)
    merged = donor_expr.merge(donor_meta, on="Donor ID", how="inner")

    long_rows = []
    status_rows = []
    present_genes = [gene for gene in genes if gene in donor_expr.columns]
    for gene in present_genes:
        gene_values = merged[gene].to_numpy(dtype=float)
        warnings = []
        wide = {"Gene": gene}
        for covariate in continuous_covariates:
            cov_values = pd.to_numeric(merged[covariate], errors="coerce").to_numpy(dtype=float)
            rho, pval = spearman_safe(gene_values, cov_values)
            wide[covariate] = rho
            wide[f"{covariate} p"] = pval
            is_technical = covariate in technical_covariates
            if is_technical and np.isfinite(rho) and abs(rho) > args.correlation_threshold and pval < args.p_threshold:
                warnings.append(f"{covariate} rho={rho:.3f} p={pval:.2g}")
            long_rows.append(
                {
                    "Gene": gene,
                    "covariate": covariate,
                    "covariate_type": "technical" if is_technical else "biological_or_pathology",
                    "test": "spearman",
                    "effect": rho,
                    "p_value": pval,
                    "warning": bool(is_technical and np.isfinite(rho) and abs(rho) > args.correlation_threshold and pval < args.p_threshold),
                }
            )
        for covariate in categorical_covariates:
            effect, pval = rank_biserial_from_mannwhitney(gene_values, merged[covariate])
            wide[covariate] = effect
            wide[f"{covariate} p"] = pval
            long_rows.append(
                {
                    "Gene": gene,
                    "covariate": covariate,
                    "covariate_type": "reported_categorical",
                    "test": "mannwhitney_rank_biserial",
                    "effect": effect,
                    "p_value": pval,
                    "warning": False,
                }
            )
        wide["n_donors"] = int(np.isfinite(gene_values).sum())
        wide["Status"] = "WARNING: Technical Artifact" if warnings else "CLEARED"
        wide["Warning Details"] = "; ".join(warnings)
        status_rows.append(wide)

    wide_df = pd.DataFrame(status_rows).set_index("Gene")
    long_df = pd.DataFrame(long_rows)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    wide_df.to_csv(args.out)
    long_df.to_csv(args.long_out, index=False)
    print("\nCovariate audit status")
    print(wide_df[["Status", "Warning Details"]].to_string())
    print(f"\nWrote audit matrix: {args.out}")
    print(f"Wrote long audit table: {args.long_out}")


if __name__ == "__main__":
    main()
