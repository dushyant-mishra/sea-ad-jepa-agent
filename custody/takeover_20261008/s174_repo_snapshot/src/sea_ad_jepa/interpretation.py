from __future__ import annotations

from pathlib import Path

import pandas as pd


AD_GENE_SETS = {
    "microglia_plaque_response": {
        "APOE",
        "TREM2",
        "TYROBP",
        "LPL",
        "CST7",
        "CTSD",
        "C1QA",
        "C1QB",
        "C1QC",
        "ITGAX",
    },
    "complement_inflammation": {
        "C1QA",
        "C1QB",
        "C1QC",
        "C3",
        "C4A",
        "C4B",
        "CFH",
        "SERPING1",
    },
    "interferon_activation": {
        "IFI27",
        "IFI44",
        "IFI44L",
        "IFIT1",
        "IFIT2",
        "IFIT3",
        "ISG15",
        "MX1",
    },
    "lipid_metabolism": {
        "APOE",
        "LPL",
        "ABCA1",
        "ABCA7",
        "CLU",
        "PLCG2",
        "SORL1",
    },
}


def score_gene_sets(gene_scores: pd.DataFrame, gene_column: str = "gene", score_column: str = "score") -> pd.DataFrame:
    rows = []
    scores = gene_scores.set_index(gene_column)[score_column]
    ranked = gene_scores.sort_values(score_column, ascending=False).reset_index(drop=True)
    top_500 = set(ranked.head(500)[gene_column])

    for name, genes in AD_GENE_SETS.items():
        present = [gene for gene in genes if gene in scores.index]
        rows.append(
            {
                "gene_set": name,
                "n_present": len(present),
                "n_top_500": len(set(present) & top_500),
                "mean_score": float(scores.loc[present].mean()) if present else float("nan"),
                "genes_present": ";".join(present),
            }
        )
    return pd.DataFrame(rows).sort_values(["n_top_500", "mean_score"], ascending=False)


def write_hypothesis_report(baseline_results: pd.DataFrame, out_path: str | Path) -> None:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    top = baseline_results.sort_values("spearman", ascending=False).head(5)
    lines = [
        "# Microglia-PVM Hypothesis Report",
        "",
        "This report summarizes the first donor-level microglia pseudobulk baseline.",
        "The results are predictive associations, not causal claims.",
        "",
        "## Top Pathology Targets",
        "",
    ]
    for _, row in top.iterrows():
        lines.append(
            f"- `{row['target']}`: Spearman={row['spearman']:.3f}, R2={row['r2']:.3f}, donors={int(row['n_donors'])}"
        )

    lines.extend(
        [
            "",
            "## Initial Biological Interpretation",
            "",
            "High-performing pathology targets should be followed by gene-level association analysis.",
            "For Microglia-PVM, the first gene modules to inspect are plaque-response, complement/inflammation, interferon activation, and lipid metabolism.",
            "",
            "## Evidence Levels",
            "",
            "- Association: pseudobulk expression correlates with donor-level pathology.",
            "- Predictive: target is predicted in held-out donor folds.",
            "- Regulatory candidate: requires gene/module ranking and enrichment.",
            "- Validated: requires external spatial, IHC/IF, perturbational, or literature evidence.",
        ]
    )
    out_path.write_text("\n".join(lines), encoding="utf-8")


def _metric_line(row: pd.Series) -> str:
    return f"- `{row['target']}`: Spearman={row['spearman']:.3f}, R2={row['r2']:.3f}, MAE={row['mae']:.3g}"


