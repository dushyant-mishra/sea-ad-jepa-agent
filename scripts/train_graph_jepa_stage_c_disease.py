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

from sea_ad_jepa.data import load_pathology_targets, normalize_donor_id
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


def make_dataset(
    h5ad: str | Path,
    edge_index: torch.Tensor,
    node_annotations: torch.Tensor | None,
    mask_fraction: float,
    seed: int,
):
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


def rehearsal_loss(
    current_z: torch.Tensor,
    frozen_bank: torch.Tensor,
    sample_id: torch.Tensor,
    mode: str,
    margin: float,
    temperature: float,
) -> tuple[torch.Tensor, torch.Tensor]:
    frozen = frozen_bank[sample_id.long()].to(current_z.device)
    cosine = F.cosine_similarity(current_z, frozen, dim=-1)
    if mode == "mse":
        loss = F.mse_loss(F.normalize(current_z, dim=-1), F.normalize(frozen, dim=-1))
    elif mode == "cosine_margin":
        loss = F.relu(margin - cosine).mean()
    elif mode == "cosine_softplus_margin":
        loss = (F.softplus(temperature * (margin - cosine)) / temperature).mean()
    else:
        raise ValueError("mode must be 'mse', 'cosine_margin', or 'cosine_softplus_margin'")
    return loss, cosine.mean()


def dimension_elasticity_loss(
    current_z: torch.Tensor,
    frozen_bank: torch.Tensor,
    sample_id: torch.Tensor,
    margins: torch.Tensor,
    weights: torch.Tensor,
    temperature: float,
) -> torch.Tensor:
    frozen = frozen_bank[sample_id.long()].to(current_z.device)
    current = F.normalize(current_z, dim=-1)
    frozen = F.normalize(frozen, dim=-1)
    margins = margins.to(current_z.device).view(1, -1)
    weights = weights.to(current_z.device).view(1, -1)
    allowed_delta = (1.0 - margins).clamp_min(0.0)
    delta = torch.abs(current - frozen)
    penalty = F.softplus(temperature * (delta - allowed_delta)) / temperature
    return (penalty * weights).sum() / weights.sum().clamp_min(1e-8) / float(current.shape[0])


def singular_value_telemetry(z: torch.Tensor) -> tuple[float, float]:
    centered = z - z.mean(dim=0, keepdim=True)
    singular_values = torch.linalg.svdvals(centered)
    total = singular_values.sum() + 1e-8
    probabilities = singular_values / total
    entropy = -torch.sum(probabilities * torch.log(probabilities + 1e-8))
    effective_dims = torch.exp(entropy)
    top_sv_ratio = singular_values[0] / total
    return float(effective_dims), float(top_sv_ratio)


def off_diagonal_covariance_loss(z: torch.Tensor) -> torch.Tensor:
    if z.shape[0] < 2:
        return z.new_tensor(0.0)
    centered = z - z.mean(dim=0, keepdim=True)
    covariance = (centered.T @ centered) / float(z.shape[0] - 1)
    covariance = covariance.clone()
    covariance.fill_diagonal_(0.0)
    return covariance.pow(2).mean()


def pathology_similarity_loss(z: torch.Tensor, y: torch.Tensor, temperature: float) -> torch.Tensor:
    """Gently pulls cells with similar donor pathology toward similar directions.

    This is intentionally not a full contrastive repulsion objective. Covariance
    handles manifold spreading; this term only asks the expanded space to preserve
    local pathology neighborhoods.
    """
    if z.shape[0] < 2 or y.numel() == 0:
        return z.new_tensor(0.0)
    valid = torch.isfinite(y).all(dim=1)
    if int(valid.sum().item()) < 2:
        return z.new_tensor(0.0)
    z = F.normalize(z[valid], dim=-1)
    y = y[valid]
    y_std = torch.std(y, dim=0, unbiased=False, keepdim=True).clamp_min(1e-6)
    y = (y - torch.mean(y, dim=0, keepdim=True)) / y_std
    target_distance = torch.cdist(y, y, p=1) / float(y.shape[1])
    weights = torch.exp(-target_distance / max(temperature, 1e-6))
    eye = torch.eye(weights.shape[0], dtype=torch.bool, device=weights.device)
    weights = weights.masked_fill(eye, 0.0)
    denominator = weights.sum().clamp_min(1e-8)
    cosine = z @ z.T
    return (weights * (1.0 - cosine)).sum() / denominator


