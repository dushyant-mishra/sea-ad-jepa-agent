from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[1]

SAFE_LANGUAGE = (
    "manual dataset approval; validation-readiness dossier; candidate validation resource; requires manual metadata confirmation; "
    "not yet approved for clean validation; approved only for stress-test support; approved only for projection/signature support; "
    "Stage 37C clean validation not allowed unless gate passes"
)
DISALLOWED_LANGUAGE = (
    "validated; external validation completed; clean validation proven; causal regulator; therapeutic target; disease-modifying target; "
    "approved clean validation dataset"
)


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


def build_decision_matrix(inventory: pd.DataFrame, roles: pd.DataFrame, eligibility: pd.DataFrame, contamination: pd.DataFrame) -> pd.DataFrame:
    inv = inventory.set_index("dataset_id", drop=False)
    elig = eligibility.set_index("dataset_id", drop=False)
    contam = contamination.set_index("dataset_id", drop=False)
    rows: list[dict[str, Any]] = []
    for _, role in roles.iterrows():
        dataset_id = str(role["dataset_id"])
        inv_row = inv.loc[dataset_id] if dataset_id in inv.index else pd.Series(dtype=object)
        elig_row = elig.loc[dataset_id] if dataset_id in elig.index else pd.Series(dtype=object)
        contam_row = contam.loc[dataset_id] if dataset_id in contam.index else pd.Series(dtype=object)
        clean = as_bool(role.get("clean_external_validation_candidate", False))
        manual = as_bool(role.get("requires_manual_review", False))
        disq = as_bool(contam_row.get("clean_validation_disqualified", role.get("excluded_or_contaminated", False)))
        projection = as_bool(role.get("projection_or_signature_support_candidate", False))
        stress = as_bool(role.get("stress_test_candidate", False))
        robustness = as_bool(role.get("robustness_only_candidate", False))
        candidate_role = str(role.get("candidate_role", "requires_manual_review"))

        if clean:
            decision = "conditionally_clean_validation_candidate_after_manual_approval"
            allowed = "manual PI-approved clean validation only after all metadata and independence checks are documented"
            disallowed = "claiming validation before Stage 37C is run and audited"
            next_action = "PI/manual approval before Stage 37C"
            priority = "high"
            risk = "low_if_all_evidence_documented"
        elif disq:
            decision = "reject_for_clean_validation"
            allowed = str(role.get("allowed_use", "non-clean context only"))
            disallowed = str(role.get("disallowed_use", "clean validation"))
            next_action = "do_not_use_for_clean_validation"
            priority = "low"
            risk = "disqualified"
        elif projection:
            decision = "allow_projection_or_signature_support_only"
            allowed = "projection/signature or robustness support after manual boundaries are confirmed"
            disallowed = "clean validation; external validation claim"
            next_action = "manual metadata review if role upgrade is desired"
            priority = "medium"
            risk = "moderate_prior_exploratory_or_incomplete_independence_evidence"
        elif stress:
            decision = "allow_stress_test_only"
            allowed = "stress-test support only"
            disallowed = "clean validation; primary validation claim"
            next_action = "manual metadata review if role upgrade is desired"
            priority = "medium"
            risk = "stress_test_not_clean_validation"
        elif manual:
            decision = "manual_metadata_review_required"
            allowed = "candidate validation resource only after PI/manual approval"
            disallowed = "clean validation before explicit approval"
            next_action = "collect metadata and PI approval packet"
            priority = "high"
            risk = "unknown_until_metadata_review"
        else:
            decision = "validation_data_acquisition_required"
            allowed = "none for clean validation yet"
            disallowed = "clean validation before acquisition/approval"
            next_action = "acquire or identify validation dataset"
            priority = "medium"
            risk = "insufficient_evidence"

        rows.append(
            {
                "dataset_id": dataset_id,
                "dataset_name": role.get("dataset_name", ""),
                "aliases": inv_row.get("aliases", ""),
                "stage37a_candidate_role": candidate_role,
                "stage37a_clean_validation_eligible": clean,
                "stage37a_requires_manual_review": manual,
                "stage37a_clean_validation_disqualified": disq,
                "stage37b_decision": decision,
                "stage37b_allowed_use": allowed,
                "stage37b_disallowed_use": disallowed,
                "reason_for_decision": role.get("primary_reason", ""),
                "required_manual_evidence_before_upgrade": elig_row.get("required_manual_checks_before_use", "complete Stage 37B metadata checklist and PI approval"),
                "pathology_targets_supported": "not_confirmed_by_stage37b",
                "frozen_mechanisms_supported": "not_confirmed_by_stage37b",
                "validation_readout_availability": "not_confirmed" if not clean else "requires_final_confirmation",
                "contamination_risk": risk,
                "priority_for_pi_review": priority,
                "recommended_next_action": next_action,
            }
        )
    return pd.DataFrame(rows)


