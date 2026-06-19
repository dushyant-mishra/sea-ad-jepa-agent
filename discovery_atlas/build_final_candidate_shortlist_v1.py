from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


PRIOR_CANDIDATES = [
    "TLR2",
    "APP",
    "APOE",
    "CD4",
    "P2RY12",
    "BCL2",
    "MAPK1",
    "CX3CR1",
    "STAT3",
    "CSF1R",
    "UGCG",
    "ROCK1",
    "CTSD",
    "P2RY13",
    "PLCG2",
    "TREM2",
    "TYROBP",
    "C1QA",
    "C1QB",
    "C1QC",
    "C3",
    "CD74",
    "HLA-DRA",
    "SPP1",
]

NAMED_AUDIT_GENES = [
    "RC3H1",
    "PAFAH1B1",
    "DLG1",
    "FIP1L1",
    "SLAIN2",
    "PTPN18",
    "KIF2A",
    "ERC1",
    "GSK3B",
    "TLR2",
    "APP",
    "APOE",
    "CD4",
]

TARGETED_PRIOR_ANCHORS = [
    "TLR2",
    "APP",
    "APOE",
    "CD4",
    "CTSD",
    "TREM2",
    "CSF1R",
    "PLCG2",
    "C3",
    "C1QA",
    "TYROBP",
]

TARGETED_BROAD_STATE_CONTROLS = [
    "RC3H1",
    "DLG1",
    "PAFAH1B1",
    "HDAC8",
    "SMG1",
    "POLK",
    "HECTD1",
    "APP",
    "APOE",
]

TARGETED_SPECIAL_REVIEW = [
    "GSK3B",
    "SLAIN2",
    "FIP1L1",
    "ERC1",
    "KIF2A",
    "PTPN18",
    "UGCG",
    "CD74",
    "MSR1",
    "PLD3",
    "SLC38A9",
    "AP1G1",
]

HIGH_SCORE_DEPRIORITIZED_AUDIT = [
    "GSK3B",
    "ABL1",
    "PTPN18",
    "SLAIN2",
    "FIP1L1",
    "ERC1",
    "KIF2A",
    "PAFAH1B1",
]

CLEANER_CLASSES = {
    "tau_lowering_neuron_preserving",
    "dual_pathology_lowering_neuron_preserving",
}

KNOWN_BIOLOGY = {
    "TLR2": "Innate immune pattern-recognition receptor previously prioritized by the project.",
    "APP": "Amyloid precursor protein; direct Alzheimer-related biological anchor.",
    "APOE": "Lipid-transport and Alzheimer-risk biology anchor with broad microglial effects.",
    "CD4": "Immune surface marker and signaling context; requires cell-state specificity review.",
    "P2RY12": "Homeostatic microglial purinergic receptor.",
    "BCL2": "Apoptosis and cell-survival regulator.",
    "MAPK1": "MAP kinase signaling node with broad pleiotropic potential.",
    "CX3CR1": "Microglial chemokine receptor involved in neuron-microglia signaling.",
    "STAT3": "Transcriptional signaling regulator with broad inflammatory effects.",
    "CSF1R": "Microglial survival and lineage receptor.",
    "UGCG": "Glycosphingolipid synthesis enzyme and lipid-state hypothesis anchor.",
    "ROCK1": "Cytoskeletal and kinase signaling regulator.",
    "CTSD": "Lysosomal protease linked to microglial degradative state.",
    "P2RY13": "Purinergic signaling receptor.",
    "PLCG2": "Microglial immune-signaling enzyme and Alzheimer-risk biology anchor.",
    "TREM2": "Microglial lipid-sensing receptor and Alzheimer-risk biology anchor.",
    "TYROBP": "Immune receptor adaptor central to microglial signaling.",
    "C1QA": "Complement component and microglial state marker.",
    "C1QB": "Complement component and microglial state marker.",
    "C1QC": "Complement component and microglial state marker.",
    "C3": "Complement pathway component with broad inflammatory context.",
    "CD74": "Antigen-presentation pathway component.",
    "HLA-DRA": "MHC class II antigen-presentation component.",
    "SPP1": "Activated microglial/myeloid state marker.",
    "GSK3B": "Kinase with established tau-phosphorylation relevance; remains an isolated model hit here.",
    "RC3H1": "RNA/immune regulatory gene with an exceptionally large but broad model-implied shift.",
    "PAFAH1B1": "Cytoskeletal/neurodevelopmental regulator with a large broad-state model shift.",
    "DLG1": "Scaffold/signaling gene with a large broad-state model shift.",
    "FIP1L1": "RNA-processing-associated candidate; project-specific biology remains under review.",
    "SLAIN2": "Microtubule-associated candidate; project-specific biology remains under review.",
    "PTPN18": "Protein tyrosine phosphatase candidate requiring pathway-specific validation.",
    "KIF2A": "Microtubule motor regulator requiring cell-state-specific validation.",
    "ERC1": "Vesicle/scaffold-associated candidate requiring cell-state-specific validation.",
}

