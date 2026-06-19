"""Lock leakage-safe v3 donor folds and benchmark harness manifests.

Stage 24 is a harness-locking stage only. This script does not train v3,
does not run the full benchmark suite, does not run external validation, and
does not alter evidence levels. It creates deterministic donor-level folds,
target/baseline/package manifests, and lightweight smoke-test records for
Stage 25.
"""

from __future__ import annotations

import importlib
import importlib.metadata
import platform
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.model_selection import KFold, StratifiedKFold


ROOT = Path(__file__).resolve().parents[1]
TABLE_DIR = ROOT / "results" / "tables"
REPORT_DIR = ROOT / "results" / "reports"

INPUT_METADATA = TABLE_DIR / "sea_ad_full_metadata_targets_with_covariates.csv"

FOLDS_OUT = TABLE_DIR / "v3_locked_donor_folds_v1.csv"
TARGETS_OUT = TABLE_DIR / "v3_benchmark_target_manifest_v1.csv"
BASELINES_OUT = TABLE_DIR / "v3_benchmark_baseline_registry_v1.csv"
PACKAGES_OUT = TABLE_DIR / "v3_benchmark_runtime_package_status_v1.csv"
SMOKE_OUT = TABLE_DIR / "v3_benchmark_harness_smoke_test_v1.csv"
REPORT_OUT = REPORT_DIR / "v3_locked_benchmark_harness_v1.md"

SEED = 7
N_FOLDS = 5
RUNTIME_ENV = "sea-ad-jepa-v3"


TARGETS = [
    {
        "target_name": "AT8",
        "target_alias": "percent AT8 positive area_Grey matter",
        "target_type": "pathology_immunostaining",
    },
    {
        "target_name": "6e10/Aβ",
        "target_alias": "percent 6e10 positive area_Grey matter",
        "target_type": "pathology_immunostaining",
    },
    {
        "target_name": "GFAP",
        "target_alias": "percent GFAP positive area_Grey matter",
        "target_type": "gliosis_immunostaining",
    },
    {
        "target_name": "Iba1",
        "target_alias": "percent Iba1 positive area_Grey matter",
        "target_type": "microglia_immunostaining",
    },
    {
        "target_name": "NeuN",
        "target_alias": "percent NeuN positive area_Grey matter",
        "target_type": "neuronal_marker_immunostaining",
    },
]


PACKAGE_CHECKS = [
    ("sklearn", "sklearn", "linear/PCA baselines"),
    ("networkx", "networkx", "graph registry and graph controls"),
    ("numpy", "numpy", "array operations"),
    ("pandas", "pandas", "manifest generation"),
    ("scipy", "scipy", "scientific routines"),
    ("umap", "umap", "UMAP baseline"),
    ("openTSNE", "openTSNE", "t-SNE exploratory baseline"),
    ("phate", "phate", "PHATE exploratory baseline"),
    ("pydiffmap", "pydiffmap", "diffusion maps exploratory baseline"),
    ("torch", "torch", "v3 neural and deep baselines"),
    ("torch_geometric", "torch_geometric", "graph/v3 controls"),
    ("scanpy", "scanpy", "single-cell data handling"),
    ("anndata", "anndata", "single-cell data handling"),
    ("scvi", "scvi", "scVI/VAE baseline"),
    ("xgboost", "xgboost", "boosting baseline"),
    ("lightgbm", "lightgbm", "boosting baseline"),
    ("dowhy", "dowhy", "causal estimator layer"),
    ("econml", "econml", "causal estimator layer"),
]

PACKAGE_DISTS = {
    "sklearn": "scikit-learn",
    "umap": "umap-learn",
    "scvi": "scvi-tools",
}


@dataclass
class Baseline:
    baseline_id: str
    baseline_name: str
    baseline_family: str
    input_features: str
    requires_package: str
    leakage_risk: str
    leakage_safe_protocol: str
    primary_or_deferred: str
    v3_role: str
    notes: str


