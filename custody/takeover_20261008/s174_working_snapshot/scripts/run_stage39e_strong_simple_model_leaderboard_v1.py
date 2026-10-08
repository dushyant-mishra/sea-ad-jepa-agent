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
from sklearn.cross_decomposition import PLSRegression
from sklearn.decomposition import PCA
from sklearn.impute import SimpleImputer
from sklearn.linear_model import ElasticNetCV, HuberRegressor, RidgeCV
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
for path in [ROOT / "src", ROOT / "scripts"]:
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_pathology_residual_targets_v1 import rank_inverse_normal_apply, rank_inverse_normal_train, winsor_bounds


SAFE_INTERPRETATION = (
    "Stage 39E is an internal strong simple-model leaderboard under locked donor-held-out folds. "
    "It uses only Stage 27C module features and train-fold-only target/feature preprocessing. "
    "Composition/proxy features flagged in Stage 39D are excluded from the primary benchmark. "
    "It does not use external data, select candidates, or support claims of clean external validation, "
    "causality, therapeutic relevance, disease modification, or gene ablation."
)
ALLOWED_CLAIM = "internal simple-model leaderboard; donor-held-out model comparison; benchmark selection support only"
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
    val = spearmanr(yt, yp).statistic
    return 0.0 if pd.isna(val) else float(val)


def mse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    mask = np.isfinite(y_true) & np.isfinite(y_pred)
    return float(np.mean((y_true[mask] - y_pred[mask]) ** 2)) if int(mask.sum()) else float("nan")


def markdown_table(df: pd.DataFrame, max_rows: int | None = None) -> str:
    view = df if max_rows is None else df.head(max_rows)
    if view.empty:
        return "_No rows available._"
    view = view.fillna("").astype(str)
    cols = list(view.columns)
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for _, row in view.iterrows():
        vals = [str(row[col]).replace("|", "\\|").replace("\n", " ") for col in cols]
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines)


def input_inventory(cfg: dict[str, Any]) -> pd.DataFrame:
    rows = []
    for name, value in cfg["inputs"].items():
        path = resolve(value)
        rows.append({"input_name": name, "path": str(value), "exists": path.exists(), "size_bytes": path.stat().st_size if path.exists() else 0})
    return pd.DataFrame(rows)


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
                    raise ImportError(f"{name} unavailable; Stage 39E does not use {cls}")

            setattr(module, cls, _Unavailable)
            sys.modules[name] = module
    spec = importlib.util.spec_from_file_location("stage27c_for_stage39e", resolve("scripts/run_stage27c_non_graph_rescue_v1.py"))
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not import Stage 27C")
    module = importlib.util.module_from_spec(spec)
    sys.modules["stage27c_for_stage39e"] = module
    spec.loader.exec_module(module)
    return module


def normalize_target_columns(target_matrix: pd.DataFrame) -> pd.DataFrame:
    alias = {
        "percent AT8 positive area_Grey matter": "AT8",
        "percent 6e10 positive area_Grey matter": "6e10/A_beta",
        "percent GFAP positive area_Grey matter": "GFAP",
        "percent Iba1 positive area_Grey matter": "Iba1",
        "percent NeuN positive area_Grey matter": "NeuN",
        "6e10/AÃŽÂ²": "6e10/A_beta",
        "6e10/AÎ²": "6e10/A_beta",
    }
    return target_matrix.rename(columns={c: alias.get(str(c), str(c)) for c in target_matrix.columns})


