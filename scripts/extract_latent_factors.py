from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import argparse
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.model_selection import StratifiedGroupKFold

from sea_ad_jepa.data import load_pathology_targets, normalize_donor_id
from sea_ad_jepa.evaluation_utils import transform_target, make_strata


def extract_weights_for_target(
    merged_df: pd.DataFrame,
    target_col: str,
    feature_cols: list[str],
    alpha: float = 10.0,
    n_splits: int = 5,
    target_bins: int = 5
) -> tuple[pd.DataFrame, pd.DataFrame]:
    # Filter for rows with finite targets
    data = merged_df.dropna(subset=[target_col]).reset_index(drop=True)
    
    X = data[feature_cols].to_numpy(dtype=np.float32)
    y = transform_target(data[target_col].to_numpy(dtype=np.float32), "log1p")
    groups = data["Donor ID"].to_numpy()
    
    # Stratified split setup
    y_strata = make_strata(data[target_col].to_numpy(dtype=np.float32), target_bins)
    splitter = StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=7)
    
    fold_coefs = []
    
    for fold_id, (train_idx, val_idx) in enumerate(splitter.split(data, y_strata, groups=groups), start=1):
        X_train, y_train = X[train_idx], y[train_idx]
        
        # Standardize features (Ridge regression works best when features are standardized)
        mean = X_train.mean(axis=0, keepdims=True)
        std = X_train.std(axis=0, keepdims=True)
        std[std == 0] = 1.0
        X_train_scaled = (X_train - mean) / std
        
        # Fit Ridge regression
        model = Ridge(alpha=alpha, fit_intercept=True)
        model.fit(X_train_scaled, y_train)
        
        fold_coefs.append(model.coef_)
        
    fold_coefs = np.array(fold_coefs)  # Shape: (5, 128)
    
    # Calculate statistics
    mean_coef = fold_coefs.mean(axis=0)
    std_coef = fold_coefs.std(axis=0)
    mean_abs_coef = np.abs(fold_coefs).mean(axis=0)
    
    coef_df = pd.DataFrame({
        "latent_dimension": feature_cols,
        "mean_coefficient": mean_coef,
        "std_coefficient": std_coef,
        "mean_abs_coefficient": mean_abs_coef
    })
    
    # Add fold-specific coefficients
    for fold_idx in range(n_splits):
        coef_df[f"fold_{fold_idx+1}_coef"] = fold_coefs[fold_idx]
        
    coef_df = coef_df.sort_values("mean_abs_coefficient", ascending=False).reset_index(drop=True)
    
    return coef_df, fold_coefs


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract donor-held-out pathology weights for JEPA latent factors.")
    parser.add_argument("--embeddings", default="results/tables/microglia_pvm_jepa_ema_var_expanded_balanced_e30_donor_embeddings.csv")
    parser.add_argument("--out", default="results/tables/pathology_latent_weights.csv")
    parser.add_argument("--targets", nargs="+", default=["percent AT8 positive area_Grey matter", "percent NeuN positive area_Grey matter"])
    parser.add_argument("--alpha", type=float, default=10.0)
    parser.add_argument("--n-splits", type=int, default=5)
    args = parser.parse_args()

    embeddings_path = Path(args.embeddings)
    if not embeddings_path.exists():
        raise FileNotFoundError(f"Required embeddings file not found: {embeddings_path}")
        
    # Load targets and embeddings
    targets, _ = load_pathology_targets()
    targets["Donor ID"] = normalize_donor_id(targets["Donor ID"])
    
    embeddings = pd.read_csv(embeddings_path)
    embeddings["Donor ID"] = normalize_donor_id(embeddings["Donor ID"])
    
    merged = embeddings.merge(targets, on="Donor ID", how="inner")
    
    feature_columns = [col for col in embeddings.columns if col.startswith("z_") or col.startswith("jepa_")]
    if not feature_columns:
        feature_columns = [col for col in embeddings.columns if col != "Donor ID"]
    
    print(f"Loaded {merged.shape[0]} donors with embeddings and pathology targets.")
    
    results = {}
    
    all_coefs_list = []
    
    for target in args.targets:
        print(f"\nExtracting latent factor weights for: {target}")
        coef_df, _ = extract_weights_for_target(
            merged,
            target,
            feature_columns,
            alpha=args.alpha,
            n_splits=args.n_splits,
        )
        
        print("Top 5 Latent Factors by Mean Absolute Coefficient:")
        print(coef_df.head(5)[["latent_dimension", "mean_coefficient", "mean_abs_coefficient"]].to_string(index=False))
        
        coef_df.insert(0, "target", target)
        all_coefs_list.append(coef_df)
        
    combined_coef_df = pd.concat(all_coefs_list, ignore_index=True)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    combined_coef_df.to_csv(out_path, index=False)
    print(f"\nWrote combined latent factor weights to {out_path}")


if __name__ == "__main__":
    main()
