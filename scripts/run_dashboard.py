from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# --- PAGE CONFIGURATION & STYLING ---
st.set_page_config(
    page_title="Alzheimer's Causal Discovery Engine",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for a premium look
st.markdown("""
<style>
    .reportview-container {
        background: #0f1116;
    }
    .main {
        background: #0f1116;
        color: #e2e8f0;
        font-family: 'Inter', sans-serif;
    }
    h1, h2, h3 {
        color: #f1f5f9 !important;
        font-weight: 700 !important;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
        background-color: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #1e293b;
        border-radius: 8px 8px 0px 0px;
        color: #94a3b8;
        padding-left: 20px;
        padding-right: 20px;
        font-weight: 600;
        border: none;
    }
    .stTabs [aria-selected="true"] {
        background-color: #3b82f6 !important;
        color: #ffffff !important;
    }
    div[data-testid="stExpander"] {
        background-color: #1e293b;
        border: 1px solid #334155;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# Title Header
st.title("🧠 Myeloid Causal Discovery Engine")
st.markdown("""
*Translating PyTorch representation learning into actionable Alzheimer's therapeutic targets.*
***
""")

# --- TARGET CONFIGURATION ---
TARGETS_MAP = {
    "percent AT8 positive area_Grey matter": {
        "friendly_name": "Tau Tangles (IHC AT8)",
        "units": "% Area",
        "description": "Hyperphosphorylated tau neurofibrillary tangles, the primary driver of cognitive decline.",
        "layman_take_gene": "**Resting vs. Active Immune States**: Deleting genes that maintain the microglia homeostatic resting state (e.g., **P2RY12**, **CX3CR1**) reduces predicted Tau accumulation. This implies that microglia must be driven out of their resting state to actively clear pathological aggregates.",
        "layman_take_module": "**Vascular & Lipid Protection**: Lipid metabolism and vascular barrier modules show highly protective effects. Microglia supporting endothelial integrity and fat clearance are crucial barriers against tau propagation."
    },
    "percent 6e10 positive area_Grey matter": {
        "friendly_name": "Amyloid Plaques (IHC 6E10)",
        "units": "% Area",
        "description": "Extracellular amyloid-beta deposits forming senile plaques.",
        "layman_take_gene": "**Plaque Response Signaling**: Turning off genes in the plaque-response module alters amyloid deposition predictions, reflecting active clearance dynamics.",
        "layman_take_module": "**Phagocytic Clearance**: Lysosomal and phagocytic programs show protective causal scores, highlighting the role of phagocytosis in plaque removal."
    },
    "percent GFAP positive area_Grey matter": {
        "friendly_name": "Astrogliosis (IHC GFAP)",
        "units": "% Area",
        "description": "Reactive astrogliosis, reflecting neuroinflammatory tissue scarring.",
        "layman_take_gene": "**Neuroinflammatory Cascade**: Deleting reactive genes attenuates the predicted neuroinflammatory state, indicating a potential target to reduce brain scarring.",
        "layman_take_module": "**Glial Crosstalk**: Inflammatory signaling modules act as major drivers of reactive astrogliosis, highlighting immune-astrocyte communication."
    },
    "percent Iba1 positive area_Grey matter": {
        "friendly_name": "Microgliosis (IHC Iba1)",
        "units": "% Area",
        "description": "Microglial activation and proliferation.",
        "layman_take_gene": "**Proliferation Control**: Knocking out signaling receptors reduces predicted microglial density, indicating key nodes that control activation.",
        "layman_take_module": "**Homeostatic Feedback**: Homeostatic programs causally suppress microgliosis, keeping microglial activation in check."
    },
    "percent NeuN positive area_Grey matter": {
        "friendly_name": "Neuronal Density (IHC NeuN)",
        "units": "% Area",
        "description": "Marker of mature healthy neurons; lower density reflects neurodegeneration.",
        "layman_take_gene": "**The Synaptic Pruning Hazard**: Deleting complement-related genes (e.g., **CR1**, **C3**) leads to a *decrease* in predicted neuronal density. This implies that these genes are vital correlates of neuronal survival, and deleting them disrupts necessary structural feedback.",
        "layman_take_module": "**Pruning Safeguards**: Complement and pruning pathways show major contributions to neuronal prediction, indicating the model heavily links microglial immune pruning to neuronal survival."
    },
    "guhcl pTau_Grey matter": {
        "friendly_name": "Guanidine-soluble pTau (Biochemical)",
        "units": "pg/mg protein",
        "description": "Biochemically extracted hyperphosphorylated tau, representing insoluble cytoskeletal pathology.",
        "layman_take_gene": "**Phosphorylation Drivers**: Interferon and stress genes causally affect biochemical pTau, highlighting metabolic stress pathways.",
        "layman_take_module": "**Senescence & Stress**: Stress pathways show strong associations with biochemical tau changes."
    },
    "guhcl abeta42_Grey matter": {
        "friendly_name": "Guanidine-soluble Aβ42 (Biochemical)",
        "units": "pg/mg protein",
        "description": "Biochemically extracted insoluble amyloid-beta 42.",
        "layman_take_gene": "**Aβ Aggregation Control**: Core immune receptors causally influence abeta42 predictions.",
        "layman_take_module": "**Lipid and Clearance Pathways**: Insoluble amyloid accumulation is highly sensitive to lipid metabolism modules."
    },
    "ripa pTau_Grey matter": {
        "friendly_name": "RIPA-soluble pTau (Biochemical)",
        "units": "pg/mg protein",
        "description": "Soluble hyperphosphorylated tau, representing early-stage tau pathology.",
        "layman_take_gene": "**Early-stage Tau Phosphorylation**: Soluble tau levels are modulated by metabolic and homeostatic genes.",
        "layman_take_module": "**Interferon Signaling**: Early tau changes correlate with interferon-induced neuroinflammation."
    },
    "ripa abeta42_Grey matter": {
        "friendly_name": "RIPA-soluble Aβ42 (Biochemical)",
        "units": "pg/mg protein",
        "description": "Soluble amyloid-beta 42, the toxic oligomeric species.",
        "layman_take_gene": "**Oligomer Dynamics**: Oligomeric amyloid species predictions are highly sensitive to immune activation states.",
        "layman_take_module": "**Complement Clearance**: Complement modules are causally linked to soluble amyloid clearance."
    }
}


def slugify(name: str) -> str:
    return name.replace(" ", "_").replace("%", "percent").replace("/", "_").replace("+", "_plus_")


# --- DATA LOADING FUNCTIONS ---
@st.cache_data
def load_gene_ko(target_name: str) -> pd.DataFrame | None:
    slug = slugify(target_name)
    path = Path(f"results/tables/multitarget_causal/causal_fold_specific_two_pass_{slug}.csv")
    if path.exists():
        df = pd.read_csv(path)
        # Rename column for dashboard display
        if "abs_mean_donor_delta" in df.columns:
            return df.sort_values("abs_mean_donor_delta", ascending=False).reset_index(drop=True)
        return df
    return None


@st.cache_data
def load_module_ko(target_name: str) -> pd.DataFrame | None:
    slug = slugify(target_name)
    path = Path(f"results/tables/multitarget_causal/causal_fold_specific_two_pass_{slug}_modules.csv")
    if path.exists():
        return pd.read_csv(path)
    return None


@st.cache_data
def load_confounder_effects(target_name: str) -> pd.DataFrame | None:
    slug = slugify(target_name)
    path = Path(f"results/tables/multitarget_causal/confounder_adjusted_module_effects_{slug}.csv")
    if path.exists():
        return pd.read_csv(path)
    return None


@st.cache_data
def load_latent_weights() -> pd.DataFrame | None:
    path = Path("results/tables/pathology_latent_weights.csv")
    if path.exists():
        return pd.read_csv(path)
    return None


# --- SIDEBAR CONTROL PANEL ---
st.sidebar.title("🎮 Control Panel")
st.sidebar.write("Configure the target selection and parameters.")

selected_friendly = st.sidebar.selectbox(
    "Select Neuropathology Target:",
    options=[TARGETS_MAP[t]["friendly_name"] for t in TARGETS_MAP.keys()]
)

# Find the internal target name
target_key = None
for k, v in TARGETS_MAP.items():
    if v["friendly_name"] == selected_friendly:
        target_key = k
        break

target_config = TARGETS_MAP[target_key]
st.sidebar.markdown(f"**Description**:\n*{target_config['description']}*")
st.sidebar.markdown(f"**Biological Units**: `{target_config['units']}`")

# --- MAIN PAGE DETAILS ---
st.subheader(f"Analyzing Target: {selected_friendly}")
st.write(target_config["description"])

tab1, tab2, tab3 = st.tabs([
    "🧬 Digital Gene Knockouts", 
    "🧩 Systems Biology (Modules)", 
    "🔮 AI Latent Dimensions"
])

# --- TAB 1: GENE KNOCKOUTS ---
with tab1:
    st.markdown("### 🧬 Counterfactual Gene Knockouts")
    st.write(f"This chart displays the predicted impact of computationally knocking out individual microglia genes. The delta measures the change in prediction in raw biological units (`{target_config['units']}`).")
    
    gene_df = load_gene_ko(target_key)
    
    if gene_df is not None and not gene_df.empty:
        # Display top 15 genes
        top_genes = gene_df.head(15).copy()
        
        # Color coding for negative (protective/reducing) vs positive
        top_genes["Direction"] = top_genes["mean_donor_delta"].apply(
            lambda x: "Reduces Pathology" if x < 0 else "Increases Pathology"
        )
        
        fig_gene = px.bar(
            top_genes,
            x="mean_donor_delta",
            y="perturbation",
            orientation="h",
            color="Direction",
            title=f"Top 15 Microglia Genes Driving Predicted {selected_friendly}",
            labels={"mean_donor_delta": f"Causal Delta ({target_config['units']})", "perturbation": "Gene Name"},
            color_discrete_map={"Reduces Pathology": "#3b82f6", "Increases Pathology": "#ef4444"},
            category_orders={"perturbation": top_genes["perturbation"].tolist()}
        )
        fig_gene.update_layout(
            template="plotly_dark",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            yaxis=dict(autorange="reversed")
        )
        st.plotly_chart(fig_gene, use_container_width=True)
        
        # Table view
        with st.expander("📋 View Complete Gene Knockout Rankings"):
            st.dataframe(
                gene_df[["perturbation", "module", "mean_donor_delta", "bootstrap_ci_low", "bootstrap_ci_high", "fold_sign_consistency"]],
                column_config={
                    "perturbation": "Gene",
                    "module": "Microglia Module",
                    "mean_donor_delta": "Causal Delta",
                    "bootstrap_ci_low": "CI Low",
                    "bootstrap_ci_high": "CI High",
                    "fold_sign_consistency": "Fold Consistency"
                },
                hide_index=True
            )
            
        # Layman take
        st.markdown(f"""
        <div style="background-color: #1e293b; padding: 20px; border-radius: 8px; border-left: 5px solid #3b82f6; margin-top: 15px;">
            <h4>💡 Layman's Take on Gene Knockouts</h4>
            <p>{target_config['layman_take_gene']}</p>
        </div>
        """, unsafe_allow_html=True)
        
    else:
        st.warning("No gene knockout data found for this target.")

# --- TAB 2: MODULE-LEVEL CAUSATION VS CORRELATION ---
with tab2:
    st.markdown("### 🧩 Systems Biology: Modules")
    st.write("We compare the **Confounder-Adjusted Module Effects** (observational correlation controlled for clinical covariates) vs. **Counterfactual Module Knockouts** (causal deletion).")
    
    col1, col2 = st.columns(2)
    
    conf_df = load_confounder_effects(target_key)
    mod_df = load_module_ko(target_key)
    
    with col1:
        st.markdown("#### 🔍 Confounder-Adjusted Associations")
        st.write("Microglia modules adjusted for Age, Sex, APOE Genotype, and background embeddings.")
        if conf_df is not None and not conf_df.empty:
            conf_display = conf_df.copy()
            conf_display["Effect"] = conf_display["adjusted_slope"].apply(
                lambda x: "Positively Correlated" if x > 0 else "Negatively Correlated"
            )
            
            fig_conf = px.bar(
                conf_display,
                x="adjusted_slope",
                y="treatment",
                orientation="h",
                color="Effect",
                labels={"adjusted_slope": "Adjusted Regression Slope", "treatment": "Module"},
                color_discrete_map={"Positively Correlated": "#ef4444", "Negatively Correlated": "#10b981"},
                category_orders={"treatment": conf_display["treatment"].tolist()}
            )
            fig_conf.update_layout(
                template="plotly_dark",
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                yaxis=dict(autorange="reversed")
            )
            st.plotly_chart(fig_conf, use_container_width=True)
        else:
            st.warning("Confounder-adjusted data not found.")
            
    with col2:
        st.markdown("#### 🛠️ Counterfactual Module Deletions")
        st.write("The physical simulated impact on prediction when an entire module's expression is removed.")
        if mod_df is not None and not mod_df.empty:
            mod_display = mod_df.copy()
            mod_display["Direction"] = mod_display["mean_donor_delta"].apply(
                lambda x: "Reduces Pathology" if x < 0 else "Increases Pathology"
            )
            
            fig_mod = px.bar(
                mod_display,
                x="mean_donor_delta",
                y="perturbation",
                orientation="h",
                color="Direction",
                labels={"mean_donor_delta": f"Causal Delta ({target_config['units']})", "perturbation": "Module"},
                color_discrete_map={"Reduces Pathology": "#3b82f6", "Increases Pathology": "#f59e0b"},
                category_orders={"perturbation": mod_display["perturbation"].tolist()}
            )
            fig_mod.update_layout(
                template="plotly_dark",
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                yaxis=dict(autorange="reversed")
            )
            st.plotly_chart(fig_mod, use_container_width=True)
        else:
            st.warning("Counterfactual module deletion data not found.")
            
    # Layman take
    st.markdown(f"""
    <div style="background-color: #1e293b; padding: 20px; border-radius: 8px; border-left: 5px solid #10b981; margin-top: 15px;">
        <h4>💡 Layman's Take on Systems Biology</h4>
        <p>{target_config['layman_take_module']}</p>
    </div>
    """, unsafe_allow_html=True)

# --- TAB 3: AI LATENT DIMENSIONS ---
with tab3:
    st.markdown("### 🔮 AI Hidden Features (Latent Factors)")
    st.write("We fit linear Ridge regression models on the 128-dimensional JEPA embedding space. By checking which dimensions receive the highest absolute weights, we map the AI's internal 'super-features' back to physical pathology outcomes.")
    
    latent_df = load_latent_weights()
    if latent_df is not None and not latent_df.empty:
        # Filter for current target
        target_latent = latent_df[latent_df["target"] == target_key].copy()
        
        if not target_latent.empty:
            # Display top 10 latent dimensions
            top_latents = target_latent.head(10).copy()
            top_latents["Sign"] = top_latents["mean_coefficient"].apply(
                lambda x: "Positive Coefficient (+)" if x > 0 else "Negative Coefficient (-)"
            )
            
            fig_latent = px.bar(
                top_latents,
                x="mean_coefficient",
                y="latent_dimension",
                orientation="h",
                color="Sign",
                labels={"mean_coefficient": "Mean Ridge Coefficient", "latent_dimension": "Latent Factor"},
                color_discrete_map={"Positive Coefficient (+)": "#ec4899", "Negative Coefficient (-)": "#8b5cf6"},
                category_orders={"latent_dimension": top_latents["latent_dimension"].tolist()}
            )
            fig_latent.update_layout(
                template="plotly_dark",
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                yaxis=dict(autorange="reversed")
            )
            st.plotly_chart(fig_latent, use_container_width=True)
            
            # Layman take
            st.info("""
            **What is a Latent Dimension?** 
            The self-supervised PyTorch JEPA model compresses 3,000 genes into a 128-dimensional coordinate system. 
            The chart above shows which dimensions are the most important predictors of this pathology target. 
            
            For example, **jepa_63** is a major negative factor for both AT8 tau and NeuN density, indicating it represents an activation checkpoint that alters microglia biology across multiple pathological cascades.
            """)
        else:
            st.warning("No latent dimension data found matching this target.")
    else:
        st.warning("pathology_latent_weights.csv not found.")

st.markdown("---")
st.caption("Powered by the SEA-AD JEPA Causal Discovery Engine | Out-of-Fold Cross-Validated")
