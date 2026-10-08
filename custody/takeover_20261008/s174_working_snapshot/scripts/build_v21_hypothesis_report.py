from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


DEFAULT_UPGRADE_ATTR = Path("results/tables/v2_1_upgrade_fine_08_latent_gene_attributions.csv")
DEFAULT_BRIDGE_ATTR = Path("results/tables/v2_1_fine_bridge_06_latent_gene_attributions.csv")
DEFAULT_UPGRADE_JAC = Path("results/tables/v2_1_upgrade_fine_08_latent_jacobian_top_edges.csv")
DEFAULT_BRIDGE_JAC = Path("results/tables/v2_1_fine_bridge_06_latent_jacobian_top_edges.csv")
DEFAULT_MODULE_CF = Path("results/tables/v2_1_upgrade_fine_08_module_counterfactual_at8.csv")
DEFAULT_GENE_CF = Path("results/tables/v2_1_upgrade_fine_08_gene_counterfactual_at8.csv")


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(path)
    return pd.read_csv(path)


def first_nonempty(values: pd.Series) -> str:
    for value in values.astype(str):
        if value and value.lower() != "nan":
            return value
    return ""


def summarize_attr(attr: pd.DataFrame, model_label: str, top_n: int = 8) -> pd.DataFrame:
    rows = []
    for latent, group in attr.groupby("latent_dimension", sort=False):
        top = group.sort_values("rank").head(top_n)
        rows.append(
            {
                "model": model_label,
                "latent_factor": latent,
                "top_genes": ", ".join(top["gene"].astype(str).tolist()),
                "top_modules": "; ".join(
                    sorted(
                        {
                            part.strip()
                            for value in top["module_annotations"].fillna("")
                            for part in str(value).split(";")
                            if part.strip()
                        }
                    )
                ),
                "actionable_hits": ", ".join(
                    top.loc[
                        (top["is_hpa_fda_drug_target"].fillna(0).astype(int) > 0)
                        | (top["is_hpa_predicted_membrane"].fillna(0).astype(int) > 0)
                        | (top["is_hpa_predicted_secreted"].fillna(0).astype(int) > 0),
                        "gene",
                    ]
                    .astype(str)
                    .tolist()
                ),
            }
        )
    return pd.DataFrame(rows)


def best_attr_by_gene(attr: pd.DataFrame, prefix: str) -> pd.DataFrame:
    attr = attr.copy()
    attr["gene"] = attr["gene"].astype(str).str.upper()
    idx = attr.groupby("gene")["rank"].idxmin()
    out = attr.loc[idx, ["gene", "latent_dimension", "rank", "module_annotations"]].copy()
    out = out.rename(
        columns={
            "latent_dimension": f"{prefix}_best_latent",
            "rank": f"{prefix}_best_rank",
            "module_annotations": f"{prefix}_modules",
        }
    )
    action_cols = ["is_hpa_fda_drug_target", "is_hpa_predicted_membrane", "is_hpa_predicted_secreted"]
    action = attr.groupby("gene")[action_cols].max().reset_index()
    out = out.merge(action, on="gene", how="left")
    return out