CLAIM_BOUNDARY = (
    "Model-implied hypothesis only. The full feature-wide run lacked nearest-neighbor manifold "
    "checking, no candidate has FDR-supported cleaner 1-hop graph coherence, and no causal or "
    "experimental validation is claimed."
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build the final Discovery Atlas v1 candidate shortlist."
    )
    parser.add_argument(
        "--scorecard",
        type=Path,
        default=Path("results/tables/discovery_scorecard_v2_graph_connected_feature_wide.csv"),
    )
    parser.add_argument(
        "--negative-controls",
        type=Path,
        default=Path("results/tables/discovery_scorecard_v2_negative_controls.csv"),
    )
    parser.add_argument(
        "--coherence",
        type=Path,
        default=Path("results/tables/discovery_scorecard_v2_graph_neighborhood_coherence.csv"),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("results/tables/discovery_final_candidate_shortlist_v1.csv"),
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("results/reports/discovery_final_candidate_shortlist_v1.md"),
    )
    parser.add_argument(
        "--targeted-audit-list",
        type=Path,
        default=Path(
            "results/tables/discovery_targeted_manifold_audit_gene_list_v1.csv"
        ),
    )
    parser.add_argument(
        "--targeted-audit-report",
        type=Path,
        default=Path(
            "results/reports/discovery_targeted_manifold_audit_gene_list_v1.md"
        ),
    )
    parser.add_argument("--broad-caution-limit", type=int, default=25)
    return parser.parse_args()


def read_required_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing required input: {path}")
    return pd.read_csv(path)


def negative_control_maps(controls: pd.DataFrame) -> tuple[dict[str, str], dict[str, str]]:
    degree = controls[controls["null_type"].eq("degree_matched")]
    class_map = {
        str(row["test_set"]).replace("class::", ""): str(row["interpretation"])
        for _, row in degree[degree["test_set"].str.startswith("class::")].iterrows()
    }
    prior_rows = degree[degree["test_set"].eq("prior_candidate_set")]
    prior_interpretation = (
        str(prior_rows["interpretation"].iloc[0]) if not prior_rows.empty else "not_testable"
    )
    named_map = {
        str(row["test_set"]).replace("named_gene::", ""): str(row["interpretation"])
        for _, row in degree[degree["test_set"].str.startswith("named_gene::")].iterrows()
    }
    return (
        {
            **{f"class::{key}": value for key, value in class_map.items()},
            "prior_candidate_set": prior_interpretation,
        },
        named_map,
    )


def make_negative_control_note(
    row: pd.Series,
    set_interpretations: dict[str, str],
    named_interpretations: dict[str, str],
) -> str:
    notes: list[str] = []
    gene = str(row["gene"])
    class_name = str(row["pathology_axis_class"])
    class_interpretation = set_interpretations.get(f"class::{class_name}", "not_testable")
    notes.append(f"class_calibration={class_interpretation}")
    if bool(row["prior_candidate_flag"]):
        notes.append(
            "prior_set="
            + set_interpretations.get("prior_candidate_set", "not_testable")
            + "_vs_random_and_degree_matched"
        )
    if gene in named_interpretations:
        notes.append(f"singleton_context={named_interpretations[gene]}")
    if class_name in CLEANER_CLASSES:
        notes.append("cleaner_vs_broad=cleaner_than_broad_reference")
    return "; ".join(notes)


