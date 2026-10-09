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


def infer_fast_model(checkpoint: dict, freeze: bool = True) -> FastGraphGeneJEPA:
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
        param.requires_grad = not freeze
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


def latent_geometry(embeddings: np.ndarray) -> dict[str, float]:
    centered = embeddings - embeddings.mean(axis=0, keepdims=True)
    singular_values = np.linalg.svd(centered, compute_uv=False)
    probs = singular_values / (singular_values.sum() + 1e-12)
    entropy = -np.sum(probs * np.log(probs + 1e-12))
    return {
        "effective_dims": float(np.exp(entropy)),
        "top_sv_ratio": float(probs[0]),
    }


def donor_prediction_from_cells(
    model: FastGraphGeneJEPA,
    head: nn.Module,
    matrix: torch.Tensor,
    donors: pd.Series,
    adj: torch.Tensor,
    device: torch.device,
    batch_size: int,
) -> tuple[pd.DataFrame, dict[str, float]]:
    model.eval()
    head.eval()
    embeddings = []
    predictions = []
    loader = DataLoader(TensorDataset(matrix), batch_size=batch_size, shuffle=False)
    with torch.no_grad():
        for (batch,) in loader:
            z = model.context_encoder(batch.to(device), adj, node_annotations=None)
            pred = head(z)
            embeddings.append(z.cpu().numpy())
            predictions.append(pred.cpu().numpy())
    z_all = np.concatenate(embeddings, axis=0)
    pred_all = np.concatenate(predictions, axis=0)
    pred_df = pd.DataFrame(pred_all)
    pred_df["Donor ID"] = donors.astype(str).to_numpy()
    donor_pred = pred_df.groupby("Donor ID", as_index=False).mean()
    return donor_pred, latent_geometry(z_all)


