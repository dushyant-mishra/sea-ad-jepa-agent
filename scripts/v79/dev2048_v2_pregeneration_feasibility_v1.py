#!/usr/bin/env python3
"""DEV2048 v2 pre-generation *design* audit; no synthetic world or learner.

No import of historical biology/observation modules, NumPy, Torch or real RNA.
Accepts only exact frozen source identities and prospective integer metadata.
Refuses to mark unreviewed biologically inconsistent role allocations ready.
"""
from __future__ import annotations

import argparse
from hashlib import sha1
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PINNED_SOURCE_BLOBS = {
    "scripts/v79/unified_synthetic_integration_v1.py": "f7801c709db66c7c1feb5ef6b84327d6d46ec0df",
    "scripts/v79/unified_synthetic_fit_view_v1.py": "5a5fdd2862dc558683231ed4ef7946efc30c62f1",
    "scripts/v79/expanded_common_world_development_v1.py": "8763f3743db90698fd1bef79bd0810eeecac1052"
}
N_GENES = 2048
SUPPORT_PERIOD = 37
SOURCE_OFFSETS = (0, 5, 11)
VIEW_SIZE = 512
N_VIEWS = 3
N_QUERIES_V2_PROPOSED = 8
PANEL_SIZE = 8
GENES_PER_RARE_PROGRAM = 15
N_RARE_PROGRAMS = 4
N_PERTURB_RESPONSE_GENES = 15
RARE_VIEW_QUOTA_PER_PROGRAM = (4, 4, 4)
RARE_TAIL_QUOTA_PER_PROGRAM = 3
MIN_SAME_PROGRAM_OTHER_PER_POSITIVE_QUERY = 3
POSITIVE_RARE_QUERIES = 4
POSITIVE_PERTURB_QUERIES = 2
NULL_QUERIES = 2

def git_blob(raw: bytes) -> str:
    return sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()

def verify_original_sources(root: Path = ROOT) -> None:
    for path, expected in PINNED_SOURCE_BLOBS.items():
        if git_blob((root / path).read_bytes()) != expected:
            raise ValueError("frozen source changed: " + path)

def support_only_roles() -> dict[str, object]:
    """Metadata-only common-address layout; no rare cell activity generated."""
    common = [
        g for g in range(N_GENES)
        if all((g + offset) % SUPPORT_PERIOD != 0 for offset in SOURCE_OFFSETS)
    ]
    needed = N_VIEWS * VIEW_SIZE + N_QUERIES_V2_PROPOSED * (1 + PANEL_SIZE)
    if len(common) < needed:
        raise ValueError("not enough common structural addresses")
    views = [common[i * VIEW_SIZE:(i + 1) * VIEW_SIZE] for i in range(N_VIEWS)]
    tail = common[N_VIEWS * VIEW_SIZE:]
    queries = tail[:N_QUERIES_V2_PROPOSED]
    panels = [
        tail[N_QUERIES_V2_PROPOSED + i * PANEL_SIZE:
             N_QUERIES_V2_PROPOSED + (i + 1) * PANEL_SIZE]
        for i in range(N_QUERIES_V2_PROPOSED)
    ]
    address_order = [*sum(views, []), *queries, *sum(panels, [])]
    if len(address_order) != len(set(address_order)):
        raise ValueError("view/query/panel addresses overlap")
    return {
        "views": views, "queries": queries, "panels": panels,
        "common_measured_addresses": len(common),
        "reserved_addresses": needed,
    }

def min_gene_members_for_distinct_panels(
    n_views: int,
    per_view: int,
    positive_queries_of_same_program: int,
    other_per_positive_query: int,
) -> int:
    """Lower bound assuming program q and panel members cannot be reused."""
    if min(n_views, per_view, positive_queries_of_same_program,
           other_per_positive_query) < 0:
        raise ValueError("negative quota")
    return n_views * per_view + positive_queries_of_same_program * (1 + other_per_positive_query)