def select_candidate_pool(scorecard: pd.DataFrame, broad_limit: int) -> pd.DataFrame:
    required = scorecard[
        scorecard["pathology_axis_class"].isin(CLEANER_CLASSES)
        | scorecard["gene"].isin(PRIOR_CANDIDATES)
        | scorecard["gene"].isin(NAMED_AUDIT_GENES)
    ]
    broad_pool = scorecard[
        scorecard["pathology_axis_class"].isin(
            {"broad_reactive_state_shift", "gliosis_inflating", "neuron_risk"}
        )
    ].nlargest(broad_limit, ["broad_shift_score_percentile", "gliosis_penalty_percentile"])
    return (
        pd.concat([required, broad_pool], ignore_index=True)
        .drop_duplicates("gene")
        .reset_index(drop=True)
    )


def assign_tier(row: pd.Series) -> str:
    class_name = str(row["pathology_axis_class"])
    clean_scorecard = (
        class_name in CLEANER_CLASSES
        and float(row["therapeutic_like_score_percentile"]) >= 95
        and float(row["tau_lowering_score_percentile"]) >= 90
        and float(row["neuron_preservation_score_percentile"]) >= 50
        and float(row["gliosis_penalty_percentile"]) < 60
        and float(row["broad_shift_score_percentile"]) < 90
    )
    broad_caution = (
        class_name in {"broad_reactive_state_shift", "gliosis_inflating", "neuron_risk"}
        or float(row["gliosis_penalty_percentile"]) >= 90
        or float(row["broad_shift_score_percentile"]) >= 95
    )
    if clean_scorecard:
        return "scorecard_supported_isolated_hypothesis"
    if bool(row["prior_candidate_flag"]) and not broad_caution:
        return "biological_anchor_prior_candidate"
    if broad_caution:
        return "broad_state_caution"
    return "unsupported_or_deprioritized"


def promotion_reason(row: pd.Series) -> str:
    return {
        "scorecard_supported_isolated_hypothesis": (
            "scorecard_supported_but_graph_isolated"
        ),
        "biological_anchor_prior_candidate": "prior_biological_anchor",
        "broad_state_caution": "broad_state_caution_example",
        "unsupported_or_deprioritized": "not_promoted",
    }[str(row["final_tier"])]


def deprioritization_reason(row: pd.Series) -> str:
    tier = str(row["final_tier"])
    class_name = str(row["pathology_axis_class"])
    therapeutic = float(row["therapeutic_like_score_percentile"])
    broad = float(row["broad_shift_score_percentile"])
    gliosis = float(row["gliosis_penalty_percentile"])

    if tier == "scorecard_supported_isolated_hypothesis":
        return "none"
    if tier == "biological_anchor_prior_candidate":
        return "prior_candidate_not_globally_enriched"
    if class_name == "neuron_risk":
        return "neuron_risk_penalty"
    if broad >= 90:
        if therapeutic >= 95:
            return "high_score_but_broad_shift_penalized"
        return "broad_shift_penalty"
    if gliosis >= 60:
        return "gliosis_penalty"
    if tier == "broad_state_caution":
        return "broad_shift_penalty"
    return "not_supported_by_scorecard_or_graph"


def scorecard_interpretation(row: pd.Series) -> str:
    tier = str(row["final_tier"])
    reason = str(row["deprioritization_reason"])
    if tier == "scorecard_supported_isolated_hypothesis":
        return "balanced_cleaner_scorecard_signal"
    if tier == "biological_anchor_prior_candidate":
        return "prior_anchor_not_scorecard_promoted"
    if reason == "high_score_but_broad_shift_penalized":
        return "high_score_confounded_by_broad_shift"
    if reason == "gliosis_penalty":
        return "high_score_or_partial_signal_with_gliosis_penalty"
    if reason == "neuron_risk_penalty":
        return "pathology_movement_with_neuron_risk"
    if tier == "broad_state_caution":
        return "broad_reactive_state_confounded"
    return "insufficient_balanced_scorecard_support"


