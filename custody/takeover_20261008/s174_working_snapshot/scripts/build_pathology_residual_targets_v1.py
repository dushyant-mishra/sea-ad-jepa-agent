from __future__ import annotations

from statistics import NormalDist
from typing import Any

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import RidgeCV
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


def as_float_array(values: Any) -> np.ndarray:
    return pd.Series(values).astype(float).to_numpy()


def winsor_bounds(values: np.ndarray, lower_q: float = 0.05, upper_q: float = 0.95) -> tuple[float, float]:
    clean = values[np.isfinite(values)]
    if clean.size == 0:
        return 0.0, 0.0
    return float(np.quantile(clean, lower_q)), float(np.quantile(clean, upper_q))


def rank_inverse_normal_train(values: np.ndarray) -> tuple[np.ndarray, dict[float, float]]:
    series = pd.Series(values)
    ranks = series.rank(method="average").to_numpy(dtype=float)
    n = int(np.isfinite(ranks).sum())
    nd = NormalDist()
    transformed = np.asarray([nd.inv_cdf((r - 0.5) / n) if np.isfinite(r) and n > 0 else np.nan for r in ranks])
    mapping = {float(v): float(t) for v, t in zip(values, transformed) if np.isfinite(v) and np.isfinite(t)}
    return transformed, mapping


def rank_inverse_normal_apply(values: np.ndarray, train_values: np.ndarray) -> np.ndarray:
    train_sorted = np.sort(train_values[np.isfinite(train_values)])
    n = len(train_sorted)
    nd = NormalDist()
    out = []
    for value in values:
        if not np.isfinite(value) or n == 0:
            out.append(np.nan)
            continue
        rank = np.searchsorted(train_sorted, value, side="right")
        p = min(max((rank + 0.5) / (n + 1), 1e-4), 1 - 1e-4)
        out.append(nd.inv_cdf(p))
    return np.asarray(out, dtype=float)


def build_covariate_preprocessor(numeric_cols: list[str], categorical_cols: list[str]) -> ColumnTransformer:
    numeric = Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler())])
    categorical = Pipeline(
        [
            ("impute", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ]
    )
    return ColumnTransformer(
        [
            ("numeric", numeric, numeric_cols),
            ("categorical", categorical, categorical_cols),
        ],
        remainder="drop",
    )


def fit_covariate_residualizer(
    covariates: pd.DataFrame,
    train_donors: list[str],
    y_train_log: np.ndarray,
    numeric_cols: list[str],
    categorical_cols: list[str],
    alphas: list[float],
) -> Pipeline:
    pre = build_covariate_preprocessor(numeric_cols, categorical_cols)
    model = RidgeCV(alphas=np.asarray(alphas, dtype=float), cv=min(3, max(2, len(train_donors) // 10)))
    pipe = Pipeline([("preprocess", pre), ("model", model)])
    pipe.fit(covariates.loc[train_donors, numeric_cols + categorical_cols], y_train_log)
    return pipe
