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
from sea_ad_jepa.mil_head import GatedAttentionMIL
from scripts.train_graph_jepa_stage_a_fast import choose_device, normalized_adjacency


def dense_h5ad(path: str) -> tuple[torch.Tensor, list[str], pd.DataFrame, pd.Index]:
    adata = ad.read_h5ad(path)
    x = adata.X
    if sparse.issparse(x):
        x = x.toarray()
    return (
        torch.from_numpy(np.asarray(x, dtype=np.float32)),
        adata.var_names.astype(str).tolist(),
        adata.obs.copy(),
        adata.obs_names.copy(),
    )


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
def encode_matrix(
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
    return np.concatenate(chunks, axis=0).astype(np.float32)


def sample_rows_by_donor(donors: pd.Series, max_cells: int, seed: int) -> np.ndarray:
    if max_cells <= 0 or max_cells >= len(donors):
        return np.arange(len(donors), dtype=np.int64)
    rng = np.random.default_rng(seed)
    per_donor = max(1, int(np.ceil(max_cells / donors.nunique())))
    sampled = []
    for _, idx in donors.groupby(donors).indices.items():
        idx = np.asarray(idx, dtype=np.int64)
        take = min(per_donor, idx.size)
        sampled.extend(rng.choice(idx, size=take, replace=False).tolist())
    sampled = np.asarray(sorted(sampled), dtype=np.int64)
    if sampled.size > max_cells:
        sampled = np.asarray(sorted(rng.choice(sampled, size=max_cells, replace=False)), dtype=np.int64)
    return sampled


def spearman_safe(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    valid = np.isfinite(y_true) & np.isfinite(y_pred)
    if int(valid.sum()) < 3 or np.nanstd(y_true[valid]) == 0 or np.nanstd(y_pred[valid]) == 0:
        return float("nan")
    rho, _ = spearmanr(y_true[valid], y_pred[valid])
    return float(rho)


def make_bags(
    embeddings: np.ndarray,
    donors: pd.Series,
    donor_targets: pd.DataFrame,
    target: str,
    cell_ids: pd.Index,
) -> tuple[dict[str, torch.Tensor], dict[str, list[str]], pd.DataFrame]:
    donor_targets = donor_targets.dropna(subset=[target]).copy()
    valid_donors = set(donor_targets["Donor ID"].astype(str))
    bags: dict[str, torch.Tensor] = {}
    bag_cell_ids: dict[str, list[str]] = {}
    for donor, indices in donors.groupby(donors).indices.items():
        donor = str(donor)
        if donor in valid_donors:
            indices = np.asarray(indices, dtype=np.int64)
            bags[donor] = torch.from_numpy(embeddings[indices])
            bag_cell_ids[donor] = [str(cell_ids[idx]) for idx in indices]
    donor_targets = donor_targets[donor_targets["Donor ID"].astype(str).isin(bags)].reset_index(drop=True)
    return bags, bag_cell_ids, donor_targets


def train_one_fold(
    bags: dict[str, torch.Tensor],
    donor_targets: pd.DataFrame,
    target: str,
    train_donors: list[str],
    val_donors: list[str],
    args: argparse.Namespace,
    device: torch.device,
    seed: int,
) -> tuple[pd.DataFrame, pd.DataFrame, GatedAttentionMIL, StandardScaler]:
    torch.manual_seed(seed)
    y_scaler = StandardScaler()
    train_y = donor_targets.set_index("Donor ID").loc[train_donors, target].to_numpy(dtype=np.float32)
    y_scaler.fit(train_y.reshape(-1, 1))
    head = GatedAttentionMIL(args.latent_dim, args.hidden_dim, args.dropout).to(device)
    optimizer = torch.optim.AdamW(head.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    rng = np.random.default_rng(seed)

    for epoch in range(1, args.epochs + 1):
        head.train()
        train_order = list(train_donors)
        rng.shuffle(train_order)
        epoch_losses = []
        for donor in train_order:
            x = bags[donor].to(device)
            if args.max_cells_per_bag > 0 and x.shape[0] > args.max_cells_per_bag:
                take = torch.randperm(x.shape[0], device=device)[: args.max_cells_per_bag]
                x = x[take]
            y_raw = donor_targets.set_index("Donor ID").loc[donor, target]
            y = torch.tensor(float(y_scaler.transform([[y_raw]])[0, 0]), dtype=torch.float32, device=device)
            pred, _ = head(x)
            loss = nn.functional.smooth_l1_loss(pred, y)
            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(head.parameters(), args.grad_clip)
            optimizer.step()
            epoch_losses.append(float(loss.detach().cpu()))
        if epoch % args.print_every == 0 or epoch == 1 or epoch == args.epochs:
            val_pred = predict_donors(head, bags, val_donors, y_scaler, device)
            y_true = donor_targets.set_index("Donor ID").loc[val_donors, target].to_numpy(dtype=np.float32)
            print(
                f"epoch={epoch:03d} loss={np.mean(epoch_losses):.4f} "
                f"val_spearman={spearman_safe(y_true, val_pred['y_pred'].to_numpy(dtype=np.float32)):.3f}"
            )

    pred_df = predict_donors(head, bags, val_donors, y_scaler, device)
    pred_df["y_true"] = donor_targets.set_index("Donor ID").loc[pred_df["Donor ID"], target].to_numpy(dtype=np.float32)
    attn_df = attention_for_donors(head, bags, val_donors, device)
    return pred_df, attn_df, head.cpu(), y_scaler


@torch.no_grad()
def predict_donors(
    head: GatedAttentionMIL,
    bags: dict[str, torch.Tensor],
    donors: list[str],
    y_scaler: StandardScaler,
    device: torch.device,
) -> pd.DataFrame:
    head.eval()
    rows = []
    for donor in donors:
        pred_scaled, _ = head(bags[donor].to(device))
        pred = y_scaler.inverse_transform([[float(pred_scaled.cpu())]])[0, 0]
        rows.append({"Donor ID": donor, "y_pred": float(pred)})
    return pd.DataFrame(rows)


@torch.no_grad()
def attention_for_donors(
    head: GatedAttentionMIL,
    bags: dict[str, torch.Tensor],
    donors: list[str],
    device: torch.device,
) -> pd.DataFrame:
    head.eval()
    rows = []
    for donor in donors:
        _, attention = head(bags[donor].to(device))
        weights = attention.cpu().numpy()
        for local_idx, weight in enumerate(weights):
            rows.append({"Donor ID": donor, "local_cell_index_in_donor_bag": local_idx, "attention_weight": float(weight)})
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Train a frozen-backbone gated-attention MIL head for 6e10.")
    parser.add_argument("--checkpoint", default="results/models/v2_2_stage_b_adversarial/stage_b_adversarial.pt")
    parser.add_argument("--h5ad", default="data/processed/sea_ad_mtg_microglia_pvm_all_hvg3k_expanded_modules.h5ad")
    parser.add_argument("--edge-csv", default="results/tables/v2_graph_consensus_edge_index.csv")
    parser.add_argument("--targets-path", default="data/processed/metadata/sea_ad_mtg_donor_pathology_targets.csv")
    parser.add_argument("--target-columns-path", default="data/processed/metadata/pathology_target_columns.csv")
    parser.add_argument("--target", default="percent 6e10 positive area_Grey matter")
    parser.add_argument("--donor-column", default="Donor ID")
    parser.add_argument("--max-cells", type=int, default=0)
    parser.add_argument("--max-cells-per-bag", type=int, default=512)
    parser.add_argument("--embedding-batch-size", type=int, default=512)
    parser.add_argument("--hidden-dim", type=int, default=64)
    parser.add_argument("--dropout", type=float, default=0.25)
    parser.add_argument("--epochs", type=int, default=200)
    parser.add_argument("--lr", type=float, default=3e-4)
    parser.add_argument("--weight-decay", type=float, default=1e-3)
    parser.add_argument("--grad-clip", type=float, default=5.0)
    parser.add_argument("--n-splits", type=int, default=5)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--print-every", type=int, default=25)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--out-dir", default="results/models/v2_2_abeta_mil_head")
    parser.add_argument("--metrics-out", default="results/tables/v2_2_abeta_mil_head_metrics.csv")
    parser.add_argument("--predictions-out", default="results/tables/v2_2_abeta_mil_head_oof_predictions.csv")
    parser.add_argument("--attention-out", default="results/tables/v2_2_abeta_mil_head_attention.csv")
    args = parser.parse_args()

    device = choose_device(args.device)
    print(f"Using device: {device}")
    matrix, gene_names, obs, cell_ids = dense_h5ad(args.h5ad)
    donors = normalize_donor_id(obs[args.donor_column]).reset_index(drop=True)
    rows = sample_rows_by_donor(donors, args.max_cells, args.seed)
    if rows.size != len(donors):
        matrix = torch.from_numpy(matrix.numpy()[rows].astype(np.float32, copy=True))
        donors = donors.iloc[rows].reset_index(drop=True)
        cell_ids = cell_ids[rows]
    print(f"Encoding {matrix.shape[0]:,} cells from {donors.nunique():,} donors")

    checkpoint = torch.load(args.checkpoint, map_location="cpu", weights_only=False)
    model = infer_fast_model(checkpoint).to(device)
    args.latent_dim = int(checkpoint["model_state"]["context_encoder.out.weight"].shape[0])
    edge_index = load_consensus_edge_index(args.edge_csv)
    adj = normalized_adjacency(edge_index, len(gene_names), 0.0, device)
    embeddings = encode_matrix(model, matrix, adj, device, args.embedding_batch_size)

    targets, _ = load_pathology_targets(args.targets_path, args.target_columns_path)
    targets["Donor ID"] = normalize_donor_id(targets["Donor ID"])
    bags, bag_cell_ids, donor_targets = make_bags(embeddings, donors, targets[["Donor ID", args.target]], args.target, cell_ids)
    donor_list = sorted(bags)
    print(f"Training MIL on {len(donor_list)} donors with valid {args.target}")

    kfold = KFold(n_splits=args.n_splits, shuffle=True, random_state=args.seed)
    prediction_rows = []
    attention_rows = []
    best_score = -np.inf
    best_payload = None
    for fold, (train_idx, val_idx) in enumerate(kfold.split(donor_list), start=1):
        print(f"\nFold {fold}")
        train_donors = [donor_list[i] for i in train_idx]
        val_donors = [donor_list[i] for i in val_idx]
        pred_df, attn_df, head, y_scaler = train_one_fold(
            bags,
            donor_targets,
            args.target,
            train_donors,
            val_donors,
            args,
            device,
            args.seed + fold,
        )
        pred_df.insert(0, "fold", fold)
        attn_df.insert(0, "fold", fold)
        prediction_rows.append(pred_df)
        attention_rows.append(attn_df)
        fold_score = spearman_safe(pred_df["y_true"].to_numpy(dtype=np.float32), pred_df["y_pred"].to_numpy(dtype=np.float32))
        if fold_score > best_score:
            best_score = fold_score
            best_payload = {
                "head_state": head.state_dict(),
                "target": args.target,
                "latent_dim": args.latent_dim,
                "hidden_dim": args.hidden_dim,
                "dropout": args.dropout,
                "y_mean": y_scaler.mean_,
                "y_scale": y_scaler.scale_,
                "source_checkpoint": args.checkpoint,
                "fold": fold,
                "fold_spearman": fold_score,
            }

    predictions = pd.concat(prediction_rows, ignore_index=True)
    oof_spearman = spearman_safe(predictions["y_true"].to_numpy(dtype=np.float32), predictions["y_pred"].to_numpy(dtype=np.float32))
    metrics = pd.DataFrame(
        [
            {
                "model": "gated_attention_mil",
                "target": args.target,
                "oof_spearman": oof_spearman,
                "n_donors": len(donor_list),
                "n_cells": int(matrix.shape[0]),
                "n_splits": args.n_splits,
                "epochs": args.epochs,
                "hidden_dim": args.hidden_dim,
                "dropout": args.dropout,
                "lr": args.lr,
                "weight_decay": args.weight_decay,
                "max_cells_per_bag": args.max_cells_per_bag,
            }
        ]
    )
    attention = pd.concat(attention_rows, ignore_index=True)
    cell_lookup = []
    for donor, ids in bag_cell_ids.items():
        for local_idx, cell_id in enumerate(ids):
            cell_lookup.append(
                {
                    "Donor ID": donor,
                    "local_cell_index_in_donor_bag": local_idx,
                    "cell_id": cell_id,
                }
            )
    attention = attention.merge(pd.DataFrame(cell_lookup), on=["Donor ID", "local_cell_index_in_donor_bag"], how="left")

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    if best_payload is not None:
        torch.save(best_payload, out_dir / "best_abeta_mil_head.pt")
    Path(args.metrics_out).parent.mkdir(parents=True, exist_ok=True)
    metrics.to_csv(args.metrics_out, index=False)
    predictions.to_csv(args.predictions_out, index=False)
    attention.to_csv(args.attention_out, index=False)
    print("\nMIL summary")
    print(metrics.to_string(index=False))
    print(f"Wrote metrics: {args.metrics_out}")
    print(f"Wrote predictions: {args.predictions_out}")
    print(f"Wrote attention: {args.attention_out}")


if __name__ == "__main__":
    main()