def graph_interpretation(row: pd.Series) -> str:
    label = str(row["graph_neighborhood_label"])
    if label == "isolated_high_score_gene":
        return "isolated_high_score_no_fdr_supported_neighborhood"
    if label == "no_graph_support":
        return "no_supportive_one_hop_enrichment"
    if label == "broad_reactive_neighborhood":
        return "broad_neighbor_context_not_fdr_supported"
    return "graph_support_not_testable"


def caution_note(row: pd.Series) -> str:
    tier = str(row["final_tier"])
    graph = str(row["graph_neighborhood_label"])
    notes: list[str] = []
    if tier == "scorecard_supported_isolated_hypothesis":
        notes.append("Balanced scorecard signal, but no FDR-supported cleaner 1-hop graph neighborhood.")
    elif tier == "biological_anchor_prior_candidate":
        notes.append("Retained for established project biology, not because the prior set passed enrichment.")
    elif tier == "broad_state_caution":
        notes.append("Broad-shift, gliosis, or neuron-risk liability prevents therapeutic promotion.")
    else:
        notes.append("Does not currently satisfy balanced scorecard or prior-anchor criteria.")
    if graph == "isolated_high_score_gene":
        notes.append("High focal score is graph-isolated.")
    elif graph == "no_graph_support":
        notes.append("No supportive 1-hop graph enrichment.")
    elif graph == "broad_reactive_neighborhood":
        notes.append("Broad-neighbor label is absolute-profile context only, not FDR-supported enrichment.")
    notes.append("Full-run manifold nearest-neighbor safety was not computed.")
    return " ".join(notes)


def recommended_validation(row: pd.Series) -> str:
    tier = str(row["final_tier"])
    if tier == "scorecard_supported_isolated_hypothesis":
        return (
            "Targeted top-hit manifold audit; donor-bootstrap stability; cell-subtype-restricted "
            "counterfactual; covariate re-audit; external biological review."
        )
    if tier == "biological_anchor_prior_candidate":
        return (
            "Targeted manifold audit and direct comparison with prior candidate evidence; verify "
            "directionality in subtype-restricted and donor-held-out analyses."
        )
    if tier == "broad_state_caution":
        return (
            "Do not promote. Test viability/apoptosis and broad stress signatures, then run targeted "
            "manifold and subtype-restricted audits only if independent biology justifies it."
        )
    return "Deprioritize unless independent external evidence motivates a targeted re-audit."


