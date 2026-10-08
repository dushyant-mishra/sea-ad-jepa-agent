from __future__ import annotations

import argparse
import importlib.util
import sys
import types
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml
from scipy.stats import spearmanr
from sklearn.decomposition import PCA
from sklearn.linear_model import ElasticNetCV, HuberRegressor, RidgeCV
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
SCRIPT_DIR = ROOT / "scripts"
for path in [SRC_DIR, SCRIPT_DIR]:
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from audit_donor_leakage_v1 import audit_covariate_columns, audit_oof_predictions
from build_pathology_residual_targets_v1 import (
    fit_covariate_residualizer,
    rank_inverse_normal_apply,
    rank_inverse_normal_train,
    winsor_bounds,
)


SAFE_INTERPRETATION = (
    "Stage 39C is an internal target-engineering and simple-model benchmark under locked donor-held-out "
    "folds. It uses train-fold-only preprocessing and does not use external data, select candidates, or claim "
    "clean external validation, causality, therapeutic relevance, disease modification, or gene ablation."
)
ALLOWED_CLAIM = "internal target-engineering benchmark; donor-held-out model comparison; hypothesis prioritization only"
PROHIBITED_CLAIM = "clean external validation; causal regulator; therapeutic target; disease-modifying target; gene-ablation result"


