from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


LEADERBOARD = Path("results/tables/stage_c_finetuning_combined_leaderboard.csv")
OUT_TABLE = Path("results/tables/stage_c_finetuning_parameter_summary.csv")
OUT_FIG = Path("results/figures/public_stage_c_finetuning_parameter_sensitivity.svg")
OUT_MD = Path("docs/stage_c_finetuning_analysis.md")


COLORS = {
    "ink": "#17212b",
    "muted": "#5c6670",
    "blue": "#2563eb",
    "green": "#059669",
    "amber": "#d97706",
    "red": "#dc2626",
    "purple": "#7c3aed",
    "line": "#cbd5e1",
}


def read_leaderboard() -> pd.DataFrame:
    df = pd.read_csv(LEADERBOARD)
    numeric_cols = [
        "checkpoint_epoch",
        "rehearsal_weight",
        "disease_covariance_weight",
        "composite_score",
        "at8_ridge",
        "neun_ridge",
        "at8_euclidean_knn",
        "neun_euclidean_knn",
        "at8_cosine_knn",
        "neun_cosine_knn",
        "gfap_cosine_knn",
        "iba1_cosine_knn",
        "effective_dims",
        "top_sv_ratio",
        "sea_anchor_cosine",
        "cellxgene_anchor_cosine",
        "anchor_penalty",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df.sort_values("composite_score", ascending=False).reset_index(drop=True)


def summarize_parameters(df: pd.DataFrame) -> pd.DataFrame:
    records = []
    for (rehearsal, covariance), group in df.groupby(["rehearsal_weight", "disease_covariance_weight"], dropna=False):
        best = group.sort_values("composite_score", ascending=False).iloc[0]
        records.append(
            {
                "rehearsal_weight": rehearsal,
                "disease_covariance_weight": covariance,
                "n_checkpoints": len(group),
                "best_run_id": best["run_id"],
                "best_epoch": int(best["checkpoint_epoch"]),
                "best_composite_score": best["composite_score"],
                "best_at8_ridge": best["at8_ridge"],
                "best_neun_ridge": best["neun_ridge"],
                "best_at8_cosine_knn": best["at8_cosine_knn"],
                "best_neun_cosine_knn": best["neun_cosine_knn"],
                "best_effective_dims": best["effective_dims"],
                "best_top_sv_ratio": best["top_sv_ratio"],
                "best_sea_anchor_cosine": best["sea_anchor_cosine"],
                "best_cellxgene_anchor_cosine": best["cellxgene_anchor_cosine"],
                "anchor_safe": bool(best["sea_anchor_cosine"] >= 0.95 and best["cellxgene_anchor_cosine"] >= 0.95),
            }
        )
    out = pd.DataFrame(records).sort_values("best_composite_score", ascending=False)
    OUT_TABLE.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT_TABLE, index=False)
    return out


