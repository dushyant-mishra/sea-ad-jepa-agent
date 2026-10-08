from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import torch
from scipy import sparse
from scipy.stats import spearmanr
from sklearn.metrics import roc_auc_score

from graph_counterfactual_knockout import choose_device, load_graph_model
from project_external_ad_microglia import (
    build_sea_ad_trajectories,
    encode_external,
    load_anchor_mean,
    markdown_table,
    sea_ad_control_centroid,
)


MAIN_TRAJECTORY = "trajectory_AT8/pTau_score"


def stage_to_numeric(value: object) -> float:
    match = re.search(r"(\d+)", str(value))
    return float(match.group(1)) if match else float("nan")


def read_matrix_h5(path: Path):
    import scanpy as sc

    adata = sc.read_10x_h5(path)
    adata.var_names_make_unique()
    return adata


def build_obs_match(meta: pd.DataFrame, adata_obs_names: pd.Index) -> tuple[pd.DataFrame, list[str], dict[str, object]]:
    obs_names = pd.Index(adata_obs_names.astype(str))
    obs_set = set(obs_names)
    candidates: list[tuple[str, pd.Series]] = [
        ("Barcode", meta["Barcode"].astype(str)),
        ("SampleID_Barcode", meta["SampleID"].astype(str) + "_" + meta["Barcode"].astype(str)),
        ("SampleID:Barcode", meta["SampleID"].astype(str) + ":" + meta["Barcode"].astype(str)),
        ("SampleID-Barcode", meta["SampleID"].astype(str) + "-" + meta["Barcode"].astype(str)),
        ("Barcode_SampleID", meta["Barcode"].astype(str) + "_" + meta["SampleID"].astype(str)),
    ]
    best_name = ""
    best_values: pd.Series | None = None
    best_hits = -1
    for name, values in candidates:
        hits = values.isin(obs_set).sum()
        if hits > best_hits:
            best_name = name
            best_values = values
            best_hits = int(hits)
    if best_values is None or best_hits == 0:
        preview = ", ".join(obs_names[:10].tolist())
        raise ValueError(
            "Could not match GSE174367 metadata barcodes to count matrix barcodes. "
            f"First matrix barcodes: {preview}"
        )

    out = meta.copy()
    out["matrix_barcode"] = best_values
    out = out[out["matrix_barcode"].isin(obs_set)].copy()
    if out["matrix_barcode"].duplicated().any():
        out = out.drop_duplicates("matrix_barcode", keep="first").copy()
    return out, out["matrix_barcode"].tolist(), {
        "barcode_match_strategy": best_name,
        "n_metadata_rows_after_match": int(len(out)),
        "n_matrix_obs": int(len(obs_names)),
    }


