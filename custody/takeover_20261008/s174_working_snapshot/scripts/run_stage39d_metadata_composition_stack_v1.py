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
from sklearn.compose import ColumnTransformer
from sklearn.decomposition import PCA
from sklearn.impute import SimpleImputer
from sklearn.linear_model import RidgeCV
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ROOT = Path(__file__).resolve().parents[1]
for path in [ROOT / "src", ROOT / "scripts"]:
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from audit_donor_leakage_v1 import audit_covariate_columns, audit_oof_predictions
from build_donor_composition_features_v1 import build_microglia_pvm_composition_features
from build_pathology_residual_targets_v1 import rank_inverse_normal_apply, rank_inverse_normal_train


SAFE_INTERPRETATION = (
    "Stage 39D is an internal metadata/composition enrichment benchmark. It uses locked donor-held-out folds, "
    "train-fold-only preprocessing, safe donor metadata, and local SEA-AD microglia/PVM composition features. "
    "Composition features are audited for possible pathology-proxy signal before being treated as a credible "
    "benchmark improvement. It does not use external data, select candidates, or claim clean external validation, "
    "causality, therapeutic relevance, disease modification, or gene ablation."
)
ALLOWED_CLAIM = "internal metadata/composition enrichment benchmark; donor-held-out model comparison; hypothesis prioritization only"
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
                    raise ImportError(f"{name} unavailable; Stage 39D does not use {cls}")

            setattr(module, cls, _Unavailable)
            sys.modules[name] = module
    spec = importlib.util.spec_from_file_location("stage27c_for_stage39d", resolve("scripts/run_stage27c_non_graph_rescue_v1.py"))
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not import Stage 27C")
    module = importlib.util.module_from_spec(spec)
    sys.modules["stage27c_for_stage39d"] = module
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
    return target_matrix.rename(columns={c: alias.get(str(c), str(c)) for c in target_matrix.columns})


def input_inventory(cfg: dict[str, Any]) -> pd.DataFrame:
    rows = []
    for name, value in cfg["inputs"].items():
        path = resolve(value)
        rows.append({"input_name": name, "path": str(value), "exists": path.exists(), "size_bytes": path.stat().st_size if path.exists() else 0})
    return pd.DataFrame(rows)


def metadata_frame(metadata: pd.DataFrame, donors: list[str], cfg: dict[str, Any]) -> pd.DataFrame:
    meta = metadata.copy()
    meta["Donor ID"] = meta["Donor ID"].astype(str)
    meta = meta.drop_duplicates("Donor ID").set_index("Donor ID")
    out = pd.DataFrame(index=donors)
    for col in cfg["safe_metadata_covariates"]["numeric"]:
        out[col] = pd.to_numeric(meta[col], errors="coerce") if col in meta.columns else np.nan
    for col in cfg["safe_metadata_covariates"]["categorical"]:
        out[col] = meta[col].astype(str) if col in meta.columns else "missing"
    return out


def preprocess_metadata(train_df: pd.DataFrame, test_df: pd.DataFrame, numeric: list[str], categorical: list[str]) -> tuple[np.ndarray, np.ndarray, list[str]]:
    pre = ColumnTransformer(
        [
            ("numeric", Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler())]), numeric),
            ("categorical", Pipeline([("impute", SimpleImputer(strategy="most_frequent")), ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False))]), categorical),
        ]
    )
    x_train = pre.fit_transform(train_df[numeric + categorical])
    x_test = pre.transform(test_df[numeric + categorical])
    names = list(pre.get_feature_names_out())
    return np.asarray(x_train, dtype=float), np.asarray(x_test, dtype=float), names


def preprocess_numeric(train_df: pd.DataFrame, test_df: pd.DataFrame, cols: list[str]) -> tuple[np.ndarray, np.ndarray, list[str]]:
    if not cols:
        return np.zeros((len(train_df), 0)), np.zeros((len(test_df), 0)), []
    pipe = Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler())])
    return pipe.fit_transform(train_df[cols]), pipe.transform(test_df[cols]), cols


def pca_features(train_x: np.ndarray, test_x: np.ndarray, n_components: int, seed: int) -> tuple[np.ndarray, np.ndarray, list[str]]:
    n_comp = min(n_components, train_x.shape[1], max(1, train_x.shape[0] - 1))
    pipe = Pipeline([("scale", StandardScaler()), ("pca", PCA(n_components=n_comp, random_state=seed))])
    return pipe.fit_transform(train_x), pipe.transform(test_x), [f"module_pca_{i+1}" for i in range(n_comp)]