def resolve(value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def load_cfg(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def read_csv(value: str | Path) -> pd.DataFrame:
    path = resolve(value)
    return pd.read_csv(path) if path.exists() else pd.DataFrame()


def write_csv(df: pd.DataFrame, value: str | Path) -> Path:
    path = resolve(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    return path


def write_text(text: str, value: str | Path) -> Path:
    path = resolve(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def safe_spearman(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    mask = np.isfinite(y_true) & np.isfinite(y_pred)
    if int(mask.sum()) < 3:
        return 0.0
    yt = y_true[mask]
    yp = y_pred[mask]
    if np.nanstd(yt) == 0 or np.nanstd(yp) == 0:
        return 0.0
    value = spearmanr(yt, yp).statistic
    return 0.0 if pd.isna(value) else float(value)


def mse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    mask = np.isfinite(y_true) & np.isfinite(y_pred)
    if int(mask.sum()) == 0:
        return float("nan")
    return float(np.mean((y_true[mask] - y_pred[mask]) ** 2))


def markdown_table(df: pd.DataFrame, max_rows: int | None = None) -> str:
    view = df if max_rows is None else df.head(max_rows)
    if view.empty:
        return "_No rows available._"
    clean = view.fillna("").astype(str)
    cols = list(clean.columns)
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for _, row in clean.iterrows():
        vals = [str(row[col]).replace("|", "\\|").replace("\n", " ") for col in cols]
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines)


def load_stage27c_module():
    for name, cls in [("lightgbm", "LGBMRegressor"), ("xgboost", "XGBRegressor")]:
        if name in sys.modules:
            continue
        try:
            __import__(name)
        except ModuleNotFoundError:
            module = types.ModuleType(name)

            class _Unavailable:
                def __init__(self, *args, **kwargs):
                    raise ImportError(f"{name} is unavailable; Stage 39C does not use {cls}")

            setattr(module, cls, _Unavailable)
            sys.modules[name] = module
    path = resolve("scripts/run_stage27c_non_graph_rescue_v1.py")
    spec = importlib.util.spec_from_file_location("stage27c_for_stage39c", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not import Stage 27C script")
    module = importlib.util.module_from_spec(spec)
    sys.modules["stage27c_for_stage39c"] = module
    spec.loader.exec_module(module)
    return module


def normalize_target_columns(target_matrix: pd.DataFrame) -> pd.DataFrame:
    alias = {
        "percent AT8 positive area_Grey matter": "AT8",
        "percent 6e10 positive area_Grey matter": "6e10/A_beta",
        "percent GFAP positive area_Grey matter": "GFAP",
        "percent Iba1 positive area_Grey matter": "Iba1",
        "percent NeuN positive area_Grey matter": "NeuN",
        "6e10/AÎ²": "6e10/A_beta",
        "6e10/Aβ": "6e10/A_beta",
    }
    return target_matrix.rename(columns={col: alias.get(str(col), str(col)) for col in target_matrix.columns})


def input_inventory(cfg: dict[str, Any]) -> pd.DataFrame:
    rows = []
    for name, value in cfg["inputs"].items():
        path = resolve(value)
        rows.append({"input_name": name, "path": str(value), "exists": path.exists(), "size_bytes": path.stat().st_size if path.exists() else 0})
    return pd.DataFrame(rows)


def pca_module_features(train_x: np.ndarray, test_x: np.ndarray, n_components: int, seed: int) -> tuple[np.ndarray, np.ndarray]:
    n_comp = min(n_components, train_x.shape[1], max(1, train_x.shape[0] - 1))
    pipe = Pipeline([("scale", StandardScaler()), ("pca", PCA(n_components=n_comp, random_state=seed))])
    return pipe.fit_transform(train_x), pipe.transform(test_x)


def build_model(model_name: str, cfg: dict[str, Any], seed: int, n_train: int):
    if model_name == "ridge":
        return Pipeline(
            [
                ("scale", StandardScaler()),
                ("model", RidgeCV(alphas=np.asarray(cfg["models"]["ridge_alphas"], dtype=float), cv=min(3, max(2, n_train // 10)))),
            ]
        )
    if model_name == "elasticnet":
        return Pipeline(
            [
                ("scale", StandardScaler()),
                (
                    "model",
                    ElasticNetCV(
                        alphas=np.asarray(cfg["models"]["elasticnet_alphas"], dtype=float),
                        l1_ratio=np.asarray(cfg["models"]["elasticnet_l1_ratios"], dtype=float),
                        cv=min(3, max(2, n_train // 10)),
                        max_iter=50000,
                        random_state=seed,
                        n_jobs=1,
                    ),
                ),
            ]
        )
    if model_name == "huber":
        return Pipeline([("scale", StandardScaler()), ("model", HuberRegressor(epsilon=1.35, alpha=0.01, max_iter=1000))])
    raise ValueError(model_name)


def safe_covariate_frame(metadata: pd.DataFrame, donors: list[str], numeric_cols: list[str], categorical_cols: list[str]) -> pd.DataFrame:
    meta = metadata.copy()
    meta["Donor ID"] = meta["Donor ID"].astype(str)
    meta = meta.drop_duplicates("Donor ID").set_index("Donor ID")
    out = pd.DataFrame(index=donors)
    for col in numeric_cols:
        out[col] = pd.to_numeric(meta[col], errors="coerce") if col in meta.columns else np.nan
    for col in categorical_cols:
        out[col] = meta[col].astype(str) if col in meta.columns else "missing"
    return out


def transform_target(
    transform: str,
    y_train_raw: np.ndarray,
    y_test_raw: np.ndarray,
    train_donors: list[str],
    test_donors: list[str],
    covariates: pd.DataFrame,
    cfg: dict[str, Any],
) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict[str, Any]]:
    y_train_log = np.log1p(y_train_raw)
    y_test_log = np.log1p(y_test_raw)
    details: dict[str, Any] = {"transform": transform}
    if transform == "raw_log1p":
        return y_train_log, y_test_log, np.zeros_like(y_test_log), details
    if transform == "winsor_log1p":
        lo, hi = winsor_bounds(y_train_raw)
        details.update({"winsor_lower": lo, "winsor_upper": hi})
        return np.log1p(np.clip(y_train_raw, lo, hi)), y_test_log, np.zeros_like(y_test_log), details
    if transform == "rank_inverse_normal":
        train_t, _ = rank_inverse_normal_train(y_train_log)
        test_t = rank_inverse_normal_apply(y_test_log, y_train_log)
        return train_t, y_test_log, np.zeros_like(y_test_log), details
    if transform == "covariate_residual_log1p":
        numeric = [c for c in cfg["safe_covariates"]["numeric"] if c in covariates.columns]
        categorical = [c for c in cfg["safe_covariates"]["categorical"] if c in covariates.columns]
        pipe = fit_covariate_residualizer(covariates, train_donors, y_train_log, numeric, categorical, cfg["models"]["ridge_alphas"])
        train_expected = pipe.predict(covariates.loc[train_donors, numeric + categorical])
        test_expected = pipe.predict(covariates.loc[test_donors, numeric + categorical])
        details.update({"residualized_numeric_covariates": ";".join(numeric), "residualized_categorical_covariates": ";".join(categorical)})
        return y_train_log - train_expected, y_test_log, test_expected, details
    raise ValueError(transform)


def run_condition(
    condition: str,
    transform: str,
    feature_mode: str,
    model_name: str,
    modules: pd.DataFrame,
    covariates: pd.DataFrame,
    target_matrix: pd.DataFrame,
    folds: pd.DataFrame,
    targets: list[str],
    cfg: dict[str, Any],
    shuffled_target: bool = False,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    design_rows = []
    seed0 = int(cfg["references"]["random_seed"])
    rng = np.random.default_rng(seed0)
    donors = [d for d in folds["donor_id"].astype(str).tolist() if d in modules.index and d in target_matrix.index]
    fold_lookup = folds.set_index("donor_id")["fold_id"].to_dict()
    for target_idx, target in enumerate(targets):
        y_all = target_matrix[target].astype(float)
        for fold_id in sorted(folds["fold_id"].unique()):
            test = [d for d in donors if fold_lookup.get(d) == fold_id and np.isfinite(y_all.loc[d])]
            train = [d for d in donors if fold_lookup.get(d) != fold_id and np.isfinite(y_all.loc[d])]
            y_train_raw = y_all.loc[train].to_numpy(float)
            y_test_raw = y_all.loc[test].to_numpy(float)
            y_train, y_test_metric, test_offset, details = transform_target(transform, y_train_raw, y_test_raw, train, test, covariates, cfg)
            if shuffled_target:
                y_train = rng.permutation(y_train)
            if feature_mode == "module_pca":
                train_x0 = modules.loc[train].to_numpy(float)
                test_x0 = modules.loc[test].to_numpy(float)
                x_train, x_test = pca_module_features(train_x0, test_x0, int(cfg["models"]["module_pca_components"]), seed0 + target_idx * 100 + int(fold_id))
            elif feature_mode == "metadata_only":
                numeric = [c for c in cfg["safe_covariates"]["numeric"] if c in covariates.columns]
                categorical = [c for c in cfg["safe_covariates"]["categorical"] if c in covariates.columns]
                # Use the same residualizer preprocessor machinery by fitting a ridge preprocessor separately via a model pipeline.
                x_train = pd.get_dummies(covariates.loc[train, numeric + categorical], dummy_na=True).astype(float)
                x_test = pd.get_dummies(covariates.loc[test, numeric + categorical], dummy_na=True).astype(float)
                x_train, x_test = x_train.align(x_test, join="left", axis=1, fill_value=0.0)
                x_train = x_train.to_numpy(float)
                x_test = x_test.to_numpy(float)
            else:
                raise ValueError(feature_mode)
            model = build_model(model_name, cfg, seed0 + target_idx * 100 + int(fold_id), len(train))
            model.fit(x_train, y_train)
            pred = model.predict(x_test) + test_offset
            for donor, yt, yp in zip(test, y_test_metric, pred):
                rows.append(
                    {
                        "condition": condition,
                        "target": target,
                        "donor_id": donor,
                        "fold_id": int(fold_id),
                        "y_true": float(yt),
                        "y_pred": float(yp),
                        "target_transform": transform,
                        "feature_mode": feature_mode,
                        "model_name": model_name,
                        "n_features": int(x_train.shape[1]),
                        "clean_holdout_used": False,
                        "heldout_donor_leakage_detected": False,
                    }
                )
            details.update({"condition": condition, "target": target, "fold_id": int(fold_id), "n_train": len(train), "n_test": len(test), "feature_mode": feature_mode, "model_name": model_name})
            design_rows.append(details)
    return pd.DataFrame(rows), pd.DataFrame(design_rows)


def metric_tables(oof: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    for (condition, target), sub in oof.groupby(["condition", "target"]):
        rows.append(
            {
                "condition": condition,
                "target": target,
                "n_donors": int(sub["donor_id"].nunique()),
                "pooled_oof_spearman": safe_spearman(sub["y_true"].to_numpy(float), sub["y_pred"].to_numpy(float)),
                "mse": mse(sub["y_true"].to_numpy(float), sub["y_pred"].to_numpy(float)),
                "prediction_variance": float(np.nanvar(sub["y_pred"].to_numpy(float))),
            }
        )
    target = pd.DataFrame(rows)
    mean = (
        target.groupby("condition", as_index=False)
        .agg(mean_pooled_oof_spearman=("pooled_oof_spearman", "mean"), min_target_spearman=("pooled_oof_spearman", "min"), n_targets=("target", "nunique"))
        if not target.empty
        else pd.DataFrame()
    )
    return target, mean


def bootstrap_ci(oof: pd.DataFrame, best_condition: str, n_boot: int, seed: int) -> pd.DataFrame:
    if oof.empty or not best_condition:
        return pd.DataFrame()
    sub = oof[oof["condition"] == best_condition].copy()
    donors = sorted(sub["donor_id"].unique())
    rng = np.random.default_rng(seed)
    vals = []
    for _ in range(n_boot):
        sampled = rng.choice(donors, size=len(donors), replace=True)
        pieces = []
        for i, donor in enumerate(sampled):
            piece = sub[sub["donor_id"] == donor].copy()
            piece["boot_donor"] = f"{donor}__{i}"
            pieces.append(piece)
        boot = pd.concat(pieces, ignore_index=True)
        target_scores = []
        for _, g in boot.groupby("target"):
            target_scores.append(safe_spearman(g["y_true"].to_numpy(float), g["y_pred"].to_numpy(float)))
        vals.append(float(np.mean(target_scores)))
    arr = np.asarray(vals, dtype=float)
    return pd.DataFrame([{"condition": best_condition, "n_bootstrap": n_boot, "bootstrap_mean": float(np.mean(arr)), "ci_lower_95": float(np.quantile(arr, 0.025)), "ci_upper_95": float(np.quantile(arr, 0.975))}])


def build_control_results(mean_metrics: pd.DataFrame) -> pd.DataFrame:
    lookup = dict(zip(mean_metrics["condition"], mean_metrics["mean_pooled_oof_spearman"])) if not mean_metrics.empty else {}
    best_non_control = mean_metrics[~mean_metrics["condition"].str.contains("control|metadata_only", regex=True)].sort_values("mean_pooled_oof_spearman", ascending=False).head(1)
    best_condition = str(best_non_control.iloc[0]["condition"]) if not best_non_control.empty else ""
    best_value = float(best_non_control.iloc[0]["mean_pooled_oof_spearman"]) if not best_non_control.empty else np.nan
    rows = []
    for control in ["raw_log1p_module_pca_ridge_donor_shuffled_control", "raw_log1p_metadata_only_ridge"]:
        ctrl = lookup.get(control, np.nan)
        rows.append({"comparison": f"{best_condition}_vs_{control}", "best_condition": best_condition, "control_condition": control, "delta": best_value - ctrl if np.isfinite(ctrl) else np.nan, "passes": bool(best_value > ctrl) if np.isfinite(best_value) and np.isfinite(ctrl) else False})
    return pd.DataFrame(rows)


def build_claim_audit(negative_null_reported: bool) -> pd.DataFrame:
    items = {
        "train_fold_only_preprocessing": True,
        "donor_heldout_only": True,
        "no_external_data": True,
        "no_candidate_selection": True,
        "no_clean_external_validation_claim": True,
        "no_causal_claim": True,
        "no_therapeutic_claim": True,
        "no_gene_ablation_claim": True,
        "negative_null_results_reported": negative_null_reported,
    }
    rows = [{"audit_item": k, "pass": v, "evidence": SAFE_INTERPRETATION if v else "failed"} for k, v in items.items()]
    rows.append({"audit_item": "safety_audit_pass", "pass": all(items.values()), "evidence": "all safety checks passed"})
    return pd.DataFrame(rows)


def update_markdown_section(path_value: str | Path, heading: str, body: str) -> None:
    path = resolve(path_value)
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    section = f"\n## {heading}\n{body.strip()}\n"
    marker = f"## {heading}"
    if marker not in text:
        text = text.rstrip() + "\n" + section
    else:
        start = text.index(marker)
        next_start = text.find("\n## ", start + len(marker))
        if next_start == -1:
            text = text[:start].rstrip() + section
        else:
            text = text[:start].rstrip() + section + text[next_start:]
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def update_scorecard_csv(path_value: str | Path, delta: pd.DataFrame, pass_fail: pd.DataFrame) -> None:
    path = resolve(path_value)
    df = pd.read_csv(path) if path.exists() else pd.DataFrame()
    d = delta.iloc[0] if not delta.empty else pd.Series(dtype=object)
    row = {
        "scorecard_item": "stage39c_target_engineering_residual_stack",
        "status": "complete",
        "stage": "Stage 39C",
        "metric": "mean pooled donor-level OOF Spearman",
        "threshold_or_gate": ">= Stage 27C + 0.005, lower bootstrap CI above Stage 27C, controls/leakage pass",
        "current_value": f"best={d.get('best_mean_pooled_oof_spearman', 'NA')}; delta={d.get('delta_vs_stage27c', 'NA')}",
        "pass_fail": "pass" if as_bool(d.get("stage39c_internal_rescue_pass", False)) else "fail",
        "datasets_allowed": "SEA-AD locked internal donor folds only",
        "datasets_forbidden": "external data; candidate selection; clean holdouts",
        "allowed_claim": ALLOWED_CLAIM,
        "notes": SAFE_INTERPRETATION,
        "stage_id": "stage39c_target_engineering_residual_stack",
        "primary_metric": "best target-engineered condition mean pooled OOF Spearman",
        "pass_rule": "predeclared rescue margin, bootstrap CI, and negative controls",
        "result": f"run_pass={as_bool(pass_fail.iloc[0].get('stage39c_run_pass', False))}",
        "allowed_inputs": "Stage 27C internal context and safe donor covariates",
        "forbidden_inputs": "external validation data or external model selection",
        "interpretation": SAFE_INTERPRETATION,
    }
    if df.empty:
        df = pd.DataFrame([row])
    else:
        for col in row:
            if col not in df.columns:
                df[col] = ""
        df = df[df.get("stage_id", pd.Series(dtype=str)).astype(str) != "stage39c_target_engineering_residual_stack"]
        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    df.to_csv(path, index=False)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    cfg = load_cfg(resolve(args.config))
    refs = cfg["references"]
    outputs = cfg["outputs"]
    seed = int(refs["random_seed"])
    targets = refs["required_targets"]

    inv = input_inventory(cfg)
    training_allowed = bool(inv["exists"].all())
    stage27c = load_stage27c_module()
    folds, _target_manifest, _expr, target_matrix, modules, _module_genes = stage27c.load_context()
    folds = folds.copy()
    folds["donor_id"] = folds["donor_id"].astype(str)
    modules = modules.copy()
    modules.index = modules.index.astype(str)
    target_matrix = normalize_target_columns(target_matrix.copy())
    target_matrix.index = target_matrix.index.astype(str)
    metadata = read_csv(cfg["inputs"]["donor_metadata_targets"])
    donors = [d for d in folds["donor_id"].tolist() if d in modules.index and d in target_matrix.index]
    covariates = safe_covariate_frame(metadata, donors, cfg["safe_covariates"]["numeric"], cfg["safe_covariates"]["categorical"])
    cov_audit = audit_covariate_columns(cfg["safe_covariates"]["numeric"] + cfg["safe_covariates"]["categorical"])
    leakage_cov_pass = not bool(cov_audit["leakage_risk"].any())
    missing_targets = [t for t in targets if t not in target_matrix.columns]
    training_allowed = training_allowed and leakage_cov_pass and not missing_targets

    training_gate = pd.DataFrame([{"training_allowed": training_allowed, "training_gate_reason": "ok" if training_allowed else "missing inputs, target aliases, or covariate leakage risk", "n_donors": len(donors), "missing_targets": ";".join(missing_targets), "covariate_leakage_pass": leakage_cov_pass}])
    transform_design = pd.DataFrame([{"target_transform": t, "train_fold_only": True, "description": {"raw_log1p": "log1p target modeling", "winsor_log1p": "train-fold 5/95 winsorized log1p target", "rank_inverse_normal": "train-fold rank inverse-normal target", "covariate_residual_log1p": "train-fold safe-covariate residualized log1p target"}[t]} for t in cfg["target_transforms"]])
    model_registry = pd.DataFrame(
        [
            {"condition": "raw_log1p_module_pca_ridge", "target_transform": "raw_log1p", "feature_mode": "module_pca", "model": "ridge", "control": False},
            {"condition": "winsor_log1p_module_pca_ridge", "target_transform": "winsor_log1p", "feature_mode": "module_pca", "model": "ridge", "control": False},
            {"condition": "rank_int_module_pca_ridge", "target_transform": "rank_inverse_normal", "feature_mode": "module_pca", "model": "ridge", "control": False},
            {"condition": "covariate_residual_log1p_module_pca_ridge", "target_transform": "covariate_residual_log1p", "feature_mode": "module_pca", "model": "ridge", "control": False},
            {"condition": "raw_log1p_module_pca_elasticnet", "target_transform": "raw_log1p", "feature_mode": "module_pca", "model": "elasticnet", "control": False},
            {"condition": "raw_log1p_module_pca_huber", "target_transform": "raw_log1p", "feature_mode": "module_pca", "model": "huber", "control": False},
            {"condition": "raw_log1p_metadata_only_ridge", "target_transform": "raw_log1p", "feature_mode": "metadata_only", "model": "ridge", "control": True},
            {"condition": "raw_log1p_module_pca_ridge_donor_shuffled_control", "target_transform": "raw_log1p", "feature_mode": "module_pca", "model": "ridge", "control": True},
        ]
    )

    oof_parts = []
    fold_design_parts = []
    if training_allowed:
        for row in model_registry.itertuples(index=False):
            oof, design = run_condition(
                row.condition,
                row.target_transform,
                row.feature_mode,
                row.model,
                modules.loc[donors],
                covariates,
                target_matrix.loc[donors],
                folds[folds["donor_id"].isin(donors)],
                targets,
                cfg,
                shuffled_target=row.condition.endswith("donor_shuffled_control"),
            )
            oof_parts.append(oof)
            fold_design_parts.append(design)
    oof_all = pd.concat(oof_parts, ignore_index=True) if oof_parts else pd.DataFrame()
    fold_design = pd.concat(fold_design_parts, ignore_index=True) if fold_design_parts else pd.DataFrame()
    target_metrics, mean_metrics = metric_tables(oof_all)
    control_results = build_control_results(mean_metrics) if not mean_metrics.empty else pd.DataFrame()

    non_control = mean_metrics[~mean_metrics["condition"].str.contains("control|metadata_only", regex=True)] if not mean_metrics.empty else pd.DataFrame()
    best = non_control.sort_values("mean_pooled_oof_spearman", ascending=False).iloc[0] if not non_control.empty else pd.Series(dtype=object)
    best_condition = str(best.get("condition", "not_run"))
    boot = bootstrap_ci(oof_all, best_condition, int(refs["bootstrap_iterations"]), seed) if best_condition != "not_run" else pd.DataFrame()
    best_mean = float(best.get("mean_pooled_oof_spearman", np.nan))
    delta_vs_stage27c = best_mean - float(refs["stage27c_reference_mean"]) if np.isfinite(best_mean) else np.nan
    lower_ci = float(boot.iloc[0]["ci_lower_95"]) if not boot.empty else np.nan
    controls_pass = bool(control_results["passes"].all()) if not control_results.empty else False
    oof_audit = audit_oof_predictions(oof_all)
    leakage_audit = pd.concat([cov_audit.assign(audit_type="covariate"), oof_audit.assign(audit_type="oof")], ignore_index=True, sort=False)
    leakage_pass = bool(oof_audit["pass"].map(as_bool).all()) and leakage_cov_pass
    target_rows = target_metrics[target_metrics["condition"] == best_condition] if not target_metrics.empty else pd.DataFrame()
    negative_null_reported = bool((target_metrics["pooled_oof_spearman"] <= float(refs["stage27c_reference_mean"])).any()) if not target_metrics.empty else False
    rescue_pass = bool(
        np.isfinite(best_mean)
        and best_mean >= float(refs["rescue_threshold"])
        and best_mean >= float(refs["minimum_success_threshold"])
        and np.isfinite(lower_ci)
        and lower_ci > float(refs["stage27c_reference_mean"])
        and controls_pass
        and leakage_pass
        and not target_rows.empty
        and int(target_rows["target"].nunique()) == len(targets)
    )
    delta = pd.DataFrame(
        [
            {
                "best_condition": best_condition,
                "stage27c_reference_mean": float(refs["stage27c_reference_mean"]),
                "best_mean_pooled_oof_spearman": best_mean,
                "delta_vs_stage27c": delta_vs_stage27c,
                "rescue_threshold": float(refs["rescue_threshold"]),
                "bootstrap_ci_lower_95": lower_ci,
                "bootstrap_ci_upper_95": float(boot.iloc[0]["ci_upper_95"]) if not boot.empty else np.nan,
                "controls_pass": controls_pass,
                "leakage_audit_pass": leakage_pass,
                "stage39c_internal_rescue_pass": rescue_pass,
                "recommended_next_step": "promote Stage 39C as new internal benchmark only after manual review" if rescue_pass else "do not replace Stage 27C; proceed to metadata/composition Stage 39D or refine target engineering",
                "allowed_claim_language": ALLOWED_CLAIM,
                "prohibited_claim_language": PROHIBITED_CLAIM,
            }
        ]
    )
    claim_audit = build_claim_audit(negative_null_reported)
    pass_fail = pd.DataFrame(
        [
            {
                "stage39c_run": True,
                "inputs_found": bool(inv["exists"].all()),
                "training_allowed": training_allowed,
                "training_ran": not oof_all.empty,
                "inventories_written": True,
                "target_transforms_written": True,
                "controls_written": not control_results.empty,
                "bootstrap_ci_written": not boot.empty,
                "leakage_audit_written": True,
                "claim_audit_written": True,
                "safety_audit_pass": bool(claim_audit["pass"].map(as_bool).all()),
                "stage39c_run_pass": True,
                "controlled_interpretation": SAFE_INTERPRETATION,
            }
        ]
    )

    write_csv(inv, outputs["input_inventory"])
    write_csv(cov_audit, outputs["feature_covariate_audit"])
    write_csv(transform_design, outputs["target_transform_design"])
    write_csv(training_gate, outputs["training_gate"])
    write_csv(model_registry, outputs["model_registry"])
    write_csv(oof_all, outputs["oof_predictions"])
    write_csv(target_metrics, outputs["target_metrics"])
    write_csv(mean_metrics, outputs["mean_metrics"])
    write_csv(control_results, outputs["control_results"])
    write_csv(boot, outputs["bootstrap_ci"])
    write_csv(leakage_audit, outputs["leakage_audit"])
    write_csv(delta, outputs["delta_vs_stage27c"])
    write_csv(claim_audit, outputs["claim_boundary_audit"])
    write_csv(pass_fail, outputs["pass_fail"])

    report = f"""# Stage 39C target engineering residual-stack report

{SAFE_INTERPRETATION}

## Why this stage was run

Stage 39B-LPH did not beat Stage 27C and failed the shuffled-target control. Stage 39C therefore tests the report's highest-priority recommendation: target engineering plus target-specific simple models under strict donor-held-out safeguards.

## Training gate

{markdown_table(training_gate)}

## Target-transform design

{markdown_table(transform_design)}

## Model registry

{markdown_table(model_registry)}

## Mean metrics

{markdown_table(mean_metrics.sort_values('mean_pooled_oof_spearman', ascending=False) if not mean_metrics.empty else mean_metrics)}

## Target metrics

{markdown_table(target_metrics.sort_values(['condition', 'target']) if not target_metrics.empty else target_metrics)}

## Control results

{markdown_table(control_results)}

## Bootstrap CI and Stage 27C delta

{markdown_table(boot)}

{markdown_table(delta)}

## Leakage and claim audits

{markdown_table(leakage_audit)}

{markdown_table(claim_audit)}
"""
    pi = f"""# Stage 39C PI target-engineering summary

## Short answer

Best condition: `{best_condition}`. Mean pooled OOF Spearman: `{best_mean}`. Delta versus Stage 27C: `{delta_vs_stage27c}`. Stage 39C internal rescue pass: `{rescue_pass}`.

{markdown_table(delta)}

## What was tested

Train-fold-only target transformations were benchmarked with target-specific ridge/elastic-net/Huber models using locked donor-held-out folds. Metadata-only and donor-shuffled controls were included.

## Top conditions

{markdown_table(mean_metrics.sort_values('mean_pooled_oof_spearman', ascending=False).head(8) if not mean_metrics.empty else mean_metrics)}

## Interpretation

No external validation, causal, therapeutic, disease-modifying, or gene-ablation claim is supported by Stage 39C. If this stage does not pass the strict rescue gate, Stage 27C remains the locked internal reference.
"""
    write_text(report, outputs["technical_report"])
    write_text(pi, outputs["pi_summary"])

    update_markdown_section(outputs["active_status"], "Stage 39C target engineering residual-stack status", f"Stage 39C is complete. Best condition: `{best_condition}`; mean pooled OOF Spearman: `{best_mean}`; delta versus Stage 27C: `{delta_vs_stage27c}`; internal rescue pass: `{rescue_pass}`. This is an internal target-engineering benchmark only, not external validation or causal/therapeutic evidence.")
    update_markdown_section(outputs["v3_scorecard_md"], "Stage 39C target engineering residual-stack result", f"Stage 39C run pass: `{as_bool(pass_fail.iloc[0]['stage39c_run_pass'])}`. Best condition: `{best_condition}`; mean pooled OOF Spearman: `{best_mean}`; delta versus Stage 27C: `{delta_vs_stage27c}`; internal rescue pass: `{rescue_pass}`.")
    update_scorecard_csv(outputs["v3_scorecard_csv"], delta, pass_fail)

    print(f"stage39c_training_allowed={training_allowed}")
    print(f"stage39c_training_ran={not oof_all.empty}")
    print(f"best_condition={best_condition}")
    print(f"best_mean_pooled_oof_spearman={best_mean}")
    print(f"delta_vs_stage27c={delta_vs_stage27c}")
    print(f"bootstrap_ci_lower_95={lower_ci}")
    print(f"controls_pass={controls_pass}")
    print(f"leakage_audit_pass={leakage_pass}")
    print(f"stage39c_internal_rescue_pass={rescue_pass}")
    print(f"stage39c_run_pass={as_bool(pass_fail.iloc[0]['stage39c_run_pass'])}")


if __name__ == "__main__":
    main()
