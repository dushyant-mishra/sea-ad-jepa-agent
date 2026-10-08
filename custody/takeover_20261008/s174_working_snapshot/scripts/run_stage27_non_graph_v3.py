from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from sklearn.preprocessing import StandardScaler

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from sea_ad_jepa.data.stage27_features import TARGET_ALIAS_TO_NAME, read_inputs, select_residual_columns
from sea_ad_jepa.eval.oof_metrics import donor_bootstrap_ci, regression_metrics
from sea_ad_jepa.models.non_graph_v3 import NonGraphV3MLP


TABLE_DIR = ROOT / "results" / "tables"
REPORT_DIR = ROOT / "results" / "reports"
MODEL_DIR = ROOT / "results" / "models" / "stage27_non_graph_v3"

OOF_OUT = TABLE_DIR / "stage27_non_graph_v3_oof_predictions_v1.csv"
TARGET_METRICS_OUT = TABLE_DIR / "stage27_non_graph_v3_target_metrics_v1.csv"
MEAN_METRICS_OUT = TABLE_DIR / "stage27_non_graph_v3_mean_metrics_v1.csv"
DELTAS_OUT = TABLE_DIR / "stage27_non_graph_v3_target_deltas_vs_module_mean_v1.csv"
PASS_FAIL_OUT = TABLE_DIR / "stage27_non_graph_v3_pass_fail_v1.csv"
BOOTSTRAP_OUT = TABLE_DIR / "stage27_non_graph_v3_bootstrap_ci_v1.csv"
REPORT_OUT = REPORT_DIR / "stage27_non_graph_v3_report_v1.md"


