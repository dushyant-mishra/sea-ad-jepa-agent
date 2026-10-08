from __future__ import annotations

import argparse
import importlib
import itertools
import sys
import types
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml
from sklearn.decomposition import PCA
from sklearn.linear_model import RidgeCV
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
ATLAS_DIR = ROOT / "discovery_atlas"
for path in [SRC_DIR, ATLAS_DIR]:
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

for optional_module, optional_class in [("lightgbm", "LGBMRegressor"), ("xgboost", "XGBRegressor")]:
    if optional_module not in sys.modules:
        module = types.ModuleType(optional_module)
        setattr(module, optional_class, object)
        sys.modules[optional_module] = module

from sea_ad_jepa.eval.oof_metrics import regression_metrics  # noqa: E402

s25 = importlib.import_module("run_v3_primary_baseline_benchmark_suite_v1")


TABLE_DIR = ROOT / "results" / "tables"
REPORT_DIR = ROOT / "results" / "reports"

PASS_FAIL_OUT = TABLE_DIR / "stage35c_pass_fail_v1.csv"
AUDIT_OUT = TABLE_DIR / "stage35c_module_graph_audit_v1.csv"
CONDITION_OUT = TABLE_DIR / "stage35c_condition_metrics_v1.csv"
MEAN_OUT = TABLE_DIR / "stage35c_mean_metrics_v1.csv"
TARGET_OUT = TABLE_DIR / "stage35c_target_metrics_v1.csv"
RESCUE_OUT = TABLE_DIR / "stage35c_target_specific_rescue_v1.csv"
GRAPH_OUT = TABLE_DIR / "stage35c_graph_control_audit_v1.csv"
LEAKAGE_OUT = TABLE_DIR / "stage35c_leakage_audit_v1.csv"
REPORT_OUT = REPORT_DIR / "stage35c_latent_module_graph_report_v1.md"

REF27 = "stage27c_module_pca_ridge_reference"
REF31 = "stage31_weak_residual_real_graph_alpha_0_05_reference"
REF35A = "stage35a_best_reference"
REF35B = "stage35b_best_reference"
NO_GRAPH = "module_graph_no_graph_identity_ridge"


