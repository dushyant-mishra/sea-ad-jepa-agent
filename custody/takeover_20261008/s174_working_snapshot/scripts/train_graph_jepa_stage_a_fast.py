from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import anndata as ad
import numpy as np
import pandas as pd
import torch
from scipy import sparse
from torch.utils.data import DataLoader, TensorDataset

from sea_ad_jepa.graph_data import load_consensus_edge_index, node_annotation_tensor
from sea_ad_jepa.graph_jepa import FastGraphGeneJEPA
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


def linear_schedule(epoch: int, start: float, end: float, warmup_epochs: int) -> float:
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
        mask = np.zeros(len(gene_names), dtype=bool)
        for gene in read_gene_list(path):
            idx = gene_to_idx.get(str(gene).upper())
            if idx is not None:
                mask[idx] = True
        if mask.any():
            masks.append(mask)
    return masks


def load_expression_matrix(path: str, max_cells: int, seed: int) -> tuple[torch.Tensor, list[str]]:
    adata = ad.read_h5ad(path)
    if max_cells and adata.n_obs > max_cells:
        rng = np.random.default_rng(seed)
        idx = np.sort(rng.choice(adata.n_obs, size=max_cells, replace=False))
        adata = adata[idx].copy()
    x = adata.X
    if sparse.issparse(x):
        x = x.toarray()
    x = np.asarray(x, dtype=np.float32)
    genes = adata.var_names.astype(str).tolist()
    return torch.from_numpy(x), genes


def normalized_adjacency(edge_index: torch.Tensor, n_genes: int, edge_dropout: float, device: torch.device) -> torch.Tensor:
    edge_index = edge_index.to(device)
    if edge_dropout > 0:
        keep = torch.rand(edge_index.shape[1], device=device) >= edge_dropout
        if not bool(keep.any()):
            keep[torch.randint(edge_index.shape[1], (1,), device=device)] = True
        edge_index = edge_index[:, keep]
    source = edge_index[0]
    target = edge_index[1]
    values = torch.ones(source.shape[0], device=device)
    degree = torch.zeros(n_genes, device=device).scatter_add_(0, target, values).clamp_min_(1.0)
    values = values / degree[target]
    return torch.sparse_coo_tensor(
        torch.stack([target, source], dim=0),
        values,
        size=(n_genes, n_genes),
        device=device,
    ).coalesce()