BASELINES = [
    Baseline(
        "raw_expression_ridge",
        "Raw expression ridge",
        "linear_expression",
        "train-fold donor/cell expression matrix",
        "sklearn",
        "low",
        "fit scaler/model on training donors only; evaluate held-out donors",
        "primary",
        "expression-only reference",
        "Primary leakage-safe baseline.",
    ),
    Baseline(
        "raw_expression_elasticnet",
        "Raw expression elastic net",
        "linear_expression",
        "train-fold donor/cell expression matrix",
        "sklearn",
        "low",
        "fit scaler/model and hyperparameters inside training donors only",
        "primary",
        "sparse expression reference",
        "Primary leakage-safe baseline.",
    ),
    Baseline(
        "pca_ridge",
        "PCA ridge",
        "linear_latent",
        "PCA components fit on training donors/cells",
        "sklearn",
        "low",
        "fit PCA on training donors/cells; transform held-out donors/cells",
        "primary",
        "linear dimensionality-control reference",
        "PCA is primary because sklearn PCA supports train-fit/test-transform.",
    ),
    Baseline(
        "pca_elasticnet",
        "PCA elastic net",
        "linear_latent",
        "PCA components fit on training donors/cells",
        "sklearn",
        "low",
        "fit PCA and ElasticNet inside training folds; transform held-out donors/cells",
        "primary",
        "sparse linear dimensionality-control reference",
        "Primary leakage-safe baseline.",
    ),
    Baseline(
        "module_mean_baseline",
        "Module mean baseline",
        "module_summary",
        "predefined module mean expression summaries",
        "numpy",
        "low",
        "use target-independent predefined modules; aggregate held-out donors without target access",
        "primary",
        "module-summary reference",
        "Primary if module definitions are target-independent.",
    ),
    Baseline(
        "wgcna_module_summary_ridge",
        "WGCNA module summary ridge",
        "module_summary",
        "WGCNA module eigengenes or means",
        "sklearn",
        "medium",
        "use precomputed target-independent WGCNA modules or recompute modules inside each training fold",
        "primary",
        "coexpression module reference",
        "Primary only with target-leakage-free module construction.",
    ),
    Baseline(
        "wgcna_module_summary_elasticnet",
        "WGCNA module summary elastic net",
        "module_summary",
        "WGCNA module eigengenes or means",
        "sklearn",
        "medium",
        "use precomputed target-independent WGCNA modules or recompute modules inside each training fold",
        "primary",
        "sparse coexpression module reference",
        "Primary only with target-leakage-free module construction.",
    ),
    Baseline(
        "xgboost_raw_expression",
        "XGBoost raw expression",
        "boosting_expression",
        "raw expression or screened training-fold expression features",
        "xgboost",
        "low",
        "feature screening, scaling, and model fitting occur inside training donors only",
        "primary",
        "nonlinear expression reference",
        "Primary leakage-safe boosting baseline.",
    ),
    Baseline(
        "lightgbm_raw_expression",
        "LightGBM raw expression",
        "boosting_expression",
        "raw expression or screened training-fold expression features",
        "lightgbm",
        "low",
        "feature screening, scaling, and model fitting occur inside training donors only",
        "primary",
        "nonlinear expression reference",
        "Primary leakage-safe boosting baseline.",
    ),
    Baseline(
        "tsne_knn_or_ridge",
        "t-SNE kNN/ridge",
        "manifold_embedding",
        "t-SNE coordinates",
        "openTSNE",
        "high",
        "exclude from primary unless a documented train-only fit plus valid held-out transform is used",
        "exploratory",
        "manifold visualization/control",
        "Standard t-SNE has no clean held-out transform; all-donor embedding is transductive.",
    ),
    Baseline(
        "umap_ridge_or_knn",
        "UMAP ridge/kNN",
        "manifold_embedding",
        "UMAP coordinates",
        "umap",
        "medium",
        "fit UMAP on training donors/cells and transform held-out donors/cells",
        "deferred",
        "manifold baseline",
        "Can become primary only with train-fit/test-transform protocol.",
    ),
    Baseline(
        "supervised_umap",
        "Supervised UMAP",
        "manifold_embedding",
        "supervised UMAP coordinates",
        "umap",
        "high",
        "must not use held-out target labels; train labels only if used at all",
        "exploratory",
        "leakage stress-test",
        "High leakage risk if test labels influence embedding.",
    ),
    Baseline(
        "phate_ridge_or_knn",
        "PHATE ridge/kNN",
        "manifold_embedding",
        "PHATE coordinates",
        "phate",
        "high",
        "exclude from primary unless a documented train/test transform protocol is used",
        "exploratory",
        "manifold baseline",
        "PHATE is leakage-sensitive under all-donor transductive embedding.",
    ),
    Baseline(
        "diffusion_maps_ridge_or_knn",
        "Diffusion maps ridge/kNN",
        "manifold_embedding",
        "diffusion map coordinates",
        "pydiffmap",
        "high",
        "exclude from primary unless a documented train/test transform protocol is used",
        "exploratory",
        "manifold baseline",
        "Diffusion maps are leakage-sensitive under all-donor transductive embedding.",
    ),
    Baseline(
        "autoencoder_latent_ridge",
        "Autoencoder latent ridge",
        "deep_expression_latent",
        "autoencoder latent variables",
        "torch",
        "medium",
        "train autoencoder only on training donors/cells; encode held-out donors/cells after training",
        "deferred",
        "deep expression-only comparator",
        "No neural training in Stage 24.",
    ),
    Baseline(
        "vae_or_scvi_latent_ridge",
        "VAE/scVI latent ridge",
        "deep_single_cell_latent",
        "VAE or scVI latent variables",
        "scvi",
        "medium",
        "train VAE/scVI only on training donors/cells; encode held-out donors/cells after training",
        "deferred",
        "single-cell latent comparator",
        "No scVI/VAE training in Stage 24.",
    ),
    Baseline(
        "expression_only_mlp",
        "Expression-only MLP",
        "deep_expression",
        "raw expression",
        "torch",
        "medium",
        "train MLP only on training donors/cells with held-out donors untouched",
        "deferred",
        "neural expression-only comparator",
        "No neural training in Stage 24.",
    ),
    Baseline(
        "module_only_mlp",
        "Module-only MLP",
        "deep_module",
        "module summaries",
        "torch",
        "medium",
        "train MLP only on training donors using leakage-free module summaries",
        "deferred",
        "neural module-only comparator",
        "No neural training in Stage 24.",
    ),
    Baseline(
        "graph_only_gnn",
        "Graph-only GNN",
        "graph_control",
        "graph topology/features without v3 perturbation heads",
        "torch_geometric",
        "medium",
        "train only on training donor folds; no held-out donor labels in graph supervision",
        "deferred",
        "graph contribution control",
        "Deferred until primary non-neural baselines are scored.",
    ),
    Baseline(
        "v3_no_graph",
        "v3 no-graph control",
        "v3_control",
        "v3 architecture with identity/no graph",
        "torch",
        "medium",
        "train only on training donor folds; compare against real graph and shuffled graph",
        "deferred",
        "ablation control",
        "No v3 training in Stage 24.",
    ),
    Baseline(
        "v3_strict_shuffled_graph",
        "v3 strict shuffled graph control",
        "v3_control",
        "v3 architecture with degree/constraint-aware shuffled graph",
        "torch_geometric",
        "medium",
        "train only on training donor folds using predeclared shuffled graph",
        "deferred",
        "topology control",
        "No v3 training in Stage 24.",
    ),
    Baseline(
        "v3_real_graph",
        "v3 real graph",
        "v3_model",
        "typed real graph with causal module-gated perturbation heads",
        "torch_geometric",
        "medium",
        "train only after baseline suite is locked and scored; donor folds fixed",
        "deferred",
        "candidate v3 model",
        "Do not start v3 neural model until baselines are locked and scored.",
    ),
    Baseline(
        "perturbation_latent_delta_baseline",
        "Perturbation latent delta baseline",
        "perturbation_baseline",
        "latent perturbation deltas",
        "numpy",
        "medium",
        "estimate perturbation deltas only from training donors; apply frozen rule to held-out donors",
        "deferred",
        "perturbation reference",
        "Requires Stage 25 protocol before scoring.",
    ),
    Baseline(
        "module_delta_perturbation_baseline",
        "Module delta perturbation baseline",
        "perturbation_baseline",
        "module perturbation deltas",
        "numpy",
        "medium",
        "estimate module deltas only from training donors; no held-out target use",
        "deferred",
        "module perturbation reference",
        "Requires Stage 25 protocol before scoring.",
    ),
    Baseline(
        "causal_inference_estimator_layer",
        "Causal inference estimator layer",
        "causal_optional",
        "confounder-adjusted target/module features",
        "dowhy;econml",
        "medium",
        "fit causal estimators on training donors only; report assumptions separately",
        "deferred",
        "causal analysis layer",
        "No causal claims from Stage 24 harness locking.",
    ),
]


