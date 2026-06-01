from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import argparse
import anndata as ad
import numpy as np
import pandas as pd
import torch
from scipy import sparse
from sklearn.model_selection import GroupKFold, StratifiedGroupKFold
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

from sea_ad_jepa.baselines import spearman_corr
from sea_ad_jepa.data import load_pathology_targets, normalize_donor_id
from sea_ad_jepa.gene_sets import MICROGLIA_GENE_MODULES
from sea_ad_jepa.jepa import GeneJEPA
from sea_ad_jepa.evaluation_utils import (
    choose_device,
    to_dense_float32,
    transform_target,
    inverse_transform_prediction,
    make_strata,
    PathologyRegressor,
    build_balanced_sampler,
    load_jepa,
    predict_cells,
    predict_by_donor,
    train_fold_head,
)



def build_perturbation_sets(
    gene_names: list[str],
    mode: str,
    modules: list[str] | None,
    min_genes: int,
) -> list[tuple[str, str, list[str], list[int]]]:
    gene_to_idx = {gene.upper(): idx for idx, gene in enumerate(gene_names)}
    selected_modules = modules or sorted(MICROGLIA_GENE_MODULES)
    perturbations = []
    for module_name in selected_modules:
        if module_name not in MICROGLIA_GENE_MODULES:
            raise KeyError(f"Unknown module: {module_name}")
        present_genes = sorted(gene for gene in MICROGLIA_GENE_MODULES[module_name] if gene.upper() in gene_to_idx)
        if mode in {"module", "two-pass"}:
            idx = [gene_to_idx[gene.upper()] for gene in present_genes]
            if len(idx) >= min_genes:
                perturbations.append((module_name, module_name, present_genes, idx))
        else:
            for gene in present_genes:
                perturbations.append((module_name, gene, [gene], [gene_to_idx[gene.upper()]]))
    return perturbations


def apply_intervention(
    x_base: np.ndarray,
    target_idx: list[int],
    intervention: str,
    donors: pd.Series,
    global_means: np.ndarray,
) -> np.ndarray:
    x_perturbed = x_base.copy()
    if intervention == "zero":
        x_perturbed[:, target_idx] = 0.0
    elif intervention == "global_mean":
        x_perturbed[:, target_idx] = global_means[target_idx]
    elif intervention == "donor_mean":
        for _, row_idx in donors.groupby(donors).indices.items():
            rows = np.asarray(row_idx, dtype=np.int64)
            donor_mean = x_base[rows][:, target_idx].mean(axis=0)
            x_perturbed[np.ix_(rows, target_idx)] = donor_mean
    else:
        raise ValueError(f"Unknown intervention: {intervention}")
    return x_perturbed


def bootstrap_ci(values: np.ndarray, n_bootstrap: int, seed: int, ci: float) -> tuple[float, float]:
    clean = np.asarray(values, dtype=np.float32)
    clean = clean[np.isfinite(clean)]
    if clean.size == 0:
        return float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    boot = np.empty(n_bootstrap, dtype=np.float32)
    for i in range(n_bootstrap):
        boot[i] = float(np.mean(rng.choice(clean, size=clean.size, replace=True)))
    alpha = (100.0 - ci) / 2.0
    return float(np.percentile(boot, alpha)), float(np.percentile(boot, 100.0 - alpha))


