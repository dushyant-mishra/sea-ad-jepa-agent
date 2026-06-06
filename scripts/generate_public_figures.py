from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


FIG_DIR = Path("results/figures")
FIG_DIR.mkdir(parents=True, exist_ok=True)


COLORS = {
    "ink": "#17212b",
    "muted": "#5c6670",
    "blue": "#2563eb",
    "cyan": "#0891b2",
    "green": "#059669",
    "amber": "#d97706",
    "red": "#dc2626",
    "purple": "#7c3aed",
    "slate": "#334155",
    "light": "#f8fafc",
    "line": "#cbd5e1",
}


def save(fig: plt.Figure, name: str) -> None:
    fig.savefig(FIG_DIR / f"{name}.svg", bbox_inches="tight")
    fig.savefig(FIG_DIR / f"{name}.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def box(ax, xy, w, h, text, fc="#ffffff", ec=COLORS["line"], color=COLORS["ink"], fontsize=10):
    patch = FancyBboxPatch(
        xy,
        w,
        h,
        boxstyle="round,pad=0.018,rounding_size=0.025",
        linewidth=1.2,
        edgecolor=ec,
        facecolor=fc,
    )
    ax.add_patch(patch)
    ax.text(xy[0] + w / 2, xy[1] + h / 2, text, ha="center", va="center", color=color, fontsize=fontsize, weight="semibold")
    return patch


def arrow(ax, start, end, color=COLORS["slate"]):
    ax.add_patch(FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=14, linewidth=1.4, color=color))


def figure_v2_curriculum() -> None:
    fig, ax = plt.subplots(figsize=(12, 5.2))
    ax.axis("off")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.text(0.03, 0.94, "Graph-JEPA v2 training curriculum", fontsize=17, weight="bold", color=COLORS["ink"])
    ax.text(
        0.03,
        0.88,
        "A three-stage curriculum separates healthy/reference learning, SEA-AD calibration, and disease-vector training.",
        fontsize=10.5,
        color=COLORS["muted"],
    )

    xs = [0.05, 0.37, 0.69]
    labels = [
        "Stage A\nCELLxGENE normal microglia\n\nlearn healthy/reference\ngene-graph manifold",
        "Stage B\nSEA-AD low-pathology anchors\n\ncalibrate to aged postmortem\nSEA-AD context",
        "Stage C\nFull SEA-AD Microglia-PVM\n\nlearn disease movement\nwith anchor rehearsal",
    ]
    fills = ["#dbeafe", "#dcfce7", "#ffedd5"]
    edge = [COLORS["blue"], COLORS["green"], COLORS["amber"]]
    for x, label, fc, ec in zip(xs, labels, fills, edge):
        box(ax, (x, 0.43), 0.24, 0.30, label, fc=fc, ec=ec, fontsize=10)
    arrow(ax, (0.29, 0.58), (0.37, 0.58), COLORS["blue"])
    arrow(ax, (0.61, 0.58), (0.69, 0.58), COLORS["green"])

    box(ax, (0.19, 0.16), 0.28, 0.15, "STRING gene graph\n2,957 genes | 231,015 edge columns", fc="#f1f5f9", ec=COLORS["slate"], fontsize=9.5)
    box(ax, (0.54, 0.16), 0.31, 0.15, "Rehearsal prevents forgetting\nSEA anchor cosine + CELLxGENE anchor cosine", fc="#f1f5f9", ec=COLORS["slate"], fontsize=9.5)
    arrow(ax, (0.33, 0.31), (0.17, 0.43), COLORS["slate"])
    arrow(ax, (0.70, 0.31), (0.81, 0.43), COLORS["slate"])
    save(fig, "public_v2_curriculum_schematic")


