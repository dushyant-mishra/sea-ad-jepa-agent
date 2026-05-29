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
from sea_ad_jepa.data import load_pathology_targets, normalize_donor_id
from sea_ad_jepa.jepa import GeneJEPA


def choose_device(requested: str) -> torch.device:
    if requested == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    return torch.device(requested)


def create_summary_writer(log_dir: str):
    if not log_dir:
        return None
    try:
        from torch.utils.tensorboard import SummaryWriter
    except ImportError as exc:
        raise RuntimeError(
            "TensorBoard logging is enabled, but tensorboard is not installed. "
            "Install it with `pip install tensorboard` or pass `--log-dir \"\"`."
        ) from exc
    return SummaryWriter(log_dir)


def to_dense_float32(matrix) -> np.ndarray:
    if sparse.issparse(matrix):
        matrix = matrix.toarray()
    return np.asarray(matrix, dtype=np.float32)


def donor_split(donors: pd.Series, train_fraction: float, seed: int) -> tuple[set[str], set[str]]:
    unique_donors = np.asarray(sorted(donors.unique()))
    rng = np.random.default_rng(seed)
    rng.shuffle(unique_donors)
    n_train = max(1, int(round(unique_donors.size * train_fraction)))
    n_train = min(n_train, unique_donors.size - 1)
    train_donors = set(unique_donors[:n_train])
    val_donors = set(unique_donors[n_train:])
    return train_donors, val_donors


def build_balanced_sampler(donors: pd.Series, indices: np.ndarray, samples_per_epoch: int) -> WeightedRandomSampler:
    donor_counts = donors.iloc[indices].value_counts()
    weights = donors.iloc[indices].map(lambda donor_id: 1.0 / float(donor_counts[donor_id])).to_numpy(dtype=np.float64)
    return WeightedRandomSampler(
        weights=torch.as_tensor(weights, dtype=torch.double),
        num_samples=samples_per_epoch or indices.size,
        replacement=True,
    )


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


def predict_by_donor(
    model: GeneJEPA,
    head: PathologyRegressor,
    x: torch.Tensor,
    donors: pd.Series,
    indices: np.ndarray,
    device: torch.device,
    batch_size: int,
) -> pd.DataFrame:
    dataset = TensorDataset(x[indices])
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=False)
    predictions = []
    model.eval()
    head.eval()
    with torch.no_grad():
        for (batch,) in loader:
            z = model.context_encoder(batch.to(device))
            pred = head(z)
            predictions.append(pred.cpu().numpy())

    pred_np = np.concatenate(predictions)
    pred_df = pd.DataFrame(
        {
            "Donor ID": donors.iloc[indices].to_numpy(),
            "prediction_z": pred_np,
        }
    )
    return pred_df.groupby("Donor ID", as_index=False)["prediction_z"].mean()


