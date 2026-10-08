from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import os
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy.stats import spearmanr


def r2_score(truth: np.ndarray, pred: np.ndarray) -> float:
    ss_res = float(np.sum((truth - pred) ** 2))
    ss_tot = float(np.sum((truth - truth.mean()) ** 2))
    return 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")


def main() -> None:
    # Colors and aesthetics
    plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
    
    oof_path = Path("results/tables/multitarget_stratified_groupkfold_oof_log1p_ridge.csv")
    if not oof_path.exists():
        raise FileNotFoundError(f"Required OOF predictions file not found: {oof_path}")
        
    df = pd.read_csv(oof_path)
    
    # Selected targets
    targets = {
        "percent AT8 positive area_Grey matter": "percent AT8 positive area_Grey matter",
        "percent NeuN positive area_Grey matter": "percent NeuN positive area_Grey matter"
    }
    
    # Models to plot
    models = {
        "pseudobulk": "Pseudobulk Ridge Baseline",
        "jepa_ema_var_e30": "Pathology-Aware EMA+Variance JEPA"
    }
    
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    fig.suptitle("Out-of-Fold Cross-Validation Performance Comparison\nRaw Biological Scale (Percentage Area)", fontsize=16, fontweight="bold", y=0.98)
    
    target_names = list(targets.keys())
    model_keys = list(models.keys())
    
    # Professional color palette
    colors = {
        "pseudobulk": "#ff7f0e",  # Orange
        "jepa_ema_var_e30": "#1f77b4"  # Blue
    }
    
    for row_idx, target in enumerate(target_names):
        target_display = "AT8 Pathology (% Area)" if "AT8" in target else "NeuN Density (% Area)"
        for col_idx, model in enumerate(model_keys):
            ax = axes[row_idx, col_idx]
            
            # Filter data
            subset = df[(df["model"] == model) & (df["target"] == target)].copy()
            if subset.empty:
                ax.text(0.5, 0.5, f"Data missing for {model}\n{target}", ha="center", va="center")
                continue
                
            truth = subset["truth"].to_numpy()
            pred = subset["prediction"].to_numpy()
            
            # Clip predictions to 0 as biological area cannot be negative
            pred_clipped = np.clip(pred, 0, None)
            
            # Get target transform and compute model scale R^2
            target_transform = subset["target_transform"].iloc[0] if "target_transform" in subset.columns else "log1p"
            if target_transform == "log1p":
                truth_model = np.log1p(np.clip(truth, 0, None))
                pred_model = subset["prediction_model_scale"].to_numpy()
            else:
                truth_model = truth
                pred_model = subset["prediction_model_scale"].to_numpy() if "prediction_model_scale" in subset.columns else pred_clipped
                
            # Compute metrics
            rho, p_val = spearmanr(truth, pred_clipped)
            r2 = r2_score(truth_model, pred_model)
            
            # Plot scatter with regplot (which adds confidence intervals)
            sns.regplot(
                x=truth,
                y=pred_clipped,
                ax=ax,
                color=colors[model],
                scatter_kws={"alpha": 0.6, "s": 40},
                line_kws={"color": "#2ca02c", "linestyle": "-", "linewidth": 2, "label": "Linear Fit"},
            )
            
            # Identity line (y = x)
            max_val = max(truth.max(), pred_clipped.max())
            ax.plot([0, max_val], [0, max_val], color="gray", linestyle="--", alpha=0.5, label="Identity Line (y=x)")
            
            ax.set_title(f"{models[model]}\n{target_display}", fontsize=12, fontweight="semibold")
            ax.set_xlabel("True Pathology", fontsize=10)
            ax.set_ylabel("Predicted Pathology", fontsize=10)
            
            # Text box for metrics
            metric_text = f"Spearman $\\rho$: {rho:.3f}\n$R^2$ (model scale): {r2:.3f}"
            ax.text(0.05, 0.95, metric_text, transform=ax.transAxes, fontsize=10,
                    verticalalignment="top", bbox=dict(boxstyle="round", facecolor="white", alpha=0.8, edgecolor="0.8"))
            
            ax.legend(loc="lower right", fontsize=8)
            ax.set_xlim(0, max_val * 1.05)
            ax.set_ylim(0, max_val * 1.05)
            
    plt.tight_layout()
    
    figures_dir = Path("results/figures")
    figures_dir.mkdir(parents=True, exist_ok=True)
    out_path = figures_dir / "validation_comparison_summary.png"
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    print(f"Successfully generated and saved comparison plot to: {out_path}")
    
    # Save individual plots just in case
    for target in target_names:
        target_display = "AT8" if "AT8" in target else "NeuN"
        fig_ind, axes_ind = plt.subplots(1, 2, figsize=(12, 5))
        fig_ind.suptitle(f"Cross-Validation Comparison - {target_display} Pathology", fontsize=14, fontweight="bold")
        for col_idx, model in enumerate(model_keys):
            ax = axes_ind[col_idx]
            subset = df[(df["model"] == model) & (df["target"] == target)]
            if subset.empty:
                continue
            truth = subset["truth"].to_numpy()
            pred = subset["prediction"].to_numpy()
            pred_clipped = np.clip(pred, 0, None)
            
            target_transform = subset["target_transform"].iloc[0] if "target_transform" in subset.columns else "log1p"
            if target_transform == "log1p":
                truth_model = np.log1p(np.clip(truth, 0, None))
                pred_model = subset["prediction_model_scale"].to_numpy()
            else:
                truth_model = truth
                pred_model = subset["prediction_model_scale"].to_numpy() if "prediction_model_scale" in subset.columns else pred_clipped
                
            rho, _ = spearmanr(truth, pred_clipped)
            r2 = r2_score(truth_model, pred_model)
            
            sns.regplot(
                x=truth,
                y=pred_clipped,
                ax=ax,
                color=colors[model],
                scatter_kws={"alpha": 0.6, "s": 50},
                line_kws={"color": "#2ca02c", "linestyle": "-", "linewidth": 2},
            )
            max_val = max(truth.max(), pred_clipped.max())
            ax.plot([0, max_val], [0, max_val], color="gray", linestyle="--", alpha=0.5)
            ax.set_title(f"{models[model]} ($\\rho$ = {rho:.3f}, $R^2$ = {r2:.3f})")
            ax.set_xlabel("True Pathology")
            ax.set_ylabel("Predicted")
            ax.set_xlim(0, max_val * 1.05)
            ax.set_ylim(0, max_val * 1.05)
            
        plt.tight_layout()
        ind_path = figures_dir / f"validation_comparison_{target_display}.png"
        plt.savefig(ind_path, dpi=300, bbox_inches="tight")
        print(f"Saved: {ind_path}")
        plt.close(fig_ind)
        
    plt.close(fig)


if __name__ == "__main__":
    main()