def align_gse174367_matrix(
    matrix_h5: Path,
    metadata_csv: Path,
    jepa_genes: list[str],
    impute_values: np.ndarray,
    max_cells: int,
    seed: int,
) -> tuple[np.ndarray, pd.DataFrame, dict[str, object]]:
    meta = pd.read_csv(metadata_csv)
    mg = meta[meta["Cell.Type"].astype(str).eq("MG")].copy()
    mg["condition"] = mg["Diagnosis"].astype(str).replace({"Control": "Control", "AD": "AD"})
    mg["external_donor_id"] = mg["SampleID"].astype(str)
    mg["tangle_stage_numeric"] = mg["Tangle.Stage"].map(stage_to_numeric)
    mg["plaque_stage_numeric"] = mg["Plaque.Stage"].map({"Stage A": 1.0, "Stage B": 2.0, "Stage C": 3.0})
    if max_cells > 0 and len(mg) > max_cells:
        mg = mg.sample(n=max_cells, random_state=seed).sort_index()

    adata = read_matrix_h5(matrix_h5)
    mg, barcodes, match_qc = build_obs_match(mg, adata.obs_names)
    adata = adata[barcodes, :].copy()

    gene_to_source: dict[str, int] = {}
    for idx, gene in enumerate(adata.var_names.astype(str)):
        gene_to_source.setdefault(gene.upper(), idx)

    matched_pairs: list[tuple[int, int]] = []
    missing: list[str] = []
    for out_idx, gene in enumerate(jepa_genes):
        src_idx = gene_to_source.get(str(gene).upper())
        if src_idx is None:
            missing.append(gene)
        else:
            matched_pairs.append((out_idx, src_idx))

    matched_src = [src for _, src in matched_pairs]
    matched_out = [out for out, _ in matched_pairs]
    x_counts = np.zeros((adata.n_obs, len(jepa_genes)), dtype=np.float32)
    if matched_src:
        sub = adata.X[:, matched_src]
        if sparse.issparse(sub):
            sub = sub.toarray()
        x_counts[:, matched_out] = np.asarray(sub, dtype=np.float32)

    totals = x_counts[:, matched_out].sum(axis=1) if matched_out else np.ones(adata.n_obs, dtype=np.float32)
    totals = np.asarray(totals, dtype=np.float32)
    totals[totals <= 0] = 1.0
    x = np.log1p(x_counts * (10000.0 / totals[:, None])).astype(np.float32)
    if missing:
        missing_idx = [idx for idx, gene in enumerate(jepa_genes) if gene in set(missing)]
        x[:, missing_idx] = impute_values[missing_idx][None, :]

    qc = {
        "n_cells_before_filter": int(meta.shape[0]),
        "n_microglia_before_match": int((meta["Cell.Type"].astype(str) == "MG").sum()),
        "n_cells_after_filter": int(x.shape[0]),
        "n_external_groups": int(mg["external_donor_id"].nunique()),
        "n_jepa_genes": int(len(jepa_genes)),
        "n_matched_genes": int(len(matched_pairs)),
        "n_missing_genes": int(len(missing)),
        "gene_overlap_fraction": float(len(matched_pairs) / max(len(jepa_genes), 1)),
        "missing_gene_imputation": "sea_ad_low_pathology_mean",
        **match_qc,
    }
    return x, mg.reset_index(drop=True), qc


def cell_embedding_frame(z: np.ndarray, obs: pd.DataFrame) -> pd.DataFrame:
    z_cols = [f"z_{i}" for i in range(z.shape[1])]
    z_frame = pd.DataFrame(z, columns=z_cols)
    return pd.concat([obs.reset_index(drop=True).copy(), z_frame], axis=1)


def control_centroid_shift_for_cells(
    cell_z: pd.DataFrame,
    sea_control: np.ndarray,
) -> tuple[pd.DataFrame, dict[str, object]]:
    z_cols = [c for c in cell_z.columns if c.startswith("z_")]
    out = cell_z.copy()
    donor_z = out.groupby(["external_donor_id", "condition"], as_index=False)[z_cols].mean()
    controls = donor_z[donor_z["condition"].eq("Control")]
    if controls.empty:
        return out, {"control_centroid_shift_applied": False, "control_centroid_shift_l2": float("nan")}
    external_control = controls[z_cols].to_numpy(dtype=np.float32).mean(axis=0)
    shift = sea_control.astype(np.float32) - external_control
    out[z_cols] = out[z_cols].to_numpy(dtype=np.float32) + shift[None, :]
    return out, {"control_centroid_shift_applied": True, "control_centroid_shift_l2": float(np.linalg.norm(shift))}


def score_cell_trajectories(cell_z: pd.DataFrame, trajectories: pd.DataFrame) -> pd.DataFrame:
    z_cols = [c for c in cell_z.columns if c.startswith("z_")]
    out = cell_z.copy()
    z = out[z_cols].to_numpy(dtype=np.float32)
    for _, row in trajectories.iterrows():
        direction = row[z_cols].to_numpy(dtype=np.float32)
        out[f"trajectory_{row['trajectory']}_score"] = z @ direction
    return out