def build_target_matrix(gene_cf: pd.DataFrame, upgrade_attr: pd.DataFrame, bridge_attr: pd.DataFrame) -> pd.DataFrame:
    targets = gene_cf.copy()
    targets["gene"] = targets["perturbation"].astype(str).str.upper()

    upgrade_best = best_attr_by_gene(upgrade_attr, "upgrade")
    bridge_best = best_attr_by_gene(bridge_attr, "bridge")
    bridge_best = bridge_best.drop(
        columns=[
            "is_hpa_fda_drug_target",
            "is_hpa_predicted_membrane",
            "is_hpa_predicted_secreted",
        ],
        errors="ignore",
    )

    targets = targets.merge(upgrade_best, on="gene", how="left")
    targets = targets.merge(bridge_best, on="gene", how="left")

    targets["direction"] = targets["mean_delta_raw_scale"].map(
        lambda x: "AT8-up when perturbed" if x > 0 else "AT8-down when perturbed"
    )
    targets["druggability_evidence"] = targets.apply(
        lambda r: "; ".join(
            label
            for label, flag in [
                ("HPA/FDA drug target", r.get("is_hpa_fda_drug_target", 0)),
                ("predicted membrane", r.get("is_hpa_predicted_membrane", 0)),
                ("predicted secreted", r.get("is_hpa_predicted_secreted", 0)),
            ]
            if int(flag or 0) > 0
        )
        or "no HPA actionability flag",
        axis=1,
    )
    targets["cross_model_support"] = targets["bridge_best_latent"].notna().map(
        {True: "also decoded in fine_bridge_06", False: "not top-ranked in fine_bridge_06 axes"}
    )

    targets["evidence_score"] = (
        targets["abs_mean_delta_raw_scale"].rank(pct=True)
        + targets["upgrade_best_latent"].notna().astype(float) * 0.5
        + targets["bridge_best_latent"].notna().astype(float) * 0.5
        + targets["is_hpa_fda_drug_target"].fillna(0).astype(float) * 0.5
        + targets["is_hpa_predicted_membrane"].fillna(0).astype(float) * 0.25
        + targets["is_hpa_predicted_secreted"].fillna(0).astype(float) * 0.25
    )

    keep = [
        "gene",
        "module",
        "upgrade_best_latent",
        "upgrade_best_rank",
        "bridge_best_latent",
        "bridge_best_rank",
        "mean_delta_raw_scale",
        "abs_mean_delta_raw_scale",
        "direction",
        "druggability_evidence",
        "cross_model_support",
        "evidence_score",
    ]
    return targets[keep].sort_values(["evidence_score", "abs_mean_delta_raw_scale"], ascending=False)