def main() -> None:
    parser = argparse.ArgumentParser(description="Fine-tune a JEPA encoder with donor-held-out pathology supervision.")
    parser.add_argument("--h5ad", required=True)
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--out-dir", default="results/models/jepa_pathology_finetuned")
    parser.add_argument("--target", default="percent AT8 positive area_Grey matter")
    parser.add_argument("--donor-column", default="Donor ID")
    parser.add_argument("--train-fraction", type=float, default=0.8)
    parser.add_argument("--epochs", type=int, default=50)
    parser.add_argument("--batch-size", type=int, default=512)
    parser.add_argument("--samples-per-epoch", type=int, default=0)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--head-hidden-dim", type=int, default=128)
    parser.add_argument("--dropout", type=float, default=0.1)
    parser.add_argument("--freeze-encoder", action="store_true")
    parser.add_argument("--device", default="auto")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument(
        "--log-dir",
        default="runs/jepa_pathology_finetune",
        help="TensorBoard log directory. Use an empty string to disable TensorBoard logging.",
    )
    args = parser.parse_args()

    torch.manual_seed(args.seed)
    np.random.seed(args.seed)
    device = choose_device(args.device)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    adata = ad.read_h5ad(args.h5ad)
    if args.donor_column not in adata.obs:
        raise KeyError(f"Donor column not found in AnnData obs: {args.donor_column}")
    donors = normalize_donor_id(adata.obs[args.donor_column]).reset_index(drop=True)

    targets, _ = load_pathology_targets()
    if args.target not in targets:
        raise KeyError(f"Target not found in pathology table: {args.target}")
    target_by_donor = targets[["Donor ID", args.target]].copy()
    target_by_donor["Donor ID"] = normalize_donor_id(target_by_donor["Donor ID"])
    target_by_donor[args.target] = pd.to_numeric(target_by_donor[args.target], errors="coerce")
    label_lookup = target_by_donor.set_index("Donor ID")[args.target]
    y = donors.map(label_lookup).to_numpy(dtype=np.float32)
    keep = np.isfinite(y)
    if keep.sum() < 10:
        raise ValueError(f"Too few cells have finite labels for target: {args.target}")

    x = torch.from_numpy(to_dense_float32(adata.X))
    checkpoint = torch.load(args.checkpoint, map_location="cpu", weights_only=False)
    model_args = checkpoint.get("args", {})
    model = GeneJEPA(
        input_dim=int(checkpoint["n_genes"]),
        hidden_dim=int(model_args.get("hidden_dim", 512)),
        latent_dim=int(model_args.get("latent_dim", 128)),
    ).to(device)
    model.load_state_dict(checkpoint["model_state"])
    if args.freeze_encoder:
        for param in model.context_encoder.parameters():
            param.requires_grad = False

    head = PathologyRegressor(
        latent_dim=int(model_args.get("latent_dim", 128)),
        hidden_dim=args.head_hidden_dim,
        dropout=args.dropout,
    ).to(device)

    labeled_donors = donors[keep]
    train_donors, val_donors = donor_split(labeled_donors, args.train_fraction, args.seed)
    train_idx = np.flatnonzero(keep & donors.isin(train_donors).to_numpy())
    val_idx = np.flatnonzero(keep & donors.isin(val_donors).to_numpy())

    train_mean = float(np.mean(y[train_idx]))
    train_std = float(np.std(y[train_idx])) or 1.0
    y_z = (y - train_mean) / train_std

    y_tensor = torch.as_tensor(y_z, dtype=torch.float32)
    train_dataset = TensorDataset(x[train_idx], y_tensor[train_idx])
    sampler = build_balanced_sampler(donors, train_idx, args.samples_per_epoch or train_idx.size)
    loader = DataLoader(train_dataset, batch_size=args.batch_size, sampler=sampler, drop_last=False)

    params = list(head.parameters()) + [param for param in model.context_encoder.parameters() if param.requires_grad]
    optimizer = torch.optim.AdamW(params, lr=args.lr, weight_decay=1e-4)
    loss_fn = nn.MSELoss()
    writer = create_summary_writer(args.log_dir)
    if writer is not None:
        writer.add_text("config/h5ad", args.h5ad)
        writer.add_text("config/checkpoint", args.checkpoint)
        writer.add_text("config/target", args.target)
        writer.add_scalar("config/train_donors", len(train_donors), 0)
        writer.add_scalar("config/val_donors", len(val_donors), 0)
        writer.add_scalar("config/freeze_encoder", float(args.freeze_encoder), 0)

    print(f"Target: {args.target}")
    print(f"Train donors: {len(train_donors)}; validation donors: {len(val_donors)}")
    print(f"Train cells: {train_idx.size:,}; validation cells: {val_idx.size:,}")

    best_spearman = -np.inf
    history = []
    for epoch in range(1, args.epochs + 1):
        model.train()
        head.train()
        losses = []
        for batch_x, batch_y in loader:
            batch_x = batch_x.to(device)
            batch_y = batch_y.to(device)
            z = model.context_encoder(batch_x)
            pred = head(z)
            loss = loss_fn(pred, batch_y)
            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            optimizer.step()
            losses.append(float(loss.detach().cpu()))

        train_loss = float(np.mean(losses))
        pred_by_donor = predict_by_donor(model, head, x, donors, val_idx, device, args.batch_size)
        pred_by_donor["prediction"] = pred_by_donor["prediction_z"] * train_std + train_mean
        val_truth = pred_by_donor["Donor ID"].map(label_lookup).to_numpy(dtype=np.float32)
        val_pred = pred_by_donor["prediction"].to_numpy(dtype=np.float32)
        val_spearman = spearman_corr(val_truth, val_pred)
        history.append({"epoch": epoch, "train_loss": train_loss, "val_spearman": val_spearman})
        if writer is not None:
            writer.add_scalar("train/loss_epoch", train_loss, epoch)
            writer.add_scalar("val/spearman_donor", val_spearman, epoch)
            writer.add_scalar("train/lr", optimizer.param_groups[0]["lr"], epoch)
        print(f"epoch={epoch:03d} train_loss={train_loss:.6f} val_spearman={val_spearman:.4f}")

        if np.isfinite(val_spearman) and val_spearman > best_spearman:
            best_spearman = val_spearman
            torch.save(
                {
                    "model_state": model.state_dict(),
                    "head_state": head.state_dict(),
                    "n_genes": adata.n_vars,
                    "gene_names": adata.var_names.astype(str).tolist(),
                    "target": args.target,
                    "train_mean": train_mean,
                    "train_std": train_std,
                    "args": vars(args),
                    "history": history,
                    "best_epoch": epoch,
                    "best_val_spearman": best_spearman,
                },
                out_dir / "jepa_pathology_finetuned.pt",
            )

    pd.DataFrame(history).to_csv(out_dir / "history.csv", index=False)
    if writer is not None:
        writer.flush()
        writer.close()
    print(f"Best validation Spearman: {best_spearman:.4f}")
    print(f"Wrote {out_dir / 'jepa_pathology_finetuned.pt'}")


if __name__ == "__main__":
    main()
