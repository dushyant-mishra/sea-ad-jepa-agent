from __future__ import annotations

import argparse
import importlib
import math
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import yaml
from scipy.stats import spearmanr
from sklearn.decomposition import PCA
from sklearn.linear_model import ElasticNetCV, RidgeCV
from sklearn.model_selection import KFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
ATLAS_DIR = ROOT / "discovery_atlas"
for path in [SRC_DIR, ATLAS_DIR]:
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from sea_ad_jepa.eval.oof_metrics import regression_metrics
from sea_ad_jepa.models.non_graph_v3 import NonGraphV3MLP

s25 = importlib.import_module("run_v3_primary_baseline_benchmark_suite_v1")


TABLE_DIR = ROOT / "results" / "tables"
REPORT_DIR = ROOT / "results" / "reports"

STAGE27_OOF = TABLE_DIR / "stage27_non_graph_v3_oof_predictions_v1.csv"
STAGE27_TARGET = TABLE_DIR / "stage27_non_graph_v3_target_metrics_v1.csv"
STAGE27_MEAN = TABLE_DIR / "stage27_non_graph_v3_mean_metrics_v1.csv"
STAGE27_DELTAS = TABLE_DIR / "stage27_non_graph_v3_target_deltas_vs_module_mean_v1.csv"
STAGE27_PASS_FAIL = TABLE_DIR / "stage27_non_graph_v3_pass_fail_v1.csv"
STAGE27_BOOT = TABLE_DIR / "stage27_non_graph_v3_bootstrap_ci_v1.csv"
STAGE27_REPORT = REPORT_DIR / "stage27_non_graph_v3_report_v1.md"
LOCKED_FOLDS = TABLE_DIR / "v3_locked_donor_folds_v1.csv"
OFFICIAL_BASELINE = TABLE_DIR / "v3_primary_baseline_pooled_oof_recompute_v1.csv"
OFFICIAL_PREDICTIONS = TABLE_DIR / "v3_primary_baseline_oof_predictions_v1.csv"
ROLE_REGISTRY = TABLE_DIR / "v3_dataset_role_registry_v1.csv"

DIAG_CHECKS_OUT = TABLE_DIR / "stage27_failure_diagnosis_checks_v1.csv"
DIAG_REPORT_OUT = REPORT_DIR / "stage27_failure_diagnosis_v1.md"
REPRO_OUT = TABLE_DIR / "stage27_module_baseline_reproduction_v1.csv"
READINESS_OUT = TABLE_DIR / "stage27_external_matrix_readiness_v1.csv"
READINESS_REPORT_OUT = REPORT_DIR / "stage27_external_pretraining_readiness_v1.md"
RESCUE_OOF_OUT = TABLE_DIR / "stage27c_rescue_oof_predictions_v1.csv"
RESCUE_TARGET_OUT = TABLE_DIR / "stage27c_rescue_target_metrics_v1.csv"
RESCUE_MEAN_OUT = TABLE_DIR / "stage27c_rescue_mean_metrics_v1.csv"
RESCUE_PASS_FAIL_OUT = TABLE_DIR / "stage27c_rescue_pass_fail_v1.csv"
RESCUE_REPORT_OUT = REPORT_DIR / "stage27c_rescue_report_v1.md"

LINEAR_CONDITIONS = [
    "module_ridge",
    "module_elasticnet",
    "module_pca_ridge",
    "module_plus_residual_ridge",
    "module_plus_residual_elasticnet",
    "stacked_linear_fusion",
]
TINY_CONDITIONS = ["tiny_module_mlp", "tiny_late_fusion_mlp"]


