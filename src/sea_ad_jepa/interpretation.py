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

