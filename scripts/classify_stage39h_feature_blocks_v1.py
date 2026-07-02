from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FeatureTier:
    feature_block_id: str
    feature_block_name: str
    risk_tier: int
    allowed_for_lock_candidate: bool
    comparator_only: bool
    forbidden: bool
    reason: str
    recommended_use: str


def classify_feature(feature_name: str) -> FeatureTier:
    name = str(feature_name)
    lower = name.lower()
    if name.startswith("latent_module_pca") or name.startswith("module_pca"):
        return FeatureTier("tier0_latent_module", "latent/module features", 0, True, False, False, "Stage 27C/39E internal module representation", "lock_candidate_allowed")
    if name.startswith("metadata_"):
        return FeatureTier("tier1_safe_metadata", "safe pre-pathology metadata", 1, True, False, False, "predeclared donor/technical covariate; not a direct target readout", "lock_candidate_allowed")
    if "pseudoprogression" in lower:
        return FeatureTier("tier4_forbidden_pseudoprogression", "pseudo-progression summaries", 4, False, False, True, "pseudo-pathology/state trajectory feature flagged by Stage 39D", "forbidden")
    if "seaa" in lower:
        return FeatureTier("tier4_forbidden_seaad_state_label", "SEAAD-labeled cell-state composition", 4, False, False, True, "SEAAD cell-state label can encode disease/pathology context", "forbidden")
    if "supertype" in lower:
        return FeatureTier("tier3_cell_state_proxy", "fine supertype composition", 3, False, True, False, "fine cell-state proportions are target-adjacent and proxy-sensitive", "comparator_only")
    if any(token in lower for token in ["subclass", "class", "total_cells", "microglia_pvm_n_cells"]):
        return FeatureTier("tier2_broad_composition", "broad composition/count features", 2, False, False, False, "biologically meaningful but target-adjacent composition", "caution_candidate_only")
    if "brain_region" in lower:
        return FeatureTier("tier1_region_context", "brain-region context", 1, True, False, False, "broad anatomical context; usable if not target-derived", "lock_candidate_allowed")
    if name == "Donor ID":
        return FeatureTier("identifier", "identifier", 4, False, False, True, "identifier is not a predictive feature", "forbidden")
    return FeatureTier("tier4_unknown_provenance", "unknown provenance feature", 4, False, False, True, "unclear provenance under proxy-safe audit", "forbidden")


def block_order(feature_block_id: str) -> int:
    order = {
        "tier0_latent_module": 0,
        "tier1_safe_metadata": 1,
        "tier1_region_context": 2,
        "tier2_broad_composition": 3,
        "tier3_cell_state_proxy": 4,
        "tier4_forbidden_pseudoprogression": 5,
        "tier4_forbidden_seaad_state_label": 6,
        "tier4_unknown_provenance": 7,
        "identifier": 8,
    }
    return order.get(feature_block_id, 99)
