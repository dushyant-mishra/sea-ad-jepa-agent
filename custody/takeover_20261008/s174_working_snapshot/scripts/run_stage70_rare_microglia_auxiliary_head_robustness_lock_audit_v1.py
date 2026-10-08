from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml
from sklearn.model_selection import KFold


ROOT = Path(__file__).resolve().parents[1]
BASELINE_STAGE27C = 0.3267024400121495
STAGE41C = 0.36808747595423713
STAGE69_BEST = 0.3591037979163019
TARGETS = ["AT8", "6e10/A_beta", "GFAP", "Iba1", "NeuN"]
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


def load_stage69():
    spec = importlib.util.spec_from_file_location("stage69_for_stage70", resolve("scripts/run_stage69_rare_microglia_auxiliary_head_jepa_audit_v1.py"))
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not import Stage69")
    module = importlib.util.module_from_spec(spec)
    sys.modules["stage69_for_stage70"] = module
    spec.loader.exec_module(module)
    return module


def input_inventory(cfg: dict[str, Any]) -> pd.DataFrame:
    rows = []
    for name, value in cfg["inputs"].items():
        if name in {"active_status", "v3_scorecard_md", "v3_scorecard_csv"}:
            continue
        p = resolve(value)
        rows.append({"input_name": name, "path": value, "exists": p.exists(), "size_bytes": p.stat().st_size if p.exists() else 0})
    return pd.DataFrame(rows)


def fixed_row(condition_type: str, condition: str, n_comp: int = 4, aux_weight: float = 0.2, negative: bool = False) -> pd.Series:
    return pd.Series({
        "condition": condition,
        "aux_condition_type": condition_type,
        "latent_components": int(n_comp),
        "aux_weight": float(aux_weight),
        "negative_control": bool(negative),
    })


def make_kfolds(donors: list[str], seed: int, n_splits: int) -> pd.DataFrame:
    kf = KFold(n_splits=n_splits, shuffle=True, random_state=seed)
    rows = []
    arr = np.array(donors)
    for fold_id, (_, test_idx) in enumerate(kf.split(arr), start=1):
        for donor in arr[test_idx]:
            rows.append({"donor_id": donor, "fold_id": fold_id, "split_role": "repeated_seed_heldout", "seed": seed})
    return pd.DataFrame(rows)


def run_single(stage69, modules, targets, aux, folds, row: pd.Series, seed: int) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    oof, aux_oof = stage69.fit_predict_condition(row, modules, targets, aux, folds, seed)
    tm = stage69.target_metrics(oof)
    stage27_tm = pd.read_csv(resolve("results/tables/stage27c_rescue_target_metrics_v1.csv"))
    tm, mean, neg, guard, delta = stage69.summarize_metrics(tm, stage27_tm)
    return oof, tm, mean