def figure_v1_to_v2() -> None:
    fig, ax = plt.subplots(figsize=(12, 5.6))
    ax.axis("off")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.text(0.03, 0.94, "Why v2 exists: v1 failure modes and Graph-JEPA fixes", fontsize=17, weight="bold", color=COLORS["ink"])
    ax.text(0.03, 0.88, "The v1 model produced useful hypotheses, but its limitations define the Graph-JEPA roadmap.", fontsize=10.5, color=COLORS["muted"])

    problems = [
        "Flat-vector topology\nGenes are independent columns",
        "Over-pinning\nAnchors preserved too tightly",
        "Disease tube\nSignal collapses into few dimensions",
        "Perturbation gap\nWeak alignment for specific regulators",
    ]
    fixes = [
        "Gene graph\nSTRING edges + gene identity embeddings",
        "Elastic rehearsal\ncosine safety boundary, not concrete wall",
        "Covariance telemetry\ntrack effective dims + top singular ratio",
        "External validation gate\nCRISPRi/drug/spatial follow-up",
    ]
    y0 = 0.70
    for i, (p, f) in enumerate(zip(problems, fixes)):
        y = y0 - i * 0.15
        box(ax, (0.05, y), 0.34, 0.095, p, fc="#fee2e2", ec=COLORS["red"], fontsize=9.3)
        box(ax, (0.61, y), 0.34, 0.095, f, fc="#dcfce7", ec=COLORS["green"], fontsize=9.3)
        arrow(ax, (0.40, y + 0.047), (0.61, y + 0.047), COLORS["slate"])
    ax.text(0.22, 0.79, "v1 lessons", ha="center", fontsize=11, weight="bold", color=COLORS["red"])
    ax.text(0.78, 0.79, "v2 responses", ha="center", fontsize=11, weight="bold", color=COLORS["green"])
    save(fig, "public_v1_to_v2_problem_solution")


def figure_stage_c_leaderboard() -> None:
    path = Path("results/tables/stage_c_finetuning_combined_leaderboard.csv")
    df = pd.read_csv(path).head(10).copy()
    df["label"] = df["run_id"].str.replace("fine_loose_", "loose_", regex=False).str.replace("sweep_", "", regex=False)
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.3), gridspec_kw={"width_ratios": [1.15, 1]})
    ax = axes[0]
    colors = [COLORS["green"] if i == 0 else COLORS["blue"] if "loose" in r else COLORS["slate"] for i, r in enumerate(df["label"])]
    ax.barh(df["label"][::-1], df["composite_score"][::-1], color=colors[::-1])
    ax.set_title("Stage C sweep leaderboard", loc="left", fontsize=14, weight="bold")
    ax.set_xlabel("Composite score")
    ax.grid(axis="x", alpha=0.25)
    ax.text(0.01, 1.04, "Best run balances pathology signal, manifold spread, and anchor safety.", transform=ax.transAxes, fontsize=9.5, color=COLORS["muted"])

    best = df.iloc[0]
    metrics = pd.Series(
        {
            "AT8 ridge": best["at8_ridge"],
            "NeuN ridge": best["neun_ridge"],
            "AT8 cosine kNN": best["at8_cosine_knn"],
            "NeuN cosine kNN": best["neun_cosine_knn"],
            "SEA anchor cosine": best["sea_anchor_cosine"],
            "CELLxGENE anchor cosine": best["cellxgene_anchor_cosine"],
        }
    )
    ax = axes[1]
    bar_colors = [COLORS["purple"], COLORS["purple"], COLORS["cyan"], COLORS["cyan"], COLORS["green"], COLORS["green"]]
    ax.barh(metrics.index[::-1], metrics.values[::-1], color=bar_colors[::-1])
    ax.axvline(0.95, color=COLORS["red"], linestyle="--", linewidth=1, label="anchor safety floor")
    ax.set_xlim(0, 1.02)
    ax.set_title("Best Stage C run", loc="left", fontsize=14, weight="bold")
    ax.set_xlabel("Spearman or cosine")
    ax.grid(axis="x", alpha=0.25)
    ax.legend(loc="lower right", frameon=False, fontsize=8)
    fig.suptitle("Current Stage C default: rehearsal=0.005, covariance=0.0005, epoch=5", y=1.03, fontsize=11, color=COLORS["ink"])
    save(fig, "public_stage_c_sweep_leaderboard")


