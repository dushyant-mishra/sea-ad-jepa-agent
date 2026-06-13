from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import anndata as ad
import numpy as np
import pandas as pd
import torch

from sea_ad_jepa.graph_data import (
    GraphExpressionDataset,
    load_consensus_edge_index,
    node_annotation_tensor,
)
from sea_ad_jepa.graph_jepa import GraphGeneJEPA
from sea_ad_jepa.gene_sets import MICROGLIA_GENE_MODULES
from sea_ad_jepa.jepa import jepa_loss


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
        raise RuntimeError("TensorBoard logging requested, but tensorboard is not installed.") from exc
    return SummaryWriter(log_dir)


def require_pyg():
    try:
        from torch_geometric.loader import DataLoader
    except ImportError as exc:
        raise RuntimeError(
            "Graph-JEPA training requires torch-geometric. Install it in sea-ad-jepa before running this script."
        ) from exc
    return DataLoader


def linear_schedule(epoch: int, total_epochs: int, start: float, end: float, warmup_epochs: int) -> float:
    if warmup_epochs <= 1:
        return end
    step = min(max(epoch - 1, 0), warmup_epochs - 1)
    frac = step / float(warmup_epochs - 1)
    return start + frac * (end - start)


def module_indices(gene_names: list[str]) -> list[np.ndarray]:
    gene_to_idx = {gene.upper(): idx for idx, gene in enumerate(gene_names)}
    modules = []
    for genes in MICROGLIA_GENE_MODULES.values():
        idx = [gene_to_idx[g.upper()] for g in genes if g.upper() in gene_to_idx]
        if idx:
            modules.append(np.asarray(sorted(set(idx)), dtype=np.int64))
    return modules


def read_gene_list(path: Path) -> list[str]:
    if path.suffix.lower() == ".csv":
        frame = pd.read_csv(path)
        if "gene" in frame.columns:
            return frame["gene"].astype(str).tolist()
        return frame.iloc[:, 0].astype(str).tolist()
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip() and not line.startswith("#")]


def load_external_gene_masks(paths: list[str], gene_names: list[str]) -> list[np.ndarray]:
    gene_to_idx = {gene.upper(): idx for idx, gene in enumerate(gene_names)}
    masks = []
    for item in paths:
        path = Path(item)
        if not path.exists():
            raise FileNotFoundError(path)
        genes = read_gene_list(path)
        mask = np.zeros(len(gene_names), dtype=bool)
        for gene in genes:
            idx = gene_to_idx.get(str(gene).upper())
            if idx is not None:
                mask[idx] = True
        if mask.any():
            masks.append(mask)
    return masks


