from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import anndata as ad
import numpy as np
import pandas as pd
import torch
from scipy import sparse
from scipy.stats import pearsonr, spearmanr
from sklearn.decomposition import PCA
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import KFold
from sklearn.preprocessing import StandardScaler

from sea_ad_jepa.data import normalize_donor_id
from sea_ad_jepa.gene_sets import MICROGLIA_GENE_MODULES
from sea_ad_jepa.graph_data import load_consensus_edge_index
from scripts.pathology_head_counterfactual_knockout import (
    encode_matrix,
    infer_fast_model,
)
from scripts.train_graph_jepa_stage_a_fast import choose_device, normalized_adjacency


DEFAULT_H5AD = Path(
    "data/processed/sea_ad_mtg_microglia_pvm_all_hvg3k_expanded_modules.h5ad"
)
DEFAULT_METADATA = Path(
    "data/processed/metadata/sea_ad_mtg_donor_pathology_targets.csv"
)
DEFAULT_CHECKPOINT = Path(
    "results/models/v2_2_stage_b_adversarial/stage_b_adversarial.pt"
)
DEFAULT_EDGE_INDEX = Path("results/tables/v2_graph_consensus_edge_index.csv")
DEFAULT_GRAPH_EDGES = Path("results/tables/v2_graph_consensus_edges.csv")
DEFAULT_SCORECARD = Path(
    "results/tables/discovery_scorecard_v2_graph_connected_feature_wide.csv"
)
DEFAULT_SHORTLIST = Path("results/tables/discovery_final_candidate_shortlist_v3.csv")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Graph-JEPA baseline gate.")
    parser.add_argument("--h5ad", type=Path, default=DEFAULT_H5AD)
    parser.add_argument("--metadata", type=Path, default=DEFAULT_METADATA)
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--edge-index", type=Path, default=DEFAULT_EDGE_INDEX)
    parser.add_argument("--graph-edges", type=Path, default=DEFAULT_GRAPH_EDGES)
    parser.add_argument("--scorecard", type=Path, default=DEFAULT_SCORECARD)
    parser.add_argument("--shortlist", type=Path, default=DEFAULT_SHORTLIST)
    parser.add_argument("--batch-size", type=int, default=512)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--seed", type=int, default=23)
    parser.add_argument(
        "--predictive-out",
        type=Path,
        default=Path(
            "results/tables/discovery_baseline_predictive_representation_comparison.csv"
        ),
    )
    parser.add_argument(
        "--ranking-out",
        type=Path,
        default=Path(
            "results/tables/discovery_baseline_discovery_ranking_comparison.csv"
        ),
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("results/reports/discovery_baseline_comparison_gate.md"),
    )
    return parser.parse_args()


def safe_corr(x: np.ndarray, y: np.ndarray, method: str) -> float:
    if len(x) < 3 or np.std(x) == 0 or np.std(y) == 0:
        return np.nan
    return float(pearsonr(x, y).statistic if method == "pearson" else spearmanr(x, y).statistic)


def load_donor_matrices(
    h5ad_path: Path, metadata_path: Path
) -> tuple[pd.DataFrame, np.ndarray, list[str], pd.DataFrame]:
    adata = ad.read_h5ad(h5ad_path)
    x = adata.X.toarray() if sparse.issparse(adata.X) else np.asarray(adata.X)
    x = np.asarray(x, dtype=np.float32)
    genes = adata.var_names.astype(str).str.upper().tolist()
    donors = normalize_donor_id(adata.obs["Donor ID"]).reset_index(drop=True)
    donor_order = sorted(donors.unique())
    donor_expression = np.vstack(
        [x[donors.to_numpy() == donor].mean(axis=0) for donor in donor_order]
    ).astype(np.float32)
    expression = pd.DataFrame(donor_expression, index=donor_order, columns=genes)

    metadata = pd.read_csv(metadata_path)
    metadata["Donor ID"] = normalize_donor_id(metadata["Donor ID"])
    metadata = metadata.drop_duplicates("Donor ID").set_index("Donor ID")
    common = expression.index.intersection(metadata.index)
    expression = expression.loc[common]
    metadata = metadata.loc[common]
    return expression, x, genes, metadata


def graph_jepa_donor_latent(
    x_cells: np.ndarray,
    genes: list[str],
    donor_ids: pd.Series,
    selected_donors: list[str],
    checkpoint_path: Path,
    edge_index_path: Path,
    device: torch.device,
    batch_size: int,
) -> np.ndarray:
    checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
    model = infer_fast_model(checkpoint).to(device)
    edge_index = load_consensus_edge_index(edge_index_path)
    adj = normalized_adjacency(edge_index, len(genes), 0.0, device)
    latent = encode_matrix(
        model, torch.from_numpy(x_cells), adj, device, batch_size
    )
    donors_array = donor_ids.to_numpy()
    return np.vstack(
        [latent[donors_array == donor].mean(axis=0) for donor in selected_donors]
    ).astype(np.float32)