def figure_pca_vs_jepa() -> None:
    df = pd.read_csv("results/tables/latent_space_evaluation_jepa_vs_pca_summary.csv")
    labels = ["GFAP", "A beta / 6e10", "Iba1", "AT8 / pTau", "NeuN"]
    df = df.set_index("target").loc[
        [
            "percent GFAP positive area_Grey matter",
            "percent 6e10 positive area_Grey matter",
            "percent Iba1 positive area_Grey matter",
            "percent AT8 positive area_Grey matter",
            "percent NeuN positive area_Grey matter",
        ]
    ]
    fig, ax = plt.subplots(figsize=(10, 5.2))
    x = range(len(labels))
    ax.bar([i - 0.18 for i in x], df["pca_knn_spearman"], width=0.36, label="PCA", color="#94a3b8")
    ax.bar([i + 0.18 for i in x], df["jepa_knn_spearman"], width=0.36, label="JEPA", color=COLORS["blue"])
    ax.axhline(0, color=COLORS["line"], linewidth=1)
    ax.set_xticks(list(x), labels, rotation=0)
    ax.set_ylabel("Donor-level kNN Spearman")
    ax.set_title("Donor-level representation geometry: PCA vs JEPA", loc="left", fontsize=14, weight="bold")
    ax.text(0, 1.04, "JEPA improves several pathology-neighborhood signals, especially GFAP and A beta/6e10, while NeuN is roughly tied.", transform=ax.transAxes, fontsize=9.5, color=COLORS["muted"])
    ax.legend(frameon=False)
    ax.grid(axis="y", alpha=0.25)
    save(fig, "public_pca_vs_jepa_pathology_geometry")


def figure_cell_mixing() -> None:
    df = pd.read_csv("results/tables/cell_level_mixing_metrics.csv").set_index("representation")
    labels = ["donor kNN accuracy", "pathology minus permuted", "|donor silhouette|"]
    pca = [
        df.loc["expression_pca_128", "donor_knn_accuracy"],
        df.loc["expression_pca_128", "pathology_minus_permuted"],
        abs(df.loc["expression_pca_128", "donor_silhouette"]),
    ]
    jepa = [
        df.loc["jepa_latent_128", "donor_knn_accuracy"],
        df.loc["jepa_latent_128", "pathology_minus_permuted"],
        abs(df.loc["jepa_latent_128", "donor_silhouette"]),
    ]
    fig, ax = plt.subplots(figsize=(9.5, 5))
    x = range(len(labels))
    ax.bar([i - 0.18 for i in x], pca, width=0.36, label="PCA", color="#94a3b8")
    ax.bar([i + 0.18 for i in x], jepa, width=0.36, label="JEPA", color=COLORS["green"])
    ax.set_xticks(list(x), labels)
    ax.set_title("Cell-level donor leakage and pathology mixing", loc="left", fontsize=14, weight="bold")
    ax.text(0, 1.05, "Lower donor kNN accuracy suggests less donor memorization; pathology signal is weak because AT8 is donor-level.", transform=ax.transAxes, fontsize=9.5, color=COLORS["muted"])
    ax.grid(axis="y", alpha=0.25)
    ax.legend(frameon=False)
    save(fig, "public_cell_level_mixing")


def figure_multitarget_oof() -> None:
    df = pd.read_csv("results/tables/multitarget_oof_jepa_vs_pseudobulk_summary.csv")
    df = df.sort_values("jepa_minus_pseudobulk", ascending=True)
    labels = (
        df["target"]
        .str.replace("percent ", "", regex=False)
        .str.replace(" positive area_Grey matter", "", regex=False)
        .str.replace("_Grey matter", "", regex=False)
        .str.replace("guhcl ", "guhcl ", regex=False)
        .str.replace("ripa ", "ripa ", regex=False)
    )
    colors = [COLORS["green"] if v >= 0 else COLORS["red"] for v in df["jepa_minus_pseudobulk"]]
    fig, ax = plt.subplots(figsize=(10, 5.8))
    ax.barh(labels, df["jepa_minus_pseudobulk"], color=colors)
    ax.axvline(0, color=COLORS["ink"], linewidth=1)
    ax.set_xlabel("Best JEPA Spearman - pseudobulk Spearman")
    ax.set_title("Pooled donor-held-out validation across pathology targets", loc="left", fontsize=14, weight="bold")
    ax.text(0, 1.04, "Positive values indicate targets where JEPA embeddings beat pseudobulk in pooled OOF validation.", transform=ax.transAxes, fontsize=9.5, color=COLORS["muted"])
    ax.grid(axis="x", alpha=0.25)
    save(fig, "public_multitarget_oof_validation")


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
    figure_v2_curriculum()
    figure_v1_to_v2()
    figure_stage_c_leaderboard()
    figure_pca_vs_jepa()
    figure_cell_mixing()
    figure_multitarget_oof()
    print("Wrote public figures to", FIG_DIR)


if __name__ == "__main__":
    main()
