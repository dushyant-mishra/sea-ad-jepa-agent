from __future__ import annotations

import argparse
from pathlib import Path

import anndata as ad
import numpy as np
import pandas as pd
import torch
from scipy import sparse
from sklearn.model_selection import GroupKFold, StratifiedGroupKFold
from torch import nn
from torch.utils.data import DataLoader, TensorDataset, WeightedRandomSampler

from sea_ad_jepa.baselines import spearman_corr
from sea_ad_jepa.data import load_pathology_targets, normalize_donor_id
from sea_ad_jepa.gene_sets import MICROGLIA_GENE_MODULES
from sea_ad_jepa.jepa import GeneJEPA


class PathologyRegressor(nn.Module):
    def __init__(self, latent_dim: int, hidden_dim: int, dropout: float):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(latent_dim, hidden_dim),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, 1),
        )

    def forward(self, z: torch.Tensor) -> torch.Tensor:
        return self.net(z).squeeze(-1)


def choose_device(requested: str) -> torch.device:
    if requested == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    return torch.device(requested)


def to_dense_float32(matrix) -> np.ndarray:
    if sparse.issparse(matrix):
        matrix = matrix.toarray()
    return np.asarray(matrix, dtype=np.float32)


def transform_target(y: np.ndarray, mode: str) -> np.ndarray:
    if mode == "raw":
        return y.astype(np.float32, copy=True)
    if mode == "log1p":
        return np.log1p(np.clip(y, a_min=0.0, a_max=None)).astype(np.float32)
    if mode == "rank":
        return pd.Series(y).rank(method="average").to_numpy(dtype=np.float32)
    raise ValueError(f"Unknown target transform: {mode}")


def inverse_transform_prediction(pred: np.ndarray, mode: str) -> np.ndarray:
    if mode == "log1p":
        return np.expm1(pred).astype(np.float32)
    return pred.astype(np.float32, copy=True)


def make_strata(y: np.ndarray, n_bins: int) -> np.ndarray:
    n_unique = pd.Series(y).nunique()
    bins = max(2, min(n_bins, int(n_unique)))
    try:
        return pd.qcut(y, q=bins, labels=False, duplicates="drop").astype(int)
    except ValueError:
        return pd.cut(y, bins=bins, labels=False, include_lowest=True).astype(int)


def build_balanced_sampler(donors: pd.Series, indices: np.ndarray, samples_per_epoch: int) -> WeightedRandomSampler:
    donor_counts = donors.iloc[indices].value_counts()
    weights = donors.iloc[indices].map(lambda donor_id: 1.0 / float(donor_counts[donor_id])).to_numpy(dtype=np.float64)
    return WeightedRandomSampler(
        weights=torch.as_tensor(weights, dtype=torch.double),
        num_samples=samples_per_epoch or indices.size,
        replacement=True,
    )


def load_jepa(checkpoint_path: str, device: torch.device) -> tuple[GeneJEPA, dict]:
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


def build_perturbation_sets(
    gene_names: list[str],
    mode: str,
    modules: list[str] | None,
    min_genes: int,
) -> list[tuple[str, str, list[str], list[int]]]:
    gene_to_idx = {gene.upper(): idx for idx, gene in enumerate(gene_names)}
    selected_modules = modules or sorted(MICROGLIA_GENE_MODULES)
    perturbations = []
    for module_name in selected_modules:
        if module_name not in MICROGLIA_GENE_MODULES:
            raise KeyError(f"Unknown module: {module_name}")
        present_genes = sorted(gene for gene in MICROGLIA_GENE_MODULES[module_name] if gene.upper() in gene_to_idx)
        if mode == "module":
            idx = [gene_to_idx[gene.upper()] for gene in present_genes]
            if len(idx) >= min_genes:
                perturbations.append((module_name, module_name, present_genes, idx))
        else:
            for gene in present_genes:
                perturbations.append((module_name, gene, [gene], [gene_to_idx[gene.upper()]]))
    return perturbations


def apply_intervention(
    x_base: np.ndarray,
    target_idx: list[int],
    intervention: str,
    donors: pd.Series,
    global_means: np.ndarray,
) -> np.ndarray:
    x_perturbed = x_base.copy()
    if intervention == "zero":
        x_perturbed[:, target_idx] = 0.0
    elif intervention == "global_mean":
        x_perturbed[:, target_idx] = global_means[target_idx]
    elif intervention == "donor_mean":
        for _, row_idx in donors.groupby(donors).indices.items():
            rows = np.asarray(row_idx, dtype=np.int64)
            donor_mean = x_base[rows][:, target_idx].mean(axis=0)
            x_perturbed[np.ix_(rows, target_idx)] = donor_mean
    else:
        raise ValueError(f"Unknown intervention: {intervention}")
    return x_perturbed


