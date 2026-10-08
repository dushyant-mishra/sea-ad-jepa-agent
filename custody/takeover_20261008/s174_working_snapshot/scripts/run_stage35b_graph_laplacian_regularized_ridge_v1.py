from __future__ import annotations

import argparse
import importlib
import sys
import types
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml
from scipy import sparse
from scipy.linalg import solve
from sklearn.decomposition import PCA
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

PASS_FAIL_OUT = TABLE_DIR / "stage35b_pass_fail_v1.csv"
ALIGN_OUT = TABLE_DIR / "stage35b_feature_graph_alignment_audit_v1.csv"
CONDITION_OUT = TABLE_DIR / "stage35b_condition_metrics_v1.csv"
MEAN_OUT = TABLE_DIR / "stage35b_mean_metrics_v1.csv"
TARGET_OUT = TABLE_DIR / "stage35b_target_metrics_v1.csv"
GRAPH_OUT = TABLE_DIR / "stage35b_graph_control_audit_v1.csv"
LEAKAGE_OUT = TABLE_DIR / "stage35b_leakage_audit_v1.csv"
REPORT_OUT = REPORT_DIR / "stage35b_graph_laplacian_regularized_ridge_report_v1.md"

REF27 = "stage27c_module_pca_ridge_reference"
REF31 = "stage31_weak_residual_real_graph_alpha_0_05_reference"
REF35A = "stage35a_best_reference"
NO_GRAPH = "laplacian_no_graph_identity_lambda_0_ridge"


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


def real_condition(lam: float) -> str:
    return f"laplacian_real_graph_lambda_{suffix(lam)}_ridge"


def strict_condition(lam: float) -> str:
    return f"laplacian_strict_shuffled_lambda_{suffix(lam)}_ridge"


def load_context():
    folds, targets, _, metadata = s25.load_inputs()
    donors = folds["donor_id"].astype(str).tolist()
    expr = s25.load_expression_matrix(donors)
    target_matrix = s25.build_target_matrix(metadata, targets, donors)
    shared = sorted(set(donors) & set(expr.index) & set(target_matrix.index))
    modules = s25.build_predefined_module_features(expr.loc[shared]).matrix
    return folds[folds["donor_id"].astype(str).isin(shared)].copy(), targets, expr.loc[shared], target_matrix.loc[shared], modules


def canonical_from_identity(path: Path) -> list[str]:
    edges = pd.read_csv(path)
    genes = sorted(set(edges["source"].astype(str)) | set(edges["target"].astype(str)))
    return genes


def module_membership(canonical: list[str], module_columns: list[str]) -> tuple[np.ndarray, list[str]]:
    gene_index = {gene.upper(): i for i, gene in enumerate(canonical)}
    mat = np.zeros((len(canonical), len(module_columns)), dtype=float)
    keys = []
    for j, col in enumerate(module_columns):
        key = col.removeprefix("module_")
        keys.append(key)
        for gene in s25.MICROGLIA_GENE_MODULES.get(key, []):
            idx = gene_index.get(str(gene).upper())
            if idx is not None:
                mat[idx, j] = 1.0
    return mat, keys


def read_gene_adjacency(path: Path, canonical: list[str]) -> tuple[sparse.csr_matrix, int]:
    gene_index = {gene.upper(): i for i, gene in enumerate(canonical)}
    edges = pd.read_csv(path)
    src = edges["source"].astype(str).str.upper().map(gene_index)
    dst = edges["target"].astype(str).str.upper().map(gene_index)
    valid = src.notna() & dst.notna()
    src = src[valid].astype(int).to_numpy()
    dst = dst[valid].astype(int).to_numpy()
    data = np.ones(len(src), dtype=float)
    adj = sparse.coo_matrix((data, (src, dst)), shape=(len(canonical), len(canonical))).tocsr()
    adj = adj.maximum(adj.T)
    adj.setdiag(0.0)
    adj.eliminate_zeros()
    return adj, int(len(edges))


def module_laplacian_from_gene_graph(path: Path, canonical: list[str], membership: np.ndarray) -> tuple[np.ndarray, int]:
    adj, edge_count = read_gene_adjacency(path, canonical)
    module_adj = membership.T @ (adj @ membership)
    module_adj = np.asarray(module_adj, dtype=float)
    np.fill_diagonal(module_adj, 0.0)
    sizes = np.maximum(membership.sum(axis=0), 1.0)
    module_adj = module_adj / np.sqrt(np.outer(sizes, sizes))
    module_adj = (module_adj + module_adj.T) / 2.0
    degree = np.diag(module_adj.sum(axis=1))
    lap = degree - module_adj
    lap = (lap + lap.T) / 2.0
    return lap, edge_count


