from __future__ import annotations

import argparse
import itertools
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import anndata as ad
import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F
from scipy import sparse
from torch.utils.data import DataLoader, TensorDataset

from sea_ad_jepa.data import load_pathology_targets, normalize_donor_id
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
        dropout=0.1,
        ema_decay=0.9995,
    )
    model.load_state_dict(state)
    return model


def build_optimizer(model: FastGraphGeneJEPA, base_lr: float, head_lr: float, weight_decay: float) -> torch.optim.Optimizer:
    base_modules = [
        model.context_encoder.gene_embedding,
        model.context_encoder.input_proj,
        model.context_encoder.self_linears,
        model.context_encoder.neighbor_linears,
        model.context_encoder.norms,
    ]
    head_modules = [
        model.context_encoder.out,
        model.predictor,
    ]
    seen: set[int] = set()

    def collect(modules):
        params = []
        for module in modules:
            for param in module.parameters():
                if param.requires_grad and id(param) not in seen:
                    seen.add(id(param))
                    params.append(param)
        return params

    return torch.optim.AdamW(
        [
            {"params": collect(base_modules), "lr": base_lr, "name": "base_graph_reader"},
            {"params": collect(head_modules), "lr": head_lr, "name": "head_coordinate_map"},
        ],
        weight_decay=weight_decay,
    )


@torch.no_grad()
def encode_matrix(model: FastGraphGeneJEPA, matrix: torch.Tensor, adj: torch.Tensor, device: torch.device, batch_size: int) -> torch.Tensor:
    model.eval()
    chunks = []
    loader = DataLoader(TensorDataset(matrix), batch_size=batch_size, shuffle=False)
    for (batch,) in loader:
        chunks.append(model.context_encoder(batch.to(device), adj, node_annotations=None).cpu())
    return torch.cat(chunks, dim=0)


def rehearsal_loss(current_z: torch.Tensor, frozen_z: torch.Tensor, margin: float, temperature: float) -> tuple[torch.Tensor, torch.Tensor]:
    cosine = F.cosine_similarity(current_z, frozen_z.to(current_z.device), dim=-1)
    loss = (F.softplus(temperature * (margin - cosine)) / temperature).mean()
    return loss, cosine.mean()


def off_diagonal_covariance_loss(z: torch.Tensor) -> torch.Tensor:
    if z.shape[0] < 2:
        return z.new_tensor(0.0)
    centered = z - z.mean(dim=0, keepdim=True)
    covariance = (centered.T @ centered) / float(z.shape[0] - 1)
    covariance = covariance.clone()
    covariance.fill_diagonal_(0.0)
    return covariance.pow(2).mean()


def pathology_similarity_loss(z: torch.Tensor, y: torch.Tensor, temperature: float) -> torch.Tensor:
    if z.shape[0] < 2:
        return z.new_tensor(0.0)
    valid = torch.isfinite(y).all(dim=1)
    if int(valid.sum().item()) < 2:
        return z.new_tensor(0.0)
    z = F.normalize(z[valid], dim=-1)
    y = y[valid]
    y = (y - y.mean(dim=0, keepdim=True)) / y.std(dim=0, unbiased=False, keepdim=True).clamp_min(1e-6)
    target_distance = torch.cdist(y, y, p=1) / float(y.shape[1])
    weights = torch.exp(-target_distance / max(temperature, 1e-6))
    eye = torch.eye(weights.shape[0], dtype=torch.bool, device=weights.device)
    weights = weights.masked_fill(eye, 0.0)
    cosine = z @ z.T
    return (weights * (1.0 - cosine)).sum() / weights.sum().clamp_min(1e-8)


def pathology_matrix(obs: pd.DataFrame, donor_column: str, target_columns: list[str], targets_path: str, columns_path: str) -> torch.Tensor:
    targets, _ = load_pathology_targets(targets_path, columns_path)
    targets = targets.copy()
    targets["Donor ID"] = normalize_donor_id(targets["Donor ID"])
    donors = normalize_donor_id(obs[donor_column]).reset_index(drop=True)
    values = targets.set_index("Donor ID")[target_columns].reindex(donors).to_numpy(dtype=np.float32)
    return torch.as_tensor(values, dtype=torch.float32)


