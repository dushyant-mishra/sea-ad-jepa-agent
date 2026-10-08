from __future__ import annotations

import pandas as pd


def skipped_benchmark_tables(reason: str, next_stage: str) -> dict[str, pd.DataFrame]:
    model_registry = pd.DataFrame(
        [
            {"candidate_id": "stage27c_reference", "feature_set_id": "stage27c_reference", "model_name": "reference", "training_status": "reference_only"},
            {"candidate_id": "stage39e_pca8_reference", "feature_set_id": "stage39e_pca8_reference", "model_name": "reference", "training_status": "reference_only"},
            {"candidate_id": "stage39h_context_reference", "feature_set_id": "stage39h_context_reference", "model_name": "reference", "training_status": "reference_only"},
            {"candidate_id": "stage41_safe_multimodal_candidate", "feature_set_id": "latent_plus_safe_multimodal", "model_name": "ridge", "training_status": "skipped_missing_safe_features"},
        ]
    )
    decision = pd.DataFrame(
        [
            {
                "candidate_id": "stage41_safe_multimodal_candidate",
                "feature_set_id": "latent_plus_safe_multimodal",
                "model_name": "ridge",
                "feature_classes_used": "",
                "risk_tiers_used": "",
                "mean_pooled_oof_spearman": pd.NA,
                "delta_vs_stage27c": pd.NA,
                "delta_vs_stage39e_pca8": pd.NA,
                "delta_vs_stage39h_context": pd.NA,
                "lower_ci_above_stage27c": False,
                "lower_ci_above_material_threshold": False,
                "target_guard_pass": False,
                "abeta_guard_pass": False,
                "iba1_rescue_status": "not_tested_missing_safe_features",
                "negative_controls_pass": False,
                "proxy_leakage_risk_pass": False,
                "high_influence_donor_or_fold_flag": False,
                "benchmark_lock_eligible": False,
                "recommended_decision": "manual_feature_acquisition_required",
                "allowed_claim_language": "internal multimodal feature acquisition planning only",
                "prohibited_claim_language": "external validation; causal; therapeutic; gene-ablation; disease-modifying claims",
                "recommended_next_stage": next_stage,
                "reason": reason,
            }
        ]
    )
    empty_cols = {
        "oof_results": ["candidate_id", "target", "fold_id", "donor_id", "y_true", "y_pred", "training_status"],
        "target_level_results": ["candidate_id", "target", "target_oof_spearman", "training_status"],
        "delta_vs_references": ["candidate_id", "delta_vs_stage27c", "delta_vs_stage39e_pca8", "delta_vs_stage39h_context", "training_status"],
        "bootstrap_ci": ["candidate_id", "ci_lower_95", "ci_upper_95", "training_status"],
        "fold_sensitivity": ["candidate_id", "fold_id", "fold_oof_spearman", "training_status"],
        "donor_influence_audit": ["candidate_id", "donor_id", "high_influence_flag", "training_status"],
        "target_guard_audit": ["candidate_id", "target", "target_guard_pass", "training_status"],
        "abeta_guard_audit": ["candidate_id", "abeta_guard_pass", "training_status"],
        "iba1_rescue_audit": ["candidate_id", "iba1_rescue_status", "training_status"],
        "negative_control_results": ["candidate_id", "control_type", "control_pass", "training_status"],
        "proxy_leakage_decision": ["candidate_id", "proxy_leakage_risk_pass", "decision", "training_status"],
    }
    tables = {"model_registry": model_registry, "benchmark_lock_decision": decision}
    for name, cols in empty_cols.items():
        tables[name] = pd.DataFrame([{col: ("skipped_missing_safe_features" if col == "training_status" else pd.NA) for col in cols}])
    tables["proxy_leakage_decision"]["decision"] = "no safe feature matrix built; no training"
    return tables