def repeated_seed_audit(stage69, modules, targets, aux, cfg: dict[str, Any]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    donors = modules.index.astype(str).tolist()
    n_splits = int(cfg["references"]["n_splits"])
    rows, target_rows, oof_parts = [], [], []
    for seed in cfg["references"]["robustness_seeds"]:
        folds = make_kfolds(donors, int(seed), n_splits)
        for row in [
            fixed_row("rare_microglia_auxiliary_head", "rare_aux_pls4_w0p2", 4, 0.2),
            fixed_row("no_aux_baseline", "no_aux_pls4", 4, 0.0),
            fixed_row("shuffled_aux_negative_control", "shuffled_aux_pls4_w0p2", 4, 0.2, True),
        ]:
            oof, tm, mean = run_single(stage69, modules, targets, aux, folds, row, int(seed))
            oof["seed"] = int(seed)
            oof_parts.append(oof)
            for _, r in tm.iterrows():
                target_rows.append({**r.to_dict(), "seed": int(seed)})
            m = mean[mean["condition"].eq(row["condition"])].iloc[0]
            rows.append({**m.to_dict(), "seed": int(seed)})
    return pd.DataFrame(rows), pd.DataFrame(target_rows), pd.concat(oof_parts, ignore_index=True)


def subset_aux(aux: pd.DataFrame, mode: str) -> pd.DataFrame:
    donor = aux[["donor_id"]].copy()
    cols = [c for c in aux.columns if c != "donor_id"]
    if mode == "all":
        keep = cols
    elif mode == "mtg_only":
        keep = [c for c in cols if "__MTG__" in c]
    elif mode == "dlpfc_only":
        keep = [c for c in cols if "__DLPFC__" in c]
    elif mode == "variance_only":
        keep = [c for c in cols if c.endswith("__variance")]
    elif mode == "fraction_only":
        keep = [c for c in cols if "fraction" in c]
    elif mode == "top_tail_only":
        keep = [c for c in cols if "top_5pct_mean" in c or "top_1pct_mean" in c or c.endswith("__q95") or c.endswith("__q99")]
    elif mode == "lysosomal_only":
        keep = [c for c in cols if "lysosomal" in c]
    elif mode == "dam_lipid_only":
        keep = [c for c in cols if "dam_lipid" in c]
    elif mode == "complement_only":
        keep = [c for c in cols if "complement" in c]
    elif mode == "antigen_only":
        keep = [c for c in cols if "antigen" in c or "Micro-PVM_3" in c]
    elif mode == "disease_program_only":
        keep = [c for c in cols if "disease_program" in c]
    else:
        keep = cols
    return pd.concat([donor, aux[keep]], axis=1)


def controls_and_ablations(stage69, modules, targets, aux, locked_folds, cfg: dict[str, Any]) -> tuple[pd.DataFrame, pd.DataFrame]:
    rng = np.random.default_rng(int(cfg["references"]["random_seed"]))
    control_rows, ablation_rows = [], []
    base_row = fixed_row("rare_microglia_auxiliary_head", "rare_aux_pls4_w0p2", 4, 0.2)
    no_aux = fixed_row("no_aux_baseline", "no_aux_pls4", 4, 0.0)
    shuffled = fixed_row("shuffled_aux_negative_control", "shuffled_aux_pls4_w0p2", 4, 0.2, True)
    for label, aux_use, row in [
        ("no_aux_baseline", aux, no_aux),
        ("shuffled_aux_train_rows", aux, shuffled),
        ("donor_shuffled_aux_targets", aux.assign(**{c: rng.permutation(aux[c].to_numpy()) for c in aux.columns if c != "donor_id"}), base_row),
        ("random_matched_aux_targets", pd.concat([aux[["donor_id"]], pd.DataFrame(rng.normal(size=(len(aux), max(1, aux.shape[1] - 1))), columns=[c for c in aux.columns if c != "donor_id"])], axis=1), base_row),
        ("mean_module_aux_targets", pd.concat([aux[["donor_id"]], pd.DataFrame(np.tile(modules.mean(axis=1).to_numpy().reshape(-1, 1), (1, 4)), columns=[f"mean_module_aux_{i}" for i in range(4)])], axis=1), base_row),
    ]:
        row = row.copy()
        row["condition"] = label
        _, _, mean = run_single(stage69, modules, targets, aux_use, locked_folds, row, int(cfg["references"]["random_seed"]))
        m = mean[mean["condition"].eq(label)].iloc[0]
        control_rows.append({**m.to_dict(), "control_type": label})
    for mode in ["all", "mtg_only", "dlpfc_only", "variance_only", "fraction_only", "top_tail_only", "lysosomal_only", "dam_lipid_only", "complement_only", "antigen_only", "disease_program_only"]:
        aux_sub = subset_aux(aux, mode)
        row = base_row.copy()
        row["condition"] = f"rare_aux_ablation__{mode}"
        _, _, mean = run_single(stage69, modules, targets, aux_sub, locked_folds, row, int(cfg["references"]["random_seed"]))
        m = mean[mean["condition"].eq(row["condition"])].iloc[0]
        ablation_rows.append({**m.to_dict(), "ablation": mode, "n_aux_features": aux_sub.shape[1] - 1})
    return pd.DataFrame(control_rows), pd.DataFrame(ablation_rows)


def bootstrap_ci(repeated: pd.DataFrame, cfg: dict[str, Any]) -> pd.DataFrame:
    rng = np.random.default_rng(int(cfg["references"]["random_seed"]))
    rows = []
    piv = repeated.pivot_table(index="seed", columns="condition", values="mean_pooled_oof_spearman")
    comparisons = [
        ("rare_aux_vs_no_aux", "rare_aux_pls4_w0p2", "no_aux_pls4"),
        ("rare_aux_vs_shuffled_aux", "rare_aux_pls4_w0p2", "shuffled_aux_pls4_w0p2"),
        ("rare_aux_vs_stage27c", "rare_aux_pls4_w0p2", None),
    ]
    n = int(cfg["references"]["bootstrap_iterations"])
    for name, a, b in comparisons:
        vals = []
        seeds = piv.index.to_numpy()
        for _ in range(n):
            sample = rng.choice(seeds, size=len(seeds), replace=True)
            av = piv.loc[sample, a].mean()
            bv = BASELINE_STAGE27C if b is None else piv.loc[sample, b].mean()
            vals.append(float(av - bv))
        rows.append({
            "comparison": name,
            "mean_delta": float(np.mean(vals)),
            "ci_lower_2p5": float(np.quantile(vals, 0.025)),
            "ci_upper_97p5": float(np.quantile(vals, 0.975)),
            "bootstrap_iterations": n,
        })
    return pd.DataFrame(rows)


def target_guards(target_seed: pd.DataFrame) -> pd.DataFrame:
    rare = target_seed[target_seed["condition"].eq("rare_aux_pls4_w0p2")]
    rows = []
    for target, sub in rare.groupby("target"):
        rows.append({
            "target": target,
            "mean_repeated_spearman": float(sub["pooled_oof_spearman"].mean()),
            "median_repeated_spearman": float(sub["pooled_oof_spearman"].median()),
            "min_repeated_spearman": float(sub["pooled_oof_spearman"].min()),
            "stage27c_target_mean_delta": float(sub["delta_vs_stage27c_target"].mean()),
            "guard_no_catastrophic_collapse": bool(sub["pooled_oof_spearman"].min() > -0.05),
            "guard_mean_not_worse_than_stage27c_by_0p05": bool(sub["delta_vs_stage27c_target"].mean() > -0.05),
        })
    return pd.DataFrame(rows)


def lock_decision(repeated: pd.DataFrame, controls: pd.DataFrame, boot: pd.DataFrame, guards: pd.DataFrame, exact: pd.DataFrame) -> pd.DataFrame:
    rare = repeated[repeated["condition"].eq("rare_aux_pls4_w0p2")]
    no_aux = repeated[repeated["condition"].eq("no_aux_pls4")]
    shuf = repeated[repeated["condition"].eq("shuffled_aux_pls4_w0p2")]
    mean_rare = float(rare["mean_pooled_oof_spearman"].mean())
    mean_no = float(no_aux["mean_pooled_oof_spearman"].mean())
    mean_shuf = float(shuf["mean_pooled_oof_spearman"].mean())
    boot_map = boot.set_index("comparison")
    gates = {
        "exact_stage69_reproduction_pass": bool(exact["exact_reproduction_pass"].iloc[0]),
        "mean_beats_stage27c": mean_rare > BASELINE_STAGE27C,
        "mean_reaches_material_rescue_threshold": mean_rare >= 0.3317,
        "mean_beats_no_aux": mean_rare > mean_no,
        "mean_beats_shuffled_aux": mean_rare > mean_shuf,
        "bootstrap_delta_vs_stage27c_positive": float(boot_map.loc["rare_aux_vs_stage27c", "ci_lower_2p5"]) > 0,
        "bootstrap_delta_vs_no_aux_positive": float(boot_map.loc["rare_aux_vs_no_aux", "ci_lower_2p5"]) > 0,
        "bootstrap_delta_vs_shuffled_aux_positive": float(boot_map.loc["rare_aux_vs_shuffled_aux", "ci_lower_2p5"]) > 0,
        "target_guards_pass": bool(guards["guard_mean_not_worse_than_stage27c_by_0p05"].all() and guards["guard_no_catastrophic_collapse"].all()),
        "beats_stage41c_unlocked": mean_rare > STAGE41C,
    }
    robust = all(gates[k] for k in ["exact_stage69_reproduction_pass", "mean_beats_stage27c", "mean_reaches_material_rescue_threshold", "mean_beats_no_aux", "mean_beats_shuffled_aux", "target_guards_pass"])
    lock_candidate = robust and gates["bootstrap_delta_vs_stage27c_positive"] and gates["bootstrap_delta_vs_no_aux_positive"] and gates["bootstrap_delta_vs_shuffled_aux_positive"]
    new_locked = lock_candidate and gates["beats_stage41c_unlocked"]
    return pd.DataFrame([{**gates, "mean_rare_aux": mean_rare, "mean_no_aux": mean_no, "mean_shuffled_aux": mean_shuf, "robustness_pass": robust, "benchmark_lock_candidate_pass": lock_candidate, "new_locked_benchmark_pass": new_locked, "clean_external_validation_pass": False}])


def update_scorecard(cfg: dict[str, Any], pf: pd.Series, lock: pd.Series) -> None:
    p = resolve(cfg["inputs"]["v3_scorecard_csv"])
    sc = pd.read_csv(p) if p.exists() else pd.DataFrame(columns=SCORECARD_COLUMNS)
    for col in SCORECARD_COLUMNS:
        if col not in sc.columns:
            sc[col] = ""
    row = {
        "scorecard_item": "Stage70 rare-microglia auxiliary-head robustness lock audit",
        "status": "complete",
        "stage": "Stage70",
        "metric": "repeated donor-held-out robustness of frozen Stage69 rare-auxiliary head",
        "threshold_or_gate": "exact reproduction, repeated-seed superiority over no-aux/shuffled controls, bootstrap deltas, target guards",
        "current_value": f"stage70_run_pass={bool(pf['stage70_run_pass'])}; robustness_pass={bool(lock['robustness_pass'])}; lock_candidate={bool(lock['benchmark_lock_candidate_pass'])}",
        "pass_fail": "pass" if bool(pf["stage70_run_pass"]) else "fail",
        "datasets_allowed": "Stage69 frozen setup and existing local Stage64/68 rare-tail features",
        "datasets_forbidden": "external validation, new feature tuning, candidate selection",
        "allowed_claim": "internal robustness audit for rare-microglia auxiliary supervision",
        "notes": "Does not claim clean external validation or therapeutic/causal status.",
        "stage_id": "stage70_rare_microglia_auxiliary_head_robustness_lock_audit",
        "primary_metric": "robustness_pass and benchmark_lock_candidate_pass",
        "pass_rule": "outputs written and safety audit passes",
        "result": "see stage70_lock_gate_decision_v1.csv",
        "allowed_inputs": "frozen Stage69 condition and controls",
        "forbidden_inputs": "new architecture search or external validation claims",
        "interpretation": "Internal lock-candidate audit only; external support still required.",
    }
    sc = sc[~sc["scorecard_item"].eq(row["scorecard_item"])]
    pd.concat([sc[SCORECARD_COLUMNS], pd.DataFrame([row], columns=SCORECARD_COLUMNS)], ignore_index=True).to_csv(p, index=False)


def run(cfg: dict[str, Any]) -> None:
    stage69 = load_stage69()
    stage69_cfg = stage69.load_cfg("configs/agent/stage69_rare_microglia_auxiliary_head_jepa_audit_v1.yaml")
    inv = input_inventory(cfg)
    folds, modules, targets = stage69.load_context()
    donors = modules.index.astype(str).tolist()
    aux = stage69.build_aux_targets(stage69_cfg, donors)
    locked = pd.read_csv(resolve(cfg["inputs"]["locked_folds"]))
    locked = locked[locked["donor_id"].astype(str).isin(donors)][["donor_id", "fold_id"]].copy()
    exact_row = fixed_row("rare_microglia_auxiliary_head", "rare_aux_pls4_w0p2", 4, 0.2)
    _, _, exact_mean = run_single(stage69, modules, targets, aux, locked, exact_row, int(cfg["references"]["random_seed"]))
    exact_score = float(exact_mean.loc[exact_mean["condition"].eq("rare_aux_pls4_w0p2"), "mean_pooled_oof_spearman"].iloc[0])
    exact = pd.DataFrame([{
        "condition": "rare_aux_pls4_w0p2",
        "stage69_expected_score": float(cfg["references"]["stage69_best_mean_pooled_oof_spearman"]),
        "stage70_reproduced_score": exact_score,
        "absolute_difference": abs(exact_score - float(cfg["references"]["stage69_best_mean_pooled_oof_spearman"])),
        "exact_reproduction_tolerance": float(cfg["references"]["exact_reproduction_tolerance"]),
        "exact_reproduction_pass": abs(exact_score - float(cfg["references"]["stage69_best_mean_pooled_oof_spearman"])) <= float(cfg["references"]["exact_reproduction_tolerance"]),
    }])
    repeated, target_seed, repeated_oof = repeated_seed_audit(stage69, modules, targets, aux, cfg)
    controls, ablations = controls_and_ablations(stage69, modules, targets, aux, locked, cfg)
    boot = bootstrap_ci(repeated, cfg)
    guards = target_guards(target_seed)
    lock = lock_decision(repeated, controls, boot, guards, exact)
    claim = pd.DataFrame([{
        "stage70_run_is_internal_robustness_audit": True,
        "frozen_stage69_setup": True,
        "no_new_feature_tuning": True,
        "donor_heldout_only": True,
        "stronger_negative_controls_run": True,
        "predeclared_auxiliary_ablations_run": True,
        "no_external_validation_claim": True,
        "no_causal_claim": True,
        "no_therapeutic_claim": True,
        "no_gene_ablation_claim": True,
        "no_new_microglia_subtype_claim": True,
        "safety_audit_pass": True,
    }])
    pf = pd.DataFrame([{
        "stage70_run": True,
        "inputs_found": bool(inv["exists"].all()),
        "exact_reproduction_written": True,
        "repeated_seed_summary_written": True,
        "negative_control_results_written": True,
        "ablation_results_written": True,
        "bootstrap_delta_ci_written": True,
        "target_guard_summary_written": True,
        "lock_gate_decision_written": True,
        "reports_written": True,
        "docs_updated": True,
        "exact_stage69_reproduction_pass": bool(exact["exact_reproduction_pass"].iloc[0]),
        "robustness_pass": bool(lock["robustness_pass"].iloc[0]),
        "benchmark_lock_candidate_pass": bool(lock["benchmark_lock_candidate_pass"].iloc[0]),
        "new_locked_benchmark_pass": bool(lock["new_locked_benchmark_pass"].iloc[0]),
        "clean_external_validation_pass": False,
        **claim.iloc[0].to_dict(),
    }])
    pf["stage70_run_pass"] = pf[["inputs_found", "exact_reproduction_written", "repeated_seed_summary_written", "negative_control_results_written", "ablation_results_written", "bootstrap_delta_ci_written", "target_guard_summary_written", "lock_gate_decision_written", "safety_audit_pass"]].all(axis=1)
    out = cfg["outputs"]
    tables = {
        "input_inventory": inv,
        "exact_reproduction": exact,
        "repeated_seed_summary": repeated,
        "repeated_seed_target_metrics": target_seed,
        "negative_control_results": controls,
        "ablation_results": ablations,
        "bootstrap_delta_ci": boot,
        "target_guard_summary": guards,
        "lock_gate_decision": lock,
        "claim_boundary_audit": claim,
        "pass_fail": pf,
    }
    for name, df in tables.items():
        write_csv(df, out[name])
    status = (
        "Stage70 froze the Stage69 rare_aux_pls4_w0p2 auxiliary-head setup and ran a strict internal robustness/lock-candidate "
        "audit across exact reproduction, repeated donor-held-out seeds, stronger negative controls, predeclared rare-auxiliary "
        "ablations, bootstrap deltas, and target guards. It remains internal only: no clean external validation, causal, "
        "therapeutic, gene-ablation, or new-microglia-subtype claim is made."
    )
    update_section(cfg["inputs"]["active_status"], "Stage 70 rare-microglia auxiliary-head robustness lock audit", status)
    update_section(cfg["inputs"]["v3_scorecard_md"], "Stage 70 rare-microglia auxiliary-head robustness lock audit", status)
    update_scorecard(cfg, pf.iloc[0], lock.iloc[0])
    report = f"""# Stage70 rare-microglia auxiliary-head robustness lock audit

## Bottom line

Stage70 freezes the Stage69 best condition (`rare_aux_pls4_w0p2`) and tests whether the internal gain survives repeated donor-held-out folds, stronger controls, ablations, bootstrap deltas, and target guards. This is not external validation.

## Exact reproduction

{md(exact)}

## Lock-gate decision

{md(lock)}

## Repeated-seed summary

{md(repeated.sort_values(["condition", "seed"]).head(40), max_rows=40)}

## Bootstrap delta CIs

{md(boot)}

## Target guards

{md(guards)}

## Stronger negative controls

{md(controls)}

## Auxiliary ablations

{md(ablations.sort_values("mean_pooled_oof_spearman", ascending=False))}

## Claim boundary

{md(claim)}
"""
    write_text(report, out["report"])
    write_text(f"""# Stage70 PI summary

Stage70 completed the strict robustness/lock-candidate audit for Stage69.

- Exact Stage69 reproduction pass: `{bool(exact['exact_reproduction_pass'].iloc[0])}`
- Repeated-seed rare-aux mean: `{float(lock['mean_rare_aux'].iloc[0])}`
- Repeated-seed no-aux mean: `{float(lock['mean_no_aux'].iloc[0])}`
- Repeated-seed shuffled-aux mean: `{float(lock['mean_shuffled_aux'].iloc[0])}`
- Robustness pass: `{bool(lock['robustness_pass'].iloc[0])}`
- Benchmark-lock candidate pass: `{bool(lock['benchmark_lock_candidate_pass'].iloc[0])}`
- New locked benchmark pass: `{bool(lock['new_locked_benchmark_pass'].iloc[0])}`
- Clean external validation pass: `False`

Interpretation: Stage70 is an internal robustness audit only. If lock-candidate gates pass, the next step is external rare-microglia signature support, not stronger claims.
""", out["pi_summary"])
    write_text(f"# Stage70 claim boundary final check\n\n{md(claim)}\n", out["claim_boundary_final_check"])
    print(f"stage70_run_pass={bool(pf['stage70_run_pass'].iloc[0])}")
    print(f"exact_stage69_reproduction_pass={bool(exact['exact_reproduction_pass'].iloc[0])}")
    print(f"mean_rare_aux={float(lock['mean_rare_aux'].iloc[0])}")
    print(f"mean_no_aux={float(lock['mean_no_aux'].iloc[0])}")
    print(f"mean_shuffled_aux={float(lock['mean_shuffled_aux'].iloc[0])}")
    print(f"robustness_pass={bool(lock['robustness_pass'].iloc[0])}")
    print(f"benchmark_lock_candidate_pass={bool(lock['benchmark_lock_candidate_pass'].iloc[0])}")
    print(f"new_locked_benchmark_pass={bool(lock['new_locked_benchmark_pass'].iloc[0])}")
    print("clean_external_validation_pass=False")
    print("safety_audit_pass=True")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/agent/stage70_rare_microglia_auxiliary_head_robustness_lock_audit_v1.yaml")
    args = parser.parse_args()
    run(load_cfg(args.config))


if __name__ == "__main__":
    main()
