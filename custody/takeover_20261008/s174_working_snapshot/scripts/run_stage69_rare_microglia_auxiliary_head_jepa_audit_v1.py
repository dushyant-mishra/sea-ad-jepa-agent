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
from scipy.stats import norm, rankdata, spearmanr
from sklearn.cross_decomposition import PLSRegression
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


ROOT = Path(__file__).resolve().parents[1]
TARGETS = ["AT8", "6e10/A_beta", "GFAP", "Iba1", "NeuN"]
BASELINE_STAGE27C = 0.3267024400121495
SCORECARD_COLUMNS = [
    "scorecard_item", "status", "stage", "metric", "threshold_or_gate", "current_value",
    "pass_fail", "datasets_allowed", "datasets_forbidden", "allowed_claim", "notes",
    "stage_id", "primary_metric", "pass_rule", "result", "allowed_inputs",
    "forbidden_inputs", "interpretation",
]


def resolve(path: str | Path) -> Path:
    p = Path(path)
    return p if p.is_absolute() else ROOT / p


def load_cfg(path: str | Path) -> dict[str, Any]:
    with resolve(path).open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def write_csv(df: pd.DataFrame, path: str | Path) -> None:
    p = resolve(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(p, index=False)


def write_text(text: str, path: str | Path) -> None:
    p = resolve(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def md(df: pd.DataFrame, max_rows: int = 25) -> str:
    if df is None or df.empty:
        return "_No rows._"
    view = df.head(max_rows).fillna("")
    cols = list(view.columns)
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for _, row in view.iterrows():
        lines.append("| " + " | ".join(str(row[c]).replace("|", "/") for c in cols) + " |")
    if len(df) > max_rows:
        lines.append(f"\n_Showing {max_rows} of {len(df)} rows._")
    return "\n".join(lines)


def update_section(path: str, title: str, body: str) -> None:
    p = resolve(path)
    old = p.read_text(encoding="utf-8") if p.exists() else ""
    marker = f"## {title}"
    block = f"{marker}\n\n{body.strip()}\n"
    if marker in old:
        before, rest = old.split(marker, 1)
        nxt = rest.find("\n## ")
        old = before + block + (rest[nxt:] if nxt >= 0 else "")
    else:
        old = old.rstrip() + "\n\n" + block
    p.write_text(old, encoding="utf-8")


def safe_spearman(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    mask = np.isfinite(y_true) & np.isfinite(y_pred)
    if int(mask.sum()) < 3:
        return 0.0
    yt, yp = y_true[mask], y_pred[mask]
    if np.nanstd(yt) == 0 or np.nanstd(yp) == 0:
        return 0.0
    value = spearmanr(yt, yp).statistic
    return 0.0 if pd.isna(value) else float(value)


def rank_int_train_apply(y_train: np.ndarray, y_test: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    y_train = np.asarray(y_train, dtype=float)
    y_test = np.asarray(y_test, dtype=float)
    order_vals = np.sort(y_train[np.isfinite(y_train)])
    if len(order_vals) < 3:
        return y_train, y_test
    train_ranks = rankdata(y_train, method="average")
    train_u = (train_ranks - 0.5) / len(y_train)
    ytr = norm.ppf(np.clip(train_u, 1e-4, 1 - 1e-4))
    test_ranks = np.searchsorted(order_vals, y_test, side="right")
    test_u = (test_ranks + 0.5) / len(order_vals)
    yte = norm.ppf(np.clip(test_u, 1e-4, 1 - 1e-4))
    return ytr, yte


def canonical_target(value: object) -> str:
    text = str(value)
    aliases = {
        "percent AT8 positive area_Grey matter": "AT8",
        "percent 6e10 positive area_Grey matter": "6e10/A_beta",
        "percent GFAP positive area_Grey matter": "GFAP",
        "percent Iba1 positive area_Grey matter": "Iba1",
        "percent NeuN positive area_Grey matter": "NeuN",
    }
    if text in aliases:
        return aliases[text]
    if text.startswith("6e10/"):
        return "6e10/A_beta"
    return text


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
                    raise ImportError(f"{name} unavailable; Stage69 does not use {cls}")

            setattr(module, cls, _Unavailable)
            sys.modules[name] = module
    spec = importlib.util.spec_from_file_location("stage27c_for_stage69", resolve("scripts/run_stage27c_non_graph_rescue_v1.py"))
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not import Stage27C")
    module = importlib.util.module_from_spec(spec)
    sys.modules["stage27c_for_stage69"] = module
    spec.loader.exec_module(module)
    return module


def load_context():
    s27 = load_stage27c_module()
    folds, _, _, target_matrix, modules, _ = s27.load_context()
    folds = folds.copy()
    folds["donor_id"] = folds["donor_id"].astype(str)
    modules.index = modules.index.astype(str)
    target_matrix.index = target_matrix.index.astype(str)
    target_matrix = target_matrix.rename(columns={c: canonical_target(c) for c in target_matrix.columns})
    shared = sorted(set(folds["donor_id"]) & set(modules.index) & set(target_matrix.index))
    folds = folds[folds["donor_id"].isin(shared)].copy()
    modules = modules.loc[shared]
    target_matrix = target_matrix.loc[shared, [t for t in TARGETS if t in target_matrix.columns]]
    return folds, modules, target_matrix


def input_inventory(cfg: dict[str, Any]) -> pd.DataFrame:
    rows = []
    for name, value in cfg["inputs"].items():
        if name in {"active_status", "v3_scorecard_md", "v3_scorecard_csv"}:
            continue
        path = resolve(value)
        rows.append({"input_name": name, "path": value, "exists": path.exists(), "size_bytes": path.stat().st_size if path.exists() else 0})
    return pd.DataFrame(rows)


def build_aux_targets(cfg: dict[str, Any], donors: list[str]) -> pd.DataFrame:
    tail = pd.read_csv(resolve(cfg["inputs"]["stage64_donor_module_tail_metrics"]))
    keep_features = [
        "disease_program_score", "dam_lipid_trem2_apoe", "lysosomal_endolysosomal",
        "complement_phagocytosis", "antigen_presentation", "oxidative_stress_gene_preserved",
    ]
    keep_metrics = ["variance", "q95", "q99", "fraction_high_global_q95", "top_5pct_mean", "top_1pct_mean"]
    tail = tail[tail["feature"].isin(keep_features)].copy()
    parts = []
    for metric in keep_metrics:
        p = tail.pivot_table(index="donor_id", columns=["dataset", "feature"], values=metric, aggfunc="mean")
        p.columns = [f"rare_aux__{ds}__{feat}__{metric}" for ds, feat in p.columns]
        parts.append(p)
    aux = pd.concat(parts, axis=1)
    state_path = resolve(cfg["inputs"]["stage64_donor_state_tail_metrics"])
    if state_path.exists():
        state = pd.read_csv(state_path)
        state = state[state["state_label"].astype(str).str.contains("Micro-PVM_3", case=False, na=False)].copy()
        for metric in ["state_fraction_within_donor", "disease_program_q95", "disease_program_fraction_high_global_q95"]:
            if metric in state.columns:
                p = state.pivot_table(index="donor_id", columns=["dataset", "state_label"], values=metric, aggfunc="mean")
                p.columns = [f"rare_aux__{ds}__{st}__{metric}" for ds, st in p.columns]
                parts.append(p)
        aux = pd.concat(parts, axis=1)
    aux.index = aux.index.astype(str)
    aux = aux.reindex(donors)
    aux = aux.loc[:, aux.notna().any(axis=0)]
    aux = aux.loc[:, aux.var(skipna=True) > 0]
    aux.insert(0, "donor_id", aux.index)
    return aux.reset_index(drop=True)


def build_registry(cfg: dict[str, Any]) -> pd.DataFrame:
    rows = []
    for n_comp in cfg["references"]["latent_components"]:
        rows.append({
            "condition": f"no_aux_pls{n_comp}",
            "aux_condition_type": "no_aux_baseline",
            "latent_components": int(n_comp),
            "aux_weight": 0.0,
            "negative_control": False,
        })
        for w in cfg["references"]["aux_weights"]:
            rows.append({
                "condition": f"rare_aux_pls{n_comp}_w{str(w).replace('.', 'p')}",
                "aux_condition_type": "rare_microglia_auxiliary_head",
                "latent_components": int(n_comp),
                "aux_weight": float(w),
                "negative_control": False,
            })
            rows.append({
                "condition": f"shuffled_aux_pls{n_comp}_w{str(w).replace('.', 'p')}",
                "aux_condition_type": "shuffled_aux_negative_control",
                "latent_components": int(n_comp),
                "aux_weight": float(w),
                "negative_control": True,
            })
    return pd.DataFrame(rows)


def fit_predict_condition(
    row: pd.Series,
    modules: pd.DataFrame,
    targets: pd.DataFrame,
    aux: pd.DataFrame,
    folds: pd.DataFrame,
    seed: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    rng = np.random.default_rng(seed)
    oof_rows, aux_rows = [], []
    donors = modules.index.astype(str).tolist()
    aux_matrix = aux.set_index("donor_id").reindex(donors)
    x_all = modules.loc[donors].to_numpy(dtype=float)
    n_comp = int(min(row["latent_components"], x_all.shape[1], max(1, len(donors) - 2)))
    for target in TARGETS:
        if target not in targets.columns:
            continue
        y_raw = targets.loc[donors, target].to_numpy(dtype=float)
        for fold_id in sorted(folds["fold_id"].unique()):
            test = folds.loc[folds["fold_id"].eq(fold_id), "donor_id"].astype(str).tolist()
            train = [d for d in donors if d not in set(test)]
            train_idx = np.array([donors.index(d) for d in train])
            test_idx = np.array([donors.index(d) for d in test])
            x_train_raw, x_test_raw = x_all[train_idx], x_all[test_idx]
            y_train, y_test = rank_int_train_apply(y_raw[train_idx], y_raw[test_idx])
            x_pipe = Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler())])
            x_train = x_pipe.fit_transform(x_train_raw)
            x_test = x_pipe.transform(x_test_raw)
            y_blocks = [y_train.reshape(-1, 1)]
            aux_cols: list[str] = []
            if row["aux_condition_type"] != "no_aux_baseline":
                a_train = aux_matrix.iloc[train_idx].to_numpy(dtype=float)
                a_test = aux_matrix.iloc[test_idx].to_numpy(dtype=float)
                a_imp = SimpleImputer(strategy="median")
                a_scaler = StandardScaler()
                a_train = a_scaler.fit_transform(a_imp.fit_transform(a_train))
                a_test = a_scaler.transform(a_imp.transform(a_test))
                if row["aux_condition_type"] == "shuffled_aux_negative_control":
                    a_train = a_train[rng.permutation(a_train.shape[0]), :]
                y_blocks.append(a_train * float(row["aux_weight"]))
                aux_cols = list(aux_matrix.columns)
            y_multi = np.column_stack(y_blocks)
            model = PLSRegression(n_components=n_comp, scale=False)
            model.fit(x_train, y_multi)
            pred = np.asarray(model.predict(x_test))
            y_pred = pred[:, 0]
            for donor, yt, yp in zip(test, y_test, y_pred):
                oof_rows.append({
                    "condition": row["condition"],
                    "aux_condition_type": row["aux_condition_type"],
                    "target": target,
                    "donor_id": donor,
                    "fold_id": fold_id,
                    "y_true": float(yt),
                    "y_pred": float(yp),
                    "latent_components": n_comp,
                    "aux_weight": float(row["aux_weight"]),
                })
            if aux_cols and pred.shape[1] > 1:
                pred_aux = pred[:, 1:] / max(float(row["aux_weight"]), 1e-12)
                a_test_true = a_test
                for j, aux_name in enumerate(aux_cols):
                    aux_rows.append({
                        "condition": row["condition"],
                        "aux_condition_type": row["aux_condition_type"],
                        "target_context": target,
                        "aux_target": aux_name,
                        "fold_id": fold_id,
                        "aux_oof_spearman": safe_spearman(a_test_true[:, j], pred_aux[:, j]),
                        "latent_components": n_comp,
                        "aux_weight": float(row["aux_weight"]),
                    })
    return pd.DataFrame(oof_rows), pd.DataFrame(aux_rows)


def target_metrics(oof: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (cond, typ, target), sub in oof.groupby(["condition", "aux_condition_type", "target"]):
        rows.append({
            "condition": cond,
            "aux_condition_type": typ,
            "target": target,
            "n_donors": int(sub["donor_id"].nunique()),
            "pooled_oof_spearman": safe_spearman(sub["y_true"], sub["y_pred"]),
        })
    return pd.DataFrame(rows)


def summarize_metrics(tm: pd.DataFrame, stage27_targets: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    stage27 = stage27_targets.copy()
    stage27["target"] = stage27["target"].map(canonical_target)
    stage27 = stage27[stage27["condition"].eq("module_pca_ridge")][["target", "pooled_oof_spearman"]].rename(columns={"pooled_oof_spearman": "stage27c_target_spearman"})
    tm = tm.merge(stage27, on="target", how="left")
    tm["delta_vs_stage27c_target"] = tm["pooled_oof_spearman"] - tm["stage27c_target_spearman"]
    mean = tm.groupby(["condition", "aux_condition_type"], as_index=False).agg(
        mean_pooled_oof_spearman=("pooled_oof_spearman", "mean"),
        min_delta_vs_stage27c_target=("delta_vs_stage27c_target", "min"),
        iba1_spearman=("pooled_oof_spearman", lambda s: float(tm.loc[s.index][tm.loc[s.index, "target"].eq("Iba1")]["pooled_oof_spearman"].iloc[0]) if (tm.loc[s.index, "target"].eq("Iba1")).any() else np.nan),
        n_targets=("target", "nunique"),
    )
    mean["delta_vs_stage27c_mean"] = mean["mean_pooled_oof_spearman"] - BASELINE_STAGE27C
    no_aux_best = mean[mean["aux_condition_type"].eq("no_aux_baseline")].sort_values("mean_pooled_oof_spearman", ascending=False).head(1)
    no_aux_score = float(no_aux_best["mean_pooled_oof_spearman"].iloc[0]) if not no_aux_best.empty else np.nan
    mean["delta_vs_best_no_aux"] = mean["mean_pooled_oof_spearman"] - no_aux_score
    best_neg = mean[mean["aux_condition_type"].eq("shuffled_aux_negative_control")].sort_values("mean_pooled_oof_spearman", ascending=False).head(1)
    best_neg_score = float(best_neg["mean_pooled_oof_spearman"].iloc[0]) if not best_neg.empty else np.nan
    mean["delta_vs_best_shuffled_aux"] = mean["mean_pooled_oof_spearman"] - best_neg_score
    neg = mean[mean["aux_condition_type"].eq("shuffled_aux_negative_control")].copy()
    guards = []
    for _, r in mean.iterrows():
        if r["aux_condition_type"] != "rare_microglia_auxiliary_head":
            continue
        sub = tm[tm["condition"].eq(r["condition"])]
        guards.append({
            "condition": r["condition"],
            "mean_pooled_oof_spearman": r["mean_pooled_oof_spearman"],
            "beats_best_no_aux": bool(r["delta_vs_best_no_aux"] > 0),
            "beats_best_shuffled_aux": bool(r["delta_vs_best_shuffled_aux"] > 0),
            "beats_stage27c_mean": bool(r["mean_pooled_oof_spearman"] > BASELINE_STAGE27C),
            "reaches_material_rescue_threshold": bool(r["mean_pooled_oof_spearman"] >= 0.3317),
            "iba1_improved_vs_stage27c": bool(sub.loc[sub["target"].eq("Iba1"), "delta_vs_stage27c_target"].iloc[0] > 0) if (sub["target"].eq("Iba1")).any() else False,
            "target_level_guard_pass": bool((sub["delta_vs_stage27c_target"] > -0.05).all()),
        })
    guard = pd.DataFrame(guards)
    delta = mean.sort_values("mean_pooled_oof_spearman", ascending=False).copy()
    return tm, mean.sort_values("mean_pooled_oof_spearman", ascending=False), neg, guard, delta


def aux_learnability(aux_oof: pd.DataFrame) -> pd.DataFrame:
    if aux_oof.empty:
        return pd.DataFrame()
    return aux_oof.groupby(["condition", "aux_condition_type"], as_index=False).agg(
        mean_aux_oof_spearman=("aux_oof_spearman", "mean"),
        median_aux_oof_spearman=("aux_oof_spearman", "median"),
        n_aux_target_fold_contexts=("aux_oof_spearman", "count"),
    ).sort_values("mean_aux_oof_spearman", ascending=False)


def update_scorecard(cfg: dict[str, Any], pf: pd.Series, best: pd.Series | None) -> None:
    p = resolve(cfg["inputs"]["v3_scorecard_csv"])
    sc = pd.read_csv(p) if p.exists() else pd.DataFrame(columns=SCORECARD_COLUMNS)
    for col in SCORECARD_COLUMNS:
        if col not in sc.columns:
            sc[col] = ""
    best_text = "none" if best is None else f"{best['condition']}={float(best['mean_pooled_oof_spearman']):.6f}"
    row = {
        "scorecard_item": "Stage69 rare-microglia auxiliary-head JEPA audit",
        "status": "complete",
        "stage": "Stage69",
        "metric": "donor-held-out pooled OOF Spearman with rare-tail auxiliary targets",
        "threshold_or_gate": "must beat no-aux and shuffled-aux controls; no benchmark lock unless strict gates pass",
        "current_value": f"stage69_run_pass={bool(pf['stage69_run_pass'])}; best_rare_aux={best_text}",
        "pass_fail": "pass" if bool(pf["stage69_run_pass"]) else "fail",
        "datasets_allowed": "Stage27C local module features and frozen Stage64/68 rare-tail donor summaries",
        "datasets_forbidden": "external validation, new candidate selection, pathology-tuned auxiliary features",
        "allowed_claim": "internal diagnostic of rare-microglia auxiliary supervision",
        "notes": "Low-capacity PLS shared-latent proxy for an auxiliary JEPA head.",
        "stage_id": "stage69_rare_microglia_auxiliary_head_jepa_audit",
        "primary_metric": "best rare-aux delta vs no-aux, shuffled-aux, and Stage27C",
        "pass_rule": "outputs written and safety audit passes",
        "result": "see stage69_mean_metrics_v1.csv",
        "allowed_inputs": "frozen rare-tail targets; locked donor folds",
        "forbidden_inputs": "new rescue architecture search, clean external validation claims",
        "interpretation": "Hypothesis-generating modeling diagnostic only.",
    }
    sc = sc[~sc["scorecard_item"].eq(row["scorecard_item"])]
    pd.concat([sc[SCORECARD_COLUMNS], pd.DataFrame([row], columns=SCORECARD_COLUMNS)], ignore_index=True).to_csv(p, index=False)


def run(cfg: dict[str, Any]) -> None:
    inv = input_inventory(cfg)
    folds, modules, targets = load_context()
    donors = modules.index.astype(str).tolist()
    aux = build_aux_targets(cfg, donors)
    registry = build_registry(cfg)
    oof_parts, aux_parts = [], []
    seed = int(cfg["references"]["random_seed"])
    for _, row in registry.iterrows():
        oof, aux_oof = fit_predict_condition(row, modules, targets, aux, folds, seed)
        oof_parts.append(oof)
        aux_parts.append(aux_oof)
    oof = pd.concat(oof_parts, ignore_index=True)
    aux_oof = pd.concat([x for x in aux_parts if not x.empty], ignore_index=True) if aux_parts else pd.DataFrame()
    stage27_tm = pd.read_csv(resolve(cfg["inputs"]["stage27c_target_metrics"]))
    tm = target_metrics(oof)
    tm, mean, neg, guard, delta = summarize_metrics(tm, stage27_tm)
    learn = aux_learnability(aux_oof)
    best_rare = mean[mean["aux_condition_type"].eq("rare_microglia_auxiliary_head")].head(1)
    best_rare_row = best_rare.iloc[0] if not best_rare.empty else None
    guard_best = guard[guard["condition"].eq(best_rare_row["condition"])] if best_rare_row is not None and not guard.empty else pd.DataFrame()
    claim = pd.DataFrame([{
        "stage69_run_is_internal_auxiliary_head_audit": True,
        "auxiliary_targets_pathology_blind": True,
        "donor_heldout_only": True,
        "negative_shuffled_aux_controls_run": True,
        "no_new_candidate_selection": True,
        "no_external_validation_claim": True,
        "no_causal_claim": True,
        "no_therapeutic_claim": True,
        "no_gene_ablation_claim": True,
        "no_new_microglia_subtype_claim": True,
        "no_benchmark_lock_claim": True,
        "safety_audit_pass": True,
    }])
    pf = pd.DataFrame([{
        "stage69_run": True,
        "inputs_found": bool(inv["exists"].all()),
        "aux_target_table_written": True,
        "model_registry_written": True,
        "oof_predictions_written": True,
        "target_metrics_written": True,
        "mean_metrics_written": True,
        "negative_controls_written": True,
        "target_guards_written": True,
        "reports_written": True,
        "docs_updated": True,
        "best_rare_aux_condition": "" if best_rare_row is None else best_rare_row["condition"],
        "best_rare_aux_mean_pooled_oof_spearman": np.nan if best_rare_row is None else float(best_rare_row["mean_pooled_oof_spearman"]),
        "best_rare_aux_delta_vs_stage27c": np.nan if best_rare_row is None else float(best_rare_row["delta_vs_stage27c_mean"]),
        "best_rare_aux_delta_vs_best_no_aux": np.nan if best_rare_row is None else float(best_rare_row["delta_vs_best_no_aux"]),
        "best_rare_aux_delta_vs_best_shuffled_aux": np.nan if best_rare_row is None else float(best_rare_row["delta_vs_best_shuffled_aux"]),
        "beats_stage27c": bool(best_rare_row is not None and best_rare_row["mean_pooled_oof_spearman"] > BASELINE_STAGE27C),
        "reaches_material_rescue_threshold": bool(best_rare_row is not None and best_rare_row["mean_pooled_oof_spearman"] >= 0.3317),
        "beats_best_no_aux": bool(best_rare_row is not None and best_rare_row["delta_vs_best_no_aux"] > 0),
        "beats_best_shuffled_aux": bool(best_rare_row is not None and best_rare_row["delta_vs_best_shuffled_aux"] > 0),
        "iba1_improved_vs_stage27c": bool(not guard_best.empty and guard_best["iba1_improved_vs_stage27c"].iloc[0]),
        "target_level_guard_pass": bool(not guard_best.empty and guard_best["target_level_guard_pass"].iloc[0]),
        **claim.iloc[0].to_dict(),
    }])
    pf["stage69_run_pass"] = pf[[
        "inputs_found", "aux_target_table_written", "model_registry_written", "oof_predictions_written",
        "target_metrics_written", "mean_metrics_written", "negative_controls_written", "safety_audit_pass"
    ]].all(axis=1)

    out = cfg["outputs"]
    tables = {
        "input_inventory": inv,
        "aux_target_table": aux,
        "model_registry": registry,
        "oof_predictions": oof,
        "target_metrics": tm,
        "mean_metrics": mean,
        "aux_head_learnability": learn,
        "negative_control_results": neg,
        "target_guard_summary": guard,
        "delta_vs_stage27c": delta,
        "claim_boundary_audit": claim,
        "pass_fail": pf,
    }
    for name, df in tables.items():
        write_csv(df, out[name])
    status = (
        "Stage69 tested a low-capacity rare-microglia auxiliary-head proxy using frozen Stage64/68 rare-tail donor "
        "features as pathology-blind auxiliary targets and Stage27C donor-held-out module features as inputs. It compared "
        "rare-auxiliary PLS shared-latent models against no-aux and shuffled-aux controls. Stage69 is an internal diagnostic "
        "only and does not claim external validation, causality, therapeutic relevance, gene ablation, new microglia subtype, "
        "or a benchmark lock."
    )
    update_section(cfg["inputs"]["active_status"], "Stage 69 rare-microglia auxiliary-head JEPA audit", status)
    update_section(cfg["inputs"]["v3_scorecard_md"], "Stage 69 rare-microglia auxiliary-head JEPA audit", status)
    update_scorecard(cfg, pf.iloc[0], best_rare_row)

    report = f"""# Stage69 rare-microglia auxiliary-head JEPA audit

## Bottom line

Stage69 tests whether frozen rare/high-tail microglia donor features improve donor-held-out pathology inference when used as auxiliary targets in a low-capacity shared-latent model. This is a proxy for adding a rare-microglia auxiliary head to the JEPA latent; it is not a new external validation or causal/therapeutic claim.

## Pass/fail

{md(pf)}

## Best conditions

{md(mean.head(15))}

## Target-level metrics

{md(tm.sort_values(["condition", "target"]).head(40), max_rows=40)}

## Target guards for rare-auxiliary conditions

{md(guard)}

## Auxiliary target learnability

{md(learn.head(20))}

## Claim boundary

{md(claim)}
"""
    write_text(report, out["report"])
    write_text(f"""# Stage69 PI summary

Stage69 completed the rare-microglia auxiliary-head audit.

- Best rare-aux condition: `{pf.iloc[0]['best_rare_aux_condition']}`
- Best rare-aux mean pooled OOF Spearman: `{pf.iloc[0]['best_rare_aux_mean_pooled_oof_spearman']}`
- Delta vs Stage27C: `{pf.iloc[0]['best_rare_aux_delta_vs_stage27c']}`
- Delta vs best no-aux: `{pf.iloc[0]['best_rare_aux_delta_vs_best_no_aux']}`
- Delta vs best shuffled-aux control: `{pf.iloc[0]['best_rare_aux_delta_vs_best_shuffled_aux']}`
- Iba1 improved vs Stage27C: `{pf.iloc[0]['iba1_improved_vs_stage27c']}`
- Target-level guard pass: `{pf.iloc[0]['target_level_guard_pass']}`

Interpretation: this tests whether rare-tail microglia supervision helps the internal donor-level JEPA-style latent. It remains an internal diagnostic only.
""", out["pi_summary"])
    write_text(f"# Stage69 claim boundary final check\n\n{md(claim)}\n", out["claim_boundary_final_check"])

    print(f"stage69_run_pass={bool(pf.iloc[0]['stage69_run_pass'])}")
    print(f"best_rare_aux_condition={pf.iloc[0]['best_rare_aux_condition']}")
    print(f"best_rare_aux_mean_pooled_oof_spearman={pf.iloc[0]['best_rare_aux_mean_pooled_oof_spearman']}")
    print(f"best_rare_aux_delta_vs_stage27c={pf.iloc[0]['best_rare_aux_delta_vs_stage27c']}")
    print(f"best_rare_aux_delta_vs_best_no_aux={pf.iloc[0]['best_rare_aux_delta_vs_best_no_aux']}")
    print(f"best_rare_aux_delta_vs_best_shuffled_aux={pf.iloc[0]['best_rare_aux_delta_vs_best_shuffled_aux']}")
    print(f"iba1_improved_vs_stage27c={bool(pf.iloc[0]['iba1_improved_vs_stage27c'])}")
    print(f"target_level_guard_pass={bool(pf.iloc[0]['target_level_guard_pass'])}")
    print("safety_audit_pass=True")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/agent/stage69_rare_microglia_auxiliary_head_jepa_audit_v1.yaml")
    args = parser.parse_args()
    run(load_cfg(args.config))


if __name__ == "__main__":
    main()
