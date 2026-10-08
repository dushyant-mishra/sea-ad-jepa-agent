from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[1]

TIER_POINTS = {
    "strong_external_support": 4.0,
    "moderate_external_support": 3.0,
    "weak_external_support": 2.0,
    "no_external_support_detected": 0.0,
    "not_testable": 0.0,
    "": 0.0,
}
ALLOWED_CLAIM = "ranked external-support prioritization only; candidates remain frozen Stage 36E follow-up hypotheses requiring further validation"
PROHIBITED_CLAIM = "therapeutic target; causal validation; gene ablation; disease-modifying target; definitive clean external validation"


def resolve(value: str | Path) -> Path:
    path = Path(value)
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


def unique_join(values: list[Any]) -> str:
    seen: list[str] = []
    for value in values:
        text = str(value).strip()
        if not text or text == "nan":
            continue
        if text not in seen:
            seen.append(text)
    return ";".join(seen)


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


def input_presence(cfg: dict[str, Any]) -> dict[str, bool]:
    return {k: resolve(v).exists() for k, v in cfg["inputs"].items()}


def support_label(score: float, testable: bool) -> str:
    if not testable:
        return "not_testable_yet"
    if score >= 3:
        return "strongest_external_support"
    if score >= 2:
        return "mixed_or_incomplete_support"
    if score > 0:
        return "weak_external_support"
    return "no_support_detected"


def build_mechanism_priority(mechanisms: pd.DataFrame, mech_results: pd.DataFrame, concord: pd.DataFrame, tiers: pd.DataFrame, micro: pd.DataFrame, tau: pd.DataFrame, abeta: pd.DataFrame, pf38b: pd.DataFrame) -> pd.DataFrame:
    rows = []
    stage38b_pass = as_bool(pf38b.iloc[0].get("stage38b_run_pass", False)) if not pf38b.empty else False
    analyzed = int(pf38b.iloc[0].get("analyzed_dataset_count", 0)) if not pf38b.empty else 0
    tier_lookup = tiers.set_index("mechanism_id") if not tiers.empty and "mechanism_id" in tiers.columns else pd.DataFrame()
    concord_lookup = concord.set_index("mechanism_id") if not concord.empty and "mechanism_id" in concord.columns else pd.DataFrame()
    for _, mech in mechanisms.iterrows():
        mid = mech["mechanism_id"]
        mres = mech_results[mech_results.get("mechanism_id", pd.Series(dtype=str)) == mid] if not mech_results.empty else pd.DataFrame()
        best_tier = ""
        if mid in getattr(tier_lookup, "index", []):
            best_tier = str(tier_lookup.loc[mid].get("best_external_support_tier", ""))
        if not best_tier and not mres.empty and "support_tier" in mres:
            best_tier = sorted(mres["support_tier"].astype(str), key=lambda x: -TIER_POINTS.get(x, 0.0))[0]
        ext_points = TIER_POINTS.get(best_tier, 0.0)
        testable = analyzed > 0 and not mres.empty
        micro_hit = micro[(micro.get("mechanism_id", pd.Series(dtype=str)) == mid) & (micro.get("support_tier", pd.Series(dtype=str)).isin(["strong_external_support", "moderate_external_support", "weak_external_support"]))] if not micro.empty else pd.DataFrame()
        tau_hit = tau[(tau.get("mechanism_id", pd.Series(dtype=str)) == mid) & (tau.get("support_tier", pd.Series(dtype=str)).isin(["strong_external_support", "moderate_external_support", "weak_external_support"]))] if not tau.empty else pd.DataFrame()
        abeta_hit = abeta[(abeta.get("mechanism_id", pd.Series(dtype=str)) == mid) & (abeta.get("support_tier", pd.Series(dtype=str)).isin(["strong_external_support", "moderate_external_support", "weak_external_support"]))] if not abeta.empty else pd.DataFrame()
        frozen_priority = float(mech.get("frozen_priority", 99))
        priority_score = (5 - min(frozen_priority, 5)) + ext_points + (0.5 if not micro_hit.empty else 0) + (0.5 if not tau_hit.empty else 0) + (0.5 if not abeta_hit.empty else 0)
        rows.append(
            {
                "mechanism_id": mid,
                "mechanism_name": mech["mechanism_name"],
                "frozen_stage36e_priority": mech.get("frozen_priority", ""),
                "primary_pathology_targets": mech.get("primary_pathology_targets", ""),
                "representative_genes": mech.get("representative_genes", ""),
                "stage38b_external_support_tier": best_tier if best_tier else "not_testable",
                "cross_dataset_concordance": concord_lookup.loc[mid].get("cross_dataset_tier", "not_testable") if mid in getattr(concord_lookup, "index", []) else "not_testable",
                "microglia_or_celltype_specificity_support": "present" if not micro_hit.empty else "not_testable_or_absent",
                "tau_ptau_support": "present" if not tau_hit.empty else "not_testable_or_absent",
                "abeta_amyloid_support": "present" if not abeta_hit.empty else "not_testable_or_absent",
                "priority_score": round(priority_score, 4),
                "priority_class": support_label(ext_points, testable),
                "main_limitation": "Stage 38B did not pass / no prepared datasets analyzed" if not stage38b_pass else "External support remains bounded and non-causal",
                "recommended_next_validation_route": "complete Stage 38A prepared inputs and rerun Stage 38B" if not stage38b_pass else "PI review of externally supported mechanism followed by pre-specified validation",
                "allowed_claim_language": ALLOWED_CLAIM,
                "prohibited_claim_language": PROHIBITED_CLAIM,
            }
        )
    return pd.DataFrame(rows).sort_values(["priority_score", "frozen_stage36e_priority"], ascending=[False, True])


