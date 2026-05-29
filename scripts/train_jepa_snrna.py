from __future__ import annotations

import argparse
from pathlib import Path

import anndata as ad
import numpy as np
import torch
from torch.utils.data import DataLoader

from sea_ad_jepa.datasets import DenseExpressionDataset
from sea_ad_jepa.gene_sets import module_indices
from sea_ad_jepa.jepa import GeneJEPA, jepa_loss


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


def main() -> None:
    parser = argparse.ArgumentParser(description="Train a minimal JEPA model on a pilot snRNA-seq AnnData file.")
    parser.add_argument("--h5ad", required=True, help="Pilot AnnData file.")
    parser.add_argument("--out-dir", default="results/models/jepa_snrna")
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--batch-size", type=int, default=256)
    parser.add_argument("--hidden-dim", type=int, default=512)
    parser.add_argument("--latent-dim", type=int, default=128)
    parser.add_argument("--mask-fraction", type=float, default=0.35)
    parser.add_argument("--mask-mode", choices=["random", "module", "mixed"], default="random")
    parser.add_argument("--min-module-genes", type=int, default=2)
    parser.add_argument(
        "--no-module-random-fill",
        action="store_true",
        help="When using module masking, mask only module genes instead of filling the mask with random genes.",
    )
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument(
        "--log-dir",
        default="runs/jepa_snrna",
        help="TensorBoard log directory. Use an empty string to disable TensorBoard logging.",
    )
    args = parser.parse_args()

    torch.manual_seed(args.seed)
    np.random.seed(args.seed)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    adata = ad.read_h5ad(args.h5ad)
    gene_names = adata.var_names.astype(str).tolist()
    modules = module_indices(gene_names, min_genes=args.min_module_genes)
    if args.mask_mode in {"module", "mixed"}:
        print(f"Using {len(modules)} gene modules for {args.mask_mode} masking")
        for name, idx in modules.items():
            print(f"  - {name}: {len(idx)} genes")
    dataset = DenseExpressionDataset(
        adata.X,
        mask_fraction=args.mask_fraction,
        seed=args.seed,
        mask_mode=args.mask_mode,
        gene_modules=modules,
        module_fill_random=not args.no_module_random_fill,
    )
    loader = DataLoader(dataset, batch_size=args.batch_size, shuffle=True, drop_last=False)

    device = choose_device(args.device)
    model = GeneJEPA(
        input_dim=adata.n_vars,
        hidden_dim=args.hidden_dim,
        latent_dim=args.latent_dim,
    ).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-4)
    writer = create_summary_writer(args.log_dir)
    if writer is not None:
        writer.add_text("config/h5ad", args.h5ad)
        writer.add_text("config/out_dir", str(out_dir))
        writer.add_text("config/mask_mode", args.mask_mode)
        writer.add_scalar("config/mask_fraction", args.mask_fraction, 0)
        writer.add_scalar("config/batch_size", args.batch_size, 0)
        writer.add_scalar("config/hidden_dim", args.hidden_dim, 0)
        writer.add_scalar("config/latent_dim", args.latent_dim, 0)
        writer.add_scalar("config/n_modules", len(modules), 0)

    history = []
    for epoch in range(1, args.epochs + 1):
        model.train()
        losses = []
        for context_x, target_x in loader:
            context_x = context_x.to(device)
            target_x = target_x.to(device)
            pred_z, target_z = model(context_x, target_x)
            loss = jepa_loss(pred_z, target_z)
            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            optimizer.step()
            losses.append(loss.item())

        mean_loss = float(np.mean(losses))
        history.append({"epoch": epoch, "loss": mean_loss})
        if writer is not None:
            writer.add_scalar("train/loss_epoch", mean_loss, epoch)
            writer.add_scalar("train/lr", optimizer.param_groups[0]["lr"], epoch)
        print(f"epoch={epoch:03d} loss={mean_loss:.6f}")

    torch.save(
        {
            "model_state": model.state_dict(),
            "n_genes": adata.n_vars,
            "gene_names": adata.var_names.astype(str).tolist(),
            "gene_modules": modules,
            "args": vars(args),
            "history": history,
        },
        out_dir / "gene_jepa.pt",
    )
    if writer is not None:
        writer.flush()
        writer.close()
        print(f"Wrote TensorBoard logs to {args.log_dir}")
    print(f"Wrote {out_dir / 'gene_jepa.pt'}")


if __name__ == "__main__":
    main()
