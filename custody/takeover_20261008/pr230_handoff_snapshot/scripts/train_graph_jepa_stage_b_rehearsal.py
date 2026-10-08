from __future__ import annotations

import argparse
import itertools
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import anndata as ad
import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F
from torch_geometric.loader import DataLoader

from sea_ad_jepa.graph_data import GraphExpressionDataset, load_consensus_edge_index, node_annotation_tensor
from sea_ad_jepa.graph_jepa import GraphGeneJEPA
from sea_ad_jepa.jepa import jepa_loss


def choose_device(requested: str) -> torch.device:
    if requested == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    return torch.device(requested)


def create_summary_writer(log_dir: str):
    if not log_dir:
        return None
    from torch.utils.tensorboard import SummaryWriter

    return SummaryWriter(log_dir)


def linear_schedule(epoch: int, start: float, end: float, warmup_epochs: int) -> float:
    if warmup_epochs <= 1:
        return end
    step = min(max(epoch - 1, 0), warmup_epochs - 1)
    frac = step / float(warmup_epochs - 1)
    return start + frac * (end - start)


def load_frozen_latents(path: str | Path) -> torch.Tensor:
    df = pd.read_csv(path)
    z_cols = [col for col in df.columns if col.startswith("z_")]
    if not z_cols:
        raise ValueError(f"No z_* latent columns found in {path}")
    return torch.as_tensor(df[z_cols].to_numpy(dtype=np.float32), dtype=torch.float32)


def make_dataset(h5ad: str, edge_index: torch.Tensor, node_annotations: torch.Tensor | None, mask_fraction: float, seed: int):
    adata = ad.read_h5ad(h5ad)
    dataset = GraphExpressionDataset(
        adata.X,
        edge_index=edge_index,
        node_annotations=node_annotations,
        mask_fraction=mask_fraction,
        seed=seed,
        return_pyg_data=True,
    )
    return adata, dataset


def rehearsal_loss(current_z: torch.Tensor, frozen_bank: torch.Tensor, sample_id: torch.Tensor) -> torch.Tensor:
    frozen = frozen_bank[sample_id.long()].to(current_z.device)
    return F.mse_loss(F.normalize(current_z, dim=-1), F.normalize(frozen, dim=-1))