def donor_average(cell_scores: pd.DataFrame) -> pd.DataFrame:
    score_cols = [c for c in cell_scores.columns if c.startswith("trajectory_") and c.endswith("_score")]
    meta_cols = [
        "external_donor_id",
        "condition",
        "Diagnosis",
        "Age",
        "Sex",
        "PMI",
        "RIN",
        "Batch",
        "Tangle.Stage",
        "Plaque.Stage",
        "tangle_stage_numeric",
        "plaque_stage_numeric",
    ]
    meta = cell_scores[meta_cols].drop_duplicates("external_donor_id").set_index("external_donor_id")
    grouped = cell_scores.groupby("external_donor_id")[score_cols].mean()
    grouped.insert(0, "n_cells", cell_scores.groupby("external_donor_id").size())
    return grouped.join(meta).reset_index()


def spearman_table(donor_scores: pd.DataFrame) -> pd.DataFrame:
    rows = []
    score_cols = [c for c in donor_scores.columns if c.startswith("trajectory_") and c.endswith("_score")]
    for score in score_cols:
        for outcome in ["tangle_stage_numeric", "plaque_stage_numeric"]:
            valid = donor_scores[[score, outcome]].dropna()
            rho, pvalue = spearmanr(valid[score], valid[outcome]) if len(valid) >= 4 else (np.nan, np.nan)
            rows.append(
                {
                    "score": score,
                    "outcome": outcome,
                    "n_donors": int(len(valid)),
                    "spearman_rho": float(rho),
                    "spearman_p": float(pvalue),
                }
            )
    return pd.DataFrame(rows).sort_values(["outcome", "spearman_rho"], ascending=[True, False])


def loo_stability(donor_scores: pd.DataFrame, score_col: str = MAIN_TRAJECTORY) -> pd.DataFrame:
    rows = []
    valid = donor_scores[["external_donor_id", score_col, "tangle_stage_numeric"]].dropna()
    for donor in valid["external_donor_id"]:
        subset = valid[valid["external_donor_id"] != donor]
        rho, pvalue = spearmanr(subset[score_col], subset["tangle_stage_numeric"])
        rows.append(
            {
                "held_out_donor": donor,
                "n_donors": int(len(subset)),
                "spearman_rho": float(rho),
                "spearman_p": float(pvalue),
            }
        )
    return pd.DataFrame(rows).sort_values("spearman_rho")


def covariate_audit(cell_scores: pd.DataFrame, donor_scores: pd.DataFrame, score_col: str = MAIN_TRAJECTORY) -> pd.DataFrame:
    rows = []
    for level, df in [("cell", cell_scores), ("donor", donor_scores)]:
        for covariate in ["Age", "PMI", "RIN", "Batch"]:
            valid = df[[score_col, covariate]].dropna()
            if len(valid) < 4 or valid[covariate].nunique() < 2:
                rho, pvalue = np.nan, np.nan
            else:
                rho, pvalue = spearmanr(valid[score_col], valid[covariate])
            rows.append(
                {
                    "level": level,
                    "score": score_col,
                    "covariate": covariate,
                    "n": int(len(valid)),
                    "spearman_rho": float(rho),
                    "spearman_p": float(pvalue),
                }
            )
    return pd.DataFrame(rows)


def rank_biserial(disease: np.ndarray, control: np.ndarray) -> float:
    if disease.size == 0 or control.size == 0:
        return float("nan")
    combined = pd.Series(np.concatenate([disease, control])).rank(method="average").to_numpy(dtype=float)
    r_disease = combined[: disease.size].sum()
    u_disease = r_disease - disease.size * (disease.size + 1) / 2.0
    return float((2.0 * u_disease / (disease.size * control.size)) - 1.0)