def markdown_table(df: pd.DataFrame, max_rows: int = 12, float_digits: int = 4) -> str:
    view = df.head(max_rows).copy()
    for col in view.select_dtypes(include=["float"]).columns:
        view[col] = view[col].map(lambda x: f"{x:.{float_digits}f}")
    view = view.fillna("")
    cols = [str(c) for c in view.columns]
    lines = [
        "| " + " | ".join(cols) + " |",
        "| " + " | ".join(["---"] * len(cols)) + " |",
    ]
    for _, row in view.iterrows():
        values = [str(row[col]).replace("\n", " ").replace("|", "/") for col in view.columns]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def write_report(
    report_path: Path,
    target_matrix: pd.DataFrame,
    module_cf: pd.DataFrame,
    upgrade_latents: pd.DataFrame,
    bridge_latents: pd.DataFrame,
    upgrade_jac: pd.DataFrame,
    bridge_jac: pd.DataFrame,
) -> None:
    module_view = module_cf.sort_values("abs_mean_delta_raw_scale", ascending=False)[
        ["module", "n_genes_perturbed", "mean_delta_raw_scale", "median_delta_raw_scale", "genes"]
    ]

    upgrade_jac_view = upgrade_jac.head(10)[
        [
            "source_latent_factor",
            "target_latent_factor",
            "mean_jacobian",
            "source_annotation",
            "target_annotation",
        ]
    ]
    bridge_jac_view = bridge_jac.head(10)[
        [
            "source_latent_factor",
            "target_latent_factor",
            "mean_jacobian",
            "source_annotation",
            "target_annotation",
        ]
    ]

    text = f"""# v2.1 Microglia Biological Hypotheses

This report summarizes biology extracted from the Graph-JEPA v2.1 checkpoint `upgrade_fine_08` and compares it with the AT8-strong bridge checkpoint `fine_bridge_06`.

## Interpretation Boundary

These results are model-implied hypotheses. They are not experimental proof of causality. The digital perturbations ask how a trained representation and donor-level pathology head respond when gene or module expression is counterfactually shifted toward a reference value. True causal validation still requires perturbation data or wet-lab follow-up.

## Model Showdown

`upgrade_fine_08` is the preferred v2.1 model because it preserves healthy anchors while improving balanced AT8, NeuN, and GFAP geometry. `fine_bridge_06` remains useful as an AT8-sensitive comparator. The core biology is more credible when both checkpoints point toward overlapping genes, modules, or latent axes.

### upgrade_fine_08 Decoded Latent Axes

{markdown_table(upgrade_latents, max_rows=13)}

### fine_bridge_06 Decoded Latent Axes

{markdown_table(bridge_latents, max_rows=13)}

## Predictor Jacobian Sensitivity

Both models show strong predictor sensitivity around lysosome/phagocytosis-annotated latent factors. That convergence suggests the Graph-JEPA predictor is routing disease-relevant information through phagocytic/lysosomal state axes rather than purely through generic donor or batch structure.

### upgrade_fine_08 Top Latent Edges

{markdown_table(upgrade_jac_view, max_rows=10)}

### fine_bridge_06 Top Latent Edges

{markdown_table(bridge_jac_view, max_rows=10)}

## Module Counterfactuals For AT8

Negative deltas mean the model's predicted AT8 burden moves down after the module is shifted toward the reference value. Positive deltas mean predicted AT8 moves up.

{markdown_table(module_view, max_rows=10)}

## Ranked Gene Target Matrix

The ranking combines counterfactual effect size, whether the gene appears in decoded latent axes, cross-model support from `fine_bridge_06`, and HPA actionability flags.

{markdown_table(target_matrix, max_rows=20)}

## Working Biological Hypotheses

1. Antigen-presentation and vascular/barrier myeloid programs are the strongest AT8-lowering module-level counterfactuals in `upgrade_fine_08`.
2. Lysosome/phagocytosis is the most stable predictor-Jacobian routing signal across both v2.1 and bridge checkpoints.
3. STAT3, APP, GRB2, APOE, HSP90AA1, CX3CR1, BCL2, and HIF1A are the largest AT8-up single-gene perturbation responses in the current screen.
4. TLR2, CD4, PTPRG, ROCK1, and P2RY13 show AT8-down perturbation direction in the current screen and should be treated as candidate intervention hypotheses.
5. The model now produces coherent biology. Further tuning should pause unless independent validation or a new target metric shows that the biological ranking is unstable.

## Next Validation Step

The next best scientific step is not more architecture tuning. It is testing whether the same ranked modules and genes reproduce in an independent AD/control or perturbation dataset, while keeping the SEA-AD-trained encoder frozen.
"""
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(text, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the v2.1 microglia hypothesis matrix and report.")
    parser.add_argument("--upgrade-attr", type=Path, default=DEFAULT_UPGRADE_ATTR)
    parser.add_argument("--bridge-attr", type=Path, default=DEFAULT_BRIDGE_ATTR)
    parser.add_argument("--upgrade-jac", type=Path, default=DEFAULT_UPGRADE_JAC)
    parser.add_argument("--bridge-jac", type=Path, default=DEFAULT_BRIDGE_JAC)
    parser.add_argument("--module-counterfactuals", type=Path, default=DEFAULT_MODULE_CF)
    parser.add_argument("--gene-counterfactuals", type=Path, default=DEFAULT_GENE_CF)
    parser.add_argument("--target-matrix-out", type=Path, default=Path("results/tables/v2_1_ranked_target_matrix.csv"))
    parser.add_argument("--report-out", type=Path, default=Path("results/reports/v2_1_microglia_biological_hypotheses.md"))
    args = parser.parse_args()

    upgrade_attr = read_csv(args.upgrade_attr)
    bridge_attr = read_csv(args.bridge_attr)
    upgrade_jac = read_csv(args.upgrade_jac)
    bridge_jac = read_csv(args.bridge_jac)
    module_cf = read_csv(args.module_counterfactuals)
    gene_cf = read_csv(args.gene_counterfactuals)

    target_matrix = build_target_matrix(gene_cf, upgrade_attr, bridge_attr)
    args.target_matrix_out.parent.mkdir(parents=True, exist_ok=True)
    target_matrix.to_csv(args.target_matrix_out, index=False)

    upgrade_latents = summarize_attr(upgrade_attr, "upgrade_fine_08")
    bridge_latents = summarize_attr(bridge_attr, "fine_bridge_06")
    write_report(args.report_out, target_matrix, module_cf, upgrade_latents, bridge_latents, upgrade_jac, bridge_jac)

    print(f"Wrote {args.target_matrix_out}")
    print(f"Wrote {args.report_out}")
    print("\nTop ranked targets:")
    print(target_matrix.head(12).to_string(index=False))


if __name__ == "__main__":
    main()