def build_targeted_audit_list(shortlist: pd.DataFrame) -> pd.DataFrame:
    top20 = (
        shortlist[
            shortlist["final_tier"].eq("scorecard_supported_isolated_hypothesis")
        ]
        .nlargest(20, "therapeutic_like_score_percentile")["gene"]
        .tolist()
    )
    group_members = {
        "top20_tier1": set(top20),
        "prior_anchor": set(TARGETED_PRIOR_ANCHORS),
        "broad_state_caution_control": set(TARGETED_BROAD_STATE_CONTROLS),
        "special_review": set(TARGETED_SPECIAL_REVIEW),
    }
    requested = set().union(*group_members.values())
    missing = sorted(requested - set(shortlist["gene"]))
    if missing:
        raise ValueError(f"Targeted manifold-audit genes missing from shortlist: {missing}")

    audit = shortlist[shortlist["gene"].isin(requested)].copy()
    for group, members in group_members.items():
        audit[f"audit_group::{group}"] = audit["gene"].isin(members)
    group_columns = [f"audit_group::{group}" for group in group_members]
    audit["audit_groups"] = audit.apply(
        lambda row: "|".join(
            group.replace("audit_group::", "")
            for group in group_columns
            if bool(row[group])
        ),
        axis=1,
    )
    audit["audit_selection_reason"] = audit.apply(
        lambda row: "; ".join(
            reason
            for flag, reason in [
                (
                    row["audit_group::top20_tier1"],
                    "top-20 Tier-1 therapeutic-like percentile",
                ),
                (
                    row["audit_group::prior_anchor"],
                    "pre-specified prior biological anchor",
                ),
                (
                    row["audit_group::broad_state_caution_control"],
                    "broad-state/gliosis/neuron-risk caution control",
                ),
                (
                    row["audit_group::special_review"],
                    "pre-specified special-review gene",
                ),
            ]
            if bool(flag)
        ),
        axis=1,
    )
    audit["audit_priority"] = np.select(
        [
            audit["audit_group::top20_tier1"],
            audit["audit_group::special_review"],
            audit["audit_group::prior_anchor"],
            audit["audit_group::broad_state_caution_control"],
        ],
        [
            "priority_1_top_tier1",
            "priority_2_special_review",
            "priority_2_prior_anchor",
            "priority_3_caution_control",
        ],
        default="not_selected",
    )
    priority_order = {
        "priority_1_top_tier1": 1,
        "priority_2_special_review": 2,
        "priority_2_prior_anchor": 3,
        "priority_3_caution_control": 4,
    }
    audit["_priority_order"] = audit["audit_priority"].map(priority_order)
    return audit.sort_values(
        ["_priority_order", "therapeutic_like_score_percentile", "gene"],
        ascending=[True, False, True],
    ).reset_index(drop=True)


def annotate_validation_priority(
    shortlist: pd.DataFrame, targeted_audit: pd.DataFrame
) -> pd.DataFrame:
    shortlist = shortlist.copy()
    priority_map = targeted_audit.set_index("gene")["audit_priority"].to_dict()
    shortlist["next_validation_priority"] = (
        shortlist["gene"].map(priority_map).fillna("not_selected_for_targeted_audit_v1")
    )
    shortlist["targeted_manifold_audit_recommended"] = shortlist["gene"].isin(
        targeted_audit["gene"]
    )
    return shortlist


def validate_shortlist(shortlist: pd.DataFrame) -> None:
    if shortlist["gene"].duplicated().any():
        duplicates = sorted(shortlist.loc[shortlist["gene"].duplicated(), "gene"].unique())
        raise ValueError(f"Duplicate genes in shortlist: {duplicates}")

    missing_prior = sorted(set(PRIOR_CANDIDATES) - set(shortlist["gene"]))
    missing_named = sorted(set(NAMED_AUDIT_GENES) - set(shortlist["gene"]))
    if missing_prior or missing_named:
        raise ValueError(
            f"Required audit genes missing: prior={missing_prior}, named={missing_named}"
        )

    tier1 = shortlist[
        shortlist["final_tier"].eq("scorecard_supported_isolated_hypothesis")
    ]
    tier1_rules = {
        "cleaner pathology-axis class": tier1["pathology_axis_class"].isin(CLEANER_CLASSES),
        "therapeutic-like percentile >= 95": tier1[
            "therapeutic_like_score_percentile"
        ].ge(95),
        "tau-lowering percentile >= 90": tier1[
            "tau_lowering_score_percentile"
        ].ge(90),
        "neuron-preservation percentile >= 50": tier1[
            "neuron_preservation_score_percentile"
        ].ge(50),
        "gliosis percentile < 60": tier1["gliosis_penalty_percentile"].lt(60),
        "broad-shift percentile < 90": tier1["broad_shift_score_percentile"].lt(90),
    }
    failed_rules = [name for name, passed in tier1_rules.items() if not passed.all()]
    if failed_rules:
        raise ValueError(f"Tier-1 invariant failure: {failed_rules}")

    graph_promoted = tier1[
        tier1["graph_neighborhood_label"].eq("coherent_cleaner_neighborhood")
        | tier1["degree_matched_enrichment_supported"].fillna(False).astype(bool)
    ]
    if not graph_promoted.empty:
        raise ValueError(
            "Graph-positive support must not promote candidates in shortlist v1: "
            + ", ".join(graph_promoted["gene"].astype(str))
        )


