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
from sea_ad_jepa.jepa import GeneJEPA


def choose_device(requested: str) -> torch.device:
    if requested == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    return torch.device(requested)


def to_dense_float32(matrix) -> np.ndarray:
    if sparse.issparse(matrix):
        matrix = matrix.toarray()
    return np.asarray(matrix, dtype=np.float32)


def select_train_variable_features(x_train: np.ndarray, max_features: int | None) -> np.ndarray:
    n_features = x_train.shape[1]
    if max_features is None or max_features <= 0 or max_features >= n_features:
        return np.arange(n_features)
    variances = np.var(x_train, axis=0)
    return np.argsort(variances)[-max_features:]


def transform_target(y: np.ndarray, mode: str) -> np.ndarray:
    if mode == "raw":
        return y.astype(np.float32, copy=True)
    if mode == "log1p":
        clipped = np.clip(y, a_min=0.0, a_max=None)
        return np.log1p(clipped).astype(np.float32)
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


def ridge_predict(
    x_train_np: np.ndarray,
    y_train_np: np.ndarray,
    x_test_np: np.ndarray,
    alpha: float,
    device: torch.device,
) -> np.ndarray:
    mean = x_train_np.mean(axis=0, keepdims=True)
    std = x_train_np.std(axis=0, keepdims=True)
    std[std == 0] = 1.0

    x_train = torch.as_tensor((x_train_np - mean) / std, dtype=torch.float32, device=device)
    x_test = torch.as_tensor((x_test_np - mean) / std, dtype=torch.float32, device=device)
    y_train = torch.as_tensor(y_train_np, dtype=torch.float32, device=device)

    x_train = torch.cat([torch.ones((x_train.shape[0], 1), dtype=torch.float32, device=device), x_train], dim=1)
    x_test = torch.cat([torch.ones((x_test.shape[0], 1), dtype=torch.float32, device=device), x_test], dim=1)

    identity = torch.eye(x_train.shape[1], dtype=torch.float32, device=device)
    identity[0, 0] = 0.0
    weights = torch.linalg.solve(x_train.T @ x_train + alpha * identity, x_train.T @ y_train)
    return (x_test @ weights).detach().cpu().numpy()


