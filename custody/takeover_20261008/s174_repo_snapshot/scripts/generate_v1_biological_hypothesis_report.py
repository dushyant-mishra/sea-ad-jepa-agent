from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


AT8_TARGET = "percent AT8 positive area_Grey matter"
NEUN_TARGET = "percent NeuN positive area_Grey matter"
FOCUS_LATENT = "jepa_63"
FOCUS_LATENT_ID = 63


def read_csv(path: str | Path) -> pd.DataFrame:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Required input not found: {path}")
    return pd.read_csv(path)


def fmt(value: float | int | str, digits: int = 3) -> str:
    if isinstance(value, str):
        return value
    if pd.isna(value):
        return "NA"
    return f"{float(value):.{digits}f}"


def signed(value: float, digits: int = 3) -> str:
    if pd.isna(value):
        return "NA"
    return f"{float(value):+.{digits}f}"


def make_gene_candidates(gene_knockouts: pd.DataFrame, adjusted_genes: pd.DataFrame) -> pd.DataFrame:
    candidates = gene_knockouts.copy()
    candidates = candidates.rename(columns={"perturbation": "gene"})
    candidates = candidates[
        [
            "gene",
            "module",
            "mean_donor_delta",
            "bootstrap_ci_low",
            "bootstrap_ci_high",
            "n_donors",
            "n_cells",
        ]
    ]

    adjusted = adjusted_genes.rename(columns={"treatment": "gene"})
    adjusted = adjusted[
        [
            "gene",
            "adjusted_slope",
            "partial_spearman",
            "mean_adjusted_contribution",
            "bootstrap_ci_low",
            "bootstrap_ci_high",
        ]
    ].rename(
        columns={
            "bootstrap_ci_low": "adjusted_ci_low",
            "bootstrap_ci_high": "adjusted_ci_high",
        }
    )

    merged = candidates.merge(adjusted, on="gene", how="left")
    merged = (
        merged.sort_values(["gene", "mean_donor_delta"])
        .groupby("gene", as_index=False)
        .agg(
            module=("module", lambda values: "; ".join(sorted(set(values)))),
            mean_donor_delta=("mean_donor_delta", "first"),
            bootstrap_ci_low=("bootstrap_ci_low", "first"),
            bootstrap_ci_high=("bootstrap_ci_high", "first"),
            n_donors=("n_donors", "first"),
            n_cells=("n_cells", "first"),
            adjusted_slope=("adjusted_slope", "first"),
            partial_spearman=("partial_spearman", "first"),
            mean_adjusted_contribution=("mean_adjusted_contribution", "first"),
            adjusted_ci_low=("adjusted_ci_low", "first"),
            adjusted_ci_high=("adjusted_ci_high", "first"),
        )
    )
    merged["model_implied_at8_reducing_knockout"] = merged["mean_donor_delta"] < 0
    merged["confounder_adjusted_abs_partial_spearman"] = merged["partial_spearman"].abs()
    return merged.sort_values(
        ["model_implied_at8_reducing_knockout", "confounder_adjusted_abs_partial_spearman", "mean_donor_delta"],
        ascending=[False, False, True],
    )


def make_module_candidates(
    module_comparison: pd.DataFrame,
    fold_modules: pd.DataFrame,
    adjusted_modules: pd.DataFrame,
) -> pd.DataFrame:
    fold = fold_modules[
        [
            "module",
            "mean_donor_delta",
            "bootstrap_ci_low",
            "bootstrap_ci_high",
            "fold_sign_consistency",
            "genes",
        ]
    ].rename(
        columns={
            "mean_donor_delta": "global_mean_delta",
            "bootstrap_ci_low": "global_mean_ci_low",
            "bootstrap_ci_high": "global_mean_ci_high",
        }
    )
    adjusted = adjusted_modules.rename(columns={"treatment": "module"})[
        [
            "module",
            "adjusted_slope",
            "partial_spearman",
            "mean_adjusted_contribution",
            "bootstrap_ci_low",
            "bootstrap_ci_high",
        ]
    ].rename(
        columns={
            "bootstrap_ci_low": "adjusted_ci_low",
            "bootstrap_ci_high": "adjusted_ci_high",
        }
    )

    merged = module_comparison.merge(fold, on="module", how="left").merge(adjusted, on="module", how="left")
    merged["confounder_adjusted_abs_partial_spearman"] = merged["partial_spearman"].abs()
    return merged.sort_values(
        ["same_sign_all_three", "max_abs_delta", "confounder_adjusted_abs_partial_spearman"],
        ascending=[False, False, False],
    )