def module_matrix(expression: pd.DataFrame) -> np.ndarray:
    gene_set = set(expression.columns)
    columns = []
    for module in sorted(MICROGLIA_GENE_MODULES):
        present = sorted(
            gene for gene in MICROGLIA_GENE_MODULES[module] if gene.upper() in gene_set
        )
        if present:
            columns.append(expression[present].mean(axis=1).to_numpy())
    if not columns:
        raise ValueError("No module genes overlap the expression feature space")
    return np.column_stack(columns).astype(np.float32)


def fold_predict(
    representation: str,
    x: np.ndarray,
    y: np.ndarray,
    train: np.ndarray,
    test: np.ndarray,
) -> np.ndarray:
    scaler = StandardScaler()
    x_train = scaler.fit_transform(x[train])
    x_test = scaler.transform(x[test])
    if representation == "pca_expression_baseline":
        n_components = min(128, x_train.shape[0] - 1, x_train.shape[1])
        pca = PCA(n_components=n_components, random_state=0)
        x_train = pca.fit_transform(x_train)
        x_test = pca.transform(x_test)
    alpha = 100.0 if representation == "raw_expression_regularized_baseline" else 10.0
    model = Ridge(alpha=alpha)
    model.fit(x_train, y[train])
    return model.predict(x_test)


def predictive_comparison(
    representations: dict[str, np.ndarray],
    targets: pd.DataFrame,
    seed: int,
) -> pd.DataFrame:
    splitter = KFold(n_splits=5, shuffle=True, random_state=seed)
    rows = []
    for representation, x in representations.items():
        for target in targets.columns:
            y = targets[target].to_numpy(dtype=np.float64)
            valid = np.isfinite(y)
            xv = x[valid]
            yv = y[valid]
            fold_metrics = []
            oof = np.full(len(yv), np.nan)
            for fold, (train, test) in enumerate(splitter.split(xv), start=1):
                pred = fold_predict(representation, xv, yv, train, test)
                oof[test] = pred
                fold_metrics.append(
                    {
                        "r2": r2_score(yv[test], pred),
                        "pearson": safe_corr(yv[test], pred, "pearson"),
                        "spearman": safe_corr(yv[test], pred, "spearman"),
                        "mae": mean_absolute_error(yv[test], pred),
                        "rmse": mean_squared_error(yv[test], pred) ** 0.5,
                    }
                )
            metrics = pd.DataFrame(fold_metrics)
            rows.append(
                {
                    "representation": representation,
                    "target": target,
                    "n_donors": len(yv),
                    "cv_scheme": "5_fold_donor_cv",
                    "r2_mean": metrics["r2"].mean(),
                    "r2_std": metrics["r2"].std(ddof=0),
                    "pearson_mean": metrics["pearson"].mean(),
                    "spearman_mean": metrics["spearman"].mean(),
                    "mae_mean": metrics["mae"].mean(),
                    "rmse_mean": metrics["rmse"].mean(),
                    "oof_pearson": safe_corr(yv, oof, "pearson"),
                    "oof_spearman": safe_corr(yv, oof, "spearman"),
                    "status": "tested",
                    "notes": "Identical donor folds and ridge readout across available representations.",
                }
            )
    for unavailable in ["shuffled_graph_jepa", "no_graph_jepa", "expression_only_autoencoder"]:
        for target in targets.columns:
            rows.append(
                {
                    "representation": unavailable,
                    "target": target,
                    "n_donors": len(targets),
                    "cv_scheme": "not_run",
                    "r2_mean": np.nan,
                    "r2_std": np.nan,
                    "pearson_mean": np.nan,
                    "spearman_mean": np.nan,
                    "mae_mean": np.nan,
                    "rmse_mean": np.nan,
                    "oof_pearson": np.nan,
                    "oof_spearman": np.nan,
                    "status": "not_available_existing_artifact",
                    "notes": "No existing trained artifact found; no model was trained for this gate.",
                }
            )
    return pd.DataFrame(rows)


def percentile(values: pd.Series) -> pd.Series:
    return values.rank(method="average", pct=True) * 100.0


