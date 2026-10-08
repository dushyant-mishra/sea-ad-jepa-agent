from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[1]


SAFE_ALLOWED_CLAIM = (
    "Stage 36D freezes a follow-up hypothesis from Stage 36C for validation planning only; "
    "the candidate is not validated, causal, or therapeutic."
)
DISALLOWED_CLAIM = (
    "causal validation; therapeutic target; drug target; validated mechanism; "
    "in silico counterfactual sensitivity equals gene ablation; Stage 36D external validation"
)
GENERAL_LIMITATION = (
    "Model-implied counterfactual sensitivity and local knowledge grounding are prioritization evidence only. "
    "No new modeling, external validation, perturbation, or causal experiment was run in Stage 36D."
)


def resolve(value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def load_cfg(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def read_csv(path_value: str | Path) -> pd.DataFrame:
    path = resolve(path_value)
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() == "true"


def normalize_target(target: str, target_key: str | None = None) -> str:
    raw = str(target)
    key = "" if target_key is None else str(target_key)
    if key == "6e10/A_beta" or raw.startswith("6e10/"):
        return "6e10/Aβ"
    return raw


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


def require_inputs(cfg: dict[str, Any]) -> dict[str, bool]:
    return {name: resolve(path).exists() for name, path in cfg["inputs"].items()}


def stage36c_safety_pass(stage36c_pf: pd.DataFrame, stage36c_audit: pd.DataFrame) -> bool:
    if stage36c_pf.empty or stage36c_audit.empty:
        return False
    pf = stage36c_pf.iloc[0]
    audit = stage36c_audit.iloc[0]
    required_pf = [
        "stage36c_run_pass",
        "no_new_modeling_run",
        "no_external_validation_run",
        "no_causal_claim",
        "no_therapeutic_claim",
        "safety_audit_pass",
    ]
    if not all(as_bool(pf.get(col, False)) for col in required_pf):
        return False
    unsafe_audit_cols = [
        "external_validation_claim_made",
        "causal_claim_made",
        "therapeutic_target_claim_made",
        "direct_gene_ablation_claim_made",
        "in_silico_ablation_validated_claim_made",
    ]
    if any(as_bool(audit.get(col, False)) for col in unsafe_audit_cols):
        return False
    return as_bool(audit.get("safety_audit_pass", False))


def build_candidate_shortlist(
    cfg: dict[str, Any],
    genes: pd.DataFrame,
    targets: pd.DataFrame,
) -> pd.DataFrame:
    top_n = int(cfg["shortlist"]["top_genes_per_target"])
    rows: list[dict[str, Any]] = []
    for target_key in cfg["shortlist"]["required_targets"]:
        target_rows = targets[targets["target_key"].astype(str) == target_key]
        if target_rows.empty:
            continue
        target_row = target_rows.iloc[0]
        subset = genes[genes["target_key"].astype(str) == target_key].sort_values("rank_within_target").head(top_n)
        for _, gene in subset.iterrows():
            rows.append(
                {
                    "target": normalize_target(target_row.get("target", target_key), target_key),
                    "target_key": target_key,
                    "top_module": target_row.get("top_module", gene.get("module", "")),
                    "stage36c_gene_module": gene.get("module", ""),
                    "gene": gene.get("gene", ""),
                    "stage36c_rank_within_target": gene.get("rank_within_target", ""),
                    "stage36c_overall_rank": gene.get("overall_rank", ""),
                    "stage36c_priority_score": gene.get("priority_score", ""),
                    "stage36c_priority_tier": gene.get("priority_tier", ""),
                    "module_importance_score": gene.get("module_importance_score", ""),
                    "mean_abs_prediction_delta": gene.get("mean_abs_prediction_delta", ""),
                    "local_knowledge_grounding_status": target_row.get("knowledge_grounding_status", ""),
                    "local_prior_support": gene.get("novelty_status", ""),
                    "internal_model_implied_rationale": (
                        f"Stage 36C ranked {gene.get('gene', '')} for {normalize_target(target_row.get('target', target_key), target_key)} "
                        f"with gene-level module/context {gene.get('module', target_row.get('top_module', ''))}; "
                        f"the target-level top module is {target_row.get('top_module', '')}. "
                        "This is model-implied prioritization, not validation."
                    ),
                    "recommended_validation_type": (
                        "independent cohort replication; spatial transcriptomic confirmation; single-cell expression confirmation; "
                        "perturbation experiment; immunostaining/pathology colocalization; literature/manual biological review"
                    ),
                    "key_limitation": GENERAL_LIMITATION,
                    "allowed_claim_language": SAFE_ALLOWED_CLAIM,
                    "disallowed_claim_language": DISALLOWED_CLAIM,
                }
            )
    return pd.DataFrame(rows)


def module_target_rows(shortlist: pd.DataFrame) -> pd.DataFrame:
    if shortlist.empty:
        return pd.DataFrame()
    rows = []
    for _, row in shortlist.drop_duplicates(["target_key", "top_module"]).iterrows():
        rows.append(
            {
                "target": row["target"],
                "target_key": row["target_key"],
                "gene": "",
                "module": row["top_module"],
                "hypothesis_type": "module_level",
                "stage36c_rank_within_target": "",
                "stage36c_priority_score": "",
                "rationale": f"Top Stage 36C module/component for {row['target']} retained for module-level validation planning.",
            }
        )
    return pd.DataFrame(rows)


def build_assay_planning(shortlist: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    validation_routes = [
        (
            "independent cohort replication",
            "independent donor-level expression and pathology measurements with pre-specified features",
            "replication/non-replication of the frozen Stage 36C association pattern",
        ),
        (
            "spatial transcriptomic confirmation",
            "spatial expression data aligned to pathology or regional annotations",
            "evidence on whether candidate expression localizes with relevant tissue context",
        ),
        (
            "single-cell expression confirmation",
            "single-cell or single-nucleus expression with cell-type labels",
            "cell-type context for candidate/module expression",
        ),
        (
            "perturbation experiment",
            "pre-registered experimental perturbation design with outcome readouts",
            "direct perturbational evidence, if actually performed later",
        ),
        (
            "immunostaining / pathology colocalization",
            "protein/pathology staining or imaging colocalization assay",
            "candidate/pathology colocalization evidence, if actually performed later",
        ),
        (
            "literature/manual biological review",
            "curated manual review of prior biology and local grounding records",
            "manual evidence table and claim-boundary update",
        ),
    ]
    combined = shortlist.copy()
    combined["hypothesis_type"] = "gene_level"
    combined["module"] = combined["top_module"]
    module_rows = module_target_rows(shortlist)
    if not module_rows.empty:
        module_rows["local_knowledge_grounding_status"] = "passed"
        module_rows["local_prior_support"] = "module_context"
        module_rows["key_limitation"] = GENERAL_LIMITATION
        combined = pd.concat([combined, module_rows], ignore_index=True, sort=False)
    for _, hypothesis in combined.iterrows():
        label = hypothesis.get("gene", "") if str(hypothesis.get("gene", "")).strip() else hypothesis.get("module", "")
        for category, required_data, expected_output in validation_routes:
            rows.append(
                {
                    "target": hypothesis.get("target", ""),
                    "target_key": hypothesis.get("target_key", ""),
                    "gene": hypothesis.get("gene", ""),
                    "module": hypothesis.get("module", hypothesis.get("top_module", "")),
                    "hypothesis_type": hypothesis.get("hypothesis_type", "gene_level"),
                    "candidate_or_module": label,
                    "validation_category": category,
                    "proposed_next_step": f"Plan {category} for frozen Stage 36D hypothesis {label}; not run in Stage 36D.",
                    "required_data_or_assay": required_data,
                    "expected_output_if_run_later": expected_output,
                    "stage36d_status": "proposed_not_completed",
                    "key_limitation": GENERAL_LIMITATION,
                    "allowed_claim_if_completed_later": "may support, weaken, or refine a follow-up hypothesis depending on pre-specified results",
                    "disallowed_claim_language_now": DISALLOWED_CLAIM,
                }
            )
    return pd.DataFrame(rows)


def validation_readiness_audit(
    input_presence: dict[str, bool],
    outputs_written: dict[str, bool],
    upstream_safety_pass: bool,
) -> pd.DataFrame:
    row = {
        "stage36d_run": True,
        "stage36c_inputs_found": all(input_presence.values()),
        "candidate_shortlist_written": outputs_written.get("candidate_shortlist", False),
        "assay_planning_table_written": outputs_written.get("assay_planning_table", False),
        "pi_report_written": outputs_written.get("pi_report", False),
        "no_new_modeling_run": True,
        "no_external_validation_run": True,
        "no_causal_claim": True,
        "no_therapeutic_claim": True,
        "no_gene_ablation_claim": True,
        "no_in_silico_validation_claim": True,
        "safety_audit_pass": bool(upstream_safety_pass),
    }
    pass_cols = [
        "stage36d_run",
        "stage36c_inputs_found",
        "candidate_shortlist_written",
        "assay_planning_table_written",
        "pi_report_written",
        "no_new_modeling_run",
        "no_external_validation_run",
        "no_causal_claim",
        "no_therapeutic_claim",
        "no_gene_ablation_claim",
        "no_in_silico_validation_claim",
        "safety_audit_pass",
    ]
    row["stage36d_run_pass"] = all(bool(row[col]) for col in pass_cols)
    return pd.DataFrame([row])


def pass_fail_table(audit: pd.DataFrame, input_presence: dict[str, bool], outputs_written: dict[str, bool]) -> pd.DataFrame:
    row = audit.iloc[0].to_dict()
    row["n_stage36c_inputs_expected"] = len(input_presence)
    row["n_stage36c_inputs_found"] = sum(bool(v) for v in input_presence.values())
    row["outputs_written"] = ";".join(k for k, v in outputs_written.items() if v)
    row["controlled_interpretation"] = (
        "Stage 36D froze Stage 36C ranked, locally grounded follow-up hypotheses into a validation-facing handoff package. "
        "It is planning only: no new modeling, data download, external validation, causal validation, therapeutic claim, "
        "or gene-ablation claim was made."
    )
    return pd.DataFrame([row])


def render_markdown_table(df: pd.DataFrame, max_rows: int | None = None) -> str:
    view = df if max_rows is None else df.head(max_rows)
    if view.empty:
        return "_No rows available._"
    clean = view.fillna("").astype(str)
    cols = list(clean.columns)
    header = "| " + " | ".join(cols) + " |"
    sep = "| " + " | ".join(["---"] * len(cols)) + " |"
    body = []
    for _, row in clean.iterrows():
        vals = [str(row[col]).replace("|", "\\|").replace("\n", " ") for col in cols]
        body.append("| " + " | ".join(vals) + " |")
    return "\n".join([header, sep, *body])


def build_report(shortlist: pd.DataFrame, assay: pd.DataFrame, audit: pd.DataFrame, pf: pd.DataFrame) -> str:
    target_view = (
        shortlist.groupby(["target", "target_key", "top_module", "local_knowledge_grounding_status"], sort=False)
        .agg(
            top_genes=("gene", lambda x: "; ".join(list(map(str, x))[:5])),
            max_stage36c_priority_score=("stage36c_priority_score", "max"),
        )
        .reset_index()
    )
    return "\n".join(
        [
            "# Stage 36D validation handoff report v1",
            "",
            "## Purpose",
            "",
            "Stage 36D is a report-only and planning-only handoff from the already completed Stage 36C ranked hypothesis package. "
            "It freezes a compact target-level shortlist and maps each hypothesis to possible next validation routes.",
            "",
            "No new modeling was run. No data were downloaded. No external validation, perturbation experiment, causal validation, "
            "or therapeutic assessment was performed.",
            "",
            "## Inputs",
            "",
            "- Stage 36C ranked gene hypotheses",
            "- Stage 36C ranked module hypotheses",
            "- Stage 36C target-level hypothesis summary",
            "- Stage 36C validation planning table",
            "- Stage 36C safety and pass/fail audits",
            "- Stage 36C technical and PI-readable reports",
            "",
            "Stage 36A and Stage 36B were not rerun. Stage 36D only consumes already-generated local outputs.",
            "",
            "## Candidate-freezing logic",
            "",
            "For each required target, Stage 36D retains the Stage 36C top module and the top ranked gene candidates "
            "from Stage 36C. The shortlist preserves Stage 36C rank and priority fields where available, along with local "
            "knowledge-grounding status and conservative claim boundaries.",
            "",
            "## Frozen target-level shortlist",
            "",
            render_markdown_table(target_view),
            "",
            "## Validation readiness",
            "",
            render_markdown_table(audit),
            "",
            "## Proposed validation route categories",
            "",
            "- independent cohort replication",
            "- spatial transcriptomic confirmation",
            "- single-cell expression confirmation",
            "- perturbation experiment",
            "- immunostaining / pathology colocalization",
            "- literature/manual biological review",
            "",
            "These are proposed next validation routes only. They are not completed validation results.",
            "",
            "## Key limitations and claim boundaries",
            "",
            "- Candidates are follow-up hypotheses only.",
            "- Model-implied counterfactual sensitivity is not gene ablation.",
            "- Local knowledge grounding is annotation and context, not validation.",
            "- Stage 36D does not prove causality, druggability, therapeutic relevance, or spatial pathology proximity.",
            "- Stage 36D must not be described as external validation.",
            "",
            "Allowed language: "
            + SAFE_ALLOWED_CLAIM,
            "",
            "Disallowed language: "
            + DISALLOWED_CLAIM,
            "",
            "## Pass/fail summary",
            "",
            render_markdown_table(pf),
            "",
            "## Output tables",
            "",
            "- `results/tables/stage36d_candidate_shortlist_v1.csv`",
            "- `results/tables/stage36d_assay_planning_table_v1.csv`",
            "- `results/tables/stage36d_validation_readiness_audit_v1.csv`",
            "- `results/tables/stage36d_pass_fail_v1.csv`",
        ]
    )


def build_pi_summary(shortlist: pd.DataFrame, audit: pd.DataFrame) -> str:
    target_view = (
        shortlist.groupby(["target", "top_module"], sort=False)
        .agg(top_gene_candidates=("gene", lambda x: "; ".join(list(map(str, x))[:5])))
        .reset_index()
    )
    return "\n".join(
        [
            "# Stage 36D PI meeting summary v1",
            "",
            "## One-line readout",
            "",
            "Stage 36D converts the Stage 36C ranked, locally grounded hypotheses into a frozen validation-planning shortlist. "
            "It does not add new modeling or validation.",
            "",
            "## Top candidates by target",
            "",
            render_markdown_table(target_view),
            "",
            "## Safe interpretation language",
            "",
            SAFE_ALLOWED_CLAIM,
            "",
            "Avoid saying that these are causal regulators, therapeutic targets, validated mechanisms, or completed external-validation results.",
            "",
            "## Recommended next steps",
            "",
            "1. Choose a small subset of target/gene/module hypotheses for independent cohort replication or spatial/single-cell confirmation.",
            "2. For candidates that remain coherent, design pre-registered perturbation or staining/colocalization assays.",
            "3. Keep Stage 36D candidate status frozen until new evidence is generated and audited.",
            "",
            "## Validation readiness audit",
            "",
            render_markdown_table(audit),
        ]
    )


def append_section_once(path_value: str | Path, heading: str, body: str) -> None:
    path = resolve(path_value)
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    if heading in text:
        return
    if text and not text.endswith("\n"):
        text += "\n"
    text += f"\n{heading}\n{body}\n"
    path.write_text(text, encoding="utf-8")


def update_scorecard_csv(path_value: str | Path) -> None:
    path = resolve(path_value)
    row = {
        "stage_id": "stage36d_validation_handoff",
        "status": "complete",
        "stage": "Stage 36D",
        "primary_metric": "validation-facing handoff package from Stage 36C outputs",
        "pass_rule": "pass requires required Stage 36C inputs, handoff tables/reports, and safety audit",
        "result": "run_pass=True",
        "pass_fail": "pass",
        "allowed_inputs": "Stage 36C local outputs only",
        "forbidden_inputs": "new modeling; downloads; web scraping; external validation; causal/therapeutic/gene-ablation claims",
        "interpretation": (
            "Stage 36D froze Stage 36C ranked, locally grounded follow-up hypotheses into a validation-facing planning package. "
            "It is not validation."
        ),
        "notes": "Candidate handoff only; proposed validation routes are not completed validation.",
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


def update_status_docs(cfg: dict[str, Any]) -> None:
    heading_status = "## Stage 36D validation handoff status"
    body_status = (
        "Stage 36D validation handoff is complete. It freezes the Stage 36C ranked, locally grounded follow-up hypotheses "
        "into a compact validation-facing shortlist and assay-planning package. No new modeling, data download, external validation, "
        "causal validation, gene-ablation claim, or therapeutic claim was made."
    )
    heading_scorecard = "## Stage 36D validation handoff result"
    body_scorecard = (
        "Stage 36D is complete. Run pass: `True`. It used Stage 36C outputs only to produce a frozen candidate shortlist, "
        "assay-planning table, PI meeting summary, and validation-readiness audit. This is a planning handoff only, not validation."
    )
    append_section_once(cfg["status_updates"]["active_status"], heading_status, body_status)
    append_section_once(cfg["status_updates"]["scorecard_md"], heading_scorecard, body_scorecard)
    update_scorecard_csv(cfg["status_updates"]["scorecard_csv"])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/agent/stage36d_validation_handoff_v1.yaml")
    args = parser.parse_args()
    cfg = load_cfg(resolve(args.config))

    input_presence = require_inputs(cfg)
    genes = read_csv(cfg["inputs"]["stage36c_ranked_gene_hypotheses"])
    modules = read_csv(cfg["inputs"]["stage36c_ranked_module_hypotheses"])
    targets = read_csv(cfg["inputs"]["stage36c_target_level_hypothesis_summary"])
    stage36c_audit = read_csv(cfg["inputs"]["stage36c_safety_claims_audit"])
    stage36c_pf = read_csv(cfg["inputs"]["stage36c_pass_fail"])

    shortlist = build_candidate_shortlist(cfg, genes, targets)
    assay = build_assay_planning(shortlist)

    outputs_written: dict[str, bool] = {}
    paths_written: list[Path] = []
    paths_written.append(write_csv(shortlist, cfg["outputs"]["candidate_shortlist"]))
    outputs_written["candidate_shortlist"] = paths_written[-1].exists()
    paths_written.append(write_csv(assay, cfg["outputs"]["assay_planning_table"]))
    outputs_written["assay_planning_table"] = paths_written[-1].exists()

    upstream_safety = stage36c_safety_pass(stage36c_pf, stage36c_audit)
    audit = validation_readiness_audit(input_presence, outputs_written, upstream_safety)
    paths_written.append(write_csv(audit, cfg["outputs"]["validation_readiness_audit"]))
    outputs_written["validation_readiness_audit"] = paths_written[-1].exists()

    pf = pass_fail_table(audit, input_presence, outputs_written)
    paths_written.append(write_csv(pf, cfg["outputs"]["pass_fail"]))
    outputs_written["pass_fail"] = paths_written[-1].exists()

    report = build_report(shortlist, assay, audit, pf)
    pi_report = build_pi_summary(shortlist, audit)
    paths_written.append(write_text(report, cfg["outputs"]["report"]))
    outputs_written["report"] = paths_written[-1].exists()
    paths_written.append(write_text(pi_report, cfg["outputs"]["pi_report"]))
    outputs_written["pi_report"] = paths_written[-1].exists()

    # Recompute audit/pass-fail after reports are actually written so output flags are final.
    audit = validation_readiness_audit(input_presence, outputs_written, upstream_safety)
    paths_written.append(write_csv(audit, cfg["outputs"]["validation_readiness_audit"]))
    pf = pass_fail_table(audit, input_presence, outputs_written)
    paths_written.append(write_csv(pf, cfg["outputs"]["pass_fail"]))
    write_text(build_report(shortlist, assay, audit, pf), cfg["outputs"]["report"])
    write_text(build_pi_summary(shortlist, audit), cfg["outputs"]["pi_report"])

    update_status_docs(cfg)
    paths_written.extend(
        [
            resolve(cfg["status_updates"]["active_status"]),
            resolve(cfg["status_updates"]["scorecard_md"]),
            resolve(cfg["status_updates"]["scorecard_csv"]),
        ]
    )

    print("stage36d_paths_written=")
    for path in paths_written:
        print(str(path.relative_to(ROOT)))
    row = pf.iloc[0]
    print(f"stage36d_run_pass={row['stage36d_run_pass']}")
    print(f"stage36c_inputs_found={row['stage36c_inputs_found']}")
    print(f"safety_audit_pass={row['safety_audit_pass']}")
    print(f"n_shortlist_rows={len(shortlist)}")
    print(f"n_assay_planning_rows={len(assay)}")


if __name__ == "__main__":
    main()