def write_report(
    out_path: Path,
    latent_weights_63: pd.DataFrame,
    latent_annotations_63: pd.DataFrame,
    latent_edges_63: pd.DataFrame,
    gene_candidates: pd.DataFrame,
    module_candidates: pd.DataFrame,
) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)

    at8_row = latent_weights_63[latent_weights_63["target"].eq(AT8_TARGET)].iloc[0]
    neun_row = latent_weights_63[latent_weights_63["target"].eq(NEUN_TARGET)].iloc[0]
    top_modules = latent_annotations_63.head(5)
    top_genes = gene_candidates.head(10)
    top_modules_table = module_candidates.head(10)

    lines: list[str] = []
    lines.append("# SEA-AD JEPA v1 Biological Hypothesis Report")
    lines.append("")
    lines.append("This report extracts the biology that the current SEA-AD JEPA v1 model appears to rely on when predicting neuropathology from Microglia-PVM expression. These are model-implied hypotheses, not experimental proof of causality.")
    lines.append("")
    lines.append("## Core Interpretation Boundary")
    lines.append("")
    lines.append("- Association means a gene, module, or latent factor tracks pathology in the observed SEA-AD cohort.")
    lines.append("- Prediction means the representation improves held-out pathology ranking or neighborhood structure.")
    lines.append("- Digital knockout means the trained model changes its prediction after an in-silico perturbation.")
    lines.append("- Causal validation requires an external perturbation experiment, such as CRISPRi, CRISPR knockout, or drug response.")
    lines.append("")
    lines.append("## Key Latent Finding: jepa_63")
    lines.append("")
    lines.append(f"`{FOCUS_LATENT}` is the strongest latent coefficient for AT8/pTau in the current pathology-weight table.")
    lines.append("")
    lines.append("| Target | Mean coefficient | Std. coefficient | Interpretation |")
    lines.append("|---|---:|---:|---|")
    lines.append(f"| AT8 / pTau | {signed(at8_row['mean_coefficient'])} | {fmt(at8_row['std_coefficient'])} | Lower `{FOCUS_LATENT}` is associated with higher model-predicted AT8 burden. |")
    lines.append(f"| NeuN | {signed(neun_row['mean_coefficient'])} | {fmt(neun_row['std_coefficient'])} | Lower `{FOCUS_LATENT}` is also associated with higher model-predicted NeuN signal in this head, making this factor pleiotropic rather than AT8-only. |")
    lines.append("")
    lines.append("Top module annotations for `jepa_63`:")
    lines.append("")
    lines.append("| Module | Correlation |")
    lines.append("|---|---:|")
    for row in top_modules.itertuples(index=False):
        lines.append(f"| {row.module} | {signed(row.correlation)} |")
    lines.append("")
    if not latent_edges_63.empty:
        lines.append("Top directed latent Jacobian edges involving `jepa_63`:")
        lines.append("")
        lines.append("| Source | Target | Mean Jacobian | Source annotation | Target annotation |")
        lines.append("|---:|---:|---:|---|---|")
        for row in latent_edges_63.head(8).itertuples(index=False):
            lines.append(
                f"| {row.source_latent_dim} | {row.target_latent_dim} | {signed(row.mean_jacobian)} | {row.source_annotation} | {row.target_annotation} |"
            )
        lines.append("")
    lines.append("Working interpretation: `jepa_63` looks like a complement/antigen-presentation/synapse-pruning axis that the model uses when ranking tau pathology and neuronal marker readouts. This should be treated as a candidate microglial immune-state axis for follow-up, not as a named biological pathway yet.")
    lines.append("")
    lines.append("## Strongest AT8 Gene-Level Hypotheses")
    lines.append("")
    lines.append("Negative digital-knockout deltas mean that reducing that gene in-silico lowers the model's AT8 prediction. The confounder-adjusted partial Spearman column asks whether the gene still tracks AT8 after adjusting for donor-level covariates included in the current workflow.")
    lines.append("")
    lines.append("| Gene | Module | Knockout delta | Confounder partial Spearman | Adjusted slope |")
    lines.append("|---|---|---:|---:|---:|")
    for row in top_genes.itertuples(index=False):
        lines.append(
            f"| {row.gene} | {row.module} | {signed(row.mean_donor_delta, 4)} | {signed(row.partial_spearman) if pd.notna(row.partial_spearman) else 'NA'} | {signed(row.adjusted_slope) if pd.notna(row.adjusted_slope) else 'NA'} |"
        )
    lines.append("")
    lines.append("The most direct v1 AT8-reduction hypotheses are therefore centered on the AT8-associated first-pass genes, especially PTPRG, CHI3L1, NFKBIA, S100A4, TNFRSF11B, DRAM1, CTSD, and P2RY12. Several of these survive confounder-adjusted association, but this still does not prove that perturbing them will reduce tau pathology in a biological system.")
    lines.append("")
    lines.append("## Module-Level Hypotheses")
    lines.append("")
    lines.append("| Module | Global-mean knockout delta | Zero/mean sign-stable | Max absolute delta | Confounder partial Spearman |")
    lines.append("|---|---:|---|---:|---:|")
    for row in top_modules_table.itertuples(index=False):
        lines.append(
            f"| {row.module} | {signed(row.global_mean_delta, 4) if pd.notna(row.global_mean_delta) else 'NA'} | {bool(row.same_sign_all_three)} | {fmt(row.max_abs_delta, 4)} | {signed(row.partial_spearman) if pd.notna(row.partial_spearman) else 'NA'} |"
        )
    lines.append("")
    lines.append("The AT8-associated first-pass module is the cleanest model-implied AT8-lowering module under multiple intervention styles. Vascular/barrier, lipid, complement, and synapse-pruning modules are also repeatedly implicated, but their sign can depend on the intervention definition. That sign sensitivity is biologically important: these modules may represent tissue context, resilience, or mixed cell-state programs rather than simple one-directional disease drivers.")
    lines.append("")
    lines.append("## Three Concrete v1 Hypotheses")
    lines.append("")
    lines.append("1. **AT8-linked inflammatory/stress program.** The model predicts lower AT8 when the AT8-associated first-pass gene set is perturbed, with strong individual signals for PTPRG, CHI3L1, NFKBIA, S100A4, TNFRSF11B, DRAM1, CTSD, and P2RY12. Validation path: test whether these markers spatially enrich near AT8-positive regions and whether their perturbation changes tau-associated microglial states in an iPSC-microglia system.")
    lines.append("")
    lines.append("2. **Complement/synapse-pruning latent axis.** `jepa_63` links AT8 prediction to complement, antigen presentation, and synapse-pruning annotations. Validation path: map `jepa_63`-high and `jepa_63`-low donors/cells to C1QA/C1QB/C1QC, HLA genes, synaptic pruning markers, and AT8 burden.")
    lines.append("")
    lines.append("3. **Vascular/barrier and lipid context as modifiers.** Vascular/barrier and lipid/complement modules have strong confounder-adjusted relationships, but their counterfactual signs are not always simple. Validation path: treat these as context-modifier hypotheses and test them against vascular adjacency, plaque proximity, and APOE/TREM2/LPL-associated microglial states rather than expecting a single monotonic knockout effect.")
    lines.append("")
    lines.append("## Next Biological Checks")
    lines.append("")
    lines.append("- Plot `jepa_63` across donors and color by AT8, NeuN, and disease progression.")
    lines.append("- Extract top genes correlated with `jepa_63` directly from cell-level expression, not only curated module annotations.")
    lines.append("- Re-run the gene/module reports for Abeta/6e10, GFAP, Iba1, and NeuN to find stable multi-pathology modules.")
    lines.append("- Treat Kampmann/iPSC-microglia CRISPRi as external stress testing, while reserving SEA-AD internal reports for AD-specific hypothesis generation.")
    lines.append("")

    out_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the v1 SEA-AD JEPA biological hypothesis report.")
    parser.add_argument("--latent-weights", default="results/tables/pathology_latent_weights.csv")
    parser.add_argument("--latent-annotations", default="results/tables/latent_jacobian_ema_var_e30_module_annotations.csv")
    parser.add_argument("--latent-edges", default="results/tables/latent_jacobian_ema_var_e30_top_edges.csv")
    parser.add_argument("--module-comparison", default="results/tables/causal_fold_specific_module_knockout_intervention_comparison.csv")
    parser.add_argument("--fold-modules", default="results/tables/causal_fold_specific_module_knockouts_at8_global_mean.csv")
    parser.add_argument("--gene-knockouts", default="results/tables/causal_gene_knockouts_top_modules_at8_global_mean.csv")
    parser.add_argument("--adjusted-genes", default="results/tables/confounder_adjusted_top_gene_effects_at8.csv")
    parser.add_argument("--adjusted-modules", default="results/tables/confounder_adjusted_module_effects_at8.csv")
    parser.add_argument("--out-report", default="results/reports/v1_microglia_biological_hypotheses.md")
    parser.add_argument("--out-genes", default="results/tables/v1_hypothesis_candidate_genes.csv")
    parser.add_argument("--out-modules", default="results/tables/v1_hypothesis_candidate_modules.csv")
    parser.add_argument("--out-latent", default="results/tables/v1_jepa_63_decode.csv")
    args = parser.parse_args()

    latent_weights = read_csv(args.latent_weights)
    latent_annotations = read_csv(args.latent_annotations)
    latent_edges = read_csv(args.latent_edges)
    module_comparison = read_csv(args.module_comparison)
    fold_modules = read_csv(args.fold_modules)
    gene_knockouts = read_csv(args.gene_knockouts)
    adjusted_genes = read_csv(args.adjusted_genes)
    adjusted_modules = read_csv(args.adjusted_modules)

    latent_weights_63 = latent_weights[latent_weights["latent_dimension"].eq(FOCUS_LATENT)].copy()
    if latent_weights_63.empty:
        raise ValueError(f"{FOCUS_LATENT} was not found in {args.latent_weights}")
    if not latent_weights_63["target"].eq(AT8_TARGET).any():
        raise ValueError(f"{AT8_TARGET} was not found for {FOCUS_LATENT}")
    if not latent_weights_63["target"].eq(NEUN_TARGET).any():
        raise ValueError(f"{NEUN_TARGET} was not found for {FOCUS_LATENT}")

    latent_annotations_63 = (
        latent_annotations[latent_annotations["latent_dim"].eq(FOCUS_LATENT_ID)]
        .sort_values("abs_correlation", ascending=False)
        .copy()
    )
    latent_edges_63 = (
        latent_edges[
            latent_edges["source_latent_dim"].eq(FOCUS_LATENT_ID)
            | latent_edges["target_latent_dim"].eq(FOCUS_LATENT_ID)
        ]
        .sort_values("abs_mean_jacobian", ascending=False)
        .copy()
    )

    gene_candidates = make_gene_candidates(gene_knockouts, adjusted_genes)
    module_candidates = make_module_candidates(module_comparison, fold_modules, adjusted_modules)

    Path(args.out_genes).parent.mkdir(parents=True, exist_ok=True)
    gene_candidates.to_csv(args.out_genes, index=False)
    module_candidates.to_csv(args.out_modules, index=False)

    latent_decode = pd.concat(
        [
            latent_weights_63.assign(section="pathology_weight"),
            latent_annotations_63.rename(columns={"latent_dim": "latent_id"}).assign(section="module_annotation"),
        ],
        ignore_index=True,
        sort=False,
    )
    latent_decode.to_csv(args.out_latent, index=False)

    write_report(
        out_path=Path(args.out_report),
        latent_weights_63=latent_weights_63,
        latent_annotations_63=latent_annotations_63,
        latent_edges_63=latent_edges_63,
        gene_candidates=gene_candidates,
        module_candidates=module_candidates,
    )

    print(f"Wrote {args.out_report}")
    print(f"Wrote {args.out_genes}")
    print(f"Wrote {args.out_modules}")
    print(f"Wrote {args.out_latent}")


if __name__ == "__main__":
    main()
