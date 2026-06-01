from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "results" / "tables"
FIGURES = ROOT / "results" / "figures"
MULTITARGET = TABLES / "multitarget_causal"

TARGETS = {
    "percent AT8 positive area_Grey matter": {
        "label": "AT8 / pTau",
        "definition": "IHC-positive hyperphosphorylated tau area in grey matter.",
    },
    "percent 6e10 positive area_Grey matter": {
        "label": "A beta / 6E10",
        "definition": "IHC-positive amyloid-beta plaque area in grey matter.",
    },
    "percent GFAP positive area_Grey matter": {
        "label": "GFAP",
        "definition": "Astrocyte reactivity / astrogliosis area in grey matter.",
    },
    "percent Iba1 positive area_Grey matter": {
        "label": "Iba1",
        "definition": "Microglial activation / microgliosis area in grey matter.",
    },
    "percent NeuN positive area_Grey matter": {
        "label": "NeuN",
        "definition": "Mature neuronal marker area; lower signal is consistent with neuronal loss.",
    },
    "guhcl pTau_Grey matter": {
        "label": "Guanidine pTau",
        "definition": "Biochemically measured insoluble phosphorylated tau.",
    },
    "guhcl abeta42_Grey matter": {
        "label": "Guanidine A beta 42",
        "definition": "Biochemically measured insoluble amyloid-beta 42.",
    },
}


def slugify(name: str) -> str:
    return name.replace(" ", "_").replace("%", "percent").replace("/", "_").replace("+", "_plus_")


@st.cache_data
def read_csv(path: Path) -> pd.DataFrame | None:
    if path.exists():
        return pd.read_csv(path)
    return None


def show_missing(path: Path) -> None:
    st.info(f"Missing expected file: `{path.relative_to(ROOT)}`")


def metric_delta(label: str, value: float, help_text: str | None = None) -> None:
    st.metric(label, f"{value:+.3f}", help=help_text)


st.set_page_config(
    page_title="SEA-AD JEPA Agent",
    page_icon="",
    layout="wide",
)

