from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import anndata as ad
import numpy as np
import pandas as pd
import torch
from scipy import sparse
from scipy.stats import spearmanr
from sklearn.model_selection import KFold
from sklearn.preprocessing import StandardScaler
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

from sea_ad_jepa.data import load_pathology_targets, normalize_donor_id
from sea_ad_jepa.graph_data import load_consensus_edge_index
from sea_ad_jepa.graph_jepa import FastGraphGeneJEPA
from scripts.train_graph_jepa_stage_a_fast import choose_device, normalized_adjacency


def dense_h5ad(path: str) -> tuple[torch.Tensor, list[str], pd.DataFrame]:
    adata = ad.read_h5ad(path)
    x = adata.X
    if sparse.issparse(x):
        x = x.toarray()
    return torch.from_numpy(np.asarray(x, dtype=np.float32)), adata.var_names.astype(str).tolist(), adata.obs.copy()


def infer_fast_model(checkpoint: dict) -> FastGraphGeneJEPA:
    state = checkpoint["model_state"]
    n_genes = int(checkpoint["n_genes"])
    gene_embed_dim = int(state["context_encoder.gene_embedding.weight"].shape[1])
    hidden_dim = int(state["context_encoder.input_proj.0.weight"].shape[0])
    latent_dim = int(state["context_encoder.out.weight"].shape[0])
    n_layers = len([key for key in state if key.startswith("context_encoder.self_linears.") and key.endswith(".weight")])
    model = FastGraphGeneJEPA(
        n_genes=n_genes,
        node_feature_dim=1,
        gene_embed_dim=gene_embed_dim,
        hidden_dim=hidden_dim,
        latent_dim=latent_dim,
        n_layers=n_layers,
        dropout=0.0,
        ema_decay=1.0,
    )
    model.load_state_dict(state)
    for param in model.parameters():
        param.requires_grad = False
    return model


@torch.no_grad()
def extract_cell_embeddings(
    model: FastGraphGeneJEPA,
    matrix: torch.Tensor,
    adj: torch.Tensor,
    device: torch.device,
    batch_size: int,
) -> np.ndarray:
    model.eval()
    chunks = []
    loader = DataLoader(TensorDataset(matrix), batch_size=batch_size, shuffle=False)
    for (batch,) in loader:
        z = model.context_encoder(batch.to(device), adj, node_annotations=None)
        chunks.append(z.cpu().numpy())
    return np.concatenate(chunks, axis=0)


def donor_embeddings(cell_embeddings: np.ndarray, obs: pd.DataFrame, donor_column: str) -> pd.DataFrame:
    donors = normalize_donor_id(obs[donor_column]).reset_index(drop=True)
    emb = pd.DataFrame(cell_embeddings, columns=[f"z_{i}" for i in range(cell_embeddings.shape[1])])
    emb["Donor ID"] = donors.values
    return emb.groupby("Donor ID", as_index=False).mean()


def make_head(kind: str, input_dim: int, output_dim: int, hidden_dim: int, dropout: float) -> nn.Module:
    if kind == "linear":
        return nn.Linear(input_dim, output_dim)
    if kind == "mlp":
        return nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, output_dim),
        )
    raise ValueError(f"Unknown head kind: {kind}")


def train_head(
    x_train: np.ndarray,
    y_train: np.ndarray,
    x_val: np.ndarray,
    kind: str,
    hidden_dim: int,
    dropout: float,
    epochs: int,
    lr: float,
    weight_decay: float,
    batch_size: int,
    device: torch.device,
    seed: int,
) -> tuple[np.ndarray, nn.Module, StandardScaler, StandardScaler]:
    torch.manual_seed(seed)
    x_scaler = StandardScaler()
    y_scaler = StandardScaler()
    x_train_scaled = x_scaler.fit_transform(x_train).astype(np.float32)
    y_train_scaled = y_scaler.fit_transform(y_train).astype(np.float32)
    x_val_scaled = x_scaler.transform(x_val).astype(np.float32)

    head = make_head(kind, x_train.shape[1], y_train.shape[1], hidden_dim, dropout).to(device)
    opt = torch.optim.AdamW(head.parameters(), lr=lr, weight_decay=weight_decay)
    loader = DataLoader(
        TensorDataset(torch.from_numpy(x_train_scaled), torch.from_numpy(y_train_scaled)),
        batch_size=batch_size,
        shuffle=True,
    )
    head.train()
    for _ in range(epochs):
        for xb, yb in loader:
            pred = head(xb.to(device))
            loss = nn.functional.smooth_l1_loss(pred, yb.to(device))
            opt.zero_grad(set_to_none=True)
            loss.backward()
            opt.step()

    head.eval()
    with torch.no_grad():
        pred_scaled = head(torch.from_numpy(x_val_scaled).to(device)).cpu().numpy()
    pred = y_scaler.inverse_transform(pred_scaled)
    return pred, head.cpu(), x_scaler, y_scaler


