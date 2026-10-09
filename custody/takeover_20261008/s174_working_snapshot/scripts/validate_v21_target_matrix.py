from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import anndata as ad
import numpy as np
import pandas as pd
from scipy import sparse
from scipy.stats import spearmanr
from sklearn.neighbors import NearestNeighbors

from graph_counterfactual_knockout import (
    aggregate_by_donor,
    apply_intervention,
    choose_device,
    encode_cells,
    fit_target_head,
    load_graph_model,
    predict_donor,
    sample_rows_by_donor,
)
from sea_ad_jepa.data import load_pathology_targets, normalize_donor_id
from sea_ad_jepa.gene_sets import MICROGLIA_GENE_MODULES


DISEASE_TARGETS = {
    "AT8/pTau": "percent AT8 positive area_Grey matter",
    "NeuN": "percent NeuN positive area_Grey matter",
    "A beta/6e10": "percent 6e10 positive area_Grey matter",
    "GFAP": "percent GFAP positive area_Grey matter",
    "Iba1": "percent Iba1 positive area_Grey matter",
}


def to_dense_float32(matrix) -> np.ndarray:
    if sparse.issparse(matrix):
        matrix = matrix.toarray()
    return np.asarray(matrix, dtype=np.float32)


def gene_indices(gene_names: list[str], genes: list[str]) -> dict[str, int]:
    lookup = {g.upper(): i for i, g in enumerate(gene_names)}
    return {gene.upper(): lookup[gene.upper()] for gene in genes if gene.upper() in lookup}


def module_score(x: np.ndarray, gene_names: list[str], module: str) -> np.ndarray:
    indices = list(gene_indices(gene_names, list(MICROGLIA_GENE_MODULES[module])).values())
    if not indices:
        raise ValueError(f"No genes for module {module}")
    return x[:, indices].mean(axis=1)


def run_alien_cell_check(
    x: np.ndarray,
    z_base: np.ndarray,
    gene_names: list[str],
    genes: list[str],
    model,
    edge_index,
    node_annotations,
    embedding_space: str,
    device,
    batch_size: int,
    seed: int,
) -> pd.DataFrame:
    baseline_nn = NearestNeighbors(n_neighbors=2, metric="euclidean")
    baseline_nn.fit(z_base)
    base_distances, _ = baseline_nn.kneighbors(z_base)
    normal_nn = base_distances[:, 1]
    threshold = float(np.quantile(normal_nn, 0.95))

    manifold_nn = NearestNeighbors(n_neighbors=1, metric="euclidean")
    manifold_nn.fit(z_base)

    means = x.mean(axis=0)
    idx_by_gene = gene_indices(gene_names, genes)
    rows = []
    for gene in genes:
        idx = idx_by_gene.get(gene.upper())
        if idx is None:
            rows.append({"gene": gene.upper(), "status": "missing_gene", "manifold_violation": True})
            continue
        x_perturbed = apply_intervention(x, [idx], "global_mean", means)
        z_perturbed = encode_cells(model, x_perturbed, edge_index, node_annotations, embedding_space, device, batch_size, seed)
        nearest, _ = manifold_nn.kneighbors(z_perturbed)
        nearest = nearest[:, 0]
        violation_fraction = float(np.mean(nearest > threshold))
        rows.append(
            {
                "gene": gene.upper(),
                "status": "ok",
                "normal_nn_distance_p95": threshold,
                "perturbed_nearest_mean": float(np.mean(nearest)),
                "perturbed_nearest_median": float(np.median(nearest)),
                "perturbed_nearest_p95": float(np.quantile(nearest, 0.95)),
                "violation_fraction": violation_fraction,
                "manifold_violation": bool(violation_fraction > 0.05),
            }
        )
    return pd.DataFrame(rows)


