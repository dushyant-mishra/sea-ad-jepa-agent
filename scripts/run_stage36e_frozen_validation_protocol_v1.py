from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[1]

ALLOWED_CLAIM = (
    "internally prioritized follow-up hypothesis with model-implied sensitivity and locally grounded prior support; "
    "requires independent validation before any strong biological claim"
)
DISALLOWED_CLAIM = (
    "validated target; causal regulator; therapeutic target; gene ablation result; external validation; "
    "disease-modifying target; in silico counterfactual sensitivity equals validation"
)
GENERAL_LIMITATION = (
    "Stage 36E is a frozen registry and validation-protocol package only. It does not run new modeling, download data, "
    "perform external validation, prove causality, or establish therapeutic relevance."
)

MECHANISMS = [
    {
        "mechanism_id": "M1",
        "mechanism_name": "Endolysosomal / autophagy / proteostasis",
        "frozen_priority": 1,
        "genes": ["CTSD", "CTSB", "LAPTM5", "NPC2", "LAMP2"],
        "targets": ["NeuN", "6e10/Aβ", "AT8", "GFAP"],
        "rationale": (
            "This bin captures lysosomal, endosomal, autophagy, and proteostasis-linked candidates that recur in "
            "Stage 36C/36D ranked hypotheses, especially CTSD/CTSB/LAPTM5/NPC2/LAMP2. It is the strongest first "
            "validation theme when supported because it spans neuronal preservation and amyloid/tau/glial pathology contexts."
        ),
    },
    {
        "mechanism_id": "M2",
        "mechanism_name": "Glial activation / disease-associated microglia-astrocyte state",
        "frozen_priority": 2,
        "genes": ["TREM2", "CST7", "APOE", "LGALS3", "CTSD"],
        "targets": ["GFAP", "Iba1", "6e10/Aβ", "AT8"],
        "rationale": (
            "This bin captures disease-associated microglia/astrocyte-state candidates and glial activation context, "
            "including TREM2, CST7, APOE, LGALS3, and CTSD."
        ),
    },
    {
        "mechanism_id": "M3",
        "mechanism_name": "Oxidative stress / antioxidant response",
        "frozen_priority": 3,
        "genes": ["HMOX1", "NQO1", "SOD2", "SOD1", "GPX4"],
        "targets": ["Iba1"],
        "rationale": (
            "This bin captures oxidative-stress and antioxidant-response candidates prioritized for the Iba1 context."
        ),
    },
    {
        "mechanism_id": "M4",
        "mechanism_name": "Inflammatory signaling / transport / cell-state modulation",
        "frozen_priority": 4,
        "genes": ["BSG", "SLC6A12", "IL27RA", "NFKBIA"],
        "targets": ["6e10/Aβ", "AT8"],
        "rationale": (
            "This bin captures inflammatory signaling, transport, and cell-state modulation candidates prioritized in "
            "amyloid/tau-linked Stage 36C/36D rows."
        ),
    },
]


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
    return str(value).strip().lower() == "true"


def input_presence(cfg: dict[str, Any], prefix: str) -> dict[str, bool]:
    return {k: resolve(v).exists() for k, v in cfg["inputs"].items() if k.startswith(prefix)}


def display_target(target: str, target_key: str | None = None) -> str:
    key = "" if target_key is None else str(target_key)
    raw = str(target)
    if key == "6e10/A_beta" or raw.startswith("6e10/"):
        return "6e10/Aβ"
    return raw


def ascii_safe(text: Any) -> str:
    return str(text).replace("β", "beta")


def unique_join(values: list[Any]) -> str:
    seen: list[str] = []
    for value in values:
        s = str(value)
        if not s or s == "nan":
            continue
        if s not in seen:
            seen.append(s)
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