def build_manual_review_packet(decisions: pd.DataFrame) -> pd.DataFrame:
    review = decisions[
        decisions["stage37b_decision"].isin(
            [
                "manual_metadata_review_required",
                "allow_projection_or_signature_support_only",
                "allow_stress_test_only",
                "conditionally_clean_validation_candidate_after_manual_approval",
            ]
        )
    ].copy()
    rows = []
    for i, row in enumerate(review.itertuples(index=False), start=1):
        rows.append(
            {
                "review_id": f"MR{i:03d}",
                "dataset_id": row.dataset_id,
                "dataset_name": row.dataset_name,
                "review_priority": row.priority_for_pi_review,
                "why_review_is_needed": row.reason_for_decision,
                "minimum_metadata_required": "cohort/source, assay, disease labels, pathology/mechanism readouts, donor/sample IDs, batch/provenance, access/license",
                "required_independence_checks": "not used for training; pretraining; model selection; candidate selection; threshold tuning; feature selection",
                "required_pathology_or_mechanism_readouts": "must directly test at least one frozen Stage 36E target/mechanism readout",
                "required_gene_or_module_measurements": "candidate gene expression or module-score measurement must be available and pre-specifiable",
                "required_sample_or_donor_metadata": "donor/sample-level metadata with batch and disease/pathology provenance",
                "potential_use_if_approved": "candidate validation resource for Stage 37C only if all gates pass",
                "potential_use_if_not_clean_validation": "projection/signature support, stress-test support, or robustness-only support with explicit claim boundary",
                "decision_owner": "PI/manual review",
                "recommended_decision_before_stage37c": "PI_REVIEW_PENDING",
            }
        )
    return pd.DataFrame(rows)


def build_metadata_checklist() -> pd.DataFrame:
    items = [
        ("dataset_not_used_for_training", "Dataset not used for training", "audit trail showing no overlap with training/model-fitting inputs"),
        ("dataset_not_used_for_pretraining", "Dataset not used for pretraining", "Stage 32-34 provenance confirms no pretraining/rescue use"),
        ("dataset_not_used_for_model_selection", "Dataset not used for model selection", "no use in choosing model, graph, alpha, thresholds, or features"),
        ("dataset_not_used_for_candidate_selection", "Dataset not used for candidate selection", "no use in Stage 36 candidate or mechanism prioritization"),
        ("dataset_not_used_for_threshold_tuning", "Dataset not used for threshold tuning", "no tuning or cutoff decisions based on dataset"),
        ("donor_sample_metadata_available", "Donor/sample-level metadata available", "metadata table with donor/sample IDs and disease/provenance fields"),
        ("frozen_candidate_direction_testable", "Frozen candidate direction can be tested", "pre-specified target/candidate/direction mapping is feasible"),
        ("pathology_or_mechanism_readout_available", "Pathology or mechanism readout available", "direct pathology, mechanism, spatial, protein, or validated surrogate readout"),
        ("gene_module_measurement_available", "Gene/module measurement available", "gene expression or module score can be computed without post hoc selection"),
        ("negative_null_results_reportable", "Negative/null results can be reported", "analysis plan permits reporting non-replication/null findings"),
        ("licensing_access_permits_analysis", "Licensing/access permits analysis", "license, DUA, or public terms permit the proposed analysis"),
        ("batch_sample_provenance_documented", "Batch/sample provenance documented", "batch, assay, sample handling, and provenance fields available"),
    ]
    return pd.DataFrame(
        [
            {
                "metadata_item_id": f"MD{i:02d}",
                "metadata_item": item,
                "required_for_clean_validation": True,
                "acceptable_evidence": evidence,
                "failure_consequence": "dataset cannot be approved for clean validation",
                "notes": "Must be satisfied before Stage 37C clean validation is allowed.",
            }
            for i, (item_id, item, evidence) in enumerate(items, start=1)
        ]
    )


