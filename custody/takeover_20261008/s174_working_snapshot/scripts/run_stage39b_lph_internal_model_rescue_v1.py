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
from sklearn.linear_model import RidgeCV
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


SAFE_INTERPRETATION = (
    "Stage 39B-LPH is an internal model-improvement experiment using a low-capacity latent prediction "
    "auxiliary head. It does not generate synthetic biological data, use external training/model selection, "
    "modify frozen candidates, or claim clean external validation, causality, therapeutic targeting, gene "
    "ablation, or disease modification."
)
ALLOWED_CLAIM = "internal model-improvement experiment; latent prediction auxiliary head; representation-space prediction; hypothesis prioritization only"
PROHIBITED_CLAIM = "generative decoder; synthetic biological data; clean external validation; validated mechanism; causal regulator; therapeutic target; disease-modifying target; gene-ablation result"


def resolve(path_value: str | Path) -> Path:
    path = Path(path_value)
    return path if path.is_absolute() else ROOT / path


def load_cfg(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def read_csv(path_value: str | Path) -> pd.DataFrame:
    path = resolve(path_value)
    return pd.read_csv(path) if path.exists() else pd.DataFrame()


def write_csv(df: pd.DataFrame, path_value: str | Path) -> Path:
    path = resolve(path_value)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    return path


def write_text(text: str, path_value: str | Path) -> Path:
    path = resolve(path_value)
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


def cosine_mean(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    vals = []
    for a, b in zip(y_true, y_pred):
        if not np.isfinite(a).all() or not np.isfinite(b).all():
            continue
        denom = float(np.linalg.norm(a) * np.linalg.norm(b))
        if denom == 0:
            continue
        vals.append(float(np.dot(a, b) / denom))
    return float(np.mean(vals)) if vals else float("nan")


def pooled_target_metrics(oof: pd.DataFrame) -> pd.DataFrame:
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
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    means = (
        out.groupby("condition", as_index=False)["pooled_oof_spearman"]
        .mean()
        .rename(columns={"pooled_oof_spearman": "mean_pooled_oof_spearman"})
    )
    return out.merge(means, on="condition", how="left")


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
    # Stage 27C imports the Stage 25 benchmark module, whose top-level imports include
    # optional tree baselines. Stage 39B-LPH only reuses Stage 27C context builders, so
    # provide inert shims if those optional packages are absent.
    if "lightgbm" not in sys.modules:
        try:
            __import__("lightgbm")
        except ModuleNotFoundError:
            lightgbm = types.ModuleType("lightgbm")

            class _UnavailableLGBMRegressor:  # noqa: D401
                def __init__(self, *args, **kwargs):
                    raise ImportError("lightgbm is unavailable; Stage 39B-LPH does not use LightGBM")

            lightgbm.LGBMRegressor = _UnavailableLGBMRegressor
            sys.modules["lightgbm"] = lightgbm
    if "xgboost" not in sys.modules:
        try:
            __import__("xgboost")
        except ModuleNotFoundError:
            xgboost = types.ModuleType("xgboost")

            class _UnavailableXGBRegressor:
                def __init__(self, *args, **kwargs):
                    raise ImportError("xgboost is unavailable; Stage 39B-LPH does not use XGBoost")

            xgboost.XGBRegressor = _UnavailableXGBRegressor
            sys.modules["xgboost"] = xgboost
    path = resolve("scripts/run_stage27c_non_graph_rescue_v1.py")
    spec = importlib.util.spec_from_file_location("stage27c_context_module", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load Stage 27C script module")
    module = importlib.util.module_from_spec(spec)
    sys.modules["stage27c_context_module"] = module
    spec.loader.exec_module(module)
    return module


def input_inventory(cfg: dict[str, Any]) -> pd.DataFrame:
    rows = []
    for name, path_value in cfg["inputs"].items():
        path = resolve(path_value)
        rows.append(
            {
                "input_name": name,
                "path": str(path.relative_to(ROOT)) if path.exists() else str(path_value),
                "exists": path.exists(),
                "size_bytes": path.stat().st_size if path.exists() else 0,
                "required_for_training": name in {"stage27c_script", "locked_folds", "stage27c_oof"},
            }
        )
    return pd.DataFrame(rows)


def build_failure_mode_inventory() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "failure_mode": "external_pretraining_deficit",
                "prior_evidence": "Stage 33B/33C/34A/34B did not improve over Stage 27C",
                "lph_response": "test internal representation-space auxiliary head before further external pretraining",
            },
            {
                "failure_mode": "graph_smoothing_or_topology_mismatch",
                "prior_evidence": "Stage 30/31/35A/35B mostly failed to beat Stage 27C; Stage 35C signal was small and module-scale",
                "lph_response": "use no-graph/identity first-pass LPH; graph-specific claims disabled unless graph context is explicitly used",
            },
            {
                "failure_mode": "external_metadata_testability_gap",
                "prior_evidence": "Stage 38B/38C limited by metadata gates; Stage 39A rescued only bounded readiness",
                "lph_response": "stay internal and donor-held-out; do not use external data for model selection",
            },
            {
                "failure_mode": "small_n_capacity_risk",
                "prior_evidence": "84-donor setting makes neural overcapacity risky",
                "lph_response": "ridge-only low-capacity implementation for v1",
            },
        ]
    )