def build_pathology_matrix(
    adata: ad.AnnData,
    donor_column: str,
    target_columns: list[str],
    targets_path: str,
    target_columns_path: str,
) -> torch.Tensor:
    targets, _ = load_pathology_targets(targets_path, target_columns_path)
    targets = targets.copy()
    targets["Donor ID"] = normalize_donor_id(targets["Donor ID"])
    if donor_column not in adata.obs:
        raise KeyError(f"Donor column not found in disease H5AD obs: {donor_column}")
    missing = [column for column in target_columns if column not in targets.columns]
    if missing:
        raise KeyError(f"Pathology target columns not found: {missing}")

    donor_to_targets = targets.set_index("Donor ID")[target_columns]
    donors = normalize_donor_id(adata.obs[donor_column]).reset_index(drop=True)
    values = donor_to_targets.reindex(donors).to_numpy(dtype=np.float32)
    return torch.as_tensor(values, dtype=torch.float32)


def load_latent_elasticity_policy(path: str | Path, latent_dim: int) -> tuple[torch.Tensor, torch.Tensor]:
    policy = pd.read_csv(path)
    if "latent_id" not in policy:
        if "latent_factor" not in policy:
            raise ValueError("Latent elasticity policy must include latent_id or latent_factor.")
        policy["latent_id"] = policy["latent_factor"].astype(str).str.extract(r"(\d+)").astype(int)
    if "margin" not in policy or "weight" not in policy:
        raise ValueError("Latent elasticity policy must include margin and weight columns.")
    margins = torch.full((latent_dim,), 0.95, dtype=torch.float32)
    weights = torch.ones(latent_dim, dtype=torch.float32)
    for row in policy.itertuples(index=False):
        latent_id = int(getattr(row, "latent_id"))
        if 0 <= latent_id < latent_dim:
            margins[latent_id] = float(getattr(row, "margin"))
            weights[latent_id] = float(getattr(row, "weight"))
    return margins, weights


def checkpoint_arg(checkpoint: dict, key: str, default):
    value = checkpoint.get("args", {}).get(key, default)
    return default if value is None else value