def truthy(value: object) -> bool:
    if value is None:
        return False
    if isinstance(value, float) and np.isnan(value):
        return False
    text = str(value).strip()
    return bool(text) and text.lower() not in {"nan", "none", "na", ""}


def load_donor_metadata() -> pd.DataFrame:
    if not INPUT_METADATA.exists():
        raise FileNotFoundError(f"Missing required donor metadata table: {INPUT_METADATA}")
    df = pd.read_csv(INPUT_METADATA)
    if "Donor ID" not in df.columns:
        raise ValueError("Donor metadata table lacks `Donor ID` column")
    df = df.dropna(subset=["Donor ID"]).drop_duplicates(subset=["Donor ID"]).copy()
    df["Donor ID"] = df["Donor ID"].astype(str)
    return df


def build_pathology_stratum(df: pd.DataFrame) -> pd.Series:
    preferred = "Overall AD neuropathological Change"
    if preferred in df.columns:
        stratum = df[preferred].fillna("unknown").astype(str).str.strip()
        return stratum.replace("", "unknown")
    pieces = []
    for col in ["Braak", "Thal", "CERAD score"]:
        if col in df.columns:
            pieces.append(df[col].fillna("unknown").astype(str))
    if pieces:
        return pd.Series(["|".join(items) for items in zip(*pieces)], index=df.index)
    return pd.Series(["unknown"] * len(df), index=df.index)