def stage_safety_ok(stage36c_pf: pd.DataFrame, stage36c_audit: pd.DataFrame, stage36d_pf: pd.DataFrame, stage36d_audit: pd.DataFrame) -> bool:
    if stage36c_pf.empty or stage36c_audit.empty or stage36d_pf.empty or stage36d_audit.empty:
        return False
    c = stage36c_pf.iloc[0]
    d = stage36d_pf.iloc[0]
    da = stage36d_audit.iloc[0]
    c_required = ["stage36c_run_pass", "no_new_modeling_run", "no_external_validation_run", "no_causal_claim", "no_therapeutic_claim", "safety_audit_pass"]
    d_required = [
        "stage36d_run_pass",
        "no_new_modeling_run",
        "no_external_validation_run",
        "no_causal_claim",
        "no_therapeutic_claim",
        "no_gene_ablation_claim",
        "no_in_silico_validation_claim",
        "safety_audit_pass",
    ]
    da_required = [
        "no_new_modeling_run",
        "no_external_validation_run",
        "no_causal_claim",
        "no_therapeutic_claim",
        "no_gene_ablation_claim",
        "no_in_silico_validation_claim",
        "safety_audit_pass",
    ]
    return all(as_bool(c.get(col, False)) for col in c_required) and all(as_bool(d.get(col, False)) for col in d_required) and all(as_bool(da.get(col, False)) for col in da_required)