def main() -> None:
    parser = argparse.ArgumentParser(description="Stage C Graph-JEPA disease-vector training with three-stream rehearsal.")
    parser.add_argument("--checkpoint", default="results/models/graph_jepa_stage_b_low_pathology_rehearsal_e20/graph_jepa_stage_b.pt")
    parser.add_argument("--disease-h5ad", default="data/processed/sea_ad_mtg_microglia_pvm_all_hvg3k_expanded_modules.h5ad")
    parser.add_argument("--sea-anchor-h5ad", default="data/processed/v2_pretraining/sea_ad_low_pathology_microglia_pvm_relaxed_jepa_aligned.h5ad")
    parser.add_argument("--sea-anchor-coordinates", default="results/tables/stage_b_rehearsal_sea_ad_low_pathology_relaxed_coordinates.csv")
    parser.add_argument("--cellxgene-anchor-h5ad", default="data/processed/v2_pretraining/cellxgene_normal_microglia_nucleus_relaxed_assay_jepa_aligned.h5ad")
    parser.add_argument("--cellxgene-anchor-coordinates", default="results/tables/stage_b_rehearsal_cellxgene_normal_microglia_coordinates.csv")
    parser.add_argument("--edge-csv", default="results/tables/v2_graph_string_edges_t700.csv")
    parser.add_argument("--annotation-csv", default="results/tables/jepa_v2_translational_actionability_matrix.csv")
    parser.add_argument("--out-dir", default="results/models/graph_jepa_stage_c_disease_rehearsal_e20")
    parser.add_argument("--log-dir", default="runs/graph_jepa_stage_c_disease_rehearsal_e20")
    parser.add_argument("--history-out", default="results/tables/graph_jepa_stage_c_disease_rehearsal_history.csv")
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--checkpoint-every", type=int, default=5)
    parser.add_argument("--disease-batch-size", type=int, default=16)
    parser.add_argument("--sea-anchor-batch-size", type=int, default=8)
    parser.add_argument("--cellxgene-anchor-batch-size", type=int, default=8)
    parser.add_argument("--sea-rehearsal-weight", type=float, default=0.5)
    parser.add_argument("--cellxgene-rehearsal-weight", type=float, default=0.5)
    parser.add_argument("--rehearsal-loss-mode", choices=["mse", "cosine_margin", "cosine_softplus_margin"], default="mse")
    parser.add_argument("--rehearsal-margin", type=float, default=0.95)
    parser.add_argument("--rehearsal-temperature", type=float, default=100.0)
    parser.add_argument("--variance-weight", type=float, default=1.0)
    parser.add_argument("--variance-gamma", type=float, default=1.0)
    parser.add_argument("--covariance-weight", type=float, default=0.0)
    parser.add_argument("--disease-covariance-weight", type=float, default=0.0)
    parser.add_argument("--use-projection-head", action="store_true")
    parser.add_argument("--projection-hidden-dim", type=int, default=0)
    parser.add_argument("--stage-c-prediction-space", choices=["encoder", "projector"], default="encoder")
    parser.add_argument("--rehearsal-space", choices=["encoder", "projector"], default="encoder")
    parser.add_argument("--downstream-embedding-space", choices=["encoder", "projector"], default="encoder")
    parser.add_argument("--pathology-contrastive-weight", type=float, default=0.0)
    parser.add_argument("--pathology-contrastive-temperature", type=float, default=0.75)
    parser.add_argument(
        "--pathology-contrastive-targets",
        nargs="+",
        default=["percent AT8 positive area_Grey matter", "percent NeuN positive area_Grey matter"],
    )
    parser.add_argument("--pathology-targets-path", default="data/processed/metadata/sea_ad_mtg_donor_pathology_targets.csv")
    parser.add_argument("--pathology-target-columns-path", default="data/processed/metadata/pathology_target_columns.csv")
    parser.add_argument("--donor-column", default="Donor ID")
    parser.add_argument("--latent-elasticity-policy", default="")
    parser.add_argument("--latent-elasticity-weight", type=float, default=0.0)
    parser.add_argument("--mask-start-fraction", type=float, default=0.2)
    parser.add_argument("--mask-fraction", type=float, default=0.5)
    parser.add_argument("--mask-warmup-epochs", type=int, default=10)
    parser.add_argument("--ema-start-decay", type=float, default=0.995)
    parser.add_argument("--ema-decay", type=float, default=0.9995)
    parser.add_argument("--ema-warmup-epochs", type=int, default=10)
    parser.add_argument("--lr", type=float, default=2e-5)
    parser.add_argument("--weight-decay", type=float, default=1e-4)
    parser.add_argument("--gradient-clip-val", type=float, default=1.0)
    parser.add_argument("--max-steps-per-epoch", type=int, default=0, help="Optional cap for smoke tests. 0 uses all disease batches.")
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
    edge_index = load_consensus_edge_index(args.edge_csv)

    disease_adata = ad.read_h5ad(args.disease_h5ad)
    gene_names = disease_adata.var_names.astype(str).tolist()
    node_annotations = node_annotation_tensor(args.annotation_csv, gene_names) if args.use_node_annotations else None
    node_feature_dim = 1 + (int(node_annotations.shape[1]) if node_annotations is not None else 0)

    disease_dataset = GraphExpressionDataset(
        disease_adata.X,
        edge_index=edge_index,
        node_annotations=node_annotations,
        mask_fraction=args.mask_start_fraction,
        seed=args.seed,
        return_pyg_data=True,
    )
    sea_anchor_adata, sea_anchor_dataset = make_dataset(
        args.sea_anchor_h5ad,
        edge_index=edge_index,
        node_annotations=node_annotations,
        mask_fraction=0.0,
        seed=args.seed + 1,
    )
    cellxgene_anchor_adata, cellxgene_anchor_dataset = make_dataset(
        args.cellxgene_anchor_h5ad,
        edge_index=edge_index,
        node_annotations=node_annotations,
        mask_fraction=0.0,
        seed=args.seed + 2,
    )

    expected_n_genes = int(checkpoint["n_genes"])
    for label, adata in (
        ("disease", disease_adata),
        ("sea_anchor", sea_anchor_adata),
        ("cellxgene_anchor", cellxgene_anchor_adata),
    ):
        if adata.n_vars != expected_n_genes:
            raise ValueError(f"{label} H5AD has {adata.n_vars} genes, but checkpoint expects {expected_n_genes}.")

    sea_frozen = load_frozen_latents(args.sea_anchor_coordinates)
    cellxgene_frozen = load_frozen_latents(args.cellxgene_anchor_coordinates)
    if sea_frozen.shape[0] != sea_anchor_adata.n_obs:
        raise ValueError("SEA anchor coordinate rows do not match SEA anchor H5AD cells.")
    if cellxgene_frozen.shape[0] != cellxgene_anchor_adata.n_obs:
        raise ValueError("CELLxGENE coordinate rows do not match CELLxGENE H5AD cells.")

    disease_loader = DataLoader(disease_dataset, batch_size=args.disease_batch_size, shuffle=True)
    sea_anchor_loader = DataLoader(sea_anchor_dataset, batch_size=args.sea_anchor_batch_size, shuffle=True)
    cellxgene_anchor_loader = DataLoader(cellxgene_anchor_dataset, batch_size=args.cellxgene_anchor_batch_size, shuffle=True)

    model = GraphGeneJEPA(
        n_genes=expected_n_genes,
        node_feature_dim=node_feature_dim,
        gene_embed_dim=int(checkpoint_arg(checkpoint, "gene_embed_dim", 32)),
        hidden_dim=int(checkpoint_arg(checkpoint, "hidden_dim", 128)),
        latent_dim=int(checkpoint_arg(checkpoint, "latent_dim", 128)),
        n_layers=int(checkpoint_arg(checkpoint, "n_layers", 2)),
        dropout=float(checkpoint_arg(checkpoint, "dropout", 0.1)),
        conv=str(checkpoint_arg(checkpoint, "conv", "sage")),
        ema_decay=float(checkpoint_arg(checkpoint, "ema_decay", args.ema_start_decay)),
        use_projection_head=args.use_projection_head,
        projection_hidden_dim=args.projection_hidden_dim or None,
    ).to(device)
    load_result = model.load_state_dict(checkpoint["model_state"], strict=not args.use_projection_head)
    if args.use_projection_head:
        print(f"Loaded checkpoint with projection head initialized fresh. Missing keys: {len(load_result.missing_keys)}")
        model.reset_target_network()

    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    writer = create_summary_writer(args.log_dir)
    history = []
    sea_frozen = sea_frozen.to(device)
    cellxgene_frozen = cellxgene_frozen.to(device)
    cellxgene_frozen_centroid = cellxgene_frozen.mean(dim=0)
    disease_pathology = None
    if args.pathology_contrastive_weight > 0:
        disease_pathology = build_pathology_matrix(
            disease_adata,
            donor_column=args.donor_column,
            target_columns=args.pathology_contrastive_targets,
            targets_path=args.pathology_targets_path,
            target_columns_path=args.pathology_target_columns_path,
        ).to(device)
        print(
            "Loaded pathology contrastive targets: "
            + ", ".join(args.pathology_contrastive_targets)
            + f" ({disease_pathology.shape[0]:,} cells x {disease_pathology.shape[1]} targets)"
        )
    latent_elasticity_margins = None
    latent_elasticity_weights = None
    if args.latent_elasticity_weight > 0:
        if not args.latent_elasticity_policy:
            raise ValueError("--latent-elasticity-policy is required when --latent-elasticity-weight > 0")
        latent_dim = int(checkpoint_arg(checkpoint, "latent_dim", 128))
        latent_elasticity_margins, latent_elasticity_weights = load_latent_elasticity_policy(
            args.latent_elasticity_policy,
            latent_dim=latent_dim,
        )
        print(
            f"Loaded latent elasticity policy: {args.latent_elasticity_policy} "
            f"(margin range {latent_elasticity_margins.min():.3f}-{latent_elasticity_margins.max():.3f}, "
            f"weight range {latent_elasticity_weights.min():.3f}-{latent_elasticity_weights.max():.3f})"
        )

    def save_checkpoint(path: Path) -> None:
        torch.save(
            {
                "model_state": model.state_dict(),
                "n_genes": expected_n_genes,
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
        disease_dataset.mask_fraction = current_mask_fraction
        model.ema_decay = current_ema_decay

        sea_iter = itertools.cycle(sea_anchor_loader)
        cellxgene_iter = itertools.cycle(cellxgene_anchor_loader)

        losses = []
        disease_jepa_losses = []
        sea_rehearsal_losses = []
        cellxgene_rehearsal_losses = []
        sea_anchor_cosines = []
        cellxgene_anchor_cosines = []
        disease_to_cellxgene_centroid_l2 = []
        disease_variance_spreads = []
        disease_covariance_losses = []
        pathology_contrastive_losses = []
        latent_elasticity_losses = []
        alignment_losses = []
        variance_losses = []
        covariance_losses = []
        epoch_disease_preds = []

        for step, (disease_context, disease_target) in enumerate(disease_loader, start=1):
            if args.max_steps_per_epoch and step > args.max_steps_per_epoch:
                break

            _, sea_anchor_target = next(sea_iter)
            _, cellxgene_anchor_target = next(cellxgene_iter)

            disease_context = disease_context.to(device)
            disease_target = disease_target.to(device)
            sea_anchor_target = sea_anchor_target.to(device)
            cellxgene_anchor_target = cellxgene_anchor_target.to(device)

            pred_z, target_z = model(disease_context, disease_target, prediction_space=args.stage_c_prediction_space)
            disease_loss, parts = jepa_loss(
                pred_z,
                target_z,
                variance_weight=args.variance_weight,
                variance_gamma=args.variance_gamma,
                covariance_weight=args.covariance_weight,
            )

            sea_current = model.encode_raw(sea_anchor_target, space=args.rehearsal_space)
            cellxgene_current = model.encode_raw(cellxgene_anchor_target, space=args.rehearsal_space)
            sea_anchor_loss, sea_anchor_cosine = rehearsal_loss(
                sea_current,
                sea_frozen,
                sea_anchor_target.sample_id,
                mode=args.rehearsal_loss_mode,
                margin=args.rehearsal_margin,
                temperature=args.rehearsal_temperature,
            )
            cellxgene_anchor_loss, cellxgene_anchor_cosine = rehearsal_loss(
                cellxgene_current,
                cellxgene_frozen,
                cellxgene_anchor_target.sample_id,
                mode=args.rehearsal_loss_mode,
                margin=args.rehearsal_margin,
                temperature=args.rehearsal_temperature,
            )
            if latent_elasticity_margins is not None and latent_elasticity_weights is not None:
                sea_latent_elasticity_loss = dimension_elasticity_loss(
                    sea_current,
                    sea_frozen,
                    sea_anchor_target.sample_id,
                    margins=latent_elasticity_margins,
                    weights=latent_elasticity_weights,
                    temperature=args.rehearsal_temperature,
                )
                cellxgene_latent_elasticity_loss = dimension_elasticity_loss(
                    cellxgene_current,
                    cellxgene_frozen,
                    cellxgene_anchor_target.sample_id,
                    margins=latent_elasticity_margins,
                    weights=latent_elasticity_weights,
                    temperature=args.rehearsal_temperature,
                )
                latent_elasticity_loss = 0.5 * (sea_latent_elasticity_loss + cellxgene_latent_elasticity_loss)
            else:
                latent_elasticity_loss = pred_z.new_tensor(0.0)
            disease_centroid_l2 = torch.norm(pred_z - cellxgene_frozen_centroid, dim=-1).mean()
            disease_variance_spread = torch.var(pred_z, dim=0, unbiased=False).mean()
            disease_covariance_loss = off_diagonal_covariance_loss(pred_z)
            if disease_pathology is not None:
                batch_pathology = disease_pathology[disease_target.sample_id.long()]
                pathology_loss = pathology_similarity_loss(
                    pred_z,
                    batch_pathology,
                    temperature=args.pathology_contrastive_temperature,
                )
            else:
                pathology_loss = pred_z.new_tensor(0.0)

            loss = (
                disease_loss
                + args.sea_rehearsal_weight * sea_anchor_loss
                + args.cellxgene_rehearsal_weight * cellxgene_anchor_loss
                + args.disease_covariance_weight * disease_covariance_loss
                + args.pathology_contrastive_weight * pathology_loss
                + args.latent_elasticity_weight * latent_elasticity_loss
            )

            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            if args.gradient_clip_val > 0:
                torch.nn.utils.clip_grad_norm_(model.parameters(), args.gradient_clip_val)
            optimizer.step()
            model.update_target_network()

            losses.append(float(loss.detach().cpu()))
            disease_jepa_losses.append(float(disease_loss.detach().cpu()))
            sea_rehearsal_losses.append(float(sea_anchor_loss.detach().cpu()))
            cellxgene_rehearsal_losses.append(float(cellxgene_anchor_loss.detach().cpu()))
            sea_anchor_cosines.append(float(sea_anchor_cosine.detach().cpu()))
            cellxgene_anchor_cosines.append(float(cellxgene_anchor_cosine.detach().cpu()))
            disease_to_cellxgene_centroid_l2.append(float(disease_centroid_l2.detach().cpu()))
            disease_variance_spreads.append(float(disease_variance_spread.detach().cpu()))
            disease_covariance_losses.append(float(disease_covariance_loss.detach().cpu()))
            pathology_contrastive_losses.append(float(pathology_loss.detach().cpu()))
            latent_elasticity_losses.append(float(latent_elasticity_loss.detach().cpu()))
            alignment_losses.append(float(parts["alignment"].cpu()))
            variance_losses.append(float(parts["variance"].cpu()))
            covariance_losses.append(float(parts.get("covariance", torch.tensor(0.0)).cpu()))
            epoch_disease_preds.append(pred_z.detach().cpu())

        all_disease_preds = torch.cat(epoch_disease_preds, dim=0)
        disease_effective_dims, disease_top_sv_ratio = singular_value_telemetry(all_disease_preds)

        row = {
            "epoch": epoch,
            "loss": float(np.mean(losses)),
            "disease_jepa_loss": float(np.mean(disease_jepa_losses)),
            "sea_rehearsal_loss": float(np.mean(sea_rehearsal_losses)),
            "cellxgene_rehearsal_loss": float(np.mean(cellxgene_rehearsal_losses)),
            "sea_anchor_cosine": float(np.mean(sea_anchor_cosines)),
            "cellxgene_anchor_cosine": float(np.mean(cellxgene_anchor_cosines)),
            "disease_to_cellxgene_centroid_l2": float(np.mean(disease_to_cellxgene_centroid_l2)),
            "disease_variance_spread": float(np.mean(disease_variance_spreads)),
            "disease_covariance_loss": float(np.mean(disease_covariance_losses)),
            "pathology_contrastive_loss": float(np.mean(pathology_contrastive_losses)),
            "latent_elasticity_loss": float(np.mean(latent_elasticity_losses)),
            "disease_effective_dims": disease_effective_dims,
            "disease_top_sv_ratio": disease_top_sv_ratio,
            "alignment_loss": float(np.mean(alignment_losses)),
            "variance_loss": float(np.mean(variance_losses)),
            "covariance_loss": float(np.mean(covariance_losses)),
            "mask_fraction": current_mask_fraction,
            "ema_decay": current_ema_decay,
            "steps": int(len(losses)),
        }
        history.append(row)
        if writer is not None:
            for key, value in row.items():
                if key != "epoch":
                    writer.add_scalar(f"train/{key}", value, epoch)
        print(
            f"epoch={epoch:03d} loss={row['loss']:.6f} disease_jepa={row['disease_jepa_loss']:.6f} "
            f"sea_rehearsal={row['sea_rehearsal_loss']:.6f} "
            f"cellxgene_rehearsal={row['cellxgene_rehearsal_loss']:.6f} "
            f"sea_cos={row['sea_anchor_cosine']:.4f} "
            f"cx_cos={row['cellxgene_anchor_cosine']:.4f} "
            f"disease_cx_l2={row['disease_to_cellxgene_centroid_l2']:.4f} "
            f"disease_var={row['disease_variance_spread']:.6f} "
            f"disease_cov={row['disease_covariance_loss']:.6f} "
            f"pathology_ctr={row['pathology_contrastive_loss']:.6f} "
            f"latent_elastic={row['latent_elasticity_loss']:.6f} "
            f"eff_dims={row['disease_effective_dims']:.2f} "
            f"top_sv={row['disease_top_sv_ratio']:.4f} "
            f"alignment={row['alignment_loss']:.6f} variance={row['variance_loss']:.6f} steps={row['steps']}"
        )
        if args.checkpoint_every and epoch % args.checkpoint_every == 0:
            path = out_dir / f"graph_jepa_stage_c_epoch_{epoch:03d}.pt"
            save_checkpoint(path)
            print(f"Wrote interim checkpoint: {path}")

    save_checkpoint(out_dir / "graph_jepa_stage_c.pt")
    history_path = Path(args.history_out)
    history_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(history).to_csv(history_path, index=False)
    if writer is not None:
        writer.flush()
        writer.close()
    print(f"Wrote {out_dir / 'graph_jepa_stage_c.pt'}")
    print(f"Wrote history to {history_path}")
    if args.log_dir:
        print(f"Wrote TensorBoard logs to {args.log_dir}")


if __name__ == "__main__":
    main()