def build_locked_folds(df: pd.DataFrame) -> pd.DataFrame:
    donor_ids = df["Donor ID"].astype(str).to_numpy()
    strata = build_pathology_stratum(df)
    n_splits = min(N_FOLDS, len(donor_ids))
    value_counts = strata.value_counts()
    can_stratify = n_splits >= 2 and len(value_counts) > 1 and value_counts.min() >= n_splits

    if can_stratify:
        splitter: Iterable[tuple[np.ndarray, np.ndarray]] = StratifiedKFold(
            n_splits=n_splits, shuffle=True, random_state=SEED
        ).split(donor_ids, strata)
        notes = "fixed_seed_7; stratified_by_overall_ad_neuropathological_change"
    else:
        splitter = KFold(n_splits=n_splits, shuffle=True, random_state=SEED).split(donor_ids)
        notes = "fixed_seed_7; kfold_fallback_due_to_small_or_imbalanced_strata"

    fold_assignments: dict[str, int] = {}
    for fold_id, (_, test_idx) in enumerate(splitter, start=1):
        for idx in test_idx:
            fold_assignments[donor_ids[idx]] = fold_id

    rows = []
    for _, row in df.sort_values("Donor ID").iterrows():
        donor_id = str(row["Donor ID"])
        availability = {
            "has_AT8": truthy(row.get("percent AT8 positive area_Grey matter")),
            "has_6e10_or_abeta": truthy(row.get("percent 6e10 positive area_Grey matter")),
            "has_GFAP": truthy(row.get("percent GFAP positive area_Grey matter")),
            "has_Iba1": truthy(row.get("percent Iba1 positive area_Grey matter")),
            "has_NeuN": truthy(row.get("percent NeuN positive area_Grey matter")),
        }
        rows.append(
            {
                "donor_id": donor_id,
                "fold_id": fold_assignments[donor_id],
                "split_role": "outer_fold_heldout",
                **availability,
                "diagnosis": row.get("Cognitive Status", ""),
                "sex": row.get("Sex", ""),
                "pathology_stratum": build_pathology_stratum(pd.DataFrame([row])).iloc[0],
                "n_available_targets": int(sum(availability.values())),
                "notes": notes,
            }
        )
    return pd.DataFrame(rows)


