from __future__ import annotations

import argparse
from pathlib import Path

import anndata as ad
import numpy as np
import pandas as pd
import torch
from scipy import sparse
from torch import nn
from torch.utils.data import DataLoader, TensorDataset, WeightedRandomSampler

from sea_ad_jepa.baselines import spearman_corr
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
    checkpoint_path: str,
    x: torch.Tensor,
    donors: pd.Series,
    y_transformed: np.ndarray,
    train_idx: np.ndarray,
    val_idx: np.ndarray,
    label_lookup: pd.Series,
    device: torch.device,
    epochs: int = 15,
    batch_size: int = 512,
    samples_per_epoch: int = 40000,
    lr: float = 5e-5,
    weight_decay: float = 1e-4,
    head_hidden_dim: int = 128,
    dropout: float = 0.1,
    freeze_encoder: bool = True,
    target_transform: str = "log1p",
    finetune_label: str = "pathology_aware_jepa",
) -> tuple[GeneJEPA, PathologyRegressor, dict[str, object], float, float]:
    model, checkpoint = load_jepa(checkpoint_path, device)
    model_args = checkpoint.get("args", {})
    latent_dim = int(model_args.get("latent_dim", 128))
    if freeze_encoder:
        for param in model.context_encoder.parameters():
            param.requires_grad = False

    head = PathologyRegressor(
        latent_dim=latent_dim,
        hidden_dim=head_hidden_dim,
        dropout=dropout,
    ).to(device)

    train_mean = float(np.mean(y_transformed[train_idx]))
    train_std = float(np.std(y_transformed[train_idx])) or 1.0
    y_z = torch.as_tensor((y_transformed - train_mean) / train_std, dtype=torch.float32)
    train_dataset = TensorDataset(x[train_idx], y_z[train_idx])
    sampler = build_balanced_sampler(donors, train_idx, samples_per_epoch or train_idx.size)
    loader = DataLoader(train_dataset, batch_size=batch_size, sampler=sampler, drop_last=False)

    params = list(head.parameters()) + [param for param in model.context_encoder.parameters() if param.requires_grad]
    optimizer = torch.optim.AdamW(params, lr=lr, weight_decay=weight_decay)
    loss_fn = nn.MSELoss()
    best_state = None
    best_row: dict[str, object] | None = None
    best_spearman = -np.inf

    for epoch in range(1, epochs + 1):
        model.train()
        if freeze_encoder:
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
            batch_size=batch_size,
            train_mean=train_mean,
            train_std=train_std,
            target_transform=target_transform,
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
