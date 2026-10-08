from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from sea_ad_jepa.gene_sets import MICROGLIA_GENE_MODULES


@dataclass(frozen=True)
class Stage27Inputs:
    folds: pd.DataFrame
    targets: pd.DataFrame
    expression: pd.DataFrame
    module_features: pd.DataFrame
    target_matrix: pd.DataFrame
    module_genes: set[str]


TARGET_ALIAS_TO_NAME = {
    "percent AT8 positive area_Grey matter": "AT8",
    "percent 6e10 positive area_Grey matter": "6e10/AÎ²",
    "percent GFAP positive area_Grey matter": "GFAP",
    "percent Iba1 positive area_Grey matter": "Iba1",
    "percent NeuN positive area_Grey matter": "NeuN",
}


def read_inputs(
    folds_path: Path,
    target_manifest_path: Path,
    metadata_targets_path: Path,
    pseudobulk_path: Path,
) -> Stage27Inputs:
    folds = pd.read_csv(folds_path)
    targets = pd.read_csv(target_manifest_path)
    metadata = pd.read_csv(metadata_targets_path)
    expr = pd.read_csv(pseudobulk_path)
    if "Donor ID" not in expr.columns:
        raise ValueError(f"{pseudobulk_path} lacks Donor ID")
    locked_donors = folds["donor_id"].astype(str).tolist()
    expression = expr.drop_duplicates("Donor ID").set_index("Donor ID")
    expression.index = expression.index.astype(str)
    expression = expression.apply(pd.to_numeric, errors="coerce")
    expression = expression.loc[[d for d in locked_donors if d in expression.index]]
    expression = expression.dropna(axis=1, how="all").fillna(0.0)

    target_aliases = [row["target_alias"] for _, row in targets.iterrows() if bool(row["available"])]
    metadata = metadata.drop_duplicates("Donor ID").set_index("Donor ID")
    metadata.index = metadata.index.astype(str)
    target_matrix = metadata.loc[[d for d in locked_donors if d in metadata.index], target_aliases].apply(pd.to_numeric, errors="coerce")

    shared = [d for d in locked_donors if d in expression.index and d in target_matrix.index]
    expression = expression.loc[shared]
    target_matrix = target_matrix.loc[shared]
    folds = folds[folds["donor_id"].astype(str).isin(shared)].copy()

    module_features, module_genes = build_module_features(expression)
    return Stage27Inputs(
        folds=folds,
        targets=targets,
        expression=expression,
        module_features=module_features,
        target_matrix=target_matrix,
        module_genes=module_genes,
    )


def build_module_features(expression: pd.DataFrame) -> tuple[pd.DataFrame, set[str]]:
    gene_to_col = {str(col).upper(): col for col in expression.columns}
    features: dict[str, pd.Series] = {}
    used_genes: set[str] = set()
    for module_name, genes in MICROGLIA_GENE_MODULES.items():
        cols = [gene_to_col[str(g).upper()] for g in genes if str(g).upper() in gene_to_col]
        if len(cols) >= 2:
            features[f"module_{module_name}"] = expression[cols].mean(axis=1)
            used_genes.update(str(c).upper() for c in cols)
    if not features:
        raise ValueError("No predefined microglia module features overlap expression table")
    return pd.DataFrame(features, index=expression.index), used_genes


def select_residual_columns(
    expression: pd.DataFrame,
    train_donors: list[str],
    module_genes: set[str],
    max_features: int,
) -> list[str]:
    candidate_cols = [col for col in expression.columns if str(col).upper() not in module_genes]
    x_train = expression.loc[train_donors, candidate_cols]
    variances = x_train.var(axis=0).replace([np.inf, -np.inf], np.nan).fillna(0.0)
    variances = variances[variances > 0]
    if variances.empty:
        return candidate_cols[:max_features]
    return list(variances.sort_values(ascending=False).head(max_features).index)