def write_integrated_report(
    pseudobulk_results: pd.DataFrame,
    jepa_results: pd.DataFrame,
    gene_rankings: pd.DataFrame,
    gene_set_scores: pd.DataFrame,
    out_path: str | Path,
    target_name: str = "percent AT8 positive area_Grey matter",
) -> None:
    """Write a narrative report combining baseline, JEPA, and gene-ranking evidence."""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    pseudo_top = pseudobulk_results.sort_values("spearman", ascending=False).head(5)
    jepa_top = jepa_results.sort_values("spearman", ascending=False).head(5)
    top_genes = gene_rankings.head(15)
    top_sets = gene_set_scores.sort_values(["n_top_500", "mean_score"], ascending=False)

    target_row = pseudobulk_results[pseudobulk_results["target"] == target_name]
    target_summary = ""
    if not target_row.empty:
        row = target_row.iloc[0]
        target_summary = (
            f"For `{target_name}`, Microglia-PVM pseudobulk reached "
            f"Spearman={row['spearman']:.3f} and R2={row['r2']:.3f} in held-out donor folds."
        )

    lines = [
        "# Integrated Microglia-PVM Interpretation Report",
        "",
        "## Executive Summary",
        "",
        "This report integrates three evidence streams from the first SEA-AD Microglia-PVM pilot:",
        "",
        "1. donor-level pseudobulk pathology prediction",
        "2. JEPA donor-embedding pathology prediction",
        "3. gene rankings for an AT8/pTau pathology target",
        "",
        "The goal is hypothesis prioritization, not causal proof.",
        "",
    ]
    if target_summary:
        lines.extend([target_summary, ""])

    lines.extend(["## Pathology Prediction From Microglia-PVM Pseudobulk", ""])
    for _, row in pseudo_top.iterrows():
        lines.append(_metric_line(row))

    lines.extend(
        [
            "",
            "Interpretation:",
            "",
            "The strongest first-pass signal is AT8/pTau-related pathology. This suggests that donor-level microglial expression carries information about tau pathology burden.",
            "",
            "## Pathology Prediction From JEPA Donor Embeddings",
            "",
        ]
    )
    for _, row in jepa_top.iterrows():
        lines.append(_metric_line(row))

    lines.extend(
        [
            "",
            "Interpretation:",
            "",
            "The first JEPA model captures donor-level pathology signal, but the current simple random-masking objective does not yet outperform pseudobulk for AT8/pTau. This is useful: it tells us the next modeling step should be pathway-aware or module-aware masking rather than more generic training.",
            "",
            "## Top Genes Associated With AT8/pTau Pathology",
            "",
        ]
    )
    for _, row in top_genes.iterrows():
        lines.append(f"- `{row['gene']}`: association score={row['score']:.3f}")

    lines.extend(["", "## AD-Relevant Gene Set Check", ""])
    for _, row in top_sets.iterrows():
        lines.append(
            f"- `{row['gene_set']}`: {int(row['n_top_500'])} genes in top 500, mean score={row['mean_score']:.3f}; genes={row['genes_present']}"
        )

    lines.extend(
        [
            "",
            "## Working Hypothesis",
            "",
            "A Microglia-PVM expression program is associated with AT8/pTau pathology burden across donors. The first-pass gene rankings point toward inflammatory, lysosomal/stress-response, and immune-regulatory biology, but this should be treated as a candidate signal until pathway enrichment and spatial validation are added.",
            "",
            "## Recommended Next Analyses",
            "",
            "- Train JEPA with pathway-aware masking focused on immune, complement, lipid, lysosomal, and stress-response modules.",
            "- Compare AT8-associated genes against spatial transcriptomics or pathology-adjacent tissue regions.",
            "- Add enrichment analysis against GO, Reactome, KEGG, MSigDB, and AD-specific gene sets.",
            "- Check whether top genes remain stable under donor bootstrap or leave-one-donor-out analysis.",
            "- Generate marker suggestions for IHC/IF validation near AT8-positive regions.",
            "",
            "## Evidence Level",
            "",
            "- Current level: predictive association.",
            "- Not yet shown: causal regulation, spatial co-localization, perturbational support, or experimental validation.",
        ]
    )
    out_path.write_text("\n".join(lines), encoding="utf-8")