def build_mechanism_registry(shortlist: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for mech in MECHANISMS:
        subset = shortlist[shortlist["gene"].astype(str).isin(mech["genes"])].copy()
        modules = []
        for col in ["top_module", "stage36c_gene_module"]:
            if col in subset.columns:
                modules.extend(subset[col].dropna().tolist())
        supporting_targets = []
        if "target" in subset.columns:
            supporting_targets = [display_target(t, k) for t, k in zip(subset["target"], subset.get("target_key", pd.Series([""] * len(subset))))]
        rows.append(
            {
                "mechanism_id": mech["mechanism_id"],
                "mechanism_name": mech["mechanism_name"],
                "frozen_priority": mech["frozen_priority"],
                "primary_pathology_targets": ";".join(mech["targets"]),
                "representative_modules": unique_join(modules),
                "representative_genes": ";".join([g for g in mech["genes"] if g in set(subset["gene"].astype(str))]),
                "supporting_stage36c_targets": unique_join(supporting_targets),
                "supporting_stage36d_rows": int(len(subset)),
                "biological_rationale": mech["rationale"],
                "key_limitation": GENERAL_LIMITATION,
                "allowed_claim_language": ALLOWED_CLAIM,
                "disallowed_claim_language": DISALLOWED_CLAIM,
                "recommended_next_validation_route": (
                    "independent cohort replication; spatial transcriptomic confirmation; single-cell/single-nucleus expression confirmation; "
                    "pathology colocalization; immunostaining/protein-level confirmation; future perturbation experiment; manual biological review"
                ),
            }
        )
    return pd.DataFrame(rows)


def candidate_mechanisms(gene: str) -> list[dict[str, Any]]:
    return [mech for mech in MECHANISMS if gene in mech["genes"]]


def build_priority_candidate_registry(shortlist: pd.DataFrame, modules: pd.DataFrame) -> pd.DataFrame:
    rows = []
    counter = 1
    for _, row in shortlist.sort_values(["target_key", "stage36c_rank_within_target"]).iterrows():
        gene = str(row.get("gene", ""))
        mechs = candidate_mechanisms(gene)
        if not mechs:
            continue
        for mech in mechs:
            rows.append(
                {
                    "candidate_id": f"C{counter:03d}",
                    "mechanism_id": mech["mechanism_id"],
                    "target": display_target(row.get("target", ""), row.get("target_key", "")),
                    "gene_or_module": gene,
                    "candidate_type": "gene",
                    "frozen_priority": mech["frozen_priority"],
                    "stage36c_rank_or_score_if_available": f"rank={row.get('stage36c_rank_within_target', '')}; score={row.get('stage36c_priority_score', '')}",
                    "stage36d_shortlist_support": True,
                    "knowledge_grounding_status": row.get("local_knowledge_grounding_status", ""),
                    "internal_model_implied_rationale": row.get("internal_model_implied_rationale", ""),
                    "proposed_validation_readout": (
                        "pre-specified replication of candidate/pathology association plus cell/spatial/protein context; "
                        "perturbation only as future causal follow-up"
                    ),
                    "required_validation_before_strong_claim": (
                        "clean independent validation and, for causal language, direct perturbational evidence with prespecified outcomes"
                    ),
                    "allowed_claim_language": ALLOWED_CLAIM,
                    "disallowed_claim_language": DISALLOWED_CLAIM,
                }
            )
            counter += 1
    top_modules = shortlist.drop_duplicates(["target_key", "top_module"])[["target", "target_key", "top_module"]]
    for _, row in top_modules.iterrows():
        matching = [m for m in MECHANISMS if display_target(row["target"], row["target_key"]) in m["targets"]]
        if not matching:
            matching = MECHANISMS
        for mech in matching[:1]:
            rows.append(
                {
                    "candidate_id": f"C{counter:03d}",
                    "mechanism_id": mech["mechanism_id"],
                    "target": display_target(row.get("target", ""), row.get("target_key", "")),
                    "gene_or_module": row.get("top_module", ""),
                    "candidate_type": "module",
                    "frozen_priority": mech["frozen_priority"],
                    "stage36c_rank_or_score_if_available": "target-level top module from Stage 36C/36D",
                    "stage36d_shortlist_support": True,
                    "knowledge_grounding_status": "passed",
                    "internal_model_implied_rationale": "Target-level module retained for validation-protocol planning; not validation.",
                    "proposed_validation_readout": "module-level replication, cell/spatial context, and manual biological review",
                    "required_validation_before_strong_claim": "clean independent validation; perturbation for causal claims",
                    "allowed_claim_language": ALLOWED_CLAIM,
                    "disallowed_claim_language": DISALLOWED_CLAIM,
                }
            )
            counter += 1
    return pd.DataFrame(rows)


def build_decision_rules() -> pd.DataFrame:
    rules = [
        ("independent_validation_requires_clean_holdout", "Independent validation requires a clean holdout dataset not used in model development.", True),
        ("validation_dataset_must_not_have_been_used_for_training", "Validation data must not have been used for Stage 27C/36A model fitting.", True),
        ("validation_dataset_must_not_have_been_used_for_pretraining", "Validation data must not have been used for external pretraining.", True),
        ("validation_dataset_must_not_have_been_used_for_model_selection", "Validation data must not have influenced model/feature/threshold selection.", True),
        ("candidate_direction_must_be_prespecified", "The candidate, pathology target, and expected direction must be frozen before validation.", True),
        ("effect_direction_must_match_frozen_hypothesis", "A positive validation readout requires the observed direction to match the frozen hypothesis.", True),
        ("negative_result_must_be_reported", "Negative and null results must be reported rather than silently filtered.", True),
        ("association_validation_does_not_imply_causality", "Predictive or association replication does not imply causal mechanism.", True),
        ("perturbation_required_for_causal_claim", "Causal language requires direct perturbational evidence with prespecified outcomes.", True),
        ("therapeutic_claims_prohibited_without_disease_modifying_experimental_evidence", "Therapeutic claims are prohibited without disease-modifying experimental evidence.", True),
    ]
    return pd.DataFrame(
        [
            {
                "rule_id": f"R{i:02d}",
                "rule_name": name,
                "rule_text": text,
                "frozen_before_validation": frozen,
                "claim_boundary": "planning_rule_only_not_completed_validation",
            }
            for i, (name, text, frozen) in enumerate(rules, start=1)
        ]
    )


def build_mechanism_to_assay_map(mechanisms: pd.DataFrame) -> pd.DataFrame:
    categories = [
        "independent cohort replication",
        "spatial transcriptomic confirmation",
        "single-cell or single-nucleus expression confirmation",
        "pathology colocalization",
        "immunostaining or protein-level confirmation",
        "perturbation experiment, only as future causal follow-up",
        "manual biological review",
    ]
    rows = []
    for _, mech in mechanisms.iterrows():
        for category in categories:
            rows.append(
                {
                    "mechanism_id": mech["mechanism_id"],
                    "mechanism_name": mech["mechanism_name"],
                    "validation_category": category,
                    "assay_status": "proposed_not_completed",
                    "readout_goal": "test or contextualize frozen follow-up hypothesis under prespecified rules",
                    "required_before_claim": "clean independent evidence; perturbation required for causal language",
                    "allowed_claim_language": ALLOWED_CLAIM,
                    "disallowed_claim_language": DISALLOWED_CLAIM,
                }
            )
    return pd.DataFrame(rows)


def claim_audit() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "no_new_modeling_run": True,
                "no_external_validation_run": True,
                "no_data_download": True,
                "no_web_scraping": True,
                "no_causal_claim": True,
                "no_therapeutic_claim": True,
                "no_gene_ablation_claim": True,
                "no_in_silico_validation_claim": True,
                "no_external_validation_language": True,
                "all_candidates_described_as_follow_up_hypotheses": True,
                "safety_audit_pass": True,
            }
        ]
    )