def transition_boundary_table(donor_scores: pd.DataFrame) -> pd.DataFrame:
    rows = []
    score_cols = [c for c in donor_scores.columns if c.startswith("trajectory_") and c.endswith("_score")]
    stage = donor_scores["tangle_stage_numeric"]
    boundary = donor_scores[stage.isin([1.0, 2.0, 5.0, 6.0])].copy()
    boundary["late_tangle"] = boundary["tangle_stage_numeric"].isin([5.0, 6.0]).astype(int)
    for score in score_cols:
        valid = boundary[[score, "late_tangle"]].dropna()
        if valid["late_tangle"].nunique() < 2:
            auc = effect = late_mean = early_mean = float("nan")
            n_early = n_late = 0
        else:
            late = valid.loc[valid["late_tangle"].eq(1), score].to_numpy(dtype=float)
            early = valid.loc[valid["late_tangle"].eq(0), score].to_numpy(dtype=float)
            auc = float(roc_auc_score(valid["late_tangle"], valid[score]))
            effect = rank_biserial(late, early)
            late_mean = float(np.mean(late))
            early_mean = float(np.mean(early))
            n_late = int(late.size)
            n_early = int(early.size)
        rows.append(
            {
                "score": score,
                "comparison": "tangle_stage_1_2_vs_5_6",
                "n_early_donors": n_early,
                "n_late_donors": n_late,
                "auc_late_vs_early": auc,
                "rank_biserial_late_minus_early": effect,
                "late_mean": late_mean,
                "early_mean": early_mean,
                "mean_difference_late_minus_early": late_mean - early_mean if np.isfinite(late_mean) and np.isfinite(early_mean) else float("nan"),
            }
        )
    return pd.DataFrame(rows).sort_values("auc_late_vs_early", ascending=False)


def plot_violin(cell_scores: pd.DataFrame, donor_scores: pd.DataFrame, out_path: Path, score_col: str = MAIN_TRAJECTORY) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    order = ["Stage 1", "Stage 2", "Stage 5", "Stage 6"]
    fig, ax = plt.subplots(figsize=(9.5, 5.5))
    sns.violinplot(
        data=cell_scores,
        x="Tangle.Stage",
        y=score_col,
        hue="Tangle.Stage",
        order=order,
        hue_order=order,
        inner="quartile",
        linewidth=0.8,
        cut=0,
        palette=["#6fa8dc", "#93c47d", "#f6b26b", "#cc0000"],
        legend=False,
        ax=ax,
    )
    sns.stripplot(
        data=donor_scores,
        x="Tangle.Stage",
        y=score_col,
        order=order,
        color="black",
        size=5,
        jitter=0.12,
        ax=ax,
    )
    ax.set_title("Frozen Graph-JEPA AT8 Trajectory in GSE174367 Microglia", weight="bold")
    ax.set_xlabel("Morabito tangle stage")
    ax.set_ylabel("SEA-AD AT8/pTau trajectory score")
    ax.text(
        0.01,
        -0.22,
        "Violin: cell-level microglia distribution. Black dots: donor means. Stages 3-4 are absent in this cohort.",
        transform=ax.transAxes,
        fontsize=9,
        color="#333333",
    )
    fig.tight_layout()
    fig.savefig(out_path, dpi=220)
    if out_path.suffix.lower() != ".svg":
        fig.savefig(out_path.with_suffix(".svg"))
    plt.close(fig)