def spearman_safe(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    if len(y_true) < 3 or np.nanstd(y_true) == 0 or np.nanstd(y_pred) == 0:
        return float("nan")
    rho, _ = spearmanr(y_true, y_pred)
    return float(rho)


def main() -> None:
    parser = argparse.ArgumentParser(description="Frozen Graph-JEPA backbone plus donor-level pathology heads.")
    parser.add_argument("--checkpoint", default="results/models/v2_2_stage_b_adversarial/stage_b_adversarial.pt")
    parser.add_argument("--disease-h5ad", default="data/processed/sea_ad_mtg_microglia_pvm_all_hvg3k_expanded_modules.h5ad")
    parser.add_argument("--edge-csv", default="results/tables/v2_graph_consensus_edge_index.csv")
    parser.add_argument("--targets-path", default="data/processed/metadata/sea_ad_mtg_donor_pathology_targets.csv")
    parser.add_argument("--target-columns-path", default="data/processed/metadata/pathology_target_columns.csv")
    parser.add_argument("--targets", nargs="+", default=[
        "percent AT8 positive area_Grey matter",
        "percent NeuN positive area_Grey matter",
        "percent GFAP positive area_Grey matter",
        "percent Iba1 positive area_Grey matter",
        "percent 6e10 positive area_Grey matter",
    ])
    parser.add_argument("--donor-column", default="Donor ID")
    parser.add_argument("--heads", nargs="+", choices=["linear", "mlp"], default=["linear", "mlp"])
    parser.add_argument("--n-splits", type=int, default=5)
    parser.add_argument("--epochs", type=int, default=500)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--weight-decay", type=float, default=1e-3)
    parser.add_argument("--hidden-dim", type=int, default=64)
    parser.add_argument("--dropout", type=float, default=0.15)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--embedding-batch-size", type=int, default=512)
    parser.add_argument("--out-dir", default="results/models/pathology_heads")
    parser.add_argument("--metrics-out", default="results/tables/pathology_mlp_head_metrics.csv")
    parser.add_argument("--predictions-out", default="results/tables/pathology_mlp_head_oof_predictions.csv")
    parser.add_argument("--donor-embeddings-out", default="results/tables/pathology_head_frozen_backbone_donor_embeddings.csv")
    parser.add_argument("--device", default="auto")
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()

    device = choose_device(args.device)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Loading frozen Graph-JEPA checkpoint: {args.checkpoint}")
    checkpoint = torch.load(args.checkpoint, map_location="cpu", weights_only=False)
    model = infer_fast_model(checkpoint).to(device)

    print("Loading SEA-AD Microglia-PVM matrix")
    disease_x, gene_names, obs = dense_h5ad(args.disease_h5ad)
    edge_index = load_consensus_edge_index(args.edge_csv)
    adj = normalized_adjacency(edge_index, len(gene_names), 0.0, device)

    print("Encoding frozen backbone embeddings")
    cell_z = extract_cell_embeddings(model, disease_x, adj, device, args.embedding_batch_size)
    donor_z = donor_embeddings(cell_z, obs, args.donor_column)
    Path(args.donor_embeddings_out).parent.mkdir(parents=True, exist_ok=True)
    donor_z.to_csv(args.donor_embeddings_out, index=False)
    print(f"Wrote donor embeddings: {args.donor_embeddings_out}")

    targets, _ = load_pathology_targets(args.targets_path, args.target_columns_path)
    targets = targets.copy()
    targets["Donor ID"] = normalize_donor_id(targets["Donor ID"])
    merged = donor_z.merge(targets[["Donor ID", *args.targets]], on="Donor ID", how="inner")
    z_cols = [col for col in merged.columns if col.startswith("z_")]
    x_all = merged[z_cols].to_numpy(dtype=np.float32)
    y_all = merged[args.targets].to_numpy(dtype=np.float32)
    valid = np.isfinite(y_all).all(axis=1)
    merged = merged.loc[valid].reset_index(drop=True)
    x_all = x_all[valid]
    y_all = y_all[valid]
    print(f"Training heads on {x_all.shape[0]} donors x {x_all.shape[1]} latent dims")

    kfold = KFold(n_splits=args.n_splits, shuffle=True, random_state=args.seed)
    metrics = []
    prediction_rows = []
    best_score = -np.inf
    best_payload: dict | None = None

    for head_kind in args.heads:
        oof = np.full_like(y_all, np.nan, dtype=np.float32)
        fold_scores = []
        for fold, (train_idx, val_idx) in enumerate(kfold.split(x_all), start=1):
            pred, head, x_scaler, y_scaler = train_head(
                x_all[train_idx],
                y_all[train_idx],
                x_all[val_idx],
                head_kind,
                args.hidden_dim,
                args.dropout,
                args.epochs,
                args.lr,
                args.weight_decay,
                args.batch_size,
                device,
                args.seed + fold,
            )
            oof[val_idx] = pred.astype(np.float32)
            fold_rhos = [spearman_safe(y_all[val_idx, i], pred[:, i]) for i in range(len(args.targets))]
            fold_scores.append(float(np.nanmean(fold_rhos)))
            for row_idx, donor_idx in enumerate(val_idx):
                for target_idx, target in enumerate(args.targets):
                    prediction_rows.append(
                        {
                            "head": head_kind,
                            "fold": fold,
                            "Donor ID": merged.loc[donor_idx, "Donor ID"],
                            "target": target,
                            "y_true": float(y_all[donor_idx, target_idx]),
                            "y_pred": float(pred[row_idx, target_idx]),
                        }
                    )

        target_scores = []
        for target_idx, target in enumerate(args.targets):
            rho = spearman_safe(y_all[:, target_idx], oof[:, target_idx])
            target_scores.append(rho)
            metrics.append(
                {
                    "head": head_kind,
                    "target": target,
                    "oof_spearman": rho,
                    "n_donors": int(x_all.shape[0]),
                    "n_splits": args.n_splits,
                    "epochs": args.epochs,
                    "hidden_dim": args.hidden_dim if head_kind == "mlp" else 0,
                    "dropout": args.dropout if head_kind == "mlp" else 0.0,
                    "lr": args.lr,
                    "weight_decay": args.weight_decay,
                }
            )
        mean_score = float(np.nanmean(target_scores))
        print(f"{head_kind} mean OOF Spearman: {mean_score:.3f}")
        for target, rho in zip(args.targets, target_scores):
            print(f"  {target}: {rho:.3f}")

        if mean_score > best_score:
            best_score = mean_score
            full_pred, full_head, full_x_scaler, full_y_scaler = train_head(
                x_all,
                y_all,
                x_all,
                head_kind,
                args.hidden_dim,
                args.dropout,
                args.epochs,
                args.lr,
                args.weight_decay,
                args.batch_size,
                device,
                args.seed,
            )
            best_payload = {
                "head_kind": head_kind,
                "head_state": full_head.state_dict(),
                "targets": args.targets,
                "x_mean": full_x_scaler.mean_,
                "x_scale": full_x_scaler.scale_,
                "y_mean": full_y_scaler.mean_,
                "y_scale": full_y_scaler.scale_,
                "latent_dim": x_all.shape[1],
                "hidden_dim": args.hidden_dim,
                "dropout": args.dropout,
                "source_checkpoint": args.checkpoint,
                "mean_oof_spearman": mean_score,
            }

    metrics_out = Path(args.metrics_out)
    metrics_out.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(metrics).to_csv(metrics_out, index=False)
    predictions_out = Path(args.predictions_out)
    predictions_out.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(prediction_rows).to_csv(predictions_out, index=False)
    print(f"Wrote metrics: {metrics_out}")
    print(f"Wrote OOF predictions: {predictions_out}")

    if best_payload is not None:
        checkpoint_path = out_dir / "best_pathology_head.pt"
        torch.save(best_payload, checkpoint_path)
        print(f"Wrote best pathology head: {checkpoint_path}")


if __name__ == "__main__":
    main()