def discovery_rankings(
    expression: pd.DataFrame,
    targets: pd.DataFrame,
    scorecard: pd.DataFrame,
    shortlist: pd.DataFrame,
    graph_edges: Path,
    seed: int,
) -> pd.DataFrame:
    genes = scorecard["gene"].astype(str).str.upper()
    scorecard = scorecard.copy()
    scorecard["gene"] = genes
    disease = pd.DataFrame(index=targets.index)
    for column in targets.columns:
        values = targets[column].astype(float)
        standardized = (values - values.mean()) / values.std(ddof=0)
        disease[column] = -standardized if "NeuN" in column else standardized
    composite = disease.mean(axis=1)

    correlation_scores = {}
    de_scores = {}
    high = composite >= composite.quantile(0.75)
    low = composite <= composite.quantile(0.25)
    for gene in genes:
        if gene not in expression.columns:
            correlation_scores[gene] = np.nan
            de_scores[gene] = np.nan
            continue
        values = expression[gene].to_numpy(dtype=float)
        correlation_scores[gene] = safe_corr(
            values, composite.to_numpy(dtype=float), "spearman"
        )
        pooled_sd = np.std(values, ddof=0)
        de_scores[gene] = (
            (values[high] .mean() - values[low].mean()) / pooled_sd
            if pooled_sd > 0
            else 0.0
        )

    edges = pd.read_csv(graph_edges, usecols=["source", "target"])
    degree = pd.concat(
        [
            edges["source"].astype(str).str.upper(),
            edges["target"].astype(str).str.upper(),
        ]
    ).value_counts()
    membership = {
        gene: sum(
            gene in {member.upper() for member in members}
            for members in MICROGLIA_GENE_MODULES.values()
        )
        for gene in genes
    }
    rng = np.random.default_rng(seed)
    ranking_scores = {
        "graph_jepa_therapeutic_like_percentile": scorecard.set_index("gene")[
            "therapeutic_like_score_percentile"
        ],
        "gene_pathology_correlation": pd.Series(correlation_scores),
        "high_vs_low_pathology_differential_expression": pd.Series(de_scores),
        "graph_degree_hubness": degree.reindex(genes).fillna(0).set_axis(genes),
        "module_membership_or_module_score": pd.Series(membership),
        "random_baseline": pd.Series(rng.random(len(genes)), index=genes),
    }
    promoted = set(
        shortlist.loc[
            shortlist["final_tier"].eq("scorecard_supported_isolated_hypothesis"),
            "gene",
        ]
    )
    broad = set(
        shortlist.loc[shortlist["final_tier"].eq("broad_state_caution"), "gene"]
    )
    priors = set(shortlist.loc[shortlist["prior_candidate_flag"], "gene"])
    rows = []
    for method, raw_score in ranking_scores.items():
        raw_score = raw_score.reindex(genes).fillna(raw_score.min() if raw_score.notna().any() else 0)
        rank_pct = percentile(raw_score)
        cleaner_values = rank_pct[[gene in promoted for gene in genes]]
        broad_values = rank_pct[[gene in broad for gene in genes]]
        separation = cleaner_values.median() - broad_values.median()
        ordered = raw_score.sort_values(ascending=False).index.tolist()
        for top_k in [20, 50]:
            selected = set(ordered[:top_k])
            rows.append(
                {
                    "ranking_method": method,
                    "top_k": top_k,
                    "overlap_promoted_tier1": len(selected & promoted),
                    "overlap_broad_state_caution": len(selected & broad),
                    "overlap_prior_anchors": len(selected & priors),
                    "cleaner_vs_broad_separation_metric": separation,
                    "status": "tested",
                    "notes": (
                        "Calibration comparison only; cleaner/broad labels derive from "
                        "Graph-JEPA scorecard axes."
                    ),
                }
            )
    return pd.DataFrame(rows)


def markdown_table(frame: pd.DataFrame, columns: list[str]) -> list[str]:
    data = frame[columns].copy()
    for column in data.columns:
        if pd.api.types.is_numeric_dtype(data[column]):
            data[column] = data[column].map(
                lambda value: "" if pd.isna(value) else f"{float(value):.5g}"
            )
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join(["---"] * len(columns)) + " |",
    ]
    lines.extend(
        "| " + " | ".join(str(value).replace("|", "/") for value in row) + " |"
        for row in data.itertuples(index=False, name=None)
    )
    return lines