def latent_geometry(z: torch.Tensor) -> dict[str, float]:
    if z.shape[0] < 2:
        return {"effective_dims": 0.0, "top_sv_ratio": 1.0, "mean_dim_std": 0.0}
    centered = z - z.mean(dim=0, keepdim=True)
    singular_values = torch.linalg.svdvals(centered)
    total = singular_values.sum() + 1e-8
    probs = singular_values / total
    entropy = -torch.sum(probs * torch.log(probs + 1e-8))
    return {
        "effective_dims": float(torch.exp(entropy).item()),
        "top_sv_ratio": float((singular_values[0] / total).item()),
        "mean_dim_std": float(z.std(dim=0, unbiased=False).mean().item()),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Stage A Graph-JEPA pretraining on healthy/normal microglia anchors.")
    parser.add_argument(
        "--h5ad",
        default="data/processed/v2_pretraining/cellxgene_normal_microglia_nucleus_relaxed_assay_jepa_aligned.h5ad",
    )
    parser.add_argument("--edge-csv", default="results/tables/v2_graph_consensus_edge_index.csv")
    parser.add_argument("--annotation-csv", default="results/tables/jepa_v2_translational_actionability_matrix.csv")
    parser.add_argument("--out-dir", default="results/models/graph_jepa_stage_a_cellxgene_10k")
    parser.add_argument("--log-dir", default="runs/graph_jepa_stage_a_cellxgene_10k")
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--checkpoint-every", type=int, default=5)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--hidden-dim", type=int, default=128)
    parser.add_argument("--latent-dim", type=int, default=128)
    parser.add_argument("--gene-embed-dim", type=int, default=32)
    parser.add_argument("--n-layers", type=int, default=2)
    parser.add_argument("--conv", choices=["sage", "gcn"], default="sage")
    parser.add_argument("--dropout", type=float, default=0.1)
    parser.add_argument("--ema-decay", type=float, default=0.9995)
    parser.add_argument("--ema-start-decay", type=float, default=0.992)
    parser.add_argument("--ema-warmup-epochs", type=int, default=10)
    parser.add_argument("--mask-fraction", type=float, default=0.5)
    parser.add_argument("--mask-start-fraction", type=float, default=0.2)
    parser.add_argument("--mask-warmup-epochs", type=int, default=10)
    parser.add_argument(
        "--random-gene-dropout",
        type=float,
        default=0.0,
        help="Additional context-only expression scalar dropout. Gene identity embeddings are preserved.",
    )
    parser.add_argument(
        "--module-dropout-prob",
        type=float,
        default=0.0,
        help="Per-sample probability of zeroing one curated microglia module's expression scalars in the context graph.",
    )
    parser.add_argument(
        "--external-mask-files",
        nargs="*",
        default=[],
        help="Optional files listing genes missing from external cohorts. One mask may be sampled per context graph.",
    )
    parser.add_argument(
        "--external-mask-prob",
        type=float,
        default=0.0,
        help="Per-sample probability of applying one known external missing-gene mask to expression scalars.",
    )
    parser.add_argument(
        "--edge-dropout",
        type=float,
        default=0.0,
        help="Context-only DropEdge probability during training. The master graph file is never modified.",
    )
    parser.add_argument("--variance-weight", type=float, default=0.05)
    parser.add_argument("--variance-gamma", type=float, default=1.0)
    parser.add_argument("--covariance-weight", type=float, default=0.01)
    parser.add_argument(
        "--collapse-alignment-threshold",
        type=float,
        default=1e-4,
        help="Stop if alignment falls below this while variance penalty remains high.",
    )
    parser.add_argument(
        "--collapse-variance-threshold",
        type=float,
        default=0.90,
        help="Stop if variance penalty stays above this after warmup while alignment is near zero.",
    )
    parser.add_argument("--collapse-warmup-epochs", type=int, default=5)
    parser.add_argument("--lr", type=float, default=2e-4)
    parser.add_argument("--weight-decay", type=float, default=1e-4)
    parser.add_argument("--gradient-clip-val", type=float, default=1.0)
    parser.add_argument(
        "--use-node-annotations",
        action="store_true",
        help="Append translational node annotations to expression. Keep off for the clean Stage A baseline.",
    )
    parser.add_argument("--max-cells", type=int, default=0, help="Optional cell cap for smoke tests.")
    parser.add_argument("--num-workers", type=int, default=0)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--history-csv", default="", help="Optional CSV path for epoch training metrics.")
    parser.add_argument("--log-file", default="", help="Optional plain-text log file mirroring epoch metrics.")
    args = parser.parse_args()

    DataLoader = require_pyg()
    torch.manual_seed(args.seed)
    np.random.seed(args.seed)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    adata = ad.read_h5ad(args.h5ad)
    if args.max_cells and adata.n_obs > args.max_cells:
        rng = np.random.default_rng(args.seed)
        idx = np.sort(rng.choice(adata.n_obs, size=args.max_cells, replace=False))
        adata = adata[idx].copy()
    gene_names = adata.var_names.astype(str).tolist()

    edge_index = load_consensus_edge_index(args.edge_csv)
    node_annotations = None
    if args.use_node_annotations:
        node_annotations = node_annotation_tensor(args.annotation_csv, gene_names)
    module_gene_indices = module_indices(gene_names) if args.module_dropout_prob > 0 else []
    external_gene_masks = load_external_gene_masks(args.external_mask_files, gene_names) if args.external_mask_files else []

    dataset = GraphExpressionDataset(
        adata.X,
        edge_index=edge_index,
        node_annotations=node_annotations,
        mask_fraction=args.mask_fraction,
        random_gene_dropout=args.random_gene_dropout,
        module_dropout_prob=args.module_dropout_prob,
        module_gene_indices=module_gene_indices,
        external_gene_masks=external_gene_masks,
        external_mask_prob=args.external_mask_prob,
        edge_dropout=args.edge_dropout,
        seed=args.seed,
        return_pyg_data=True,
    )
    loader = DataLoader(dataset, batch_size=args.batch_size, shuffle=True, num_workers=args.num_workers)

    device = choose_device(args.device)
    node_feature_dim = 1 + (int(node_annotations.shape[1]) if node_annotations is not None else 0)
    model = GraphGeneJEPA(
        n_genes=adata.n_vars,
        node_feature_dim=node_feature_dim,
        gene_embed_dim=args.gene_embed_dim,
        hidden_dim=args.hidden_dim,
        latent_dim=args.latent_dim,
        n_layers=args.n_layers,
        dropout=args.dropout,
        conv=args.conv,
        ema_decay=args.ema_decay,
    ).to(device)

    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    writer = create_summary_writer(args.log_dir)
    if writer is not None:
        writer.add_text("config/h5ad", args.h5ad)
        writer.add_text("config/edge_csv", args.edge_csv)
        writer.add_text("config/out_dir", str(out_dir))
        writer.add_scalar("config/n_cells", adata.n_obs, 0)
        writer.add_scalar("config/n_genes", adata.n_vars, 0)
        writer.add_scalar("config/batch_size", args.batch_size, 0)
        writer.add_scalar("config/use_node_annotations", float(args.use_node_annotations), 0)
        writer.add_scalar("config/node_feature_dim", node_feature_dim, 0)
        writer.add_scalar("config/ema_start_decay", args.ema_start_decay, 0)
        writer.add_scalar("config/ema_end_decay", args.ema_decay, 0)
        writer.add_scalar("config/mask_start_fraction", args.mask_start_fraction, 0)
        writer.add_scalar("config/mask_end_fraction", args.mask_fraction, 0)
        writer.add_scalar("config/covariance_weight", args.covariance_weight, 0)
        writer.add_scalar("config/gradient_clip_val", args.gradient_clip_val, 0)
        writer.add_scalar("config/random_gene_dropout", args.random_gene_dropout, 0)
        writer.add_scalar("config/module_dropout_prob", args.module_dropout_prob, 0)
        writer.add_scalar("config/external_mask_prob", args.external_mask_prob, 0)
        writer.add_scalar("config/edge_dropout", args.edge_dropout, 0)
        writer.add_scalar("config/n_module_masks", len(module_gene_indices), 0)
        writer.add_scalar("config/n_external_masks", len(external_gene_masks), 0)

    history = []
    log_handle = None
    if args.log_file:
        log_path = Path(args.log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_handle = log_path.open("w", encoding="utf-8")
        log_handle.write("Graph-JEPA Stage A training log\n")
        log_handle.write(f"args={vars(args)}\n")
        log_handle.write(f"n_module_masks={len(module_gene_indices)} n_external_masks={len(external_gene_masks)}\n")

    def save_checkpoint(path: Path) -> None:
        torch.save(
            {
                "model_state": model.state_dict(),
                "n_genes": adata.n_vars,
                "gene_names": gene_names,
                "args": vars(args),
                "history": history,
            },
            path,
        )

    for epoch in range(1, args.epochs + 1):
        model.train()
        current_mask_fraction = linear_schedule(
            epoch,
            args.epochs,
            args.mask_start_fraction,
            args.mask_fraction,
            args.mask_warmup_epochs,
        )
        current_ema_decay = linear_schedule(
            epoch,
            args.epochs,
            args.ema_start_decay,
            args.ema_decay,
            args.ema_warmup_epochs,
        )
        dataset.mask_fraction = current_mask_fraction
        model.ema_decay = current_ema_decay
        dataset.reset_augmentation_counts()
        losses = []
        alignment_losses = []
        variance_losses = []
        covariance_losses = []
        grad_norms = []
        epoch_pred_z = []
        for context_data, target_data in loader:
            context_data = context_data.to(device)
            target_data = target_data.to(device)
            pred_z, target_z = model(context_data, target_data)
            epoch_pred_z.append(pred_z.detach().cpu())
            loss, loss_parts = jepa_loss(
                pred_z,
                target_z,
                variance_weight=args.variance_weight,
                variance_gamma=args.variance_gamma,
                covariance_weight=args.covariance_weight,
            )
            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            if args.gradient_clip_val > 0:
                grad_norm = torch.nn.utils.clip_grad_norm_(model.parameters(), args.gradient_clip_val)
                grad_norms.append(float(grad_norm.detach().cpu()))
            optimizer.step()
            model.update_target_network()
            losses.append(float(loss.detach().cpu()))
            alignment_losses.append(float(loss_parts["alignment"].cpu()))
            variance_losses.append(float(loss_parts["variance"].cpu()))
            covariance_losses.append(float(loss_parts["covariance"].cpu()))

        mean_loss = float(np.mean(losses))
        mean_alignment = float(np.mean(alignment_losses))
        mean_variance = float(np.mean(variance_losses))
        mean_covariance = float(np.mean(covariance_losses))
        mean_grad_norm = float(np.mean(grad_norms)) if grad_norms else 0.0
        geometry = latent_geometry(torch.cat(epoch_pred_z, dim=0))
        history.append(
            {
                "epoch": epoch,
                "loss": mean_loss,
                "alignment_loss": mean_alignment,
                "variance_loss": mean_variance,
                "covariance_loss": mean_covariance,
                "mask_fraction": current_mask_fraction,
                "ema_decay": current_ema_decay,
                "grad_norm": mean_grad_norm,
                **geometry,
                **dataset.augmentation_counts,
            }
        )
        if writer is not None:
            writer.add_scalar("train/loss_epoch", mean_loss, epoch)
            writer.add_scalar("train/alignment_loss_epoch", mean_alignment, epoch)
            writer.add_scalar("train/variance_loss_epoch", mean_variance, epoch)
            writer.add_scalar("train/covariance_loss_epoch", mean_covariance, epoch)
            writer.add_scalar("train/lr", optimizer.param_groups[0]["lr"], epoch)
            writer.add_scalar("train/mask_fraction", current_mask_fraction, epoch)
            writer.add_scalar("train/ema_decay", current_ema_decay, epoch)
            writer.add_scalar("train/grad_norm", mean_grad_norm, epoch)
            writer.add_scalar("geometry/effective_dims", geometry["effective_dims"], epoch)
            writer.add_scalar("geometry/top_sv_ratio", geometry["top_sv_ratio"], epoch)
            writer.add_scalar("geometry/mean_dim_std", geometry["mean_dim_std"], epoch)
            for key, value in dataset.augmentation_counts.items():
                writer.add_scalar(f"augment/{key}", value, epoch)
        message = (
            f"epoch={epoch:03d} loss={mean_loss:.6f} "
            f"alignment={mean_alignment:.6f} variance={mean_variance:.6f} "
            f"covariance={mean_covariance:.6f} mask={current_mask_fraction:.3f} "
            f"ema={current_ema_decay:.5f} grad_norm={mean_grad_norm:.3f} "
            f"eff_dims={geometry['effective_dims']:.2f} top_sv={geometry['top_sv_ratio']:.3f} "
            f"mean_std={geometry['mean_dim_std']:.4f}"
        )
        print(message)
        if log_handle is not None:
            log_handle.write(message + "\n")
            log_handle.flush()
        if (
            epoch >= args.collapse_warmup_epochs
            and mean_alignment < args.collapse_alignment_threshold
            and mean_variance > args.collapse_variance_threshold
        ):
            print(
                "\n[FATAL] Possible representation collapse: "
                f"alignment={mean_alignment:.6f}, variance_penalty={mean_variance:.6f} "
                f"at epoch {epoch}. Halting."
            )
            break
        if args.checkpoint_every and epoch % args.checkpoint_every == 0:
            checkpoint_path = out_dir / f"graph_jepa_epoch_{epoch:03d}.pt"
            save_checkpoint(checkpoint_path)
            print(f"Wrote interim checkpoint: {checkpoint_path}")

    save_checkpoint(out_dir / "graph_jepa.pt")
    if args.history_csv:
        history_path = Path(args.history_csv)
        history_path.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(history).to_csv(history_path, index=False)
        print(f"Wrote history CSV to {history_path}")
    if log_handle is not None:
        log_handle.write(f"Wrote {out_dir / 'graph_jepa.pt'}\n")
        log_handle.close()
    if writer is not None:
        writer.flush()
        writer.close()
        print(f"Wrote TensorBoard logs to {args.log_dir}")
    print(f"Wrote {out_dir / 'graph_jepa.pt'}")


if __name__ == "__main__":
    main()