def train_finetuned_head(
    checkpoint: dict,
    gene_names: list[str],
    matrix: torch.Tensor,
    donors: pd.Series,
    donor_targets: pd.DataFrame,
    target_columns: list[str],
    train_donors: list[str],
    val_donors: list[str] | None,
    adj: torch.Tensor,
    head_kind: str,
    args: argparse.Namespace,
    device: torch.device,
    seed: int,
) -> tuple[pd.DataFrame, dict[str, float], FastGraphGeneJEPA, nn.Module, StandardScaler]:
    torch.manual_seed(seed)
    model = infer_fast_model(checkpoint, freeze=False).to(device)
    head = make_head(
        head_kind,
        int(checkpoint["model_state"]["context_encoder.out.weight"].shape[0]),
        len(target_columns),
        args.hidden_dim,
        args.dropout,
    ).to(device)

    train_donor_set = set(train_donors)
    train_mask = donors.astype(str).isin(train_donor_set).to_numpy()
    if val_donors is None:
        eval_mask = np.ones(len(donors), dtype=bool)
        eval_donors = sorted(train_donor_set)
    else:
        val_donor_set = set(val_donors)
        eval_mask = donors.astype(str).isin(val_donor_set).to_numpy()
        eval_donors = sorted(val_donor_set)

    train_y_raw = donor_targets.set_index("Donor ID").loc[sorted(train_donor_set), target_columns].to_numpy(dtype=np.float32)
    y_scaler = StandardScaler()
    y_scaler.fit(train_y_raw)
    donor_y_scaled = pd.DataFrame(
        y_scaler.transform(donor_targets.set_index("Donor ID")[target_columns].to_numpy(dtype=np.float32)),
        index=donor_targets["Donor ID"].astype(str),
        columns=target_columns,
    )

    train_x = matrix[train_mask]
    train_y = torch.from_numpy(
        np.vstack([donor_y_scaled.loc[str(donor)].to_numpy(dtype=np.float32) for donor in donors[train_mask]]).astype(np.float32)
    )
    loader = DataLoader(TensorDataset(train_x, train_y), batch_size=args.batch_size, shuffle=True)
    optimizer = torch.optim.AdamW(
        [
            {"params": model.context_encoder.parameters(), "lr": args.base_lr},
            {"params": head.parameters(), "lr": args.head_lr},
        ],
        weight_decay=args.weight_decay,
    )

    best_eval_score = -np.inf
    best_metrics: dict[str, float] = {}
    for epoch in range(1, args.epochs + 1):
        model.train()
        head.train()
        losses = []
        for xb, yb in loader:
            z = model.context_encoder(xb.to(device), adj, node_annotations=None)
            pred = head(z)
            loss = nn.functional.smooth_l1_loss(pred, yb.to(device))
            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            if args.gradient_clip_val > 0:
                torch.nn.utils.clip_grad_norm_(list(model.context_encoder.parameters()) + list(head.parameters()), args.gradient_clip_val)
            optimizer.step()
            losses.append(float(loss.detach().cpu()))

        donor_pred_scaled, geometry = donor_prediction_from_cells(model, head, matrix[eval_mask], donors[eval_mask].reset_index(drop=True), adj, device, args.embedding_batch_size)
        if geometry["effective_dims"] < args.min_effective_dims or geometry["top_sv_ratio"] > args.max_top_sv_ratio:
            raise RuntimeError("Geometry collapse detected. Aborting training.")
        pred_scaled = donor_pred_scaled.set_index("Donor ID").loc[eval_donors].to_numpy(dtype=np.float32)
        pred = y_scaler.inverse_transform(pred_scaled)
        truth = donor_targets.set_index("Donor ID").loc[eval_donors, target_columns].to_numpy(dtype=np.float32)
        target_scores = [spearman_safe(truth[:, i], pred[:, i]) for i in range(len(target_columns))]
        mean_score = float(np.nanmean(target_scores))
        if mean_score > best_eval_score:
            best_eval_score = mean_score
            best_metrics = {
                "epoch": epoch,
                "loss": float(np.mean(losses)),
                "mean_spearman": mean_score,
                "effective_dims": geometry["effective_dims"],
                "top_sv_ratio": geometry["top_sv_ratio"],
            }
        print(
            f"epoch={epoch:03d} loss={np.mean(losses):.5f} mean_spearman={mean_score:.3f} "
            f"eff={geometry['effective_dims']:.2f} top_sv={geometry['top_sv_ratio']:.3f}",
            flush=True,
        )

    donor_pred_scaled, geometry = donor_prediction_from_cells(model, head, matrix[eval_mask], donors[eval_mask].reset_index(drop=True), adj, device, args.embedding_batch_size)
    pred_scaled = donor_pred_scaled.set_index("Donor ID").loc[eval_donors].to_numpy(dtype=np.float32)
    pred = y_scaler.inverse_transform(pred_scaled)
    pred_df = pd.DataFrame(pred, columns=target_columns)
    pred_df.insert(0, "Donor ID", eval_donors)
    final_metrics = {**best_metrics, "final_effective_dims": geometry["effective_dims"], "final_top_sv_ratio": geometry["top_sv_ratio"]}
    return pred_df, final_metrics, model.cpu(), head.cpu(), y_scaler


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
    parser.add_argument("--unfreeze-encoder", action="store_true")
    parser.add_argument("--base-lr", type=float, default=5e-6)
    parser.add_argument("--head-lr", type=float, default=5e-5)
    parser.add_argument("--full-train", action="store_true")
    parser.add_argument("--min-effective-dims", type=float, default=20.0)
    parser.add_argument("--max-top-sv-ratio", type=float, default=0.35)
    parser.add_argument("--gradient-clip-val", type=float, default=1.0)
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

    if args.unfreeze_encoder and args.epochs == 500:
        args.epochs = 50
        print("unfreeze-encoder requested with default epochs=500; using safer fine-tuning default epochs=50")

    print(f"Loading Graph-JEPA checkpoint: {args.checkpoint}")
    checkpoint = torch.load(args.checkpoint, map_location="cpu", weights_only=False)
    model = infer_fast_model(checkpoint).to(device)

    print("Loading SEA-AD Microglia-PVM matrix")
    disease_x, gene_names, obs = dense_h5ad(args.disease_h5ad)
    edge_index = load_consensus_edge_index(args.edge_csv)
    adj = normalized_adjacency(edge_index, len(gene_names), 0.0, device)

    targets, _ = load_pathology_targets(args.targets_path, args.target_columns_path)
    targets = targets.copy()
    targets["Donor ID"] = normalize_donor_id(targets["Donor ID"])
    donors_all = normalize_donor_id(obs[args.donor_column]).reset_index(drop=True)

    if args.unfreeze_encoder:
        print("Running forked-backbone fine-tuning mode")
        donor_frame = pd.DataFrame({"Donor ID": sorted(donors_all.unique())})
        donor_targets = donor_frame.merge(targets[["Donor ID", *args.targets]], on="Donor ID", how="inner").dropna(subset=args.targets)
        donor_list = donor_targets["Donor ID"].astype(str).tolist()
        if args.full_train:
            head_kind = args.heads[0]
            pred_df, metrics_dict, ft_model, ft_head, y_scaler = train_finetuned_head(
                checkpoint,
                gene_names,
                disease_x,
                donors_all,
                donor_targets,
                args.targets,
                donor_list,
                None,
                adj,
                head_kind,
                args,
                device,
                args.seed,
            )
            metrics = []
            for target_idx, target in enumerate(args.targets):
                y_true = donor_targets.set_index("Donor ID").loc[pred_df["Donor ID"], target].to_numpy(dtype=np.float32)
                y_pred = pred_df[target].to_numpy(dtype=np.float32)
                metrics.append(
                    {
                        "head": f"finetuned_{head_kind}",
                        "target": target,
                        "oof_spearman": spearman_safe(y_true, y_pred),
                        "n_donors": int(len(donor_list)),
                        "n_splits": 0,
                        "epochs": args.epochs,
                        "hidden_dim": args.hidden_dim if head_kind == "mlp" else 0,
                        "dropout": args.dropout if head_kind == "mlp" else 0.0,
                        "lr": args.head_lr,
                        "base_lr": args.base_lr,
                        "weight_decay": args.weight_decay,
                        **metrics_dict,
                    }
                )
            out_dir.mkdir(parents=True, exist_ok=True)
            torch.save(
                {
                    "model_state": ft_model.state_dict(),
                    "n_genes": len(gene_names),
                    "gene_names": gene_names,
                    "source_checkpoint": args.checkpoint,
                    "args": vars(args),
                    "model_class": "FastGraphGeneJEPA",
                },
                out_dir / "fine_tuned_encoder.pt",
            )
            torch.save(
                {
                    "head_kind": head_kind,
                    "head_state": ft_head.state_dict(),
                    "targets": args.targets,
                    "x_mean": np.zeros(int(checkpoint["model_state"]["context_encoder.out.weight"].shape[0]), dtype=np.float32),
                    "x_scale": np.ones(int(checkpoint["model_state"]["context_encoder.out.weight"].shape[0]), dtype=np.float32),
                    "y_mean": y_scaler.mean_,
                    "y_scale": y_scaler.scale_,
                    "latent_dim": int(checkpoint["model_state"]["context_encoder.out.weight"].shape[0]),
                    "hidden_dim": args.hidden_dim,
                    "dropout": args.dropout,
                    "source_checkpoint": str(out_dir / "fine_tuned_encoder.pt"),
                    "mean_oof_spearman": float(np.nanmean([row["oof_spearman"] for row in metrics])),
                },
                out_dir / "best_pathology_head.pt",
            )
            Path(args.metrics_out).parent.mkdir(parents=True, exist_ok=True)
            pd.DataFrame(metrics).to_csv(args.metrics_out, index=False)
            Path(args.predictions_out).parent.mkdir(parents=True, exist_ok=True)
            pred_df.to_csv(args.predictions_out, index=False)
            print(f"Wrote final fine-tuned encoder: {out_dir / 'fine_tuned_encoder.pt'}")
            print(f"Wrote final pathology head: {out_dir / 'best_pathology_head.pt'}")
            print(f"Wrote metrics: {args.metrics_out}")
            print(f"Wrote predictions: {args.predictions_out}")
            return

        kfold = KFold(n_splits=args.n_splits, shuffle=True, random_state=args.seed)
        prediction_rows = []
        metrics = []
        head_kind = args.heads[0]
        oof = np.full((len(donor_list), len(args.targets)), np.nan, dtype=np.float32)
        donor_index = {donor: idx for idx, donor in enumerate(donor_list)}
        fold_geometry = []
        for fold, (train_idx, val_idx) in enumerate(kfold.split(donor_list), start=1):
            train_donors = [donor_list[i] for i in train_idx]
            val_donors = [donor_list[i] for i in val_idx]
            print(f"Fold {fold}: train donors={len(train_donors)} val donors={len(val_donors)}")
            pred_df, metrics_dict, _, _, _ = train_finetuned_head(
                checkpoint,
                gene_names,
                disease_x,
                donors_all,
                donor_targets,
                args.targets,
                train_donors,
                val_donors,
                adj,
                head_kind,
                args,
                device,
                args.seed + fold,
            )
            fold_geometry.append(metrics_dict)
            for _, row in pred_df.iterrows():
                donor = str(row["Donor ID"])
                for target_idx, target in enumerate(args.targets):
                    oof[donor_index[donor], target_idx] = float(row[target])
                    prediction_rows.append(
                        {
                            "head": f"finetuned_{head_kind}",
                            "fold": fold,
                            "Donor ID": donor,
                            "target": target,
                            "y_true": float(donor_targets.set_index("Donor ID").loc[donor, target]),
                            "y_pred": float(row[target]),
                        }
                    )
        truth = donor_targets.set_index("Donor ID").loc[donor_list, args.targets].to_numpy(dtype=np.float32)
        for target_idx, target in enumerate(args.targets):
            rho = spearman_safe(truth[:, target_idx], oof[:, target_idx])
            metrics.append(
                {
                    "head": f"finetuned_{head_kind}",
                    "target": target,
                    "oof_spearman": rho,
                    "n_donors": int(len(donor_list)),
                    "n_splits": args.n_splits,
                    "epochs": args.epochs,
                    "hidden_dim": args.hidden_dim if head_kind == "mlp" else 0,
                    "dropout": args.dropout if head_kind == "mlp" else 0.0,
                    "lr": args.head_lr,
                    "base_lr": args.base_lr,
                    "weight_decay": args.weight_decay,
                    "min_fold_effective_dims": float(np.nanmin([m["final_effective_dims"] for m in fold_geometry])),
                    "max_fold_top_sv_ratio": float(np.nanmax([m["final_top_sv_ratio"] for m in fold_geometry])),
                }
            )
        Path(args.metrics_out).parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(metrics).to_csv(args.metrics_out, index=False)
        Path(args.predictions_out).parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(prediction_rows).to_csv(args.predictions_out, index=False)
        print(pd.DataFrame(metrics).to_string(index=False))
        print(f"Wrote CV metrics: {args.metrics_out}")
        print(f"Wrote CV predictions: {args.predictions_out}")
        return

    print("Encoding frozen backbone embeddings")
    cell_z = extract_cell_embeddings(model, disease_x, adj, device, args.embedding_batch_size)
    donor_z = donor_embeddings(cell_z, obs, args.donor_column)
    Path(args.donor_embeddings_out).parent.mkdir(parents=True, exist_ok=True)
    donor_z.to_csv(args.donor_embeddings_out, index=False)
    print(f"Wrote donor embeddings: {args.donor_embeddings_out}")

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
