from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Stage41Risk:
    risk_tier: int
    allowed_for_benchmark_candidate: bool
    comparator_only: bool
    forbidden: bool
    reason: str
    recommended_use: str


def classify_source(feature_class: str, source_path: str, donor_linked: bool) -> Stage41Risk:
    feature = str(feature_class).lower()
    path = str(source_path).lower()
    if any(k in path for k in ["stage27c", "stage39e", "module_pca", "latent"]):
        return Stage41Risk(0, True, False, False, "safe internal module/latent reference", "reference_or_lock_candidate_baseline")
    if any(k in feature for k in ["region", "anatomy", "covariate"]) and donor_linked:
        return Stage41Risk(1, True, False, False, "safe pre-pathology metadata/context candidate if provenance is confirmed", "manual_review_then_candidate")
    if any(k in feature for k in ["composition", "density", "neighborhood"]):
        return Stage41Risk(2, False, False, False, "biologically meaningful but target-adjacent feature class", "caution_candidate_after_proxy_audit")
    if any(k in feature for k in ["image", "morphology", "slide", "section", "spatial"]):
        return Stage41Risk(2, False, False, False, "potentially valuable multimodal feature class but needs provenance/donor linkage audit", "priority_manual_acquisition")
    if "pathology" in feature or "pathology" in path:
        return Stage41Risk(3, False, True, False, "pathology-named file may encode target burden directly", "comparator_or_manual_review_only")
    if any(k in path for k in ["pseudo", "seaa", "target", "label_change"]):
        return Stage41Risk(4, False, False, True, "possible target-derived or disease-state proxy feature", "forbidden_for_training")
    if not donor_linked:
        return Stage41Risk(4, False, False, True, "not clearly donor-linked or provenance unclear", "missing_or_manual_review")
    return Stage41Risk(4, False, False, True, "unclear provenance", "missing_or_manual_review")
