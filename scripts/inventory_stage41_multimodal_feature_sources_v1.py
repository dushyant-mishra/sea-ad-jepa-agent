from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd


def infer_feature_class(path: Path) -> str:
    text = str(path).lower()
    if any(k in text for k in ["image", "tile", "patch"]):
        return "image_or_tile_feature_candidate"
    if any(k in text for k in ["morphology", "morph"]):
        return "morphology_feature_candidate"
    if "spatial" in text or "neighborhood" in text:
        return "spatial_or_neighborhood_candidate"
    if "slide" in text or "section" in text:
        return "slide_or_section_candidate"
    if "region" in text or "anatomy" in text:
        return "region_anatomy_candidate"
    if "density" in text:
        return "density_candidate"
    if "composition" in text:
        return "composition_candidate"
    if "covariate" in text:
        return "covariate_candidate"
    if "pathology" in text:
        return "pathology_named_candidate"
    if "embedding" in text:
        return "embedding_candidate"
    return "keyword_candidate"


def likely_donor_linked(path: Path) -> bool:
    name = path.name.lower()
    text = str(path).lower()
    return any(k in name or k in text for k in ["donor", "metadata", "targets", "stage39", "stage40"])


def inventory_sources(root: Path, include_roots: Iterable[str], keywords: Iterable[str]) -> pd.DataFrame:
    rows = []
    lower_keywords = [k.lower() for k in keywords]
    for rel_root in include_roots:
        base = root / rel_root
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if not path.is_file():
                continue
            rel = path.relative_to(root)
            text = str(rel).lower()
            matched = [k for k in lower_keywords if k in text]
            if not matched:
                continue
            rows.append(
                {
                    "source_path": str(rel),
                    "file_name": path.name,
                    "feature_class_guess": infer_feature_class(rel),
                    "matched_keywords": ";".join(matched),
                    "size_bytes": path.stat().st_size,
                    "extension": path.suffix.lower(),
                    "likely_donor_linked": likely_donor_linked(rel),
                    "internal_or_external_guess": "external_or_public" if any(k in text for k in ["gse", "cellxgene", "external", "grubman"]) else "internal_or_project",
                    "stage41_candidate_status": "candidate_for_manual_review",
                }
            )
    return pd.DataFrame(rows).sort_values(["feature_class_guess", "source_path"]) if rows else pd.DataFrame(columns=["source_path", "file_name", "feature_class_guess", "matched_keywords", "size_bytes", "extension", "likely_donor_linked", "internal_or_external_guess", "stage41_candidate_status"])