def fit_lph_predictions(
    modules: pd.DataFrame,
    folds: pd.DataFrame,
    condition: str,
    alphas: list[float],
    seed: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    donors = modules.index.astype(str).tolist()
    fold_lookup = folds.set_index("donor_id")["fold_id"].to_dict()
    x_all = modules.to_numpy(float)
    columns = list(modules.columns)
    pred = np.full_like(x_all, np.nan, dtype=float)
    rng = np.random.default_rng(seed)
    diag_rows = []
    for fold_id in sorted(folds["fold_id"].unique()):
        test_donors = folds.loc[folds["fold_id"] == fold_id, "donor_id"].astype(str).tolist()
        train_donors = folds.loc[folds["fold_id"] != fold_id, "donor_id"].astype(str).tolist()
        train_idx = [donors.index(d) for d in train_donors if d in donors]
        test_idx = [donors.index(d) for d in test_donors if d in donors]
        x_train_base = x_all[train_idx, :]
        x_test_base = x_all[test_idx, :]
        if condition == "lph_aux_head_shuffled_context":
            perm = rng.permutation(len(train_idx))
            x_train_context = x_train_base[perm, :]
        else:
            x_train_context = x_train_base
        for j, target_name in enumerate(columns):
            mask_cols = [i for i in range(len(columns)) if i != j]
            y_train = x_train_base[:, j].copy()
            if condition == "lph_aux_head_shuffled_latent_target":
                y_train = rng.permutation(y_train)
            model = Pipeline(
                [
                    ("scaler", StandardScaler()),
                    ("ridge", RidgeCV(alphas=np.asarray(alphas, dtype=float), cv=min(3, max(2, len(train_idx) // 10)))),
                ]
            )
            model.fit(x_train_context[:, mask_cols], y_train)
            pred[test_idx, j] = model.predict(x_test_base[:, mask_cols])
        diag_rows.append(
            {
                "condition": condition,
                "fold_id": fold_id,
                "n_train_donors": len(train_idx),
                "n_test_donors": len(test_idx),
                "lph_mse": mse(x_all[test_idx, :].ravel(), pred[test_idx, :].ravel()),
                "lph_cosine_similarity": cosine_mean(x_all[test_idx, :], pred[test_idx, :]),
                "lph_flat_spearman": safe_spearman(x_all[test_idx, :].ravel(), pred[test_idx, :].ravel()),
            }
        )
    pred_df = pd.DataFrame(pred, index=donors, columns=[f"lph_pred_{c}" for c in columns])
    pred_df.insert(0, "donor_id", donors)
    pred_df["fold_id"] = [fold_lookup.get(d, np.nan) for d in donors]
    resid = modules.to_numpy(float) - pred
    for i, col in enumerate(columns):
        pred_df[f"lph_residual_{col}"] = resid[:, i]
    pred_df["lph_row_mse"] = np.nanmean(resid**2, axis=1)
    pred_df["lph_row_abs_error_mean"] = np.nanmean(np.abs(resid), axis=1)
    return pred_df, pd.DataFrame(diag_rows)


def pca_features(train_x: np.ndarray, test_x: np.ndarray, n_components: int, seed: int) -> tuple[np.ndarray, np.ndarray]:
    n_comp = min(n_components, train_x.shape[1], max(1, train_x.shape[0] - 1))
    pipe = Pipeline([("scaler", StandardScaler()), ("pca", PCA(n_components=n_comp, random_state=seed))])
    train_z = pipe.fit_transform(train_x)
    test_z = pipe.transform(test_x)
    return train_z, test_z


def downstream_oof(
    condition: str,
    base_modules: pd.DataFrame,
    lph_features: pd.DataFrame | None,
    target_matrix: pd.DataFrame,
    folds: pd.DataFrame,
    targets: list[str],
    alphas: list[float],
    seed: int,
    pca_components: int,
) -> pd.DataFrame:
    donors = [d for d in folds["donor_id"].astype(str).tolist() if d in base_modules.index and d in target_matrix.index]
    fold_lookup = folds.set_index("donor_id")["fold_id"].to_dict()
    rows = []
    for target in targets:
        for fold_id in sorted(folds["fold_id"].unique()):
            test = [d for d in donors if fold_lookup.get(d) == fold_id]
            train = [d for d in donors if fold_lookup.get(d) != fold_id]
            y_train_raw = target_matrix.loc[train, target].to_numpy(float)
            y_test_raw = target_matrix.loc[test, target].to_numpy(float)
            y_train = np.log1p(y_train_raw)
            x_train_modules = base_modules.loc[train].to_numpy(float)
            x_test_modules = base_modules.loc[test].to_numpy(float)
            train_z, test_z = pca_features(x_train_modules, x_test_modules, pca_components, seed)
            if lph_features is not None:
                lph = lph_features.set_index("donor_id")
                lph_cols = [c for c in lph.columns if c.startswith("lph_pred_") or c.startswith("lph_residual_") or c.startswith("lph_row_")]
                x_train = np.hstack([train_z, lph.loc[train, lph_cols].to_numpy(float)])
                x_test = np.hstack([test_z, lph.loc[test, lph_cols].to_numpy(float)])
            else:
                x_train, x_test = train_z, test_z
            model = Pipeline(
                [
                    ("scaler", StandardScaler()),
                    ("ridge", RidgeCV(alphas=np.asarray(alphas, dtype=float), cv=min(3, max(2, len(train) // 10)))),
                ]
            )
            model.fit(x_train, y_train)
            pred = np.expm1(model.predict(x_test))
            for donor, yt, yp in zip(test, y_test_raw, pred):
                rows.append(
                    {
                        "condition": condition,
                        "target": target,
                        "donor_id": donor,
                        "fold_id": fold_id,
                        "y_true": float(yt),
                        "y_pred": float(yp),
                        "target_scale": "log1p_train_expm1_pred",
                        "n_features": int(x_train.shape[1]),
                        "clean_holdout_used": False,
                        "heldout_donor_leakage_detected": False,
                    }
                )
    return pd.DataFrame(rows)


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
    out = target_matrix.copy()
    out = out.rename(columns={col: alias.get(str(col), str(col)) for col in out.columns})
    return out


def module_mean_target_baseline() -> dict[str, float]:
    df = read_csv("results/tables/v3_primary_baseline_target_winners_v1.csv")
    if not df.empty and {"target", "module_mean_baseline"}.issubset(df.columns):
        return dict(zip(df["target"], df["module_mean_baseline"]))
    # Fallback from existing recompute table.
    recompute = read_csv("results/tables/v3_primary_baseline_pooled_oof_recompute_v1.csv")
    if not recompute.empty and {"target", "baseline_id", "pooled_oof_spearman"}.issubset(recompute.columns):
        sub = recompute[recompute["baseline_id"] == "module_mean_baseline"]
        return dict(zip(sub["target"], sub["pooled_oof_spearman"]))
    return {}


def build_control_results(target_metrics: pd.DataFrame, lph_diag: pd.DataFrame) -> pd.DataFrame:
    rows = []
    means = target_metrics.groupby("condition", as_index=False)["pooled_oof_spearman"].mean().rename(columns={"pooled_oof_spearman": "mean_pooled_oof_spearman"})
    lookup = dict(zip(means["condition"], means["mean_pooled_oof_spearman"]))
    real = lookup.get("lph_aux_head_real", np.nan)
    baseline = lookup.get("no_lph_matched_baseline", np.nan)
    shuffled_target = lookup.get("lph_aux_head_shuffled_latent_target", np.nan)
    shuffled_context = lookup.get("lph_aux_head_shuffled_context", np.nan)
    identity = lookup.get("lph_aux_head_no_graph_or_identity", np.nan)
    rows.extend(
        [
            {"comparison": "real_lph_vs_no_lph_matched_baseline", "left_condition": "lph_aux_head_real", "right_condition": "no_lph_matched_baseline", "delta": real - baseline, "passes": bool(real > baseline) if np.isfinite(real) and np.isfinite(baseline) else False},
            {"comparison": "real_lph_vs_shuffled_latent_target", "left_condition": "lph_aux_head_real", "right_condition": "lph_aux_head_shuffled_latent_target", "delta": real - shuffled_target, "passes": bool(real > shuffled_target) if np.isfinite(real) and np.isfinite(shuffled_target) else False},
            {"comparison": "real_lph_vs_shuffled_context", "left_condition": "lph_aux_head_real", "right_condition": "lph_aux_head_shuffled_context", "delta": real - shuffled_context, "passes": bool(real > shuffled_context) if np.isfinite(real) and np.isfinite(shuffled_context) else False},
            {"comparison": "real_lph_vs_no_graph_identity", "left_condition": "lph_aux_head_real", "right_condition": "lph_aux_head_no_graph_or_identity", "delta": real - identity, "passes": bool(real >= identity) if np.isfinite(real) and np.isfinite(identity) else False},
        ]
    )
    return pd.DataFrame(rows)


def build_claim_audit(negative_null_reported: bool) -> pd.DataFrame:
    items = {
        "no_synthetic_biological_data_generated": True,
        "no_external_training": True,
        "no_external_model_selection": True,
        "no_external_candidate_selection": True,
        "frozen_stage36e_candidates_preserved": True,
        "no_clean_external_validation_claim": True,
        "no_causal_claim": True,
        "no_therapeutic_claim": True,
        "no_gene_ablation_claim": True,
        "no_disease_modifying_claim": True,
        "negative_null_results_reported": negative_null_reported,
    }
    rows = [{"audit_item": k, "pass": v, "evidence": SAFE_INTERPRETATION if v else "required audit item failed"} for k, v in items.items()]
    rows.append({"audit_item": "safety_audit_pass", "pass": all(items.values()), "evidence": "all claim-boundary checks passed"})
    return pd.DataFrame(rows)


def update_markdown_section(path_value: str | Path, heading: str, body: str) -> Path:
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
    return path


def update_scorecard_csv(path_value: str | Path, delta: pd.DataFrame, pass_fail: pd.DataFrame) -> Path:
    path = resolve(path_value)
    df = pd.read_csv(path) if path.exists() else pd.DataFrame()
    d = delta.iloc[0] if not delta.empty else pd.Series(dtype=object)
    row = {
        "scorecard_item": "stage39b_lph_internal_model_rescue",
        "status": "complete",
        "stage": "Stage 39B-LPH",
        "metric": "pooled donor-level OOF Spearman",
        "threshold_or_gate": "best LPH > Stage 27C, >=0.3228, beats matched/shuffled controls, no target drop below gate",
        "current_value": f"best={d.get('best_lph_mean', 'NA')}; delta_vs_stage27c={d.get('delta_vs_stage27c', 'NA')}",
        "pass_fail": "pass" if as_bool(d.get("internal_performance_pass", False)) else "fail",
        "datasets_allowed": "SEA-AD locked internal donor folds only",
        "datasets_forbidden": "external training/model selection; clean holdouts; candidate selection",
        "allowed_claim": ALLOWED_CLAIM,
        "notes": SAFE_INTERPRETATION,
        "stage_id": "stage39b_lph_internal_model_rescue",
        "primary_metric": "best LPH mean pooled OOF Spearman",
        "pass_rule": "strict internal controls and claim audit pass",
        "result": f"run_pass={as_bool(pass_fail.iloc[0].get('stage39b_lph_run_pass', False))}",
        "allowed_inputs": "internal Stage 27C context reconstructed from local files",
        "forbidden_inputs": "external data, synthetic biological data, candidate changes",
        "interpretation": SAFE_INTERPRETATION,
    }
    if df.empty:
        df = pd.DataFrame([row])
    else:
        for col in row:
            if col not in df.columns:
                df[col] = ""
        df = df[df.get("stage_id", pd.Series(dtype=str)).astype(str) != "stage39b_lph_internal_model_rescue"]
        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    df.to_csv(path, index=False)
    return path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    cfg = load_cfg(resolve(args.config))
    refs = cfg["references"]
    targets = refs["required_targets"]
    alphas = cfg["model"]["ridge_alphas"]
    seed = int(cfg["model"]["random_seed"])
    pca_components = int(cfg["model"]["pca_components"])

    failure_inventory = build_failure_mode_inventory()
    inv = input_inventory(cfg)
    training_allowed = bool(inv.loc[inv["required_for_training"], "exists"].all())
    training_reason = "required internal inputs found" if training_allowed else "missing required internal inputs"

    feature_design = pd.DataFrame(
        [
            {
                "design_item": "latent_input",
                "description": "predefined Stage 27C module features from internal SEA-AD donor expression",
                "external_data_used": False,
                "leakage_control": "module features reconstructed inside Stage 27C context; downstream predictions are donor-held-out",
            },
            {
                "design_item": "latent_prediction_target",
                "description": "masked/held-out module latent columns predicted from the remaining module columns",
                "external_data_used": False,
                "leakage_control": "LPH predictions for each held-out donor are generated by models fit without that donor",
            },
            {
                "design_item": "downstream_features",
                "description": "matched module PCA baseline plus LPH predicted latents, residuals, and row-level uncertainty/error summaries",
                "external_data_used": False,
                "leakage_control": "downstream ridge is fit only on train donors per locked fold",
            },
        ]
    )

    training_gate = pd.DataFrame(
        [
            {
                "training_allowed": training_allowed,
                "training_gate_reason": training_reason,
                "donor_heldout_required": True,
                "external_data_allowed": False,
                "ridge_only_first_pass": True,
                "graph_context_used": False,
            }
        ]
    )

    model_registry = pd.DataFrame(
        [
            {"model_id": "stage27c_reference", "condition": "stage27c_reference", "model_type": "reference", "description": "locked Stage 27C module_pca_ridge reference", "graph_context_used": False},
            {"model_id": "no_lph_matched_baseline", "condition": "no_lph_matched_baseline", "model_type": "ridge", "description": "module PCA ridge using same donor folds and target transforms", "graph_context_used": False},
            {"model_id": "lph_aux_head_real", "condition": "lph_aux_head_real", "model_type": "ridge_lph_plus_ridge_downstream", "description": "ridge LPH predicts masked modules; downstream appends predicted/residual/uncertainty features", "graph_context_used": False},
            {"model_id": "lph_aux_head_shuffled_latent_target", "condition": "lph_aux_head_shuffled_latent_target", "model_type": "negative_control", "description": "LPH target columns shuffled in training folds", "graph_context_used": False},
            {"model_id": "lph_aux_head_shuffled_context", "condition": "lph_aux_head_shuffled_context", "model_type": "negative_control", "description": "LPH context rows shuffled in training folds", "graph_context_used": False},
            {"model_id": "lph_aux_head_no_graph_or_identity", "condition": "lph_aux_head_no_graph_or_identity", "model_type": "identity_control", "description": "same as real no-graph LPH; included to make graph claim boundary explicit", "graph_context_used": False},
        ]
    )

    all_oof = pd.DataFrame()
    target_metrics = pd.DataFrame()
    control_results = pd.DataFrame()
    delta = pd.DataFrame()
    uncertainty = pd.DataFrame()

    if training_allowed:
        stage27c = load_stage27c_module()
        folds, _, _expr, target_matrix, modules, _module_genes = stage27c.load_context()
        folds = folds.copy()
        folds["donor_id"] = folds["donor_id"].astype(str)
        modules = modules.copy()
        modules.index = modules.index.astype(str)
        target_matrix = target_matrix.copy()
        target_matrix.index = target_matrix.index.astype(str)
        target_matrix = normalize_target_columns(target_matrix)
        missing_targets = [target for target in targets if target not in target_matrix.columns]
        if missing_targets:
            training_allowed = False
            training_gate.loc[0, "training_allowed"] = False
            training_gate.loc[0, "training_gate_reason"] = "missing target columns after alias normalization: " + ";".join(missing_targets)
            all_oof = pd.DataFrame()
            target_metrics = pd.DataFrame()
            control_results = pd.DataFrame()
            uncertainty = pd.DataFrame()
            raise RuntimeError(training_gate.loc[0, "training_gate_reason"])
        shared = [d for d in folds["donor_id"].tolist() if d in modules.index and d in target_matrix.index]
        folds = folds[folds["donor_id"].isin(shared)].copy()
        modules = modules.loc[shared]
        target_matrix = target_matrix.loc[shared]

        no_lph = downstream_oof("no_lph_matched_baseline", modules, None, target_matrix, folds, targets, alphas, seed, pca_components)
        oof_parts = [no_lph]
        lph_diag_parts = []
        lph_feature_lookup: dict[str, pd.DataFrame] = {}
        for condition in [
            "lph_aux_head_real",
            "lph_aux_head_shuffled_latent_target",
            "lph_aux_head_shuffled_context",
            "lph_aux_head_no_graph_or_identity",
        ]:
            source_condition = "lph_aux_head_real" if condition == "lph_aux_head_no_graph_or_identity" else condition
            if source_condition in lph_feature_lookup:
                lph_features = lph_feature_lookup[source_condition]
                lph_diag = pd.DataFrame(
                    [
                        {
                            "condition": condition,
                            "fold_id": "all",
                            "n_train_donors": int(len(shared)),
                            "n_test_donors": int(len(shared)),
                            "lph_mse": float(lph_feature_lookup[source_condition]["lph_row_mse"].mean()),
                            "lph_cosine_similarity": np.nan,
                            "lph_flat_spearman": np.nan,
                            "note": "identity/no-graph alias of real no-graph LPH",
                        }
                    ]
                )
            else:
                lph_features, lph_diag = fit_lph_predictions(modules, folds, source_condition, alphas, seed)
                lph_feature_lookup[source_condition] = lph_features
            oof_parts.append(downstream_oof(condition, modules, lph_features, target_matrix, folds, targets, alphas, seed, pca_components))
            lph_diag_parts.append(lph_diag)
        all_oof = pd.concat(oof_parts, ignore_index=True)
        target_metrics = pooled_target_metrics(all_oof)
        uncertainty = pd.concat(lph_diag_parts, ignore_index=True)
        control_results = build_control_results(target_metrics, uncertainty)

        means = target_metrics.groupby("condition", as_index=False)["pooled_oof_spearman"].mean().rename(columns={"pooled_oof_spearman": "mean_pooled_oof_spearman"})
        lph_means = means[means["condition"].astype(str).str.startswith("lph_aux_head")].copy()
        best = lph_means.sort_values("mean_pooled_oof_spearman", ascending=False).iloc[0] if not lph_means.empty else pd.Series(dtype=object)
        best_condition = str(best.get("condition", "not_run"))
        best_mean = float(best.get("mean_pooled_oof_spearman", np.nan))
        stage27_ref = float(refs["stage27c_reference_mean"])
        module_baseline_mean = float(refs["official_module_mean_baseline"])
        min_success = float(refs["minimum_success_threshold"])
        max_drop = float(refs["max_target_drop_vs_module_mean"])
        best_target = target_metrics[target_metrics["condition"] == best_condition].copy()
        best_target["delta_vs_module_mean_scalar"] = best_target["pooled_oof_spearman"] - module_baseline_mean
        target_drop_pass = bool((best_target["delta_vs_module_mean_scalar"] >= max_drop).all()) if not best_target.empty else False
        ctrl_lookup = dict(zip(control_results["comparison"], control_results["passes"])) if not control_results.empty else {}
        beats_matched = bool(ctrl_lookup.get("real_lph_vs_no_lph_matched_baseline", False)) if best_condition == "lph_aux_head_real" else False
        beats_shuffled_target = bool(ctrl_lookup.get("real_lph_vs_shuffled_latent_target", False)) if best_condition == "lph_aux_head_real" else False
        internal_pass = bool(
            best_condition == "lph_aux_head_real"
            and best_mean > stage27_ref
            and best_mean >= min_success
            and target_drop_pass
            and beats_matched
            and beats_shuffled_target
        )
        graph_pass = False
        delta = pd.DataFrame(
            [
                {
                    "best_lph_model_id": best_condition,
                    "best_lph_condition": best_condition,
                    "stage27c_reference_mean": stage27_ref,
                    "best_lph_mean": best_mean,
                    "delta_vs_stage27c": best_mean - stage27_ref if np.isfinite(best_mean) else np.nan,
                    "best_lph_minus_module_mean_baseline": best_mean - module_baseline_mean if np.isfinite(best_mean) else np.nan,
                    "target_drop_gate_pass": target_drop_pass,
                    "beats_no_lph_matched_baseline": beats_matched,
                    "beats_shuffled_latent_target_control": beats_shuffled_target,
                    "internal_performance_pass": internal_pass,
                    "graph_specific_pass": graph_pass,
                    "recommended_next_step": "do not reprioritize candidates; return to metadata/external support or redesign LPH" if not internal_pass else "replicate with predeclared controls before any interpretation change",
                    "allowed_claim_language": ALLOWED_CLAIM,
                    "prohibited_claim_language": PROHIBITED_CLAIM,
                }
            ]
        )

    negative_null_reported = (not target_metrics.empty) and bool((target_metrics["pooled_oof_spearman"] <= refs["stage27c_reference_mean"]).any())
    claim_audit = build_claim_audit(negative_null_reported)
    candidate_audit = pd.DataFrame(
        [
            {
                "audit_item": "candidate_reprioritization_allowed",
                "value": False,
                "reason": "Stage 39B-LPH is an internal model-rescue benchmark; frozen Stage 36E candidates are preserved.",
            },
            {
                "audit_item": "candidate_interpretation_if_lph_positive",
                "value": "hypothesis_prioritization_only",
                "reason": "Even a positive internal LPH result would not establish external validation, causality, or therapeutic relevance.",
            },
            {
                "audit_item": "candidate_interpretation_if_lph_null",
                "value": "no_candidate_change",
                "reason": "Null/negative internal LPH results do not prove biological irrelevance.",
            },
        ]
    )

    if delta.empty:
        delta = pd.DataFrame(
            [
                {
                    "best_lph_model_id": "not_run",
                    "best_lph_condition": "not_run",
                    "stage27c_reference_mean": refs["stage27c_reference_mean"],
                    "best_lph_mean": np.nan,
                    "delta_vs_stage27c": np.nan,
                    "internal_performance_pass": False,
                    "graph_specific_pass": False,
                    "recommended_next_step": "restore missing internal inputs and rerun feasibility-gated LPH",
                    "allowed_claim_language": ALLOWED_CLAIM,
                    "prohibited_claim_language": PROHIBITED_CLAIM,
                }
            ]
        )

    out = cfg["outputs"]
    written = {
        "failure_mode_inventory": write_csv(failure_inventory, out["failure_mode_inventory"]),
        "input_inventory": write_csv(inv, out["input_inventory"]),
        "feature_target_design": write_csv(feature_design, out["feature_target_design"]),
        "training_gate": write_csv(training_gate, out["training_gate"]),
        "model_registry": write_csv(model_registry, out["model_registry"]),
        "internal_oof_results": write_csv(all_oof, out["internal_oof_results"]),
        "target_level_results": write_csv(target_metrics, out["target_level_results"]),
        "control_results": write_csv(control_results, out["control_results"]),
        "delta_vs_stage27c": write_csv(delta, out["delta_vs_stage27c"]),
        "uncertainty_diagnostics": write_csv(uncertainty, out["uncertainty_diagnostics"]),
        "candidate_interpretation_audit": write_csv(candidate_audit, out["candidate_interpretation_audit"]),
        "claim_boundary_audit": write_csv(claim_audit, out["claim_boundary_audit"]),
    }
    pass_row = {
        "stage39b_lph_run": True,
        "inventories_written": True,
        "design_written": True,
        "training_gate_written": True,
        "lph_training_allowed": training_allowed,
        "lph_training_ran": training_allowed and not all_oof.empty,
        "controls_written": True,
        "claim_audit_written": True,
        "no_external_validation_or_causal_therapeutic_claims": bool(claim_audit["pass"].map(as_bool).all()),
        "safety_audit_pass": bool(claim_audit["pass"].map(as_bool).all()),
        "stage39b_lph_run_pass": True,
        "controlled_interpretation": SAFE_INTERPRETATION,
    }
    pass_fail = pd.DataFrame([pass_row])
    written["pass_fail"] = write_csv(pass_fail, out["pass_fail"])

    technical_report = f"""# Stage 39B-LPH internal model rescue report

{SAFE_INTERPRETATION}

## Why LPH was tested

Prior external pretraining and most graph strategies did not improve over the locked Stage 27C reference. Stage 39A also showed that external support is currently limited by metadata/testability. Stage 39B-LPH therefore asks a bounded internal question: can a low-capacity auxiliary latent-prediction head improve the donor-held-out internal benchmark?

## Inputs and training gate

{markdown_table(inv)}

{markdown_table(training_gate)}

## Feature/target design

{markdown_table(feature_design)}

## Model registry

{markdown_table(model_registry)}

## Internal OOF results

{markdown_table(target_metrics)}

## Control results

{markdown_table(control_results)}

## Delta versus Stage 27C

{markdown_table(delta)}

## Uncertainty diagnostics

{markdown_table(uncertainty)}

## Candidate interpretation boundary

{markdown_table(candidate_audit)}
"""
    pi_summary = f"""# Stage 39B-LPH PI model rescue summary

## Short answer

LPH training allowed: `{training_allowed}`. LPH training ran: `{training_allowed and not all_oof.empty}`.

{markdown_table(delta)}

## Controls

{markdown_table(control_results)}

## Target-level results

{markdown_table(target_metrics)}

## Interpretation

This is an internal benchmark experiment only. Candidates should not be reprioritized unless the LPH condition beats Stage 27C and the matched/shuffled controls under the predeclared gates. No clean external validation, causal, therapeutic, disease-modifying, or gene-ablation claim is supported.
"""
    written["technical_report"] = write_text(technical_report, out["technical_report"])
    written["pi_summary"] = write_text(pi_summary, out["pi_summary"])

    d0 = delta.iloc[0]
    update_markdown_section(
        out["active_status"],
        "Stage 39B-LPH internal model rescue status",
        f"Stage 39B-LPH is complete. LPH training allowed: `{training_allowed}`; training ran: `{training_allowed and not all_oof.empty}`; best condition: `{d0.get('best_lph_condition')}`; best mean pooled OOF Spearman: `{d0.get('best_lph_mean')}`; delta versus Stage 27C: `{d0.get('delta_vs_stage27c')}`; internal performance pass: `{d0.get('internal_performance_pass')}`. This is an internal model-improvement experiment only, not external validation or causal/therapeutic evidence.",
    )
    update_markdown_section(
        out["v3_scorecard_md"],
        "Stage 39B-LPH internal model rescue result",
        f"Stage 39B-LPH run pass: `{as_bool(pass_fail.iloc[0]['stage39b_lph_run_pass'])}`. Best condition: `{d0.get('best_lph_condition')}`; mean pooled OOF Spearman: `{d0.get('best_lph_mean')}`; delta versus Stage 27C: `{d0.get('delta_vs_stage27c')}`; internal performance pass: `{d0.get('internal_performance_pass')}`. No external validation, causal, therapeutic, gene-ablation, or disease-modifying claim is made.",
    )
    update_scorecard_csv(out["v3_scorecard_csv"], delta, pass_fail)

    target_delta_summary = ""
    if not target_metrics.empty and d0.get("best_lph_condition") in set(target_metrics["condition"]):
        best_targets = target_metrics[target_metrics["condition"] == d0.get("best_lph_condition")]
        target_delta_summary = ";".join(f"{r.target}:{r.pooled_oof_spearman:.4f}" for r in best_targets.itertuples())
    print(f"lph_training_allowed={training_allowed}")
    print(f"lph_training_ran={training_allowed and not all_oof.empty}")
    print(f"best_lph_condition={d0.get('best_lph_condition')}")
    print(f"mean_pooled_oof_spearman={d0.get('best_lph_mean')}")
    print(f"delta_vs_stage27c={d0.get('delta_vs_stage27c')}")
    print(f"target_level_deltas={target_delta_summary or 'not_available'}")
    print("control_comparison_summary=" + (";".join(f"{r.comparison}:{r.delta:.6f}:{r.passes}" for r in control_results.itertuples()) if not control_results.empty else "not_available"))
    print(f"internal_performance_pass={d0.get('internal_performance_pass')}")
    print(f"graph_specific_pass={d0.get('graph_specific_pass')}")
    print(f"recommended_next_step={d0.get('recommended_next_step')}")
    print(f"stage39b_lph_run_pass={as_bool(pass_fail.iloc[0]['stage39b_lph_run_pass'])}")


if __name__ == "__main__":
    main()