def structural_findings() -> dict[str, object]:
    roles = support_only_roles()
    # Actual PR328 mechanism: rare regime 0 and perturbation response
    # act upon the SAME original 15 addresses, not two independent blocks.
    minimum_1q = min_gene_members_for_distinct_panels(3, 4, 1, 3)
    minimum_overlap = min_gene_members_for_distinct_panels(3, 4, 3, 3)
    nominal_tail = RARE_TAIL_QUOTA_PER_PROGRAM
    verdict = {
        "schema": "DEV2048_V2_PREGENERATION_SOURCE_AND_LAYOUT_AUDIT_V1",
        "scope": "METADATA_AND_PINNED_SOURCE_ONLY",
        "reference_pr": 547,
        "old_fixture_untouched": True,
        "original_rare_program_count": N_RARE_PROGRAMS,
        "rare_program_genes": GENES_PER_RARE_PROGRAM,
        "perturbation_response_genes": N_PERTURB_RESPONSE_GENES,
        "perturbation_overlaps_original_rare_regime_zero": True,
        "proposed_queries": {
            "rare": POSITIVE_RARE_QUERIES,
            "perturb": POSITIVE_PERTURB_QUERIES,
            "null": NULL_QUERIES,
            "total": N_QUERIES_V2_PROPOSED,
        },
        "support_and_role_placement": {
            "common_measured": roles["common_measured_addresses"],
            "reserved_distinct": roles["reserved_addresses"],
            "three_disjoint_512_views_feasible": True,
            "eight_queries_eight_distinct_other_panels_feasible": True,
            "gene_program_incidences_proved": False,
        },
        "design_contradictions": {
            "rare_one_query_min_gene_members_if_4_per_view": minimum_1q,
            "gene_members_available_per_rare_program": GENES_PER_RARE_PROGRAM,
            "original_3_tail_gene_quota_can_support_q_plus_three_other":
                nominal_tail >= 1 + MIN_SAME_PROGRAM_OTHER_PER_POSITIVE_QUERY,
            "rare0_and_perturb_three_query_min_gene_members_if_disjoint_panels":
                minimum_overlap,
            "perturbation_response_is_separate_from_rare0": False,
            "four_per_view_and_three_disjoint_positive_panels_fit_15": minimum_overlap <= 15,
        },
        "available_design_choices_for_independent_review": [
            "Use prospectively reviewed cross-query panel reuse, with all query genes excluded from all panels; recompute source/donor confounds and preserve original perturb overlap.",
            "Or explicitly version a changed perturbation mechanism and larger gene program, with new independent scientific review; do not call this PR328-unchanged.",
        ],
        "biological_realism_requirements": [
            "real train-only per-source/operator measured depth and detected gene distributions",
            "measured zeros distinct from structural absence/collision/rights withholding",
            "per-gene mean and detection, count-tail and dispersion",
            "signed correlation, conditional covariance, T1-T5 topology, eigenspectrum",
            "broad-class prevalence and within-class plus donor-by-class variation",
            "rare and perturb known-truth observability across all views and q panels",
            "source-stratified and donor-held-out controls, matched null and wrong query",
            "source/issuer and actual parameter-to-operator binding"
        ],
        "historical_reference_versions_reused": ["V74", "V77", "S174", "V78", "V79", "V80", "PS_Task3_493", "PR531"],
        "prospective_controls": {
            "predefine_mechanistic_arms_and_finite_iteration_limit": True,
            "heldout_data_must_not_control_retuning": True,
            "all_realism_metrics_must_be_jointly_assessed": True,
            "retain_known_synthetic_truth_without_real_program_copy": True,
        },
        "v2_source_approved": False,
        "world_generated": False,
        "world_qualified": False,
        "realism_qualified": False,
        "model_trained": False,
        "status": "DESIGN_CONTRADICTION__FREEZE_REALISM_CRITERIA_BEFORE_ANY_REALIZATION",
    }
    if minimum_1q <= GENES_PER_RARE_PROGRAM or nominal_tail >= 4:
        raise AssertionError("old proposal contradiction no longer holds")
    if minimum_overlap <= GENES_PER_RARE_PROGRAM:
        raise AssertionError("rare/perturb overlap capacity unexpectedly changed")
    return verdict

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    verify_original_sources(args.root)
    print(json.dumps(structural_findings(), sort_keys=True, indent=2))

if __name__ == "__main__":
    main()