def write_report(
    report_path: Path,
    qc: dict[str, object],
    corr: pd.DataFrame,
    loo: pd.DataFrame,
    covariates: pd.DataFrame,
    transition: pd.DataFrame,
    figure_path: Path,
) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    main_corr = corr[(corr["score"] == MAIN_TRAJECTORY) & (corr["outcome"] == "tangle_stage_numeric")]
    loo_summary = {
        "mean_rho": float(loo["spearman_rho"].mean()) if not loo.empty else float("nan"),
        "min_rho": float(loo["spearman_rho"].min()) if not loo.empty else float("nan"),
        "max_rho": float(loo["spearman_rho"].max()) if not loo.empty else float("nan"),
    }
    try:
        figure_link = Path("../figures") / figure_path.with_suffix(".svg").name
    except Exception:
        figure_link = figure_path
    report_path.write_text(
        "\n".join(
            [
                "# GSE174367 Morabito External Validation",
                "",
                "This analysis projects Morabito et al. GSE174367 microglia through the frozen SEA-AD Graph-JEPA v2.1 encoder (`upgrade_fine_08`). It treats the missing Braak/tangle stages 3-4 as a state-transition boundary, so the primary interpretation is early-stage versus late-stage tau pathology rather than a smooth continuous trajectory.",
                "",
                "## Projection Setup",
                "",
                f"- projected microglia: `{qc['n_cells_after_filter']}`",
                f"- donors/samples: `{qc['n_external_groups']}`",
                f"- matched genes: `{qc['n_matched_genes']} / {qc['n_jepa_genes']}`",
                f"- missing genes imputed from SEA-AD low-pathology anchor: `{qc['n_missing_genes']}`",
                f"- barcode match strategy: `{qc['barcode_match_strategy']}`",
                f"- control-centroid shift applied: `{qc['control_centroid_shift_applied']}`",
                f"- control-centroid shift L2: `{qc['control_centroid_shift_l2']:.4f}`",
                "",
                "## Cell-Level Distribution",
                "",
                f"![AT8 trajectory by tangle stage]({figure_link.as_posix()})",
                "",
                "## Donor-Level Ordinal Correlations",
                "",
                markdown_table(corr, max_rows=20),
                "",
                "## Leave-One-Donor-Out Stability",
                "",
                f"- mean rho: `{loo_summary['mean_rho']:.4f}`",
                f"- min rho: `{loo_summary['min_rho']:.4f}`",
                f"- max rho: `{loo_summary['max_rho']:.4f}`",
                "",
                markdown_table(loo, max_rows=20),
                "",
                "## Early-Versus-Late Transition Boundary",
                "",
                "Because stages 3-4 are absent, this table treats Morabito as an early-versus-late tangle-state boundary test.",
                "",
                markdown_table(transition, max_rows=20),
                "",
                "## Covariate Audit",
                "",
                markdown_table(covariates, max_rows=20),
                "",
                "## Interpretation Boundary",
                "",
                "This is external observational validation, not perturbational causal proof. Because GSE174367 contains tangle stages 1, 2, 5, and 6 but not 3 or 4, positive trajectory separation supports cross-cohort early-versus-late tau-state transfer. It should not be over-described as continuous Braak-stage tracking unless intermediate-stage cohorts reproduce the same monotonic relationship.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Project GSE174367 Morabito microglia through frozen Graph-JEPA and audit tau-stage transfer.")
    parser.add_argument("--matrix-h5", default="data/external/gse174367/GSE174367_snRNA-seq_filtered_feature_bc_matrix.h5")
    parser.add_argument("--metadata-csv", default="data/external/gse174367/GSE174367_snRNA-seq_cell_meta.csv.gz")
    parser.add_argument("--checkpoint", default="results/models/stage_c_upgrade_fine_08_r0045_cov0005_pc0075/graph_jepa_stage_c_epoch_005.pt")
    parser.add_argument("--local-h5ad", default="data/processed/sea_ad_mtg_microglia_pvm_all_hvg3k_expanded_modules.h5ad")
    parser.add_argument("--edge-csv", default="results/tables/v2_graph_string_edges_t700.csv")
    parser.add_argument("--annotation-csv", default="results/tables/jepa_v2_translational_actionability_matrix.csv")
    parser.add_argument("--sea-donor-embeddings", default="results/tables/stage_c_upgrade_fine_08_r0045_cov0005_pc0075_epoch_005_donor_embeddings.csv")
    parser.add_argument("--sea-anchor-h5ad", default="data/processed/v2_pretraining/sea_ad_low_pathology_microglia_pvm_relaxed_jepa_aligned.h5ad")
    parser.add_argument("--embedding-space", choices=["auto", "encoder", "projector"], default="auto")
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--max-cells", type=int, default=0)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--out-prefix", default="results/tables/v2_1_gse174367")
    parser.add_argument("--figure-out", default="results/figures/v2_1_gse174367_at8_trajectory_by_tangle.png")
    parser.add_argument("--report-out", default="results/reports/external_validation_gse174367.md")
    args = parser.parse_args()

    device = choose_device(args.device)
    import anndata as ad

    adata_ref = ad.read_h5ad(args.local_h5ad, backed="r")
    jepa_genes = adata_ref.var_names.astype(str).tolist()
    model, checkpoint, edge_index, node_annotations = load_graph_model(
        args.checkpoint,
        adata_ref,
        args.edge_csv,
        args.annotation_csv,
        device,
    )
    for parameter in model.parameters():
        parameter.requires_grad_(False)
    model.eval()
    if any(parameter.requires_grad for parameter in model.parameters()):
        raise RuntimeError("Strict freeze failed: at least one model parameter still requires gradients.")

    checkpoint_args = checkpoint.get("args", {})
    embedding_space = args.embedding_space
    if embedding_space == "auto":
        embedding_space = str(checkpoint_args.get("downstream_embedding_space", "projector" if checkpoint_args.get("use_projection_head") else "encoder"))

    impute_values = load_anchor_mean(Path(args.sea_anchor_h5ad), jepa_genes)
    x, obs, qc = align_gse174367_matrix(
        Path(args.matrix_h5),
        Path(args.metadata_csv),
        jepa_genes,
        impute_values=impute_values,
        max_cells=args.max_cells,
        seed=args.seed,
    )
    z = encode_external(model, x, edge_index, node_annotations, embedding_space, device, args.batch_size, args.seed)
    cell_z = cell_embedding_frame(z, obs)
    cell_z, shift_qc = control_centroid_shift_for_cells(cell_z, sea_ad_control_centroid(Path(args.sea_donor_embeddings)))
    qc.update(shift_qc)
    qc["embedding_space"] = embedding_space
    trajectories = build_sea_ad_trajectories(Path(args.sea_donor_embeddings))
    cell_scores = score_cell_trajectories(cell_z, trajectories)
    donor_scores = donor_average(cell_scores)
    corr = spearman_table(donor_scores)
    loo = loo_stability(donor_scores)
    covariates = covariate_audit(cell_scores, donor_scores)
    transition = transition_boundary_table(donor_scores)

    prefix = Path(args.out_prefix)
    prefix.parent.mkdir(parents=True, exist_ok=True)
    figure_path = Path(args.figure_out)
    plot_violin(cell_scores, donor_scores, figure_path)

    cell_scores.drop(columns=[c for c in cell_scores.columns if c.startswith("z_")]).to_csv(prefix.with_name(prefix.name + "_cell_trajectory_scores.csv"), index=False)
    donor_scores.to_csv(prefix.with_name(prefix.name + "_donor_trajectory_scores.csv"), index=False)
    corr.to_csv(prefix.with_name(prefix.name + "_trajectory_correlations.csv"), index=False)
    loo.to_csv(prefix.with_name(prefix.name + "_loo_stability.csv"), index=False)
    covariates.to_csv(prefix.with_name(prefix.name + "_covariate_audit.csv"), index=False)
    transition.to_csv(prefix.with_name(prefix.name + "_transition_boundary_auc.csv"), index=False)
    trajectories.to_csv(prefix.with_name(prefix.name + "_sea_ad_trajectory_vectors.csv"), index=False)
    pd.DataFrame([qc]).to_csv(prefix.with_name(prefix.name + "_projection_qc.csv"), index=False)
    write_report(Path(args.report_out), qc, corr, loo, covariates, transition, figure_path)

    print("Projection QC:")
    print(pd.DataFrame([qc]).to_string(index=False))
    print("\nTrajectory correlations:")
    print(corr.to_string(index=False))
    print("\nLOO stability:")
    print(loo.to_string(index=False))
    print("\nCovariate audit:")
    print(covariates.to_string(index=False))
    print("\nTransition boundary AUC:")
    print(transition.to_string(index=False))
    print(f"\nWrote {prefix.with_name(prefix.name + '_trajectory_correlations.csv')}")
    print(f"Wrote {args.report_out}")


if __name__ == "__main__":
    main()