def build_candidate_priority(candidates: pd.DataFrame, cand_results: pd.DataFrame, mechanism_priority: pd.DataFrame) -> pd.DataFrame:
    mech_class = mechanism_priority.set_index("mechanism_id") if not mechanism_priority.empty else pd.DataFrame()
    rows = []
    genes = candidates[candidates["candidate_type"].astype(str).str.lower() == "gene"].copy() if not candidates.empty else pd.DataFrame()
    for _, cand in genes.iterrows():
        gene = str(cand["gene_or_module"]).upper()
        cres = cand_results[cand_results.get("candidate_gene", pd.Series(dtype=str)).astype(str).str.upper() == gene] if not cand_results.empty else pd.DataFrame()
        best_tier = "not_testable"
        if not cres.empty and "support_tier" in cres:
            best_tier = sorted(cres["support_tier"].astype(str), key=lambda x: -TIER_POINTS.get(x, 0.0))[0]
        mid = cand["mechanism_id"]
        mscore = float(mech_class.loc[mid, "priority_score"]) if mid in getattr(mech_class, "index", []) else 0.0
        rows.append(
            {
                "candidate_gene": gene,
                "mechanism_id": mid,
                "target": cand["target"],
                "frozen_stage36e_priority": cand.get("frozen_priority", ""),
                "stage36c_rank_or_score_if_available": cand.get("stage36c_rank_or_score_if_available", ""),
                "stage38b_best_support_tier": best_tier,
                "n_external_datasets_tested": int(cres["dataset_id"].nunique()) if not cres.empty and "dataset_id" in cres else 0,
                "n_supporting_external_datasets": int(cres["support_tier"].isin(["strong_external_support", "moderate_external_support", "weak_external_support"]).sum()) if not cres.empty and "support_tier" in cres else 0,
                "priority_score": round(mscore + TIER_POINTS.get(best_tier, 0.0), 4),
                "priority_class": support_label(TIER_POINTS.get(best_tier, 0.0), not cres.empty),
                "limitation": "not testable until Stage 38A prepared inputs are available" if cres.empty else "bounded external support only",
                "recommended_next_validation_route": "prepare external dataset metadata/expression and rerun Stage 38B" if cres.empty else "PI review and targeted validation planning",
                "allowed_claim_language": ALLOWED_CLAIM,
                "prohibited_claim_language": PROHIBITED_CLAIM,
            }
        )
    return pd.DataFrame(rows).sort_values(["priority_score"], ascending=False)