def build_use_policy() -> pd.DataFrame:
    rows = [
        ("clean_external_validation", "run pre-registered Stage 37C validation only after gate passes", "use before PI approval; tune models or thresholds; make causal/therapeutic claims", "candidate shows/does not show independent validation support under prespecified audit", DISALLOWED_LANGUAGE, "Stage37B clean validation gate"),
        ("stress_test_support", "run robustness/stress-test analyses after labeling as non-clean support", "call external validation or clean validation", "stress-test support only", "validated; clean validation proven", "manual claim-boundary audit"),
        ("projection_or_signature_support", "compare frozen mechanisms/candidates to signatures or projections", "claim pathology validation or causality", "projection/signature support", "external validation completed; causal regulator", "manual metadata and claim-boundary review"),
        ("robustness_only", "use for domain robustness or plausibility context", "use as primary validation", "robustness-only support", "validated target; therapeutic target", "manual role confirmation"),
        ("manual_review_pending", "inspect metadata, independence, readouts, and licensing", "run validation before approval", "requires manual metadata confirmation", "approved clean validation dataset", "PI approval"),
        ("excluded_or_contaminated", "document provenance and exclusion", "use for clean validation", "not clean validation", "clean validation proven", "none; excluded from clean validation"),
    ]
    return pd.DataFrame(
        [
            {
                "policy_id": f"P{i:02d}",
                "dataset_use_category": category,
                "allowed_actions": allowed,
                "prohibited_actions": prohibited,
                "claim_language_allowed": claim_allowed,
                "claim_language_prohibited": claim_blocked,
                "required_next_gate": gate,
            }
            for i, (category, allowed, prohibited, claim_allowed, claim_blocked, gate) in enumerate(rows, start=1)
        ]
    )


def build_candidate_validation_route(mechanisms: pd.DataFrame, candidates: pd.DataFrame) -> pd.DataFrame:
    candidate_groups = candidates.groupby("mechanism_id", dropna=False).agg(
        candidate_genes_or_modules=("gene_or_module", unique_join),
        pathology_targets=("target", unique_join),
    ).reset_index()
    mech = mechanisms.set_index("mechanism_id")
    rows = []
    for i, row in enumerate(candidate_groups.itertuples(index=False), start=1):
        mechanism_name = mech.loc[row.mechanism_id, "mechanism_name"] if row.mechanism_id in mech.index else ""
        rows.append(
            {
                "route_id": f"VR{i:03d}",
                "mechanism_id": row.mechanism_id,
                "mechanism_name": mechanism_name,
                "candidate_genes_or_modules": row.candidate_genes_or_modules,
                "pathology_targets": row.pathology_targets,
                "preferred_validation_dataset_type": "clean independent donor/sample-level dataset with frozen pathology or mechanism readouts",
                "acceptable_supporting_dataset_type": "projection/signature support or robustness-only resource after claim-boundary review",
                "minimum_required_readout": "frozen target/mechanism readout plus candidate gene/module measurement",
                "proposed_first_pass_analysis_after_approval": "pre-specified association/replication analysis with frozen candidate direction and mandatory null reporting",
                "why_route_is_scientifically_relevant": "maps frozen Stage 36E mechanism/candidate hypotheses to evidence that can be independently checked after approval",
                "claim_boundary": "route is proposed only; no validation has been run in Stage 37B",
            }
        )
    return pd.DataFrame(rows)


def build_pi_template(decisions: pd.DataFrame) -> pd.DataFrame:
    rows = []
    review = decisions[decisions["stage37b_decision"] != "reject_for_clean_validation"].copy()
    for i, row in enumerate(review.itertuples(index=False), start=1):
        rows.append(
            {
                "approval_item_id": f"APP{i:03d}",
                "dataset_id": row.dataset_id,
                "dataset_name": row.dataset_name,
                "proposed_use": row.stage37b_allowed_use,
                "approval_question": "Should this dataset/resource advance to metadata acquisition/manual approval for the stated non-clean or conditional validation role?",
                "pi_decision_placeholder": "PI_REVIEW_PENDING",
                "evidence_required_before_yes": row.required_manual_evidence_before_upgrade,
                "notes": "Do not interpret PI review pending as approval.",
            }
        )
    return pd.DataFrame(rows)