def main() -> None:
    parser = argparse.ArgumentParser(description="Stage B Graph-JEPA calibration with frozen-coordinate rehearsal.")
    parser.add_argument("--checkpoint", default="results/models/graph_jepa_stage_a_string_t700_rawvar_e30/graph_jepa.pt")
    parser.add_argument("--primary-h5ad", default="data/processed/v2_pretraining/sea_ad_low_pathology_microglia_pvm_relaxed_jepa_aligned.h5ad")
    parser.add_argument("--primary-coordinates", default="results/tables/stage_a_frozen_sea_ad_low_pathology_relaxed_coordinates.csv")
    parser.add_argument("--rehearsal-h5ad", default="data/processed/v2_pretraining/cellxgene_normal_microglia_nucleus_relaxed_assay_jepa_aligned.h5ad")
    parser.add_argument("--rehearsal-coordinates", default="results/tables/stage_a_frozen_cellxgene_normal_microglia_coordinates.csv")
    parser.add_argument("--edge-csv", default="results/tables/v2_graph_string_edges_t700.csv")
    parser.add_argument("--annotation-csv", default="results/tables/jepa_v2_translational_actionability_matrix.csv")
    parser.add_argument("--out-dir", default="results/models/graph_jepa_stage_b_low_pathology_rehearsal_e20")
    parser.add_argument("--log-dir", default="runs/graph_jepa_stage_b_low_pathology_rehearsal_e20")
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--checkpoint-every", type=int, default=5)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--rehearsal-batch-size", type=int, default=16)
    parser.add_argument("--primary-rehearsal-weight", type=float, default=0.25)
    parser.add_argument("--external-rehearsal-weight", type=float, default=0.25)
    parser.add_argument("--variance-weight", type=float, default=1.0)
    parser.add_argument("--variance-gamma", type=float, default=1.0)
    parser.add_argument("--covariance-weight", type=float, default=0.0)
    parser.add_argument("--mask-start-fraction", type=float, default=0.2)
    parser.add_argument("--mask-fraction", type=float, default=0.5)
    parser.add_argument("--mask-warmup-epochs", type=int, default=10)
    parser.add_argument("--ema-start-decay", type=float, default=0.992)
    parser.add_argument("--ema-decay", type=float, default=0.9995)
    parser.add_argument("--ema-warmup-epochs", type=int, default=10)
    parser.add_argument("--lr", type=float, default=5e-5)
    parser.add_argument("--weight-decay", type=float, default=1e-4)
    parser.add_argument("--gradient-clip-val", type=float, default=1.0)
    parser.add_argument("--use-node-annotations", action="store_true")
    parser.add_argument("--device", default="auto")
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()

    torch.manual_seed(args.seed)
    np.random.seed(args.seed)
    device = choose_device(args.device)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    checkpoint = torch.load(args.checkpoint, map_location="cpu", weights_only=False)
    ckpt_args = checkpoint.get("args", {})
    edge_index = load_consensus_edge_index(args.edge_csv)

    primary_adata = ad.read_h5ad(args.primary_h5ad)
    gene_names = primary_adata.var_names.astype(str).tolist()
    node_annotations = node_annotation_tensor(args.annotation_csv, gene_names) if args.use_node_annotations else None
    node_feature_dim = 1 + (int(node_annotations.shape[1]) if node_annotations is not None else 0)

    primary_dataset = GraphExpressionDataset(
        primary_adata.X,
        edge_index=edge_index,
        node_annotations=node_annotations,
        mask_fraction=args.mask_start_fraction,
        seed=args.seed,
        return_pyg_data=True,
    )
    rehearsal_adata, rehearsal_dataset = make_dataset(
        args.rehearsal_h5ad,
        edge_index=edge_index,
        node_annotations=node_annotations,
        mask_fraction=0.0,
        seed=args.seed + 1,
    )
    if primary_adata.n_vars != int(checkpoint["n_genes"]) or rehearsal_adata.n_vars != int(checkpoint["n_genes"]):
        raise ValueError("Primary/rehearsal H5AD gene counts must match checkpoint n_genes.")

    primary_frozen = load_frozen_latents(args.primary_coordinates)
    rehearsal_frozen = load_frozen_latents(args.rehearsal_coordinates)
    if primary_frozen.shape[0] != primary_adata.n_obs:
        raise ValueError("Primary coordinate rows do not match primary H5AD cells.")
    if rehearsal_frozen.shape[0] != rehearsal_adata.n_obs:
        raise ValueError("Rehearsal coordinate rows do not match rehearsal H5AD cells.")

    primary_loader = DataLoader(primary_dataset, batch_size=args.batch_size, shuffle=True)
    rehearsal_loader = DataLoader(rehearsal_dataset, batch_size=args.rehearsal_batch_size, shuffle=True)

    model = GraphGeneJEPA(
        n_genes=int(checkpoint["n_genes"]),
        node_feature_dim=node_feature_dim,
        gene_embed_dim=int(ckpt_args.get("gene_embed_dim", 32)),
        hidden_dim=int(ckpt_args.get("hidden_dim", 128)),
        latent_dim=int(ckpt_args.get("latent_dim", 128)),
        n_layers=int(ckpt_args.get("n_layers", 2)),
        dropout=float(ckpt_args.get("dropout", 0.1)),
        conv=str(ckpt_args.get("conv", "sage")),
        ema_decay=float(ckpt_args.get("ema_decay", 0.996)),
    ).to(device)
    model.load_state_dict(checkpoint["model_state"])

    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    writer = create_summary_writer(args.log_dir)
    history = []

    primary_frozen = primary_frozen.to(device)
    rehearsal_frozen = rehearsal_frozen.to(device)

    def save_checkpoint(path: Path) -> None:
        torch.save(
            {
                "model_state": model.state_dict(),
                "n_genes": int(checkpoint["n_genes"]),
                "gene_names": gene_names,
                "args": vars(args),
                "history": history,
            },
            path,
        )

    for epoch in range(1, args.epochs + 1):
        model.train()
        current_mask_fraction = linear_schedule(epoch, args.mask_start_fraction, args.mask_fraction, args.mask_warmup_epochs)
        current_ema_decay = linear_schedule(epoch, args.ema_start_decay, args.ema_decay, args.ema_warmup_epochs)
        primary_dataset.mask_fraction = current_mask_fraction
        model.ema_decay = current_ema_decay
        rehearsal_iter = itertools.cycle(rehearsal_loader)

        losses = []
        jepa_losses = []
        primary_rehearsal_losses = []
        external_rehearsal_losses = []
        variance_losses = []
        alignment_losses = []

        for primary_context, primary_target in primary_loader:
            rehearse_context, rehearse_target = next(rehearsal_iter)
            primary_context = primary_context.to(device)
            primary_target = primary_target.to(device)
            rehearse_target = rehearse_target.to(device)

            pred_z, target_z = model(primary_context, primary_target)
            base_loss, parts = jepa_loss(
                pred_z,
                target_z,
                variance_weight=args.variance_weight,
                variance_gamma=args.variance_gamma,
                covariance_weight=args.covariance_weight,
            )
            primary_current = model.context_encoder(primary_target)
            external_current = model.context_encoder(rehearse_target)
            primary_anchor_loss = rehearsal_loss(primary_current, primary_frozen, primary_target.sample_id)
            external_anchor_loss = rehearsal_loss(external_current, rehearsal_frozen, rehearse_target.sample_id)
            loss = (
                base_loss
                + args.primary_rehearsal_weight * primary_anchor_loss
                + args.external_rehearsal_weight * external_anchor_loss
            )

            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            if args.gradient_clip_val > 0:
                torch.nn.utils.clip_grad_norm_(model.parameters(), args.gradient_clip_val)
            optimizer.step()
            model.update_target_network()

            losses.append(float(loss.detach().cpu()))
            jepa_losses.append(float(base_loss.detach().cpu()))
            primary_rehearsal_losses.append(float(primary_anchor_loss.detach().cpu()))
            external_rehearsal_losses.append(float(external_anchor_loss.detach().cpu()))
            variance_losses.append(float(parts["variance"].cpu()))
            alignment_losses.append(float(parts["alignment"].cpu()))

        row = {
            "epoch": epoch,
            "loss": float(np.mean(losses)),
            "jepa_loss": float(np.mean(jepa_losses)),
            "primary_rehearsal_loss": float(np.mean(primary_rehearsal_losses)),
            "external_rehearsal_loss": float(np.mean(external_rehearsal_losses)),
            "alignment_loss": float(np.mean(alignment_losses)),
            "variance_loss": float(np.mean(variance_losses)),
            "mask_fraction": current_mask_fraction,
            "ema_decay": current_ema_decay,
        }
        history.append(row)
        for key, value in row.items():
            if key != "epoch":
                writer.add_scalar(f"train/{key}", value, epoch)
        print(
            f"epoch={epoch:03d} loss={row['loss']:.6f} jepa={row['jepa_loss']:.6f} "
            f"primary_rehearsal={row['primary_rehearsal_loss']:.6f} "
            f"external_rehearsal={row['external_rehearsal_loss']:.6f} "
            f"alignment={row['alignment_loss']:.6f} variance={row['variance_loss']:.6f}"
        )
        if args.checkpoint_every and epoch % args.checkpoint_every == 0:
            path = out_dir / f"graph_jepa_stage_b_epoch_{epoch:03d}.pt"
            save_checkpoint(path)
            print(f"Wrote interim checkpoint: {path}")

    save_checkpoint(out_dir / "graph_jepa_stage_b.pt")
    writer.flush()
    writer.close()
    print(f"Wrote {out_dir / 'graph_jepa_stage_b.pt'}")
    print(f"Wrote TensorBoard logs to {args.log_dir}")


if __name__ == "__main__":
    main()