def validate_targeted_audit(audit: pd.DataFrame) -> None:
    if audit["gene"].duplicated().any():
        raise ValueError("Duplicate genes in targeted manifold-audit list")
    expected = (
        set(TARGETED_PRIOR_ANCHORS)
        | set(TARGETED_BROAD_STATE_CONTROLS)
        | set(TARGETED_SPECIAL_REVIEW)
    )
    missing = sorted(expected - set(audit["gene"]))
    if missing:
        raise ValueError(f"Missing pre-specified targeted-audit genes: {missing}")
    if audit["audit_groups"].eq("").any():
        raise ValueError("Targeted-audit row without group membership")


def markdown_table(df: pd.DataFrame, columns: list[str], n: int | None = None) -> list[str]:
    subset = df.loc[:, columns].copy()
    if n is not None:
        subset = subset.head(n)
    if subset.empty:
        return ["_No rows._"]
    for column in subset.columns:
        if pd.api.types.is_numeric_dtype(subset[column]):
            subset[column] = subset[column].map(
                lambda value: "" if pd.isna(value) else f"{float(value):.5g}"
            )
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join(["---"] * len(columns)) + " |",
    ]
    lines.extend(
        "| " + " | ".join(str(value).replace("|", "/") for value in row) + " |"
        for row in subset.itertuples(index=False, name=None)
    )
    return lines


def write_report(shortlist: pd.DataFrame, args: argparse.Namespace) -> None:
    tier_counts = shortlist["final_tier"].value_counts()
    display = [
        "gene",
        "final_tier",
        "promotion_reason",
        "deprioritization_reason",
        "scorecard_interpretation",
        "graph_interpretation",
        "next_validation_priority",
        "targeted_manifold_audit_recommended",
        "pathology_axis_class",
        "therapeutic_like_score_percentile",
        "tau_lowering_score_percentile",
        "neuron_preservation_score_percentile",
        "gliosis_penalty_percentile",
        "broad_shift_score_percentile",
        "prior_candidate_flag",
    ]
    lines = [
        "# Discovery Atlas Final Candidate Shortlist v1",
        "",
        "## Gate Summary",
        "",
        "This shortlist combines scorecard-v2, the feature-wide negative-control gate, and graph-neighborhood coherence. Raw score rank alone is not sufficient for promotion.",
        "",
        "**No candidates currently have FDR-supported coherent cleaner 1-hop graph neighborhoods. Graph-neighborhood evidence is therefore not used as positive support in the final shortlist; it is used as a penalty/context label.**",
        "",
        "## Tier Meaning",
        "",
        "1. `scorecard_supported_isolated_hypothesis`: high balanced scorecard support, but no independent FDR-supported 1-hop graph-neighborhood validation.",
        "2. `biological_anchor_prior_candidate`: retained for prior biological relevance, not because the prior set passed global scorecard/null enrichment.",
        "3. `broad_state_caution`: useful caution examples where raw pathology movement may reflect broad reactive-state, gliosis, or neuron-risk effects.",
        "4. `unsupported_or_deprioritized`: not promoted under the current conservative rules. This does **not** establish biological irrelevance.",
        "",
        "Tier counts:",
        "",
    ]
    lines.extend(f"- `{tier}`: {count:,}" for tier, count in tier_counts.items())
    for tier, heading in [
        ("scorecard_supported_isolated_hypothesis", "Tier 1: Scorecard-Supported Isolated Hypotheses"),
        ("biological_anchor_prior_candidate", "Tier 2: Biological-Anchor Prior Candidates"),
        ("broad_state_caution", "Tier 3: Broad-State Cautions"),
        ("unsupported_or_deprioritized", "Tier 4: Unsupported or Deprioritized"),
    ]:
        group = shortlist[shortlist["final_tier"].eq(tier)].sort_values(
            "therapeutic_like_score_percentile", ascending=False
        )
        lines.extend(["", f"## {heading}", "", *markdown_table(group, display)])

    high_score_audit = (
        shortlist[shortlist["gene"].isin(HIGH_SCORE_DEPRIORITIZED_AUDIT)]
        .copy()
        .sort_values("therapeutic_like_score_percentile", ascending=False)
    )
    high_score_columns = [
        "gene",
        "final_tier",
        "therapeutic_like_score_percentile",
        "gliosis_penalty_percentile",
        "broad_shift_score_percentile",
        "deprioritization_reason",
        "graph_interpretation",
        "known_biology_note",
    ]
    lines.extend(
        [
            "",
            "## High-scoring but deprioritized candidates",
            "",
            "These genes illustrate why raw score rank alone is insufficient. Several have very high therapeutic-like percentiles but remain unpromoted because their movement is broad, gliosis-associated, graph-isolated, or biologically/contextually unresolved. Deprioritization under this synthesis is a validation decision, not a claim of biological irrelevance.",
            "",
            *markdown_table(high_score_audit, high_score_columns),
            "",
            "## Interpretation Boundary",
            "",
            "- The full feature-wide graph-connected screen is the official pathology-delta ranking.",
            "- The full run skipped nearest-neighbor manifold checking because of the Windows sklearn/threadpoolctl failure.",
            "- The successful pilot supports feasibility and manifold safety for the pilot subset only.",
            "- The next targeted manifold audit will provide candidate-level QC for shortlisted genes.",
            "- No current result proves causality, druggability, spatial plaque proximity, or experimental therapeutic efficacy.",
            "",
            "Class-level null enrichment is calibration rather than independent validation; singleton named-gene nulls are descriptive only; the prior candidate set did not outperform random or degree-matched background.",
            "",
            "The manuscript conclusions remain unchanged. The next step is targeted top-hit manifold auditing and candidate-specific biological review.",
            "",
        ]
    )
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text("\n".join(lines), encoding="utf-8")