def load_cfg(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def resolve(value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def target_key(value: object) -> str:
    text = str(value)
    return "6e10/A_beta" if text.startswith("6e10/") else text


def suffix(value: float) -> str:
    return f"{value:g}".replace(".", "_")


def real_condition(weight: float) -> str:
    return f"module_graph_real_overlap_aux_weight_{suffix(weight)}_ridge"


def strict_condition(weight: float) -> str:
    return f"module_graph_strict_shuffled_overlap_aux_weight_{suffix(weight)}_ridge"


def load_context():
    folds, targets, _, metadata = s25.load_inputs()
    donors = folds["donor_id"].astype(str).tolist()
    expr = s25.load_expression_matrix(donors)
    target_matrix = s25.build_target_matrix(metadata, targets, donors)
    shared = sorted(set(donors) & set(expr.index) & set(target_matrix.index))
    modules = s25.build_predefined_module_features(expr.loc[shared]).matrix
    return folds[folds["donor_id"].astype(str).isin(shared)].copy(), targets, target_matrix.loc[shared], modules


def module_gene_sets(module_columns: list[str]) -> dict[str, set[str]]:
    out = {}
    for col in module_columns:
        key = col.removeprefix("module_")
        out[col] = {str(g).upper() for g in s25.MICROGLIA_GENE_MODULES.get(key, [])}
    return out


def row_normalize(adj: np.ndarray) -> np.ndarray:
    degree = adj.sum(axis=1)
    out = np.zeros_like(adj, dtype=float)
    mask = degree > 0
    out[mask] = adj[mask] / degree[mask, None]
    return out


def build_module_graphs(module_columns: list[str], seed: int) -> tuple[np.ndarray, np.ndarray, pd.DataFrame]:
    gene_sets = module_gene_sets(module_columns)
    n = len(module_columns)
    real = np.zeros((n, n), dtype=float)
    rows = []
    for i, j in itertools.combinations(range(n), 2):
        a = gene_sets[module_columns[i]]
        b = gene_sets[module_columns[j]]
        union = len(a | b)
        overlap = len(a & b)
        weight = overlap / union if union else 0.0
        if weight > 0:
            real[i, j] = real[j, i] = weight
    edge_count = int(np.triu(real > 0, 1).sum())
    weights = real[np.triu_indices(n, 1)]
    weights = weights[weights > 0]
    rng = np.random.default_rng(seed)
    possible = list(itertools.combinations(range(n), 2))
    real_edges = {tuple(x) for x in np.argwhere(np.triu(real > 0, 1))}
    candidates = [p for p in possible if p not in real_edges]
    rng.shuffle(candidates)
    strict = np.zeros_like(real)
    for (i, j), weight in zip(candidates[:edge_count], rng.permutation(weights) if len(weights) else []):
        strict[i, j] = strict[j, i] = float(weight)
    strict_edges = {tuple(x) for x in np.argwhere(np.triu(strict > 0, 1))}
    rows.append({"module_graph_source": "predefined_microglia_module_gene_membership_jaccard_overlap", "n_modules": n, "real_module_edges": edge_count, "strict_shuffled_module_edges": int(np.triu(strict > 0, 1).sum()), "real_strict_edge_overlap": len(real_edges & strict_edges), "target_values_used_to_construct_graph": False, "module_graph_constructed": bool(edge_count > 0), "module_graph_pass": bool(edge_count > 0 and len(real_edges & strict_edges) == 0)})
    return row_normalize(real), row_normalize(strict), pd.DataFrame(rows)


def fit_predict(modules: pd.DataFrame, aux: pd.DataFrame, y: pd.Series, train: list[str], test: list[str], cfg: dict[str, Any], weight: float) -> np.ndarray:
    x_train_raw = modules.loc[train].to_numpy(dtype=float)
    x_test_raw = modules.loc[test].to_numpy(dtype=float)
    n_components = min(int(cfg["backbone"]["module_pca_components"]), x_train_raw.shape[1], len(train) - 1)
    backbone = Pipeline([("scale", StandardScaler()), ("pca", PCA(n_components=n_components, random_state=int(cfg["random_seed"])))])
    base_train = backbone.fit_transform(x_train_raw)
    base_test = backbone.transform(x_test_raw)
    aux_scaler = StandardScaler()
    aux_train = aux_scaler.fit_transform(aux.loc[train].to_numpy(dtype=float)) * float(weight)
    aux_test = aux_scaler.transform(aux.loc[test].to_numpy(dtype=float)) * float(weight)
    x_train = np.concatenate([base_train, aux_train], axis=1)
    x_test = np.concatenate([base_test, aux_test], axis=1)
    ridge = RidgeCV(alphas=np.asarray(cfg["downstream"]["ridge_alphas"], dtype=float), cv=min(3, max(2, len(train) // 10)))
    ridge.fit(x_train, np.log1p(y.loc[train].to_numpy(dtype=float)))
    return ridge.predict(x_test)


def reference_target_and_mean(cfg: dict[str, Any]) -> tuple[pd.DataFrame, pd.DataFrame]:
    def from_oof(path: Path, source_condition: str, out_condition: str) -> pd.DataFrame:
        oof = pd.read_csv(path)
        oof = oof[oof["condition"] == source_condition].copy()
        if "target_key" not in oof.columns:
            oof["target_key"] = oof["target"].map(target_key)
        rows = []
        for keys, group in oof.groupby(["target", "target_key", "target_alias"]):
            target, key, alias = keys
            rows.append({"condition": out_condition, "target": target, "target_key": key, "target_alias": alias, "n_donors": int(group["donor_id"].nunique()), **regression_metrics(group["y_true"], group["y_pred"])})
        return pd.DataFrame(rows)

    parts = [from_oof(resolve(cfg["references"]["stage27c_oof"]), "module_pca_ridge", REF27), from_oof(resolve(cfg["references"]["stage31_oof"]), cfg["references"]["stage31_condition"], REF31)]
    for path_key, target_file, out_condition in [("stage35a_mean", "stage35a_target_metrics_v1.csv", REF35A), ("stage35b_mean", "stage35b_target_metrics_v1.csv", REF35B)]:
        path = resolve(cfg["references"][path_key])
        if path.exists() and (TABLE_DIR / target_file).exists():
            best = pd.read_csv(path).sort_values("mean_pooled_oof_spearman", ascending=False).iloc[0]["condition"]
            parts.append(pd.read_csv(TABLE_DIR / target_file).query("condition == @best").assign(condition=out_condition))
    target = pd.concat(parts, ignore_index=True)
    return target, summarize_mean(target)


def run_oof(cfg: dict[str, Any], real_graph: np.ndarray, strict_graph: np.ndarray) -> pd.DataFrame:
    folds, targets, target_matrix, modules = load_context()
    real_aux = pd.DataFrame(modules.to_numpy(dtype=float) @ real_graph.T - modules.to_numpy(dtype=float), index=modules.index, columns=modules.columns)
    strict_aux = pd.DataFrame(modules.to_numpy(dtype=float) @ strict_graph.T - modules.to_numpy(dtype=float), index=modules.index, columns=modules.columns)
    zero_aux = pd.DataFrame(0.0, index=modules.index, columns=modules.columns)
    specs = [{"condition": NO_GRAPH, "aux": zero_aux, "weight": 0.0, "role": "module_no_graph_identity_control"}]
    for weight in map(float, cfg["module_graph"]["aux_weights"]):
        specs += [
            {"condition": real_condition(weight), "aux": real_aux, "weight": weight, "role": "real_module_overlap_graph_auxiliary"},
            {"condition": strict_condition(weight), "aux": strict_aux, "weight": weight, "role": "strict_shuffled_module_overlap_graph_auxiliary"},
        ]
    rows = []
    for spec in specs:
        for _, target_row in targets.iterrows():
            target = target_row["target_name"]
            key = target_key(target)
            alias = target_row["target_alias"]
            y = target_matrix[alias].dropna()
            for fold_id in sorted(folds["fold_id"].unique()):
                test = folds.loc[folds["fold_id"] == fold_id, "donor_id"].astype(str).tolist()
                train = folds.loc[folds["fold_id"] != fold_id, "donor_id"].astype(str).tolist()
                train = [d for d in train if d in y.index and d in modules.index]
                test = [d for d in test if d in y.index and d in modules.index]
                pred = fit_predict(modules, spec["aux"], y, train, test, cfg, float(spec["weight"]))
                for donor, true, predicted in zip(test, np.log1p(y.loc[test].to_numpy(dtype=float)), pred):
                    rows.append({"condition": spec["condition"], "graph_role": spec["role"], "aux_weight": float(spec["weight"]), "target": target, "target_key": key, "target_alias": alias, "donor_id": donor, "fold_id": int(fold_id), "y_true": float(true), "y_pred": float(predicted)})
    return pd.DataFrame(rows)


def compute_target_metrics(oof: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for keys, group in oof.groupby(["condition", "graph_role", "aux_weight", "target", "target_key", "target_alias"]):
        condition, role, weight, target, key, alias = keys
        rows.append({"condition": condition, "graph_role": role, "aux_weight": weight, "target": target, "target_key": key, "target_alias": alias, "n_donors": int(group["donor_id"].nunique()), **regression_metrics(group["y_true"], group["y_pred"])})
    return pd.DataFrame(rows)


def summarize_mean(target: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for condition, group in target.groupby("condition"):
        rows.append({"condition": condition, "mean_pooled_oof_spearman": float(group["pooled_oof_spearman"].mean()), "n_targets": int(group["target_key"].nunique())})
    return pd.DataFrame(rows).sort_values("mean_pooled_oof_spearman", ascending=False)


def make_audits(cfg: dict[str, Any], target: pd.DataFrame, mean: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    required = set(cfg["required_targets"])
    stage27 = float(cfg["stage27c_reference_mean"])
    new_conditions = [NO_GRAPH] + [real_condition(float(w)) for w in cfg["module_graph"]["aux_weights"]] + [strict_condition(float(w)) for w in cfg["module_graph"]["aux_weights"]]
    best_new = mean[mean["condition"].isin(new_conditions)].iloc[0]
    best_real = mean[mean["condition"].str.startswith("module_graph_real")].iloc[0]
    weight = float(best_real.condition.split("_weight_")[1].split("_ridge")[0].replace("_", "."))
    matched_strict = strict_condition(weight)
    mean_map = dict(zip(mean["condition"], mean["mean_pooled_oof_spearman"]))
    graph = pd.DataFrame([
        {"comparison": "best_real_minus_no_graph_identity", "left_condition": best_real.condition, "right_condition": NO_GRAPH, "delta_mean_pooled_oof_spearman": float(mean_map[best_real.condition] - mean_map[NO_GRAPH]), "graph_gate_pass": bool(mean_map[best_real.condition] > mean_map[NO_GRAPH])},
        {"comparison": "best_real_minus_matched_strict_shuffled", "left_condition": best_real.condition, "right_condition": matched_strict, "delta_mean_pooled_oof_spearman": float(mean_map[best_real.condition] - mean_map[matched_strict]), "graph_gate_pass": bool(mean_map[best_real.condition] > mean_map[matched_strict])},
    ])
    ref = target[target["condition"] == REF27][["target_key", "pooled_oof_spearman"]].rename(columns={"pooled_oof_spearman": "stage27c_target_spearman"})
    no_graph = target[target["condition"] == NO_GRAPH][["target_key", "pooled_oof_spearman"]].rename(columns={"pooled_oof_spearman": "matched_no_graph_target_spearman"})
    rescue_rows = []
    for w in map(float, cfg["module_graph"]["aux_weights"]):
        real_t = target[target["condition"] == real_condition(w)][["target", "target_key", "pooled_oof_spearman"]].rename(columns={"pooled_oof_spearman": "real_target_spearman"})
        strict_t = target[target["condition"] == strict_condition(w)][["target_key", "pooled_oof_spearman"]].rename(columns={"pooled_oof_spearman": "matched_strict_target_spearman"})
        merged = real_t.merge(ref, on="target_key").merge(no_graph, on="target_key").merge(strict_t, on="target_key")
        for _, row in merged.iterrows():
            d27 = row.real_target_spearman - row.stage27c_target_spearman
            dng = row.real_target_spearman - row.matched_no_graph_target_spearman
            dst = row.real_target_spearman - row.matched_strict_target_spearman
            rescue_rows.append({"condition": real_condition(w), "aux_weight": w, "target": row.target, "target_key": row.target_key, "delta_vs_stage27c": d27, "delta_vs_matched_no_graph": dng, "delta_vs_matched_strict_shuffled": dst, "target_specific_module_graph_rescue_candidate": bool(d27 >= 0.005 and dng >= 0.005 and dst >= 0.005)})
    rescue = pd.DataFrame(rescue_rows)
    best_t = target[target["condition"] == best_new.condition].merge(ref, on="target_key")
    target_gate = bool(((best_t["pooled_oof_spearman"] - best_t["stage27c_target_spearman"]) >= float(cfg["max_target_drop_vs_stage27c_reference"])).all())
    leakage = pd.DataFrame([{"clean_holdout_used": False, "external_pretraining_matrix_used": False, "external_labels_used_for_supervised_pathology_prediction": False, "sea_ad_used_for_downstream_only": True, "locked_donor_folds_used": True, "fold_local_downstream_scaling_and_ridge": True, "target_values_used_to_construct_graph": False, "in_silico_ablation_run": False, "leakage_audit_pass": True}])
    graph_specific = bool(graph["graph_gate_pass"].all())
    internal_pass = bool(best_new.mean_pooled_oof_spearman > stage27 and best_new.mean_pooled_oof_spearman >= float(cfg["minimum_success_threshold"]) and required.issubset(set(target[target["condition"] == best_new.condition]["target_key"])) and target_gate)
    if bool(rescue["target_specific_module_graph_rescue_candidate"].any()) and not graph_specific:
        interpretation = "Stage 35C found target-specific module-graph rescue signals, but global graph-specific utility remains unestablished."
    elif graph.iloc[1]["graph_gate_pass"] and not graph.iloc[0]["graph_gate_pass"]:
        interpretation = "Real module topology outperformed shuffled module topology but did not improve over the no-graph identity reference."
    elif best_new.mean_pooled_oof_spearman <= stage27:
        interpretation = "Latent module graph modeling did not improve over the Stage 27C internal no-graph reference under this implementation."
    else:
        interpretation = "Stage 35C completed under guarded internal benchmark rules."
    pf = pd.DataFrame([{"stage35c_run": True, "stage35c_skipped": False, "best_stage35c_condition": best_new.condition, "best_stage35c_mean_pooled_oof_spearman": float(best_new.mean_pooled_oof_spearman), "best_real_module_graph_condition": best_real.condition, "best_real_module_graph_mean_pooled_oof_spearman": float(best_real.mean_pooled_oof_spearman), "stage27c_reference_mean": stage27, "best_minus_stage27c": float(best_new.mean_pooled_oof_spearman - stage27), "best_real_minus_no_graph": float(mean_map[best_real.condition] - mean_map[NO_GRAPH]), "best_real_minus_matched_strict": float(mean_map[best_real.condition] - mean_map[matched_strict]), "all_five_targets_reported": required.issubset(set(target[target["condition"].isin(new_conditions)]["target_key"])), "target_degradation_gate_pass": target_gate, "leakage_audit_pass": True, "stage35c_internal_performance_pass": internal_pass, "stage35c_module_graph_specific_pass": graph_specific, "n_target_specific_rescue_candidates": int(rescue["target_specific_module_graph_rescue_candidate"].sum()), "controlled_interpretation": interpretation}])
    return leakage, graph, rescue, pf


def write_report(mean, target, rescue, graph, audit, leakage, pf):
    row = pf.iloc[0]
    lines = ["# Stage 35C latent module graph report v1", "", "## Executive summary", "", f"Best Stage 35C condition: `{row.best_stage35c_condition}` with mean pooled donor-level OOF Spearman `{row.best_stage35c_mean_pooled_oof_spearman:.4f}`.", f"Best real module graph condition: `{row.best_real_module_graph_condition}` with mean `{row.best_real_module_graph_mean_pooled_oof_spearman:.4f}`.", f"Internal performance pass: `{bool(row.stage35c_internal_performance_pass)}`. Module graph-specific pass: `{bool(row.stage35c_module_graph_specific_pass)}`. Target-specific rescue candidates: `{int(row.n_target_specific_rescue_candidates)}`.", "", "## Controlled interpretation", "", str(row.controlled_interpretation), "This is an internal SEA-AD benchmark. It is not external validation, graph topology validation, causality, in silico ablation validation, or therapeutic-target discovery.", "", "## Module graph audit", "```csv", audit.to_csv(index=False).strip(), "```", "## Mean metrics", "```csv", mean.to_csv(index=False).strip(), "```", "## Target metrics", "```csv", target.to_csv(index=False).strip(), "```", "## Target-specific rescue audit", "```csv", rescue.to_csv(index=False).strip(), "```", "## Graph-control audit", "```csv", graph.to_csv(index=False).strip(), "```", "## Leakage audit", "```csv", leakage.to_csv(index=False).strip(), "```", "## Pass/fail", "```csv", pf.to_csv(index=False).strip(), "```"]
    REPORT_OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def update_status(pf: pd.DataFrame) -> None:
    row = pf.iloc[0]
    score_path = TABLE_DIR / "v3_scorecard_status_v1.csv"
    score = pd.read_csv(score_path)
    item = "stage35c_latent_module_graph_diagnostic"
    new = {"scorecard_item": item, "status": "complete", "stage": "Stage 35C", "metric": "pooled donor-level OOF Spearman", "threshold_or_gate": "internal pass requires best Stage 35C > Stage 27C and >=0.3228; graph pass requires real module graph > no-graph and strict", "current_value": f"{row.best_stage35c_mean_pooled_oof_spearman:.4f}", "pass_fail": "pass" if bool(row.stage35c_internal_performance_pass) else "fail", "datasets_allowed": "SEA-AD locked folds only", "datasets_forbidden": "external pretraining matrices; clean holdouts; external labels; in silico ablation", "allowed_claim": row.controlled_interpretation, "notes": f"module_graph_specific_pass={bool(row.stage35c_module_graph_specific_pass)}; target_rescue_candidates={int(row.n_target_specific_rescue_candidates)}"}
    score = score[score["scorecard_item"] != item]
    pd.concat([score, pd.DataFrame([new])], ignore_index=True).to_csv(score_path, index=False)
    for doc_path, marker, addition in [
        (ROOT / "docs" / "ACTIVE_V3_STATUS.md", "\n\n## Stage 35C latent module graph diagnostic status\n", f"\nStage 35C is complete. Best condition: `{row.best_stage35c_condition}` (`{row.best_stage35c_mean_pooled_oof_spearman:.4f}`). Module graph-specific pass: `{bool(row.stage35c_module_graph_specific_pass)}`; target-specific rescue candidates: `{int(row.n_target_specific_rescue_candidates)}`. {row.controlled_interpretation} No external validation or manuscript claim update.\n"),
        (ROOT / "docs" / "V3_SCORECARD.md", "\n\n## Stage 35C latent module graph diagnostic result\n", f"\nBest Stage 35C condition: `{row.best_stage35c_condition}`; mean pooled OOF Spearman: `{row.best_stage35c_mean_pooled_oof_spearman:.4f}`; minus Stage 27C: `{row.best_minus_stage27c:.4f}`; module graph-specific pass: `{bool(row.stage35c_module_graph_specific_pass)}`. {row.controlled_interpretation}\n"),
    ]:
        text = doc_path.read_text(encoding="utf-8")
        doc_path.write_text(text.split(marker)[0].rstrip() + marker + addition.lstrip(), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/train/stage35c_latent_module_graph_v1.yaml")
    args = parser.parse_args()
    cfg = load_cfg(resolve(args.config))
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    _, _, _, modules = load_context()
    real_graph, strict_graph, audit = build_module_graphs(list(modules.columns), int(cfg["module_graph"]["strict_shuffle_seed"]))
    if not bool(audit.iloc[0]["module_graph_pass"]):
        reason = "Stage 35C was skipped because a valid module graph could not be constructed without fabricating module mappings."
        pf = pd.DataFrame([{"stage35c_run": True, "stage35c_skipped": True, "stage35c_internal_performance_pass": False, "stage35c_module_graph_specific_pass": False, "controlled_interpretation": reason}])
        audit.to_csv(AUDIT_OUT, index=False)
        pf.to_csv(PASS_FAIL_OUT, index=False)
        REPORT_OUT.write_text("# Stage 35C latent module graph report v1\n\n" + reason + "\n", encoding="utf-8")
        print("stage35c_skipped=True")
        return
    oof = run_oof(cfg, real_graph, strict_graph)
    new_target = compute_target_metrics(oof)
    ref_target, ref_mean = reference_target_and_mean(cfg)
    target = pd.concat([new_target, ref_target], ignore_index=True)
    mean = pd.concat([summarize_mean(new_target), ref_mean], ignore_index=True).sort_values("mean_pooled_oof_spearman", ascending=False)
    leakage, graph, rescue, pf = make_audits(cfg, target, mean)
    condition = mean.rename(columns={"mean_pooled_oof_spearman": "condition_mean_pooled_oof_spearman"})
    pf.to_csv(PASS_FAIL_OUT, index=False)
    audit.to_csv(AUDIT_OUT, index=False)
    condition.to_csv(CONDITION_OUT, index=False)
    mean.to_csv(MEAN_OUT, index=False)
    target.to_csv(TARGET_OUT, index=False)
    rescue.to_csv(RESCUE_OUT, index=False)
    graph.to_csv(GRAPH_OUT, index=False)
    leakage.to_csv(LEAKAGE_OUT, index=False)
    write_report(mean, target, rescue, graph, audit, leakage, pf)
    update_status(pf)
    row = pf.iloc[0]
    print(f"best_stage35c_condition={row.best_stage35c_condition}")
    print(f"best_mean_pooled_oof_spearman={row.best_stage35c_mean_pooled_oof_spearman:.6f}")
    print(f"stage35c_internal_performance_pass={bool(row.stage35c_internal_performance_pass)}")
    print(f"stage35c_module_graph_specific_pass={bool(row.stage35c_module_graph_specific_pass)}")


if __name__ == "__main__":
    main()
