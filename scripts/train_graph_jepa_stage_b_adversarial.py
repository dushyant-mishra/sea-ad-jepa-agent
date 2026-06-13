from __future__ import annotations

import itertools
import math
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import anndata as ad
import hydra
import numpy as np
import pandas as pd
import torch
from omegaconf import DictConfig, OmegaConf
from scipy import sparse
from torch import nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, TensorDataset

from sea_ad_jepa.graph_data import load_consensus_edge_index
from sea_ad_jepa.graph_jepa import FastGraphGeneJEPA
from sea_ad_jepa.jepa import jepa_loss
from scripts.train_graph_jepa_stage_a_fast import (
    apply_context_masks,
    choose_device,
    create_summary_writer,
    latent_geometry,
    linear_schedule,
    load_external_gene_masks,
    module_indices,
    normalized_adjacency,
)


DOMAIN_NAMES = ("sea_ad", "rexach", "olah")


class GradientReversal(torch.autograd.Function):
    @staticmethod
    def forward(ctx, x: torch.Tensor, lambda_grl: float) -> torch.Tensor:
        ctx.lambda_grl = float(lambda_grl)
        return x.view_as(x)

    @staticmethod
    def backward(ctx, grad_output: torch.Tensor) -> tuple[torch.Tensor, None]:
        return -ctx.lambda_grl * grad_output, None


class DomainClassifier(nn.Module):
    def __init__(self, latent_dim: int, hidden_dim: int = 128, n_domains: int = 3, dropout: float = 0.1):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(latent_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, n_domains),
        )

    def forward(self, z: torch.Tensor) -> torch.Tensor:
        return self.net(z)


def load_dense_matrix(path: str) -> tuple[torch.Tensor, list[str]]:
    adata = ad.read_h5ad(path)
    x = adata.X
    if sparse.issparse(x):
        x = x.toarray()
    x = np.asarray(x, dtype=np.float32)
    return torch.from_numpy(x), adata.var_names.astype(str).tolist()


def cycle_loader(loader: DataLoader):
    while True:
        yield from loader


def grl_lambda(progress: float, max_lambda: float) -> float:
    return float(max_lambda * (2.0 / (1.0 + math.exp(-10.0 * progress)) - 1.0))


def build_model_from_checkpoint(checkpoint_path: str, device: torch.device) -> tuple[FastGraphGeneJEPA, dict]:
    checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
    args = checkpoint.get("args", {})
    model = FastGraphGeneJEPA(
        n_genes=int(checkpoint["n_genes"]),
        node_feature_dim=1,
        gene_embed_dim=int(args.get("gene_embed_dim", 32)),
        hidden_dim=int(args.get("hidden_dim", 128)),
        latent_dim=int(args.get("latent_dim", 128)),
        n_layers=int(args.get("n_layers", 2)),
        dropout=float(args.get("dropout", 0.1)),
        ema_decay=float(args.get("ema_decay", 0.9995)),
    )
    model.load_state_dict(checkpoint["model_state"])
    model.to(device)
    return model, args


def apply_freeze_mode(model: FastGraphGeneJEPA, freeze_mode: str) -> None:
    for param in model.parameters():
        param.requires_grad = False

    freeze_mode = freeze_mode.lower()
    if freeze_mode == "frozen":
        return
    if freeze_mode == "partial_encoder":
        for param in model.context_encoder.out.parameters():
            param.requires_grad = True
        for param in model.predictor.parameters():
            param.requires_grad = True
    elif freeze_mode == "full":
        for param in model.context_encoder.parameters():
            param.requires_grad = True
        for param in model.predictor.parameters():
            param.requires_grad = True
    else:
        raise ValueError("freeze_mode must be one of: frozen, partial_encoder, full")

    for param in model.target_encoder.parameters():
        param.requires_grad = False


def trainable_parameters(module: nn.Module) -> list[nn.Parameter]:
    return [param for param in module.parameters() if param.requires_grad]


def pairwise_centroid_distances(z: torch.Tensor, labels: torch.Tensor) -> dict[str, float]:
    centroids = []
    for domain_id in range(len(DOMAIN_NAMES)):
        centroids.append(z[labels == domain_id].mean(dim=0))
    output = {}
    for i, j in itertools.combinations(range(len(DOMAIN_NAMES)), 2):
        key = f"centroid_l2_{DOMAIN_NAMES[i]}_{DOMAIN_NAMES[j]}"
        output[key] = float(torch.norm(centroids[i] - centroids[j], p=2).item())
    return output