def summarize_outputs(
    donor_df: pd.DataFrame,
    fold_df: pd.DataFrame,
    n_bootstrap: int,
    seed: int,
    ci: float,
) -> pd.DataFrame:
    rows = []
    for (module, perturbation, intervention), group in donor_df.groupby(["module", "perturbation", "intervention"]):
        donor_delta = group["delta"].to_numpy(dtype=np.float32)
        fold_group = fold_df[
            (fold_df["module"] == module)
            & (fold_df["perturbation"] == perturbation)
            & (fold_df["intervention"] == intervention)
        ]
        fold_deltas = fold_group["mean_donor_delta"].to_numpy(dtype=np.float32)
        ci_low, ci_high = bootstrap_ci(donor_delta, n_bootstrap=n_bootstrap, seed=seed, ci=ci)
        sign_consistency = float(np.mean(np.sign(fold_deltas) == np.sign(np.mean(donor_delta)))) if fold_deltas.size else float("nan")
        rows.append(
            {
                "module": module,
                "perturbation": perturbation,
                "intervention": intervention,
                "n_genes_perturbed": int(group["n_genes_perturbed"].iloc[0]),
                "genes": str(group["genes"].iloc[0]),
                "mean_baseline_prediction": float(group["baseline_prediction"].mean()),
                "mean_perturbed_prediction": float(group["perturbed_prediction"].mean()),
                "mean_donor_delta": float(np.mean(donor_delta)),
                "median_donor_delta": float(np.median(donor_delta)),
                "abs_mean_donor_delta": float(abs(np.mean(donor_delta))),
                "bootstrap_ci_low": ci_low,
                "bootstrap_ci_high": ci_high,
                "n_donors": int(group["Donor ID"].nunique()),
                "n_predictions": int(group.shape[0]),
                "n_fold_evals": int(fold_deltas.size),
                "fold_delta_std": float(np.std(fold_deltas, ddof=1)) if fold_deltas.size > 1 else float("nan"),
                "fold_sign_consistency": sign_consistency,
                "mean_fold_val_spearman": float(fold_group["val_spearman"].mean()) if not fold_group.empty else float("nan"),
            }
        )
    return pd.DataFrame(rows).sort_values("abs_mean_donor_delta", ascending=False)