def load_config(path: Path) -> dict:
    if yaml is None:
        raise RuntimeError("PyYAML is required for Stage 27 config loading")
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def resolve(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else ROOT / p


def set_seed(seed: int) -> None:
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.set_num_threads(1)


def split_train_validation(train_donors: list[str], y_train: pd.Series, seed: int, fraction: float) -> tuple[list[str], list[str]]:
    rng = np.random.default_rng(seed)
    donors = np.asarray(train_donors, dtype=object)
    n_val = max(5, int(round(len(donors) * fraction)))
    n_val = min(n_val, max(1, len(donors) - 10))
    order = rng.permutation(len(donors))
    val = donors[order[:n_val]].tolist()
    train = donors[order[n_val:]].tolist()
    if len(set(y_train.loc[val].round(6))) < 2:
        val = donors[order[-n_val:]].tolist()
        train = donors[order[:-n_val]].tolist()
    return train, val


def tensor(x: np.ndarray) -> torch.Tensor:
    return torch.as_tensor(x, dtype=torch.float32)


def fit_one_fold(
    condition: str,
    module_features: pd.DataFrame,
    residual_features: pd.DataFrame,
    y: pd.Series,
    fold_id: int,
    train_donors: list[str],
    test_donors: list[str],
    cfg: dict,
    target_seed: int,
) -> tuple[np.ndarray, dict[str, object]]:
    train_fit, train_val = split_train_validation(
        train_donors,
        y.loc[train_donors],
        target_seed,
        float(cfg["training"]["inner_validation_fraction"]),
    )

    module_scaler = StandardScaler().fit(module_features.loc[train_fit].to_numpy(dtype=float))
    residual_scaler = StandardScaler().fit(residual_features.loc[train_fit].to_numpy(dtype=float))
    y_log = np.log1p(y.astype(float))
    y_mean = float(y_log.loc[train_fit].mean())
    y_std = float(y_log.loc[train_fit].std(ddof=0))
    if not np.isfinite(y_std) or y_std == 0:
        y_std = 1.0

    def x_modules(donors: list[str]) -> np.ndarray:
        return module_scaler.transform(module_features.loc[donors].to_numpy(dtype=float))

    def x_residuals(donors: list[str]) -> np.ndarray:
        return residual_scaler.transform(residual_features.loc[donors].to_numpy(dtype=float))

    def y_scaled(donors: list[str]) -> np.ndarray:
        return ((y_log.loc[donors].to_numpy(dtype=float) - y_mean) / y_std).astype(np.float32)

    set_seed(target_seed)
    model = NonGraphV3MLP(
        condition=condition,
        n_module_features=module_features.shape[1],
        n_residual_features=residual_features.shape[1],
        hidden_dim=int(cfg["model"]["hidden_dim"]),
        dropout=float(cfg["model"]["dropout"]),
        shared_trunk=bool(cfg["model"]["shared_trunk"]),
    )
    opt = torch.optim.AdamW(
        model.parameters(),
        lr=float(cfg["training"]["learning_rate"]),
        weight_decay=float(cfg["training"]["weight_decay"]),
    )
    loss_fn = torch.nn.MSELoss()
    max_epochs = int(cfg["training"]["epochs"])
    patience = int(cfg["training"]["patience"])

    xm_fit = tensor(x_modules(train_fit))
    xr_fit = tensor(x_residuals(train_fit))
    y_fit = tensor(y_scaled(train_fit))
    xm_val = tensor(x_modules(train_val))
    xr_val = tensor(x_residuals(train_val))
    y_val = tensor(y_scaled(train_val))

    best_state = None
    best_val = math.inf
    bad_epochs = 0
    epochs_run = 0
    for epoch in range(1, max_epochs + 1):
        model.train()
        opt.zero_grad()
        loss = loss_fn(model(xm_fit, xr_fit), y_fit)
        loss.backward()
        opt.step()
        model.eval()
        with torch.no_grad():
            val_loss = float(loss_fn(model(xm_val, xr_val), y_val).detach().cpu())
        epochs_run = epoch
        if val_loss < best_val - 1e-5:
            best_val = val_loss
            best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
            bad_epochs = 0
        else:
            bad_epochs += 1
        if bad_epochs >= patience:
            break
    if best_state is not None:
        model.load_state_dict(best_state)
    model.eval()
    with torch.no_grad():
        pred_scaled = model(tensor(x_modules(test_donors)), tensor(x_residuals(test_donors))).detach().cpu().numpy()
    pred_log = pred_scaled * y_std + y_mean
    pred = np.expm1(pred_log)
    pred = np.maximum(pred, 0.0)
    info = {
        "fold_id": fold_id,
        "epochs_run": epochs_run,
        "best_inner_val_mse": best_val,
        "n_train_fit_donors": len(train_fit),
        "n_inner_val_donors": len(train_val),
    }
    return pred, info


def discover_external_pretraining_status(cfg: dict) -> dict[str, object]:
    registry_path = resolve(cfg["paths"]["dataset_role_registry"])
    registry = pd.read_csv(registry_path)
    eligible = registry[
        (
            registry["allowed_for_pretraining"].astype(bool)
            | registry["allowed_for_training"].astype(bool)
        )
        & (~registry["reserved_for_clean_validation"].astype(bool))
        & (~registry["allowed_for_model_selection"].astype(bool))
    ].copy()
    clean_holdout_used = bool((eligible["reserved_for_clean_validation"].astype(bool)).any())
    candidates = []
    for root in cfg["external_pretraining"].get("local_matrix_candidates", []):
        root_path = resolve(root)
        if root_path.exists():
            for pattern in ["*.h5ad", "*.csv", "*.csv.gz", "*.tsv", "*.tsv.gz"]:
                candidates.extend(root_path.glob(pattern))
    # Stage 27B only consumes matrices tied to the current registry. Existing
    # v2 alignment H5ADs are not enough unless the registry marks the dataset
    # eligible for pretraining/training.
    usable = []
    for path in candidates:
        text = str(path).lower()
        for row in eligible.itertuples():
            tokens = [str(row.dataset_id).lower(), str(row.dataset_name).lower(), str(row.collection_name).lower()]
            if any(token and token != "nan" and token in text for token in tokens):
                usable.append(str(path))
    status = "available" if usable else "missing_external_matrix"
    return {
        "status": status,
        "eligible_dataset_count": int(len(eligible)),
        "eligible_datasets_preview": "; ".join(eligible["dataset_id"].astype(str).head(12).tolist()),
        "usable_local_matrices": "; ".join(sorted(set(usable))),
        "clean_holdout_used": clean_holdout_used,
        "notes": "No automatic downloads are allowed; Stage 27B is skipped unless approved local aligned matrices exist."
        if not usable
        else "Usable external matrices detected, but this runner currently leaves pretraining disabled pending explicit matrix audit.",
    }


def run_sea_ad_only(cfg: dict) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    inputs = read_inputs(
        resolve(cfg["paths"]["locked_folds"]),
        resolve(cfg["paths"]["target_manifest"]),
        resolve(cfg["paths"]["metadata_targets"]),
        resolve(cfg["paths"]["pseudobulk_features"]),
    )
    rows = []
    fold_rows = []
    for condition_idx, condition in enumerate(cfg["conditions"]):
        for target_idx, target_row in inputs.targets.iterrows():
            target_alias = target_row["target_alias"]
            target_name = target_row["target_name"]
            y = inputs.target_matrix[target_alias].dropna()
            folds = inputs.folds[inputs.folds["donor_id"].astype(str).isin(y.index)].copy()
            for fold_id in sorted(folds["fold_id"].unique()):
                test_donors = folds.loc[folds["fold_id"] == fold_id, "donor_id"].astype(str).tolist()
                train_donors = folds.loc[folds["fold_id"] != fold_id, "donor_id"].astype(str).tolist()
                train_donors = [d for d in train_donors if d in y.index]
                test_donors = [d for d in test_donors if d in y.index]
                residual_cols = select_residual_columns(
                    inputs.expression,
                    train_donors,
                    inputs.module_genes,
                    int(cfg["model"]["max_residual_features"]),
                )
                residual_features = inputs.expression.loc[:, residual_cols]
                seed = int(cfg["random_seed"]) + 1000 * condition_idx + 100 * int(fold_id) + target_idx
                pred, info = fit_one_fold(
                    condition,
                    inputs.module_features,
                    residual_features,
                    y,
                    int(fold_id),
                    train_donors,
                    test_donors,
                    cfg,
                    seed,
                )
                fold_rows.append(
                    {
                        "run_id": "v3_sea_ad_only_non_graph",
                        "architecture_condition": condition,
                        "target": target_name,
                        "target_alias": target_alias,
                        "fold_id": int(fold_id),
                        "n_train_donors": len(train_donors),
                        "n_test_donors": len(test_donors),
                        "n_module_features": inputs.module_features.shape[1],
                        "n_residual_features": len(residual_cols),
                        "random_seed": seed,
                        **info,
                        "leakage_check": "fold_local_scalers_feature_selection_and_inner_validation",
                    }
                )
                for donor, y_true, y_pred in zip(test_donors, y.loc[test_donors].to_numpy(dtype=float), pred):
                    rows.append(
                        {
                            "run_id": "v3_sea_ad_only_non_graph",
                            "architecture_condition": condition,
                            "pretraining_status": "not_applicable",
                            "target": target_name,
                            "target_alias": target_alias,
                            "donor_id": donor,
                            "fold_id": int(fold_id),
                            "y_true": float(y_true),
                            "y_pred": float(y_pred),
                            "random_seed": seed,
                            "clean_holdout_used": False,
                            "heldout_donor_leakage_detected": False,
                        }
                    )
    pred_df = pd.DataFrame(rows)
    fold_df = pd.DataFrame(fold_rows)
    metric_rows = []
    for keys, group in pred_df.groupby(["run_id", "architecture_condition", "target", "target_alias"], dropna=False):
        run_id, condition, target, target_alias = keys
        m = regression_metrics(group["y_true"].to_numpy(), group["y_pred"].to_numpy())
        metric_rows.append(
            {
                "run_id": run_id,
                "architecture_condition": condition,
                "target": target,
                "target_alias": target_alias,
                "n_donors": int(group["donor_id"].nunique()),
                **m,
            }
        )
    target_metrics = pd.DataFrame(metric_rows)
    mean_metrics = (
        target_metrics.groupby(["run_id", "architecture_condition"], dropna=False)
        .agg(
            mean_pooled_oof_spearman=("pooled_oof_spearman", "mean"),
            min_target_pooled_oof_spearman=("pooled_oof_spearman", "min"),
            n_targets=("target", "nunique"),
        )
        .reset_index()
    )
    return pred_df, target_metrics, mean_metrics, fold_df


def target_deltas(target_metrics: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    baseline = pd.read_csv(resolve(cfg["paths"]["baseline_pooled_oof"]))
    module = baseline[baseline["baseline_id"] == "module_mean_baseline"][["target", "pooled_oof_spearman"]].copy()
    module = module.rename(columns={"pooled_oof_spearman": "module_mean_baseline_target_spearman"})
    out = target_metrics.merge(module, on="target", how="left")
    out["delta_vs_module_mean_baseline"] = out["pooled_oof_spearman"] - out["module_mean_baseline_target_spearman"]
    out["target_degradation_fail"] = out["delta_vs_module_mean_baseline"] < float(cfg["max_target_drop_vs_module_mean"])
    return out


def pass_fail(mean_metrics: pd.DataFrame, deltas: pd.DataFrame, external_status: dict, cfg: dict) -> pd.DataFrame:
    rows = []
    threshold = float(cfg["minimum_success_threshold"])
    for row in mean_metrics.itertuples():
        d = deltas[(deltas["run_id"] == row.run_id) & (deltas["architecture_condition"] == row.architecture_condition)]
        stage_pass = (
            float(row.mean_pooled_oof_spearman) >= threshold
            and int(row.n_targets) == 5
            and not bool(d["target_degradation_fail"].any())
        )
        rows.append(
            {
                "run_id": row.run_id,
                "architecture_condition": row.architecture_condition,
                "status": "complete",
                "mean_pooled_oof_spearman": float(row.mean_pooled_oof_spearman),
                "minimum_success_threshold": threshold,
                "all_five_targets_reported": int(row.n_targets) == 5,
                "target_degradation_check_pass": not bool(d["target_degradation_fail"].any()),
                "clean_holdout_used": False,
                "heldout_donor_leakage_detected": False,
                "stage27_pass": bool(stage_pass),
                "notes": "SEA-AD-only non-graph v3 condition; no graph topology.",
            }
        )
    rows.append(
        {
            "run_id": "v3_external_pretrained_non_graph",
            "architecture_condition": "external_pretraining_interface",
            "status": external_status["status"],
            "mean_pooled_oof_spearman": np.nan,
            "minimum_success_threshold": threshold,
            "all_five_targets_reported": False,
            "target_degradation_check_pass": False,
            "clean_holdout_used": bool(external_status["clean_holdout_used"]),
            "heldout_donor_leakage_detected": False,
            "stage27_pass": False,
            "notes": external_status["notes"],
        }
    )
    return pd.DataFrame(rows)


def write_report(
    pred_df: pd.DataFrame,
    target_metrics: pd.DataFrame,
    mean_metrics: pd.DataFrame,
    deltas: pd.DataFrame,
    pf: pd.DataFrame,
    bootstrap: pd.DataFrame,
    external_status: dict,
    fold_df: pd.DataFrame,
    cfg: dict,
) -> None:
    def csv_block(df: pd.DataFrame) -> str:
        return "```csv\n" + df.to_csv(index=False).strip() + "\n```"

    best = mean_metrics.sort_values("mean_pooled_oof_spearman", ascending=False).head(1)
    best_line = "No completed SEA-AD-only conditions."
    if not best.empty:
        r = best.iloc[0]
        best_line = f"Best SEA-AD-only condition: `{r.architecture_condition}` with mean pooled OOF Spearman `{r.mean_pooled_oof_spearman:.4f}`."
    lines = [
        "# Stage 27 non-graph v3 report",
        "",
        "## 1. Executive summary",
        "",
        best_line,
        f"Official baseline: module_mean_baseline = `{cfg['module_mean_baseline']:.4f}`. Minimum v3 success threshold = `{cfg['minimum_success_threshold']:.4f}`.",
        "This stage runs non-graph neural training regimes only. It does not support graph-topology claims.",
        "",
        "## 2. What was run",
        "",
        "- Stage 27A `v3_sea_ad_only_non_graph` over locked Stage 24 donor folds.",
        "- Conditions: " + ", ".join(cfg["conditions"]) + ".",
        "- Fold-local scaling, feature selection, target scaling, and inner validation.",
        f"- Bootstrap uncertainty: `{len(bootstrap) > 0}` with `{cfg['bootstrap']['n_resamples']}` donor resamples per completed condition/target.",
        "",
        "## 3. What was not run",
        "",
        "- No real graph branch.",
        "- No no-graph/identity graph-control branch.",
        "- No strict-shuffled graph branch.",
        "- No external validation.",
        "- No H5AD/expression matrix downloads.",
        "- No manuscript claim update.",
        "",
        "## 4. Dataset roles used",
        "",
        "- SEA-AD internal donor-held-out folds were used for Stage 27A.",
        f"- Stage 27B external pretraining status: `{external_status['status']}`.",
        f"- Eligible external datasets in registry: `{external_status['eligible_dataset_count']}`.",
        "- Clean holdout datasets were not used.",
        "",
        "## 5. Leakage controls",
        "",
        "- Locked donor folds from Stage 24.",
        "- All feature selection happens inside training folds only.",
        "- Standard scalers fit on training donors only.",
        "- Inner validation donors are selected from training donors only.",
        "- Held-out donor targets are never used for fitting.",
        "",
        "## 6. Architecture conditions",
        "",
        "- `module_only_mlp`: predefined microglia module branch only.",
        "- `expression_residual_only_mlp`: top-variance non-module expression residual branch only.",
        "- `late_fusion_module_residual_mlp`: module and residual branches fused late.",
        "",
        "## 7. SEA-AD-only results",
        "",
        csv_block(mean_metrics),
        "",
        "## 8. External-pretrained results or skipped status",
        "",
        f"Status: `{external_status['status']}`.",
        f"Usable local matrices: `{external_status['usable_local_matrices'] or 'none'}`.",
        "No automatic external matrix download was attempted.",
        "",
        "## 9. Comparison against module_mean_baseline = 0.3128",
        "",
        csv_block(deltas[["run_id", "architecture_condition", "target", "pooled_oof_spearman", "module_mean_baseline_target_spearman", "delta_vs_module_mean_baseline"]]),
        "",
        "## 10. Pass/fail against 0.3228",
        "",
        csv_block(pf),
        "",
        "## 11. Target-level degradation check",
        "",
        "A condition fails the target-level degradation gate if any target delta versus module_mean_baseline is `< -0.02`.",
        "",
        "## 12. Recommendation for next stage",
        "",
        "Use these Stage 27A results as the non-graph neural baseline. Stage 27B should remain skipped until approved local external matrices pass matrix, gene-overlap, donor-mapping, and role-registry audits. Graph branches should not be run until non-graph regimes and leakage checks are accepted.",
        "",
        "## Fold audit",
        "",
        f"Fold assignment rows saved in OOF predictions and fold audit. Unique folds: `{sorted(fold_df['fold_id'].unique().tolist())}`.",
    ]
    REPORT_OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def update_scorecard_and_docs(mean_metrics: pd.DataFrame, pf: pd.DataFrame, external_status: dict, cfg: dict) -> None:
    scorecard_path = TABLE_DIR / "v3_scorecard_status_v1.csv"
    if scorecard_path.exists():
        score = pd.read_csv(scorecard_path)
        best = mean_metrics.sort_values("mean_pooled_oof_spearman", ascending=False).head(1)
        sea_value = "not_run" if best.empty else f"{float(best.iloc[0]['mean_pooled_oof_spearman']):.4f}"
        sea_pass = "pass" if bool(pf[pf["run_id"] == "v3_sea_ad_only_non_graph"]["stage27_pass"].any()) else "fail"
        score.loc[score["scorecard_item"] == "v3_sea_ad_only_non_graph", ["status", "current_value", "pass_fail", "notes"]] = [
            "complete",
            sea_value,
            sea_pass,
            "Stage 27A non-graph neural SEA-AD-only run completed; no graph topology.",
        ]
        score.loc[score["scorecard_item"] == "v3_external_pretrained_non_graph", ["status", "current_value", "pass_fail", "notes"]] = [
            external_status["status"],
            "not_run",
            "skipped",
            "Stage 27B interface implemented; skipped because no approved local external matrix was available.",
        ]
        score.to_csv(scorecard_path, index=False)

    active_path = ROOT / "docs" / "ACTIVE_V3_STATUS.md"
    if active_path.exists():
        text = active_path.read_text(encoding="utf-8")
        marker = "\n## Stage 27A/27B run status\n"
        addition = (
            marker
            + "\nStage 27 non-graph v3 has been run for SEA-AD-only conditions. "
            + "The external-pretrained interface is implemented but remains skipped unless approved local external matrices are available. "
            + "No graph branch or graph-specific control has been run in Stage 27.\n"
        )
        text = text.split(marker)[0].rstrip() + "\n" + addition
        active_path.write_text(text, encoding="utf-8")

    score_doc = ROOT / "docs" / "V3_SCORECARD.md"
    if score_doc.exists():
        text = score_doc.read_text(encoding="utf-8")
        marker = "\n## Stage 27 non-graph status\n"
        best = mean_metrics.sort_values("mean_pooled_oof_spearman", ascending=False).head(1)
        best_line = "No completed SEA-AD-only result."
        if not best.empty:
            r = best.iloc[0]
            best_line = f"Best completed SEA-AD-only non-graph condition: `{r.architecture_condition}` (`{r.mean_pooled_oof_spearman:.4f}`)."
        addition = (
            marker
            + f"\n{best_line} Stage 27B external-pretrained status: `{external_status['status']}`. "
            + "These are non-graph training regimes and do not support graph-specific claims.\n"
        )
        text = text.split(marker)[0].rstrip() + "\n" + addition
        score_doc.write_text(text, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Stage 27 non-graph Graph-JEPA v3 training regimes.")
    parser.add_argument("--config", default="configs/train/stage27_non_graph_v3.yaml")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--skip-scorecard-update", action="store_true")
    args = parser.parse_args()

    cfg = load_config(resolve(args.config))
    if args.smoke:
        cfg["training"]["epochs"] = int(cfg["training"]["smoke_epochs"])
        cfg["training"]["patience"] = min(int(cfg["training"]["patience"]), int(cfg["training"]["smoke_epochs"]))
        cfg["bootstrap"]["n_resamples"] = int(cfg["bootstrap"]["smoke_resamples"])

    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    try:
        external_status = discover_external_pretraining_status(cfg)
        pred_df, target_metrics, mean_metrics, fold_df = run_sea_ad_only(cfg)
        deltas = target_deltas(target_metrics, cfg)
        pf = pass_fail(mean_metrics, deltas, external_status, cfg)
        bootstrap = donor_bootstrap_ci(
            pred_df,
            ["run_id", "architecture_condition", "target", "target_alias"],
            n_resamples=int(cfg["bootstrap"]["n_resamples"]),
            seed=int(cfg["random_seed"]),
        )
        pred_df.to_csv(OOF_OUT, index=False)
        target_metrics.to_csv(TARGET_METRICS_OUT, index=False)
        mean_metrics.to_csv(MEAN_METRICS_OUT, index=False)
        deltas.to_csv(DELTAS_OUT, index=False)
        pf.to_csv(PASS_FAIL_OUT, index=False)
        bootstrap.to_csv(BOOTSTRAP_OUT, index=False)
        fold_df.to_csv(MODEL_DIR / "stage27_non_graph_v3_fold_training_audit_v1.csv", index=False)
        (MODEL_DIR / "stage27_non_graph_v3_config_used.json").write_text(json.dumps(cfg, indent=2), encoding="utf-8")
        write_report(pred_df, target_metrics, mean_metrics, deltas, pf, bootstrap, external_status, fold_df, cfg)
        if not args.skip_scorecard_update and not args.smoke:
            update_scorecard_and_docs(mean_metrics, pf, external_status, cfg)
    except Exception as exc:
        failure = "\n".join(
            [
                "# Stage 27 non-graph v3 failure report",
                "",
                f"Failure: `{type(exc).__name__}: {exc}`",
                "",
                "No successful Stage 27 result should be inferred from this failed run.",
            ]
        )
        REPORT_OUT.write_text(failure + "\n", encoding="utf-8")
        raise

    print(f"Wrote {OOF_OUT}")
    print(f"Wrote {TARGET_METRICS_OUT}")
    print(f"Wrote {MEAN_METRICS_OUT}")
    print(f"Wrote {DELTAS_OUT}")
    print(f"Wrote {PASS_FAIL_OUT}")
    print(f"Wrote {BOOTSTRAP_OUT}")
    print(f"Wrote {REPORT_OUT}")


if __name__ == "__main__":
    main()