def write_targeted_audit_report(audit: pd.DataFrame, args: argparse.Namespace) -> None:
    display = [
        "gene",
        "audit_priority",
        "audit_groups",
        "audit_selection_reason",
        "final_tier",
        "therapeutic_like_score_percentile",
        "deprioritization_reason",
        "graph_interpretation",
    ]
    group_counts = {
        column.replace("audit_group::", ""): int(audit[column].sum())
        for column in audit.columns
        if column.startswith("audit_group::")
    }
    lines = [
        "# Discovery Targeted Manifold Audit Gene List v1",
        "",
        "This is a bounded candidate list for a future targeted manifold audit. The audit has **not** been run.",
        "",
        "Graph-neighborhood evidence is carried only as penalty/context. No gene is selected because of positive 1-hop graph support, because no coherent cleaner neighborhood survived FDR.",
        "",
        "## Group counts",
        "",
        *[f"- `{group}`: {count}" for group, count in group_counts.items()],
        f"- unique genes after deduplication: {len(audit)}",
        "",
        "## Candidate list",
        "",
        *markdown_table(audit, display),
        "",
        "## Required boundaries",
        "",
        "- The full feature-wide graph-connected screen is the official pathology-delta ranking.",
        "- The full run skipped nearest-neighbor manifold checking because of the Windows sklearn/threadpoolctl failure.",
        "- The successful pilot supports feasibility and manifold safety for the pilot subset only.",
        "- This candidate list prepares candidate-level QC; it does not report targeted manifold-audit results.",
        "- No current result proves causality, druggability, spatial plaque proximity, or experimental therapeutic efficacy.",
        "",
    ]
    args.targeted_audit_report.parent.mkdir(parents=True, exist_ok=True)
    args.targeted_audit_report.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    scorecard = read_required_csv(args.scorecard)
    controls = read_required_csv(args.negative_controls)
    coherence = read_required_csv(args.coherence)
    scorecard["gene"] = scorecard["gene"].astype(str).str.upper()
    coherence["gene"] = coherence["gene"].astype(str).str.upper()
    set_interpretations, named_interpretations = negative_control_maps(controls)

    pool = select_candidate_pool(scorecard, args.broad_caution_limit)
    pool = pool.merge(
        coherence[
            [
                "gene",
                "coherence_status",
                "coherence_evidence_basis",
                "degree_matched_enrichment_supported",
            ]
        ],
        on="gene",
        how="left",
    )
    pool["prior_candidate_flag"] = pool["gene"].isin(PRIOR_CANDIDATES)
    pool["graph_neighborhood_label"] = pool["coherence_status"].fillna("not_testable")
    pool["negative_control_interpretation"] = pool.apply(
        lambda row: make_negative_control_note(
            row, set_interpretations, named_interpretations
        ),
        axis=1,
    )
    pool["final_tier"] = pool.apply(assign_tier, axis=1)
    pool["promotion_reason"] = pool.apply(promotion_reason, axis=1)
    pool["deprioritization_reason"] = pool.apply(deprioritization_reason, axis=1)
    pool["scorecard_interpretation"] = pool.apply(scorecard_interpretation, axis=1)
    pool["graph_interpretation"] = pool.apply(graph_interpretation, axis=1)
    pool["known_biology_note"] = pool["gene"].map(KNOWN_BIOLOGY).fillna(
        "No project-curated biology note yet; literature review is required before promotion."
    )
    pool["caution_note"] = pool.apply(caution_note, axis=1)
    pool["recommended_next_validation"] = pool.apply(recommended_validation, axis=1)
    pool["claim_boundary"] = CLAIM_BOUNDARY

    ordered = [
        "gene",
        "final_tier",
        "promotion_reason",
        "deprioritization_reason",
        "scorecard_interpretation",
        "graph_interpretation",
        "next_validation_priority",
        "targeted_manifold_audit_recommended",
        "pathology_axis_class",
        "therapeutic_like_score_percentile",
        "tau_lowering_score_percentile",
        "neuron_preservation_score_percentile",
        "gliosis_penalty_percentile",
        "broad_shift_score_percentile",
        "negative_control_interpretation",
        "graph_neighborhood_label",
        "prior_candidate_flag",
        "known_biology_note",
        "caution_note",
        "recommended_next_validation",
        "claim_boundary",
    ]
    tier_order = {
        "scorecard_supported_isolated_hypothesis": 1,
        "biological_anchor_prior_candidate": 2,
        "broad_state_caution": 3,
        "unsupported_or_deprioritized": 4,
    }
    pool["_tier_order"] = pool["final_tier"].map(tier_order)
    pool = pool.sort_values(
        ["_tier_order", "therapeutic_like_score_percentile"],
        ascending=[True, False],
    ).reset_index(drop=True)
    targeted_audit = build_targeted_audit_list(pool)
    pool = annotate_validation_priority(pool, targeted_audit)
    targeted_audit = build_targeted_audit_list(pool)
    validate_shortlist(pool)
    validate_targeted_audit(targeted_audit)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    pool[ordered].to_csv(args.out, index=False)
    write_report(pool, args)
    targeted_columns = [
        "gene",
        "audit_priority",
        "audit_groups",
        "audit_selection_reason",
        "audit_group::top20_tier1",
        "audit_group::prior_anchor",
        "audit_group::broad_state_caution_control",
        "audit_group::special_review",
        "final_tier",
        "promotion_reason",
        "deprioritization_reason",
        "scorecard_interpretation",
        "graph_interpretation",
        "therapeutic_like_score_percentile",
        "tau_lowering_score_percentile",
        "neuron_preservation_score_percentile",
        "gliosis_penalty_percentile",
        "broad_shift_score_percentile",
        "known_biology_note",
        "claim_boundary",
    ]
    args.targeted_audit_list.parent.mkdir(parents=True, exist_ok=True)
    targeted_audit[targeted_columns].to_csv(args.targeted_audit_list, index=False)
    write_targeted_audit_report(targeted_audit, args)

    print(f"Wrote {args.out}")
    print(f"Wrote {args.report}")
    print(f"Wrote {args.targeted_audit_list}")
    print(f"Wrote {args.targeted_audit_report}")
    print("\nFinal tier counts:")
    print(pool["final_tier"].value_counts().to_string())


if __name__ == "__main__":
    main()
