from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import pandas as pd
import torch
from scipy import sparse
from scipy.stats import mannwhitneyu, spearmanr
from sklearn.linear_model import Ridge
from sklearn.metrics import roc_auc_score
from sklearn.preprocessing import StandardScaler
from torch_geometric.loader import DataLoader

from graph_counterfactual_knockout import choose_device, load_graph_model
from sea_ad_jepa.data import load_pathology_targets, normalize_donor_id
from sea_ad_jepa.evaluation_utils import inverse_transform_prediction, transform_target
from sea_ad_jepa.gene_sets import MICROGLIA_GENE_MODULES
from sea_ad_jepa.graph_data import GraphExpressionDataset


DEFAULT_TARGETS = {
    "AT8/pTau": "percent AT8 positive area_Grey matter",
    "A beta/6e10": "percent 6e10 positive area_Grey matter",
    "GFAP": "percent GFAP positive area_Grey matter",
    "Iba1": "percent Iba1 positive area_Grey matter",
    "NeuN": "percent NeuN positive area_Grey matter",
}

DEFAULT_LATENTS = [
    "z_120",
    "z_26",
    "z_30",
    "z_94",
    "z_71",
    "z_63",
    "z_1",
    "z_57",
    "z_103",
]


def infer_pool(cell_id: str) -> str:
    parts = str(cell_id).split("_")
    if len(parts) >= 3:
        return "_".join(parts[-2:])
    return str(cell_id)


def normalize_condition(value: object) -> str:
    lower = str(value).strip().lower()
    if lower in {"ct", "ctrl", "control", "healthy"}:
        return "Control"
    if lower in {"ad", "alz", "alzheimer", "alzheimers"}:
        return "AD"
    return str(value)


def rank_biserial(disease: np.ndarray, control: np.ndarray) -> float:
    if disease.size == 0 or control.size == 0:
        return float("nan")
    combined = pd.Series(np.concatenate([disease, control])).rank(method="average").to_numpy(dtype=float)
    r_disease = combined[: disease.size].sum()
    u_disease = r_disease - disease.size * (disease.size + 1) / 2.0
    return float((2.0 * u_disease / (disease.size * control.size)) - 1.0)


def group_difference(
    df: pd.DataFrame,
    value_col: str,
    group_col: str,
    disease_label: str = "AD",
    control_label: str = "Control",
) -> dict[str, object]:
    disease = pd.to_numeric(df.loc[df[group_col].eq(disease_label), value_col], errors="coerce").dropna().to_numpy(dtype=float)
    control = pd.to_numeric(df.loc[df[group_col].eq(control_label), value_col], errors="coerce").dropna().to_numpy(dtype=float)
    row: dict[str, object] = {
        "variable": value_col,
        "disease_label": disease_label,
        "control_label": control_label,
        "n_disease": int(disease.size),
        "n_control": int(control.size),
        "disease_mean": float(np.mean(disease)) if disease.size else float("nan"),
        "control_mean": float(np.mean(control)) if control.size else float("nan"),
        "mean_difference_disease_minus_control": float(np.mean(disease) - np.mean(control)) if disease.size and control.size else float("nan"),
        "rank_biserial_effect": rank_biserial(disease, control),
        "mannwhitney_p": float("nan"),
        "auc_ad_vs_control": float("nan"),
    }
    if disease.size and control.size:
        try:
            row["mannwhitney_p"] = float(mannwhitneyu(disease, control, alternative="two-sided").pvalue)
        except Exception:
            pass
        try:
            y = np.concatenate([np.ones(disease.size), np.zeros(control.size)])
            score = np.concatenate([disease, control])
            row["auc_ad_vs_control"] = float(roc_auc_score(y, score))
        except Exception:
            pass
    return row