def apply_context_masks(
    target: torch.Tensor,
    mask_fraction: float,
    random_gene_dropout: float,
    module_dropout_prob: float,
    modules: list[np.ndarray],
    external_masks: list[np.ndarray],
    external_mask_prob: float,
    rng: np.random.Generator,
) -> tuple[torch.Tensor, dict[str, int]]:
    context = target.clone()
    batch_size, n_genes = context.shape
    counts = {
        "random_gene_dropout_genes": 0,
        "module_dropout_events": 0,
        "module_dropout_genes": 0,
        "external_mask_events": 0,
        "external_mask_genes": 0,
    }
    if mask_fraction > 0:
        context[torch.rand_like(context) < mask_fraction] = 0.0
    if random_gene_dropout > 0:
        drop = torch.rand_like(context) < random_gene_dropout
        context[drop] = 0.0
        counts["random_gene_dropout_genes"] = int(drop.sum().item())
    if modules and module_dropout_prob > 0:
        for row in range(batch_size):
            if rng.random() < module_dropout_prob:
                idx = modules[int(rng.integers(0, len(modules)))]
                context[row, torch.as_tensor(idx, device=context.device)] = 0.0
                counts["module_dropout_events"] += 1
                counts["module_dropout_genes"] += int(len(idx))
    if external_masks and external_mask_prob > 0:
        for row in range(batch_size):
            if rng.random() < external_mask_prob:
                mask = external_masks[int(rng.integers(0, len(external_masks)))]
                context[row, torch.as_tensor(mask, device=context.device, dtype=torch.bool)] = 0.0
                counts["external_mask_events"] += 1
                counts["external_mask_genes"] += int(mask.sum())
    return context, counts


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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fast shared-topology Stage A Graph-JEPA pretraining.")
    parser.add_argument("--h5ad", default="data/processed/sea_ad_mtg_microglia_pvm_all_hvg3k_expanded_modules.h5ad")
    parser.add_argument("--edge-csv", default="results/tables/v2_graph_consensus_edge_index.csv")
    parser.add_argument("--annotation-csv", default="results/tables/jepa_v2_translational_actionability_matrix.csv")
    parser.add_argument("--out-dir", default="results/models/v2_2_topology_dropout_full_e50_fast")
    parser.add_argument("--log-dir", default="runs/v2_2_topology_dropout_full_e50_fast")
    parser.add_argument("--epochs", type=int, default=50)
    parser.add_argument("--checkpoint-every", type=int, default=5)
    parser.add_argument("--batch-size", type=int, default=128)
    parser.add_argument("--hidden-dim", type=int, default=128)
    parser.add_argument("--latent-dim", type=int, default=128)
    parser.add_argument("--gene-embed-dim", type=int, default=32)
    parser.add_argument("--n-layers", type=int, default=2)
    parser.add_argument("--dropout", type=float, default=0.1)
    parser.add_argument("--ema-decay", type=float, default=0.9995)
    parser.add_argument("--ema-start-decay", type=float, default=0.992)
    parser.add_argument("--ema-warmup-epochs", type=int, default=10)
    parser.add_argument("--mask-fraction", type=float, default=0.5)
    parser.add_argument("--mask-start-fraction", type=float, default=0.2)
    parser.add_argument("--mask-warmup-epochs", type=int, default=10)
    parser.add_argument("--random-gene-dropout", type=float, default=0.15)
    parser.add_argument("--module-dropout-prob", type=float, default=0.10)
    parser.add_argument("--external-mask-files", nargs="*", default=[])
    parser.add_argument("--external-mask-prob", type=float, default=0.25)
    parser.add_argument("--edge-dropout", type=float, default=0.10)
    parser.add_argument("--variance-weight", type=float, default=0.20)
    parser.add_argument("--variance-gamma", type=float, default=0.02)
    parser.add_argument("--covariance-weight", type=float, default=0.05)
    parser.add_argument("--lr", type=float, default=2e-4)
    parser.add_argument("--weight-decay", type=float, default=1e-4)
    parser.add_argument("--gradient-clip-val", type=float, default=1.0)
    parser.add_argument("--use-node-annotations", action="store_true")
    parser.add_argument("--max-cells", type=int, default=0)
    parser.add_argument("--num-workers", type=int, default=0)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--history-csv", default="")
    parser.add_argument("--log-file", default="")
    return parser