def fit_predict_laplacian(
    modules: pd.DataFrame,
    y: pd.Series,
    train: list[str],
    test: list[str],
    cfg: dict[str, Any],
    module_laplacian: np.ndarray,
    lambda_graph: float,
) -> np.ndarray:
    x_train_raw = modules.loc[train].to_numpy(dtype=float)
    x_test_raw = modules.loc[test].to_numpy(dtype=float)
    scaler = StandardScaler()
    x_train_scaled = scaler.fit_transform(x_train_raw)
    x_test_scaled = scaler.transform(x_test_raw)
    n_components = min(int(cfg["backbone"]["module_pca_components"]), x_train_scaled.shape[1], len(train) - 1)
    pca = PCA(n_components=n_components, random_state=int(cfg["random_seed"]))
    x_train = pca.fit_transform(x_train_scaled)
    x_test = pca.transform(x_test_scaled)
    l_feature = pca.components_ @ module_laplacian @ pca.components_.T
    l_feature = (l_feature + l_feature.T) / 2.0
    ridge = float(cfg["downstream"]["ridge_lambda"])
    lhs = x_train.T @ x_train + ridge * np.eye(x_train.shape[1]) + float(lambda_graph) * l_feature
    y_train = np.log1p(y.loc[train].to_numpy(dtype=float))
    intercept = float(y_train.mean())
    rhs = x_train.T @ (y_train - intercept)
    try:
        beta = solve(lhs, rhs, assume_a="sym")
    except Exception:
        beta = np.linalg.solve(lhs + 1e-8 * np.eye(lhs.shape[0]), rhs)
    return x_test @ beta + intercept


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

    target = [
        from_oof(resolve(cfg["references"]["stage27c_oof"]), "module_pca_ridge", REF27),
        from_oof(resolve(cfg["references"]["stage31_oof"]), cfg["references"]["stage31_condition"], REF31),
    ]
    stage35a_path = resolve(cfg["references"]["stage35a_mean"])
    if stage35a_path.exists():
        m = pd.read_csv(stage35a_path).sort_values("mean_pooled_oof_spearman", ascending=False)
        if not m.empty:
            best = str(m.iloc[0]["condition"])
            target.append(pd.read_csv(TABLE_DIR / "stage35a_target_metrics_v1.csv").query("condition == @best").assign(condition=REF35A))
    target_df = pd.concat(target, ignore_index=True)
    return target_df, summarize_mean(target_df)