def make_figure(df: pd.DataFrame, param_summary: pd.DataFrame) -> None:
    OUT_FIG.parent.mkdir(parents=True, exist_ok=True)
    top = df.head(10).copy()
    top["label"] = top["run_id"].str.replace("fine_loose_", "loose_", regex=False).str.replace("sweep_", "", regex=False)

    fig, axes = plt.subplots(2, 2, figsize=(13, 8.5))
    fig.suptitle("Stage C fine-tuning diagnostics", fontsize=16, weight="bold", color=COLORS["ink"], y=0.98)

    ax = axes[0, 0]
    colors = [COLORS["green"] if i == 0 else COLORS["blue"] for i in range(len(top))]
    ax.barh(top["label"][::-1], top["composite_score"][::-1], color=colors[::-1])
    ax.set_title("Top configurations", loc="left", fontsize=12, weight="bold")
    ax.set_xlabel("Composite score")
    ax.grid(axis="x", alpha=0.25)

    ax = axes[0, 1]
    scatter = ax.scatter(
        param_summary["rehearsal_weight"],
        param_summary["best_composite_score"],
        c=param_summary["disease_covariance_weight"],
        s=90,
        cmap="viridis",
        edgecolor=COLORS["ink"],
        linewidth=0.4,
    )
    ax.set_xscale("log")
    ax.set_title("Rehearsal weight sensitivity", loc="left", fontsize=12, weight="bold")
    ax.set_xlabel("Rehearsal weight")
    ax.set_ylabel("Best composite score")
    ax.grid(alpha=0.25)
    cb = fig.colorbar(scatter, ax=ax)
    cb.set_label("Disease covariance weight")

    ax = axes[1, 0]
    best = df.iloc[0]
    metrics = pd.Series(
        {
            "AT8 ridge": best["at8_ridge"],
            "NeuN ridge": best["neun_ridge"],
            "AT8 cosine kNN": best["at8_cosine_knn"],
            "NeuN cosine kNN": best["neun_cosine_knn"],
            "GFAP cosine kNN": best["gfap_cosine_knn"],
            "Iba1 cosine kNN": best["iba1_cosine_knn"],
        }
    )
    ax.barh(metrics.index[::-1], metrics.values[::-1], color=COLORS["purple"])
    ax.axvline(0, color=COLORS["line"], linewidth=1)
    ax.set_title("Best-run pathology readouts", loc="left", fontsize=12, weight="bold")
    ax.set_xlabel("Spearman")
    ax.grid(axis="x", alpha=0.25)

    ax = axes[1, 1]
    geometry = pd.Series(
        {
            "effective dims": best["effective_dims"],
            "top SV ratio x10": best["top_sv_ratio"] * 10,
            "SEA anchor cosine x5": best["sea_anchor_cosine"] * 5,
            "CELLxGENE anchor cosine x5": best["cellxgene_anchor_cosine"] * 5,
        }
    )
    ax.barh(geometry.index[::-1], geometry.values[::-1], color=[COLORS["amber"], COLORS["red"], COLORS["green"], COLORS["green"]][::-1])
    ax.set_title("Best-run geometry and anchor safety", loc="left", fontsize=12, weight="bold")
    ax.set_xlabel("Scaled diagnostic value")
    ax.grid(axis="x", alpha=0.25)
    ax.text(
        0.0,
        -0.26,
        "Scaled view: top SV ratio and anchor cosines are multiplied for readability.",
        transform=ax.transAxes,
        fontsize=9,
        color=COLORS["muted"],
    )

    fig.tight_layout(rect=[0, 0.03, 1, 0.95])
    fig.savefig(OUT_FIG, bbox_inches="tight")
    plt.close(fig)


def fmt(value: float, digits: int = 3) -> str:
    if pd.isna(value):
        return "NA"
    return f"{value:.{digits}f}"


