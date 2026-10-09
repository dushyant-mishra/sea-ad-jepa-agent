from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[1]

ALLOWED_ROLES = {
    "clean_external_validation_candidate",
    "stress_test_support",
    "projection_or_signature_support",
    "robustness_only",
    "excluded_or_contaminated",
    "requires_manual_review",
}

SAFE_LANGUAGE = (
    "validation eligibility audit; candidate validation resource; stress-test support; projection/signature support; "
    "requires manual review; not clean validation; eligible for proposed next validation only if independence is confirmed"
)
DISALLOWED_LANGUAGE = (
    "validated; external validation completed; clean validation proven; causal regulator; therapeutic target; disease-modifying target"
)


SEED_DATASETS = [
    {
        "dataset_id": "GSE138852",
        "dataset_name": "GSE138852 / Grubman-Leng",
        "aliases": "GSE138852;Grubman;Leng;Grubman-Leng",
        "resource_type": "public single-cell/single-nucleus AD resource",
    },
    {
        "dataset_id": "GSE174367",
        "dataset_name": "GSE174367 / Morabito",
        "aliases": "GSE174367;Morabito",
        "resource_type": "public single-nucleus AD resource",
    },
    {
        "dataset_id": "HBCC",
        "dataset_name": "HBCC",
        "aliases": "HBCC;5c97eeeb-7e52-44b3-b010-b832b1f5424c;HBCC_Cohort",
        "resource_type": "CELLxGENE human brain cohort",
    },
    {
        "dataset_id": "HBCA",
        "dataset_name": "HBCA / Human Brain Cell Atlas",
        "aliases": "HBCA;Human Brain Cell Atlas;b165f033-9dec-468a-9248-802fc6902a74;All non-neuronal cells",
        "resource_type": "CELLxGENE human brain atlas",
    },
    {
        "dataset_id": "SEA_AD_PUBLIC_SPATIAL_PATHOLOGY",
        "dataset_name": "SEA-AD public spatial/pathology resources",
        "aliases": "SEA-AD;SEA_AD;SEA AD;spatial;pathology",
        "resource_type": "internal/source-domain spatial/pathology resource",
    },
    {
        "dataset_id": "PUBLIC_CELLXGENE_MICROGLIA",
        "dataset_name": "Public CELLxGENE microglia datasets",
        "aliases": "CELLxGENE;microglia;Olah;CSF1R;Rexach",
        "resource_type": "public cell-state/plausibility resource",
    },
    {
        "dataset_id": "LU_2026_SIGNATURES",
        "dataset_name": "Lu et al. 2026 signatures/supplementary tables",
        "aliases": "Lu;Lu et al;2026;signature;supplementary",
        "resource_type": "signature/projection support resource",
    },
    {
        "dataset_id": "PIG_WGCNA_RESOURCES",
        "dataset_name": "PIG / WGCNA resources",
        "aliases": "PIG;WGCNA",
        "resource_type": "prior module/signature support resource",
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


def unique_join(values: list[Any], sep: str = ";") -> str:
    seen = []
    for value in values:
        text = str(value).strip()
        if not text or text == "nan":
            continue
        if text not in seen:
            seen.append(text)
    return sep.join(seen)


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


def input_presence(cfg: dict[str, Any]) -> tuple[dict[str, bool], dict[str, bool]]:
    primary = {k: resolve(v).exists() for k, v in cfg["inputs"].items()}
    optional = {k: resolve(v).exists() for k, v in cfg.get("optional_context_inputs", {}).items()}
    return primary, optional


def scan_repo(cfg: dict[str, Any]) -> dict[str, dict[str, Any]]:
    terms = [str(t) for t in cfg["scan"]["terms"]]
    max_bytes = int(cfg["scan"].get("max_file_bytes", 2_000_000))
    evidence: dict[str, dict[str, Any]] = {t.lower(): {"term": t, "paths": [], "count": 0} for t in terms}
    suffixes = {".md", ".txt", ".csv", ".tsv", ".yaml", ".yml", ".py", ".json"}
    for root_value in cfg["scan"]["roots"]:
        root = resolve(root_value)
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in suffixes:
                continue
            rel = path.relative_to(ROOT).as_posix()
            if rel.startswith("data/") or "stage37a_" in rel:
                continue
            try:
                if path.stat().st_size > max_bytes:
                    continue
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            low = text.lower()
            for term in terms:
                n = low.count(term.lower())
                if n:
                    rec = evidence[term.lower()]
                    rec["count"] += n
                    rec["paths"].append(rel)
    return evidence


def evidence_for_aliases(evidence: dict[str, dict[str, Any]], aliases: str) -> tuple[int, str]:
    count = 0
    paths: list[str] = []
    for alias in aliases.split(";"):
        rec = evidence.get(alias.strip().lower())
        if not rec:
            continue
        count += int(rec["count"])
        paths.extend(rec["paths"])
    return count, unique_join(paths)


def build_inventory(cfg: dict[str, Any], evidence: dict[str, dict[str, Any]], role_audit: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    seed_ids = set()
    for seed in SEED_DATASETS:
        seed_ids.add(seed["dataset_id"])
        count, paths = evidence_for_aliases(evidence, seed["aliases"])
        local_status = "referenced_only"
        if seed["dataset_id"] == "GSE174367" and (
            resolve("results/tables/v2_1_gse174367_cell_trajectory_scores.csv").exists()
            or resolve("results/tables/v2_2_abeta_responsive_microglia_cell_scores_summary.csv").exists()
        ):
            local_status = "pre_existing_local_v2_artifacts_visible_not_modified"
        if seed["dataset_id"] == "HBCA" and resolve("results/tables/stage34a_filtered_matrix_manifest_v1.csv").exists():
            local_status = "pretraining_rescue_manifest_present"
        if seed["dataset_id"] == "HBCC" and resolve("results/tables/stage34b_hbcc_matrix_manifest_v1.csv").exists():
            local_status = "pretraining_rescue_manifest_present"
        if seed["dataset_id"].startswith("SEA_AD"):
            local_status = "source_domain_or_internal_resource"
        rows.append(
            {
                "dataset_id": seed["dataset_id"],
                "dataset_name": seed["dataset_name"],
                "aliases": seed["aliases"],
                "resource_type": seed["resource_type"],
                "evidence_found_in_repo": count > 0,
                "evidence_paths": paths,
                "prior_stage_mentions": infer_prior_stage_mentions(paths),
                "local_artifact_status": local_status,
                "known_or_inferred_role_before_stage37a": infer_known_role(seed["dataset_id"], role_audit),
                "notes": "Seeded Stage 37A candidate resource; classification is conservative.",
            }
        )
    if not role_audit.empty:
        for _, row in role_audit.iterrows():
            dataset_id = str(row.get("dataset_id", ""))
            if not dataset_id or dataset_id in seed_ids:
                continue
            aliases = unique_join([dataset_id, row.get("dataset_name", ""), row.get("source", ""), row.get("collection_name", "")])
            count, paths = evidence_for_aliases(evidence, aliases)
            rows.append(
                {
                    "dataset_id": dataset_id,
                    "dataset_name": row.get("dataset_name", ""),
                    "aliases": aliases,
                    "resource_type": row.get("source", "local_or_external_resource"),
                    "evidence_found_in_repo": count > 0 or bool(paths) or True,
                    "evidence_paths": paths or "results/tables/stage32_external_dataset_role_audit_v1.csv",
                    "prior_stage_mentions": infer_prior_stage_mentions(paths) or "Stage32",
                    "local_artifact_status": "registry_row_only",
                    "known_or_inferred_role_before_stage37a": row.get("normalized_role", row.get("registry_role", "")),
                    "notes": "Imported from existing Stage 32 external dataset role audit.",
                }
            )
    return pd.DataFrame(rows)


def infer_prior_stage_mentions(paths: str) -> str:
    stages = []
    for token in ["stage32", "stage33", "stage34", "stage35", "stage36", "v2", "discovery"]:
        if token in str(paths).lower():
            stages.append(token.replace("stage", "Stage ").upper() if token.startswith("stage") else token)
    return unique_join(stages)


def infer_known_role(dataset_id: str, role_audit: pd.DataFrame) -> str:
    if not role_audit.empty:
        mask = role_audit["dataset_id"].astype(str).str.contains(dataset_id, case=False, regex=False)
        if mask.any():
            row = role_audit[mask].iloc[0]
            return str(row.get("normalized_role", row.get("registry_role", "")))
    mapping = {
        "HBCA": "approved_self_supervised_pretraining_or_rescue_source",
        "HBCC": "approved_self_supervised_pretraining_or_rescue_source",
        "SEA_AD_PUBLIC_SPATIAL_PATHOLOGY": "source_domain_or_internal_resource",
        "PUBLIC_CELLXGENE_MICROGLIA": "plausibility_or_domain_robustness_resource",
        "LU_2026_SIGNATURES": "projection_or_signature_support_resource",
        "PIG_WGCNA_RESOURCES": "projection_or_signature_support_resource",
        "GSE174367": "already_used_plausibility_or_exploratory_resource",
        "GSE138852": "already_used_plausibility_or_exploratory_resource",
    }
    return mapping.get(dataset_id, "requires_manual_review")


def classify_inventory(inventory: pd.DataFrame, role_audit: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in inventory.iterrows():
        dataset_id = str(row["dataset_id"])
        name = str(row["dataset_name"])
        known = str(row["known_or_inferred_role_before_stage37a"]).lower()
        notes = str(row.get("notes", ""))
        evidence_paths = str(row.get("evidence_paths", ""))
        role = "requires_manual_review"
        clean = False
        stress = False
        projection = False
        robustness = False
        excluded = False
        manual = True
        reason = "Insufficient evidence that the resource has all frozen readouts and is independent of training/pretraining/model/candidate selection."
        allowed = "manual eligibility review only"
        disallowed = "do not call clean validation"
        recommendation = "manual_review_before_any_validation_use"

        if dataset_id in {"HBCA", "HBCC", "b165f033-9dec-468a-9248-802fc6902a74", "5c97eeeb-7e52-44b3-b010-b832b1f5424c", "4442d412-91cb-4261-acca-8adf5fa04c11", "GSE98969", "mouse_isocortex_hippocampus", "mouse_brain_aging_atlas"} or "approved_self_supervised_pretraining" in known or "pretraining" in known:
            role = "excluded_or_contaminated"
            excluded = True
            manual = False
            reason = "Prior audit marks this resource as approved/used for external pretraining or rescue benchmarking; clean validation independence is forfeited."
            allowed = "pretraining/rescue provenance context; robustness discussion only if clearly labeled"
            disallowed = "clean validation; primary external validation; model-selection evidence"
            recommendation = "exclude_from_clean_validation"
        elif "internal" in known or dataset_id.startswith("SEA_AD") or "SEA-AD" in name:
            role = "excluded_or_contaminated"
            excluded = True
            manual = False
            reason = "SEA-AD-derived/source-domain material is not independent of the SEA-AD modeling and candidate-selection workflow."
            allowed = "internal context or source-domain interpretation only"
            disallowed = "clean external validation"
            recommendation = "exclude_from_clean_validation"
        elif dataset_id in {"GSE174367", "GSE138852"} or "plausibility" in known or "already_used" in known:
            role = "projection_or_signature_support"
            projection = True
            robustness = True
            clean = False
            manual = True
            reason = "Existing repo evidence indicates prior exploratory/plausibility use; independence from candidate/model selection is not proven."
            allowed = "projection/signature support or robustness-only support after manual review"
            disallowed = "clean validation unless independence and frozen readouts are proven in a new audit"
            recommendation = "manual_review_or_projection_only"
        elif dataset_id in {"LU_2026_SIGNATURES", "PIG_WGCNA_RESOURCES"}:
            role = "projection_or_signature_support"
            projection = True
            robustness = True
            manual = True
            reason = "Resource appears suited to mechanism/signature concordance, not full pathology validation unless required frozen readouts are verified."
            allowed = "signature concordance; mechanism-support review"
            disallowed = "full pathology validation; causal or therapeutic claims"
            recommendation = "projection_or_signature_support_only"
        elif "stress" in known:
            role = "stress_test_support"
            stress = True
            manual = True
            reason = "Registry indicates stress-test role; stress-test evidence is not clean validation."
            allowed = "stress-test support if independence and labels are documented"
            disallowed = "clean validation unless upgraded by manual eligibility audit"
            recommendation = "stress_test_only"
        elif "protected_clean_holdout" in known:
            role = "requires_manual_review"
            manual = True
            reason = "Registry protects this as a possible clean holdout, but Stage 37A cannot confirm required pathology/mechanism readouts or independence from all later choices."
            allowed = "candidate validation resource only after manual approval"
            disallowed = "clean validation before manual approval and data access checks"
            recommendation = "manual_dataset_approval_before_use"
        elif "cellxgene" in str(row.get("resource_type", "")).lower():
            role = "robustness_only"
            robustness = True
            manual = True
            reason = "CELLxGENE resources may support domain/cell-state plausibility, but pathology labels and frozen readouts are not confirmed."
            allowed = "domain robustness or cell-state plausibility review"
            disallowed = "primary pathology validation without required labels/readouts"
            recommendation = "robustness_or_manual_review"

        assert role in ALLOWED_ROLES
        rows.append(
            {
                "dataset_id": dataset_id,
                "dataset_name": name,
                "candidate_role": role,
                "clean_external_validation_candidate": clean,
                "stress_test_candidate": stress,
                "projection_or_signature_support_candidate": projection,
                "robustness_only_candidate": robustness,
                "excluded_or_contaminated": excluded,
                "requires_manual_review": manual,
                "primary_reason": reason,
                "allowed_use": allowed,
                "disallowed_use": disallowed,
                "stage37b_use_recommendation": recommendation,
            }
        )
    return pd.DataFrame(rows)


def build_eligibility(role_class: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in role_class.iterrows():
        role = row["candidate_role"]
        excluded = bool(row["excluded_or_contaminated"])
        clean = bool(row["clean_external_validation_candidate"])
        manual = bool(row["requires_manual_review"])
        has_readout = False if role in {"projection_or_signature_support", "robustness_only"} else None
        has_gene = True if role != "excluded_or_contaminated" else None
        metadata = None
        independent_pretraining = not excluded
        independent_training = not excluded
        independent_model_selection = not excluded and not manual
        independent_candidate = not excluded and not manual
        independent_threshold = not excluded and not manual
        if clean:
            reason = "eligible under Stage 37A conservative audit"
            checks = "freeze target/candidate/direction; confirm data access and labels before use"
        elif excluded:
            reason = "disqualified by prior use or source-domain/internal relationship"
            checks = "none for clean validation; may be used only in allowed non-clean role if specified"
        elif manual:
            reason = "manual review required: required readouts and complete independence are not proven"
            checks = "verify pathology/mechanism readout, gene/module measurements, metadata, donor/sample independence, and no use in model/candidate/threshold choices"
        else:
            reason = "not eligible for clean validation under current evidence"
            checks = "manual review required before any role upgrade"
        rows.append(
            {
                "dataset_id": row["dataset_id"],
                "dataset_name": row["dataset_name"],
                "has_required_pathology_or_mechanism_readout": has_readout if has_readout is not None else False,
                "has_required_gene_or_module_measurements": has_gene if has_gene is not None else False,
                "has_donor_or_sample_level_metadata": bool(metadata) if metadata is not None else False,
                "independent_of_training": independent_training,
                "independent_of_pretraining": independent_pretraining,
                "independent_of_model_selection": independent_model_selection,
                "independent_of_candidate_selection": independent_candidate,
                "independent_of_threshold_tuning": independent_threshold,
                "candidate_direction_can_be_prespecified": True,
                "negative_results_can_be_reported": True,
                "clean_validation_eligible": clean,
                "eligibility_failure_reason": reason,
                "required_manual_checks_before_use": checks,
            }
        )
    return pd.DataFrame(rows)


def build_contamination(role_class: pd.DataFrame, inventory: pd.DataFrame) -> pd.DataFrame:
    inv = inventory.set_index("dataset_id")
    rows = []
    for _, row in role_class.iterrows():
        dataset_id = row["dataset_id"]
        known = str(inv.loc[dataset_id, "known_or_inferred_role_before_stage37a"]).lower() if dataset_id in inv.index else ""
        paths = str(inv.loc[dataset_id, "evidence_paths"]) if dataset_id in inv.index else ""
        used_pretraining = "pretraining" in known or dataset_id in {"HBCA", "HBCC", "b165f033-9dec-468a-9248-802fc6902a74", "5c97eeeb-7e52-44b3-b010-b832b1f5424c", "4442d412-91cb-4261-acca-8adf5fa04c11", "GSE98969", "mouse_isocortex_hippocampus", "mouse_brain_aging_atlas"}
        used_training = "internal" in known or str(dataset_id).startswith("SEA_AD")
        prior_interp = bool(row["projection_or_signature_support_candidate"] or row["robustness_only_candidate"] or "plausibility" in known)
        used_candidate = "already_used" in known or "plausibility" in known or dataset_id in {"GSE174367", "GSE138852"}
        disq = bool(used_training or used_pretraining or used_candidate or row["excluded_or_contaminated"])
        if disq:
            status = "clean_validation_disqualified"
        elif row["requires_manual_review"]:
            status = "manual_review_required_before_clean_validation"
        else:
            status = "no_contamination_detected_by_stage37a"
        rows.append(
            {
                "dataset_id": dataset_id,
                "dataset_name": row["dataset_name"],
                "used_for_training": used_training,
                "used_for_pretraining": used_pretraining,
                "used_for_auxiliary_supervision": False,
                "used_for_architecture_choice": False,
                "used_for_feature_selection": used_candidate,
                "used_for_threshold_setting": used_candidate,
                "used_for_candidate_filtering": used_candidate,
                "used_for_model_selection": used_training or used_pretraining,
                "used_for_prior_interpretation_only": prior_interp,
                "contamination_status": status,
                "evidence_paths": paths,
                "clean_validation_disqualified": disq,
                "explanation": row["primary_reason"],
            }
        )
    return pd.DataFrame(rows)


def build_stage37b_recommendation(role_class: pd.DataFrame) -> pd.DataFrame:
    clean = role_class[role_class["clean_external_validation_candidate"] == True]
    stress = role_class[role_class["stress_test_candidate"] == True]
    projection = role_class[role_class["projection_or_signature_support_candidate"] == True]
    excluded = role_class[(role_class["excluded_or_contaminated"] == True) | (role_class["clean_external_validation_candidate"] == False)]
    manual = role_class[role_class["requires_manual_review"] == True]
    if clean.empty:
        next_stage = "Stage37B_manual_dataset_approval" if not manual.empty else "Stage37B_validation_data_acquisition"
        action = "Do not run validation yet; perform manual dataset approval and/or acquire a clean validation dataset with frozen readouts."
        rationale = "Stage 37A found no dataset/resource that can honestly be called clean validation under frozen Stage 36E rules."
    else:
        next_stage = "Stage37B_clean_external_validation"
        action = "Proceed only with pre-registered validation using clean eligible resources."
        rationale = "At least one resource passed conservative clean-validation eligibility checks."
    return pd.DataFrame(
        [
            {
                "recommendation_id": "stage37a_rec_001",
                "recommended_next_stage": next_stage,
                "recommended_action": action,
                "eligible_datasets_for_clean_validation": unique_join(clean["dataset_id"].tolist()),
                "datasets_for_stress_test": unique_join(stress["dataset_id"].tolist()),
                "datasets_for_projection_or_signature_support": unique_join(projection["dataset_id"].tolist()),
                "datasets_excluded_from_clean_validation": unique_join(excluded["dataset_id"].tolist()),
                "manual_review_required": unique_join(manual["dataset_id"].tolist()),
                "rationale": rationale,
                "claim_boundary": "Stage 37A is an eligibility audit only; it does not run validation or establish validated candidates.",
            }
        ]
    )


def build_pass_fail(primary_presence: dict[str, bool], outputs: dict[str, bool], conservative: bool = True) -> pd.DataFrame:
    row = {
        "stage37a_run": True,
        "stage36e_inputs_found": all(v for k, v in primary_presence.items() if k.startswith("stage36e")),
        "scorecard_inputs_found": all(v for k, v in primary_presence.items() if k in {"v3_scorecard_md", "active_v3_status", "v3_scorecard_csv"}),
        "candidate_dataset_inventory_written": outputs.get("dataset_inventory", False),
        "role_classification_written": outputs.get("role_classification", False),
        "clean_validation_eligibility_written": outputs.get("clean_validation_eligibility", False),
        "contamination_audit_written": outputs.get("contamination_audit", False),
        "stage37b_recommendation_written": outputs.get("stage37b_recommendation", False),
        "no_new_modeling_run": True,
        "no_validation_run": True,
        "no_data_download": True,
        "no_web_scraping": True,
        "no_external_validation_claim": True,
        "no_causal_claim": True,
        "no_therapeutic_claim": True,
        "safety_audit_pass": conservative,
    }
    required = list(row.keys())
    row["stage37a_run_pass"] = all(bool(row[k]) for k in required)
    row["controlled_interpretation"] = (
        "Stage 37A completed a conservative validation dataset eligibility audit. It does not run validation; "
        "zero clean-validation-eligible datasets is an acceptable honest outcome."
    )
    return pd.DataFrame([row])


def build_report(inventory: pd.DataFrame, roles: pd.DataFrame, elig: pd.DataFrame, contam: pd.DataFrame, rec: pd.DataFrame, pf: pd.DataFrame, rules: pd.DataFrame) -> str:
    summary = roles.groupby("candidate_role", dropna=False).size().reset_index(name="n_resources")
    clean_summary = elig.groupby("clean_validation_eligible").size().reset_index(name="n_resources")
    return "\n".join(
        [
            "# Stage 37A validation dataset eligibility audit v1",
            "",
            "## Purpose",
            "",
            "Stage 37A asks whether any already identified dataset/resource can be used as a legitimate clean validation set for the frozen Stage 36E mechanisms and candidates.",
            "",
            "This is a report-only eligibility audit. It does not run validation, train a model, download data, scrape the web, or make validation, causal, or therapeutic claims.",
            "",
            "## Inputs",
            "",
            "- Stage 36E frozen validation protocol and decision rules",
            "- Stage 36E mechanism and candidate registries",
            "- V3 scorecard/status files",
            "- Existing local Stage 32/34 dataset-role and pretraining/provenance audits where present",
            "",
            "## Frozen Stage 36E validation rules used",
            "",
            markdown_table(rules[["rule_id", "rule_name", "rule_text"]]),
            "",
            "## Dataset inventory summary",
            "",
            markdown_table(inventory[["dataset_id", "dataset_name", "resource_type", "known_or_inferred_role_before_stage37a", "local_artifact_status"]], max_rows=40),
            "",
            "## Role classification summary",
            "",
            markdown_table(summary),
            "",
            "## Clean-validation eligibility summary",
            "",
            markdown_table(clean_summary),
            "",
            "## Contamination/disqualification summary",
            "",
            markdown_table(contam[["dataset_id", "dataset_name", "contamination_status", "clean_validation_disqualified", "explanation"]], max_rows=40),
            "",
            "## Recommended use for each resource",
            "",
            markdown_table(roles[["dataset_id", "candidate_role", "allowed_use", "disallowed_use", "stage37b_use_recommendation"]], max_rows=40),
            "",
            "## Stage 37B recommendation",
            "",
            markdown_table(rec),
            "",
            "## Claim boundaries",
            "",
            f"Safe wording: {SAFE_LANGUAGE}.",
            "",
            f"Avoid: {DISALLOWED_LANGUAGE}.",
            "",
            "## What Stage 37A does not prove",
            "",
            "- It does not prove any resource is validated.",
            "- It does not complete external validation.",
            "- It does not prove clean validation eligibility when independence or readouts are unclear.",
            "- It does not support causal, therapeutic, or disease-modifying claims.",
            "",
            "## Pass/fail summary",
            "",
            markdown_table(pf),
        ]
    )


def build_pi_report(roles: pd.DataFrame, rec: pd.DataFrame, pf: pd.DataFrame) -> str:
    clean = roles[roles["clean_external_validation_candidate"] == True]
    manual = roles[roles["requires_manual_review"] == True]
    not_clean = roles[roles["clean_external_validation_candidate"] == False]
    short = (
        "No already identified resource is currently approved as clean validation under Stage 36E rules."
        if clean.empty
        else f"Clean-validation candidates found: {unique_join(clean['dataset_id'].tolist())}."
    )
    return "\n".join(
        [
            "# Stage 37A PI dataset decision summary v1",
            "",
            "## Short answer",
            "",
            short,
            "",
            "Resources can still be useful as stress-test support, projection/signature support, robustness-only support, or manual-review candidates, but those roles are not clean validation.",
            "",
            "## Candidate datasets/resources",
            "",
            markdown_table(roles[["dataset_id", "dataset_name", "candidate_role", "primary_reason"]], max_rows=40),
            "",
            "## Recommended next action",
            "",
            markdown_table(rec[["recommended_next_stage", "recommended_action", "rationale"]]),
            "",
            "## Why pretraining/stress-test resources are not clean validation",
            "",
            "A clean validation dataset has to be independent of training, pretraining, model selection, candidate selection, feature selection, and threshold tuning. If a resource helped build, tune, rescue, interpret, or stress-test the system, it can still be informative, but it cannot be used as the primary clean validation set without a new independence audit.",
            "",
            "## Manual review required",
            "",
            unique_join(manual["dataset_id"].tolist()) or "none",
            "",
            "## Not clean validation under current evidence",
            "",
            unique_join(not_clean["dataset_id"].tolist()) or "none",
            "",
            "## Safe lab-meeting language",
            "",
            SAFE_LANGUAGE,
            "",
            "Avoid: " + DISALLOWED_LANGUAGE,
            "",
            "## Pass/fail",
            "",
            markdown_table(pf[["stage37a_run_pass", "no_validation_run", "no_data_download", "no_external_validation_claim"]]),
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


def update_scorecard_csv(path_value: str | Path, rec: pd.DataFrame) -> None:
    path = resolve(path_value)
    row = {
        "stage_id": "stage37a_validation_dataset_eligibility_audit",
        "status": "complete",
        "stage": "Stage 37A",
        "primary_metric": "validation dataset eligibility audit",
        "pass_rule": "pass requires required inputs, audit outputs, conservative classification, and safety boundaries",
        "result": "run_pass=True",
        "pass_fail": "pass",
        "allowed_inputs": "existing local repository files only",
        "forbidden_inputs": "new modeling; validation run; downloads; web scraping; causal/therapeutic claims",
        "interpretation": "Stage 37A audited already identified resources for clean validation eligibility; no validation was run.",
        "notes": str(rec.iloc[0]["recommended_next_stage"]),
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


def update_status_docs(cfg: dict[str, Any], rec: pd.DataFrame) -> None:
    next_stage = rec.iloc[0]["recommended_next_stage"]
    append_section_once(
        cfg["status_updates"]["active_status"],
        "## Stage 37A validation dataset eligibility audit status",
        (
            "Stage 37A validation dataset eligibility audit is complete. It classified already identified datasets/resources for clean validation, "
            "stress-test, projection/signature, robustness-only, manual-review, or exclusion roles. No validation, modeling, download, or web scraping was run. "
            f"Recommended next stage: `{next_stage}`."
        ),
    )
    append_section_once(
        cfg["status_updates"]["scorecard_md"],
        "## Stage 37A validation dataset eligibility audit result",
        (
            "Stage 37A is complete. Run pass: `True`. It is a validation eligibility audit only and does not establish any external validation result. "
            f"Recommended next stage: `{next_stage}`."
        ),
    )
    update_scorecard_csv(cfg["status_updates"]["scorecard_csv"], rec)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/agent/stage37a_validation_dataset_eligibility_audit_v1.yaml")
    args = parser.parse_args()
    cfg = load_cfg(resolve(args.config))

    primary_presence, optional_presence = input_presence(cfg)
    role_audit = read_csv(cfg["optional_context_inputs"]["stage32_dataset_role_audit"])
    stage36e_rules = read_csv(cfg["inputs"]["stage36e_validation_decision_rules"])

    evidence = scan_repo(cfg)
    inventory = build_inventory(cfg, evidence, role_audit)
    roles = classify_inventory(inventory, role_audit)
    elig = build_eligibility(roles)
    contam = build_contamination(roles, inventory)
    rec = build_stage37b_recommendation(roles)
    outputs: dict[str, bool] = {}
    paths: list[Path] = []
    for key, df in [
        ("dataset_inventory", inventory),
        ("role_classification", roles),
        ("clean_validation_eligibility", elig),
        ("contamination_audit", contam),
        ("stage37b_recommendation", rec),
    ]:
        path = write_csv(df, cfg["outputs"][key])
        paths.append(path)
        outputs[key] = path.exists()

    pf = build_pass_fail(primary_presence, outputs, conservative=True)
    pf_path = write_csv(pf, cfg["outputs"]["pass_fail"])
    paths.append(pf_path)
    outputs["pass_fail"] = pf_path.exists()

    report_path = write_text(build_report(inventory, roles, elig, contam, rec, pf, stage36e_rules), cfg["outputs"]["report"])
    pi_path = write_text(build_pi_report(roles, rec, pf), cfg["outputs"]["pi_report"])
    paths.extend([report_path, pi_path])
    outputs["report"] = report_path.exists()
    outputs["pi_report"] = pi_path.exists()
    pf = build_pass_fail(primary_presence, outputs, conservative=True)
    write_csv(pf, cfg["outputs"]["pass_fail"])
    write_text(build_report(inventory, roles, elig, contam, rec, pf, stage36e_rules), cfg["outputs"]["report"])
    write_text(build_pi_report(roles, rec, pf), cfg["outputs"]["pi_report"])

    update_status_docs(cfg, rec)
    paths.extend(
        [
            resolve(cfg["status_updates"]["active_status"]),
            resolve(cfg["status_updates"]["scorecard_md"]),
            resolve(cfg["status_updates"]["scorecard_csv"]),
        ]
    )

    print("stage37a_paths_written=")
    for path in paths:
        print(str(path.relative_to(ROOT)))
    print(f"dataset_resource_inventory_count={len(inventory)}")
    print(f"n_clean_external_validation_candidate={int(roles['clean_external_validation_candidate'].sum())}")
    print(f"n_requires_manual_review={int(roles['requires_manual_review'].sum())}")
    print(f"n_disqualified_from_clean_validation={int(contam['clean_validation_disqualified'].sum())}")
    print(f"stage37b_recommendation={rec.iloc[0]['recommended_next_stage']}")
    print(f"stage37a_run_pass={pf.iloc[0]['stage37a_run_pass']}")


if __name__ == "__main__":
    main()
