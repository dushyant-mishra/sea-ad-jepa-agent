from __future__ import annotations

from pathlib import Path

import pandas as pd


TARGET_LABELS = {
    "percent AT8 positive area_Grey matter": "AT8/pTau",
    "percent 6e10 positive area_Grey matter": "A beta/6e10",
    "percent GFAP positive area_Grey matter": "GFAP",
    "percent Iba1 positive area_Grey matter": "Iba1",
    "percent NeuN positive area_Grey matter": "NeuN",
}

MODULE_FILES = [
    Path("results/tables/v2_1_upgrade_fine_08_module_counterfactual_at8.csv"),
    Path("results/tables/v2_1_upgrade_fine_08_module_counterfactual_6e10.csv"),
    Path("results/tables/v2_1_upgrade_fine_08_module_counterfactual_gfap.csv"),
    Path("results/tables/v2_1_upgrade_fine_08_module_counterfactual_iba1.csv"),
    Path("results/tables/v2_1_upgrade_fine_08_module_counterfactual_neun.csv"),
]

GENE_FILES = [
    Path("results/tables/v2_1_upgrade_fine_08_gene_counterfactual_at8.csv"),
    Path("results/tables/v2_1_upgrade_fine_08_gene_counterfactual_6e10.csv"),
    Path("results/tables/v2_1_upgrade_fine_08_gene_counterfactual_gfap.csv"),
    Path("results/tables/v2_1_upgrade_fine_08_gene_counterfactual_iba1.csv"),
    Path("results/tables/v2_1_upgrade_fine_08_gene_counterfactual_neun.csv"),
]


def load_many(paths: list[Path]) -> pd.DataFrame:
    frames = []
    for path in paths:
        if not path.exists():
            raise FileNotFoundError(path)
        frame = pd.read_csv(path)
        frame["source_file"] = str(path)
        frames.append(frame)
    data = pd.concat(frames, ignore_index=True)
    data["target_short"] = data["target"].map(TARGET_LABELS).fillna(data["target"])
    data["effect_direction"] = data["mean_delta_raw_scale"].map(lambda x: "up" if x > 0 else "down")
    return data


def summarize(data: pd.DataFrame, entity_col: str) -> pd.DataFrame:
    rows = []
    for entity, group in data.groupby(entity_col):
        effects = group.set_index("target_short")["mean_delta_raw_scale"].to_dict()
        abs_effects = group.set_index("target_short")["abs_mean_delta_raw_scale"].to_dict()
        rows.append(
            {
                entity_col: entity,
                "n_targets": group["target_short"].nunique(),
                "n_targets_up": int((group["mean_delta_raw_scale"] > 0).sum()),
                "n_targets_down": int((group["mean_delta_raw_scale"] < 0).sum()),
                "mean_abs_delta": group["abs_mean_delta_raw_scale"].mean(),
                "max_abs_delta": group["abs_mean_delta_raw_scale"].max(),
                "strongest_target": group.sort_values("abs_mean_delta_raw_scale", ascending=False).iloc[0][
                    "target_short"
                ],
                "strongest_delta": group.sort_values("abs_mean_delta_raw_scale", ascending=False).iloc[0][
                    "mean_delta_raw_scale"
                ],
                "AT8_delta": effects.get("AT8/pTau", pd.NA),
                "A_beta_6e10_delta": effects.get("A beta/6e10", pd.NA),
                "GFAP_delta": effects.get("GFAP", pd.NA),
                "Iba1_delta": effects.get("Iba1", pd.NA),
                "NeuN_delta": effects.get("NeuN", pd.NA),
                "effect_signature": "; ".join(
                    f"{row.target_short}:{'up' if row.mean_delta_raw_scale > 0 else 'down'}"
                    for row in group.sort_values("target_short").itertuples()
                ),
            }
        )
    return pd.DataFrame(rows).sort_values(["mean_abs_delta", "max_abs_delta"], ascending=False)


def write_report(module_summary: pd.DataFrame, gene_summary: pd.DataFrame, out: Path) -> None:
    def md_table(df: pd.DataFrame) -> str:
        view = df.copy().fillna("")
        for col in view.select_dtypes(include=["float"]).columns:
            view[col] = view[col].map(lambda x: f"{x:.4f}")
        cols = [str(c) for c in view.columns]
        lines = [
            "| " + " | ".join(cols) + " |",
            "| " + " | ".join(["---"] * len(cols)) + " |",
        ]
        for _, row in view.iterrows():
            values = [str(row[col]).replace("\n", " ").replace("|", "/") for col in view.columns]
            lines.append("| " + " | ".join(values) + " |")
        return "\n".join(lines)

    out.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# v2.1 Multi-Target Counterfactual Stability",
        "",
        "This summary compares the same Graph-JEPA v2.1 digital perturbations across AT8/pTau, A beta/6e10, GFAP, Iba1, and NeuN. Effects are model-implied prediction shifts, not validated causal effects.",
        "",
        "## Module-Level Stability",
        "",
        md_table(module_summary.head(10)),
        "",
        "## Gene-Level Stability",
        "",
        md_table(gene_summary.head(15)),
        "",
        "## Interpretation",
        "",
        "- A module/gene with the same sign across many targets is likely a broad tissue-state axis.",
        "- A module/gene with opposite signs across targets may separate amyloid/tau burden from gliosis, microglial activation, or neuronal-density readouts.",
        "- NeuN should be interpreted carefully: positive NeuN deltas mean the model predicts higher neuronal marker area after the perturbation.",
    ]
    out.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    module_data = load_many(MODULE_FILES)
    gene_data = load_many(GENE_FILES)

    module_summary = summarize(module_data, "module")
    gene_summary = summarize(gene_data, "perturbation")

    module_data.to_csv("results/tables/v2_1_multitarget_module_counterfactual_long.csv", index=False)
    gene_data.to_csv("results/tables/v2_1_multitarget_gene_counterfactual_long.csv", index=False)
    module_summary.to_csv("results/tables/v2_1_multitarget_module_counterfactual_summary.csv", index=False)
    gene_summary.to_csv("results/tables/v2_1_multitarget_gene_counterfactual_summary.csv", index=False)
    write_report(
        module_summary,
        gene_summary,
        Path("results/reports/v2_1_multitarget_counterfactual_stability.md"),
    )

    print("Top module stability:")
    print(module_summary.head(10).to_string(index=False))
    print("\nTop gene stability:")
    print(gene_summary.head(15).to_string(index=False))


if __name__ == "__main__":
    main()
