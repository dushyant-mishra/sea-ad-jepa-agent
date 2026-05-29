from __future__ import annotations

import argparse
from pathlib import Path

import anndata as ad
import numpy as np
import torch
from torch.utils.data import DataLoader

from sea_ad_jepa.datasets import DenseExpressionDataset
from sea_ad_jepa.jepa import GeneJEPA, jepa_loss


def choose_device(requested: str) -> torch.device:
    if requested == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    return torch.device(requested)


def main() -> None:
    parser = argparse.ArgumentParser(description="Train a minimal JEPA model on a pilot snRNA-seq AnnData file.")
    parser.add_argument("--h5ad", required=True, help="Pilot AnnData file.")
    parser.add_argument("--out-dir", default="results/models/jepa_snrna")
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--batch-size", type=int, default=256)
    parser.add_argument("--hidden-dim", type=int, default=512)
    parser.add_argument("--latent-dim", type=int, default=128)
    parser.add_argument("--mask-fraction", type=float, default=0.35)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()

    torch.manual_seed(args.seed)
    np.random.seed(args.seed)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    adata = ad.read_h5ad(args.h5ad)
    dataset = DenseExpressionDataset(adata.X, mask_fraction=args.mask_fraction, seed=args.seed)
    loader = DataLoader(dataset, batch_size=args.batch_size, shuffle=True, drop_last=False)

    device = choose_device(args.device)
    model = GeneJEPA(
        input_dim=adata.n_vars,
        hidden_dim=args.hidden_dim,
        latent_dim=args.latent_dim,
    ).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-4)

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
        print(f"epoch={epoch:03d} loss={mean_loss:.6f}")

    torch.save(
        {
            "model_state": model.state_dict(),
            "n_genes": adata.n_vars,
            "gene_names": adata.var_names.astype(str).tolist(),
            "args": vars(args),
            "history": history,
        },
        out_dir / "gene_jepa.pt",
    )
    print(f"Wrote {out_dir / 'gene_jepa.pt'}")


if __name__ == "__main__":
    main()

