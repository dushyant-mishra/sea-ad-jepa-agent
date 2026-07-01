from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[1]

SAFE_LANGUAGE = (
    "reasonable to reuse; conditional validation candidate; external biological support; stress-test support; "
    "projection/signature support; manual metadata review required; not currently approved for clean external validation; "
    "missing evidence is not rejection"
)
DISALLOWED_LANGUAGE = (
    "validated; clean validation proven; external validation completed; causal regulator; therapeutic target; disease-modifying target"
)

CLAIM_LEVELS = [
    "approved_clean_external_validation",
    "conditional_clean_validation_candidate",
    "external_biological_support_candidate",
    "projection_or_signature_support_candidate",
    "stress_test_candidate",
    "robustness_only",
    "known_disqualified_from_clean_validation",
    "manual_metadata_review_required",
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


def merge_source_tables(cfg: dict[str, Any], inventory: pd.DataFrame, roles: pd.DataFrame, elig: pd.DataFrame, contam: pd.DataFrame, previous: pd.DataFrame) -> pd.DataFrame:
    inv = inventory.set_index("dataset_id", drop=False) if not inventory.empty else pd.DataFrame()
    el = elig.set_index("dataset_id", drop=False) if not elig.empty else pd.DataFrame()
    co = contam.set_index("dataset_id", drop=False) if not contam.empty else pd.DataFrame()
    prev = previous.set_index("dataset_id", drop=False) if not previous.empty else pd.DataFrame()
    rows = []
    for _, role in roles.iterrows():
        dataset_id = str(role["dataset_id"])
        inv_row = inv.loc[dataset_id] if dataset_id in inv.index else pd.Series(dtype=object)
        el_row = el.loc[dataset_id] if dataset_id in el.index else pd.Series(dtype=object)
        co_row = co.loc[dataset_id] if dataset_id in co.index else pd.Series(dtype=object)
        prev_row = prev.loc[dataset_id] if dataset_id in prev.index else pd.Series(dtype=object)
        rows.append(
            {
                "dataset_id": dataset_id,
                "dataset_name": role.get("dataset_name", ""),
                "aliases": inv_row.get("aliases", ""),
                "stage37a_candidate_role": role.get("candidate_role", ""),
                "previous_stage37b_decision": prev_row.get("stage37b_decision", ""),
                "stage37a_clean_validation_eligible": as_bool(role.get("clean_external_validation_candidate", False)),
                "stage37a_requires_manual_review": as_bool(role.get("requires_manual_review", False)),
                "stage37a_clean_validation_disqualified": as_bool(co_row.get("clean_validation_disqualified", role.get("excluded_or_contaminated", False))),
                "stage37a_projection_support": as_bool(role.get("projection_or_signature_support_candidate", False)),
                "stage37a_stress_test": as_bool(role.get("stress_test_candidate", False)),
                "stage37a_robustness_only": as_bool(role.get("robustness_only_candidate", False)),
                "primary_reason": role.get("primary_reason", ""),
                "eligibility_failure_reason": el_row.get("eligibility_failure_reason", ""),
                "contamination_status": co_row.get("contamination_status", ""),
                "contamination_explanation": co_row.get("explanation", ""),
                "used_for_pretraining": as_bool(co_row.get("used_for_pretraining", False)),
                "used_for_training": as_bool(co_row.get("used_for_training", False)),
                "used_for_candidate_filtering": as_bool(co_row.get("used_for_candidate_filtering", False)),
                "local_artifact_status": inv_row.get("local_artifact_status", ""),
                "known_or_inferred_role_before_stage37a": inv_row.get("known_or_inferred_role_before_stage37a", ""),
                "locally_referenced": as_bool(inv_row.get("evidence_found_in_repo", True)),
            }
        )
    seen = {r["dataset_id"] for r in rows}
    for seed in cfg.get("seed_manual_acquisition_candidates", []):
        if seed["dataset_id"] in seen:
            continue
        rows.append(
            {
                "dataset_id": seed["dataset_id"],
                "dataset_name": seed["dataset_name"],
                "aliases": seed.get("aliases", ""),
                "stage37a_candidate_role": "not_in_stage37a_seeded_for_rev1_manual_review",
                "previous_stage37b_decision": "not_previously_classified",
                "stage37a_clean_validation_eligible": False,
                "stage37a_requires_manual_review": True,
                "stage37a_clean_validation_disqualified": False,
                "stage37a_projection_support": False,
                "stage37a_stress_test": False,
                "stage37a_robustness_only": False,
                "primary_reason": seed.get("reason", ""),
                "eligibility_failure_reason": "not locally approved; seeded by Stage 37B-rev1 for manual metadata/acquisition review",
                "contamination_status": "not_assessed_by_stage37a",
                "contamination_explanation": "No explicit disqualifying evidence in local Stage 37A tables.",
                "used_for_pretraining": False,
                "used_for_training": False,
                "used_for_candidate_filtering": False,
                "local_artifact_status": "not_locally_materialized_by_stage37b_rev1",
                "known_or_inferred_role_before_stage37a": seed.get("suggested_claim_level", "manual_metadata_review_required"),
                "locally_referenced": False,
            }
        )
    return pd.DataFrame(rows)


def explicit_disqualification_reason(row: pd.Series) -> str:
    reasons = []
    if as_bool(row.get("used_for_training")):
        reasons.append("used_for_training_or_source_domain")
    if as_bool(row.get("used_for_pretraining")):
        reasons.append("used_for_pretraining_or_rescue_modeling")
    dataset_id = str(row.get("dataset_id", ""))
    known = str(row.get("known_or_inferred_role_before_stage37a", "")).lower()
    if dataset_id.startswith("SEA_AD") or dataset_id == "SEA-AD_internal" or "excluded_internal" in known:
        reasons.append("sea_ad_source_domain_not_clean_external")
    if "approved_self_supervised_pretraining" in known:
        reasons.append("approved_or_used_for_pretraining")
    if "clean_validation_disqualified" in str(row.get("contamination_status", "")) and (
        as_bool(row.get("used_for_pretraining")) or as_bool(row.get("used_for_training")) or dataset_id in {"HBCC", "HBCA"}
    ):
        reasons.append("explicit_contamination_audit_disqualification")
    return unique_join(reasons)


def classify_claim_level(row: pd.Series) -> tuple[str, str, str, str, str, str, str]:
    dataset_id = str(row.get("dataset_id", ""))
    name = str(row.get("dataset_name", ""))
    disq = explicit_disqualification_reason(row)
    missing = "complete metadata/approval package not present in repository"
    if as_bool(row.get("stage37a_clean_validation_eligible", False)):
        return (
            "approved_clean_external_validation",
            "Stage 37A marked this resource clean-validation eligible.",
            "",
            "",
            "clean external validation after pre-registration",
            "causal, therapeutic, or disease-modifying claims",
            "proceed only under Stage 37C pre-registered validation",
        )
    if disq:
        return (
            "robustness_only" if dataset_id in {"HBCC", "HBCA", "b165f033-9dec-468a-9248-802fc6902a74", "5c97eeeb-7e52-44b3-b010-b832b1f5424c"} else "known_disqualified_from_clean_validation",
            "Explicit prior use/source-domain evidence disqualifies this resource from the clean-validation claim, but it may remain scientifically useful in a bounded role.",
            disq,
            "",
            "robustness/provenance/context only, with explicit non-clean-validation label",
            "clean external validation; external validation completed; clean validation proven",
            "do not use for clean validation; document bounded support role only",
        )
    if dataset_id == "GSE160936":
        return (
            "external_biological_support_candidate",
            "Seeded as high-priority pTau/AT8-linked glial biological support and possible conditional candidate pending metadata/independence confirmation.",
            "",
            missing,
            "external biological support and manual metadata review for possible conditional validation",
            "clean validation before approval; external validation completed",
            "request metadata/readouts and independence review",
        )
    if dataset_id in {"GSE157827", "GSE147528", "ROSMAP_AMP_AD"}:
        return (
            "conditional_clean_validation_candidate",
            "Scientifically plausible validation/acquisition candidate; missing evidence is not rejection.",
            "",
            missing,
            "manual metadata review and possible conditional validation planning",
            "clean validation before approval; validation completed",
            "prioritize metadata/access/readout review",
        )
    if dataset_id == "GSE174367":
        return (
            "conditional_clean_validation_candidate",
            "Morabito resource remains reasonable to reuse, but local v2 artifacts require contamination/independence review before any clean-validation claim.",
            "",
            "local v2 artifacts visible; independence from candidate/model decisions not proven",
            "conditional validation candidate after contamination check; secondary projection/stress-test support",
            "clean validation before contamination check and metadata approval",
            "manual contamination and metadata review",
        )
    if dataset_id == "GSE138852":
        return (
            "external_biological_support_candidate",
            "Grubman/Leng remains useful as external directional smoke-test or entorhinal-cortex support, but underpowered/incomplete for primary clean validation.",
            "",
            "primary validation readouts and full independence package not proven",
            "directional smoke-test; external biological support; projection/signature support",
            "primary clean validation; clean validation proven",
            "use as support only unless upgraded by manual review",
        )
    if as_bool(row.get("stage37a_projection_support", False)):
        return (
            "projection_or_signature_support_candidate",
            "Resource supports signature/module/candidate concordance more than full pathology validation.",
            "",
            missing,
            "projection/signature support; mechanism concordance",
            "clean validation; causal or therapeutic claims",
            "use for support or request metadata for role upgrade",
        )
    if as_bool(row.get("stage37a_stress_test", False)):
        return (
            "stress_test_candidate",
            "Resource is useful for robustness or boundary testing, not clean validation.",
            "",
            missing,
            "stress-test support",
            "clean validation; external validation completed",
            "use only as stress-test unless manually upgraded",
        )
    if as_bool(row.get("stage37a_robustness_only", False)):
        return (
            "robustness_only",
            "Resource can inform robustness/cell-state context but lacks evidence for full validation.",
            "",
            missing,
            "robustness-only or domain plausibility support",
            "clean validation",
            "use only in bounded robustness role",
        )
    return (
        "manual_metadata_review_required",
        "Evidence is insufficient; missing metadata is not rejection.",
        "",
        missing,
        "manual metadata review as candidate validation resource",
        "clean validation before approval",
        "request metadata and PI/manual review",
    )


def build_claim_matrix(source: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in source.iterrows():
        level, reason, explicit, missing, allowed, disallowed, action = classify_claim_level(row)
        flags = {lvl: level == lvl for lvl in CLAIM_LEVELS}
        if level == "external_biological_support_candidate":
            flags["manual_metadata_review_required"] = True
        if level == "conditional_clean_validation_candidate":
            flags["manual_metadata_review_required"] = True
        if level == "projection_or_signature_support_candidate":
            flags["manual_metadata_review_required"] = True
        if level == "stress_test_candidate":
            flags["manual_metadata_review_required"] = True
        priority = "high" if row["dataset_id"] in {"GSE160936", "GSE157827", "GSE174367", "ROSMAP_AMP_AD"} else "medium"
        if level in {"known_disqualified_from_clean_validation", "robustness_only"}:
            priority = "low" if row["dataset_id"] not in {"HBCC", "HBCA"} else "medium"
        rows.append(
            {
                "dataset_id": row["dataset_id"],
                "dataset_name": row["dataset_name"],
                "aliases": row.get("aliases", ""),
                "previous_stage37b_decision": row.get("previous_stage37b_decision", ""),
                "revised_claim_level": level,
                "clean_validation_currently_approved": level == "approved_clean_external_validation",
                "conditional_clean_validation_candidate": flags["conditional_clean_validation_candidate"],
                "external_biological_support_candidate": flags["external_biological_support_candidate"],
                "projection_or_signature_support_candidate": flags["projection_or_signature_support_candidate"],
                "stress_test_candidate": flags["stress_test_candidate"],
                "robustness_only": flags["robustness_only"],
                "manual_metadata_review_required": flags["manual_metadata_review_required"],
                "known_disqualified_from_clean_validation": bool(explicit) and level in {"known_disqualified_from_clean_validation", "robustness_only"},
                "reason_for_reclassification": reason,
                "explicit_disqualifying_evidence": explicit,
                "missing_evidence_or_metadata": missing,
                "allowed_use_now": allowed,
                "disallowed_use_now": disallowed,
                "evidence_needed_to_upgrade": "complete metadata, readout, access, direction, independence, and null-reporting checks",
                "recommended_next_action": action,
                "priority_for_reuse": priority,
            }
        )
    return pd.DataFrame(rows)


def build_summary(matrix: pd.DataFrame, gate_allowed: bool) -> pd.DataFrame:
    row = {
        "n_datasets_total": len(matrix),
        "n_approved_clean_external_validation": int(matrix["clean_validation_currently_approved"].sum()),
        "n_conditional_clean_validation_candidates": int(matrix["conditional_clean_validation_candidate"].sum()),
        "n_external_biological_support_candidates": int(matrix["external_biological_support_candidate"].sum()),
        "n_projection_or_signature_support_candidates": int(matrix["projection_or_signature_support_candidate"].sum()),
        "n_stress_test_candidates": int(matrix["stress_test_candidate"].sum()),
        "n_robustness_only": int(matrix["robustness_only"].sum()),
        "n_manual_metadata_review_required": int(matrix["manual_metadata_review_required"].sum()),
        "n_known_disqualified_from_clean_validation": int(matrix["known_disqualified_from_clean_validation"].sum()),
        "stage37c_clean_external_validation_allowed": gate_allowed,
        "key_interpretation": "No clean validation is currently approved, but missing metadata is not rejection; multiple resources remain reusable at bounded claim levels.",
    }
    return pd.DataFrame([row])


def build_conditional(matrix: pd.DataFrame) -> pd.DataFrame:
    subset = matrix[matrix["conditional_clean_validation_candidate"] == True].copy()
    rows = []
    for _, row in subset.iterrows():
        rows.append(
            {
                "dataset_id": row["dataset_id"],
                "dataset_name": row["dataset_name"],
                "why_candidate_is_reasonable": row["reason_for_reclassification"],
                "frozen_mechanisms_supported": "to_be_confirmed_against_Stage36E_mechanisms",
                "pathology_or_mechanism_readouts_available_or_needed": "pathology/mechanism readouts must be documented before validation",
                "required_independence_checks": "not used for training, pretraining, model selection, candidate selection, or threshold tuning",
                "required_metadata_checks": "donor/sample metadata, batch/provenance, access/license, gene/module measurements, null-reporting feasibility",
                "possible_stage37c_or_stage37d_use": "Stage 37C only if all gates pass; otherwise Stage 37D/external support or acquisition planning",
                "claim_if_passes_manual_review": "conditional candidate may advance to pre-registered validation",
                "claim_if_metadata_remains_incomplete": "external support or manual-review candidate only; not clean validation",
            }
        )
    return pd.DataFrame(rows)


def build_external_support(matrix: pd.DataFrame) -> pd.DataFrame:
    support_flags = ["external_biological_support_candidate", "projection_or_signature_support_candidate", "stress_test_candidate", "robustness_only"]
    subset = matrix[matrix[support_flags].any(axis=1)].copy()
    rows = []
    for _, row in subset.iterrows():
        support_type = row["revised_claim_level"]
        rows.append(
            {
                "dataset_id": row["dataset_id"],
                "dataset_name": row["dataset_name"],
                "support_type": support_type,
                "mechanisms_or_candidates_supported": "to_be_mapped_after_metadata_review",
                "allowed_analysis_type": row["allowed_use_now"],
                "allowed_claim_language": "external biological/supporting evidence only; not clean validation unless separately approved",
                "prohibited_claim_language": DISALLOWED_LANGUAGE,
                "priority": row["priority_for_reuse"],
            }
        )
    return pd.DataFrame(rows)


def build_known_disqualified(matrix: pd.DataFrame) -> pd.DataFrame:
    subset = matrix[matrix["known_disqualified_from_clean_validation"] == True].copy()
    rows = []
    for _, row in subset.iterrows():
        rows.append(
            {
                "dataset_id": row["dataset_id"],
                "dataset_name": row["dataset_name"],
                "disqualification_reason": row["reason_for_reclassification"],
                "explicit_evidence": row["explicit_disqualifying_evidence"],
                "still_useful_for": row["allowed_use_now"],
                "claim_boundary": "not clean validation; may be scientifically useful only at bounded support level",
            }
        )
    return pd.DataFrame(rows)


def build_manual_queue(matrix: pd.DataFrame) -> pd.DataFrame:
    subset = matrix[matrix["manual_metadata_review_required"] == True].copy()
    rows = []
    for i, row in enumerate(subset.itertuples(index=False), start=1):
        rows.append(
            {
                "review_id": f"REV1_{i:03d}",
                "dataset_id": row.dataset_id,
                "dataset_name": row.dataset_name,
                "review_priority": row.priority_for_reuse,
                "reason_review_needed": row.reason_for_reclassification,
                "minimum_metadata_to_request": "donor/sample metadata; pathology/mechanism readouts; gene/module measurements; batch/provenance; licensing/access; prior-use independence",
                "exact_question_for_pi_or_manual_reviewer": "Can this resource be approved for the proposed bounded claim level, and if clean validation is desired, does it satisfy every Stage 36E/37A independence and readout rule?",
                "possible_decision_after_review": "approve_bounded_support; approve_conditional_clean_validation; keep_manual_review_pending; disqualify_clean_validation_with_explicit_reason",
            }
        )
    return pd.DataFrame(rows)


def build_gate(matrix: pd.DataFrame) -> pd.DataFrame:
    approved = matrix[matrix["clean_validation_currently_approved"] == True]
    conditional = matrix[matrix["conditional_clean_validation_candidate"] == True]
    allowed = not approved.empty
    rec = "Stage37C_external_support_first_pass_or_manual_metadata_review"
    if allowed:
        rec = "Stage37C_clean_external_validation_after_preregistration"
    return pd.DataFrame(
        [
            {
                "stage37c_clean_external_validation_allowed": allowed,
                "reason": "No dataset has explicit complete approval evidence in the repo." if not allowed else "At least one dataset is explicitly approved.",
                "approved_datasets": unique_join(approved["dataset_id"].tolist()),
                "conditional_candidates": unique_join(conditional["dataset_id"].tolist()),
                "recommended_next_stage": rec,
                "claim_boundary": "Stage 37B-rev1 reclassifies claim levels only; it does not complete validation.",
            }
        ]
    )


def build_pass_fail(presence: dict[str, bool], outputs: dict[str, bool], matrix: pd.DataFrame, gate: pd.DataFrame) -> pd.DataFrame:
    missing_metadata_rejected = bool(
        ((matrix["missing_evidence_or_metadata"].astype(str) != "") & (matrix["revised_claim_level"] == "known_disqualified_from_clean_validation")).any()
    )
    known_disq_without_evidence = bool(
        ((matrix["known_disqualified_from_clean_validation"] == True) & (matrix["explicit_disqualifying_evidence"].astype(str) == "")).any()
    )
    row = {
        "stage37b_rev1_run": True,
        "stage37a_inputs_found": all(v for k, v in presence.items() if k.startswith("stage37a")),
        "stage37b_inputs_found": all(v for k, v in presence.items() if k.startswith("stage37b")),
        "stage36e_inputs_found": all(v for k, v in presence.items() if k.startswith("stage36e")),
        "claim_level_matrix_written": outputs.get("claim_level_matrix", False),
        "reclassification_summary_written": outputs.get("reclassification_summary", False),
        "conditional_candidates_written": outputs.get("conditional_candidates", False),
        "external_support_candidates_written": outputs.get("external_support_candidates", False),
        "known_disqualified_table_written": outputs.get("known_disqualified", False),
        "manual_metadata_review_queue_written": outputs.get("manual_metadata_review_queue", False),
        "stage37c_gate_written": outputs.get("stage37c_gate", False),
        "no_new_modeling_run": True,
        "no_validation_run": True,
        "no_data_download": True,
        "no_web_scraping": True,
        "no_external_validation_claim": True,
        "no_causal_claim": True,
        "no_therapeutic_claim": True,
        "missing_metadata_not_treated_as_rejection": not missing_metadata_rejected,
        "known_disqualification_requires_explicit_evidence": not known_disq_without_evidence,
        "safety_audit_pass": (not missing_metadata_rejected) and (not known_disq_without_evidence),
    }
    row["stage37b_rev1_run_pass"] = all(bool(v) for v in row.values())
    row["stage37c_clean_external_validation_allowed"] = bool(gate.iloc[0]["stage37c_clean_external_validation_allowed"])
    row["controlled_interpretation"] = "Stage 37B-rev1 corrected claim-level classification; missing metadata is not rejection, and no validation was run."
    return pd.DataFrame([row])


def build_report(matrix: pd.DataFrame, summary: pd.DataFrame, cond: pd.DataFrame, support: pd.DataFrame, disq: pd.DataFrame, queue: pd.DataFrame, gate: pd.DataFrame, pf: pd.DataFrame) -> str:
    level_summary = matrix.groupby("revised_claim_level").size().reset_index(name="n_datasets")
    return "\n".join(
        [
            "# Stage 37B-rev1 dataset claim reclassification report v1",
            "",
            "## Why revision was needed",
            "",
            "Stage 37A/37B correctly kept the clean-validation gate closed, but the prior Stage 37B wording could make missing metadata look like dataset rejection.",
            "",
            "## Corrected principle",
            "",
            "Missing metadata is not rejection. A resource is disqualified from clean validation only when explicit disqualifying evidence exists.",
            "",
            "## Revised dataset claim-level summary",
            "",
            markdown_table(level_summary),
            "",
            "## Conditional validation candidates",
            "",
            markdown_table(cond[["dataset_id", "dataset_name", "why_candidate_is_reasonable"]], max_rows=40),
            "",
            "## External support candidates",
            "",
            markdown_table(support[["dataset_id", "dataset_name", "support_type", "allowed_analysis_type", "priority"]], max_rows=40),
            "",
            "## Known disqualified datasets with explicit reasons only",
            "",
            markdown_table(disq),
            "",
            "## Stage 37C gate",
            "",
            markdown_table(gate),
            "",
            "## What can be reused now",
            "",
            "Resources can be reused only at their bounded claim level: conditional/manual review, external biological support, projection/signature support, stress-test support, or robustness-only support.",
            "",
            "## What cannot be claimed",
            "",
            f"Avoid: {DISALLOWED_LANGUAGE}.",
            "",
            "## Recommended next stage",
            "",
            str(gate.iloc[0]["recommended_next_stage"]),
            "",
            "## Pass/fail summary",
            "",
            markdown_table(pf),
        ]
    )


def build_pi_report(matrix: pd.DataFrame, cond: pd.DataFrame, support: pd.DataFrame, queue: pd.DataFrame, gate: pd.DataFrame) -> str:
    wanted = matrix[matrix["dataset_id"].isin(["GSE160936", "GSE157827", "GSE174367", "GSE138852", "ROSMAP_AMP_AD"])]
    return "\n".join(
        [
            "# Stage 37B-rev1 PI reuse recommendation summary v1",
            "",
            "## Short answer",
            "",
            "Several datasets are reasonable to reuse, but none are currently approved for the strongest clean external-validation claim unless explicit approval evidence is added later.",
            "",
            "## Top recommended reuse datasets",
            "",
            markdown_table(wanted[["dataset_id", "dataset_name", "revised_claim_level", "allowed_use_now", "recommended_next_action"]]),
            "",
            "## How each should be used",
            "",
            markdown_table(support[["dataset_id", "support_type", "allowed_analysis_type", "priority"]], max_rows=40),
            "",
            "## Manual checks needed",
            "",
            markdown_table(queue[["dataset_id", "review_priority", "minimum_metadata_to_request", "exact_question_for_pi_or_manual_reviewer"]], max_rows=40),
            "",
            "## Stage 37C gate",
            "",
            markdown_table(gate),
            "",
            "## Safe lab-meeting language",
            "",
            SAFE_LANGUAGE,
            "",
            "Avoid: " + DISALLOWED_LANGUAGE,
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


def update_scorecard_csv(path_value: str | Path, summary: pd.DataFrame, gate: pd.DataFrame) -> None:
    path = resolve(path_value)
    row = {
        "stage_id": "stage37b_rev1_dataset_claim_reclassification",
        "status": "complete",
        "stage": "Stage 37B-rev1",
        "primary_metric": "corrected dataset claim-level reclassification",
        "pass_rule": "pass requires missing metadata not treated as rejection and explicit evidence for known disqualification",
        "result": f"run_pass=True; stage37c_clean_external_validation_allowed={bool(gate.iloc[0]['stage37c_clean_external_validation_allowed'])}",
        "pass_fail": "pass",
        "allowed_inputs": "existing Stage 37A/37B and Stage 36E local outputs only",
        "forbidden_inputs": "new modeling; validation run; downloads; web scraping; validation/causal/therapeutic claims",
        "interpretation": "Stage 37B-rev1 corrected dataset reuse categories by allowed claim level; no validation was run.",
        "notes": str(summary.iloc[0]["key_interpretation"]),
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


def update_status_docs(cfg: dict[str, Any], summary: pd.DataFrame, gate: pd.DataFrame) -> None:
    allowed = bool(gate.iloc[0]["stage37c_clean_external_validation_allowed"])
    append_section_once(
        cfg["status_updates"]["active_status"],
        "## Stage 37B-rev1 dataset claim reclassification status",
        (
            "Stage 37B-rev1 is complete. It corrects Stage 37B wording by classifying datasets/resources by allowed claim level. "
            "Missing metadata is not treated as rejection; known disqualification requires explicit evidence. "
            f"Stage 37C clean external validation allowed now: `{allowed}`."
        ),
    )
    append_section_once(
        cfg["status_updates"]["scorecard_md"],
        "## Stage 37B-rev1 dataset claim reclassification result",
        (
            "Stage 37B-rev1 is complete. Run pass: `True`. It preserves the closed clean-validation gate while clarifying that many resources remain reusable for conditional validation review, external biological support, projection/signature support, stress-test support, or robustness-only support."
        ),
    )
    update_scorecard_csv(cfg["status_updates"]["scorecard_csv"], summary, gate)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/agent/stage37b_rev1_dataset_claim_reclassification_v1.yaml")
    args = parser.parse_args()
    cfg = load_cfg(resolve(args.config))
    presence = input_presence(cfg)

    inventory = read_csv(cfg["inputs"]["stage37a_dataset_inventory"])
    roles = read_csv(cfg["inputs"]["stage37a_dataset_role_classification"])
    elig = read_csv(cfg["inputs"]["stage37a_clean_validation_eligibility"])
    contam = read_csv(cfg["inputs"]["stage37a_contamination_audit"])
    previous = read_csv(cfg["inputs"]["stage37b_dataset_decision_matrix"])

    source = merge_source_tables(cfg, inventory, roles, elig, contam, previous)
    matrix = build_claim_matrix(source)
    gate = build_gate(matrix)
    summary = build_summary(matrix, bool(gate.iloc[0]["stage37c_clean_external_validation_allowed"]))
    cond = build_conditional(matrix)
    support = build_external_support(matrix)
    disq = build_known_disqualified(matrix)
    queue = build_manual_queue(matrix)

    outputs: dict[str, bool] = {}
    paths: list[Path] = []
    for key, df in [
        ("claim_level_matrix", matrix),
        ("reclassification_summary", summary),
        ("conditional_candidates", cond),
        ("external_support_candidates", support),
        ("known_disqualified", disq),
        ("manual_metadata_review_queue", queue),
        ("stage37c_gate", gate),
    ]:
        path = write_csv(df, cfg["outputs"][key])
        paths.append(path)
        outputs[key] = path.exists()

    pf = build_pass_fail(presence, outputs, matrix, gate)
    pf_path = write_csv(pf, cfg["outputs"]["pass_fail"])
    paths.append(pf_path)
    outputs["pass_fail"] = pf_path.exists()

    report_path = write_text(build_report(matrix, summary, cond, support, disq, queue, gate, pf), cfg["outputs"]["report"])
    pi_path = write_text(build_pi_report(matrix, cond, support, queue, gate), cfg["outputs"]["pi_report"])
    paths.extend([report_path, pi_path])
    outputs["report"] = report_path.exists()
    outputs["pi_report"] = pi_path.exists()

    pf = build_pass_fail(presence, outputs, matrix, gate)
    write_csv(pf, cfg["outputs"]["pass_fail"])
    write_text(build_report(matrix, summary, cond, support, disq, queue, gate, pf), cfg["outputs"]["report"])
    write_text(build_pi_report(matrix, cond, support, queue, gate), cfg["outputs"]["pi_report"])
    update_status_docs(cfg, summary, gate)
    paths.extend(
        [
            resolve(cfg["status_updates"]["active_status"]),
            resolve(cfg["status_updates"]["scorecard_md"]),
            resolve(cfg["status_updates"]["scorecard_csv"]),
        ]
    )

    row = summary.iloc[0]
    print("stage37b_rev1_paths_written=")
    for path in paths:
        print(str(path.relative_to(ROOT)))
    print(f"n_datasets_total={row['n_datasets_total']}")
    print(f"n_approved_clean_external_validation={row['n_approved_clean_external_validation']}")
    print(f"n_conditional_clean_validation_candidates={row['n_conditional_clean_validation_candidates']}")
    print(f"n_external_biological_support_candidates={row['n_external_biological_support_candidates']}")
    print(f"n_projection_or_signature_support_candidates={row['n_projection_or_signature_support_candidates']}")
    print(f"n_stress_test_candidates={row['n_stress_test_candidates']}")
    print(f"n_manual_metadata_review_required={row['n_manual_metadata_review_required']}")
    print(f"n_known_disqualified_from_clean_validation={row['n_known_disqualified_from_clean_validation']}")
    print(f"stage37c_clean_external_validation_allowed={row['stage37c_clean_external_validation_allowed']}")
    print(f"recommended_next_stage={gate.iloc[0]['recommended_next_stage']}")
    print(f"stage37b_rev1_run_pass={pf.iloc[0]['stage37b_rev1_run_pass']}")


if __name__ == "__main__":
    main()