def run_knockouts_for_perturbations(
    perturbations: list[tuple[str, str, list[str], list[int]]],
    cached_folds: dict,
    x_np: np.ndarray,
    donors: pd.Series,
    global_means: np.ndarray,
    args: argparse.Namespace,
    device: torch.device,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    donor_rows = []
    fold_rows = []
    
    for repeat, folds in cached_folds.items():
        for fold_id, fold_data in folds.items():
            model = fold_data["model"]
            head = fold_data["head"]
            fit_row = fold_data["fit_row"]
            train_mean = fold_data["train_mean"]
            train_std = fold_data["train_std"]
            val_idx = fold_data["val_idx"]
            
            x_val = x_np[val_idx]
            val_donor_series = donors.iloc[val_idx].reset_index(drop=True)
            
            # Predict baseline (inverts scale internally in predict_cells, but wait, predict_cells returns pred_raw_scale as the second element)
            # Let's verify that baseline_raw and perturbed_raw are in real biological units.
            # Yes! predict_cells returns: pred_model_scale, pred_raw_scale (with inverse target transform).
            # So baseline_raw is in real biological units.
            _, baseline_raw = predict_cells(
                model=model,
                head=head,
                x_np=x_val,
                device=device,
                batch_size=args.batch_size,
                train_mean=train_mean,
                train_std=train_std,
                target_transform=args.target_transform,
            )
            
            for module, perturbation, genes, idx in perturbations:
                x_ko = apply_intervention(
                    x_base=x_val,
                    target_idx=idx,
                    intervention=args.intervention,
                    donors=val_donor_series,
                    global_means=global_means,
                )
                _, perturbed_raw = predict_cells(
                    model=model,
                    head=head,
                    x_np=x_ko,
                    device=device,
                    batch_size=args.batch_size,
                    train_mean=train_mean,
                    train_std=train_std,
                    target_transform=args.target_transform,
                )
                
                # Causal delta in raw biological units!
                cell_delta = perturbed_raw - baseline_raw
                
                donor_df = (
                    pd.DataFrame(
                        {
                            "Donor ID": val_donor_series.to_numpy(),
                            "baseline_prediction": baseline_raw,
                            "perturbed_prediction": perturbed_raw,
                            "delta": cell_delta,
                        }
                    )
                    .groupby("Donor ID", as_index=False)
                    .mean()
                )
                donor_df.insert(0, "repeat", repeat)
                donor_df.insert(1, "fold", fold_id)
                donor_df.insert(2, "module", module)
                donor_df.insert(3, "perturbation", perturbation)
                donor_df.insert(4, "intervention", args.intervention)
                donor_df["n_genes_perturbed"] = len(genes)
                donor_df["genes"] = ";".join(genes)
                donor_rows.append(donor_df)
                
                fold_delta = donor_df["delta"].to_numpy(dtype=np.float32)
                fold_rows.append(
                    {
                        "repeat": repeat,
                        "fold": fold_id,
                        "module": module,
                        "perturbation": perturbation,
                        "intervention": args.intervention,
                        "n_genes_perturbed": len(genes),
                        "genes": ";".join(genes),
                        "mean_baseline_prediction": float(donor_df["baseline_prediction"].mean()),
                        "mean_perturbed_prediction": float(donor_df["perturbed_prediction"].mean()),
                        "mean_donor_delta": float(np.mean(fold_delta)),
                        "median_donor_delta": float(np.median(fold_delta)),
                        "abs_mean_donor_delta": float(abs(np.mean(fold_delta))),
                        "n_donors": int(donor_df["Donor ID"].nunique()),
                        "n_cells": int(val_idx.size),
                        "best_epoch": fit_row["best_epoch"],
                        "val_spearman": fit_row["val_spearman"],
                        "val_mae": fit_row["val_mae"],
                    }
                )
                
    donor_df = pd.concat(donor_rows, ignore_index=True) if donor_rows else pd.DataFrame()
    fold_df = pd.DataFrame(fold_rows)
    summary_df = summarize_outputs(
        donor_df=donor_df,
        fold_df=fold_df,
        n_bootstrap=args.n_bootstrap,
        seed=args.seed,
        ci=args.ci,
    )
    return summary_df, donor_df, fold_df



def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run donor-held-out fold-specific in-silico knockouts with a JEPA pathology head."
    )
    parser.add_argument("--h5ad", required=True)
    parser.add_argument("--checkpoint", required=True, help="Self-supervised JEPA checkpoint used to initialize each fold.")
    parser.add_argument("--target", default="percent AT8 positive area_Grey matter")
    parser.add_argument("--target-transform", choices=["raw", "log1p", "rank"], default="log1p")
    parser.add_argument("--splitter", choices=["groupkfold", "stratified_groupkfold"], default="stratified_groupkfold")
    parser.add_argument("--target-bins", type=int, default=5)
    parser.add_argument("--n-splits", type=int, default=5)
    parser.add_argument("--n-repeats", type=int, default=1, help="Number of times to repeat the K-fold split with different random shuffles.")
    parser.add_argument("--mode", choices=["module", "gene", "two-pass"], default="module")
    parser.add_argument("--top-n-modules", type=int, default=3, help="In two-pass mode, how many top modules (by highest OOF absolute delta) to run gene-level knockouts on.")
    parser.add_argument("--save-fold-heads-dir", default="results/models/fold_heads", help="Directory where fold-specific pathology heads will be saved. Set empty to disable.")
    parser.add_argument("--load-fold-heads-dir", default="", help="If set, loads saved fold-specific pathology heads from this directory instead of training them.")
    parser.add_argument("--modules", nargs="*", default=None)
    parser.add_argument("--intervention", choices=["global_mean", "donor_mean", "zero"], default="global_mean")
    parser.add_argument("--donor-column", default="Donor ID")
    parser.add_argument("--min-genes", type=int, default=2)
    parser.add_argument("--epochs", type=int, default=15)
    parser.add_argument("--batch-size", type=int, default=512)
    parser.add_argument("--samples-per-epoch", type=int, default=40000)
    parser.add_argument("--lr", type=float, default=5e-5)
    parser.add_argument("--head-hidden-dim", type=int, default=128)
    parser.add_argument("--dropout", type=float, default=0.1)
    parser.add_argument("--weight-decay", type=float, default=1e-4)
    parser.add_argument("--freeze-encoder", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--n-bootstrap", type=int, default=2000)
    parser.add_argument("--ci", type=float, default=95.0)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--out", default="results/tables/causal_fold_specific_module_knockouts_at8.csv")
    parser.add_argument("--donor-out", default="results/tables/causal_fold_specific_module_knockouts_at8_by_donor.csv")
    parser.add_argument("--fold-out", default="results/tables/causal_fold_specific_module_knockouts_at8_by_fold.csv")
    args = parser.parse_args()

    torch.manual_seed(args.seed)
    np.random.seed(args.seed)
    device = choose_device(args.device)
    adata = ad.read_h5ad(args.h5ad)
    if args.donor_column not in adata.obs:
        raise KeyError(f"Donor column not found in AnnData obs: {args.donor_column}")
    donors = normalize_donor_id(adata.obs[args.donor_column]).reset_index(drop=True)
    x_np = to_dense_float32(adata.X)
    x = torch.from_numpy(x_np)
    gene_names = adata.var_names.astype(str).tolist()

    _, base_checkpoint = load_jepa(args.checkpoint, device)
    if int(base_checkpoint["n_genes"]) != x_np.shape[1]:
        raise ValueError(f"Checkpoint expects {base_checkpoint['n_genes']} genes but AnnData has {x_np.shape[1]} genes.")

    targets, _ = load_pathology_targets()
    targets["Donor ID"] = normalize_donor_id(targets["Donor ID"])
    if args.target not in targets:
        raise KeyError(f"Target not found in pathology table: {args.target}")
    target_df = targets[["Donor ID", args.target]].copy()
    target_df[args.target] = pd.to_numeric(target_df[args.target], errors="coerce")
    target_df = target_df.dropna(subset=[args.target]).reset_index(drop=True)
    label_lookup = target_df.set_index("Donor ID")[args.target]
    y_raw = donors.map(label_lookup).to_numpy(dtype=np.float32)
    keep = np.isfinite(y_raw)
    y_transformed = transform_target(y_raw, args.target_transform)

    cached_folds = {}
    print(f"Loaded {x_np.shape[0]:,} cells x {x_np.shape[1]:,} genes")
    print(f"Target: {args.target}")
    print(f"Target transform: {args.target_transform}; Splitter: {args.splitter}")
    print(f"Repeats to run: {args.n_repeats}; Splits per repeat: {args.n_splits}")

    for repeat in range(args.n_repeats):
        cached_folds[repeat] = {}
        split_target_df = target_df[target_df["Donor ID"].isin(set(donors[keep]))].reset_index(drop=True)
        groups = split_target_df["Donor ID"].to_numpy()
        y_for_split = split_target_df[args.target].to_numpy(dtype=np.float32)
        if args.splitter == "stratified_groupkfold":
            y_for_split = make_strata(y_for_split, args.target_bins)
            splitter = StratifiedGroupKFold(n_splits=args.n_splits, shuffle=True, random_state=args.seed + repeat)
        else:
            splitter = GroupKFold(n_splits=args.n_splits)
        folds = list(splitter.split(split_target_df, y_for_split, groups=groups))

        for fold_id, (train_donor_idx, val_donor_idx) in enumerate(folds, start=1):
            train_donors = set(split_target_df.iloc[train_donor_idx]["Donor ID"])
            val_donors = set(split_target_df.iloc[val_donor_idx]["Donor ID"])
            train_idx = np.flatnonzero(keep & donors.isin(train_donors).to_numpy())
            val_idx = np.flatnonzero(keep & donors.isin(val_donors).to_numpy())
            if train_idx.size < 2 or val_idx.size < 2:
                continue

            loaded = False
            if args.load_fold_heads_dir:
                fold_cp_path = Path(args.load_fold_heads_dir) / f"fold_checkpoint_repeat_{repeat}_fold_{fold_id}.pt"
                if fold_cp_path.exists():
                    print(f"Loading fold-specific head from {fold_cp_path}")
                    cp = torch.load(fold_cp_path, map_location=device)
                    model, _ = load_jepa(args.checkpoint, device)
                    model.load_state_dict(cp["model_state"])
                    model_args = base_checkpoint.get("args", {})
                    latent_dim = int(model_args.get("latent_dim", 128))
                    head = PathologyRegressor(
                        latent_dim=latent_dim,
                        hidden_dim=args.head_hidden_dim,
                        dropout=args.dropout,
                    ).to(device)
                    head.load_state_dict(cp["head_state"])
                    train_mean = cp["train_mean"]
                    train_std = cp["train_std"]
                    fit_row = cp["fit_row"]
                    loaded = True

            if not loaded:
                model, head, fit_row, train_mean, train_std = train_fold_head(
                    checkpoint_path=args.checkpoint,
                    x=x,
                    donors=donors,
                    y_transformed=y_transformed,
                    train_idx=train_idx,
                    val_idx=val_idx,
                    label_lookup=label_lookup,
                    device=device,
                    epochs=args.epochs,
                    batch_size=args.batch_size,
                    samples_per_epoch=args.samples_per_epoch,
                    lr=args.lr,
                    weight_decay=args.weight_decay,
                    head_hidden_dim=args.head_hidden_dim,
                    dropout=args.dropout,
                    freeze_encoder=args.freeze_encoder,
                    target_transform=args.target_transform,
                )

                if args.save_fold_heads_dir:
                    save_dir = Path(args.save_fold_heads_dir)
                    save_dir.mkdir(parents=True, exist_ok=True)
                    fold_cp_path = save_dir / f"fold_checkpoint_repeat_{repeat}_fold_{fold_id}.pt"
                    print(f"Saving fold-specific head to {fold_cp_path}")
                    torch.save({
                        "model_state": {k: v.cpu().clone() for k, v in model.state_dict().items()},
                        "head_state": {k: v.cpu().clone() for k, v in head.state_dict().items()},
                        "train_mean": train_mean,
                        "train_std": train_std,
                        "fit_row": fit_row
                    }, fold_cp_path)

            print(
                f"Repeat {repeat} fold={fold_id} train_donors={len(train_donors)} val_donors={len(val_donors)} "
                f"best_epoch={fit_row['best_epoch']} val_spearman={fit_row['val_spearman']:.4f}"
            )

            cached_folds[repeat][fold_id] = {
                "model": model,
                "head": head,
                "fit_row": fit_row,
                "train_mean": train_mean,
                "train_std": train_std,
                "val_idx": val_idx,
                "val_donors": val_donors,
            }

    global_means = x_np.mean(axis=0)

    if args.mode == "two-pass":
        print("\n--- Running Pass 1: Module-level Causal Knockout Screen ---")
        module_perturbations = build_perturbation_sets(gene_names, "module", args.modules, args.min_genes)
        print(f"Running {len(module_perturbations)} module-level perturbations...")
        mod_summary, mod_donor, mod_fold = run_knockouts_for_perturbations(
            module_perturbations, cached_folds, x_np, donors, global_means, args, device
        )

        out_path = Path(args.out)
        mod_out = out_path.with_name(out_path.stem + "_modules.csv")
        mod_donor_out = Path(args.donor_out).with_name(Path(args.donor_out).stem + "_modules.csv")
        mod_fold_out = Path(args.fold_out).with_name(Path(args.fold_out).stem + "_modules.csv")
        mod_summary.to_csv(mod_out, index=False)
        mod_donor.to_csv(mod_donor_out, index=False)
        mod_fold.to_csv(mod_fold_out, index=False)
        print(f"Pass 1 complete. Saved module results to {mod_out}")

        top_modules = mod_summary.head(args.top_n_modules)["module"].tolist()
        print(f"\nSelected top {len(top_modules)} modules for targeted gene-level screens: {top_modules}")

        print("\n--- Running Pass 2: Targeted Gene-level Causal Knockout Screen ---")
        gene_perturbations = build_perturbation_sets(gene_names, "gene", top_modules, args.min_genes)
        print(f"Running {len(gene_perturbations)} gene-level perturbations...")
        summary_df, donor_df, fold_df = run_knockouts_for_perturbations(
            gene_perturbations, cached_folds, x_np, donors, global_means, args, device
        )
    else:
        perturbations = build_perturbation_sets(
            gene_names=gene_names,
            mode=args.mode,
            modules=args.modules,
            min_genes=args.min_genes,
        )
        print(f"\nRunning {len(perturbations)} perturbations ({args.mode} mode)...")
        summary_df, donor_df, fold_df = run_knockouts_for_perturbations(
            perturbations, cached_folds, x_np, donors, global_means, args, device
        )

    out_path = Path(args.out)
    donor_out_path = Path(args.donor_out)
    fold_out_path = Path(args.fold_out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    donor_out_path.parent.mkdir(parents=True, exist_ok=True)
    fold_out_path.parent.mkdir(parents=True, exist_ok=True)
    summary_df.to_csv(out_path, index=False)
    donor_df.to_csv(donor_out_path, index=False)
    fold_df.to_csv(fold_out_path, index=False)

    print("\nTop perturbation effects:")
    print(summary_df.head(20).to_string(index=False))
    print(f"\nWrote summary results to {out_path}")
    print(f"Wrote donor results to {donor_out_path}")
    print(f"Wrote fold results to {fold_out_path}")


if __name__ == "__main__":
    main()
