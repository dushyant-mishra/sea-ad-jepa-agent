from __future__ import annotations

import math

import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


def safe_corr(y_true: np.ndarray, y_pred: np.ndarray, method: str = "spearman") -> float:
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    ok = np.isfinite(y_true) & np.isfinite(y_pred)
    y_true = y_true[ok]
    y_pred = y_pred[ok]
    if len(y_true) < 3 or np.nanstd(y_true) == 0 or np.nanstd(y_pred) == 0:
        return 0.0
    try:
        value = pearsonr(y_true, y_pred).statistic if method == "pearson" else spearmanr(y_true, y_pred).statistic
        return 0.0 if pd.isna(value) else float(value)
    except Exception:
        return 0.0


def regression_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    ok = np.isfinite(y_true) & np.isfinite(y_pred)
    y_true = y_true[ok]
    y_pred = y_pred[ok]
    return {
        "pooled_oof_spearman": safe_corr(y_true, y_pred, "spearman"),
        "pooled_oof_pearson": safe_corr(y_true, y_pred, "pearson"),
        "r2": float(r2_score(y_true, y_pred)) if len(y_true) >= 2 else float("nan"),
        "mae": float(mean_absolute_error(y_true, y_pred)) if len(y_true) else float("nan"),
        "rmse": float(math.sqrt(mean_squared_error(y_true, y_pred))) if len(y_true) else float("nan"),
    }


def donor_bootstrap_ci(
    predictions: pd.DataFrame,
    group_cols: list[str],
    target_col: str = "y_true",
    pred_col: str = "y_pred",
    n_resamples: int = 500,
    seed: int = 7,
) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows = []
    for keys, group in predictions.groupby(group_cols, dropna=False):
        if not isinstance(keys, tuple):
            keys = (keys,)
        donors = group["donor_id"].astype(str).to_numpy()
        unique_donors = np.unique(donors)
        values = []
        for _ in range(n_resamples):
            sampled = rng.choice(unique_donors, size=len(unique_donors), replace=True)
            sampled_rows = pd.concat([group[group["donor_id"].astype(str) == donor] for donor in sampled], ignore_index=True)
            values.append(safe_corr(sampled_rows[target_col].to_numpy(), sampled_rows[pred_col].to_numpy(), "spearman"))
        arr = np.asarray(values, dtype=float)
        row = {col: key for col, key in zip(group_cols, keys)}
        row.update(
            {
                "n_bootstrap_resamples": int(n_resamples),
                "spearman_ci_low": float(np.nanpercentile(arr, 2.5)),
                "spearman_ci_median": float(np.nanpercentile(arr, 50.0)),
                "spearman_ci_high": float(np.nanpercentile(arr, 97.5)),
                "uncertainty_status": "complete",
            }
        )
        rows.append(row)
    return pd.DataFrame(rows)