@hydra.main(version_base=None, config_path="../configs/train", config_name="stage_b_adversarial")
def main(cfg: DictConfig) -> None:
    print("Resolved Stage B adversarial config:")
    print(OmegaConf.to_yaml(cfg, resolve=True))

    torch.manual_seed(int(cfg.seed))
    np.random.seed(int(cfg.seed))
    rng = np.random.default_rng(int(cfg.seed))
    device = choose_device(str(cfg.device))

    model, stage_a_args = build_model_from_checkpoint(str(cfg.stage_a_checkpoint), device)
    apply_freeze_mode(model, str(cfg.freeze_mode))
    latent_dim = int(stage_a_args.get("latent_dim", 128))
    domain_classifier = DomainClassifier(latent_dim, hidden_dim=int(cfg.domain_hidden_dim)).to(device)

    optimizer_groups = [{"params": domain_classifier.parameters(), "lr": float(cfg.domain_lr)}]
    model_params = trainable_parameters(model)
    if model_params:
        optimizer_groups.append({"params": model_params, "lr": float(cfg.lr)})
    optimizer = torch.optim.AdamW(optimizer_groups, weight_decay=float(cfg.weight_decay))

    matrices = []
    genes_by_domain = []
    for path in (cfg.sea_ad_h5ad, cfg.rexach_h5ad, cfg.olah_h5ad):
        matrix, genes = load_dense_matrix(str(path))
        matrices.append(matrix)
        genes_by_domain.append(genes)
    if any(genes != genes_by_domain[0] for genes in genes_by_domain[1:]):
        raise ValueError("All Stage B H5AD inputs must already be aligned to the exact same gene order")
    gene_names = genes_by_domain[0]

    loaders = [
        DataLoader(
            TensorDataset(matrix),
            batch_size=int(cfg.per_domain_batch_size),
            shuffle=True,
            drop_last=True,
            pin_memory=device.type == "cuda",
        )
        for matrix in matrices
    ]
    steps_per_epoch = min(len(loader) for loader in loaders)
    if int(cfg.max_steps_per_epoch) > 0:
        steps_per_epoch = min(steps_per_epoch, int(cfg.max_steps_per_epoch))

    edge_index = load_consensus_edge_index(str(cfg.edge_csv))
    target_adj = normalized_adjacency(edge_index, len(gene_names), 0.0, device)
    modules = module_indices(gene_names) if float(cfg.module_dropout_prob) > 0 else []
    external_masks = load_external_gene_masks(list(cfg.external_mask_files), gene_names) if cfg.external_mask_files else []

    out_dir = Path(str(cfg.out_dir))
    out_dir.mkdir(parents=True, exist_ok=True)
    writer = create_summary_writer(str(cfg.log_dir))
    history = []
    log_handle = None
    if cfg.log_file:
        log_path = Path(str(cfg.log_file))
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_handle = log_path.open("w", encoding="utf-8")
        log_handle.write("Graph-JEPA Stage B domain-adversarial training log\n")
        log_handle.write(OmegaConf.to_yaml(cfg, resolve=True))
        log_handle.write("\n")

    def save_checkpoint(path: Path) -> None:
        torch.save(
            {
                "model_state": model.state_dict(),
                "domain_classifier_state": domain_classifier.state_dict(),
                "n_genes": len(gene_names),
                "gene_names": gene_names,
                "cfg": OmegaConf.to_container(cfg, resolve=True),
                "history": history,
                "model_class": "FastGraphGeneJEPA",
            },
            path,
        )

    for epoch in range(1, int(cfg.epochs) + 1):
        start_time = time.perf_counter()
        model.train()
        domain_classifier.train()
        loaders_iter = [cycle_loader(loader) for loader in loaders]
        current_mask_fraction = linear_schedule(
            epoch,
            float(cfg.mask_start_fraction),
            float(cfg.mask_fraction),
            int(cfg.mask_warmup_epochs),
        )
        losses = []
        jepa_losses = []
        domain_losses = []
        lambdas = []
        domain_correct = 0
        domain_total = 0
        epoch_z = []
        epoch_labels = []
        augmentation_counts = {
            "random_gene_dropout_genes": 0,
            "module_dropout_events": 0,
            "module_dropout_genes": 0,
            "external_mask_events": 0,
            "external_mask_genes": 0,
            "edge_dropout_edges": 0,
        }
        for step in range(steps_per_epoch):
            progress = ((epoch - 1) * steps_per_epoch + step) / max(int(cfg.epochs) * steps_per_epoch - 1, 1)
            lambda_grl = grl_lambda(progress, float(cfg.lambda_grl_max))
            lambdas.append(lambda_grl)
            target_batches = [next(loader_iter)[0].to(device, non_blocking=True) for loader_iter in loaders_iter]
            target_batch = torch.cat(target_batches, dim=0)
            labels = torch.cat(
                [
                    torch.full((batch.shape[0],), domain_id, dtype=torch.long, device=device)
                    for domain_id, batch in enumerate(target_batches)
                ],
                dim=0,
            )
            context_batch, counts = apply_context_masks(
                target_batch,
                current_mask_fraction,
                float(cfg.random_gene_dropout),
                float(cfg.module_dropout_prob),
                modules,
                external_masks,
                float(cfg.external_mask_prob),
                rng,
            )
            for key, value in counts.items():
                augmentation_counts[key] += value
            context_adj = normalized_adjacency(edge_index, len(gene_names), float(cfg.edge_dropout), device)
            augmentation_counts["edge_dropout_edges"] += int(edge_index.shape[1] - context_adj._nnz())

            pred_z, target_z = model(
                context_batch,
                target_batch,
                context_adj=context_adj,
                target_adj=target_adj,
                node_annotations=None,
            )
            loss_jepa, _ = jepa_loss(
                pred_z,
                target_z,
                variance_weight=float(cfg.variance_weight),
                variance_gamma=float(cfg.variance_gamma),
                covariance_weight=float(cfg.covariance_weight),
            )
            with torch.set_grad_enabled(str(cfg.freeze_mode).lower() != "frozen"):
                domain_z = model.context_encoder(target_batch, target_adj, node_annotations=None)
            logits = domain_classifier(GradientReversal.apply(domain_z, lambda_grl))
            loss_domain = F.cross_entropy(logits, labels)
            if str(cfg.freeze_mode).lower() == "frozen":
                total_loss = loss_domain
            else:
                total_loss = loss_jepa + float(cfg.domain_loss_weight) * loss_domain

            optimizer.zero_grad(set_to_none=True)
            total_loss.backward()
            if float(cfg.gradient_clip_val) > 0:
                torch.nn.utils.clip_grad_norm_(trainable_parameters(model) + list(domain_classifier.parameters()), float(cfg.gradient_clip_val))
            optimizer.step()
            if str(cfg.freeze_mode).lower() != "frozen":
                model.update_target_network()

            losses.append(float(total_loss.detach().cpu()))
            jepa_losses.append(float(loss_jepa.detach().cpu()))
            domain_losses.append(float(loss_domain.detach().cpu()))
            domain_correct += int((logits.argmax(dim=1) == labels).sum().detach().cpu())
            domain_total += int(labels.numel())
            epoch_z.append(domain_z.detach().cpu())
            epoch_labels.append(labels.detach().cpu())

        all_z = torch.cat(epoch_z, dim=0)
        all_labels = torch.cat(epoch_labels, dim=0)
        geometry = latent_geometry(all_z)
        centroid_metrics = pairwise_centroid_distances(all_z, all_labels)
        epoch_seconds = time.perf_counter() - start_time
        row = {
            "epoch": epoch,
            "loss": float(np.mean(losses)),
            "jepa_loss": float(np.mean(jepa_losses)),
            "domain_loss": float(np.mean(domain_losses)),
            "domain_accuracy": float(domain_correct / max(domain_total, 1)),
            "lambda_grl": float(np.mean(lambdas)) if lambdas else 0.0,
            "mask_fraction": current_mask_fraction,
            "epoch_seconds": epoch_seconds,
            "cells_per_second": float(domain_total / max(epoch_seconds, 1e-8)),
            **geometry,
            **centroid_metrics,
            **augmentation_counts,
        }
        history.append(row)
        if writer is not None:
            for key, value in row.items():
                if isinstance(value, (int, float)):
                    writer.add_scalar(f"stage_b/{key}", value, epoch)
        message = (
            f"epoch={epoch:03d} loss={row['loss']:.6f} jepa={row['jepa_loss']:.6f} "
            f"domain={row['domain_loss']:.6f} acc={row['domain_accuracy']:.3f} "
            f"lambda={row['lambda_grl']:.3f} eff_dims={row['effective_dims']:.2f} "
            f"top_sv={row['top_sv_ratio']:.3f} mean_std={row['mean_dim_std']:.4f} "
            f"sec={epoch_seconds:.1f}"
        )
        print(message, flush=True)
        if log_handle is not None:
            log_handle.write(message + "\n")
            log_handle.flush()
        if int(cfg.checkpoint_every) and epoch % int(cfg.checkpoint_every) == 0:
            checkpoint_path = out_dir / f"stage_b_adversarial_epoch_{epoch:03d}.pt"
            save_checkpoint(checkpoint_path)
            print(f"Wrote interim checkpoint: {checkpoint_path}", flush=True)

    save_checkpoint(out_dir / "stage_b_adversarial.pt")
    if cfg.history_csv:
        history_path = Path(str(cfg.history_csv))
        history_path.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(history).to_csv(history_path, index=False)
        print(f"Wrote history CSV to {history_path}")
    if log_handle is not None:
        log_handle.write(f"Wrote {out_dir / 'stage_b_adversarial.pt'}\n")
        log_handle.close()
    if writer is not None:
        writer.flush()
        writer.close()
        print(f"Wrote TensorBoard logs to {cfg.log_dir}")
    print(f"Wrote {out_dir / 'stage_b_adversarial.pt'}")


if __name__ == "__main__":
    main()