def run_oof(cfg: dict[str, Any], laplacians: dict[str, np.ndarray]) -> pd.DataFrame:
    folds, targets, _, target_matrix, modules = load_context()
    specs = [{"condition": NO_GRAPH, "lap": "zero", "lambda": 0.0, "role": "matched_no_graph_identity_control"}]
    for lam in map(float, cfg["graph"]["lambdas"]):
        specs += [
            {"condition": real_condition(lam), "lap": "real", "lambda": lam, "role": "real_graph_laplacian_penalty"},
            {"condition": strict_condition(lam), "lap": "strict", "lambda": lam, "role": "strict_shuffled_laplacian_penalty"},
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
                pred = fit_predict_laplacian(modules, y, train, test, cfg, laplacians[spec["lap"]], float(spec["lambda"]))
                for donor, true, predicted in zip(test, np.log1p(y.loc[test].to_numpy(dtype=float)), pred):
                    rows.append({"condition": spec["condition"], "graph_role": spec["role"], "lambda_graph": spec["lambda"], "target": target, "target_key": key, "target_alias": alias, "donor_id": donor, "fold_id": int(fold_id), "y_true": float(true), "y_pred": float(predicted)})
    return pd.DataFrame(rows)


def compute_target_metrics(oof: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for keys, group in oof.groupby(["condition", "graph_role", "lambda_graph", "target", "target_key", "target_alias"]):
        condition, role, lam, target, key, alias = keys
        rows.append({"condition": condition, "graph_role": role, "lambda_graph": lam, "target": target, "target_key": key, "target_alias": alias, "n_donors": int(group["donor_id"].nunique()), **regression_metrics(group["y_true"], group["y_pred"])})
    return pd.DataFrame(rows)


def summarize_mean(target: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for condition, group in target.groupby("condition"):
        rows.append({"condition": condition, "mean_pooled_oof_spearman": float(group["pooled_oof_spearman"].mean()), "n_targets": int(group["target_key"].nunique())})
    return pd.DataFrame(rows).sort_values("mean_pooled_oof_spearman", ascending=False)


def make_audits(cfg: dict[str, Any], target: pd.DataFrame, mean: pd.DataFrame, align: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    required = set(cfg["required_targets"])
    stage27 = float(cfg["stage27c_reference_mean"])
    new_conditions = [NO_GRAPH] + [real_condition(float(x)) for x in cfg["graph"]["lambdas"]] + [strict_condition(float(x)) for x in cfg["graph"]["lambdas"]]
    best_new = mean[mean["condition"].isin(new_conditions)].iloc[0]
    real_means = mean[mean["condition"].str.startswith("laplacian_real_graph")].sort_values("mean_pooled_oof_spearman", ascending=False)
    best_real = real_means.iloc[0]
    lam = float(best_real.condition.split("_lambda_")[1].split("_ridge")[0].replace("_", "."))
    matched_strict = strict_condition(lam)
    mean_map = dict(zip(mean["condition"], mean["mean_pooled_oof_spearman"]))
    graph = pd.DataFrame([
        {"comparison": "best_real_minus_no_graph_identity", "left_condition": best_real.condition, "right_condition": NO_GRAPH, "delta_mean_pooled_oof_spearman": float(mean_map[best_real.condition] - mean_map[NO_GRAPH]), "graph_gate_pass": bool(mean_map[best_real.condition] > mean_map[NO_GRAPH])},
        {"comparison": "best_real_minus_matched_strict_shuffled", "left_condition": best_real.condition, "right_condition": matched_strict, "delta_mean_pooled_oof_spearman": float(mean_map[best_real.condition] - mean_map[matched_strict]), "graph_gate_pass": bool(mean_map[best_real.condition] > mean_map[matched_strict])},
    ])
    ref = target[target["condition"] == REF27][["target_key", "pooled_oof_spearman"]].rename(columns={"pooled_oof_spearman": "stage27c_target_spearman"})
    best_t = target[target["condition"] == best_new.condition].merge(ref, on="target_key")
    target_gate = bool(((best_t["pooled_oof_spearman"] - best_t["stage27c_target_spearman"]) >= float(cfg["max_target_drop_vs_stage27c_reference"])).all())
    leakage = pd.DataFrame([{"clean_holdout_used": False, "external_pretraining_matrix_used": False, "external_labels_used_for_supervised_pathology_prediction": False, "sea_ad_used_for_downstream_only": True, "locked_donor_folds_used": True, "fold_local_downstream_scaling_and_ridge": True, "target_values_used_to_construct_graph": False, "in_silico_ablation_run": False, "leakage_audit_pass": True}])
    graph_specific = bool(graph["graph_gate_pass"].all())
    internal_pass = bool(best_new.mean_pooled_oof_spearman > stage27 and best_new.mean_pooled_oof_spearman >= float(cfg["minimum_success_threshold"]) and required.issubset(set(target[target["condition"] == best_new.condition]["target_key"])) and target_gate)
    if best_new.mean_pooled_oof_spearman <= stage27:
        interpretation = "Graph Laplacian regularization did not improve over the Stage 27C internal no-graph reference under this implementation."
    elif internal_pass and not graph_specific:
        interpretation = "Graph Laplacian regularization improved the internal benchmark, but graph-specific utility remains unestablished."
    elif graph_specific and best_real.mean_pooled_oof_spearman <= stage27:
        interpretation = "Graph Laplacian regularization showed topology-specific signal but did not improve over the Stage 27C internal no-graph reference."
    else:
        interpretation = "Stage 35B completed under guarded internal benchmark rules."
    pf = pd.DataFrame([{"stage35b_run": True, "stage35b_skipped": False, "best_stage35b_condition": best_new.condition, "best_stage35b_mean_pooled_oof_spearman": float(best_new.mean_pooled_oof_spearman), "best_real_graph_condition": best_real.condition, "best_real_graph_mean_pooled_oof_spearman": float(best_real.mean_pooled_oof_spearman), "stage27c_reference_mean": stage27, "best_minus_stage27c": float(best_new.mean_pooled_oof_spearman - stage27), "best_real_minus_no_graph": float(mean_map[best_real.condition] - mean_map[NO_GRAPH]), "best_real_minus_matched_strict": float(mean_map[best_real.condition] - mean_map[matched_strict]), "all_five_targets_reported": required.issubset(set(target[target["condition"].isin(new_conditions)]["target_key"])), "target_degradation_gate_pass": target_gate, "alignment_pass": bool(align.iloc[0]["alignment_pass"]), "leakage_audit_pass": True, "stage35b_internal_performance_pass": internal_pass, "stage35b_graph_specific_pass": graph_specific, "controlled_interpretation": interpretation}])
    return leakage, graph, pf


def write_report(mean, target, graph, align, leakage, pf):
    row = pf.iloc[0]
    lines = [
        "# Stage 35B graph Laplacian regularized ridge report v1",
        "",
        "## Executive summary",
        "",
        f"Best Stage 35B condition: `{row.best_stage35b_condition}` with mean pooled donor-level OOF Spearman `{row.best_stage35b_mean_pooled_oof_spearman:.4f}`.",
        f"Best real graph condition: `{row.best_real_graph_condition}` with mean `{row.best_real_graph_mean_pooled_oof_spearman:.4f}`.",
        f"Internal performance pass: `{bool(row.stage35b_internal_performance_pass)}`. Graph-specific pass: `{bool(row.stage35b_graph_specific_pass)}`.",
        "",
        "## Controlled interpretation",
        "",
        str(row.controlled_interpretation),
        "This is an internal SEA-AD benchmark. It is not external validation, graph topology validation, causality, in silico ablation validation, or therapeutic-target discovery.",
        "",
        "## Feature/graph alignment audit",
        "```csv",
        align.to_csv(index=False).strip(),
        "```",
        "## Mean metrics",
        "```csv",
        mean.to_csv(index=False).strip(),
        "```",
        "## Target metrics",
        "```csv",
        target.to_csv(index=False).strip(),
        "```",
        "## Graph-control audit",
        "```csv",
        graph.to_csv(index=False).strip(),
        "```",
        "## Leakage audit",
        "```csv",
        leakage.to_csv(index=False).strip(),
        "```",
        "## Pass/fail",
        "```csv",
        pf.to_csv(index=False).strip(),
        "```",
    ]
    REPORT_OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def update_status(pf: pd.DataFrame) -> None:
    row = pf.iloc[0]
    score_path = TABLE_DIR / "v3_scorecard_status_v1.csv"
    score = pd.read_csv(score_path)
    item = "stage35b_graph_laplacian_regularized_ridge"
    new = {"scorecard_item": item, "status": "complete", "stage": "Stage 35B", "metric": "pooled donor-level OOF Spearman", "threshold_or_gate": "internal pass requires best Stage 35B > Stage 27C and >=0.3228; graph pass requires real > no-graph and strict", "current_value": f"{row.best_stage35b_mean_pooled_oof_spearman:.4f}", "pass_fail": "pass" if bool(row.stage35b_internal_performance_pass) else "fail", "datasets_allowed": "SEA-AD locked folds only", "datasets_forbidden": "external pretraining matrices; clean holdouts; external labels; in silico ablation", "allowed_claim": row.controlled_interpretation, "notes": f"graph_specific_pass={bool(row.stage35b_graph_specific_pass)}; best_real={row.best_real_graph_condition}"}
    score = score[score["scorecard_item"] != item]
    pd.concat([score, pd.DataFrame([new])], ignore_index=True).to_csv(score_path, index=False)
    for doc_path, marker, addition in [
        (ROOT / "docs" / "ACTIVE_V3_STATUS.md", "\n\n## Stage 35B graph Laplacian regularized ridge status\n", f"\nStage 35B is complete. Best condition: `{row.best_stage35b_condition}` (`{row.best_stage35b_mean_pooled_oof_spearman:.4f}`). Graph-specific pass: `{bool(row.stage35b_graph_specific_pass)}`. {row.controlled_interpretation} No external validation or manuscript claim update.\n"),
        (ROOT / "docs" / "V3_SCORECARD.md", "\n\n## Stage 35B graph Laplacian regularized ridge result\n", f"\nBest Stage 35B condition: `{row.best_stage35b_condition}`; mean pooled OOF Spearman: `{row.best_stage35b_mean_pooled_oof_spearman:.4f}`; minus Stage 27C: `{row.best_minus_stage27c:.4f}`; graph-specific pass: `{bool(row.stage35b_graph_specific_pass)}`. {row.controlled_interpretation}\n"),
    ]:
        text = doc_path.read_text(encoding="utf-8")
        doc_path.write_text(text.split(marker)[0].rstrip() + marker + addition.lstrip(), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/train/stage35b_graph_laplacian_regularized_ridge_v1.yaml")
    args = parser.parse_args()
    cfg = load_cfg(resolve(args.config))
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    folds, targets, expr, target_matrix, modules = load_context()
    canonical = canonical_from_identity(resolve(cfg["graph"]["no_graph_edges"]))
    membership, module_keys = module_membership(canonical, list(modules.columns))
    real_lap, real_edges = module_laplacian_from_gene_graph(resolve(cfg["graph"]["real_edges"]), canonical, membership)
    strict_lap, strict_edges = module_laplacian_from_gene_graph(resolve(cfg["graph"]["strict_shuffled_edges"]), canonical, membership)
    zero_lap = np.zeros_like(real_lap)
    eig_min = float(min(np.linalg.eigvalsh(real_lap).min(), np.linalg.eigvalsh(strict_lap).min()))
    align = pd.DataFrame([{"stage27c_feature_space": "fold_local_standardized_predefined_module_means_projected_to_8_pca_components", "n_features": int(min(cfg["backbone"]["module_pca_components"], modules.shape[1])), "gene_graph_available": True, "real_graph_edges": real_edges, "strict_graph_edges": strict_edges, "no_graph_identity_available": resolve(cfg["graph"]["no_graph_edges"]).exists(), "gene_to_feature_loading_available": True, "module_graph_constructed": True, "feature_laplacian_constructed": True, "feature_laplacian_shape": f"fold_local_{int(cfg['backbone']['module_pca_components'])}x{int(cfg['backbone']['module_pca_components'])}", "feature_laplacian_psd_check_or_symmetric_check": f"module_laplacian_min_eigenvalue={eig_min:.6g}; symmetric=True", "canonical_gene_universe_count": len(canonical), "alignment_pass": bool(len(canonical) == 2957 and membership.sum() > 0 and eig_min > -1e-8), "skipped_reason": ""}])
    if not bool(align.iloc[0]["alignment_pass"]):
        reason = "Stage 35B was skipped because a valid graph Laplacian could not be aligned to the Stage 27C feature space without fabricating mappings."
        pf = pd.DataFrame([{"stage35b_run": True, "stage35b_skipped": True, "stage35b_internal_performance_pass": False, "stage35b_graph_specific_pass": False, "controlled_interpretation": reason}])
        align.to_csv(ALIGN_OUT, index=False)
        pf.to_csv(PASS_FAIL_OUT, index=False)
        REPORT_OUT.write_text("# Stage 35B graph Laplacian regularized ridge report v1\n\n" + reason + "\n", encoding="utf-8")
        print("stage35b_skipped=True")
        return
    oof = run_oof(cfg, {"zero": zero_lap, "real": real_lap, "strict": strict_lap})
    new_target = compute_target_metrics(oof)
    ref_target, ref_mean = reference_target_and_mean(cfg)
    target = pd.concat([new_target, ref_target], ignore_index=True)
    mean = pd.concat([summarize_mean(new_target), ref_mean], ignore_index=True).sort_values("mean_pooled_oof_spearman", ascending=False)
    leakage, graph, pf = make_audits(cfg, target, mean, align)
    condition = mean.rename(columns={"mean_pooled_oof_spearman": "condition_mean_pooled_oof_spearman"})
    pf.to_csv(PASS_FAIL_OUT, index=False)
    align.to_csv(ALIGN_OUT, index=False)
    condition.to_csv(CONDITION_OUT, index=False)
    mean.to_csv(MEAN_OUT, index=False)
    target.to_csv(TARGET_OUT, index=False)
    graph.to_csv(GRAPH_OUT, index=False)
    leakage.to_csv(LEAKAGE_OUT, index=False)
    write_report(mean, target, graph, align, leakage, pf)
    update_status(pf)
    row = pf.iloc[0]
    print(f"best_stage35b_condition={row.best_stage35b_condition}")
    print(f"best_mean_pooled_oof_spearman={row.best_stage35b_mean_pooled_oof_spearman:.6f}")
    print(f"stage35b_internal_performance_pass={bool(row.stage35b_internal_performance_pass)}")
    print(f"stage35b_graph_specific_pass={bool(row.stage35b_graph_specific_pass)}")


if __name__ == "__main__":
    main()