def evaluate_feature_table(
    label: str,
    features_path: str,
    target_df: pd.DataFrame,
    target: str,
    folds: list[tuple[np.ndarray, np.ndarray]],
    max_features: int | None,
    alpha: float,
    device: torch.device,
    target_transform: str,
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    features = pd.read_csv(features_path)
    features["Donor ID"] = normalize_donor_id(features["Donor ID"])
    merged = features.merge(target_df[["Donor ID", target]], on="Donor ID", how="inner")
    merged[target] = pd.to_numeric(merged[target], errors="coerce")
    merged = merged.dropna(subset=[target]).reset_index(drop=True)

    feature_columns = [column for column in merged.columns if column not in {"Donor ID", target}]
    x = merged[feature_columns].to_numpy(dtype=np.float32)
    y = merged[target].to_numpy(dtype=np.float32)
    donors = merged["Donor ID"].to_numpy()

    rows = []
    prediction_rows = []
    for fold_id, (train_donors_idx, val_donors_idx) in enumerate(folds, start=1):
        train_donors = set(target_df.iloc[train_donors_idx]["Donor ID"])
        val_donors = set(target_df.iloc[val_donors_idx]["Donor ID"])
        train_mask = np.asarray([donor in train_donors for donor in donors])
        val_mask = np.asarray([donor in val_donors for donor in donors])
        if train_mask.sum() < 2 or val_mask.sum() < 2:
            continue

        keep_features = select_train_variable_features(x[train_mask], max_features)
        y_train = transform_target(y[train_mask], target_transform)
        pred = ridge_predict(
            x[train_mask][:, keep_features],
            y_train,
            x[val_mask][:, keep_features],
            alpha=alpha,
            device=device,
        )
        truth = y[val_mask]
        pred_raw_scale = inverse_transform_prediction(pred, target_transform)
        residual = truth - pred_raw_scale
        donor_val = donors[val_mask]
        prediction_rows.extend(
            {
                "model": label,
                "fold": fold_id,
                "target": target,
                "donor_id": donor,
                "truth": float(truth_value),
                "prediction": float(prediction),
                "prediction_model_scale": float(model_prediction),
                "target_transform": target_transform,
            }
            for donor, truth_value, prediction, model_prediction in zip(donor_val, truth, pred_raw_scale, pred)
        )
        rows.append(
            {
                "model": label,
                "fold": fold_id,
                "target": target,
                "n_train_donors": int(train_mask.sum()),
                "n_val_donors": int(val_mask.sum()),
                "spearman": spearman_corr(truth, pred),
                "mae": float(np.mean(np.abs(residual))),
                "r2": r2_score(truth, pred_raw_scale),
                "target_transform": target_transform,
            }
        )
    return rows, prediction_rows


def r2_score(truth: np.ndarray, pred: np.ndarray) -> float:
    ss_res = float(np.sum((truth - pred) ** 2))
    ss_tot = float(np.sum((truth - truth.mean()) ** 2))
    return 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")


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


def build_balanced_sampler(donors: pd.Series, indices: np.ndarray, samples_per_epoch: int) -> WeightedRandomSampler:
    donor_counts = donors.iloc[indices].value_counts()
    weights = donors.iloc[indices].map(lambda donor_id: 1.0 / float(donor_counts[donor_id])).to_numpy(dtype=np.float64)
    return WeightedRandomSampler(
        weights=torch.as_tensor(weights, dtype=torch.double),
        num_samples=samples_per_epoch or indices.size,
        replacement=True,
    )


def predict_cells_by_donor(
    model: GeneJEPA,
    head: PathologyRegressor,
    x: torch.Tensor,
    donors: pd.Series,
    indices: np.ndarray,
    device: torch.device,
    batch_size: int,
) -> pd.DataFrame:
    loader = DataLoader(TensorDataset(x[indices]), batch_size=batch_size, shuffle=False)
    preds = []
    model.eval()
    head.eval()
    with torch.no_grad():
        for (batch,) in loader:
            z = model.context_encoder(batch.to(device))
            preds.append(head(z).cpu().numpy())
    pred_df = pd.DataFrame({"Donor ID": donors.iloc[indices].to_numpy(), "prediction_z": np.concatenate(preds)})
    return pred_df.groupby("Donor ID", as_index=False)["prediction_z"].mean()


def evaluate_pathology_finetune(
    h5ad_path: str,
    checkpoint_path: str,
    target_df: pd.DataFrame,
    target: str,
    folds: list[tuple[np.ndarray, np.ndarray]],
    args: argparse.Namespace,
    device: torch.device,
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    adata = ad.read_h5ad(h5ad_path)
    donors = normalize_donor_id(adata.obs[args.donor_column]).reset_index(drop=True)
    label_lookup = target_df.set_index("Donor ID")[target]
    y_raw = donors.map(label_lookup).to_numpy(dtype=np.float32)
    keep = np.isfinite(y_raw)
    y = transform_target(y_raw, args.target_transform)
    x = torch.from_numpy(to_dense_float32(adata.X))

    checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
    model_args = checkpoint.get("args", {})

    rows = []
    prediction_rows = []
    for fold_id, (train_donors_idx, val_donors_idx) in enumerate(folds, start=1):
        train_donors = set(target_df.iloc[train_donors_idx]["Donor ID"])
        val_donors = set(target_df.iloc[val_donors_idx]["Donor ID"])
        train_idx = np.flatnonzero(keep & donors.isin(train_donors).to_numpy())
        val_idx = np.flatnonzero(keep & donors.isin(val_donors).to_numpy())
        if train_idx.size < 2 or val_idx.size < 2:
            continue

        model = GeneJEPA(
            input_dim=int(checkpoint["n_genes"]),
            hidden_dim=int(model_args.get("hidden_dim", 512)),
            latent_dim=int(model_args.get("latent_dim", 128)),
            ema_decay=float(model_args.get("ema_decay", 0.996)),
        ).to(device)
        model.load_state_dict(checkpoint["model_state"])
        head = PathologyRegressor(
            latent_dim=int(model_args.get("latent_dim", 128)),
            hidden_dim=args.head_hidden_dim,
            dropout=args.dropout,
        ).to(device)

        train_mean = float(np.mean(y[train_idx]))
        train_std = float(np.std(y[train_idx])) or 1.0
        y_z = torch.as_tensor((y - train_mean) / train_std, dtype=torch.float32)
        train_dataset = TensorDataset(x[train_idx], y_z[train_idx])
        sampler = build_balanced_sampler(donors, train_idx, args.samples_per_epoch or train_idx.size)
        loader = DataLoader(train_dataset, batch_size=args.batch_size, sampler=sampler, drop_last=False)

        optimizer = torch.optim.AdamW(
            list(model.context_encoder.parameters()) + list(head.parameters()),
            lr=args.finetune_lr,
            weight_decay=args.weight_decay,
        )
        loss_fn = nn.MSELoss()
        best_row = None
        best_predictions = []
        best_spearman = -np.inf

        for epoch in range(1, args.finetune_epochs + 1):
            model.train()
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

            pred_by_donor = predict_cells_by_donor(model, head, x, donors, val_idx, device, args.batch_size)
            pred_by_donor["prediction"] = pred_by_donor["prediction_z"] * train_std + train_mean
            truth = pred_by_donor["Donor ID"].map(label_lookup).to_numpy(dtype=np.float32)
            pred_model_scale = pred_by_donor["prediction"].to_numpy(dtype=np.float32)
            pred_raw_scale = inverse_transform_prediction(pred_model_scale, args.target_transform)
            spearman = spearman_corr(truth, pred_model_scale)
            if np.isfinite(spearman) and spearman > best_spearman:
                best_spearman = spearman
                residual = truth - pred_raw_scale
                best_row = {
                    "model": args.finetune_label,
                    "fold": fold_id,
                    "target": target,
                    "n_train_donors": len(train_donors),
                    "n_val_donors": len(val_donors),
                    "spearman": spearman,
                    "mae": float(np.mean(np.abs(residual))),
                    "r2": r2_score(truth, pred_raw_scale),
                    "best_epoch": epoch,
                    "train_loss_at_best": float(np.mean(losses)),
                    "target_transform": args.target_transform,
                }
                best_predictions = [
                    {
                        "model": args.finetune_label,
                        "fold": fold_id,
                        "target": target,
                        "donor_id": donor,
                        "truth": float(truth_value),
                        "prediction": float(prediction),
                        "prediction_model_scale": float(model_prediction),
                        "target_transform": args.target_transform,
                    }
                    for donor, truth_value, prediction, model_prediction in zip(
                        pred_by_donor["Donor ID"], truth, pred_raw_scale, pred_model_scale
                    )
                ]
        if best_row is not None:
            rows.append(best_row)
            prediction_rows.extend(best_predictions)
            print(
                f"{args.finetune_label} fold={fold_id} "
                f"best_epoch={best_row['best_epoch']} spearman={best_row['spearman']:.4f}"
            )
    return rows, prediction_rows


def summarize(results: pd.DataFrame) -> pd.DataFrame:
    summary = (
        results.groupby(["model", "target"], as_index=False)
        .agg(
            n_folds=("fold", "nunique"),
            spearman_mean=("spearman", "mean"),
            spearman_std=("spearman", "std"),
            r2_mean=("r2", "mean"),
            r2_std=("r2", "std"),
            mae_mean=("mae", "mean"),
            mae_std=("mae", "std"),
        )
        .sort_values("spearman_mean", ascending=False)
    )
    return summary


def summarize_oof(predictions: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (model, target), group in predictions.groupby(["model", "target"]):
        truth = group["truth"].to_numpy(dtype=np.float32)
        pred = group["prediction_model_scale"].to_numpy(dtype=np.float32)
        pred_raw = group["prediction"].to_numpy(dtype=np.float32)
        residual = truth - pred_raw
        rows.append(
            {
                "model": model,
                "target": target,
                "n_oof_donors": int(group["donor_id"].nunique()),
                "pooled_oof_spearman": spearman_corr(truth, pred),
                "pooled_oof_r2": r2_score(truth, pred_raw),
                "pooled_oof_mae": float(np.mean(np.abs(residual))),
            }
        )
    return pd.DataFrame(rows).sort_values("pooled_oof_spearman", ascending=False)


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare models using donor-grouped K-fold validation.")
    parser.add_argument(
        "--feature-result",
        action="append",
        nargs=2,
        metavar=("LABEL", "CSV"),
        default=[],
        help="Donor-level feature table to evaluate with ridge regression. Can be repeated.",
    )
    parser.add_argument("--target", default="percent AT8 positive area_Grey matter")
    parser.add_argument("--n-splits", type=int, default=5)
    parser.add_argument("--splitter", choices=["groupkfold", "stratified_groupkfold"], default="groupkfold")
    parser.add_argument("--target-bins", type=int, default=5)
    parser.add_argument("--target-transform", choices=["raw", "log1p", "rank"], default="raw")
    parser.add_argument("--alpha", type=float, default=10.0)
    parser.add_argument("--max-features", type=int, default=0)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--out", default="results/tables/donor_groupkfold_validation.csv")
    parser.add_argument("--summary-out", default="results/tables/donor_groupkfold_validation_summary.csv")
    parser.add_argument("--oof-out", default="results/tables/donor_groupkfold_oof_predictions.csv")
    parser.add_argument("--oof-summary-out", default="results/tables/donor_groupkfold_oof_summary.csv")
    parser.add_argument("--finetune-h5ad", default="")
    parser.add_argument("--finetune-checkpoint", default="")
    parser.add_argument("--finetune-label", default="pathology_aware_jepa")
    parser.add_argument("--donor-column", default="Donor ID")
    parser.add_argument("--finetune-epochs", type=int, default=20)
    parser.add_argument("--finetune-lr", type=float, default=5e-5)
    parser.add_argument("--batch-size", type=int, default=512)
    parser.add_argument("--samples-per-epoch", type=int, default=40000)
    parser.add_argument("--head-hidden-dim", type=int, default=128)
    parser.add_argument("--dropout", type=float, default=0.1)
    parser.add_argument("--weight-decay", type=float, default=1e-4)
    args = parser.parse_args()

    device = choose_device(args.device)
    targets, _ = load_pathology_targets()
    targets["Donor ID"] = normalize_donor_id(targets["Donor ID"])
    targets[args.target] = pd.to_numeric(targets[args.target], errors="coerce")
    target_df = targets[["Donor ID", args.target]].dropna(subset=[args.target]).reset_index(drop=True)
    if target_df.shape[0] < args.n_splits:
        raise ValueError(f"Need at least {args.n_splits} donors with finite target values.")

    groups = target_df["Donor ID"].to_numpy()
    y_for_split = target_df[args.target].to_numpy()
    if args.splitter == "stratified_groupkfold":
        y_for_split = make_strata(y_for_split, args.target_bins)
        splitter = StratifiedGroupKFold(n_splits=args.n_splits, shuffle=True, random_state=7)
    else:
        splitter = GroupKFold(n_splits=args.n_splits)
    folds = list(splitter.split(target_df, y_for_split, groups=groups))

    rows: list[dict[str, object]] = []
    prediction_rows: list[dict[str, object]] = []
    for label, path in args.feature_result:
        model_rows, model_prediction_rows = evaluate_feature_table(
            label=label,
            features_path=path,
            target_df=target_df,
            target=args.target,
            folds=folds,
            max_features=args.max_features,
            alpha=args.alpha,
            device=device,
            target_transform=args.target_transform,
        )
        rows.extend(model_rows)
        prediction_rows.extend(model_prediction_rows)
        if model_rows:
            print(f"{label}: mean Spearman={np.mean([row['spearman'] for row in model_rows]):.4f}")

    if args.finetune_h5ad and args.finetune_checkpoint:
        finetune_rows, finetune_prediction_rows = evaluate_pathology_finetune(
            h5ad_path=args.finetune_h5ad,
            checkpoint_path=args.finetune_checkpoint,
            target_df=target_df,
            target=args.target,
            folds=folds,
            args=args,
            device=device,
        )
        rows.extend(finetune_rows)
        prediction_rows.extend(finetune_prediction_rows)

    results = pd.DataFrame(rows)
    predictions = pd.DataFrame(prediction_rows)
    out_path = Path(args.out)
    summary_path = Path(args.summary_out)
    oof_path = Path(args.oof_out)
    oof_summary_path = Path(args.oof_summary_out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    oof_path.parent.mkdir(parents=True, exist_ok=True)
    oof_summary_path.parent.mkdir(parents=True, exist_ok=True)
    results.to_csv(out_path, index=False)
    predictions.to_csv(oof_path, index=False)
    summary = summarize(results)
    oof_summary = summarize_oof(predictions)
    summary.to_csv(summary_path, index=False)
    oof_summary.to_csv(oof_summary_path, index=False)
    print(summary.to_string(index=False))
    print(oof_summary.to_string(index=False))
    print(f"Wrote {out_path}")
    print(f"Wrote {summary_path}")
    print(f"Wrote {oof_path}")
    print(f"Wrote {oof_summary_path}")


if __name__ == "__main__":
    main()