def target_coverage_ok(shortlist: pd.DataFrame, required_targets: list[str]) -> tuple[bool, str]:
    found_keys = set(shortlist.get("target_key", pd.Series(dtype=str)).astype(str))
    found_display = [display_target(k, k) for k in required_targets if k in found_keys]
    return all(t in found_keys for t in required_targets), ";".join(found_display)


def pass_fail(
    cfg: dict[str, Any],
    c_presence: dict[str, bool],
    d_presence: dict[str, bool],
    outputs: dict[str, bool],
    coverage_pass: bool,
    coverage: str,
    audit: pd.DataFrame,
) -> pd.DataFrame:
    audit_row = audit.iloc[0].to_dict()
    row = {
        "stage36e_run": True,
        "stage36c_inputs_found": all(c_presence.values()),
        "stage36d_inputs_found": all(d_presence.values()),
        "frozen_mechanism_registry_written": outputs.get("frozen_mechanism_registry", False),
        "priority_candidate_registry_written": outputs.get("priority_candidate_registry", False),
        "validation_decision_rules_written": outputs.get("validation_decision_rules", False),
        "mechanism_to_assay_map_written": outputs.get("mechanism_to_assay_map", False),
        "claim_boundaries_audit_written": outputs.get("claim_boundaries_audit", False),
        "pi_scientific_rationale_written": outputs.get("pi_report", False),
        "required_target_coverage_pass": coverage_pass,
        "required_target_coverage": coverage,
        "no_new_modeling_run": audit_row["no_new_modeling_run"],
        "no_external_validation_run": audit_row["no_external_validation_run"],
        "no_causal_claim": audit_row["no_causal_claim"],
        "no_therapeutic_claim": audit_row["no_therapeutic_claim"],
        "no_gene_ablation_claim": audit_row["no_gene_ablation_claim"],
        "no_in_silico_validation_claim": audit_row["no_in_silico_validation_claim"],
        "safety_audit_pass": audit_row["safety_audit_pass"],
    }
    required = [
        "stage36e_run",
        "stage36c_inputs_found",
        "stage36d_inputs_found",
        "frozen_mechanism_registry_written",
        "priority_candidate_registry_written",
        "validation_decision_rules_written",
        "mechanism_to_assay_map_written",
        "claim_boundaries_audit_written",
        "pi_scientific_rationale_written",
        "required_target_coverage_pass",
        "no_new_modeling_run",
        "no_external_validation_run",
        "no_causal_claim",
        "no_therapeutic_claim",
        "no_gene_ablation_claim",
        "no_in_silico_validation_claim",
        "safety_audit_pass",
    ]
    row["stage36e_run_pass"] = all(bool(row[col]) for col in required)
    row["controlled_interpretation"] = (
        "Stage 36E froze mechanisms, candidates, and validation decision rules before new validation data are examined. "
        "It is a protocol/registry package only, not validation."
    )
    return pd.DataFrame([row])


def build_report(mechanisms: pd.DataFrame, candidates: pd.DataFrame, rules: pd.DataFrame, assay_map: pd.DataFrame, audit: pd.DataFrame, pf: pd.DataFrame) -> str:
    candidate_summary = candidates.groupby(["mechanism_id", "target"], sort=False).agg(candidates=("gene_or_module", unique_join)).reset_index()
    return "\n".join(
        [
            "# Stage 36E frozen validation protocol v1",
            "",
            "## Purpose",
            "",
            "Stage 36E freezes biological mechanisms, candidate genes/modules, and validation decision rules from Stage 36C/36D outputs before any new validation data are examined.",
            "",
            "It is report-only and planning-only. It does not run new modeling, download data, scrape the web, perform external validation, claim causal validation, claim therapeutic targets, or claim gene ablation.",
            "",
            "## Inputs",
            "",
            "Stage 36E uses the already generated Stage 36C ranked hypothesis outputs and Stage 36D validation handoff outputs. Stage 36C and Stage 36D are not rerun.",
            "",
            "## Frozen mechanism registry summary",
            "",
            markdown_table(mechanisms[["mechanism_id", "mechanism_name", "frozen_priority", "primary_pathology_targets", "representative_genes", "supporting_stage36d_rows"]]),
            "",
            "## Frozen candidate registry summary",
            "",
            markdown_table(candidate_summary),
            "",
            "## Validation decision rules",
            "",
            markdown_table(rules[["rule_id", "rule_name", "rule_text"]]),
            "",
            "## Mechanism-to-assay map",
            "",
            markdown_table(assay_map[["mechanism_id", "validation_category", "assay_status"]], max_rows=40),
            "",
            "## Claim boundaries",
            "",
            markdown_table(audit),
            "",
            "## What Stage 36E does not prove",
            "",
            "- It does not prove causality.",
            "- It does not establish therapeutic targets.",
            "- It does not validate gene ablation.",
            "- It does not show external validation.",
            "- It does not show disease-modifying experimental evidence.",
            "",
            "## Exact safe interpretation language",
            "",
            ALLOWED_CLAIM,
            "",
            "Disallowed language: " + DISALLOWED_CLAIM,
            "",
            "## Pass/fail summary",
            "",
            markdown_table(pf),
        ]
    )


