from __future__ import annotations

from pathlib import Path

import pandas as pd


DEFAULT_TARGETS_PATH = Path("data/processed/metadata/sea_ad_mtg_donor_pathology_targets.csv")
DEFAULT_TARGET_COLUMNS_PATH = Path("data/processed/metadata/pathology_target_columns.csv")


def load_pathology_targets(
    targets_path: str | Path = DEFAULT_TARGETS_PATH,
    target_columns_path: str | Path = DEFAULT_TARGET_COLUMNS_PATH,
) -> tuple[pd.DataFrame, list[str]]:
    """Load joined donor metadata/pathology targets and selected numeric target columns."""
    targets = pd.read_csv(targets_path)
    target_columns = pd.read_csv(target_columns_path)["target_column"].tolist()
    return targets, target_columns


def normalize_donor_id(series: pd.Series) -> pd.Series:
    """Normalize donor identifiers for safe joins across SEA-AD metadata tables."""
    return series.astype(str).str.strip()