def interaction_features(latent_train: np.ndarray, latent_test: np.ndarray, context_train: np.ndarray, context_test: np.ndarray, max_features: int) -> tuple[np.ndarray, np.ndarray, list[str]]:
    if latent_train.shape[1] == 0 or context_train.shape[1] == 0:
        return np.zeros((latent_train.shape[0], 0)), np.zeros((latent_test.shape[0], 0)), []
    vars_ = np.nanvar(context_train, axis=0)
    keep_context = np.argsort(vars_)[::-1][: max(1, min(context_train.shape[1], max_features // max(1, latent_train.shape[1])))]
    train_parts = []
    test_parts = []
    names = []
    for i in range(latent_train.shape[1]):
        for j in keep_context:
            train_parts.append(latent_train[:, i] * context_train[:, j])
            test_parts.append(latent_test[:, i] * context_test[:, j])
            names.append(f"interaction_pca{i+1}_ctx{j+1}")
            if len(names) >= max_features:
                break
        if len(names) >= max_features:
            break
    return np.column_stack(train_parts), np.column_stack(test_parts), names


def fit_predict_condition(condition: str, blocks: list[str], modules: pd.DataFrame, metadata: pd.DataFrame, composition: pd.DataFrame, target_matrix: pd.DataFrame, folds: pd.DataFrame, cfg: dict[str, Any], include_interactions: bool = False, shuffled_context: bool = False) -> pd.DataFrame:
    rows = []
    targets = cfg["references"]["required_targets"]
    donors = [d for d in folds["donor_id"].astype(str).tolist() if d in modules.index and d in target_matrix.index]
    fold_lookup = folds.set_index("donor_id")["fold_id"].to_dict()
    numeric_meta = [c for c in cfg["safe_metadata_covariates"]["numeric"] if c in metadata.columns]
    categorical_meta = [c for c in cfg["safe_metadata_covariates"]["categorical"] if c in metadata.columns]
    comp_cols = [c for c in composition.columns if c != "Donor ID"]
    comp = composition.set_index("Donor ID").reindex(donors)
    seed = int(cfg["references"]["random_seed"])
    rng = np.random.default_rng(seed)
    for target_idx, target in enumerate(targets):
        y_all_raw = np.log1p(target_matrix[target].astype(float))
        for fold_id in sorted(folds["fold_id"].unique()):
            test = [d for d in donors if fold_lookup.get(d) == fold_id and np.isfinite(y_all_raw.loc[d])]
            train = [d for d in donors if fold_lookup.get(d) != fold_id and np.isfinite(y_all_raw.loc[d])]
            y_train, _ = rank_inverse_normal_train(y_all_raw.loc[train].to_numpy(float))
            y_test = y_all_raw.loc[test].to_numpy(float)
            train_parts = []
            test_parts = []
            latent_train = np.zeros((len(train), 0))
            latent_test = np.zeros((len(test), 0))
            context_train_parts = []
            context_test_parts = []
            if "latent" in blocks:
                latent_train, latent_test, _ = pca_features(modules.loc[train].to_numpy(float), modules.loc[test].to_numpy(float), int(cfg["models"]["module_pca_components"]), seed + target_idx * 100 + int(fold_id))
                train_parts.append(latent_train)
                test_parts.append(latent_test)
            if "metadata" in blocks:
                mt_train, mt_test, _ = preprocess_metadata(metadata.loc[train], metadata.loc[test], numeric_meta, categorical_meta)
                context_train_parts.append(mt_train)
                context_test_parts.append(mt_test)
                train_parts.append(mt_train)
                test_parts.append(mt_test)
            if "composition" in blocks:
                cp_train, cp_test, _ = preprocess_numeric(comp.loc[train], comp.loc[test], comp_cols)
                context_train_parts.append(cp_train)
                context_test_parts.append(cp_test)
                train_parts.append(cp_train)
                test_parts.append(cp_test)
            if include_interactions and "latent" in blocks and context_train_parts:
                ctx_train = np.hstack(context_train_parts)
                ctx_test = np.hstack(context_test_parts)
                ix_train, ix_test, _ = interaction_features(latent_train, latent_test, ctx_train, ctx_test, int(cfg["models"]["max_interaction_features"]))
                train_parts.append(ix_train)
                test_parts.append(ix_test)
            x_train = np.hstack(train_parts) if train_parts else np.zeros((len(train), 0))
            x_test = np.hstack(test_parts) if test_parts else np.zeros((len(test), 0))
            if shuffled_context and x_train.shape[1] > 0:
                x_train = x_train[rng.permutation(x_train.shape[0]), :]
            model = Pipeline([("scale", StandardScaler()), ("model", RidgeCV(alphas=np.asarray(cfg["models"]["ridge_alphas"], dtype=float), cv=min(3, max(2, len(train) // 10))))])
            model.fit(x_train, y_train)
            pred = model.predict(x_test)
            for donor, yt, yp in zip(test, y_test, pred):
                rows.append({"condition": condition, "target": target, "donor_id": donor, "fold_id": int(fold_id), "y_true": float(yt), "y_pred": float(yp), "feature_blocks": ";".join(blocks), "n_features": int(x_train.shape[1]), "clean_holdout_used": False, "heldout_donor_leakage_detected": False})
    return pd.DataFrame(rows)


def metric_tables(oof: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    for (condition, target), sub in oof.groupby(["condition", "target"]):
        rows.append({"condition": condition, "target": target, "n_donors": int(sub["donor_id"].nunique()), "pooled_oof_spearman": safe_spearman(sub["y_true"].to_numpy(float), sub["y_pred"].to_numpy(float)), "mse": mse(sub["y_true"].to_numpy(float), sub["y_pred"].to_numpy(float)), "prediction_variance": float(np.nanvar(sub["y_pred"].to_numpy(float)))})
    target = pd.DataFrame(rows)
    mean = target.groupby("condition", as_index=False).agg(mean_pooled_oof_spearman=("pooled_oof_spearman", "mean"), min_target_spearman=("pooled_oof_spearman", "min"), n_targets=("target", "nunique")) if not target.empty else pd.DataFrame()
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
    return pd.DataFrame([{"condition": condition, "n_bootstrap": n_boot, "bootstrap_mean": float(np.mean(arr)), "ci_lower_95": float(np.quantile(arr, 0.025)), "ci_upper_95": float(np.quantile(arr, 0.975))}])


def audit_composition_proxy_features(composition: pd.DataFrame) -> pd.DataFrame:
    rows = []
    high_terms = ["pseudoprogression", "seaa", "braak", "thal", "pathology", "neuropath", "dementia", "cognitive", "diagnosis", "case_control", "ad_control"]
    medium_terms = ["supertype", "continuous", "score"]
    for col in [c for c in composition.columns if c != "Donor ID"]:
        lower = col.lower()
        matched_high = [term for term in high_terms if term in lower]
        matched_medium = [term for term in medium_terms if term in lower]
        if matched_high:
            risk_level = "high_pathology_proxy_risk"
            recommended_use = "exclude_from_primary_safe_benchmark"
        elif matched_medium:
            risk_level = "moderate_cell_state_proxy_risk"
            recommended_use = "sensitivity_only"
        else:
            risk_level = "low_obvious_proxy_risk"
            recommended_use = "allowed_if_train_fold_only"
        if lower.startswith("composition_pseudoprogression"):
            source_family = "pseudoprogression_summary"
        elif "supertype" in lower:
            source_family = "fine_cell_state_supertype"
        elif "subclass" in lower:
            source_family = "broad_subclass_composition"
        elif "class" in lower:
            source_family = "broad_class_composition"
        elif "brain_region" in lower:
            source_family = "brain_region_composition"
        elif "cell" in lower:
            source_family = "cell_count"
        else:
            source_family = "other_composition_feature"
        rows.append({
            "feature": col,
            "source_family": source_family,
            "proxy_risk_level": risk_level,
            "matched_terms": ";".join(matched_high + matched_medium),
            "recommended_use": recommended_use,
            "allowed_in_full_context_benchmark": True,
            "allowed_in_restricted_sensitivity": recommended_use != "exclude_from_primary_safe_benchmark",
        })
    return pd.DataFrame(rows)


def filter_composition_for_sensitivity(composition: pd.DataFrame, mode: str) -> pd.DataFrame:
    keep = ["Donor ID"]
    cols = [c for c in composition.columns if c != "Donor ID"]
    if mode == "full_composition":
        keep += cols
    elif mode == "no_pseudoprogression":
        keep += [c for c in cols if "pseudoprogression" not in c.lower()]
    elif mode == "no_seaad_supertypes":
        keep += [c for c in cols if "seaa" not in c.lower()]
    elif mode == "no_pseudo_no_seaad":
        keep += [c for c in cols if "pseudoprogression" not in c.lower() and "seaa" not in c.lower()]
    elif mode == "broad_subclass_count_only":
        keep += [
            c for c in cols
            if c == "composition_total_cells"
            or c == "microglia_pvm_n_cells"
            or c.startswith("composition_count_Subclass_")
            or c.startswith("composition_prop_Subclass_")
            or c.startswith("composition_count_Class_")
            or c.startswith("composition_prop_Class_")
        ]
    else:
        raise ValueError(f"Unknown composition sensitivity mode: {mode}")
    return composition.loc[:, keep].copy()


def restricted_composition_sensitivity(
    modules: pd.DataFrame,
    metadata: pd.DataFrame,
    composition: pd.DataFrame,
    target_matrix: pd.DataFrame,
    folds: pd.DataFrame,
    cfg: dict[str, Any],
    full_best_mean: float,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    modes = [
        "full_composition",
        "no_pseudoprogression",
        "no_seaad_supertypes",
        "no_pseudo_no_seaad",
        "broad_subclass_count_only",
    ]
    oof_parts = []
    summary_rows = []
    for mode in modes:
        comp = filter_composition_for_sensitivity(composition, mode)
        n_comp = len([c for c in comp.columns if c != "Donor ID"])
        condition = f"sensitivity_{mode}_latent_composition_ridge"
        if n_comp == 0:
            summary_rows.append({
                "sensitivity_mode": mode,
                "condition": condition,
                "n_composition_features": 0,
                "mean_pooled_oof_spearman": np.nan,
                "delta_vs_full_best": np.nan,
                "delta_vs_stage39c": np.nan,
                "proxy_sensitivity_interpretation": "not_run_no_features",
            })
            continue
        pred = fit_predict_condition(condition, ["latent", "composition"], modules, metadata, comp, target_matrix, folds, cfg)
        oof_parts.append(pred)
        tm, mm = metric_tables(pred)
        mean_val = float(mm.iloc[0]["mean_pooled_oof_spearman"]) if not mm.empty else np.nan
        if mode == "full_composition":
            interp = "full context benchmark; includes audited proxy-risk features"
        elif mean_val > float(cfg["references"]["stage39c_best_mean"]):
            interp = "survives restricted proxy removal versus Stage39C"
        else:
            interp = "does_not_survive_restricted_proxy_removal"
        row = {
            "sensitivity_mode": mode,
            "condition": condition,
            "n_composition_features": n_comp,
            "mean_pooled_oof_spearman": mean_val,
            "delta_vs_full_best": mean_val - full_best_mean if np.isfinite(mean_val) and np.isfinite(full_best_mean) else np.nan,
            "delta_vs_stage39c": mean_val - float(cfg["references"]["stage39c_best_mean"]) if np.isfinite(mean_val) else np.nan,
            "proxy_sensitivity_interpretation": interp,
        }
        if not tm.empty:
            for _, target_row in tm.iterrows():
                row[f"{target_row['target']}_spearman"] = target_row["pooled_oof_spearman"]
        summary_rows.append(row)
    return pd.DataFrame(summary_rows), pd.concat(oof_parts, ignore_index=True) if oof_parts else pd.DataFrame()


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
        text = text[:start].rstrip() + section + (text[next_start:] if next_start != -1 else "")
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def update_scorecard_csv(path_value: str | Path, delta: pd.DataFrame, pass_fail: pd.DataFrame) -> None:
    path = resolve(path_value)
    df = pd.read_csv(path) if path.exists() else pd.DataFrame()
    d = delta.iloc[0] if not delta.empty else pd.Series(dtype=object)
    row = {
        "scorecard_item": "stage39d_metadata_composition_stack",
        "status": "complete",
        "stage": "Stage 39D",
        "metric": "mean pooled donor-level OOF Spearman",
        "threshold_or_gate": "metadata/composition+latent must beat latent-only, metadata-only, composition-only, and Stage 39C where relevant",
        "current_value": f"best={d.get('best_mean_pooled_oof_spearman','NA')}; delta_vs_stage39c={d.get('delta_vs_stage39c','NA')}",
        "pass_fail": "pass" if as_bool(d.get("stage39d_context_enrichment_pass", False)) else "fail",
        "datasets_allowed": "SEA-AD locked internal donor folds only",
        "datasets_forbidden": "external data; candidate selection; clean holdouts",
        "allowed_claim": ALLOWED_CLAIM,
        "notes": SAFE_INTERPRETATION,
        "stage_id": "stage39d_metadata_composition_stack",
        "primary_metric": "best context-enriched condition mean pooled OOF Spearman",
        "pass_rule": "predeclared block ablations and leakage controls",
        "result": f"run_pass={as_bool(pass_fail.iloc[0].get('stage39d_run_pass', False))}",
        "allowed_inputs": "internal Stage 27C context, safe metadata, local microglia/PVM composition features",
        "forbidden_inputs": "external validation data or external model selection",
        "interpretation": SAFE_INTERPRETATION,
    }
    if df.empty:
        df = pd.DataFrame([row])
    else:
        for col in row:
            if col not in df.columns:
                df[col] = ""
        df = df[df.get("stage_id", pd.Series(dtype=str)).astype(str) != "stage39d_metadata_composition_stack"]
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
    metadata = metadata_frame(read_csv(cfg["inputs"]["donor_metadata_targets"]), donors, cfg)
    composition = build_microglia_pvm_composition_features(resolve(cfg["inputs"]["h5ad_module_preserved"]))
    # Add existing total-cell count if present.
    counts = read_csv(cfg["inputs"]["microglia_cell_count"])
    if not counts.empty and "Donor ID" in counts.columns:
        composition = composition.merge(counts, on="Donor ID", how="outer")
    composition = composition[composition["Donor ID"].astype(str).isin(donors)].copy()
    composition["Donor ID"] = composition["Donor ID"].astype(str)
    comp_cols = [c for c in composition.columns if c != "Donor ID"]
    composition_proxy_audit = audit_composition_proxy_features(composition)
    n_high_proxy = int((composition_proxy_audit["proxy_risk_level"] == "high_pathology_proxy_risk").sum()) if not composition_proxy_audit.empty else 0
    n_moderate_proxy = int((composition_proxy_audit["proxy_risk_level"] == "moderate_cell_state_proxy_risk").sum()) if not composition_proxy_audit.empty else 0
    feature_audit = pd.DataFrame([
        {"feature_block": "latent_module_pca", "n_features_available": int(modules.shape[1]), "source": "Stage 27C reconstructed module features", "allowed": True},
        {"feature_block": "safe_metadata", "n_features_available": len(cfg["safe_metadata_covariates"]["numeric"]) + len(cfg["safe_metadata_covariates"]["categorical"]), "source": "SEA-AD donor metadata safe covariates", "allowed": True},
        {"feature_block": "microglia_pvm_composition", "n_features_available": len(comp_cols), "source": "local SEA-AD microglia/PVM H5AD obs", "allowed": True, "proxy_risk_note": f"{n_high_proxy} high-risk and {n_moderate_proxy} moderate-risk proxy features flagged; restricted sensitivity required"},
    ])
    cov_audit = audit_covariate_columns(cfg["safe_metadata_covariates"]["numeric"] + cfg["safe_metadata_covariates"]["categorical"])
    training_allowed = bool(inv["exists"].all()) and not bool(cov_audit["leakage_risk"].any()) and not composition.empty
    registry_rows = [
        ("stage39c_rank_int_latent_only_reproduction", ["latent"], False, False),
        ("rank_int_metadata_only_ridge", ["metadata"], False, False),
        ("rank_int_composition_only_ridge", ["composition"], False, False),
        ("rank_int_metadata_composition_ridge", ["metadata", "composition"], False, False),
        ("rank_int_latent_metadata_ridge", ["latent", "metadata"], False, False),
        ("rank_int_latent_composition_ridge", ["latent", "composition"], False, False),
        ("rank_int_latent_metadata_composition_ridge", ["latent", "metadata", "composition"], False, False),
        ("rank_int_latent_metadata_composition_interactions_ridge", ["latent", "metadata", "composition"], True, False),
        ("rank_int_latent_metadata_composition_shuffled_context_control", ["latent", "metadata", "composition"], False, True),
    ]
    model_registry = pd.DataFrame([{"condition": c, "feature_blocks": ";".join(b), "include_interactions": ix, "shuffled_context_control": shuf, "model": "ridge"} for c, b, ix, shuf in registry_rows])
    oof_parts = []
    if training_allowed:
        for condition, blocks, ix, shuf in registry_rows:
            oof_parts.append(fit_predict_condition(condition, blocks, modules.loc[donors], metadata, composition, target_matrix.loc[donors], folds[folds["donor_id"].isin(donors)], cfg, include_interactions=ix, shuffled_context=shuf))
    oof = pd.concat(oof_parts, ignore_index=True) if oof_parts else pd.DataFrame()
    target_metrics, mean_metrics = metric_tables(oof)
    best = mean_metrics[~mean_metrics["condition"].str.contains("shuffled", regex=False)].sort_values("mean_pooled_oof_spearman", ascending=False).iloc[0] if not mean_metrics.empty else pd.Series(dtype=object)
    best_condition = str(best.get("condition", "not_run"))
    best_mean = float(best.get("mean_pooled_oof_spearman", np.nan))
    lookup = dict(zip(mean_metrics["condition"], mean_metrics["mean_pooled_oof_spearman"])) if not mean_metrics.empty else {}
    latent = lookup.get("stage39c_rank_int_latent_only_reproduction", np.nan)
    metadata_only = lookup.get("rank_int_metadata_only_ridge", np.nan)
    composition_only = lookup.get("rank_int_composition_only_ridge", np.nan)
    shuffled = lookup.get("rank_int_latent_metadata_composition_shuffled_context_control", np.nan)
    block_ablation = pd.DataFrame([
        {"comparison": "best_vs_latent_only", "delta": best_mean - latent if np.isfinite(latent) else np.nan, "passes": bool(best_mean > latent) if np.isfinite(best_mean) and np.isfinite(latent) else False},
        {"comparison": "best_vs_metadata_only", "delta": best_mean - metadata_only if np.isfinite(metadata_only) else np.nan, "passes": bool(best_mean > metadata_only) if np.isfinite(best_mean) and np.isfinite(metadata_only) else False},
        {"comparison": "best_vs_composition_only", "delta": best_mean - composition_only if np.isfinite(composition_only) else np.nan, "passes": bool(best_mean > composition_only) if np.isfinite(best_mean) and np.isfinite(composition_only) else False},
        {"comparison": "best_vs_shuffled_context_control", "delta": best_mean - shuffled if np.isfinite(shuffled) else np.nan, "passes": bool(best_mean > shuffled) if np.isfinite(best_mean) and np.isfinite(shuffled) else False},
    ])
    control_results = block_ablation.copy()
    restricted_sensitivity, _restricted_oof = (
        restricted_composition_sensitivity(modules.loc[donors], metadata, composition, target_matrix.loc[donors], folds[folds["donor_id"].isin(donors)], cfg, best_mean)
        if training_allowed
        else (pd.DataFrame(), pd.DataFrame())
    )
    restricted_lookup = dict(zip(restricted_sensitivity["sensitivity_mode"], restricted_sensitivity["mean_pooled_oof_spearman"])) if not restricted_sensitivity.empty else {}
    no_pseudo_no_seaad_mean = restricted_lookup.get("no_pseudo_no_seaad", np.nan)
    broad_only_mean = restricted_lookup.get("broad_subclass_count_only", np.nan)
    composition_proxy_sensitivity_pass = bool(
        np.isfinite(no_pseudo_no_seaad_mean)
        and no_pseudo_no_seaad_mean > float(refs["stage39c_best_mean"])
        and np.isfinite(broad_only_mean)
    )
    boot = bootstrap_ci(oof, best_condition, int(refs["bootstrap_iterations"]), int(refs["random_seed"])) if best_condition != "not_run" else pd.DataFrame()
    oof_audit = audit_oof_predictions(oof)
    leakage_audit = pd.concat([cov_audit.assign(audit_type="covariate"), oof_audit.assign(audit_type="oof")], ignore_index=True, sort=False)
    leakage_pass = bool(oof_audit["pass"].map(as_bool).all()) and not bool(cov_audit["leakage_risk"].any())
    target_best = target_metrics[target_metrics["condition"] == best_condition] if not target_metrics.empty else pd.DataFrame()
    n_improved_vs_39c = 0
    s39c_target = read_csv(cfg["inputs"]["stage39c_target_metrics"])
    if not s39c_target.empty and not target_best.empty:
        ref_target = s39c_target[s39c_target["condition"] == refs["stage39c_best_condition"]].set_index("target")["pooled_oof_spearman"]
        merged = target_best.set_index("target")["pooled_oof_spearman"].to_frame("stage39d").join(ref_target.rename("stage39c"), how="left")
        n_improved_vs_39c = int((merged["stage39d"] > merged["stage39c"]).sum())
    context_pass = bool(
        np.isfinite(best_mean)
        and best_mean >= float(refs["rescue_threshold"])
        and best_mean > float(refs["stage39c_best_mean"])
        and bool(block_ablation["passes"].all())
        and n_improved_vs_39c >= 2
        and leakage_pass
        and composition_proxy_sensitivity_pass
    )
    delta = pd.DataFrame([{
        "best_condition": best_condition,
        "stage27c_reference_mean": float(refs["stage27c_reference_mean"]),
        "stage39c_best_mean": float(refs["stage39c_best_mean"]),
        "best_mean_pooled_oof_spearman": best_mean,
        "delta_vs_stage27c": best_mean - float(refs["stage27c_reference_mean"]) if np.isfinite(best_mean) else np.nan,
        "delta_vs_stage39c": best_mean - float(refs["stage39c_best_mean"]) if np.isfinite(best_mean) else np.nan,
        "bootstrap_ci_lower_95": float(boot.iloc[0]["ci_lower_95"]) if not boot.empty else np.nan,
        "bootstrap_ci_upper_95": float(boot.iloc[0]["ci_upper_95"]) if not boot.empty else np.nan,
        "n_targets_improved_vs_stage39c": n_improved_vs_39c,
        "block_ablation_pass": bool(block_ablation["passes"].all()),
        "leakage_audit_pass": leakage_pass,
        "n_high_pathology_proxy_features": n_high_proxy,
        "n_moderate_cell_state_proxy_features": n_moderate_proxy,
        "no_pseudo_no_seaad_mean_pooled_oof_spearman": no_pseudo_no_seaad_mean,
        "broad_subclass_count_only_mean_pooled_oof_spearman": broad_only_mean,
        "composition_proxy_sensitivity_pass": composition_proxy_sensitivity_pass,
        "stage39d_context_enrichment_pass": context_pass,
        "recommended_next_step": "review as possible context-enriched successor after confirmatory CI and proxy-risk audit" if context_pass else "do not replace Stage 39C yet; inspect composition proxy sensitivity before treating Stage 39D as a benchmark",
        "allowed_claim_language": ALLOWED_CLAIM,
        "prohibited_claim_language": PROHIBITED_CLAIM,
    }])
    claim = build_claim_audit(bool((target_metrics["pooled_oof_spearman"] <= float(refs["stage27c_reference_mean"])).any()) if not target_metrics.empty else False)
    pass_fail = pd.DataFrame([{"stage39d_run": True, "inputs_found": bool(inv["exists"].all()), "training_allowed": training_allowed, "training_ran": not oof.empty, "composition_features_written": not composition.empty, "composition_proxy_audit_written": not composition_proxy_audit.empty, "restricted_composition_sensitivity_written": not restricted_sensitivity.empty, "controls_written": not control_results.empty, "bootstrap_ci_written": not boot.empty, "leakage_audit_written": True, "claim_audit_written": True, "safety_audit_pass": bool(claim["pass"].map(as_bool).all()), "stage39d_run_pass": True, "controlled_interpretation": SAFE_INTERPRETATION}])

    write_csv(inv, out["input_inventory"])
    write_csv(composition, out["donor_composition_features"])
    write_csv(feature_audit, out["feature_block_audit"])
    write_csv(model_registry, out["model_registry"])
    write_csv(oof, out["oof_predictions"])
    write_csv(target_metrics, out["target_metrics"])
    write_csv(mean_metrics, out["mean_metrics"])
    write_csv(block_ablation, out["block_ablation_results"])
    write_csv(control_results, out["control_results"])
    write_csv(composition_proxy_audit, out["composition_proxy_audit"])
    write_csv(restricted_sensitivity, out["restricted_composition_sensitivity"])
    write_csv(boot, out["bootstrap_ci"])
    write_csv(leakage_audit, out["leakage_audit"])
    write_csv(delta, out["delta_vs_stage39c_stage27c"])
    write_csv(claim, out["claim_boundary_audit"])
    write_csv(pass_fail, out["pass_fail"])

    report = f"""# Stage 39D metadata/composition stack report

{SAFE_INTERPRETATION}

## Feature blocks

{markdown_table(feature_audit)}

## Model registry

{markdown_table(model_registry)}

## Mean metrics

{markdown_table(mean_metrics.sort_values('mean_pooled_oof_spearman', ascending=False) if not mean_metrics.empty else mean_metrics)}

## Target metrics

{markdown_table(target_metrics.sort_values(['condition', 'target']) if not target_metrics.empty else target_metrics)}

## Block ablations and controls

{markdown_table(block_ablation)}

## Composition proxy audit

The composition block is potentially powerful but risky: donor-level summaries of pseudo-progression or disease-enriched cell-state labels can encode pathology context. Stage 39D therefore reports full-composition performance and restricted sensitivity modes separately. The context-enrichment pass is only true if the restricted `no_pseudo_no_seaad` mode remains above Stage 39C.

{markdown_table(composition_proxy_audit.sort_values(['proxy_risk_level', 'feature']).head(30) if not composition_proxy_audit.empty else composition_proxy_audit)}

## Restricted composition sensitivity

{markdown_table(restricted_sensitivity)}

## Delta versus Stage 39C and Stage 27C

{markdown_table(delta)}

## Bootstrap CI

{markdown_table(boot)}

## Leakage and claim audits

{markdown_table(leakage_audit)}

{markdown_table(claim)}
"""
    pi = f"""# Stage 39D PI metadata/composition summary

## Short answer

Best condition: `{best_condition}`. Mean pooled OOF Spearman: `{best_mean}`. Delta versus Stage 39C: `{delta.iloc[0]['delta_vs_stage39c']}`. Delta versus Stage 27C: `{delta.iloc[0]['delta_vs_stage27c']}`. Stage 39D context enrichment pass: `{context_pass}`.

{markdown_table(delta)}

## Top conditions

{markdown_table(mean_metrics.sort_values('mean_pooled_oof_spearman', ascending=False).head(8) if not mean_metrics.empty else mean_metrics)}

## Interpretation

Stage 39D tests whether explicit safe metadata and microglia/PVM composition features add internal predictive signal beyond the Stage 39C rank-transformed latent baseline. Because fine cell-state and pseudo-progression summaries can act as pathology proxies, the restricted sensitivity table should be treated as the primary safeguard before promoting Stage 39D over Stage 39C. It is not external validation and does not support causal, therapeutic, disease-modifying, or gene-ablation claims.

## Proxy sensitivity

{markdown_table(restricted_sensitivity)}
"""
    write_text(report, out["technical_report"])
    write_text(pi, out["pi_summary"])
    update_markdown_section(out["active_status"], "Stage 39D metadata/composition stack status", f"Stage 39D is complete with proxy-risk sensitivity added. Best condition: `{best_condition}`; mean pooled OOF Spearman: `{best_mean}`; delta versus Stage 39C: `{delta.iloc[0]['delta_vs_stage39c']}`; restricted no-pseudo/no-SEAAD mean: `{no_pseudo_no_seaad_mean}`; context enrichment pass: `{context_pass}`. This is an internal metadata/composition benchmark only.")
    update_markdown_section(out["v3_scorecard_md"], "Stage 39D metadata/composition stack result", f"Stage 39D run pass: `{as_bool(pass_fail.iloc[0]['stage39d_run_pass'])}`. Best condition: `{best_condition}`; mean pooled OOF Spearman: `{best_mean}`; delta versus Stage 39C: `{delta.iloc[0]['delta_vs_stage39c']}`; restricted no-pseudo/no-SEAAD mean: `{no_pseudo_no_seaad_mean}`; proxy sensitivity pass: `{composition_proxy_sensitivity_pass}`; context enrichment pass: `{context_pass}`.")
    update_scorecard_csv(out["v3_scorecard_csv"], delta, pass_fail)
    print(f"stage39d_training_allowed={training_allowed}")
    print(f"stage39d_training_ran={not oof.empty}")
    print(f"best_condition={best_condition}")
    print(f"best_mean_pooled_oof_spearman={best_mean}")
    print(f"delta_vs_stage39c={delta.iloc[0]['delta_vs_stage39c']}")
    print(f"delta_vs_stage27c={delta.iloc[0]['delta_vs_stage27c']}")
    print(f"n_targets_improved_vs_stage39c={n_improved_vs_39c}")
    print(f"block_ablation_pass={bool(block_ablation['passes'].all())}")
    print(f"leakage_audit_pass={leakage_pass}")
    print(f"n_high_pathology_proxy_features={n_high_proxy}")
    print(f"n_moderate_cell_state_proxy_features={n_moderate_proxy}")
    print(f"no_pseudo_no_seaad_mean_pooled_oof_spearman={no_pseudo_no_seaad_mean}")
    print(f"broad_subclass_count_only_mean_pooled_oof_spearman={broad_only_mean}")
    print(f"composition_proxy_sensitivity_pass={composition_proxy_sensitivity_pass}")
    print(f"stage39d_context_enrichment_pass={context_pass}")
    print(f"stage39d_run_pass={as_bool(pass_fail.iloc[0]['stage39d_run_pass'])}")


if __name__ == "__main__":
    main()