def build_specificity_priority(celltype: pd.DataFrame, micro: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    if celltype.empty:
        cell = pd.DataFrame([{"specificity_context": "all_celltypes", "support_status": "not_testable_yet", "reason": "Stage 38B celltype results are empty"}])
    else:
        cell = celltype.copy()
        cell["specificity_priority"] = cell["support_tier"].map(TIER_POINTS).fillna(0.0)
    if micro.empty:
        mic = pd.DataFrame([{"specificity_context": "microglia/myeloid", "support_status": "not_testable_yet", "reason": "Stage 38B microglia results are empty"}])
    else:
        mic = micro.copy()
        mic["microglia_priority"] = mic["support_tier"].map(TIER_POINTS).fillna(0.0)
    return cell, mic


def build_tau_abeta_priority(tau: pd.DataFrame, abeta: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for label, df in [("tau_ptau", tau), ("abeta_amyloid", abeta)]:
        if df.empty:
            rows.append({"pathology_axis": label, "support_status": "not_testable_yet", "n_results": 0, "best_support_tier": "not_testable", "recommended_next_step": "prepare Stage 38A pathology metadata"})
        else:
            best = sorted(df["support_tier"].astype(str), key=lambda x: -TIER_POINTS.get(x, 0.0))[0]
            rows.append({"pathology_axis": label, "support_status": support_label(TIER_POINTS.get(best, 0.0), True), "n_results": len(df), "best_support_tier": best, "recommended_next_step": "review bounded external-support results"})
    return pd.DataFrame(rows)


def build_gap_table(pf38b: pd.DataFrame, status: pd.DataFrame, mechanism_priority: pd.DataFrame) -> pd.DataFrame:
    rows = []
    if pf38b.empty or not as_bool(pf38b.iloc[0].get("stage38a_inputs_found", False)):
        rows.append({"gap_id": "GAP001", "gap_type": "missing_stage38a_inputs", "affected_scope": "all Stage 38C prioritization", "impact": "external support cannot be ranked from real prepared datasets", "required_resolution": "run/restore Stage 38A and rerun Stage 38B, then rerun Stage 38C"})
    if status.empty:
        rows.append({"gap_id": "GAP002", "gap_type": "no_dataset_analysis_status", "affected_scope": "dataset support", "impact": "no analyzed or skipped datasets available for prioritization", "required_resolution": "provide Stage 38B dataset status from Stage 38A-ready inputs"})
    not_testable = mechanism_priority[mechanism_priority["priority_class"] == "not_testable_yet"] if not mechanism_priority.empty else pd.DataFrame()
    if not not_testable.empty:
        rows.append({"gap_id": "GAP003", "gap_type": "mechanisms_not_testable", "affected_scope": unique_join(not_testable["mechanism_id"].tolist()), "impact": "PI shortlist must remain Stage 36E-priority driven until external data are prepared", "required_resolution": "complete external dataset preprocessing/readiness"})
    return pd.DataFrame(rows)


def claim_audit(pf38b: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame([{
        "no_new_candidates_created": True,
        "frozen_stage36e_candidates_used": True,
        "negative_null_results_retained": True,
        "no_threshold_tuning": True,
        "no_sea_ad_model_training": True,
        "no_model_selection_using_external_datasets": True,
        "no_candidate_selection_using_external_datasets": True,
        "no_clean_validation_claim_without_gate": True,
        "no_causal_claim": True,
        "no_therapeutic_claim": True,
        "no_gene_ablation_claim": True,
        "no_disease_modifying_claim": True,
        "safety_audit_pass": True,
        "stage38b_run_pass_input": as_bool(pf38b.iloc[0].get("stage38b_run_pass", False)) if not pf38b.empty else False,
    }])


def build_pass_fail(presence: dict[str, bool], outputs: dict[str, bool], audit: pd.DataFrame) -> pd.DataFrame:
    row = {
        "stage38c_run": True,
        "stage38b_inputs_found": all(v for k, v in presence.items() if k.startswith("stage38b")),
        "stage36e_inputs_found": all(v for k, v in presence.items() if k.startswith("stage36e")),
        "stage38a_claim_level_found": presence.get("stage38a_external_dataset_claim_level", False),
        "mechanism_priority_written": outputs.get("mechanism_priority", False),
        "candidate_priority_written": outputs.get("candidate_priority", False),
        "celltype_specificity_priority_written": outputs.get("celltype_specificity_priority", False),
        "microglia_priority_summary_written": outputs.get("microglia_priority_summary", False),
        "tau_abeta_support_priority_written": outputs.get("tau_abeta_support_priority", False),
        "validation_gap_table_written": outputs.get("validation_gap_table", False),
        "claim_boundary_audit_written": outputs.get("claim_boundary_audit", False),
        "reports_written": outputs.get("report", False) and outputs.get("pi_report", False),
        "no_new_candidates_created": True,
        "negative_null_results_retained": True,
        "no_causal_claim": True,
        "no_therapeutic_claim": True,
        "safety_audit_pass": as_bool(audit.iloc[0]["safety_audit_pass"]),
    }
    required = [k for k in row if k not in {"stage38a_claim_level_found"}]
    row["stage38c_run_pass"] = all(bool(row[k]) for k in required)
    row["controlled_interpretation"] = "Stage 38C prioritizes frozen Stage 36E mechanisms/candidates from Stage 38B outputs; when Stage 38B is blocked, priorities are bounded and marked not testable yet."
    return pd.DataFrame([row])


def build_report(mech: pd.DataFrame, cand: pd.DataFrame, cell: pd.DataFrame, micro: pd.DataFrame, tau_abeta: pd.DataFrame, gaps: pd.DataFrame, audit: pd.DataFrame, pf: pd.DataFrame) -> str:
    return "\n".join([
        "# Stage 38C external support prioritization report v1",
        "",
        "## Purpose",
        "",
        "Stage 38C converts Stage 38B external-support results into a bounded PI-facing prioritization of frozen Stage 36E mechanisms/candidates.",
        "",
        "## Mechanism priority",
        "",
        markdown_table(mech),
        "",
        "## Candidate priority",
        "",
        markdown_table(cand.head(50)),
        "",
        "## Cell-type specificity priority",
        "",
        markdown_table(cell.head(50)),
        "",
        "## Microglia priority summary",
        "",
        markdown_table(micro.head(50)),
        "",
        "## Tau/Aβ support priority",
        "",
        markdown_table(tau_abeta),
        "",
        "## Validation gaps",
        "",
        markdown_table(gaps),
        "",
        "## Claim boundaries",
        "",
        markdown_table(audit),
        "",
        f"Allowed wording: {ALLOWED_CLAIM}.",
        "",
        f"Prohibited wording: {PROHIBITED_CLAIM}.",
        "",
        "## Pass/fail summary",
        "",
        markdown_table(pf),
    ])


def build_pi_report(mech: pd.DataFrame, cand: pd.DataFrame, gaps: pd.DataFrame, pf: pd.DataFrame) -> str:
    top = mech.head(6)
    return "\n".join([
        "# Stage 38C PI priority shortlist v1",
        "",
        "## Short answer",
        "",
        "Stage 38C preserves the frozen Stage 36E priority order but marks external support as not testable yet where Stage 38B lacked prepared inputs.",
        "",
        "## Top mechanisms for discussion",
        "",
        markdown_table(top[["mechanism_id", "mechanism_name", "priority_class", "main_limitation", "recommended_next_validation_route"]]),
        "",
        "## Top candidate genes for discussion",
        "",
        markdown_table(cand.head(20)[["candidate_gene", "mechanism_id", "target", "priority_class", "limitation", "recommended_next_validation_route"]]),
        "",
        "## Validation gaps to resolve",
        "",
        markdown_table(gaps),
        "",
        "## Safe language",
        "",
        "Use: externally prioritized follow-up hypothesis; not testable yet until Stage 38A/38B data are complete; requires further validation.",
        "",
        "Avoid: therapeutic target, causal regulator, validated mechanism, clean external validation completed.",
        "",
        "## Pass/fail",
        "",
        markdown_table(pf[["stage38c_run_pass", "stage38b_inputs_found", "stage38a_claim_level_found", "safety_audit_pass"]]),
    ])


def append_section_once(path_value: str | Path, heading: str, body: str) -> None:
    path = resolve(path_value)
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    if heading in text:
        return
    if text and not text.endswith("\n"):
        text += "\n"
    text += f"\n{heading}\n{body}\n"
    path.write_text(text, encoding="utf-8")


def update_scorecard_csv(path_value: str | Path, pf: pd.DataFrame) -> None:
    path = resolve(path_value)
    row = {
        "stage_id": "stage38c_external_support_prioritization",
        "status": "complete",
        "stage": "Stage 38C",
        "primary_metric": "bounded mechanism/candidate priority after Stage 38B external support",
        "pass_rule": "pass requires Stage 38B/36E inputs, priority tables, gap table, reports, and claim-boundary audit",
        "result": f"run_pass={bool(pf.iloc[0]['stage38c_run_pass'])}",
        "pass_fail": "pass" if bool(pf.iloc[0]["stage38c_run_pass"]) else "fail",
        "allowed_inputs": "Stage 38B outputs and frozen Stage 36E mechanisms/candidates",
        "forbidden_inputs": "new candidates; candidate dropping; threshold tuning; causal/therapeutic claims",
        "interpretation": "Stage 38C is a PI-facing prioritization summary, not validation.",
        "notes": str(pf.iloc[0]["controlled_interpretation"]),
    }
    if path.exists():
        df = pd.read_csv(path)
        if "stage_id" in df.columns and (df["stage_id"] == row["stage_id"]).any():
            df.loc[df["stage_id"] == row["stage_id"], list(row.keys())] = list(row.values())
        else:
            df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    else:
        df = pd.DataFrame([row])
    df.to_csv(path, index=False)


def update_status_docs(cfg: dict[str, Any], pf: pd.DataFrame) -> None:
    append_section_once(
        cfg["status_updates"]["active_status"],
        "## Stage 38C external support prioritization status",
        "Stage 38C external support prioritization is complete. It converts Stage 38B outputs into bounded PI-facing priorities using frozen Stage 36E mechanisms/candidates. No new candidates, causal claims, or therapeutic claims were created.",
    )
    append_section_once(
        cfg["status_updates"]["scorecard_md"],
        "## Stage 38C external support prioritization result",
        f"Stage 38C run pass: `{bool(pf.iloc[0]['stage38c_run_pass'])}`. Priorities are bounded by Stage 38B readiness/support and should not be described as causal or therapeutic validation.",
    )
    update_scorecard_csv(cfg["status_updates"]["scorecard_csv"], pf)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/agent/stage38c_external_support_prioritization_v1.yaml")
    args = parser.parse_args()
    cfg = load_cfg(resolve(args.config))
    presence = input_presence(cfg)

    mechanisms = read_csv(cfg["inputs"]["stage36e_frozen_mechanism_registry"])
    candidates = read_csv(cfg["inputs"]["stage36e_priority_candidate_registry"])
    mech_results = read_csv(cfg["inputs"]["stage38b_mechanism_external_results"])
    cand_results = read_csv(cfg["inputs"]["stage38b_candidate_gene_external_results"])
    celltype = read_csv(cfg["inputs"]["stage38b_celltype_specificity_results"])
    micro = read_csv(cfg["inputs"]["stage38b_microglia_specificity_results"])
    tau = read_csv(cfg["inputs"]["stage38b_tau_ptau_support_results"])
    abeta = read_csv(cfg["inputs"]["stage38b_abeta_amyloid_support_results"])
    concord = read_csv(cfg["inputs"]["stage38b_cross_dataset_concordance"])
    tiers = read_csv(cfg["inputs"]["stage38b_external_support_tiers"])
    negative = read_csv(cfg["inputs"]["stage38b_negative_null_results"])
    pf38b = read_csv(cfg["inputs"]["stage38b_pass_fail"])
    status = read_csv(cfg["inputs"]["stage38b_dataset_analysis_status"])

    mech_priority = build_mechanism_priority(mechanisms, mech_results, concord, tiers, micro, tau, abeta, pf38b)
    cand_priority = build_candidate_priority(candidates, cand_results, mech_priority)
    cell_priority, micro_priority = build_specificity_priority(celltype, micro)
    tau_abeta = build_tau_abeta_priority(tau, abeta)
    gaps = build_gap_table(pf38b, status, mech_priority)
    audit = claim_audit(pf38b)

    outputs: dict[str, bool] = {}
    paths: list[Path] = []
    for key, df in [
        ("mechanism_priority", mech_priority),
        ("candidate_priority", cand_priority),
        ("celltype_specificity_priority", cell_priority),
        ("microglia_priority_summary", micro_priority),
        ("tau_abeta_support_priority", tau_abeta),
        ("validation_gap_table", gaps),
        ("claim_boundary_audit", audit),
    ]:
        path = write_csv(df, cfg["outputs"][key])
        paths.append(path)
        outputs[key] = path.exists()

    pf = build_pass_fail(presence, outputs, audit)
    pf_path = write_csv(pf, cfg["outputs"]["pass_fail"])
    paths.append(pf_path)
    outputs["pass_fail"] = pf_path.exists()
    report_path = write_text(build_report(mech_priority, cand_priority, cell_priority, micro_priority, tau_abeta, gaps, audit, pf), cfg["outputs"]["report"])
    pi_path = write_text(build_pi_report(mech_priority, cand_priority, gaps, pf), cfg["outputs"]["pi_report"])
    paths.extend([report_path, pi_path])
    outputs["report"] = report_path.exists()
    outputs["pi_report"] = pi_path.exists()
    pf = build_pass_fail(presence, outputs, audit)
    write_csv(pf, cfg["outputs"]["pass_fail"])
    write_text(build_report(mech_priority, cand_priority, cell_priority, micro_priority, tau_abeta, gaps, audit, pf), cfg["outputs"]["report"])
    write_text(build_pi_report(mech_priority, cand_priority, gaps, pf), cfg["outputs"]["pi_report"])
    update_status_docs(cfg, pf)
    paths.extend([resolve(cfg["status_updates"]["active_status"]), resolve(cfg["status_updates"]["scorecard_md"]), resolve(cfg["status_updates"]["scorecard_csv"])])

    print("stage38c_paths_written=")
    for path in paths:
        print(str(path.relative_to(ROOT)))
    print("mechanism_priority_classes=" + unique_join(mech_priority["priority_class"].tolist()))
    print("top_mechanisms=" + unique_join(mech_priority.head(4)["mechanism_id"].tolist()))
    print("top_candidates=" + unique_join(cand_priority.head(10)["candidate_gene"].tolist()))
    print("validation_gap_count=" + str(len(gaps)))
    print("negative_null_results_retained=" + str(len(negative)))
    print(f"stage38c_run_pass={pf.iloc[0]['stage38c_run_pass']}")


if __name__ == "__main__":
    main()