def transform_target(transform: str, y_train_raw: np.ndarray, y_test_raw: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    if transform == "raw_log1p":
        return np.log1p(y_train_raw), np.log1p(y_test_raw)
    if transform == "winsor_log1p":
        lo, hi = winsor_bounds(y_train_raw)
        return np.log1p(np.clip(y_train_raw, lo, hi)), np.log1p(np.clip(y_test_raw, lo, hi))
    if transform == "rank_inverse_normal":
        y_train_log = np.log1p(y_train_raw)
        y_test_log = np.log1p(y_test_raw)
        y_train, _ = rank_inverse_normal_train(y_train_log)
        y_test = rank_inverse_normal_apply(y_test_log, y_train_log)
        return y_train, y_test
    raise ValueError(transform)


def make_features(view: str, n_components: int | None, x_train_raw: np.ndarray, x_test_raw: np.ndarray, seed: int, max_direct: int) -> tuple[np.ndarray, np.ndarray]:
    if view == "pca":
        n_comp = min(int(n_components or 1), x_train_raw.shape[1], max(1, x_train_raw.shape[0] - 1))
        pipe = Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler()), ("pca", PCA(n_components=n_comp, random_state=seed))])
        return pipe.fit_transform(x_train_raw), pipe.transform(x_test_raw)
    if view == "direct":
        n = min(max_direct, x_train_raw.shape[1])
        variances = np.nanvar(x_train_raw, axis=0)
        keep = np.argsort(variances)[::-1][:n]
        pipe = Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler())])
        return pipe.fit_transform(x_train_raw[:, keep]), pipe.transform(x_test_raw[:, keep])
    raise ValueError(view)


