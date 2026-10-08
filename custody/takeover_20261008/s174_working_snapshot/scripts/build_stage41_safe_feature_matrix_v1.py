from __future__ import annotations

import pandas as pd


NEW_SAFE_FEATURE_CLASSES = {
    "image_or_tile_feature_candidate",
    "morphology_feature_candidate",
    "spatial_or_neighborhood_candidate",
    "slide_or_section_candidate",
    "region_anatomy_candidate",
}


def build_safe_feature_matrix_manifest(source_inventory: pd.DataFrame, risk_tiers: pd.DataFrame) -> pd.DataFrame:
    if source_inventory.empty or risk_tiers.empty:
        return pd.DataFrame(
            [
                {
                    "safe_feature_matrix_built": False,
                    "reason": "no candidate source inventory available",
                    "n_candidate_sources": 0,
                    "n_new_safe_multimodal_sources": 0,
                    "matrix_path": "",
                    "training_allowed": False,
                }
            ]
        )
    merged = source_inventory.merge(risk_tiers[["source_path", "risk_tier", "allowed_for_benchmark_candidate", "forbidden"]], on="source_path", how="left")
    candidates = merged[
        merged["feature_class_guess"].isin(NEW_SAFE_FEATURE_CLASSES)
        & merged["likely_donor_linked"].astype(bool)
        & merged["allowed_for_benchmark_candidate"].astype(bool)
        & ~merged["forbidden"].astype(bool)
        & merged["extension"].isin([".csv", ".tsv", ".parquet", ".feather"])
    ]
    return pd.DataFrame(
        [
            {
                "safe_feature_matrix_built": False,
                "reason": "new donor-linked safe multimodal/spatial/image feature table not found" if candidates.empty else "candidate tables require manual schema review before matrix build",
                "n_candidate_sources": int(len(merged)),
                "n_new_safe_multimodal_sources": int(len(candidates)),
                "candidate_source_paths": ";".join(candidates["source_path"].astype(str).tolist()),
                "matrix_path": "",
                "training_allowed": False,
            }
        ]
    )