def main() -> None:
    args = parse_args()
    expression, x_cells, genes, metadata = load_donor_matrices(
        args.h5ad, args.metadata
    )
    targets = [
        "percent AT8 positive area_Grey matter",
        "percent 6e10 positive area_Grey matter",
        "percent GFAP positive area_Grey matter",
        "percent Iba1 positive area_Grey matter",
        "percent NeuN positive area_Grey matter",
    ]
    missing_targets = [target for target in targets if target not in metadata.columns]
    if missing_targets:
        raise ValueError(f"Missing donor pathology targets: {missing_targets}")
    target_frame = metadata[targets].apply(pd.to_numeric, errors="coerce")

    adata = ad.read_h5ad(args.h5ad, backed="r")
    donor_ids = normalize_donor_id(adata.obs["Donor ID"]).reset_index(drop=True)
    adata.file.close()
    device = choose_device(args.device)
    graph_latent = graph_jepa_donor_latent(
        x_cells,
        genes,
        donor_ids,
        expression.index.tolist(),
        args.checkpoint,
        args.edge_index,
        device,
        args.batch_size,
    )
    representations = {
        "graph_jepa_real_graph_latent": graph_latent,
        "pca_expression_baseline": expression.to_numpy(dtype=np.float32),
        "module_mean_baseline": module_matrix(expression),
        "raw_expression_regularized_baseline": expression.to_numpy(dtype=np.float32),
    }
    predictive = predictive_comparison(representations, target_frame, args.seed)

    scorecard = pd.read_csv(args.scorecard)
    shortlist = pd.read_csv(args.shortlist)
    ranking = discovery_rankings(
        expression, target_frame, scorecard, shortlist, args.graph_edges, args.seed
    )
    args.predictive_out.parent.mkdir(parents=True, exist_ok=True)
    predictive.to_csv(args.predictive_out, index=False)
    ranking.to_csv(args.ranking_out, index=False)

    tested = predictive[predictive["status"].eq("tested")]
    mean_spearman = (
        tested.groupby("representation")["oof_spearman"].mean().sort_values(ascending=False)
    )
    graph_best = (
        not mean_spearman.empty
        and mean_spearman.index[0] == "graph_jepa_real_graph_latent"
    )
    conclusion = (
        "Graph-JEPA showed added predictive/representation value over the tested baselines."
        if graph_best
        else "Graph-JEPA remains a useful hypothesis-generation framework, but superiority over simpler baselines was not established."
    )
    artifact_rows = [
        ("real_graph_stage_b", args.checkpoint, args.checkpoint.exists()),
        ("shuffled_graph_jepa", Path(""), False),
        ("no_graph_jepa", Path(""), False),
        ("expression_only_autoencoder", Path(""), False),
    ]
    lines = [
        "# Discovery Baseline Comparison Gate",
        "",
        "## Gate conclusion",
        "",
        conclusion,
        "",
        "## Predictive representation comparison",
        "",
        "All tested representations use identical donor-level five-fold splits and a ridge readout. PCA is fit within each training fold. Cells are never split across train/test because the modeling unit is donor.",
        "",
        *markdown_table(
            tested,
            [
                "representation",
                "target",
                "n_donors",
                "r2_mean",
                "oof_pearson",
                "oof_spearman",
                "mae_mean",
                "rmse_mean",
            ],
        ),
        "",
        "Mean out-of-fold Spearman across pathology targets:",
        "",
        *[f"- `{name}`: {value:.4f}" for name, value in mean_spearman.items()],
        "",
        "## Discovery ranking calibration",
        "",
        *markdown_table(
            ranking,
            [
                "ranking_method",
                "top_k",
                "overlap_promoted_tier1",
                "overlap_broad_state_caution",
                "overlap_prior_anchors",
                "cleaner_vs_broad_separation_metric",
            ],
        ),
        "",
        "Cleaner/broad classes are derived from Graph-JEPA scorecard axes. This ranking analysis is calibration, not independent biological validation.",
        "",
        "## Ablation artifacts found",
        "",
        f"- Real-graph Stage B Graph-JEPA: `{args.checkpoint}`",
        "",
        "## Ablation artifacts requiring future training",
        "",
        "- `shuffled_graph_jepa`: `not_available_existing_artifact`",
        "- `no_graph_jepa`: `not_available_existing_artifact`",
        "- `expression_only_autoencoder`: `not_available_existing_artifact`",
        "",
        "No ablation model was trained for this gate.",
        "",
        "## Boundaries",
        "",
        "- Predictive comparison evaluates donor-level association, not causal discovery.",
        "- Discovery-ranking comparison is not independent because the cleaner/broad labels originate from Graph-JEPA score axes.",
        "- No result proves causal mechanism, druggability, spatial plaque proximity, or therapeutic efficacy.",
        "",
    ]
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {args.predictive_out}")
    print(f"Wrote {args.ranking_out}")
    print(f"Wrote {args.report}")
    print(conclusion)


if __name__ == "__main__":
    main()
