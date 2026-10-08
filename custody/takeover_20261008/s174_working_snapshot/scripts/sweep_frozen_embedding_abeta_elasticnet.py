from __future__ import annotations

import argparse
import sys
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.linear_model import ElasticNet, Ridge
from sklearn.exceptions import ConvergenceWarning
from sklearn.model_selection import KFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from sea_ad_jepa.data import load_pathology_targets, normalize_donor_id


def spearman_safe(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    if y_true.size < 3 or np.nanstd(y_true) == 0 or np.nanstd(y_pred) == 0:
        return float("nan")
    rho, _ = spearmanr(y_true, y_pred)
    return float(rho)


def parse_float_list(value: str) -> list[float]:
    return [float(item.strip()) for item in value.split(",") if item.strip()]


def parse_int_list(value: str) -> list[int]:
    return [int(item.strip()) for item in value.split(",") if item.strip()]


def load_dataset(args: argparse.Namespace) -> tuple[pd.DataFrame, np.ndarray, np.ndarray, list[str]]:
    embeddings = pd.read_csv(args.embeddings)
    embeddings["Donor ID"] = normalize_donor_id(embeddings["Donor ID"])
    targets, _ = load_pathology_targets(args.targets_path, args.target_columns_path)
    targets["Donor ID"] = normalize_donor_id(targets["Donor ID"])

    z_cols = [col for col in embeddings.columns if col.startswith("z_")]
    if not z_cols:
        raise ValueError(f"No z_* latent columns found in {args.embeddings}")
    if args.target not in targets.columns:
        raise ValueError(f"Target column not found: {args.target}")

    merged = embeddings[["Donor ID", *z_cols]].merge(
        targets[["Donor ID", args.target]],
        on="Donor ID",
        how="inner",
    )
    merged = merged.dropna(subset=[args.target]).reset_index(drop=True)
    if merged.shape[0] < args.n_splits:
        raise ValueError(f"Only {merged.shape[0]} valid donors for {args.n_splits} folds")

    x = merged[z_cols].to_numpy(dtype=np.float32)
    y = merged[args.target].to_numpy(dtype=np.float32)
    return merged, x, y, z_cols


def build_model(model_type: str, alpha: float, l1_ratio: float, max_iter: int, seed: int):
    if model_type == "ridge":
        return make_pipeline(StandardScaler(), Ridge(alpha=alpha))
    if model_type == "elasticnet":
        return make_pipeline(
            StandardScaler(),
            ElasticNet(
                alpha=alpha,
                l1_ratio=l1_ratio,
                max_iter=max_iter,
                random_state=seed,
                selection="cyclic",
            ),
        )
    raise ValueError(f"Unsupported model type: {model_type}")


def cross_validated_predictions(
    x: np.ndarray,
    y: np.ndarray,
    model_type: str,
    alpha: float,
    l1_ratio: float,
    n_splits: int,
    seed: int,
    max_iter: int,
) -> tuple[np.ndarray, list[float]]:
    kfold = KFold(n_splits=n_splits, shuffle=True, random_state=seed)
    oof = np.full(y.shape, np.nan, dtype=np.float32)
    fold_scores: list[float] = []
    for fold, (train_idx, val_idx) in enumerate(kfold.split(x), start=1):
        y_scaler = StandardScaler()
        y_train = y_scaler.fit_transform(y[train_idx].reshape(-1, 1)).ravel()
        model = build_model(model_type, alpha, l1_ratio, max_iter, seed + fold)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", ConvergenceWarning)
            model.fit(x[train_idx], y_train)
        pred_scaled = model.predict(x[val_idx]).astype(np.float32)
        pred = y_scaler.inverse_transform(pred_scaled.reshape(-1, 1)).ravel().astype(np.float32)
        oof[val_idx] = pred
        fold_scores.append(spearman_safe(y[val_idx], pred))
    return oof, fold_scores


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Last conservative A-beta probe: sweep regularized heads on frozen Stage B "
            "donor embeddings only."
        )
    )
    parser.add_argument(
        "--embeddings",
        default="results/tables/pathology_head_stage_b_frozen_donor_embeddings.csv",
        help="Frozen donor-level z embedding table from the Stage B backbone.",
    )
    parser.add_argument("--targets-path", default="data/processed/metadata/sea_ad_mtg_donor_pathology_targets.csv")
    parser.add_argument("--target-columns-path", default="data/processed/metadata/pathology_target_columns.csv")
    parser.add_argument("--target", default="percent 6e10 positive area_Grey matter")
    parser.add_argument("--n-splits", type=int, default=5)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument(
        "--seeds",
        default=None,
        help="Optional comma-separated KFold seeds for stability testing. Defaults to --seed only.",
    )
    parser.add_argument(
        "--ridge-alphas",
        default="0.001,0.003,0.01,0.03,0.1,0.3,1,3,10,30,100,300,1000",
    )
    parser.add_argument(
        "--elasticnet-alphas",
        default="0.0001,0.0003,0.001,0.003,0.01,0.03,0.1,0.3,1,3,10",
    )
    parser.add_argument("--l1-ratios", default="0.05,0.1,0.25,0.5,0.75,0.9,0.95")
    parser.add_argument("--max-iter", type=int, default=20000)
    parser.add_argument("--summary-out", default="results/tables/v2_2_abeta_frozen_embedding_elasticnet_sweep.csv")
    parser.add_argument(
        "--predictions-out",
        default="results/tables/v2_2_abeta_frozen_embedding_elasticnet_oof_predictions.csv",
    )
    args = parser.parse_args()

    merged, x, y, z_cols = load_dataset(args)
    print(f"Loaded {x.shape[0]} valid donors x {x.shape[1]} frozen latent dims")
    print(f"Target: {args.target}")
    seeds = parse_int_list(args.seeds) if args.seeds else [args.seed]
    print(f"CV seeds: {seeds}")

    configs: list[dict[str, float | str]] = []
    for alpha in parse_float_list(args.ridge_alphas):
        configs.append({"model": "ridge", "alpha": alpha, "l1_ratio": 0.0})
    for alpha in parse_float_list(args.elasticnet_alphas):
        for l1_ratio in parse_float_list(args.l1_ratios):
            configs.append({"model": "elasticnet", "alpha": alpha, "l1_ratio": l1_ratio})

    rows = []
    best: dict | None = None
    best_oof: np.ndarray | None = None
    for i, cfg in enumerate(configs, start=1):
        seed_scores = []
        seed_fold_means = []
        seed_fold_stds = []
        representative_oof = None
        for seed in seeds:
            oof, fold_scores = cross_validated_predictions(
                x,
                y,
                str(cfg["model"]),
                float(cfg["alpha"]),
                float(cfg["l1_ratio"]),
                args.n_splits,
                seed,
                args.max_iter,
            )
            seed_scores.append(spearman_safe(y, oof))
            seed_fold_means.append(float(np.nanmean(fold_scores)))
            seed_fold_stds.append(float(np.nanstd(fold_scores)))
            if seed == args.seed:
                representative_oof = oof.copy()
        if representative_oof is None:
            representative_oof = oof.copy()
        oof_spearman = float(np.nanmean(seed_scores))
        row = {
            "rank_order": i,
            "model": cfg["model"],
            "alpha": cfg["alpha"],
            "l1_ratio": cfg["l1_ratio"],
            "mean_oof_spearman": oof_spearman,
            "std_oof_spearman": float(np.nanstd(seed_scores)),
            "min_oof_spearman": float(np.nanmin(seed_scores)),
            "max_oof_spearman": float(np.nanmax(seed_scores)),
            "representative_seed_oof_spearman": spearman_safe(y, representative_oof),
            "fold_spearman_mean": float(np.nanmean(seed_fold_means)),
            "fold_spearman_std": float(np.nanmean(seed_fold_stds)),
            "n_donors": int(x.shape[0]),
            "n_latent_dims": int(len(z_cols)),
            "n_splits": args.n_splits,
            "seeds": ",".join(str(seed) for seed in seeds),
            "representative_seed": args.seed,
            "target": args.target,
        }
        rows.append(row)
        if best is None or np.nan_to_num(oof_spearman, nan=-np.inf) > np.nan_to_num(best["mean_oof_spearman"], nan=-np.inf):
            best = row
            best_oof = representative_oof.copy()

    summary = pd.DataFrame(rows).sort_values("mean_oof_spearman", ascending=False).reset_index(drop=True)
    summary.insert(0, "rank", np.arange(1, len(summary) + 1))
    Path(args.summary_out).parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(args.summary_out, index=False)

    if best is None or best_oof is None:
        raise RuntimeError("No sweep configuration produced predictions")

    pred_df = pd.DataFrame(
        {
            "Donor ID": merged["Donor ID"],
            "target": args.target,
            "y_true": y,
            "y_pred": best_oof,
            "best_model": best["model"],
            "best_alpha": best["alpha"],
            "best_l1_ratio": best["l1_ratio"],
            "best_mean_oof_spearman": best["mean_oof_spearman"],
            "best_representative_seed_oof_spearman": best["representative_seed_oof_spearman"],
            "representative_seed": args.seed,
        }
    )
    Path(args.predictions_out).parent.mkdir(parents=True, exist_ok=True)
    pred_df.to_csv(args.predictions_out, index=False)

    print("\nTop frozen-embedding A-beta probes:")
    print(summary.head(10).to_string(index=False))
    print(f"\nWrote sweep summary: {args.summary_out}")
    print(f"Wrote best OOF predictions: {args.predictions_out}")


if __name__ == "__main__":
    main()