def run_covariate_check(
    donor_z: pd.DataFrame,
    target_matrix: pd.DataFrame,
    target_columns: dict[str, str],
    metadata_path: Path,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    metadata = pd.read_csv(metadata_path)
    metadata["Donor ID"] = normalize_donor_id(metadata["Donor ID"])
    donor_z = donor_z.copy()
    donor_z["Donor ID"] = normalize_donor_id(donor_z["Donor ID"])
    merged = donor_z.merge(metadata, on="Donor ID", how="inner")

    candidate_covariates = [
        "Age at Death",
        "Sex",
        "PMI",
        "RIN",
        "Brain pH",
        "Fresh Brain Weight",
    ]
    covariates = [c for c in candidate_covariates if c in merged.columns]
    missing = [c for c in candidate_covariates if c not in merged.columns]

    latent_cols = sorted(
        {
            str(v)
            for col in ["upgrade_best_latent", "bridge_best_latent"]
            if col in target_matrix
            for v in target_matrix[col].dropna().astype(str).tolist()
            if str(v).startswith("z_")
        },
        key=lambda z: int(z.split("_")[1]),
    )
    latent_cols = [z for z in latent_cols if z in merged.columns]

    rows = []
    for latent in latent_cols:
        z = pd.to_numeric(merged[latent], errors="coerce")
        for kind, names in [("covariate", {c: c for c in covariates}), ("pathology", target_columns)]:
            for label, col in names.items():
                if col not in merged:
                    continue
                y = merged[col]
                if y.dtype == object:
                    y = y.astype(str).str.lower().map({"female": 0.0, "male": 1.0})
                else:
                    y = pd.to_numeric(y, errors="coerce")
                valid = z.notna() & y.notna()
                if valid.sum() < 8 or y[valid].nunique() < 2:
                    continue
                rho, p = spearmanr(z[valid], y[valid])
                rows.append(
                    {
                        "latent_factor": latent,
                        "variable_type": kind,
                        "variable": label,
                        "spearman_rho": float(rho),
                        "p_value": float(p),
                        "n_donors": int(valid.sum()),
                    }
                )
    corr = pd.DataFrame(rows)
    flags = []
    for latent, group in corr.groupby("latent_factor"):
        cov = group[group["variable_type"].eq("covariate")]
        path = group[group["variable_type"].eq("pathology")]
        max_cov = float(cov["spearman_rho"].abs().max()) if not cov.empty else np.nan
        max_path = float(path["spearman_rho"].abs().max()) if not path.empty else np.nan
        flags.append(
            {
                "latent_factor": latent,
                "max_abs_covariate_rho": max_cov,
                "max_abs_pathology_rho": max_path,
                "covariate_confounded": bool(np.isfinite(max_cov) and np.isfinite(max_path) and max_cov > max_path),
                "available_covariates": ";".join(covariates),
                "missing_covariates": ";".join(missing),
            }
        )
    return corr, pd.DataFrame(flags)


def run_within_state_check(
    x: np.ndarray,
    z_base: np.ndarray,
    donors: pd.Series,
    gene_names: list[str],
    genes: list[str],
    full_gene_cf: pd.DataFrame,
    model,
    edge_index,
    node_annotations,
    embedding_space: str,
    device,
    batch_size: int,
    seed: int,
    target: str,
) -> pd.DataFrame:
    plaque = module_score(x, gene_names, "plaque_response")
    dam = module_score(x, gene_names, "disease_associated_microglia")
    state_score = 0.5 * plaque + 0.5 * dam
    threshold = float(np.quantile(state_score, 0.75))
    mask = state_score >= threshold
    if mask.sum() < 100:
        raise ValueError("Within-state mask produced too few cells.")

    x_state = x[mask]
    donors_state = donors.loc[mask].reset_index(drop=True)
    z_state = z_base[mask]
    means = x.mean(axis=0)
    donor_base = aggregate_by_donor(z_state, donors_state)
    head, scaler, donor_order, _ = fit_target_head(donor_base, target, "log1p")
    baseline_pred = predict_donor(head, scaler, donor_base, donor_order, "log1p")

    idx_by_gene = gene_indices(gene_names, genes)
    rows = []
    for gene in genes:
        idx = idx_by_gene.get(gene.upper())
        if idx is None:
            continue
        x_perturbed = apply_intervention(x_state, [idx], "global_mean", means)
        z_perturbed = encode_cells(model, x_perturbed, edge_index, node_annotations, embedding_space, device, batch_size, seed)
        donor_perturbed = aggregate_by_donor(z_perturbed, donors_state)
        perturbed_pred = predict_donor(head, scaler, donor_perturbed, donor_order, "log1p")
        merged = baseline_pred.merge(perturbed_pred, on="Donor ID", suffixes=("_baseline", "_perturbed"))
        merged["delta_raw_scale"] = merged["prediction_raw_scale_perturbed"] - merged["prediction_raw_scale_baseline"]
        within_delta = float(merged["delta_raw_scale"].mean())
        full_row = full_gene_cf[full_gene_cf["perturbation"].astype(str).str.upper().eq(gene.upper())]
        full_delta = float(full_row["mean_delta_raw_scale"].iloc[0]) if not full_row.empty else np.nan
        same_sign = bool(np.sign(within_delta) == np.sign(full_delta)) if np.isfinite(full_delta) and full_delta != 0 else False
        retained = abs(within_delta) / (abs(full_delta) + 1e-8) if np.isfinite(full_delta) else np.nan
        rows.append(
            {
                "gene": gene.upper(),
                "state_definition": "top_quartile_plaque_response_DAM_score",
                "n_state_cells": int(mask.sum()),
                "n_state_donors": int(donors_state.nunique()),
                "full_delta_raw_scale": full_delta,
                "within_state_delta_raw_scale": within_delta,
                "same_sign": same_sign,
                "effect_retention_fraction": float(retained),
                "compositional_artifact": bool((not same_sign) or (np.isfinite(retained) and retained < 0.25)),
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate v2.1 target matrix against artifact controls.")
    parser.add_argument("--checkpoint", default="results/models/stage_c_upgrade_fine_08_r0045_cov0005_pc0075/graph_jepa_stage_c_epoch_005.pt")
    parser.add_argument("--model-label", default="upgrade_fine_08")
    parser.add_argument("--h5ad", default="data/processed/sea_ad_mtg_microglia_pvm_all_hvg3k_expanded_modules.h5ad")
    parser.add_argument("--edge-csv", default="results/tables/v2_graph_string_edges_t700.csv")
    parser.add_argument("--annotation-csv", default="results/tables/jepa_v2_translational_actionability_matrix.csv")
    parser.add_argument("--target-matrix", default="results/tables/v2_1_ranked_target_matrix.csv")
    parser.add_argument("--full-gene-counterfactual", default="results/tables/v2_1_upgrade_fine_08_gene_counterfactual_at8.csv")
    parser.add_argument("--metadata", default="data/processed/metadata/sea_ad_mtg_donor_pathology_targets.csv")
    parser.add_argument("--target", default="percent AT8 positive area_Grey matter")
    parser.add_argument("--donor-column", default="Donor ID")
    parser.add_argument("--max-cells", type=int, default=12000)
    parser.add_argument("--top-n", type=int, default=10)
    parser.add_argument("--within-state-top-n", type=int, default=5)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--out-prefix", default="results/tables/v2_1_target_validation")
    args = parser.parse_args()

    device = choose_device(args.device)
    target_matrix = pd.read_csv(args.target_matrix)
    full_gene_cf = pd.read_csv(args.full_gene_counterfactual)
    top_genes = target_matrix["gene"].astype(str).str.upper().head(args.top_n).tolist()
    within_genes = target_matrix["gene"].astype(str).str.upper().head(args.within_state_top_n).tolist()

    adata_all = ad.read_h5ad(args.h5ad)
    donors_all = normalize_donor_id(adata_all.obs[args.donor_column]).reset_index(drop=True)
    rows = sample_rows_by_donor(donors_all, args.max_cells, args.seed)
    adata = adata_all[rows].copy()
    donors = normalize_donor_id(adata.obs[args.donor_column]).reset_index(drop=True)
    gene_names = adata.var_names.astype(str).tolist()
    x = to_dense_float32(adata.X)

    model, checkpoint, edge_index, node_annotations = load_graph_model(
        args.checkpoint, adata, args.edge_csv, args.annotation_csv, device
    )
    model_args = checkpoint.get("args", {})
    embedding_space = "projector" if bool(model_args.get("use_projection_head", False)) else "encoder"
    z_base = encode_cells(model, x, edge_index, node_annotations, embedding_space, device, args.batch_size, args.seed)
    donor_z = aggregate_by_donor(z_base, donors)

    alien = run_alien_cell_check(
        x, z_base, gene_names, top_genes, model, edge_index, node_annotations, embedding_space, device, args.batch_size, args.seed
    )
    cov_corr, cov_flags = run_covariate_check(donor_z, target_matrix, DISEASE_TARGETS, Path(args.metadata))
    within = run_within_state_check(
        x,
        z_base,
        donors,
        gene_names,
        within_genes,
        full_gene_cf,
        model,
        edge_index,
        node_annotations,
        embedding_space,
        device,
        args.batch_size,
        args.seed,
        args.target,
    )

    validated = target_matrix.copy()
    validated["gene"] = validated["gene"].astype(str).str.upper()
    validated = validated.merge(alien[["gene", "manifold_violation", "violation_fraction"]], on="gene", how="left")
    validated["alien_cell_checked"] = validated["manifold_violation"].notna()
    latent_flag_map = cov_flags.set_index("latent_factor")["covariate_confounded"].to_dict()
    validated["upgrade_latent_covariate_confounded"] = validated["upgrade_best_latent"].map(latent_flag_map)
    validated["bridge_latent_covariate_confounded"] = validated["bridge_best_latent"].map(latent_flag_map)
    validated["covariate_checked"] = validated["upgrade_latent_covariate_confounded"].notna() | validated[
        "bridge_latent_covariate_confounded"
    ].notna()
    validated = validated.merge(within[["gene", "compositional_artifact", "within_state_delta_raw_scale", "effect_retention_fraction"]], on="gene", how="left")
    validated["within_state_checked"] = validated["compositional_artifact"].notna()
    validated["validation_flag_count"] = validated[
        ["manifold_violation", "upgrade_latent_covariate_confounded", "bridge_latent_covariate_confounded", "compositional_artifact"]
    ].fillna(False).astype(bool).sum(axis=1)
    validated["validation_checks_completed"] = (
        validated[["alien_cell_checked", "covariate_checked", "within_state_checked"]].astype(bool).sum(axis=1)
    )
    validated["validation_tier"] = np.select(
        [
            validated["validation_flag_count"].eq(0) & validated["validation_checks_completed"].eq(3),
            validated["validation_flag_count"].eq(0) & validated["validation_checks_completed"].between(1, 2),
            validated["validation_flag_count"].eq(1),
        ],
        ["passes_current_controls", "partial_controls_passed", "caution_one_flag"],
        default="downgrade_or_not_tested",
    )

    prefix = Path(args.out_prefix)
    prefix.parent.mkdir(parents=True, exist_ok=True)
    alien.to_csv(prefix.with_name(prefix.name + "_alien_cell_check.csv"), index=False)
    cov_corr.to_csv(prefix.with_name(prefix.name + "_covariate_correlations.csv"), index=False)
    cov_flags.to_csv(prefix.with_name(prefix.name + "_covariate_flags.csv"), index=False)
    within.to_csv(prefix.with_name(prefix.name + "_within_state_check.csv"), index=False)
    validated.to_csv(prefix.with_name(prefix.name + "_validated_target_matrix.csv"), index=False)
    available_covariates = "none"
    missing_covariates = "none"
    if not cov_flags.empty:
        available_values = sorted(
            {
                covariate
                for value in cov_flags["available_covariates"].dropna().astype(str)
                for covariate in value.split(";")
                if covariate
            }
        )
        missing_values = sorted(
            {
                covariate
                for value in cov_flags["missing_covariates"].dropna().astype(str)
                for covariate in value.split(";")
                if covariate
            }
        )
        available_covariates = ", ".join(available_values) if available_values else "none"
        missing_covariates = ", ".join(missing_values) if missing_values else "none"
    report_path = prefix.with_name(prefix.name + "_report.md")
    report_path.write_text(
        "\n".join(
            [
                "# v2.1 Target Matrix Artifact Validation",
                "",
                "This report stress-tests the v2.1 ranked target matrix before accepting model-implied counterfactual hypotheses.",
                "",
                "## Alien Cell Check",
                "",
                "Top-10 gene perturbations were embedded and compared with the nearest real, unperturbed cell in latent space. A target is flagged if more than 5% of perturbed cells exceed the 95th percentile of normal nearest-neighbor distances.",
                "",
                f"- Normal nearest-neighbor 95th percentile: {alien['normal_nn_distance_p95'].dropna().iloc[0]:.6f}",
                f"- Manifold violations: {int(alien['manifold_violation'].fillna(False).sum())} / {alien.shape[0]} tested genes",
                "",
                "## Covariate Confounder Check",
                "",
                "Donor-level latent factors were correlated with available nuisance covariates and pathology targets.",
                "",
                f"- Available nuisance covariates: {available_covariates}",
                f"- Missing nuisance covariates: {missing_covariates}",
                f"- Covariate-confounded latent factors: {int(cov_flags['covariate_confounded'].sum())} / {cov_flags.shape[0]} tested factors",
                "",
                "## Within-State Compositional Artifact Check",
                "",
                "Top-5 gene perturbations were rerun only on cells in the top quartile of plaque-response/DAM module score. A target is flagged if its sign flips or less than 25% of the full effect remains.",
                "",
                f"- Compositional artifacts: {int(within['compositional_artifact'].sum())} / {within.shape[0]} tested genes",
                "",
                "## Validated Matrix Tiers",
                "",
                validated["validation_tier"].value_counts(dropna=False).to_string(),
                "",
                "## Recommendation",
                "",
                "Targets passing all current controls remain hypotheses, not causal facts. The next validation step is independent external cohort or perturbation validation.",
            ]
        ),
        encoding="utf-8",
    )
    print("Alien cell check:")
    print(alien.to_string(index=False))
    print("\nCovariate flags:")
    print(cov_flags.to_string(index=False))
    print("\nWithin-state check:")
    print(within.to_string(index=False))
    print("\nValidated target matrix:")
    print(validated.head(15).to_string(index=False))


if __name__ == "__main__":
    main()