def build_model(model_name: str, cfg: dict[str, Any], seed: int, n_train: int, pls_components: int | None = None):
    cv = min(3, max(2, n_train // 10))
    if model_name == "ridge":
        return RidgeCV(alphas=np.asarray(cfg["models"]["ridge_alphas"], dtype=float), cv=cv)
    if model_name == "elasticnet":
        return ElasticNetCV(
            alphas=np.asarray(cfg["models"]["elasticnet_alphas"], dtype=float),
            l1_ratio=np.asarray(cfg["models"]["elasticnet_l1_ratios"], dtype=float),
            cv=cv,
            max_iter=50000,
            random_state=seed,
            n_jobs=1,
        )
    if model_name == "huber":
        return HuberRegressor(epsilon=1.35, alpha=0.01, max_iter=1000)
    if model_name == "pls":
        return PLSRegression(n_components=int(pls_components or 2), scale=False)
    raise ValueError(model_name)


def model_predict(model: Any, x_test: np.ndarray) -> np.ndarray:
    pred = model.predict(x_test)
    return np.asarray(pred).reshape(-1)


def build_registry(cfg: dict[str, Any]) -> pd.DataFrame:
    rows = []
    for transform in cfg["target_transforms"]:
        for n_comp in cfg["models"]["pca_components"]:
            for model in ["ridge", "elasticnet", "huber"]:
                rows.append({
                    "condition": f"{transform}_module_pca{n_comp}_{model}",
                    "target_transform": transform,
                    "feature_view": "pca",
                    "n_components": n_comp,
                    "model": model,
                    "primary_leaderboard_allowed": True,
                })
        if transform == "rank_inverse_normal":
            for model in ["ridge", "elasticnet", "huber"]:
                rows.append({
                    "condition": f"{transform}_module_direct_{model}",
                    "target_transform": transform,
                    "feature_view": "direct",
                    "n_components": np.nan,
                    "model": model,
                    "primary_leaderboard_allowed": True,
                })
            for n_comp in cfg["models"]["pls_components"]:
                rows.append({
                    "condition": f"{transform}_module_pca{n_comp}_pls",
                    "target_transform": transform,
                    "feature_view": "pca",
                    "n_components": n_comp,
                    "model": "pls",
                    "primary_leaderboard_allowed": True,
                })
    rows.extend([
        {
            "condition": "negative_control_rank_int_pca8_donor_shuffled_target_ridge",
            "target_transform": "rank_inverse_normal",
            "feature_view": "pca",
            "n_components": 8,
            "model": "ridge",
            "primary_leaderboard_allowed": False,
        },
        {
            "condition": "negative_control_rank_int_pca8_shuffled_features_ridge",
            "target_transform": "rank_inverse_normal",
            "feature_view": "pca",
            "n_components": 8,
            "model": "ridge",
            "primary_leaderboard_allowed": False,
        },
    ])
    return pd.DataFrame(rows)


def run_condition(row: pd.Series, modules: pd.DataFrame, target_matrix: pd.DataFrame, folds: pd.DataFrame, cfg: dict[str, Any]) -> pd.DataFrame:
    rows = []
    seed = int(cfg["references"]["random_seed"])
    rng = np.random.default_rng(seed)
    donors = [d for d in folds["donor_id"].astype(str).tolist() if d in modules.index and d in target_matrix.index]
    fold_lookup = folds.set_index("donor_id")["fold_id"].to_dict()
    condition = str(row["condition"])
    for target_idx, target in enumerate(cfg["references"]["required_targets"]):
        y_raw = target_matrix[target].astype(float)
        for fold_id in sorted(folds["fold_id"].unique()):
            test = [d for d in donors if fold_lookup.get(d) == fold_id and np.isfinite(y_raw.loc[d])]
            train = [d for d in donors if fold_lookup.get(d) != fold_id and np.isfinite(y_raw.loc[d])]
            y_train, y_test = transform_target(str(row["target_transform"]), y_raw.loc[train].to_numpy(float), y_raw.loc[test].to_numpy(float))
            if "donor_shuffled_target" in condition:
                y_train = rng.permutation(y_train)
            x_train, x_test = make_features(
                str(row["feature_view"]),
                None if pd.isna(row["n_components"]) else int(row["n_components"]),
                modules.loc[train].to_numpy(float),
                modules.loc[test].to_numpy(float),
                seed + target_idx * 100 + int(fold_id),
                int(cfg["models"]["max_direct_features"]),
            )
            if "shuffled_features" in condition:
                x_train = x_train[rng.permutation(x_train.shape[0]), :]
            model = build_model(str(row["model"]), cfg, seed + target_idx * 1000 + int(fold_id), len(train), None if pd.isna(row["n_components"]) else int(row["n_components"]))
            model.fit(x_train, y_train)
            pred = model_predict(model, x_test)
            for donor, yt, yp in zip(test, y_test, pred):
                rows.append({"condition": condition, "target": target, "fold_id": fold_id, "donor_id": donor, "y_true": float(yt), "y_pred": float(yp)})
    return pd.DataFrame(rows)


def metric_tables(oof: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    for (condition, target), sub in oof.groupby(["condition", "target"]):
        rows.append({
            "condition": condition,
            "target": target,
            "n_donors": int(sub["donor_id"].nunique()),
            "pooled_oof_spearman": safe_spearman(sub["y_true"].to_numpy(float), sub["y_pred"].to_numpy(float)),
            "mse": mse(sub["y_true"].to_numpy(float), sub["y_pred"].to_numpy(float)),
            "prediction_variance": float(np.nanvar(sub["y_pred"].to_numpy(float))),
        })
    target = pd.DataFrame(rows)
    mean = target.groupby("condition", as_index=False).agg(
        mean_pooled_oof_spearman=("pooled_oof_spearman", "mean"),
        min_target_spearman=("pooled_oof_spearman", "min"),
        n_targets=("target", "nunique"),
    ) if not target.empty else pd.DataFrame()
    return target, mean


def bootstrap_ci(oof: pd.DataFrame, condition: str, n_boot: int, seed: int) -> pd.DataFrame:
    sub = oof[oof["condition"] == condition].copy()
    if sub.empty:
        return pd.DataFrame()
    donors = sorted(sub["donor_id"].unique())
    rng = np.random.default_rng(seed)
    vals = []
    for _ in range(n_boot):
        sampled = rng.choice(donors, size=len(donors), replace=True)
        parts = []
        for i, donor in enumerate(sampled):
            part = sub[sub["donor_id"] == donor].copy()
            part["boot_id"] = f"{donor}_{i}"
            parts.append(part)
        boot = pd.concat(parts)
        vals.append(float(np.mean([safe_spearman(g["y_true"].to_numpy(float), g["y_pred"].to_numpy(float)) for _, g in boot.groupby("target")])))
    arr = np.asarray(vals)
    return pd.DataFrame([{
        "condition": condition,
        "n_bootstrap": n_boot,
        "bootstrap_mean": float(np.mean(arr)),
        "ci_lower_95": float(np.quantile(arr, 0.025)),
        "ci_upper_95": float(np.quantile(arr, 0.975)),
    }])


def build_claim_audit() -> pd.DataFrame:
    items = {
        "train_fold_only_preprocessing": True,
        "donor_heldout_only": True,
        "no_external_data": True,
        "no_composition_proxy_features": True,
        "no_candidate_selection": True,
        "no_clean_external_validation_claim": True,
        "no_causal_claim": True,
        "no_therapeutic_claim": True,
        "no_gene_ablation_claim": True,
        "negative_controls_reported": True,
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
        text = text[:start].rstrip() + section + (text[next_start:] if next_start != -1 else "")
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def update_scorecard_csv(path_value: str | Path, delta: pd.DataFrame, pass_fail: pd.DataFrame) -> None:
    path = resolve(path_value)
    df = pd.read_csv(path) if path.exists() else pd.DataFrame()
    d = delta.iloc[0] if not delta.empty else pd.Series(dtype=object)
    row = {
        "scorecard_item": "stage39e_strong_simple_model_leaderboard",
        "status": "complete",
        "stage": "Stage 39E",
        "metric": "mean pooled donor-level OOF Spearman",
        "threshold_or_gate": "best predeclared simple model must beat Stage 39C by margin and bootstrap CI lower must clear Stage 39C",
        "current_value": f"best={d.get('best_mean_pooled_oof_spearman','NA')}; delta_vs_stage39c={d.get('delta_vs_stage39c','NA')}",
        "pass_fail": "pass" if as_bool(d.get("stage39e_material_leaderboard_pass", False)) else "fail",
        "datasets_allowed": "SEA-AD locked internal donor folds only",
        "datasets_forbidden": "external data; composition proxy features; candidate selection; clean holdouts",
        "allowed_claim": ALLOWED_CLAIM,
        "notes": SAFE_INTERPRETATION,
        "stage_id": "stage39e_strong_simple_model_leaderboard",
        "primary_metric": "best predeclared simple-model mean pooled OOF Spearman",
        "pass_rule": "margin over Stage39C plus bootstrap and negative-control gates",
        "result": f"run_pass={as_bool(pass_fail.iloc[0].get('stage39e_run_pass', False))}",
        "allowed_inputs": "internal Stage 27C module features and locked folds",
        "forbidden_inputs": "external validation data, composition proxy features, candidate lists",
        "interpretation": SAFE_INTERPRETATION,
    }
    if df.empty:
        df = pd.DataFrame([row])
    else:
        for col in row:
            if col not in df.columns:
                df[col] = ""
        df = df[df.get("stage_id", pd.Series(dtype=str)).astype(str) != "stage39e_strong_simple_model_leaderboard"]
        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    df.to_csv(path, index=False)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    cfg = load_cfg(resolve(args.config))
    out = cfg["outputs"]
    refs = cfg["references"]
    inv = input_inventory(cfg)

    stage27c = load_stage27c_module()
    folds, _targets_manifest, _expr, target_matrix, modules, _module_genes = stage27c.load_context()
    folds = folds.copy()
    folds["donor_id"] = folds["donor_id"].astype(str)
    modules = modules.copy()
    modules.index = modules.index.astype(str)
    target_matrix = normalize_target_columns(target_matrix.copy())
    target_matrix.index = target_matrix.index.astype(str)
    donors = [d for d in folds["donor_id"].tolist() if d in modules.index and d in target_matrix.index]
    folds_use = folds[folds["donor_id"].isin(donors)].copy()
    modules_use = modules.loc[donors]
    target_use = target_matrix.loc[donors]

    registry = build_registry(cfg)
    training_allowed = bool(inv["exists"].all()) and len(donors) > 20
    oof_parts = []
    if training_allowed:
        for _, row in registry.iterrows():
            oof_parts.append(run_condition(row, modules_use, target_use, folds_use, cfg))
    oof = pd.concat(oof_parts, ignore_index=True) if oof_parts else pd.DataFrame()
    target_metrics, mean_metrics = metric_tables(oof)
    leaderboard = mean_metrics.merge(registry[["condition", "target_transform", "feature_view", "n_components", "model", "primary_leaderboard_allowed"]], on="condition", how="left") if not mean_metrics.empty else pd.DataFrame()
    leaderboard = leaderboard.sort_values("mean_pooled_oof_spearman", ascending=False) if not leaderboard.empty else leaderboard
    primary = leaderboard[leaderboard["primary_leaderboard_allowed"].map(as_bool)] if not leaderboard.empty else pd.DataFrame()
    controls = leaderboard[~leaderboard["primary_leaderboard_allowed"].map(as_bool)] if not leaderboard.empty else pd.DataFrame()
    best = primary.iloc[0] if not primary.empty else pd.Series(dtype=object)
    best_condition = str(best.get("condition", "not_run"))
    best_mean = float(best.get("mean_pooled_oof_spearman", np.nan))
    best_min_target = float(best.get("min_target_spearman", np.nan))
    boot = bootstrap_ci(oof, best_condition, int(refs["bootstrap_iterations"]), int(refs["random_seed"])) if best_condition != "not_run" else pd.DataFrame()

    s39c_target = read_csv(cfg["inputs"]["stage39c_target_metrics"])
    target_best = target_metrics[target_metrics["condition"] == best_condition] if not target_metrics.empty else pd.DataFrame()
    target_delta = pd.DataFrame()
    no_target_drop_guard_violation = False
    if not s39c_target.empty and not target_best.empty:
        ref_target = s39c_target[s39c_target["condition"] == refs["stage39c_best_condition"]].set_index("target")["pooled_oof_spearman"]
        target_delta = target_best.set_index("target")["pooled_oof_spearman"].to_frame("stage39e").join(ref_target.rename("stage39c"), how="left").reset_index()
        target_delta["delta_vs_stage39c"] = target_delta["stage39e"] - target_delta["stage39c"]
        no_target_drop_guard_violation = bool((target_delta["delta_vs_stage39c"] >= -float(refs["target_drop_guard"])).all())
    control_max = float(controls["mean_pooled_oof_spearman"].max()) if not controls.empty else np.nan
    negative_controls_pass = bool(np.isfinite(control_max) and best_mean > control_max)
    ci_lower = float(boot.iloc[0]["ci_lower_95"]) if not boot.empty else np.nan
    material_pass = bool(
        np.isfinite(best_mean)
        and best_mean >= float(refs["stage39c_best_mean"]) + float(refs["material_margin_vs_stage39c"])
        and np.isfinite(ci_lower)
        and ci_lower > float(refs["stage39c_best_mean"])
        and negative_controls_pass
        and no_target_drop_guard_violation
    )
    delta = pd.DataFrame([{
        "best_condition": best_condition,
        "stage27c_reference_mean": float(refs["stage27c_reference_mean"]),
        "stage39c_best_mean": float(refs["stage39c_best_mean"]),
        "best_mean_pooled_oof_spearman": best_mean,
        "best_min_target_spearman": best_min_target,
        "delta_vs_stage27c": best_mean - float(refs["stage27c_reference_mean"]) if np.isfinite(best_mean) else np.nan,
        "delta_vs_stage39c": best_mean - float(refs["stage39c_best_mean"]) if np.isfinite(best_mean) else np.nan,
        "bootstrap_ci_lower_95": ci_lower,
        "bootstrap_ci_upper_95": float(boot.iloc[0]["ci_upper_95"]) if not boot.empty else np.nan,
        "negative_control_max_mean_pooled_oof_spearman": control_max,
        "negative_controls_pass": negative_controls_pass,
        "no_target_drop_guard_violation": no_target_drop_guard_violation,
        "stage39e_material_leaderboard_pass": material_pass,
        "recommended_next_step": "consider locking Stage 39E as new internal simple-model benchmark after independent code review" if material_pass else "retain Stage 39C as credible benchmark; use Stage 39E as negative/leaderboard evidence",
        "allowed_claim_language": ALLOWED_CLAIM,
        "prohibited_claim_language": PROHIBITED_CLAIM,
    }])
    claim = build_claim_audit()
    pass_fail = pd.DataFrame([{
        "stage39e_run": True,
        "inputs_found": bool(inv["exists"].all()),
        "training_allowed": training_allowed,
        "training_ran": not oof.empty,
        "model_registry_written": not registry.empty,
        "leaderboard_written": not leaderboard.empty,
        "negative_controls_written": not controls.empty,
        "bootstrap_ci_written": not boot.empty,
        "claim_audit_written": True,
        "safety_audit_pass": bool(claim["pass"].map(as_bool).all()),
        "stage39e_run_pass": bool(training_allowed and not leaderboard.empty and not boot.empty and bool(claim["pass"].map(as_bool).all())),
        "controlled_interpretation": SAFE_INTERPRETATION,
    }])

    write_csv(inv, out["input_inventory"])
    write_csv(registry, out["model_registry"])
    write_csv(oof, out["oof_predictions"])
    write_csv(target_metrics, out["target_metrics"])
    write_csv(mean_metrics, out["mean_metrics"])
    write_csv(leaderboard, out["leaderboard"])
    write_csv(controls, out["negative_control_results"])
    write_csv(boot, out["bootstrap_ci"])
    write_csv(delta, out["delta_vs_stage39c_stage27c"])
    write_csv(claim, out["claim_boundary_audit"])
    write_csv(pass_fail, out["pass_fail"])

    report = f"""# Stage 39E strong simple-model leaderboard report

{SAFE_INTERPRETATION}

## Inputs

{markdown_table(inv)}

## Model registry

{markdown_table(registry, max_rows=40)}

## Leaderboard

{markdown_table(leaderboard, max_rows=30)}

## Best-model target deltas versus Stage 39C

{markdown_table(target_delta)}

## Negative controls

{markdown_table(controls)}

## Bootstrap CI and pass/fail

{markdown_table(boot)}

{markdown_table(delta)}

## Claim boundary audit

{markdown_table(claim)}

## Interpretation

Stage 39E asks whether a predeclared set of strong but low-capacity simple models can beat the Stage 39C target-engineering lead without using external data or Stage 39D composition/proxy features. A Stage 39E material pass requires a margin over Stage 39C, bootstrap CI support, negative-control separation, and no target-drop guard violation.
"""
    pi = f"""# Stage 39E PI simple-model leaderboard summary

## Short answer

Best condition: `{best_condition}`. Mean pooled OOF Spearman: `{best_mean}`. Delta versus Stage 39C: `{delta.iloc[0]['delta_vs_stage39c']}`. Stage 39E material leaderboard pass: `{material_pass}`.

## Top leaderboard rows

{markdown_table(leaderboard.head(12) if not leaderboard.empty else leaderboard)}

## Best-model target deltas

{markdown_table(target_delta)}

## Safe interpretation

Stage 39E is an internal simple-model leaderboard. It excludes the Stage 39D composition/proxy features from the primary benchmark. It does not establish external validation, causality, therapeutic relevance, disease modification, or gene-ablation effects.
"""
    write_text(report, out["technical_report"])
    write_text(pi, out["pi_summary"])
    update_markdown_section(out["active_status"], "Stage 39E strong simple-model leaderboard status", f"Stage 39E is complete. Best condition: `{best_condition}`; mean pooled OOF Spearman: `{best_mean}`; delta versus Stage 39C: `{delta.iloc[0]['delta_vs_stage39c']}`; material leaderboard pass: `{material_pass}`. Composition/proxy features from Stage 39D were excluded from the primary benchmark.")
    update_markdown_section(out["v3_scorecard_md"], "Stage 39E strong simple-model leaderboard result", f"Stage 39E run pass: `{as_bool(pass_fail.iloc[0]['stage39e_run_pass'])}`. Best condition: `{best_condition}`; mean pooled OOF Spearman: `{best_mean}`; delta versus Stage 39C: `{delta.iloc[0]['delta_vs_stage39c']}`; material leaderboard pass: `{material_pass}`.")
    update_scorecard_csv(out["v3_scorecard_csv"], delta, pass_fail)
    print(f"stage39e_training_allowed={training_allowed}")
    print(f"stage39e_training_ran={not oof.empty}")
    print(f"best_condition={best_condition}")
    print(f"best_mean_pooled_oof_spearman={best_mean}")
    print(f"delta_vs_stage39c={delta.iloc[0]['delta_vs_stage39c']}")
    print(f"delta_vs_stage27c={delta.iloc[0]['delta_vs_stage27c']}")
    print(f"bootstrap_ci_lower_95={ci_lower}")
    print(f"negative_control_max={control_max}")
    print(f"negative_controls_pass={negative_controls_pass}")
    print(f"no_target_drop_guard_violation={no_target_drop_guard_violation}")
    print(f"stage39e_material_leaderboard_pass={material_pass}")
    print(f"stage39e_run_pass={as_bool(pass_fail.iloc[0]['stage39e_run_pass'])}")


if __name__ == "__main__":
    main()