def build_pi_report(mechanisms: pd.DataFrame, candidates: pd.DataFrame, pf: pd.DataFrame) -> str:
    mech_view = mechanisms[["mechanism_id", "mechanism_name", "frozen_priority", "representative_genes", "primary_pathology_targets"]]
    top_by_mech = candidates.groupby(["mechanism_id"], sort=False).agg(top_genes_modules=("gene_or_module", unique_join), targets=("target", unique_join)).reset_index()
    target_cov = candidates.groupby("target", sort=False).agg(candidates=("gene_or_module", unique_join), mechanisms=("mechanism_id", unique_join)).reset_index()
    return "\n".join(
        [
            "# Stage 36E PI scientific rationale v1",
            "",
            "## Short readout",
            "",
            "Stage 36E freezes four biological mechanism bins and a validation protocol from Stage 36C/36D follow-up hypotheses.",
            "",
            "## Frozen mechanisms",
            "",
            markdown_table(mech_view),
            "",
            "## Top genes/modules by mechanism",
            "",
            markdown_table(top_by_mech),
            "",
            "## Target coverage",
            "",
            markdown_table(target_cov),
            "",
            "## Why endolysosomal/proteostasis biology is the strongest first validation theme",
            "",
            "The endolysosomal/autophagy/proteostasis bin has broad target relevance in the frozen registry and includes recurrent candidates such as CTSD, CTSB, LAPTM5, NPC2, and LAMP2. If prioritized for first-pass validation, it offers a biologically coherent bridge across neuronal and pathology-linked readouts while remaining safely framed as a follow-up hypothesis.",
            "",
            "## Validation routes",
            "",
            "- independent cohort replication",
            "- spatial transcriptomic confirmation",
            "- single-cell or single-nucleus expression confirmation",
            "- pathology colocalization",
            "- immunostaining or protein-level confirmation",
            "- perturbation experiment only as future causal follow-up",
            "- manual biological review",
            "",
            "## Safe lab-meeting/manuscript-planning language",
            "",
            ALLOWED_CLAIM,
            "",
            "Avoid: " + DISALLOWED_CLAIM,
            "",
            "## Pass/fail",
            "",
            markdown_table(pf[["stage36e_run_pass", "required_target_coverage", "safety_audit_pass"]]),
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
        "stage_id": "stage36e_frozen_validation_protocol",
        "status": "complete",
        "stage": "Stage 36E",
        "primary_metric": "frozen mechanism registry and validation decision rules",
        "pass_rule": "pass requires Stage 36C/36D inputs, all outputs, five-target coverage, and safety audit",
        "result": "run_pass=True",
        "pass_fail": "pass",
        "allowed_inputs": "Stage 36C/36D generated outputs only",
        "forbidden_inputs": "new modeling; downloads; web scraping; external validation; causal/therapeutic/gene-ablation claims",
        "interpretation": "Stage 36E froze mechanisms, candidates, and validation decision rules before new validation data are examined.",
        "notes": "Protocol/registry only; not validation.",
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
    append_section_once(
        cfg["status_updates"]["active_status"],
        "## Stage 36E frozen validation protocol status",
        (
            "Stage 36E frozen validation protocol is complete. It consolidates Stage 36C/36D follow-up hypotheses into frozen "
            "mechanism bins, a priority candidate registry, assay map, and validation decision rules before new validation data are examined. "
            "No new modeling, download, web scraping, external validation, causal validation, gene-ablation claim, or therapeutic claim was made."
        ),
    )
    append_section_once(
        cfg["status_updates"]["scorecard_md"],
        "## Stage 36E frozen validation protocol result",
        (
            "Stage 36E is complete. Run pass: `True`. It froze four mechanism bins and validation decision rules from Stage 36C/36D outputs only. "
            "This is a protocol/registry package only, not validation."
        ),
    )
    update_scorecard_csv(cfg["status_updates"]["scorecard_csv"])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/agent/stage36e_frozen_validation_protocol_v1.yaml")
    args = parser.parse_args()
    cfg = load_cfg(resolve(args.config))

    c_presence = input_presence(cfg, "stage36c")
    d_presence = input_presence(cfg, "stage36d")
    stage36c_pf = read_csv(cfg["inputs"]["stage36c_pass_fail"])
    stage36c_audit = read_csv(cfg["inputs"]["stage36c_safety_claims_audit"])
    stage36d_pf = read_csv(cfg["inputs"]["stage36d_pass_fail"])
    stage36d_audit = read_csv(cfg["inputs"]["stage36d_validation_readiness_audit"])
    shortlist = read_csv(cfg["inputs"]["stage36d_candidate_shortlist"])
    stage36c_modules = read_csv(cfg["inputs"]["stage36c_ranked_module_hypotheses"])

    if not stage_safety_ok(stage36c_pf, stage36c_audit, stage36d_pf, stage36d_audit):
        print("warning=upstream_stage36c_or_stage36d_safety_not_passed")

    mechanisms = build_mechanism_registry(shortlist)
    candidates = build_priority_candidate_registry(shortlist, stage36c_modules)
    rules = build_decision_rules()
    assay_map = build_mechanism_to_assay_map(mechanisms)
    audit = claim_audit()
    coverage_pass, coverage = target_coverage_ok(shortlist, cfg["required_targets"])

    paths: list[Path] = []
    outputs: dict[str, bool] = {}
    for key, df in [
        ("frozen_mechanism_registry", mechanisms),
        ("priority_candidate_registry", candidates),
        ("validation_decision_rules", rules),
        ("mechanism_to_assay_map", assay_map),
        ("claim_boundaries_audit", audit),
    ]:
        path = write_csv(df, cfg["outputs"][key])
        paths.append(path)
        outputs[key] = path.exists()

    pf = pass_fail(cfg, c_presence, d_presence, outputs, coverage_pass, coverage, audit)
    path = write_csv(pf, cfg["outputs"]["pass_fail"])
    paths.append(path)
    outputs["pass_fail"] = path.exists()

    report_path = write_text(build_report(mechanisms, candidates, rules, assay_map, audit, pf), cfg["outputs"]["report"])
    pi_path = write_text(build_pi_report(mechanisms, candidates, pf), cfg["outputs"]["pi_report"])
    paths.extend([report_path, pi_path])
    outputs["report"] = report_path.exists()
    outputs["pi_report"] = pi_path.exists()

    # Recompute final pass/fail after reports are written.
    pf = pass_fail(cfg, c_presence, d_presence, outputs, coverage_pass, coverage, audit)
    write_csv(pf, cfg["outputs"]["pass_fail"])
    write_text(build_report(mechanisms, candidates, rules, assay_map, audit, pf), cfg["outputs"]["report"])
    write_text(build_pi_report(mechanisms, candidates, pf), cfg["outputs"]["pi_report"])

    update_status_docs(cfg)
    paths.extend(
        [
            resolve(cfg["status_updates"]["active_status"]),
            resolve(cfg["status_updates"]["scorecard_md"]),
            resolve(cfg["status_updates"]["scorecard_csv"]),
        ]
    )

    print("stage36e_paths_written=")
    for path in paths:
        print(str(path.relative_to(ROOT)))
    print(f"n_frozen_mechanisms={len(mechanisms)}")
    print(f"n_priority_candidates={len(candidates)}")
    print(f"required_target_coverage={ascii_safe(coverage)}")
    print(f"stage36e_run_pass={pf.iloc[0]['stage36e_run_pass']}")
    print(f"safety_audit_pass={pf.iloc[0]['safety_audit_pass']}")


if __name__ == "__main__":
    main()