def predict_cells(
    model: GeneJEPA,
    head: PathologyRegressor,
    x_np: np.ndarray,
    device: torch.device,
    batch_size: int,
    train_mean: float,
    train_std: float,
    target_transform: str,
) -> tuple[np.ndarray, np.ndarray]:
    loader = DataLoader(TensorDataset(torch.from_numpy(x_np)), batch_size=batch_size, shuffle=False)
    pred_z = []
    model.eval()
    head.eval()
    with torch.no_grad():
        for (batch,) in loader:
            z = model.context_encoder(batch.to(device))
            pred_z.append(head(z).cpu().numpy())
    pred_model_scale = np.concatenate(pred_z).astype(np.float32) * train_std + train_mean
    pred_raw_scale = inverse_transform_prediction(pred_model_scale, target_transform)
    return pred_model_scale, pred_raw_scale


def predict_by_donor(
    model: GeneJEPA,
    head: PathologyRegressor,
    x_np: np.ndarray,
    donors: pd.Series,
    device: torch.device,
    batch_size: int,
    train_mean: float,
    train_std: float,
    target_transform: str,
) -> pd.DataFrame:
    pred_model, pred_raw = predict_cells(
        model=model,
        head=head,
        x_np=x_np,
        device=device,
        batch_size=batch_size,
        train_mean=train_mean,
        train_std=train_std,
        target_transform=target_transform,
    )
    return (
        pd.DataFrame(
            {
                "Donor ID": donors.to_numpy(),
                "prediction_model_scale": pred_model,
                "prediction": pred_raw,
            }
        )
        .groupby("Donor ID", as_index=False)
        .mean()
    )


def train_fold_head(
    base_checkpoint: dict,
    checkpoint_path: str,
    x: torch.Tensor,
    donors: pd.Series,
    y_transformed: np.ndarray,
    train_idx: np.ndarray,
    val_idx: np.ndarray,
    label_lookup: pd.Series,
    args: argparse.Namespace,
    device: torch.device,
) -> tuple[GeneJEPA, PathologyRegressor, dict[str, object], float, float]:
    model, _ = load_jepa(checkpoint_path, device)
    model_args = base_checkpoint.get("args", {})
    latent_dim = int(model_args.get("latent_dim", 128))
    if args.freeze_encoder:
        for param in model.context_encoder.parameters():
            param.requires_grad = False

    head = PathologyRegressor(
        latent_dim=latent_dim,
        hidden_dim=args.head_hidden_dim,
        dropout=args.dropout,
    ).to(device)

    train_mean = float(np.mean(y_transformed[train_idx]))
    train_std = float(np.std(y_transformed[train_idx])) or 1.0
    y_z = torch.as_tensor((y_transformed - train_mean) / train_std, dtype=torch.float32)
    train_dataset = TensorDataset(x[train_idx], y_z[train_idx])
    sampler = build_balanced_sampler(donors, train_idx, args.samples_per_epoch or train_idx.size)
    loader = DataLoader(train_dataset, batch_size=args.batch_size, sampler=sampler, drop_last=False)

    params = list(head.parameters()) + [param for param in model.context_encoder.parameters() if param.requires_grad]
    optimizer = torch.optim.AdamW(params, lr=args.lr, weight_decay=args.weight_decay)
    loss_fn = nn.MSELoss()
    best_state = None
    best_row: dict[str, object] | None = None
    best_spearman = -np.inf

    for epoch in range(1, args.epochs + 1):
        model.train()
        if args.freeze_encoder:
            model.context_encoder.eval()
        head.train()
        losses = []
        for batch_x, batch_y in loader:
            batch_x = batch_x.to(device)
            batch_y = batch_y.to(device)
            pred = head(model.context_encoder(batch_x))
            loss = loss_fn(pred, batch_y)
            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            optimizer.step()
            losses.append(float(loss.detach().cpu()))

        pred_by_donor = predict_by_donor(
            model=model,
            head=head,
            x_np=x[val_idx].numpy(),
            donors=donors.iloc[val_idx].reset_index(drop=True),
            device=device,
            batch_size=args.batch_size,
            train_mean=train_mean,
            train_std=train_std,
            target_transform=args.target_transform,
        )
        truth = pred_by_donor["Donor ID"].map(label_lookup).to_numpy(dtype=np.float32)
        pred_model = pred_by_donor["prediction_model_scale"].to_numpy(dtype=np.float32)
        pred_raw = pred_by_donor["prediction"].to_numpy(dtype=np.float32)
        spearman = spearman_corr(truth, pred_model)
        if np.isfinite(spearman) and spearman > best_spearman:
            best_spearman = spearman
            best_state = {
                "model": {key: value.detach().cpu().clone() for key, value in model.state_dict().items()},
                "head": {key: value.detach().cpu().clone() for key, value in head.state_dict().items()},
            }
            best_row = {
                "best_epoch": epoch,
                "val_spearman": spearman,
                "val_mae": float(np.mean(np.abs(truth - pred_raw))),
                "train_loss_at_best": float(np.mean(losses)),
            }

    if best_state is not None:
        model.load_state_dict(best_state["model"])
        head.load_state_dict(best_state["head"])
    if best_row is None:
        best_row = {"best_epoch": 0, "val_spearman": float("nan"), "val_mae": float("nan"), "train_loss_at_best": float("nan")}
    return model, head, best_row, train_mean, train_std