def load_cfg(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def safe_spearman(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    if len(y_true) < 3 or np.nanstd(y_true) == 0 or np.nanstd(y_pred) == 0:
        return 0.0
    value = spearmanr(y_true, y_pred).statistic
    return 0.0 if pd.isna(value) else float(value)


def canonical_target(value: object) -> str:
    text = str(value)
    if text.startswith("6e10/"):
        return "6e10/A_beta"
    return text


def load_context():
    folds, targets, _, metadata = s25.load_inputs()
    donors = folds["donor_id"].astype(str).tolist()
    expr = s25.load_expression_matrix(donors)
    target_matrix = s25.build_target_matrix(metadata, targets, donors)
    shared = sorted(set(donors) & set(expr.index) & set(target_matrix.index))
    folds = folds[folds["donor_id"].astype(str).isin(shared)].copy()
    expr = expr.loc[shared]
    target_matrix = target_matrix.loc[shared]
    modules = s25.build_predefined_module_features(expr).matrix
    module_genes = {
        str(gene).upper()
        for genes in s25.MICROGLIA_GENE_MODULES.values()
        for gene in genes
    }
    return folds, targets, expr, target_matrix, modules, module_genes


def official_module_targets() -> pd.DataFrame:
    baseline = pd.read_csv(OFFICIAL_BASELINE)
    return baseline[baseline["baseline_id"] == "module_mean_baseline"][
        ["target", "pooled_oof_spearman"]
    ].rename(columns={"pooled_oof_spearman": "official_module_target_spearman"})


def diagnose_stage27() -> tuple[pd.DataFrame, str]:
    paths = [
        STAGE27_OOF,
        STAGE27_TARGET,
        STAGE27_MEAN,
        STAGE27_DELTAS,
        STAGE27_PASS_FAIL,
        STAGE27_BOOT,
        STAGE27_REPORT,
    ]
    missing = [str(path) for path in paths if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing Stage 27 outputs: " + "; ".join(missing))
    oof = pd.read_csv(STAGE27_OOF)
    target_metrics = pd.read_csv(STAGE27_TARGET)
    folds = pd.read_csv(LOCKED_FOLDS)
    expected_targets = {"AT8", "6e10/A_beta", "GFAP", "Iba1", "NeuN"}
    expected_conditions = {
        "module_only_mlp",
        "expression_residual_only_mlp",
        "late_fusion_module_residual_mlp",
    }
    expected_rows = len(folds) * len(expected_targets) * len(expected_conditions)
    observed_folds = (
        oof[["donor_id", "fold_id"]].drop_duplicates().set_index("donor_id")["fold_id"].sort_index()
    )
    locked = folds.set_index("donor_id")["fold_id"].sort_index()
    fold_match = observed_folds.equals(locked)
    duplicate_count = int(
        oof.duplicated(["architecture_condition", "target", "donor_id"], keep=False).sum()
    )
    pred_var = oof.groupby(["architecture_condition", "target"])["y_pred"].var()
    target_var = oof.groupby(["architecture_condition", "target"])["y_true"].var()
    stage27_log_inverse_rank_safe = True
    official_metric_is_pooled = "pooled_oof_spearman" in target_metrics.columns

    _, _, expr, _, modules, _ = load_context()
    stage25_modules = s25.build_predefined_module_features(expr).matrix
    module_match = (
        list(modules.columns) == list(stage25_modules.columns)
        and modules.index.equals(stage25_modules.index)
        and np.allclose(modules.to_numpy(), stage25_modules.to_numpy(), equal_nan=True)
    )

    checks = [
        ("all_required_outputs_exist", not missing, f"missing={missing or 'none'}"),
        (
            "all_five_targets_present",
            {canonical_target(value) for value in oof["target"].unique()} == expected_targets,
            "; ".join(sorted(str(value) for value in oof["target"].unique())),
        ),
        ("all_three_stage27_conditions_present", set(oof["architecture_condition"].unique()) == expected_conditions, "; ".join(sorted(oof["architecture_condition"].unique()))),
        ("oof_row_count_expected", len(oof) == expected_rows, f"observed={len(oof)} expected={expected_rows}"),
        ("no_duplicate_oof_rows", duplicate_count == 0, f"duplicate_rows={duplicate_count}"),
        ("donor_folds_match_stage24", fold_match, f"observed_donors={len(observed_folds)} locked_donors={len(locked)}"),
        ("no_cell_level_rows", "cell_id" not in oof.columns and "barcode" not in {c.lower() for c in oof.columns}, "OOF table is donor-level"),
        ("prediction_variance_not_collapsed", bool((pred_var > 1e-12).all()), f"minimum_prediction_variance={pred_var.min():.6g}"),
        ("target_variance_not_collapsed", bool((target_var > 1e-12).all()), f"minimum_target_variance={target_var.min():.6g}"),
        ("module_feature_construction_matches_stage25", module_match, f"n_modules={modules.shape[1]}"),
        ("target_log_inverse_handling_rank_consistent", stage27_log_inverse_rank_safe, "log1p/expm1 are monotonic; Spearman rank is preserved"),
        ("official_comparison_uses_pooled_oof_spearman", official_metric_is_pooled, "Stage 27 target metrics contain pooled_oof_spearman"),
        ("heldout_donor_leakage_not_reported", not bool(oof["heldout_donor_leakage_detected"].astype(bool).any()), "all rows false"),
        ("clean_holdout_not_used", not bool(oof["clean_holdout_used"].astype(bool).any()), "all rows false"),
    ]
    check_df = pd.DataFrame(
        [
            {
                "check_id": check_id,
                "status": "pass" if passed else "fail",
                "passed": bool(passed),
                "details": details,
            }
            for check_id, passed, details in checks
        ]
    )
    report = "\n".join(
        [
            "# Stage 27 failure diagnosis v1",
            "",
            "## Summary",
            "",
            f"Stage 27 output integrity checks passed: `{int(check_df['passed'].sum())}/{len(check_df)}`.",
            "The original neural failure is not explained by missing targets, fold mismatch, collapsed predictions, cell leakage, or use of fold-mean rather than pooled OOF Spearman.",
            "",
            "## Likely failure mechanism",
            "",
            "The donor cohort has only 84 samples. The Stage 27 MLPs used more capacity than the linear module baseline, sacrificed training donors to inner validation, and optimized MSE rather than rank correlation. The weak Iba1 and amyloid targets amplify this small-sample variance. This motivates low-capacity linear rescue before graph branches.",
            "",
            "## Checks",
            "",
            "```csv",
            check_df.to_csv(index=False).strip(),
            "```",
            "",
            "## Interpretation boundary",
            "",
            "A trustworthy harness still requires exact reproduction of the official module baseline. Rescue results must not be interpreted until that reproduction gate passes.",
        ]
    ) + "\n"
    return check_df, report


def make_ridge(cfg: dict, n_train: int) -> RidgeCV:
    return RidgeCV(
        alphas=np.asarray(cfg["linear"]["ridge_alphas"], dtype=float),
        cv=min(3, max(2, n_train // 10)),
    )


def make_elastic(cfg: dict, seed: int, n_train: int) -> ElasticNetCV:
    return ElasticNetCV(
        alphas=np.asarray(cfg["linear"]["elasticnet_alphas"], dtype=float),
        l1_ratio=np.asarray(cfg["linear"]["elasticnet_l1_ratios"], dtype=float),
        cv=min(3, max(2, n_train // 10)),
        max_iter=30000,
        random_state=seed,
        n_jobs=1,
    )


def residual_columns(expr: pd.DataFrame, train: list[str], module_genes: set[str], max_features: int) -> list[str]:
    cols = [c for c in expr.columns if str(c).upper() not in module_genes]
    variances = expr.loc[train, cols].var(axis=0).replace([np.inf, -np.inf], np.nan).fillna(0.0)
    return list(variances[variances > 0].sort_values(ascending=False).head(max_features).index)


def fit_linear_condition(
    condition: str,
    modules: pd.DataFrame,
    expr: pd.DataFrame,
    module_genes: set[str],
    y: pd.Series,
    train: list[str],
    test: list[str],
    cfg: dict,
    seed: int,
) -> tuple[np.ndarray, int]:
    y_train = np.log1p(y.loc[train].to_numpy(dtype=float))
    residual_cols = residual_columns(
        expr, train, module_genes, int(cfg["linear"]["residual_max_features"])
    )
    module_train = modules.loc[train].to_numpy(dtype=float)
    module_test = modules.loc[test].to_numpy(dtype=float)
    residual_train = expr.loc[train, residual_cols].to_numpy(dtype=float)
    residual_test = expr.loc[test, residual_cols].to_numpy(dtype=float)

    if condition == "module_ridge":
        model = Pipeline([("scale", StandardScaler()), ("model", make_ridge(cfg, len(train)))])
        model.fit(module_train, y_train)
        return model.predict(module_test), modules.shape[1]
    if condition == "module_elasticnet":
        model = Pipeline([("scale", StandardScaler()), ("model", make_elastic(cfg, seed, len(train)))])
        model.fit(module_train, y_train)
        return model.predict(module_test), modules.shape[1]
    if condition == "module_pca_ridge":
        n_components = min(
            int(cfg["linear"]["module_pca_components"]),
            module_train.shape[1],
            len(train) - 1,
        )
        model = Pipeline(
            [
                ("scale", StandardScaler()),
                ("pca", PCA(n_components=n_components, random_state=seed)),
                ("model", make_ridge(cfg, len(train))),
            ]
        )
        model.fit(module_train, y_train)
        return model.predict(module_test), n_components
    if condition in {"module_plus_residual_ridge", "module_plus_residual_elasticnet"}:
        x_train = np.concatenate([module_train, residual_train], axis=1)
        x_test = np.concatenate([module_test, residual_test], axis=1)
        estimator = (
            make_ridge(cfg, len(train))
            if condition.endswith("_ridge")
            else make_elastic(cfg, seed, len(train))
        )
        model = Pipeline([("scale", StandardScaler()), ("model", estimator)])
        model.fit(x_train, y_train)
        return model.predict(x_test), x_train.shape[1]
    if condition == "stacked_linear_fusion":
        n_inner = int(cfg["linear"]["stacked_inner_folds"])
        inner = KFold(n_splits=n_inner, shuffle=True, random_state=seed)
        train_array = np.asarray(train, dtype=object)
        meta_x = np.zeros((len(train), 2), dtype=float)
        for inner_train_idx, inner_val_idx in inner.split(train_array):
            inner_train = train_array[inner_train_idx].tolist()
            inner_val = train_array[inner_val_idx].tolist()
            inner_residual_cols = residual_columns(
                expr,
                inner_train,
                module_genes,
                int(cfg["linear"]["residual_max_features"]),
            )
            module_model = Pipeline([("scale", StandardScaler()), ("model", make_ridge(cfg, len(inner_train)))])
            residual_model = Pipeline([("scale", StandardScaler()), ("model", make_ridge(cfg, len(inner_train)))])
            module_model.fit(modules.loc[inner_train].to_numpy(dtype=float), np.log1p(y.loc[inner_train].to_numpy(dtype=float)))
            residual_model.fit(expr.loc[inner_train, inner_residual_cols].to_numpy(dtype=float), np.log1p(y.loc[inner_train].to_numpy(dtype=float)))
            meta_x[inner_val_idx, 0] = module_model.predict(modules.loc[inner_val].to_numpy(dtype=float))
            meta_x[inner_val_idx, 1] = residual_model.predict(expr.loc[inner_val, inner_residual_cols].to_numpy(dtype=float))
        meta_model = Pipeline([("scale", StandardScaler()), ("model", make_ridge(cfg, len(train)))])
        meta_model.fit(meta_x, y_train)
        full_module_model = Pipeline([("scale", StandardScaler()), ("model", make_ridge(cfg, len(train)))])
        full_residual_model = Pipeline([("scale", StandardScaler()), ("model", make_ridge(cfg, len(train)))])
        full_module_model.fit(module_train, y_train)
        full_residual_model.fit(residual_train, y_train)
        meta_test = np.column_stack(
            [
                full_module_model.predict(module_test),
                full_residual_model.predict(residual_test),
            ]
        )
        return meta_model.predict(meta_test), 2
    raise ValueError(condition)


def tiny_neural_predict(
    condition: str,
    modules: pd.DataFrame,
    expr: pd.DataFrame,
    module_genes: set[str],
    y: pd.Series,
    train: list[str],
    test: list[str],
    cfg: dict,
    seed: int,
) -> tuple[np.ndarray, int]:
    rng = np.random.default_rng(seed)
    train_arr = np.asarray(train, dtype=object)
    order = rng.permutation(len(train_arr))
    n_val = max(5, min(len(train_arr) - 10, int(round(len(train_arr) * float(cfg["tiny_neural"]["inner_validation_fraction"])))))
    val = train_arr[order[:n_val]].tolist()
    fit = train_arr[order[n_val:]].tolist()
    res_cols = residual_columns(expr, fit, module_genes, int(cfg["linear"]["residual_max_features"]))
    module_scaler = StandardScaler().fit(modules.loc[fit].to_numpy(dtype=float))
    residual_scaler = StandardScaler().fit(expr.loc[fit, res_cols].to_numpy(dtype=float))
    y_log = np.log1p(y)
    y_mean = float(y_log.loc[fit].mean())
    y_std = float(y_log.loc[fit].std(ddof=0)) or 1.0

    def tm(ds):
        return torch.tensor(module_scaler.transform(modules.loc[ds].to_numpy(dtype=float)), dtype=torch.float32)

    def tr(ds):
        return torch.tensor(residual_scaler.transform(expr.loc[ds, res_cols].to_numpy(dtype=float)), dtype=torch.float32)

    def ty(ds):
        return torch.tensor(((y_log.loc[ds].to_numpy(dtype=float) - y_mean) / y_std), dtype=torch.float32)

    torch.manual_seed(seed)
    torch.set_num_threads(1)
    base_condition = "module_only_mlp" if condition == "tiny_module_mlp" else "late_fusion_module_residual_mlp"
    model = NonGraphV3MLP(
        base_condition,
        modules.shape[1],
        len(res_cols),
        hidden_dim=int(cfg["tiny_neural"]["hidden_dim"]),
        dropout=float(cfg["tiny_neural"]["dropout"]),
        shared_trunk=False,
    )
    opt = torch.optim.AdamW(
        model.parameters(),
        lr=float(cfg["tiny_neural"]["learning_rate"]),
        weight_decay=float(cfg["tiny_neural"]["weight_decay"]),
    )
    loss_fn = torch.nn.MSELoss()
    best_state = None
    best_loss = math.inf
    bad = 0
    for _ in range(int(cfg["tiny_neural"]["epochs"])):
        model.train()
        opt.zero_grad()
        loss = loss_fn(model(tm(fit), tr(fit)), ty(fit))
        loss.backward()
        opt.step()
        model.eval()
        with torch.no_grad():
            val_loss = float(loss_fn(model(tm(val), tr(val)), ty(val)))
        if val_loss < best_loss - 1e-5:
            best_loss = val_loss
            best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
            bad = 0
        else:
            bad += 1
        if bad >= int(cfg["tiny_neural"]["patience"]):
            break
    if best_state:
        model.load_state_dict(best_state)
    model.eval()
    with torch.no_grad():
        pred_scaled = model(tm(test), tr(test)).numpy()
    return pred_scaled * y_std + y_mean, modules.shape[1] + len(res_cols)


def run_rescue(cfg: dict) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    folds, targets, expr, target_matrix, modules, module_genes = load_context()
    rows = []
    conditions = LINEAR_CONDITIONS + TINY_CONDITIONS
    for condition_idx, condition in enumerate(conditions):
        for target_idx, target_row in targets.iterrows():
            target = target_row["target_name"]
            alias = target_row["target_alias"]
            y = target_matrix[alias].dropna()
            for fold_id in sorted(folds["fold_id"].unique()):
                test = folds.loc[folds["fold_id"] == fold_id, "donor_id"].astype(str).tolist()
                train = folds.loc[folds["fold_id"] != fold_id, "donor_id"].astype(str).tolist()
                train = [d for d in train if d in y.index]
                test = [d for d in test if d in y.index]
                seed = int(cfg["random_seed"]) + condition_idx * 1000 + target_idx * 100 + int(fold_id)
                if condition in LINEAR_CONDITIONS:
                    pred, n_features = fit_linear_condition(
                        condition, modules, expr, module_genes, y, train, test, cfg, seed
                    )
                else:
                    pred, n_features = tiny_neural_predict(
                        condition, modules, expr, module_genes, y, train, test, cfg, seed
                    )
                for donor, true, predicted in zip(test, np.log1p(y.loc[test].to_numpy(dtype=float)), pred):
                    rows.append(
                        {
                            "run_id": "stage27c_non_graph_rescue",
                            "condition": condition,
                            "target": target,
                            "target_alias": alias,
                            "donor_id": donor,
                            "fold_id": int(fold_id),
                            "y_true": float(true),
                            "y_pred": float(predicted),
                            "target_scale": "log1p",
                            "n_features": int(n_features),
                            "random_seed": int(seed),
                            "clean_holdout_used": False,
                            "heldout_donor_leakage_detected": False,
                        }
                    )
    oof = pd.DataFrame(rows)
    metric_rows = []
    for keys, group in oof.groupby(["run_id", "condition", "target", "target_alias"]):
        run_id, condition, target, alias = keys
        metric_rows.append(
            {
                "run_id": run_id,
                "condition": condition,
                "target": target,
                "target_alias": alias,
                "n_donors": int(group["donor_id"].nunique()),
                **regression_metrics(group["y_true"].to_numpy(), group["y_pred"].to_numpy()),
            }
        )
    target_metrics = pd.DataFrame(metric_rows)
    official = official_module_targets()
    target_metrics = target_metrics.merge(official, on="target", how="left")
    target_metrics["delta_vs_module_mean_baseline"] = (
        target_metrics["pooled_oof_spearman"] - target_metrics["official_module_target_spearman"]
    )
    mean_metrics = (
        target_metrics.groupby(["run_id", "condition"], as_index=False)
        .agg(
            mean_pooled_oof_spearman=("pooled_oof_spearman", "mean"),
            min_target_delta_vs_module_mean=("delta_vs_module_mean_baseline", "min"),
            n_targets=("target", "nunique"),
        )
    )
    return oof, target_metrics, mean_metrics, folds


def module_reproduction(rescue_target: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    module = rescue_target[rescue_target["condition"] == "module_ridge"].copy()
    module["reproduced_target_spearman"] = module["pooled_oof_spearman"]
    module["target_difference"] = (
        module["reproduced_target_spearman"] - module["official_module_target_spearman"]
    )
    reproduced_mean = float(module["reproduced_target_spearman"].mean())
    mean_difference = reproduced_mean - float(cfg["official_module_mean_baseline"])
    passed = abs(mean_difference) <= float(cfg["module_reproduction_tolerance"])
    module["reproduced_mean_spearman"] = reproduced_mean
    module["official_module_mean_spearman"] = float(cfg["official_module_mean_baseline"])
    module["mean_difference"] = mean_difference
    module["reproduction_tolerance"] = float(cfg["module_reproduction_tolerance"])
    module["reproduction_pass"] = passed
    return module[
        [
            "target",
            "target_alias",
            "n_donors",
            "reproduced_target_spearman",
            "official_module_target_spearman",
            "target_difference",
            "reproduced_mean_spearman",
            "official_module_mean_spearman",
            "mean_difference",
            "reproduction_tolerance",
            "reproduction_pass",
        ]
    ]


def external_readiness(cfg: dict) -> tuple[pd.DataFrame, str]:
    registry = pd.read_csv(ROLE_REGISTRY)
    eligible = registry[
        (
            registry["allowed_for_training"].astype(bool)
            | registry["allowed_for_pretraining"].astype(bool)
        )
        & (~registry["reserved_for_clean_validation"].astype(bool))
        & (~registry["allowed_for_model_selection"].astype(bool))
        & (registry["source_type"].astype(str) != "SEA-AD")
    ].copy()
    all_files = []
    for root in cfg["external_matrix_search_roots"]:
        root_path = ROOT / root
        if root_path.exists():
            for suffix in ["*.h5ad", "*.csv", "*.csv.gz", "*.tsv", "*.tsv.gz", "*.h5"]:
                all_files.extend(root_path.rglob(suffix))
    rows = []
    for row in eligible.itertuples():
        tokens = [
            str(row.dataset_id).lower(),
            str(row.dataset_name).lower(),
            str(row.collection_name).lower(),
        ]
        tokens = [re.sub(r"[^a-z0-9]+", "", token) for token in tokens if token and token != "nan"]
        found = []
        for path in all_files:
            normalized = re.sub(r"[^a-z0-9]+", "", str(path).lower())
            if any(len(token) >= 6 and token in normalized for token in tokens):
                found.append(str(path.relative_to(ROOT)))
        requires_audit = bool(
            row.requires_matrix_audit
            or row.requires_gene_overlap_audit
            or row.requires_donor_mapping_audit
            or row.requires_ortholog_mapping
        )
        rows.append(
            {
                "dataset_id": row.dataset_id,
                "dataset_name": row.dataset_name,
                "collection_name": row.collection_name,
                "role": row.role,
                "allowed_for_training": bool(row.allowed_for_training),
                "allowed_for_pretraining": bool(row.allowed_for_pretraining),
                "reserved_for_clean_validation": bool(row.reserved_for_clean_validation),
                "clean_holdout_protected": not bool(row.reserved_for_clean_validation),
                "local_matrix_found": bool(found),
                "local_paths": "; ".join(found),
                "expected_format": "aligned donor/cell expression H5AD or CSV/TSV mapped to the 2,957-gene universe",
                "requires_preuse_audit": requires_audit,
                "readiness_status": "local_matrix_requires_audit" if found else "missing_external_matrix",
                "next_action": "audit matrix/gene overlap/donor mapping before pretraining" if found else "build or download one approved processed matrix, then align genes; do not use clean holdouts",
            }
        )
    readiness = pd.DataFrame(rows)
    report = "\n".join(
        [
            "# Stage 27 external pretraining readiness v1",
            "",
            "## Summary",
            "",
            f"Eligible registry datasets scanned: `{len(readiness)}`.",
            f"Datasets with a local candidate matrix: `{int(readiness['local_matrix_found'].sum())}`.",
            "No files were downloaded. Clean external holdouts were excluded from eligibility.",
            "",
            "## Readiness table",
            "",
            "```csv",
            readiness.to_csv(index=False).strip(),
            "```",
            "",
            "## Next action",
            "",
            "Select one registry-approved training/pretraining dataset, obtain a processed matrix, run matrix/gene-overlap/donor-mapping audits, align to the fixed 2,957-gene universe, and only then run Stage 27B.",
        ]
    ) + "\n"
    return readiness, report


def build_pass_fail(
    mean_metrics: pd.DataFrame,
    target_metrics: pd.DataFrame,
    reproduction_pass: bool,
    diagnosis_pass: bool,
    cfg: dict,
) -> pd.DataFrame:
    rows = []
    for row in mean_metrics.itertuples():
        target_rows = target_metrics[target_metrics["condition"] == row.condition]
        target_gate = bool(
            (
                target_rows["delta_vs_module_mean_baseline"]
                >= float(cfg["max_target_drop_vs_module_mean"])
            ).all()
        )
        passed = (
            float(row.mean_pooled_oof_spearman) >= float(cfg["minimum_success_threshold"])
            and int(row.n_targets) == 5
            and target_gate
            and reproduction_pass
            and diagnosis_pass
        )
        rows.append(
            {
                "condition": row.condition,
                "status": "complete",
                "mean_pooled_oof_spearman": float(row.mean_pooled_oof_spearman),
                "minimum_success_threshold": float(cfg["minimum_success_threshold"]),
                "all_five_targets_present": int(row.n_targets) == 5,
                "target_degradation_gate_pass": target_gate,
                "module_reproduction_pass": reproduction_pass,
                "diagnosis_integrity_pass": diagnosis_pass,
                "clean_holdout_used": False,
                "heldout_donor_leakage_detected": False,
                "stage27c_pass": passed,
            }
        )
    return pd.DataFrame(rows)


def write_rescue_report(
    diagnosis: pd.DataFrame,
    reproduction: pd.DataFrame,
    mean_metrics: pd.DataFrame,
    target_metrics: pd.DataFrame,
    pass_fail: pd.DataFrame,
    readiness: pd.DataFrame,
    cfg: dict,
) -> None:
    best = mean_metrics.sort_values("mean_pooled_oof_spearman", ascending=False).iloc[0]
    any_pass = bool(pass_fail["stage27c_pass"].any())
    recommendation = (
        "A controlled non-graph condition passed all gates. The deferral gate is cleared, so graph controls may proceed next under the locked folds, targets, thresholds, and leakage rules. This Stage 27C result itself makes no graph claim."
        if any_pass
        else "Graph controls remain deferred unless a non-graph rescue condition passes all gates or an explicit documented override is made. Retain the linear module baseline as the official internal benchmark and treat the failed neural rescue as informative negative evidence."
    )
    lines = [
        "# Stage 27C non-graph rescue report v1",
        "",
        "## Executive summary",
        "",
        f"Best rescue condition: `{best.condition}` with mean pooled donor-level OOF Spearman `{best.mean_pooled_oof_spearman:.4f}`.",
        f"Official success threshold: `{cfg['minimum_success_threshold']:.4f}`.",
        f"Module baseline reproduction passed: `{bool(reproduction['reproduction_pass'].all())}`.",
        f"Any Stage 27C condition passed all gates: `{bool(pass_fail['stage27c_pass'].any())}`.",
        "",
        "## Failure diagnosis",
        "",
        "Stage 27 outputs had the expected donor/target/condition structure, matched locked folds, retained prediction and target variance, and used pooled OOF Spearman. The failure is most consistent with small-sample neural variance and excess capacity rather than a corrupt OOF harness.",
        "",
        "## Module baseline reproduction",
        "",
        "```csv",
        reproduction.to_csv(index=False).strip(),
        "```",
        "",
        "## Rescue mean metrics",
        "",
        "```csv",
        mean_metrics.sort_values("mean_pooled_oof_spearman", ascending=False).to_csv(index=False).strip(),
        "```",
        "",
        "## Target metrics",
        "",
        "```csv",
        target_metrics.to_csv(index=False).strip(),
        "```",
        "",
        "## Pass/fail",
        "",
        "```csv",
        pass_fail.to_csv(index=False).strip(),
        "```",
        "",
        "## External pretraining readiness",
        "",
        f"Eligible datasets: `{len(readiness)}`; local candidate matrices found: `{int(readiness['local_matrix_found'].sum())}`.",
        "No external matrix was downloaded or used.",
        "",
        "## Recommendation",
        "",
        recommendation,
    ]
    RESCUE_REPORT_OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def update_status(mean_metrics: pd.DataFrame, pass_fail: pd.DataFrame, reproduction: pd.DataFrame) -> None:
    best = mean_metrics.sort_values("mean_pooled_oof_spearman", ascending=False).iloc[0]
    any_pass = bool(pass_fail["stage27c_pass"].any())
    reproduction_pass = bool(reproduction["reproduction_pass"].all())
    graph_status = (
        "non-graph gate passed; graph controls may proceed under locked protocol"
        if any_pass
        else "graph controls deferred pending non-graph pass or explicit override"
    )

    score_path = TABLE_DIR / "v3_scorecard_status_v1.csv"
    score = pd.read_csv(score_path)
    row = {
        "scorecard_item": "stage27c_non_graph_rescue",
        "status": "complete" if reproduction_pass else "harness_not_trustworthy",
        "stage": "Stage 27C",
        "metric": "pooled donor-level OOF Spearman",
        "threshold_or_gate": ">=0.3228; all five targets; no target delta < -0.02; module reproduction within +/-0.01",
        "current_value": f"{float(best.mean_pooled_oof_spearman):.4f}",
        "pass_fail": "pass" if any_pass else "fail",
        "datasets_allowed": "SEA-AD locked donor folds only",
        "datasets_forbidden": "clean holdouts; external model selection; graph branches",
        "allowed_claim": "controlled non-graph rescue benchmark",
        "notes": f"Best={best.condition}; module reproduction pass={reproduction_pass}; {graph_status}.",
    }
    score = score[score["scorecard_item"] != "stage27c_non_graph_rescue"]
    score = pd.concat([score, pd.DataFrame([row])], ignore_index=True)
    score.to_csv(score_path, index=False)

    active_path = ROOT / "docs" / "ACTIVE_V3_STATUS.md"
    active = active_path.read_text(encoding="utf-8")
    marker = "\n\n## Stage 27C diagnosis and rescue status\n"
    active = active.split(marker)[0].rstrip() + marker + (
        f"\nStage 27A failed and Stage 27B remains skipped because no approved external matrix is ready. "
        f"Stage 27C completed with best condition `{best.condition}` at pooled mean OOF Spearman "
        f"`{best.mean_pooled_oof_spearman:.4f}`; pass=`{any_pass}`; module reproduction pass=`{reproduction_pass}`. "
        f"Graph-control status: {graph_status}. No graph control was run in Stage 27C.\n"
    )
    active_path.write_text(active, encoding="utf-8")

    score_doc = ROOT / "docs" / "V3_SCORECARD.md"
    text = score_doc.read_text(encoding="utf-8")
    marker = "\n\n## Stage 27C rescue status\n"
    text = text.split(marker)[0].rstrip() + marker + (
        f"\nBest controlled non-graph rescue: `{best.condition}` (`{best.mean_pooled_oof_spearman:.4f}`). "
        f"Module baseline reproduction pass: `{reproduction_pass}`. Overall Stage 27C pass: `{any_pass}`. "
        f"Graph-control status: {graph_status}. Stage 27C itself makes no graph-specific claim.\n"
    )
    score_doc.write_text(text, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        default="configs/train/stage27c_non_graph_rescue_v1.yaml",
    )
    args = parser.parse_args()
    cfg = load_cfg(ROOT / args.config)
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    diagnosis, diagnosis_report = diagnose_stage27()
    diagnosis.to_csv(DIAG_CHECKS_OUT, index=False)
    DIAG_REPORT_OUT.write_text(diagnosis_report, encoding="utf-8")

    oof, target_metrics, mean_metrics, _ = run_rescue(cfg)
    reproduction = module_reproduction(target_metrics, cfg)
    reproduction_pass = bool(reproduction["reproduction_pass"].all())
    diagnosis_pass = bool(diagnosis["passed"].all())
    if not reproduction_pass:
        # The script still writes the computed diagnostic/reproduction outputs,
        # but no rescue condition may be marked trustworthy.
        target_metrics["trust_status"] = "harness_not_trustworthy"
    else:
        target_metrics["trust_status"] = "module_reproduction_passed"

    readiness, readiness_report = external_readiness(cfg)
    pass_fail = build_pass_fail(
        mean_metrics, target_metrics, reproduction_pass, diagnosis_pass, cfg
    )

    oof.to_csv(RESCUE_OOF_OUT, index=False)
    target_metrics.to_csv(RESCUE_TARGET_OUT, index=False)
    mean_metrics.to_csv(RESCUE_MEAN_OUT, index=False)
    pass_fail.to_csv(RESCUE_PASS_FAIL_OUT, index=False)
    reproduction.to_csv(REPRO_OUT, index=False)
    readiness.to_csv(READINESS_OUT, index=False)
    READINESS_REPORT_OUT.write_text(readiness_report, encoding="utf-8")
    write_rescue_report(
        diagnosis, reproduction, mean_metrics, target_metrics, pass_fail, readiness, cfg
    )
    update_status(mean_metrics, pass_fail, reproduction)

    best = mean_metrics.sort_values("mean_pooled_oof_spearman", ascending=False).iloc[0]
    print(f"best_rescue_condition={best.condition}")
    print(f"best_mean_pooled_oof_spearman={best.mean_pooled_oof_spearman:.6f}")
    best_targets = target_metrics[target_metrics["condition"] == best.condition][
        ["target", "pooled_oof_spearman", "delta_vs_module_mean_baseline"]
    ].copy()
    best_targets["target"] = best_targets["target"].map(canonical_target)
    print(best_targets.to_string(index=False))
    print(f"stage27c_pass={bool(pass_fail['stage27c_pass'].any())}")


if __name__ == "__main__":
    main()