def run(args: argparse.Namespace) -> None:
    torch.manual_seed(args.seed)
    np.random.seed(args.seed)
    rng = np.random.default_rng(args.seed)
    device = choose_device(args.device)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    matrix, gene_names = load_expression_matrix(args.h5ad, args.max_cells, args.seed)
    edge_index = load_consensus_edge_index(args.edge_csv)
    node_annotations = None
    if args.use_node_annotations:
        node_annotations = node_annotation_tensor(args.annotation_csv, gene_names)
    node_feature_dim = 1 + (int(node_annotations.shape[1]) if node_annotations is not None else 0)
    if node_annotations is not None:
        node_annotations = node_annotations.to(device)
    modules = module_indices(gene_names) if args.module_dropout_prob > 0 else []
    external_masks = load_external_gene_masks(args.external_mask_files, gene_names) if args.external_mask_files else []

    loader = DataLoader(
        TensorDataset(matrix),
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=args.num_workers,
        pin_memory=device.type == "cuda",
    )
    model = FastGraphGeneJEPA(
        n_genes=matrix.shape[1],
        node_feature_dim=node_feature_dim,
        gene_embed_dim=args.gene_embed_dim,
        hidden_dim=args.hidden_dim,
        latent_dim=args.latent_dim,
        n_layers=args.n_layers,
        dropout=args.dropout,
        ema_decay=args.ema_decay,
    ).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    writer = create_summary_writer(args.log_dir)

    history = []
    log_handle = None
    if args.log_file:
        log_path = Path(args.log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_handle = log_path.open("w", encoding="utf-8")
        log_handle.write("Fast Graph-JEPA Stage A training log\n")
        log_handle.write(f"args={vars(args)}\n")
        log_handle.write(f"n_module_masks={len(modules)} n_external_masks={len(external_masks)}\n")

    def save_checkpoint(path: Path) -> None:
        torch.save(
            {
                "model_state": model.state_dict(),
                "n_genes": matrix.shape[1],
                "gene_names": gene_names,
                "args": vars(args),
                "history": history,
                "model_class": "FastGraphGeneJEPA",
            },
            path,
        )

    target_adj = normalized_adjacency(edge_index, matrix.shape[1], 0.0, device)
    for epoch in range(1, args.epochs + 1):
        start_time = time.perf_counter()
        model.train()
        current_mask_fraction = linear_schedule(epoch, args.mask_start_fraction, args.mask_fraction, args.mask_warmup_epochs)
        current_ema_decay = linear_schedule(epoch, args.ema_start_decay, args.ema_decay, args.ema_warmup_epochs)
        model.ema_decay = current_ema_decay
        losses = []
        alignment_losses = []
        variance_losses = []
        covariance_losses = []
        grad_norms = []
        epoch_pred_z = []
        augmentation_counts = {
            "random_gene_dropout_genes": 0,
            "module_dropout_events": 0,
            "module_dropout_genes": 0,
            "external_mask_events": 0,
            "external_mask_genes": 0,
            "edge_dropout_edges": 0,
        }
        for (target_batch,) in loader:
            target_batch = target_batch.to(device, non_blocking=True)
            context_batch, counts = apply_context_masks(
                target_batch,
                current_mask_fraction,
                args.random_gene_dropout,
                args.module_dropout_prob,
                modules,
                external_masks,
                args.external_mask_prob,
                rng,
            )
            for key, value in counts.items():
                augmentation_counts[key] += value
            context_adj = normalized_adjacency(edge_index, matrix.shape[1], args.edge_dropout, device)
            augmentation_counts["edge_dropout_edges"] += int(edge_index.shape[1] - context_adj._nnz())
            pred_z, target_z = model(
                context_batch,
                target_batch,
                context_adj=context_adj,
                target_adj=target_adj,
                node_annotations=node_annotations,
            )
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

        geometry = latent_geometry(torch.cat(epoch_pred_z, dim=0))
        epoch_seconds = time.perf_counter() - start_time
        row = {
            "epoch": epoch,
            "loss": float(np.mean(losses)),
            "alignment_loss": float(np.mean(alignment_losses)),
            "variance_loss": float(np.mean(variance_losses)),
            "covariance_loss": float(np.mean(covariance_losses)),
            "mask_fraction": current_mask_fraction,
            "ema_decay": current_ema_decay,
            "grad_norm": float(np.mean(grad_norms)) if grad_norms else 0.0,
            "epoch_seconds": epoch_seconds,
            "cells_per_second": float(matrix.shape[0] / max(epoch_seconds, 1e-8)),
            **geometry,
            **augmentation_counts,
        }
        history.append(row)
        if writer is not None:
            for key, value in row.items():
                if isinstance(value, (int, float)):
                    writer.add_scalar(f"train/{key}" if key.endswith("loss") or key in {"loss", "grad_norm", "cells_per_second"} else f"metrics/{key}", value, epoch)
        message = (
            f"epoch={epoch:03d} loss={row['loss']:.6f} alignment={row['alignment_loss']:.6f} "
            f"variance={row['variance_loss']:.6f} covariance={row['covariance_loss']:.6f} "
            f"mask={current_mask_fraction:.3f} ema={current_ema_decay:.5f} "
            f"eff_dims={geometry['effective_dims']:.2f} top_sv={geometry['top_sv_ratio']:.3f} "
            f"mean_std={geometry['mean_dim_std']:.4f} sec={epoch_seconds:.1f} "
            f"cells_s={row['cells_per_second']:.1f}"
        )
        print(message, flush=True)
        if log_handle is not None:
            log_handle.write(message + "\n")
            log_handle.flush()
        if args.checkpoint_every and epoch % args.checkpoint_every == 0:
            checkpoint_path = out_dir / f"fast_graph_jepa_epoch_{epoch:03d}.pt"
            save_checkpoint(checkpoint_path)
            print(f"Wrote interim checkpoint: {checkpoint_path}", flush=True)

    save_checkpoint(out_dir / "fast_graph_jepa.pt")
    if args.history_csv:
        history_path = Path(args.history_csv)
        history_path.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(history).to_csv(history_path, index=False)
        print(f"Wrote history CSV to {history_path}")
    if log_handle is not None:
        log_handle.write(f"Wrote {out_dir / 'fast_graph_jepa.pt'}\n")
        log_handle.close()
    if writer is not None:
        writer.flush()
        writer.close()
        print(f"Wrote TensorBoard logs to {args.log_dir}")
    print(f"Wrote {out_dir / 'fast_graph_jepa.pt'}")


def main() -> None:
    run(build_parser().parse_args())


if __name__ == "__main__":
    main()