def main() -> None:
    parser = argparse.ArgumentParser(description="Fast Stage C Graph-JEPA disease fine-tuning with safety gates.")
    parser.add_argument("--checkpoint", default="results/models/v2_2_stage_b_adversarial/stage_b_adversarial.pt")
    parser.add_argument("--disease-h5ad", default="data/processed/sea_ad_mtg_microglia_pvm_all_hvg3k_expanded_modules.h5ad")
    parser.add_argument("--sea-anchor-h5ad", default="data/processed/v2_pretraining/sea_ad_low_pathology_microglia_pvm_relaxed_jepa_aligned.h5ad")
    parser.add_argument("--cellxgene-anchor-h5ad", default="data/processed/v2_pretraining/cellxgene_normal_microglia_nucleus_relaxed_assay_jepa_aligned.h5ad")
    parser.add_argument("--edge-csv", default="results/tables/v2_graph_consensus_edge_index.csv")
    parser.add_argument("--out-dir", default="results/models/v2_2_fast_stage_c_disease")
    parser.add_argument("--log-dir", default="runs/v2_2_fast_stage_c_disease")
    parser.add_argument("--history-out", default="results/tables/v2_2_fast_stage_c_disease_history.csv")
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--checkpoint-every", type=int, default=5)
    parser.add_argument("--disease-batch-size", type=int, default=256)
    parser.add_argument("--anchor-batch-size", type=int, default=128)
    parser.add_argument("--max-steps-per-epoch", type=int, default=0)
    parser.add_argument("--mask-start-fraction", type=float, default=0.2)
    parser.add_argument("--mask-fraction", type=float, default=0.5)
    parser.add_argument("--mask-warmup-epochs", type=int, default=5)
    parser.add_argument("--ema-start-decay", type=float, default=0.995)
    parser.add_argument("--ema-decay", type=float, default=0.9995)
    parser.add_argument("--ema-warmup-epochs", type=int, default=5)
    parser.add_argument("--random-gene-dropout", type=float, default=0.15)
    parser.add_argument("--module-dropout-prob", type=float, default=0.10)
    parser.add_argument("--external-mask-files", nargs="*", default=[
        "results/tables/external_gene_masks/gse174367_morabito_missing_genes.txt",
        "results/tables/external_gene_masks/gse138852_grubman_missing_genes.txt",
    ])
    parser.add_argument("--external-mask-prob", type=float, default=0.25)
    parser.add_argument("--edge-dropout", type=float, default=0.10)
    parser.add_argument("--sea-rehearsal-weight", type=float, default=0.0045)
    parser.add_argument("--cellxgene-rehearsal-weight", type=float, default=0.0045)
    parser.add_argument("--rehearsal-margin", type=float, default=0.85)
    parser.add_argument("--rehearsal-temperature", type=float, default=100.0)
    parser.add_argument("--variance-weight", type=float, default=1.0)
    parser.add_argument("--variance-gamma", type=float, default=1.0)
    parser.add_argument("--covariance-weight", type=float, default=0.0)
    parser.add_argument("--disease-covariance-weight", type=float, default=0.0005)
    parser.add_argument("--pathology-contrastive-weight", type=float, default=0.075)
    parser.add_argument("--pathology-contrastive-warmup-epochs", type=int, default=5)
    parser.add_argument("--pathology-contrastive-temperature", type=float, default=0.75)
    parser.add_argument("--pathology-contrastive-targets", nargs="+", default=[
        "percent AT8 positive area_Grey matter",
        "percent NeuN positive area_Grey matter",
    ])
    parser.add_argument("--pathology-targets-path", default="data/processed/metadata/sea_ad_mtg_donor_pathology_targets.csv")
    parser.add_argument("--pathology-target-columns-path", default="data/processed/metadata/pathology_target_columns.csv")
    parser.add_argument("--donor-column", default="Donor ID")
    parser.add_argument("--base-lr", type=float, default=1e-6)
    parser.add_argument("--lr", type=float, default=2e-5)
    parser.add_argument("--weight-decay", type=float, default=1e-4)
    parser.add_argument("--gradient-clip-val", type=float, default=1.0)
    parser.add_argument("--safety-gate-start-epoch", type=int, default=6)
    parser.add_argument("--min-embedding-effective-dims", type=float, default=50.0)
    parser.add_argument("--max-embedding-top-sv-ratio", type=float, default=0.2)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()

    torch.manual_seed(args.seed)
    np.random.seed(args.seed)
    rng = np.random.default_rng(args.seed)
    device = choose_device(args.device)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    checkpoint = torch.load(args.checkpoint, map_location="cpu", weights_only=False)
    model = infer_fast_model(checkpoint).to(device)
    optimizer = build_optimizer(model, args.base_lr, args.lr, args.weight_decay)
    print("optimizer groups: " + ", ".join(f"{g.get('name')} lr={g['lr']:.2e}" for g in optimizer.param_groups))

    disease_x, gene_names, disease_obs = dense_h5ad(args.disease_h5ad)
    sea_x, sea_genes, _ = dense_h5ad(args.sea_anchor_h5ad)
    cx_x, cx_genes, _ = dense_h5ad(args.cellxgene_anchor_h5ad)
    if gene_names != sea_genes or gene_names != cx_genes:
        raise ValueError("Disease and anchor H5ADs must have the same gene order")

    edge_index = load_consensus_edge_index(args.edge_csv)
    target_adj = normalized_adjacency(edge_index, len(gene_names), 0.0, device)
    modules = module_indices(gene_names) if args.module_dropout_prob > 0 else []
    external_masks = load_external_gene_masks(args.external_mask_files, gene_names) if args.external_mask_files else []
    writer = create_summary_writer(args.log_dir)

    print("encoding frozen Stage C rehearsal anchors")
    sea_frozen = encode_matrix(model, sea_x, target_adj, device, args.anchor_batch_size).to(device)
    cx_frozen = encode_matrix(model, cx_x, target_adj, device, args.anchor_batch_size).to(device)
    pathology = pathology_matrix(
        disease_obs,
        args.donor_column,
        args.pathology_contrastive_targets,
        args.pathology_targets_path,
        args.pathology_target_columns_path,
    ).to(device)

    disease_loader = DataLoader(TensorDataset(disease_x, torch.arange(disease_x.shape[0])), batch_size=args.disease_batch_size, shuffle=True)
    sea_loader = DataLoader(TensorDataset(sea_x, torch.arange(sea_x.shape[0])), batch_size=args.anchor_batch_size, shuffle=True, drop_last=True)
    cx_loader = DataLoader(TensorDataset(cx_x, torch.arange(cx_x.shape[0])), batch_size=args.anchor_batch_size, shuffle=True, drop_last=True)
    history = []

    def save_checkpoint(path: Path) -> None:
        torch.save(
            {
                "model_state": model.state_dict(),
                "n_genes": len(gene_names),
                "gene_names": gene_names,
                "args": vars(args),
                "history": history,
                "model_class": "FastGraphGeneJEPA",
            },
            path,
        )

    for epoch in range(1, args.epochs + 1):
        model.train()
        sea_iter = itertools.cycle(sea_loader)
        cx_iter = itertools.cycle(cx_loader)
        current_mask_fraction = linear_schedule(epoch, args.mask_start_fraction, args.mask_fraction, args.mask_warmup_epochs)
        current_ema = linear_schedule(epoch, args.ema_start_decay, args.ema_decay, args.ema_warmup_epochs)
        current_pathology_weight = linear_schedule(epoch, 0.0, args.pathology_contrastive_weight, args.pathology_contrastive_warmup_epochs)
        model.ema_decay = current_ema

        losses = []
        jepa_losses = []
        sea_losses = []
        cx_losses = []
        pathology_losses = []
        embedding_chunks = []
        pred_chunks = []
        sea_cosines = []
        cx_cosines = []
        for step, (target_batch_cpu, cell_ids_cpu) in enumerate(disease_loader, start=1):
            if args.max_steps_per_epoch and step > args.max_steps_per_epoch:
                break
            target_batch = target_batch_cpu.to(device, non_blocking=True)
            cell_ids = cell_ids_cpu.to(device, non_blocking=True)
            sea_batch_cpu, sea_ids_cpu = next(sea_iter)
            cx_batch_cpu, cx_ids_cpu = next(cx_iter)
            sea_batch = sea_batch_cpu.to(device, non_blocking=True)
            cx_batch = cx_batch_cpu.to(device, non_blocking=True)
            sea_ids = sea_ids_cpu.to(device, non_blocking=True)
            cx_ids = cx_ids_cpu.to(device, non_blocking=True)

            context_batch, _ = apply_context_masks(
                target_batch,
                current_mask_fraction,
                args.random_gene_dropout,
                args.module_dropout_prob,
                modules,
                external_masks,
                args.external_mask_prob,
                rng,
            )
            context_adj = normalized_adjacency(edge_index, len(gene_names), args.edge_dropout, device)
            pred_z, target_z = model(context_batch, target_batch, context_adj=context_adj, target_adj=target_adj)
            loss_jepa, _ = jepa_loss(
                pred_z,
                target_z,
                variance_weight=args.variance_weight,
                variance_gamma=args.variance_gamma,
                covariance_weight=args.covariance_weight,
            )
            sea_z = model.context_encoder(sea_batch, target_adj, node_annotations=None)
            cx_z = model.context_encoder(cx_batch, target_adj, node_annotations=None)
            sea_loss, sea_cos = rehearsal_loss(sea_z, sea_frozen[sea_ids].to(device), args.rehearsal_margin, args.rehearsal_temperature)
            cx_loss, cx_cos = rehearsal_loss(cx_z, cx_frozen[cx_ids].to(device), args.rehearsal_margin, args.rehearsal_temperature)
            disease_cov = off_diagonal_covariance_loss(pred_z)
            pathology_loss = pathology_similarity_loss(pred_z, pathology[cell_ids].to(device), args.pathology_contrastive_temperature)
            loss = (
                loss_jepa
                + args.sea_rehearsal_weight * sea_loss
                + args.cellxgene_rehearsal_weight * cx_loss
                + args.disease_covariance_weight * disease_cov
                + current_pathology_weight * pathology_loss
            )
            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            if args.gradient_clip_val > 0:
                torch.nn.utils.clip_grad_norm_(model.parameters(), args.gradient_clip_val)
            optimizer.step()
            model.update_target_network()

            with torch.no_grad():
                embedding_z = model.context_encoder(target_batch, target_adj, node_annotations=None)
            losses.append(float(loss.detach().cpu()))
            jepa_losses.append(float(loss_jepa.detach().cpu()))
            sea_losses.append(float(sea_loss.detach().cpu()))
            cx_losses.append(float(cx_loss.detach().cpu()))
            pathology_losses.append(float(pathology_loss.detach().cpu()))
            sea_cosines.append(float(sea_cos.detach().cpu()))
            cx_cosines.append(float(cx_cos.detach().cpu()))
            embedding_chunks.append(embedding_z.detach().cpu())
            pred_chunks.append(pred_z.detach().cpu())

        embedding_geometry = latent_geometry(torch.cat(embedding_chunks, dim=0))
        pred_geometry = latent_geometry(torch.cat(pred_chunks, dim=0))
        row = {
            "epoch": epoch,
            "loss": float(np.mean(losses)),
            "jepa_loss": float(np.mean(jepa_losses)),
            "sea_rehearsal_loss": float(np.mean(sea_losses)),
            "cellxgene_rehearsal_loss": float(np.mean(cx_losses)),
            "sea_anchor_cosine": float(np.mean(sea_cosines)),
            "cellxgene_anchor_cosine": float(np.mean(cx_cosines)),
            "pathology_contrastive_loss": float(np.mean(pathology_losses)),
            "pathology_contrastive_weight": current_pathology_weight,
            "embedding_effective_dims": embedding_geometry["effective_dims"],
            "embedding_top_sv_ratio": embedding_geometry["top_sv_ratio"],
            "embedding_mean_dim_std": embedding_geometry["mean_dim_std"],
            "predictor_effective_dims": pred_geometry["effective_dims"],
            "predictor_top_sv_ratio": pred_geometry["top_sv_ratio"],
            "mask_fraction": current_mask_fraction,
            "ema_decay": current_ema,
            "base_lr": args.base_lr,
            "head_lr": args.lr,
            "steps": len(losses),
        }
        history.append(row)
        if writer is not None:
            for key, value in row.items():
                writer.add_scalar(f"fast_stage_c/{key}", value, epoch)
        print(
            f"epoch={epoch:03d} loss={row['loss']:.6f} jepa={row['jepa_loss']:.6f} "
            f"pathology_w={row['pathology_contrastive_weight']:.5f} "
            f"embed_eff={row['embedding_effective_dims']:.2f} embed_top={row['embedding_top_sv_ratio']:.3f} "
            f"pred_eff={row['predictor_effective_dims']:.2f} pred_top={row['predictor_top_sv_ratio']:.3f} "
            f"sea_cos={row['sea_anchor_cosine']:.4f} cx_cos={row['cellxgene_anchor_cosine']:.4f} steps={row['steps']}",
            flush=True,
        )
        if args.safety_gate_start_epoch and epoch >= args.safety_gate_start_epoch:
            if row["embedding_effective_dims"] < args.min_embedding_effective_dims:
                raise RuntimeError(f"Stage C safety gate failed: embedding_effective_dims={row['embedding_effective_dims']:.2f}")
            if row["embedding_top_sv_ratio"] > args.max_embedding_top_sv_ratio:
                raise RuntimeError(f"Stage C safety gate failed: embedding_top_sv_ratio={row['embedding_top_sv_ratio']:.4f}")
        if args.checkpoint_every and epoch % args.checkpoint_every == 0:
            save_checkpoint(out_dir / f"fast_graph_jepa_stage_c_epoch_{epoch:03d}.pt")

    save_checkpoint(out_dir / "fast_graph_jepa_stage_c.pt")
    history_path = Path(args.history_out)
    history_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(history).to_csv(history_path, index=False)
    if writer is not None:
        writer.flush()
        writer.close()
    print(f"Wrote {out_dir / 'fast_graph_jepa_stage_c.pt'}")
    print(f"Wrote history to {history_path}")


if __name__ == "__main__":
    main()