def build_target_manifest(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for target in TARGETS:
        alias = target["target_alias"]
        available = alias in df.columns
        n_donors = int(df[alias].notna().sum()) if available else 0
        rows.append(
            {
                "target_name": target["target_name"],
                "target_alias": alias,
                "available": available,
                "n_donors_with_target": n_donors,
                "target_type": target["target_type"],
                "used_for_primary_benchmark": available,
                "notes": "Preserved for v3 benchmark manifest; do not drop after seeing results."
                if available
                else "Target alias not found in metadata source.",
            }
        )
    return pd.DataFrame(rows)


def import_package(import_name: str) -> tuple[bool, str, str]:
    try:
        module = importlib.import_module(import_name)
        dist_name = PACKAGE_DISTS.get(import_name, import_name)
        try:
            version = importlib.metadata.version(dist_name)
        except importlib.metadata.PackageNotFoundError:
            version = str(getattr(module, "__version__", "unknown"))
        notes = ""
        if import_name == "torch":
            cuda_available = bool(module.cuda.is_available())
            cuda_version = getattr(module.version, "cuda", None)
            gpu_name = module.cuda.get_device_name(0) if cuda_available else ""
            notes = f"cuda_available={cuda_available}; torch_cuda={cuda_version}; gpu={gpu_name}"
        return True, version, notes
    except Exception as exc:
        return False, "", f"{type(exc).__name__}: {str(exc)[:240]}"


def build_package_status() -> pd.DataFrame:
    rows = []
    for package_name, import_name, needed_for in PACKAGE_CHECKS:
        available, version, notes = import_package(import_name)
        rows.append(
            {
                "package_name": package_name,
                "import_name": import_name,
                "available": available,
                "version": version,
                "needed_for": needed_for,
                "blocking_for_stage24": False,
                "notes": notes,
            }
        )
    return pd.DataFrame(rows)


def package_available(package_status: pd.DataFrame, requirement: str) -> bool:
    packages = [part.strip() for part in requirement.split(";") if part.strip()]
    available = {
        row["package_name"]: bool(row["available"])
        for _, row in package_status.iterrows()
    }
    return all(available.get(pkg, False) for pkg in packages)


def build_baseline_registry(package_status: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for baseline in BASELINES:
        pkg_ok = package_available(package_status, baseline.requires_package)
        immediately_runnable = (
            pkg_ok
            and baseline.primary_or_deferred == "primary"
            and baseline.leakage_risk in {"low", "medium"}
        )
        rows.append(
            {
                "baseline_id": baseline.baseline_id,
                "baseline_name": baseline.baseline_name,
                "baseline_family": baseline.baseline_family,
                "input_features": baseline.input_features,
                "requires_package": baseline.requires_package,
                "package_available": pkg_ok,
                "immediately_runnable": immediately_runnable,
                "leakage_risk": baseline.leakage_risk,
                "leakage_safe_protocol": baseline.leakage_safe_protocol,
                "primary_or_deferred": baseline.primary_or_deferred,
                "v3_role": baseline.v3_role,
                "notes": baseline.notes,
            }
        )
    return pd.DataFrame(rows)


def build_smoke_tests(
    folds: pd.DataFrame,
    targets: pd.DataFrame,
    baselines: pd.DataFrame,
    packages: pd.DataFrame,
) -> pd.DataFrame:
    tests = []
    fold_ids = [int(value) for value in sorted(folds["fold_id"].unique())]
    tests.append(
        {
            "test_name": "donor_folds_built",
            "status": "pass" if folds["donor_id"].nunique() > 0 and folds["fold_id"].nunique() >= 2 else "fail",
            "details": f"donors={folds['donor_id'].nunique()}; folds={fold_ids}",
            "blocking": True,
            "notes": "Donor-level held-out fold assignments only; no cell-level split.",
        }
    )
    tests.append(
        {
            "test_name": "target_manifest_built",
            "status": "pass" if targets["available"].all() and len(targets) == len(TARGETS) else "fail",
            "details": "; ".join(
                f"{row.target_name}:n={row.n_donors_with_target}" for row in targets.itertuples()
            ),
            "blocking": True,
            "notes": "All five pathology targets preserved before seeing benchmark results.",
        }
    )
    tests.append(
        {
            "test_name": "baseline_registry_leakage_labels",
            "status": "pass"
            if {"primary", "deferred", "exploratory"}.issubset(set(baselines["primary_or_deferred"]))
            else "fail",
            "details": baselines["primary_or_deferred"].value_counts().to_dict(),
            "blocking": True,
            "notes": "Registry distinguishes primary, deferred, and exploratory/leakage-sensitive baselines.",
        }
    )
    tests.append(
        {
            "test_name": "runtime_package_imports",
            "status": "pass" if packages["available"].all() else "fail",
            "details": f"available={int(packages['available'].sum())}/{len(packages)}",
            "blocking": True,
            "notes": f"Imports checked in runtime `{RUNTIME_ENV}`.",
        }
    )
    try:
        rng = np.random.default_rng(SEED)
        x = rng.normal(size=(12, 4))
        y = rng.normal(size=12)
        model = Ridge(alpha=1.0).fit(x[:8], y[:8])
        pred = model.predict(x[8:])
        ok = pred.shape == (4,) and np.isfinite(pred).all()
        tests.append(
            {
                "test_name": "tiny_synthetic_ridge_smoke",
                "status": "pass" if ok else "fail",
                "details": "fit 8 synthetic samples; predicted 4 held-out synthetic samples",
                "blocking": False,
                "notes": "Synthetic sklearn-only smoke test; not a biological benchmark result.",
            }
        )
    except Exception as exc:
        tests.append(
            {
                "test_name": "tiny_synthetic_ridge_smoke",
                "status": "fail",
                "details": f"{type(exc).__name__}: {exc}",
                "blocking": False,
                "notes": "Synthetic sklearn-only smoke test failed.",
            }
        )
    return pd.DataFrame(tests)


def write_report(
    folds: pd.DataFrame,
    targets: pd.DataFrame,
    baselines: pd.DataFrame,
    packages: pd.DataFrame,
    smoke: pd.DataFrame,
) -> None:
    primary = baselines[baselines["primary_or_deferred"] == "primary"]
    leakage_sensitive = baselines[baselines["leakage_risk"].isin(["medium", "high"])]
    package_summary = f"{int(packages['available'].sum())}/{len(packages)} packages import successfully"
    target_lines = [
        f"- {row.target_name} (`{row.target_alias}`): available={row.available}, donors={row.n_donors_with_target}"
        for row in targets.itertuples()
    ]
    primary_lines = [
        f"- `{row.baseline_id}`: {row.leakage_safe_protocol}"
        for row in primary.itertuples()
    ]
    leakage_lines = [
        f"- `{row.baseline_id}` ({row.leakage_risk}): {row.leakage_safe_protocol}"
        for row in leakage_sensitive.itertuples()
    ]
    smoke_lines = [
        f"- {row.test_name}: {row.status} ({row.details})"
        for row in smoke.itertuples()
    ]

    REPORT_OUT.write_text(
        "\n".join(
            [
                "# v3 locked donor folds and benchmark harness v1",
                "",
                "## 1. Executive summary",
                "",
                f"Stage 24 locked donor-level folds and the no-training benchmark harness for `Causal Module-Gated Typed Perturbation Graph-JEPA v3`. It created manifests only; no v3 training, full benchmark suite, external validation, evidence-level changes, candidate biology cards, or manuscript prose were run.",
                "",
                "## 2. Runtime used",
                "",
                f"- Runtime environment: `{RUNTIME_ENV}`",
                f"- Python: {platform.python_version()}",
                f"- Package status: {package_summary}",
                "",
                "## 3. Locked donor fold protocol",
                "",
                f"- Fold seed: `{SEED}`",
                f"- Requested/default folds: `{N_FOLDS}`",
                f"- Locked donors: `{folds['donor_id'].nunique()}`",
                f"- Actual folds: `{folds['fold_id'].nunique()}`",
                "- Split unit: donor only; Stage 25 must never split cells from the same donor across train/test.",
                "- Fold table stores each donor's held-out outer fold assignment. For fold k, train on all donors with `fold_id != k` and test on donors with `fold_id == k`.",
                "",
                "## 4. Target manifest",
                "",
                *target_lines,
                "",
                "All five pathology targets are preserved before seeing v3 benchmark results; targets must not be dropped post hoc.",
                "",
                "## 5. Primary benchmark baselines",
                "",
                *primary_lines,
                "",
                "## 6. Leakage-sensitive/deferred baselines",
                "",
                *leakage_lines,
                "",
                "Transductive embeddings over all donors/cells are exploratory only and excluded from the primary benchmark.",
                "",
                "## 7. Runtime package status",
                "",
                f"{package_summary}. See `results/tables/v3_benchmark_runtime_package_status_v1.csv` for versions and notes.",
                "",
                "## 8. Smoke-test results",
                "",
                *smoke_lines,
                "",
                "The tiny ridge smoke test is synthetic and is not a biological result.",
                "",
                "## 9. Recommended Stage 25 plan",
                "",
                "- Run the full baseline benchmark suite using these locked donor folds.",
                "- Start with raw expression, PCA, module/WGCNA, XGBoost, and LightGBM baselines.",
                "- Include UMAP/PHATE/diffusion/t-SNE only with clearly labeled leakage-safe or exploratory protocols.",
                "- Do not start the v3 neural model until baselines are locked and scored.",
                "",
                "## 10. Anti-leakage rules",
                "",
                "- Donor IDs define split boundaries; no cell leakage across donor folds.",
                "- All scaling, feature selection, PCA, module recomputation, manifold fitting, neural latent training, and causal fitting must occur inside training donors only.",
                "- Held-out donors may only be transformed or scored by artifacts fitted without their labels or cells.",
                "- WGCNA/module summaries are primary only if precomputed without target leakage or recomputed within training folds.",
                "- Supervised UMAP must not use test labels.",
                "- scVI/VAE baselines must be trained only on training folds if used for a primary benchmark.",
                "- Any all-donor/cell transductive embedding must be labeled exploratory and excluded from primary comparisons.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def main() -> None:
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    metadata = load_donor_metadata()
    folds = build_locked_folds(metadata)
    targets = build_target_manifest(metadata)
    packages = build_package_status()
    baselines = build_baseline_registry(packages)
    smoke = build_smoke_tests(folds, targets, baselines, packages)

    folds.to_csv(FOLDS_OUT, index=False)
    targets.to_csv(TARGETS_OUT, index=False)
    baselines.to_csv(BASELINES_OUT, index=False)
    packages.to_csv(PACKAGES_OUT, index=False)
    smoke.to_csv(SMOKE_OUT, index=False)
    write_report(folds, targets, baselines, packages, smoke)

    print(f"Wrote {FOLDS_OUT}")
    print(f"Wrote {TARGETS_OUT}")
    print(f"Wrote {BASELINES_OUT}")
    print(f"Wrote {PACKAGES_OUT}")
    print(f"Wrote {SMOKE_OUT}")
    print(f"Wrote {REPORT_OUT}")


if __name__ == "__main__":
    main()