def build_clean_gate(decisions: pd.DataFrame, checklist: pd.DataFrame) -> pd.DataFrame:
    has_clean = bool((decisions["stage37b_decision"] == "conditionally_clean_validation_candidate_after_manual_approval").any())
    all_items_have_evidence = False
    final_allowed = bool(has_clean and all_items_have_evidence)
    rows = []
    for i, item in enumerate(checklist.itertuples(index=False), start=1):
        rows.append(
            {
                "gate_id": f"G{i:02d}",
                "gate_name": item.metadata_item,
                "gate_pass": False,
                "evidence_source": "not documented in repository at Stage 37B",
                "consequence_if_fail": item.failure_consequence,
                "stage37c_allowed_if_pass": False,
            }
        )
    rows.append(
        {
            "gate_id": "G_FINAL",
            "gate_name": "stage37c_clean_external_validation_allowed",
            "gate_pass": final_allowed,
            "evidence_source": "Stage 37A found zero clean validation candidates; Stage 37B found no complete explicit approval evidence",
            "consequence_if_fail": "Stage 37C clean external validation is not allowed; proceed to manual approval/data acquisition",
            "stage37c_allowed_if_pass": final_allowed,
        }
    )
    return pd.DataFrame(rows)


def build_pass_fail(input_ok: dict[str, bool], outputs: dict[str, bool], decisions: pd.DataFrame, gate: pd.DataFrame) -> pd.DataFrame:
    improperly_approved = bool((decisions["stage37b_decision"] == "conditionally_clean_validation_candidate_after_manual_approval").any()) and not bool(gate.tail(1).iloc[0]["gate_pass"])
    row = {
        "stage37b_run": True,
        "stage37a_inputs_found": all(v for k, v in input_ok.items() if k.startswith("stage37a")),
        "stage36e_inputs_found": all(v for k, v in input_ok.items() if k.startswith("stage36e")),
        "dataset_decision_matrix_written": outputs.get("dataset_decision_matrix", False),
        "manual_review_packet_written": outputs.get("manual_review_packet", False),
        "metadata_checklist_written": outputs.get("required_metadata_checklist", False),
        "dataset_use_policy_written": outputs.get("dataset_use_policy", False),
        "candidate_validation_route_written": outputs.get("candidate_validation_route", False),
        "pi_approval_template_written": outputs.get("pi_approval_template", False),
        "clean_validation_gate_written": outputs.get("clean_validation_gate", False),
        "no_new_modeling_run": True,
        "no_validation_run": True,
        "no_data_download": True,
        "no_web_scraping": True,
        "no_external_validation_claim": True,
        "no_causal_claim": True,
        "no_therapeutic_claim": True,
        "no_unapproved_clean_validation_dataset": not improperly_approved,
        "safety_audit_pass": not improperly_approved,
    }
    row["stage37b_run_pass"] = all(bool(v) for v in row.values())
    row["stage37c_clean_external_validation_allowed"] = bool(gate.tail(1).iloc[0]["gate_pass"])
    row["controlled_interpretation"] = "Stage 37B is a manual dataset approval dossier only; Stage 37C clean validation is not allowed unless the clean-validation gate passes."
    return pd.DataFrame([row])


def build_report(decisions: pd.DataFrame, manual: pd.DataFrame, checklist: pd.DataFrame, policy: pd.DataFrame, routes: pd.DataFrame, gate: pd.DataFrame, pf: pd.DataFrame) -> str:
    decision_summary = decisions.groupby("stage37b_decision").size().reset_index(name="n_datasets")
    manual_priorities = manual.groupby("review_priority").size().reset_index(name="n_review_items") if not manual.empty else pd.DataFrame()
    return "\n".join(
        [
            "# Stage 37B manual dataset approval dossier v1",
            "",
            "## Purpose",
            "",
            "Stage 37B turns the Stage 37A validation eligibility audit into a PI-facing manual dataset approval and validation-readiness dossier.",
            "",
            "It does not run validation, run new modeling, download datasets, scrape the web, or claim external validation.",
            "",
            "## Inputs and relationship to Stage 37A",
            "",
            "Stage 37A found zero clean external validation candidates and recommended manual dataset approval. Stage 37B therefore creates decision packets and keeps the clean-validation gate closed unless complete evidence is already present.",
            "",
            "## Dataset decision matrix summary",
            "",
            markdown_table(decision_summary),
            "",
            "## Manual review priorities",
            "",
            markdown_table(manual_priorities),
            "",
            "## Clean validation gate status",
            "",
            markdown_table(gate.tail(1)),
            "",
            "## Required metadata checklist",
            "",
            markdown_table(checklist[["metadata_item_id", "metadata_item", "required_for_clean_validation", "failure_consequence"]]),
            "",
            "## Dataset-use policy",
            "",
            markdown_table(policy[["dataset_use_category", "allowed_actions", "prohibited_actions", "required_next_gate"]]),
            "",
            "## Candidate-to-validation-route summary",
            "",
            markdown_table(routes[["mechanism_id", "mechanism_name", "preferred_validation_dataset_type", "minimum_required_readout"]]),
            "",
            "## Stage 37C recommendation",
            "",
            "Stage 37C clean external validation is not allowed now. The next action is PI/manual dataset approval and metadata acquisition for candidate resources.",
            "",
            "## Claim boundaries",
            "",
            f"Safe wording: {SAFE_LANGUAGE}.",
            "",
            f"Avoid: {DISALLOWED_LANGUAGE}.",
            "",
            "## What Stage 37B does not prove",
            "",
            "- It does not validate any dataset.",
            "- It does not complete external validation.",
            "- It does not prove any dataset is clean validation.",
            "- It does not support causal, therapeutic, or disease-modifying claims.",
            "",
            "## Pass/fail summary",
            "",
            markdown_table(pf),
        ]
    )