def write_markdown(df: pd.DataFrame, param_summary: pd.DataFrame) -> None:
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    best = df.iloc[0]
    top_rows = df.head(8)
    safe = df[(df["sea_anchor_cosine"] >= 0.95) & (df["cellxgene_anchor_cosine"] >= 0.95)].copy()
    best_safe = safe.iloc[0] if len(safe) else None
    best_is_anchor_safe = bool(best["sea_anchor_cosine"] >= 0.95 and best["cellxgene_anchor_cosine"] >= 0.95)
    anchor_text = (
        "Interpretation: the best run is anchor-safe by the current 0.95 cosine rule. It keeps both reference anchors above the safety boundary while allowing more disease movement than the earlier over-pinned Stage C runs."
        if best_is_anchor_safe
        else "Interpretation: the best run is the current performance leader, but it is not strictly anchor-safe by the 0.95 cosine rule. It should be treated as a high-performing exploratory candidate, while the best strict anchor-safe run remains the conservative default."
    )

    lines = [
        "# Stage C Fine-Tuning Analysis",
        "",
        "This report uses the current Stage C fine-tuning sweep as the active v2 baseline. It is generated from:",
        "",
        "```text",
        str(LEADERBOARD),
        "```",
        "",
        "## Current Best Configuration",
        "",
        "```text",
        f"run: {best['run_id']}",
        f"checkpoint epoch: {int(best['checkpoint_epoch'])}",
        f"SEA/CELLxGENE rehearsal weight: {fmt(best['rehearsal_weight'], 4)}",
        f"disease covariance weight: {fmt(best['disease_covariance_weight'], 4)}",
        f"composite score: {fmt(best['composite_score'])}",
        "```",
        "",
        "Key readouts:",
        "",
        "```text",
        f"AT8 ridge Spearman:          {fmt(best['at8_ridge'])}",
        f"NeuN ridge Spearman:         {fmt(best['neun_ridge'])}",
        f"AT8 cosine kNN Spearman:     {fmt(best['at8_cosine_knn'])}",
        f"NeuN cosine kNN Spearman:    {fmt(best['neun_cosine_knn'])}",
        f"GFAP cosine kNN Spearman:    {fmt(best['gfap_cosine_knn'])}",
        f"Iba1 cosine kNN Spearman:    {fmt(best['iba1_cosine_knn'])}",
        f"effective dimensions:        {fmt(best['effective_dims'])}",
        f"top singular value ratio:    {fmt(best['top_sv_ratio'])}",
        f"SEA anchor cosine:           {fmt(best['sea_anchor_cosine'])}",
        f"CELLxGENE anchor cosine:     {fmt(best['cellxgene_anchor_cosine'])}",
        "```",
        "",
        anchor_text,
        "",
        "![Stage C fine-tuning diagnostics](../results/figures/public_stage_c_finetuning_parameter_sensitivity.svg)",
        "",
        "**Figure legend:** The diagnostics summarize which Stage C parameter settings worked best. The current performance leader uses low rehearsal weight and a very small disease covariance penalty. This supports the idea that the disease manifold needs room to move, while the anchor cosines provide a safety check against catastrophic forgetting.",
        "",
        "## Top Fine-Tuned Runs",
        "",
        "| rank | run | epoch | rehearsal | covariance | composite | AT8 ridge | NeuN ridge | AT8 cosine kNN | anchor cosines |",
        "|---:|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for idx, row in top_rows.iterrows():
        lines.append(
            "| "
            + " | ".join(
                [
                    str(idx + 1),
                    str(row["run_id"]),
                    str(int(row["checkpoint_epoch"])),
                    fmt(row["rehearsal_weight"], 4),
                    fmt(row["disease_covariance_weight"], 4),
                    fmt(row["composite_score"]),
                    fmt(row["at8_ridge"]),
                    fmt(row["neun_ridge"]),
                    fmt(row["at8_cosine_knn"]),
                    f"{fmt(row['sea_anchor_cosine'])} / {fmt(row['cellxgene_anchor_cosine'])}",
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## Parameter Takeaways",
            "",
            "- The best current regime is not the tightest anchor regime. Earlier runs with anchor cosines near 0.999 preserved the reference space too strongly and limited disease geometry.",
            "- Very loose rehearsal can help, but the anchor safety boundary still matters. The current winner sits just above the 0.95 cosine floor for both SEA-AD and CELLxGENE anchors.",
            "- A small covariance penalty helps reduce the narrow disease-tube failure mode without fully over-damping the disease manifold.",
            "- Cosine kNN is more informative than Euclidean kNN in the current 128D space, suggesting that disease direction/profile is more stable than raw Euclidean neighborhood distance.",
            "",
            "## Current Default for Next Runs",
            "",
            "Use the current performance leader for exploratory downstream analyses:",
            "",
            "```text",
            f"--weight-sea {best['rehearsal_weight']}",
            f"--weight-cx {best['rehearsal_weight']}",
            f"--disease-cov-weight {best['disease_covariance_weight']}",
            "--epochs 5",
            "```",
            "",
        ]
    )

    if best_safe is not None:
        lines.extend(
            [
                "Use the best strict anchor-safe setting when the 0.95 cosine rule is required:",
                "",
                "```text",
                f"run: {best_safe['run_id']}",
                f"--weight-sea {best_safe['rehearsal_weight']}",
                f"--weight-cx {best_safe['rehearsal_weight']}",
                f"--disease-cov-weight {best_safe['disease_covariance_weight']}",
                "--epochs 5",
                "```",
                "",
            ]
        )

    lines.extend(
        [
        "Recommended next diagnostic:",
        "",
        "```text",
        "Compare the performance leader and strict anchor-safe leader with module/gene attribution,",
        "then decide whether to relax the anchor rule or tune margin/temperature to recover anchor safety.",
        "```",
            "",
            "## Evidence Boundary",
            "",
            "These are fine-tuning diagnostics, not biological causal validation. The best checkpoint should be treated as the current representation baseline for downstream hypothesis generation and external validation.",
        ]
    )

    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.labelcolor": COLORS["ink"],
            "xtick.color": COLORS["ink"],
            "ytick.color": COLORS["ink"],
        }
    )
    df = read_leaderboard()
    param_summary = summarize_parameters(df)
    make_figure(df, param_summary)
    write_markdown(df, param_summary)
    print(f"Wrote {OUT_TABLE}")
    print(f"Wrote {OUT_FIG}")
    print(f"Wrote {OUT_MD}")


if __name__ == "__main__":
    main()