def read_gse138852_microglia(
    counts_csv: Path,
    covariates_csv: Path,
    jepa_genes: list[str],
    cell_type_col: str,
    condition_col: str,
    cell_type_pattern: str,
    max_cells: int,
    seed: int,
    chunksize: int,
    impute_values: np.ndarray | None,
) -> tuple[np.ndarray, pd.DataFrame, dict[str, object]]:
    cov = pd.read_csv(covariates_csv)
    cov = cov.rename(columns={cov.columns[0]: "cell_id"})
    cov["cell_id"] = cov["cell_id"].astype(str)
    if cell_type_col not in cov:
        raise KeyError(f"{covariates_csv} does not contain cell type column {cell_type_col!r}")
    if condition_col not in cov:
        raise KeyError(f"{covariates_csv} does not contain condition column {condition_col!r}")

    keep = cov[cell_type_col].astype(str).str.contains(cell_type_pattern, case=False, regex=True, na=False)
    obs = cov.loc[keep].copy()
    if max_cells > 0 and len(obs) > max_cells:
        obs = obs.sample(n=max_cells, random_state=seed).sort_index()
    obs["external_donor_id"] = obs["cell_id"].map(infer_pool)
    obs["condition"] = obs[condition_col].map(normalize_condition)

    selected_cells = obs["cell_id"].tolist()
    selected_set = set(selected_cells)
    gene_to_jepa: dict[str, int] = {}
    for idx, gene in enumerate(jepa_genes):
        gene_to_jepa.setdefault(str(gene).upper(), idx)

    header = pd.read_csv(counts_csv, nrows=0).columns.tolist()
    selected_cols = [col for col in header[1:] if col in selected_set]
    if not selected_cols:
        raise ValueError("No selected microglia cell IDs were found in the count matrix header.")
    cell_order = selected_cols
    cell_to_output = {cell: idx for idx, cell in enumerate(cell_order)}
    obs = obs.set_index("cell_id").loc[cell_order].reset_index()

    if impute_values is not None:
        x = np.tile(impute_values.astype(np.float32), (len(cell_order), 1))
    else:
        x = np.zeros((len(cell_order), len(jepa_genes)), dtype=np.float32)
    cell_totals = np.zeros(len(cell_order), dtype=np.float64)
    matched = 0
    matched_jepa_idx: set[int] = set()
    usecols = [header[0], *cell_order]

    for chunk in pd.read_csv(counts_csv, usecols=usecols, chunksize=chunksize):
        gene_col = chunk.columns[0]
        genes = chunk[gene_col].astype(str).tolist()
        values = chunk[cell_order].to_numpy(dtype=np.float32, copy=False)
        cell_totals += values.sum(axis=0)
        for row_idx, gene in enumerate(genes):
            jepa_idx = gene_to_jepa.get(gene.upper())
            if jepa_idx is None or jepa_idx in matched_jepa_idx:
                continue
            matched_jepa_idx.add(jepa_idx)
            x[:, jepa_idx] = values[row_idx]
            matched += 1

    cell_totals[cell_totals <= 0] = 1.0
    x = np.log1p(x * (10000.0 / cell_totals[:, None]).astype(np.float32)).astype(np.float32)
    metadata = {
        "n_cells_before_filter": int(cov.shape[0]),
        "n_cells_after_filter": int(x.shape[0]),
        "n_external_groups": int(obs["external_donor_id"].nunique()),
        "n_jepa_genes": int(len(jepa_genes)),
        "n_matched_genes": int(matched),
        "gene_overlap_fraction": float(matched / max(len(jepa_genes), 1)),
    }
    return x, obs, metadata


def to_dense_float32(matrix) -> np.ndarray:
    if sparse.issparse(matrix):
        matrix = matrix.toarray()
    return np.asarray(matrix, dtype=np.float32)


def load_anchor_mean(anchor_h5ad: Path, jepa_genes: list[str]) -> np.ndarray:
    import anndata as ad

    anchor = ad.read_h5ad(anchor_h5ad)
    anchor_genes = anchor.var_names.astype(str).tolist()
    if [g.upper() for g in anchor_genes] != [g.upper() for g in jepa_genes]:
        raise ValueError(f"{anchor_h5ad} gene order does not match the Graph-JEPA input gene order.")
    return to_dense_float32(anchor.X).mean(axis=0).astype(np.float32)