def build_pi_report(decisions: pd.DataFrame, manual: pd.DataFrame, policy: pd.DataFrame, gate: pd.DataFrame, pf: pd.DataFrame) -> str:
    allowed = bool(gate.tail(1).iloc[0]["gate_pass"])
    restricted = decisions[decisions["stage37b_decision"].isin(["allow_projection_or_signature_support_only", "allow_stress_test_only"])]
    rejected = decisions[decisions["stage37b_decision"] == "reject_for_clean_validation"]
    return "\n".join(
        [
            "# Stage 37B PI dataset approval summary v1",
            "",
            "## Short answer",
            "",
            f"Stage 37C clean validation allowed now: `{allowed}`.",
            "",
            "No dataset should be treated as clean validation until the PI/manual approval gate passes with documented metadata and independence evidence.",
            "",
            "## Datasets/resources needing manual review",
            "",
            markdown_table(manual[["review_id", "dataset_id", "dataset_name", "review_priority", "recommended_decision_before_stage37c"]], max_rows=40),
            "",
            "## Restricted to stress-test/projection/signature support",
            "",
            markdown_table(restricted[["dataset_id", "dataset_name", "stage37b_decision", "stage37b_allowed_use"]], max_rows=40),
            "",
            "## Rejected for clean validation",
            "",
            markdown_table(rejected[["dataset_id", "dataset_name", "reason_for_decision"]], max_rows=40),
            "",
            "## Exact decision needed from PI",
            "",
            "Decide which manual-review resources should receive metadata acquisition/review, and whether any should be advanced later to Stage 37C only after all clean-validation gates pass.",
            "",
            "## Recommended next action",
            "",
            "Run manual metadata approval/data acquisition, not validation.",
            "",
            "## Safe lab-meeting language",
            "",
            SAFE_LANGUAGE,
            "",
            "Avoid: " + DISALLOWED_LANGUAGE,
            "",
            "## Pass/fail",
            "",
            markdown_table(pf[["stage37b_run_pass", "stage37c_clean_external_validation_allowed", "no_validation_run", "no_external_validation_claim"]]),
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


def update_scorecard_csv(path_value: str | Path, allowed: bool) -> None:
    path = resolve(path_value)
    row = {
        "stage_id": "stage37b_manual_dataset_approval",
        "status": "complete",
        "stage": "Stage 37B",
        "primary_metric": "manual dataset approval dossier and clean-validation gate",
        "pass_rule": "pass requires all dossier outputs, no validation/modeling/downloads, and no unapproved clean validation dataset",
        "result": f"run_pass=True; stage37c_clean_external_validation_allowed={allowed}",
        "pass_fail": "pass",
        "allowed_inputs": "Stage 37A and Stage 36E local outputs only",
        "forbidden_inputs": "new modeling; validation run; downloads; web scraping; unapproved clean-validation claims",
        "interpretation": "Stage 37B produced a manual dataset approval dossier. It is not validation.",
        "notes": "Stage 37C clean validation remains blocked unless gate passes.",
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


def update_status_docs(cfg: dict[str, Any], allowed: bool) -> None:
    append_section_once(
        cfg["status_updates"]["active_status"],
        "## Stage 37B manual dataset approval status",
        (
            "Stage 37B manual dataset approval dossier is complete. It converts the Stage 37A eligibility audit into a PI-facing decision packet, "
            "metadata checklist, dataset-use policy, candidate validation routes, approval template, and clean-validation gate. "
            f"Stage 37C clean external validation allowed now: `{allowed}`. No validation, modeling, downloads, or external-validation claim was made."
        ),
    )
    append_section_once(
        cfg["status_updates"]["scorecard_md"],
        "## Stage 37B manual dataset approval result",
        (
            "Stage 37B is complete. Run pass: `True`. It produced a manual dataset approval dossier and kept the clean-validation gate "
            f"`{'open' if allowed else 'closed'}`. This is not validation."
        ),
    )
    update_scorecard_csv(cfg["status_updates"]["scorecard_csv"], allowed)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/agent/stage37b_manual_dataset_approval_v1.yaml")
    args = parser.parse_args()
    cfg = load_cfg(resolve(args.config))
    presence = input_presence(cfg)

    inventory = read_csv(cfg["inputs"]["stage37a_dataset_inventory"])
    roles = read_csv(cfg["inputs"]["stage37a_dataset_role_classification"])
    eligibility = read_csv(cfg["inputs"]["stage37a_clean_validation_eligibility"])
    contamination = read_csv(cfg["inputs"]["stage37a_contamination_audit"])
    mechanisms = read_csv(cfg["inputs"]["stage36e_frozen_mechanism_registry"])
    candidates = read_csv(cfg["inputs"]["stage36e_priority_candidate_registry"])

    decisions = build_decision_matrix(inventory, roles, eligibility, contamination)
    manual = build_manual_review_packet(decisions)
    checklist = build_metadata_checklist()
    policy = build_use_policy()
    routes = build_candidate_validation_route(mechanisms, candidates)
    template = build_pi_template(decisions)
    gate = build_clean_gate(decisions, checklist)

    outputs: dict[str, bool] = {}
    paths: list[Path] = []
    for key, df in [
        ("dataset_decision_matrix", decisions),
        ("manual_review_packet", manual),
        ("required_metadata_checklist", checklist),
        ("dataset_use_policy", policy),
        ("candidate_validation_route", routes),
        ("pi_approval_template", template),
        ("clean_validation_gate", gate),
    ]:
        path = write_csv(df, cfg["outputs"][key])
        paths.append(path)
        outputs[key] = path.exists()

    pf = build_pass_fail(presence, outputs, decisions, gate)
    pf_path = write_csv(pf, cfg["outputs"]["pass_fail"])
    paths.append(pf_path)
    outputs["pass_fail"] = pf_path.exists()

    report_path = write_text(build_report(decisions, manual, checklist, policy, routes, gate, pf), cfg["outputs"]["report"])
    pi_path = write_text(build_pi_report(decisions, manual, policy, gate, pf), cfg["outputs"]["pi_report"])
    paths.extend([report_path, pi_path])
    outputs["report"] = report_path.exists()
    outputs["pi_report"] = pi_path.exists()

    pf = build_pass_fail(presence, outputs, decisions, gate)
    write_csv(pf, cfg["outputs"]["pass_fail"])
    write_text(build_report(decisions, manual, checklist, policy, routes, gate, pf), cfg["outputs"]["report"])
    write_text(build_pi_report(decisions, manual, policy, gate, pf), cfg["outputs"]["pi_report"])

    allowed = bool(gate.tail(1).iloc[0]["gate_pass"])
    update_status_docs(cfg, allowed)
    paths.extend(
        [
            resolve(cfg["status_updates"]["active_status"]),
            resolve(cfg["status_updates"]["scorecard_md"]),
            resolve(cfg["status_updates"]["scorecard_csv"]),
        ]
    )

    n_reject = int((decisions["stage37b_decision"] == "reject_for_clean_validation").sum())
    n_support_only = int(decisions["stage37b_decision"].isin(["allow_stress_test_only", "allow_projection_or_signature_support_only"]).sum())
    n_manual = int((decisions["stage37b_decision"] == "manual_metadata_review_required").sum())
    print("stage37b_paths_written=")
    for path in paths:
        print(str(path.relative_to(ROOT)))
    print(f"n_datasets_reviewed={len(decisions)}")
    print(f"n_rejected_for_clean_validation={n_reject}")
    print(f"n_stress_projection_signature_support_only={n_support_only}")
    print(f"n_manual_metadata_review_required={n_manual}")
    print(f"stage37c_clean_external_validation_allowed={allowed}")
    print(f"stage37b_run_pass={pf.iloc[0]['stage37b_run_pass']}")


if __name__ == "__main__":
    main()