st.markdown(
    """
    <style>
    .block-container { padding-top: 1.5rem; max-width: 1320px; }
    div[data-testid="stMetric"] {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 0.8rem 1rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("SEA-AD JEPA Agent")
st.caption(
    "A pathology-grounded biological state space for Alzheimer's disease, with prediction, "
    "representation diagnostics, and model-implied counterfactual screens."
)

target = st.sidebar.selectbox(
    "Pathology target",
    options=list(TARGETS),
    format_func=lambda value: TARGETS[value]["label"],
)
target_info = TARGETS[target]
target_slug = slugify(target)

st.sidebar.markdown(f"**{target_info['label']}**")
st.sidebar.write(target_info["definition"])
st.sidebar.markdown("---")
st.sidebar.write("Interpretation boundary:")
st.sidebar.write("Association and prediction are not biological proof of causality.")
st.sidebar.write("Digital knockouts are model-implied counterfactual hypotheses.")

overview_tab, representation_tab, prediction_tab, counterfactual_tab, latent_tab, perturb_tab = st.tabs(
    [
        "Overview",
        "Representation Space",
        "Prediction",
        "Counterfactuals",
        "Latent Factors",
        "External Perturbation",
    ]
)

with overview_tab:
    st.subheader("Project Thesis")
    st.write(
        "The project asks whether a JEPA model can learn Microglia-PVM cell-state representations "
        "that preserve disease-relevant biology better than standard expression-only dimensionality "
        "reduction. The practical output is a ranked set of Alzheimer's gene-network hypotheses."
    )

    st.markdown("**Current v1 evidence**")
    c1, c2, c3 = st.columns(3)
    latent_summary = read_csv(TABLES / "latent_space_evaluation_jepa_vs_pca_summary.csv")
    multitarget_summary = read_csv(TABLES / "multitarget_oof_jepa_vs_pseudobulk_summary.csv")
    cell_mixing = read_csv(TABLES / "cell_level_mixing_metrics.csv")

    with c1:
        if latent_summary is not None:
            best_delta = latent_summary["delta_knn_spearman"].max()
            metric_delta("Best JEPA vs PCA neighborhood gain", best_delta, "kNN Spearman delta across pathology targets")
        else:
            show_missing(TABLES / "latent_space_evaluation_jepa_vs_pca_summary.csv")
    with c2:
        if multitarget_summary is not None:
            best_oof = multitarget_summary["jepa_minus_pseudobulk"].max()
            metric_delta("Best JEPA vs pseudobulk OOF gain", best_oof, "Pooled held-out donor Spearman delta")
        else:
            show_missing(TABLES / "multitarget_oof_jepa_vs_pseudobulk_summary.csv")
    with c3:
        if cell_mixing is not None:
            pca_acc = float(cell_mixing.loc[cell_mixing["representation"] == "expression_pca_128", "donor_knn_accuracy"].iloc[0])
            jepa_acc = float(cell_mixing.loc[cell_mixing["representation"] == "jepa_latent_128", "donor_knn_accuracy"].iloc[0])
            metric_delta("JEPA donor kNN accuracy reduction", jepa_acc - pca_acc, "Lower donor identity leakage is better")
        else:
            show_missing(TABLES / "cell_level_mixing_metrics.csv")

    st.markdown("**What each result means**")
    st.write(
        "PCA/UMAP plots show geometry. kNN and pooled OOF scores test whether neighborhoods predict pathology. "
        "Donor leakage metrics test whether the representation is merely memorizing patients. "
        "Counterfactual screens identify genes and modules the trained model relies on when predicting pathology."
    )

with representation_tab:
    st.subheader("PCA vs JEPA Latent Space")
    umap_df = read_csv(TABLES / "latent_space_umap_coordinates.csv")
    latent_summary = read_csv(TABLES / "latent_space_evaluation_jepa_vs_pca_summary.csv")
    cell_mixing = read_csv(TABLES / "cell_level_mixing_metrics.csv")

    if umap_df is not None:
        color_col = target if target in umap_df.columns else "percent AT8 positive area_Grey matter"
        fig = px.scatter(
            umap_df,
            x="x",
            y="y",
            color=color_col,
            facet_col="representation",
            hover_data=["Donor ID"],
            color_continuous_scale="Viridis",
            title=f"Donor-level UMAP colored by {TARGETS.get(color_col, {}).get('label', color_col)}",
        )
        fig.update_traces(marker={"size": 8, "opacity": 0.85})
        fig.update_layout(height=520)
        st.plotly_chart(fig, width="stretch")
    else:
        show_missing(TABLES / "latent_space_umap_coordinates.csv")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Donor-level neighborhood metrics**")
        if latent_summary is not None:
            display = latent_summary.sort_values("delta_knn_spearman", ascending=False)
            st.dataframe(display, hide_index=True, width="stretch")
        else:
            show_missing(TABLES / "latent_space_evaluation_jepa_vs_pca_summary.csv")
    with c2:
        st.markdown("**Cell-level donor leakage check**")
        if cell_mixing is not None:
            st.dataframe(cell_mixing, hide_index=True, width="stretch")
        else:
            show_missing(TABLES / "cell_level_mixing_metrics.csv")

with prediction_tab:
    st.subheader("Held-Out Donor Prediction")
    multitarget_summary = read_csv(TABLES / "multitarget_oof_jepa_vs_pseudobulk_summary.csv")
    if multitarget_summary is not None:
        plot_df = multitarget_summary.sort_values("jepa_minus_pseudobulk", ascending=False)
        fig = px.bar(
            plot_df,
            x="jepa_minus_pseudobulk",
            y="target",
            orientation="h",
            color="jepa_minus_pseudobulk",
            color_continuous_scale="RdBu",
            title="JEPA minus pseudobulk pooled OOF Spearman",
        )
        fig.update_layout(yaxis={"autorange": "reversed"}, height=520)
        st.plotly_chart(fig, width="stretch")
        st.dataframe(plot_df, hide_index=True, width="stretch")
    else:
        show_missing(TABLES / "multitarget_oof_jepa_vs_pseudobulk_summary.csv")

with counterfactual_tab:
    st.subheader(f"Model-Implied Counterfactuals: {target_info['label']}")
    gene_path = MULTITARGET / f"causal_fold_specific_two_pass_{target_slug}.csv"
    module_path = MULTITARGET / f"causal_fold_specific_two_pass_{target_slug}_modules.csv"
    gene_df = read_csv(gene_path)
    module_df = read_csv(module_path)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Top gene knockouts**")
        if gene_df is not None:
            top = gene_df.sort_values("abs_mean_donor_delta", ascending=False).head(20)
            fig = px.bar(
                top,
                x="mean_donor_delta",
                y="perturbation",
                orientation="h",
                color="mean_donor_delta",
                color_continuous_scale="RdBu",
            )
            fig.update_layout(yaxis={"autorange": "reversed"}, height=560)
            st.plotly_chart(fig, width="stretch")
            st.dataframe(top, hide_index=True, width="stretch")
        else:
            show_missing(gene_path)
    with c2:
        st.markdown("**Module knockouts**")
        if module_df is not None:
            top_modules = module_df.sort_values("abs_mean_donor_delta", ascending=False)
            fig = px.bar(
                top_modules,
                x="mean_donor_delta",
                y="perturbation",
                orientation="h",
                color="mean_donor_delta",
                color_continuous_scale="RdBu",
            )
            fig.update_layout(yaxis={"autorange": "reversed"}, height=560)
            st.plotly_chart(fig, width="stretch")
            st.dataframe(top_modules, hide_index=True, width="stretch")
        else:
            show_missing(module_path)

with latent_tab:
    st.subheader("JEPA Latent Factors")
    latent_weights = read_csv(TABLES / "pathology_latent_weights.csv")
    if latent_weights is not None:
        target_latents = latent_weights[latent_weights["target"] == target].sort_values("mean_abs_coefficient", ascending=False)
        top = target_latents.head(20)
        fig = px.bar(
            top,
            x="mean_coefficient",
            y="latent_dimension",
            orientation="h",
            color="mean_coefficient",
            color_continuous_scale="RdBu",
            title=f"Latent dimensions most predictive of {target_info['label']}",
        )
        fig.update_layout(yaxis={"autorange": "reversed"}, height=560)
        st.plotly_chart(fig, width="stretch")
        st.dataframe(top, hide_index=True, width="stretch")
    else:
        show_missing(TABLES / "pathology_latent_weights.csv")

with perturb_tab:
    st.subheader("External Perturbation Smoke Tests")
    st.write(
        "K562 Perturb-seq is used here only to test the benchmark machinery. "
        "The biologically meaningful next validation target is an iPSC-microglia or macrophage perturbation dataset."
    )
    k562 = read_csv(TABLES / "perturbseq_streaming_validation.csv")
    if k562 is not None:
        st.dataframe(k562, hide_index=True, width="stretch")
        if {"target_gene", "cosine_similarity"}.issubset(k562.columns):
            fig = px.bar(k562, x="target_gene", y="cosine_similarity", color="cosine_similarity", color_continuous_scale="RdBu")
            st.plotly_chart(fig, width="stretch")
    else:
        show_missing(TABLES / "perturbseq_streaming_validation.csv")

st.caption("Repository dashboard for SEA-AD JEPA v1 evaluation. Generated from lightweight CSV/SVG outputs in results/.")