def encode_external(
    model,
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


def aggregate_embeddings(z: np.ndarray, obs: pd.DataFrame, group_col: str) -> pd.DataFrame:
    z_cols = [f"z_{i}" for i in range(z.shape[1])]
    df = pd.DataFrame(z, columns=z_cols)
    df.insert(0, group_col, obs[group_col].astype(str).to_numpy())
    df.insert(1, "condition", obs["condition"].astype(str).to_numpy())
    grouped = df.groupby([group_col, "condition"], as_index=False)[z_cols].mean()
    grouped.insert(0, "n_cells", df.groupby([group_col, "condition"]).size().to_numpy())
    return grouped


def sea_ad_control_centroid(sea_donor_embeddings: Path) -> np.ndarray:
    sea = pd.read_csv(sea_donor_embeddings)
    if "Donor ID" not in sea:
        raise KeyError(f"{sea_donor_embeddings} must contain `Donor ID`.")
    z_cols = [c for c in sea.columns if c.startswith("z_")]
    targets, _ = load_pathology_targets()
    targets["Donor ID"] = normalize_donor_id(targets["Donor ID"])
    sea["Donor ID"] = normalize_donor_id(sea["Donor ID"])
    data = sea.merge(targets, on="Donor ID", how="inner")
    low_score = pd.Series(0.0, index=data.index)
    for col in [
        "percent AT8 positive area_Grey matter",
        "percent 6e10 positive area_Grey matter",
        "percent GFAP positive area_Grey matter",
        "percent Iba1 positive area_Grey matter",
    ]:
        if col in data:
            values = pd.to_numeric(data[col], errors="coerce")
            ranks = values.rank(pct=True)
            low_score = low_score.add(ranks.fillna(0.5), fill_value=0.5)
    if "percent NeuN positive area_Grey matter" in data:
        values = pd.to_numeric(data["percent NeuN positive area_Grey matter"], errors="coerce")
        low_score = low_score.add((1.0 - values.rank(pct=True)).fillna(0.5), fill_value=0.5)
    n_low = max(5, int(np.ceil(0.25 * len(data))))
    low = data.loc[low_score.nsmallest(n_low).index]
    return low[z_cols].to_numpy(dtype=np.float32).mean(axis=0)


def apply_control_centroid_shift(
    donor_z: pd.DataFrame,
    sea_control: np.ndarray,
    group_col: str = "external_donor_id",
) -> tuple[pd.DataFrame, dict[str, object]]:
    z_cols = [c for c in donor_z.columns if c.startswith("z_")]
    shifted = donor_z.copy()
    external_controls = shifted[shifted["condition"].eq("Control")]
    if external_controls.empty:
        return shifted, {"control_centroid_shift_applied": False, "control_centroid_shift_l2": float("nan")}
    external_control_centroid = external_controls[z_cols].to_numpy(dtype=np.float32).mean(axis=0)
    shift = sea_control.astype(np.float32) - external_control_centroid
    shifted[z_cols] = shifted[z_cols].to_numpy(dtype=np.float32) + shift[None, :]
    return shifted, {
        "control_centroid_shift_applied": True,
        "control_centroid_shift_l2": float(np.linalg.norm(shift)),
    }


def build_sea_ad_trajectories(sea_donor_embeddings: Path) -> pd.DataFrame:
    sea = pd.read_csv(sea_donor_embeddings)
    if "Donor ID" not in sea:
        raise KeyError(f"{sea_donor_embeddings} must contain `Donor ID`.")
    z_cols = [c for c in sea.columns if c.startswith("z_")]
    targets, _ = load_pathology_targets()
    sea["Donor ID"] = normalize_donor_id(sea["Donor ID"])
    targets["Donor ID"] = normalize_donor_id(targets["Donor ID"])
    data = sea.merge(targets, on="Donor ID", how="inner")
    rows = []
    for label, col in DEFAULT_TARGETS.items():
        if col not in data:
            continue
        values = pd.to_numeric(data[col], errors="coerce")
        valid = data.loc[values.notna()].copy()
        values = values.loc[valid.index]
        if len(valid) < 12 or values.nunique() < 3:
            continue
        low_idx = values.nsmallest(max(5, int(np.ceil(0.25 * len(valid))))).index
        high_idx = values.nlargest(max(5, int(np.ceil(0.25 * len(valid))))).index
        low = data.loc[low_idx, z_cols].to_numpy(dtype=np.float32).mean(axis=0)
        high = data.loc[high_idx, z_cols].to_numpy(dtype=np.float32).mean(axis=0)
        if label == "NeuN":
            direction = low - high
            direction_label = "low_NeuN_direction"
        else:
            direction = high - low
            direction_label = f"high_{label}_direction"
        norm = float(np.linalg.norm(direction))
        if norm <= 0:
            continue
        row = {
            "trajectory": label,
            "direction_label": direction_label,
            "n_low_donors": int(len(low_idx)),
            "n_high_donors": int(len(high_idx)),
            "direction_norm": norm,
        }
        row.update({col_name: float(value) for col_name, value in zip(z_cols, direction / norm)})
        rows.append(row)
    return pd.DataFrame(rows)


def score_trajectories(donor_z: pd.DataFrame, trajectories: pd.DataFrame) -> pd.DataFrame:
    z_cols = [c for c in donor_z.columns if c.startswith("z_")]
    out = donor_z[["external_donor_id", "condition", "n_cells"]].copy()
    if trajectories.empty:
        return out
    z = donor_z[z_cols].to_numpy(dtype=np.float32)
    for _, row in trajectories.iterrows():
        direction = row[z_cols].to_numpy(dtype=np.float32)
        out[f"trajectory_{row['trajectory']}_score"] = z @ direction
    return out


def module_scores(matrix: np.ndarray, obs: pd.DataFrame, jepa_genes: list[str], group_col: str) -> pd.DataFrame:
    gene_to_idx = {gene.upper(): idx for idx, gene in enumerate(jepa_genes)}
    rows = pd.DataFrame({group_col: obs[group_col].astype(str), "condition": obs["condition"].astype(str)})
    for module, genes in MICROGLIA_GENE_MODULES.items():
        idx = [gene_to_idx[g.upper()] for g in genes if g.upper() in gene_to_idx]
        if len(idx) >= 2:
            rows[f"module_{module}"] = matrix[:, idx].mean(axis=1)
    module_cols = [c for c in rows.columns if c.startswith("module_")]
    return rows.groupby([group_col, "condition"], as_index=False)[module_cols].mean()


def fit_pathology_heads(sea_donor_embeddings: Path, target_transform: str) -> dict[str, tuple[Ridge, StandardScaler]]:
    sea = pd.read_csv(sea_donor_embeddings)
    if "Donor ID" not in sea:
        raise KeyError(f"{sea_donor_embeddings} must contain `Donor ID`.")
    sea["Donor ID"] = normalize_donor_id(sea["Donor ID"])
    z_cols = [c for c in sea.columns if c.startswith("z_")]
    targets, _ = load_pathology_targets()
    targets["Donor ID"] = normalize_donor_id(targets["Donor ID"])
    data = sea.merge(targets[["Donor ID", *DEFAULT_TARGETS.values()]], on="Donor ID", how="inner")
    heads = {}
    for label, target_col in DEFAULT_TARGETS.items():
        subset = data.dropna(subset=[target_col]).copy()
        x = subset[z_cols].to_numpy(dtype=np.float32)
        y = transform_target(subset[target_col].to_numpy(dtype=np.float32), target_transform)
        scaler = StandardScaler()
        x_scaled = scaler.fit_transform(x)
        head = Ridge(alpha=10.0)
        head.fit(x_scaled, y)
        heads[label] = (head, scaler)
    return heads


def predict_pathology(
    donor_z: pd.DataFrame,
    heads: dict[str, tuple[Ridge, StandardScaler]],
    target_transform: str,
) -> pd.DataFrame:
    z_cols = [c for c in donor_z.columns if c.startswith("z_")]
    out = donor_z[["external_donor_id", "condition", "n_cells"]].copy()
    for label, (head, scaler) in heads.items():
        pred = head.predict(scaler.transform(donor_z[z_cols].to_numpy(dtype=np.float32))).astype(np.float32)
        out[f"predicted_{label}_raw_scale"] = inverse_transform_prediction(pred, target_transform)
        out[f"predicted_{label}_model_scale"] = pred
    return out


def summarize_external(
    donor_predictions: pd.DataFrame,
    donor_embeddings: pd.DataFrame,
    donor_modules: pd.DataFrame,
    donor_trajectories: pd.DataFrame,
    latents: list[str],
) -> pd.DataFrame:
    rows = []
    for col in [c for c in donor_predictions.columns if c.startswith("predicted_") and c.endswith("_model_scale")]:
        row = group_difference(donor_predictions, col, "condition")
        row["category"] = "sea_ad_calibrated_pathology_prediction"
        rows.append(row)
    for latent in latents:
        if latent in donor_embeddings:
            row = group_difference(donor_embeddings, latent, "condition")
            row["category"] = "latent_axis"
            rows.append(row)
    for col in [c for c in donor_modules.columns if c.startswith("module_")]:
        row = group_difference(donor_modules, col, "condition")
        row["category"] = "module_score"
        rows.append(row)
    for col in [c for c in donor_trajectories.columns if c.startswith("trajectory_") and c.endswith("_score")]:
        row = group_difference(donor_trajectories, col, "condition")
        row["category"] = "sea_ad_disease_trajectory"
        rows.append(row)
    summary = pd.DataFrame(rows)
    if not summary.empty:
        summary = summary.sort_values(["category", "auc_ad_vs_control", "variable"], ascending=[True, False, True])
    return summary


def markdown_table(df: pd.DataFrame, max_rows: int = 30) -> str:
    if df.empty:
        return "No summary rows were produced."
    view = df.head(max_rows).copy()
    cols = view.columns.tolist()
    lines = [
        "| " + " | ".join(cols) + " |",
        "| " + " | ".join(["---"] * len(cols)) + " |",
    ]
    for _, row in view.iterrows():
        values = []
        for col in cols:
            value = row[col]
            if isinstance(value, float):
                values.append(f"{value:.4g}")
            else:
                values.append(str(value))
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Project external AD microglia through a strictly frozen Graph-JEPA encoder.")
    parser.add_argument("--dataset-label", default="GSE138852_Grubman_Leng")
    parser.add_argument("--counts-csv", default="data/external/grubman_gse138852/GSE138852_counts.csv.gz")
    parser.add_argument("--covariates-csv", default="data/external/grubman_gse138852/GSE138852_covariates.csv.gz")
    parser.add_argument("--checkpoint", default="results/models/stage_c_upgrade_fine_08_r0045_cov0005_pc0075/graph_jepa_stage_c_epoch_005.pt")
    parser.add_argument("--local-h5ad", default="data/processed/sea_ad_mtg_microglia_pvm_all_hvg3k_expanded_modules.h5ad")
    parser.add_argument("--edge-csv", default="results/tables/v2_graph_string_edges_t700.csv")
    parser.add_argument("--annotation-csv", default="results/tables/jepa_v2_translational_actionability_matrix.csv")
    parser.add_argument("--sea-donor-embeddings", default="results/tables/stage_c_upgrade_fine_08_r0045_cov0005_pc0075_epoch_005_donor_embeddings.csv")
    parser.add_argument("--sea-anchor-h5ad", default="data/processed/v2_pretraining/sea_ad_low_pathology_microglia_pvm_relaxed_jepa_aligned.h5ad")
    parser.add_argument("--cell-type-col", default="oupSample.cellType")
    parser.add_argument("--condition-col", default="oupSample.batchCond")
    parser.add_argument("--cell-type-pattern", default="^mg$|micro|myeloid")
    parser.add_argument("--embedding-space", choices=["auto", "encoder", "projector"], default="auto")
    parser.add_argument("--missing-gene-imputation", choices=["zero", "sea_ad_low_pathology_mean"], default="zero")
    parser.add_argument("--alignment", choices=["none", "control_centroid_shift"], default="none")
    parser.add_argument("--target-transform", choices=["raw", "log1p", "rank"], default="log1p")
    parser.add_argument("--latents", nargs="+", default=DEFAULT_LATENTS)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--counts-chunksize", type=int, default=512)
    parser.add_argument("--max-cells", type=int, default=0)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--out-prefix", default="results/tables/gse138852_graph_jepa_zero_shot")
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
    if int(checkpoint.get("n_genes", len(jepa_genes))) != len(jepa_genes):
        raise ValueError(f"Checkpoint gene count does not match reference H5AD gene count: {checkpoint.get('n_genes')} vs {len(jepa_genes)}")

    x, obs, qc = read_gse138852_microglia(
        counts_csv=Path(args.counts_csv),
        covariates_csv=Path(args.covariates_csv),
        jepa_genes=jepa_genes,
        cell_type_col=args.cell_type_col,
        condition_col=args.condition_col,
        cell_type_pattern=args.cell_type_pattern,
        max_cells=args.max_cells,
        seed=args.seed,
        chunksize=args.counts_chunksize,
        impute_values=load_anchor_mean(Path(args.sea_anchor_h5ad), jepa_genes) if args.missing_gene_imputation == "sea_ad_low_pathology_mean" else None,
    )
    z = encode_external(model, x, edge_index, node_annotations, embedding_space, device, args.batch_size, args.seed)
    donor_z = aggregate_embeddings(z, obs, "external_donor_id")
    alignment_qc: dict[str, object] = {"control_centroid_shift_applied": False, "control_centroid_shift_l2": float("nan")}
    if args.alignment == "control_centroid_shift":
        donor_z, alignment_qc = apply_control_centroid_shift(donor_z, sea_ad_control_centroid(Path(args.sea_donor_embeddings)))
    trajectories = build_sea_ad_trajectories(Path(args.sea_donor_embeddings))
    donor_trajectories = score_trajectories(donor_z, trajectories)
    donor_modules = module_scores(x, obs, jepa_genes, "external_donor_id")
    heads = fit_pathology_heads(Path(args.sea_donor_embeddings), args.target_transform)
    donor_predictions = predict_pathology(donor_z, heads, args.target_transform)
    summary = summarize_external(donor_predictions, donor_z, donor_modules, donor_trajectories, args.latents)

    qc.update(alignment_qc)
    qc["missing_gene_imputation"] = args.missing_gene_imputation
    qc["alignment"] = args.alignment
    for frame in [donor_z, donor_modules, donor_predictions, donor_trajectories, summary]:
        frame.insert(0, "dataset", args.dataset_label)
        frame.insert(1, "embedding_space", embedding_space)
        for key, value in qc.items():
            frame[key] = value

    prefix = Path(args.out_prefix)
    prefix.parent.mkdir(parents=True, exist_ok=True)
    donor_z.to_csv(prefix.with_name(prefix.name + "_donor_embeddings.csv"), index=False)
    donor_predictions.to_csv(prefix.with_name(prefix.name + "_predicted_pathology.csv"), index=False)
    donor_modules.to_csv(prefix.with_name(prefix.name + "_module_scores.csv"), index=False)
    donor_trajectories.to_csv(prefix.with_name(prefix.name + "_trajectory_scores.csv"), index=False)
    trajectories.to_csv(prefix.with_name(prefix.name + "_sea_ad_trajectory_vectors.csv"), index=False)
    summary.to_csv(prefix.with_name(prefix.name + "_summary.csv"), index=False)

    report_path = prefix.with_name(prefix.name + "_report.md")
    report_path.write_text(
        "\n".join(
            [
                f"# {args.dataset_label} Frozen Graph-JEPA Zero-Shot Projection",
                "",
                "This smoke test projects external microglia/immune nuclei through the SEA-AD-trained Graph-JEPA encoder with all weights frozen.",
                "",
                "## Strict Freeze",
                "",
                f"- checkpoint: `{args.checkpoint}`",
                f"- embedding space: `{embedding_space}`",
                "- all model parameters set to `requires_grad=False`",
                f"- missing gene imputation: `{args.missing_gene_imputation}`",
                f"- alignment: `{args.alignment}`",
                "",
                "## Feature Alignment",
                "",
                f"- projected cells: `{qc['n_cells_after_filter']}`",
                f"- external groups: `{qc['n_external_groups']}`",
                f"- matched genes: `{qc['n_matched_genes']} / {qc['n_jepa_genes']}`",
                f"- gene overlap fraction: `{qc['gene_overlap_fraction']:.3f}`",
                f"- control-centroid shift applied: `{qc['control_centroid_shift_applied']}`",
                f"- control-centroid shift L2: `{qc['control_centroid_shift_l2']:.4f}`",
                "",
                "## Summary",
                "",
                markdown_table(summary),
                "",
                "## Interpretation Boundary",
                "",
                "This is independent observational-cohort projection, not perturbational causal proof. The GSE138852 labels support an AD/control smoke test, not continuous SEA-AD-style AT8/6e10/GFAP regression validation. SEA-AD-calibrated pathology heads should be interpreted on model scale for ranking/separation; raw-scale values may be out of distribution in small external cohorts. Trajectory scores and module scores are the primary readouts for cross-cohort geometry.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    print(summary.to_string(index=False))
    print(f"Wrote {prefix.with_name(prefix.name + '_donor_embeddings.csv')}")
    print(f"Wrote {prefix.with_name(prefix.name + '_predicted_pathology.csv')}")
    print(f"Wrote {prefix.with_name(prefix.name + '_module_scores.csv')}")
    print(f"Wrote {prefix.with_name(prefix.name + '_trajectory_scores.csv')}")
    print(f"Wrote {prefix.with_name(prefix.name + '_sea_ad_trajectory_vectors.csv')}")
    print(f"Wrote {prefix.with_name(prefix.name + '_summary.csv')}")
    print(f"Wrote {report_path}")


if __name__ == "__main__":
    main()