def bootstrap_ci(values: np.ndarray, n_bootstrap: int, seed: int, ci: float) -> tuple[float, float]:
    clean = np.asarray(values, dtype=np.float32)
    clean = clean[np.isfinite(clean)]
    if clean.size == 0:
        return float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    boot = np.empty(n_bootstrap, dtype=np.float32)
    for i in range(n_bootstrap):
        boot[i] = float(np.mean(rng.choice(clean, size=clean.size, replace=True)))
    alpha = (100.0 - ci) / 2.0
    return float(np.percentile(boot, alpha)), float(np.percentile(boot, 100.0 - alpha))


def summarize_outputs(
    donor_df: pd.DataFrame,
    fold_df: pd.DataFrame,
    n_bootstrap: int,
    seed: int,
    ci: float,
) -> pd.DataFrame:
    rows = []
    for (module, perturbation, intervention), group in donor_df.groupby(["module", "perturbation", "intervention"]):
        donor_delta = group["delta"].to_numpy(dtype=np.float32)
        fold_group = fold_df[
            (fold_df["module"] == module)
            & (fold_df["perturbation"] == perturbation)
            & (fold_df["intervention"] == intervention)
        ]
        fold_deltas = fold_group["mean_donor_delta"].to_numpy(dtype=np.float32)
        ci_low, ci_high = bootstrap_ci(donor_delta, n_bootstrap=n_bootstrap, seed=seed, ci=ci)
        sign_consistency = float(np.mean(np.sign(fold_deltas) == np.sign(np.mean(donor_delta)))) if fold_deltas.size else float("nan")
        rows.append(
            {
                "module": module,
                "perturbation": perturbation,
                "intervention": intervention,
                "n_genes_perturbed": int(group["n_genes_perturbed"].iloc[0]),
                "genes": str(group["genes"].iloc[0]),
                "mean_baseline_prediction": float(group["baseline_prediction"].mean()),
                "mean_perturbed_prediction": float(group["perturbed_prediction"].mean()),
                "mean_donor_delta": float(np.mean(donor_delta)),
                "median_donor_delta": float(np.median(donor_delta)),
                "abs_mean_donor_delta": float(abs(np.mean(donor_delta))),
                "bootstrap_ci_low": ci_low,
                "bootstrap_ci_high": ci_high,
                "n_donors": int(group["Donor ID"].nunique()),
                "n_folds": int(group["fold"].nunique()),
                "fold_delta_std": float(np.std(fold_deltas, ddof=1)) if fold_deltas.size > 1 else float("nan"),
                "fold_sign_consistency": sign_consistency,
                "mean_fold_val_spearman": float(fold_group["val_spearman"].mean()) if not fold_group.empty else float("nan"),
            }
        )
    return pd.DataFrame(rows).sort_values("abs_mean_donor_delta", ascending=False)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run donor-held-out fold-specific in-silico knockouts with a JEPA pathology head."
    )
    parser.add_argument("--h5ad", required=True)
    parser.add_argument("--checkpoint", required=True, help="Self-supervised JEPA checkpoint used to initialize each fold.")
    parser.add_argument("--target", default="percent AT8 positive area_Grey matter")
    parser.add_argument("--target-transform", choices=["raw", "log1p", "rank"], default="log1p")
    parser.add_argument("--splitter", choices=["groupkfold", "stratified_groupkfold"], default="stratified_groupkfold")
    parser.add_argument("--target-bins", type=int, default=5)
    parser.add_argument("--n-splits", type=int, default=5)
    parser.add_argument("--mode", choices=["module", "gene"], default="module")
    parser.add_argument("--modules", nargs="*", default=None)
    parser.add_argument("--intervention", choices=["global_mean", "donor_mean", "zero"], default="global_mean")
    parser.add_argument("--donor-column", default="Donor ID")
    parser.add_argument("--min-genes", type=int, default=2)
    parser.add_argument("--epochs", type=int, default=15)
    parser.add_argument("--batch-size", type=int, default=512)
    parser.add_argument("--samples-per-epoch", type=int, default=40000)
    parser.add_argument("--lr", type=float, default=5e-5)
    parser.add_argument("--head-hidden-dim", type=int, default=128)
    parser.add_argument("--dropout", type=float, default=0.1)
    parser.add_argument("--weight-decay", type=float, default=1e-4)
    parser.add_argument("--freeze-encoder", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--n-bootstrap", type=int, default=2000)
    parser.add_argument("--ci", type=float, default=95.0)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--out", default="results/tables/causal_fold_specific_module_knockouts_at8.csv")
    parser.add_argument("--donor-out", default="results/tables/causal_fold_specific_module_knockouts_at8_by_donor.csv")
    parser.add_argument("--fold-out", default="results/tables/causal_fold_specific_module_knockouts_at8_by_fold.csv")
    args = parser.parse_args()

    torch.manual_seed(args.seed)
    np.random.seed(args.seed)
    device = choose_device(args.device)
    adata = ad.read_h5ad(args.h5ad)
    if args.donor_column not in adata.obs:
        raise KeyError(f"Donor column not found in AnnData obs: {args.donor_column}")
    donors = normalize_donor_id(adata.obs[args.donor_column]).reset_index(drop=True)
    x_np = to_dense_float32(adata.X)
    x = torch.from_numpy(x_np)
    gene_names = adata.var_names.astype(str).tolist()

    base_model, checkpoint = load_jepa(args.checkpoint, device)
    del base_model
    if int(checkpoint["n_genes"]) != x_np.shape[1]:
        raise ValueError(f"Checkpoint expects {checkpoint['n_genes']} genes but AnnData has {x_np.shape[1]} genes.")

    targets, _ = load_pathology_targets()
    targets["Donor ID"] = normalize_donor_id(targets["Donor ID"])
    if args.target not in targets:
        raise KeyError(f"Target not found in pathology table: {args.target}")
    target_df = targets[["Donor ID", args.target]].copy()
    target_df[args.target] = pd.to_numeric(target_df[args.target], errors="coerce")
    target_df = target_df.dropna(subset=[args.target]).reset_index(drop=True)
    label_lookup = target_df.set_index("Donor ID")[args.target]
    y_raw = donors.map(label_lookup).to_numpy(dtype=np.float32)
    keep = np.isfinite(y_raw)
    y_transformed = transform_target(y_raw, args.target_transform)

    split_target_df = target_df[target_df["Donor ID"].isin(set(donors[keep]))].reset_index(drop=True)
    groups = split_target_df["Donor ID"].to_numpy()
    y_for_split = split_target_df[args.target].to_numpy(dtype=np.float32)
    if args.splitter == "stratified_groupkfold":
        y_for_split = make_strata(y_for_split, args.target_bins)
        splitter = StratifiedGroupKFold(n_splits=args.n_splits, shuffle=True, random_state=args.seed)
    else:
        splitter = GroupKFold(n_splits=args.n_splits)
    folds = list(splitter.split(split_target_df, y_for_split, groups=groups))

    perturbations = build_perturbation_sets(
        gene_names=gene_names,
        mode=args.mode,
        modules=args.modules,
        min_genes=args.min_genes,
    )
    global_means = x_np.mean(axis=0)
    donor_rows = []
    fold_rows = []
    print(f"Loaded {x_np.shape[0]:,} cells x {x_np.shape[1]:,} genes")
    print(f"Target: {args.target}")
    print(f"Fold splitter: {args.splitter}; target transform: {args.target_transform}")
    print(f"Perturbations to run: {len(perturbations):,}; intervention: {args.intervention}")

    for fold_id, (train_donor_idx, val_donor_idx) in enumerate(folds, start=1):
        train_donors = set(split_target_df.iloc[train_donor_idx]["Donor ID"])
        val_donors = set(split_target_df.iloc[val_donor_idx]["Donor ID"])
        train_idx = np.flatnonzero(keep & donors.isin(train_donors).to_numpy())
        val_idx = np.flatnonzero(keep & donors.isin(val_donors).to_numpy())
        if train_idx.size < 2 or val_idx.size < 2:
            continue

        model, head, fit_row, train_mean, train_std = train_fold_head(
            base_checkpoint=checkpoint,
            checkpoint_path=args.checkpoint,
            x=x,
            donors=donors,
            y_transformed=y_transformed,
            train_idx=train_idx,
            val_idx=val_idx,
            label_lookup=label_lookup,
            args=args,
            device=device,
        )
        x_val = x_np[val_idx]
        val_donor_series = donors.iloc[val_idx].reset_index(drop=True)
        baseline_model, baseline_raw = predict_cells(
            model=model,
            head=head,
            x_np=x_val,
            device=device,
            batch_size=args.batch_size,
            train_mean=train_mean,
            train_std=train_std,
            target_transform=args.target_transform,
        )
        print(
            f"fold={fold_id} train_donors={len(train_donors)} val_donors={len(val_donors)} "
            f"best_epoch={fit_row['best_epoch']} val_spearman={fit_row['val_spearman']:.4f}"
        )

        for module, perturbation, genes, idx in perturbations:
            x_ko = apply_intervention(
                x_base=x_val,
                target_idx=idx,
                intervention=args.intervention,
                donors=val_donor_series,
                global_means=global_means,
            )
            _, perturbed_raw = predict_cells(
                model=model,
                head=head,
                x_np=x_ko,
                device=device,
                batch_size=args.batch_size,
                train_mean=train_mean,
                train_std=train_std,
                target_transform=args.target_transform,
            )
            cell_delta = perturbed_raw - baseline_raw
            donor_df = (
                pd.DataFrame(
                    {
                        "Donor ID": val_donor_series.to_numpy(),
                        "baseline_prediction": baseline_raw,
                        "perturbed_prediction": perturbed_raw,
                        "delta": cell_delta,
                    }
                )
                .groupby("Donor ID", as_index=False)
                .mean()
            )
            donor_df.insert(0, "fold", fold_id)
            donor_df.insert(1, "module", module)
            donor_df.insert(2, "perturbation", perturbation)
            donor_df.insert(3, "intervention", args.intervention)
            donor_df["n_genes_perturbed"] = len(genes)
            donor_df["genes"] = ";".join(genes)
            donor_rows.append(donor_df)

            fold_delta = donor_df["delta"].to_numpy(dtype=np.float32)
            fold_rows.append(
                {
                    "fold": fold_id,
                    "module": module,
                    "perturbation": perturbation,
                    "intervention": args.intervention,
                    "n_genes_perturbed": len(genes),
                    "genes": ";".join(genes),
                    "mean_baseline_prediction": float(donor_df["baseline_prediction"].mean()),
                    "mean_perturbed_prediction": float(donor_df["perturbed_prediction"].mean()),
                    "mean_donor_delta": float(np.mean(fold_delta)),
                    "median_donor_delta": float(np.median(fold_delta)),
                    "abs_mean_donor_delta": float(abs(np.mean(fold_delta))),
                    "n_donors": int(donor_df["Donor ID"].nunique()),
                    "n_cells": int(val_idx.size),
                    "best_epoch": fit_row["best_epoch"],
                    "val_spearman": fit_row["val_spearman"],
                    "val_mae": fit_row["val_mae"],
                    "train_loss_at_best": fit_row["train_loss_at_best"],
                }
            )

    donor_df = pd.concat(donor_rows, ignore_index=True) if donor_rows else pd.DataFrame()
    fold_df = pd.DataFrame(fold_rows)
    summary_df = summarize_outputs(
        donor_df=donor_df,
        fold_df=fold_df,
        n_bootstrap=args.n_bootstrap,
        seed=args.seed,
        ci=args.ci,
    )

    out_path = Path(args.out)
    donor_out_path = Path(args.donor_out)
    fold_out_path = Path(args.fold_out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    donor_out_path.parent.mkdir(parents=True, exist_ok=True)
    fold_out_path.parent.mkdir(parents=True, exist_ok=True)
    summary_df.to_csv(out_path, index=False)
    donor_df.to_csv(donor_out_path, index=False)
    fold_df.to_csv(fold_out_path, index=False)
    print(summary_df.head(20).to_string(index=False))
    print(f"Wrote {out_path}")
    print(f"Wrote {donor_out_path}")
    print(f"Wrote {fold_out_path}")


if __name__ == "__main__":
    main()
