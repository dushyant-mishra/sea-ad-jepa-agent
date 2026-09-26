#!/usr/bin/env python3
"""V43 design-only firewall. Does not read biological data or authorize training."""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "docs/agent/JEPA_V43_TEAM_ARCHITECTURE_COMPARISON_CONTRACT_20260926.json"
REQUIRED_ARMS = {
    "A_SINGLE_RICH": (["RICH_NATIVE"], ["SINGLE_MASKED"]),
    "B_SHARED_MULTIPLE_HEADS": (
        ["COMMON_CORE_HEAD", "FINE_NATIVE_HEAD", "CONDITIONAL_RARE_HEAD"],
        ["SHARED_CORE_FINE_RARE_HEADS"],
    ),
    "C_COMPLEMENTARY_TEACHER_TEAM": (
        ["INDEPENDENT_COMMON_CORE", "INDEPENDENT_FINE_NATIVE",
         "CONDITIONAL_INDEPENDENT_RARE"],
        ["CORE_STUDENT", "FINE_RARE_STUDENT"],
    ),
}
REQUIRED_CONTROLS = {
    "STUDENT_Q_COUNT_COUNTERFACTUAL_INVARIANCE",
    "FULL_LIBRARY_DENOMINATOR_LEAKAGE_EXPECTED_FAIL",
    "STRUCTURAL_UNMEASURED_NE_ZERO",
    "DONOR_DUPLICATION_NO_PSEUDOREPLICATION",
    "GENERIC_CELL_ONLY_COMPARATOR",
    "QUERY_IDENTITY_ONLY_COMPARATOR",
    "TECHNICAL_ONLY_COMPARATOR",
    "QUERY_EXCHANGEABILITY",
    "CAPACITY_AND_COMPUTE_MATCHED_SINGLE_TEACHER",
    "RARE_EXPERT_VS_SHUFFLED_EXPERT",
    "RARE_DONOR_RECURRENCE",
    "SPECIALIST_NONCOLLAPSE",
    "TEACHER_DISAGREEMENT_DOMAIN_AUDIT",
    "REAL_VS_IDENTICAL_GRAPH_NEGATIVE_CONTROL",
    "ORIGINAL_EXECUTED_TEST_EVIDENCE",
}
REQUIRED_UNSET = (
    "teacher_query_scalar_policy", "teacher_head_independent_biological_falsifiers",
    "rare_state_eligibility_and_recurrence", "independent_biology_measurement",
    "train_population", "donor_split", "head_loss_weights",
    "model_capacities_and_compute", "masking_budgets", "selection_thresholds",
    "control_margins",
)
REQUIRED_FALSE = (
    "execution_authorized", "training_authorized", "audit_b_n1_opened",
    "d_shared_g5_opened", "protected_full104_outcomes_opened",
    "scientific_target_selected", "architecture_selected",
)

def verify(x: dict) -> None:
    def require(condition: bool, why: str) -> None:
        if not condition:
            raise ValueError(why)
    require(x.get("schema") == "JEPA_V43_TEAM_ARCHITECTURE_COMPARISON_NONAUTHORIZING_V1", "schema")
    a = x.get("authority")
    require(type(a) is dict, "authority must be a mapping")
    for name in REQUIRED_FALSE:
        require(a.get(name) is False, f"attempted authority elevation: {name}")
    for name in REQUIRED_UNSET:
        require(x.get(name) == "UNSET_REQUIRES_APPROVAL", f"unapproved choice: {name}")
    require(x.get("student_query_scalar_policy") == "MUST_EXCLUDE_DIRECT_SCALAR_AND_ALL_DERIVED_LEAKAGE", "student q firewall")
    require(x.get("physically_executed_current_v5") is False, "invented physical execution")
    h=x.get("historical_roles", {})
    require(h.get("common_core_addresses")==17186 and h.get("canonical_addresses")==41238, "historical support")
    require(h.get("donors")==104 and h.get("operators")==42 and h.get("reader_fit_cells")==4553407, "historical population")
    for k in ("rare_head_historical_stage70_not_benchmark","stage71_real_vs_random_graph_lock_failed","pr163_competing_targets_unselected","pr169_versioned_repair_not_scientific_approval"):
        require(h.get(k) is True, f"historical false authority: {k}")
    arms = x.get("arms")
    require(type(arms) is list and len(arms) == 3, "exactly 3 arms")
    require({a.get("id") for a in arms} == set(REQUIRED_ARMS), "wrong arms")
    for arm in arms:
        t, s = REQUIRED_ARMS[arm["id"]]
        require(arm.get("teacher") == t and arm.get("student") == s, f"arm geometry: {arm['id']}")
        require(isinstance(arm.get("hypothesis"), str) and len(arm["hypothesis"]) > 30, "falsifiable arm description")
    controls = x.get("mandatory_controls")
    require(type(controls) is list and len(controls)==len(REQUIRED_CONTROLS) and set(controls)==REQUIRED_CONTROLS, "exact control list; no duplicates or omissions")
    rules = x.get("validity_rules", {})
    require(rules.get("unmeasured_gene_is_zero") is False, "unmeasured is not zero")
    for k in ("rare_head_missing_support_abstains","rare_donors_independent_unit","diagnostic_teacher_disagreement_retained","teacher_weights_update_only_post_verified_optimizer"):
        require(rules.get(k) is True, f"unsafe scientific semantics: {k}")

def main() -> None:
    verify(json.loads(CONTRACT.read_text(encoding="utf-8")))
    report=ROOT/"docs/agent/JEPA_V43_COMPLEMENTARY_TEACHER_STUDENT_RESEARCH_20260926.md"
    text=report.read_text(encoding="utf-8")
    for phrase in ("Stage69","Stage70","Stage71","#163","#169","UNSET_REQUIRES_APPROVAL","TRAINING=OFF","AUDIT_B_N1=UNOPENED"):
        if phrase not in text:
            raise ValueError(f"missing research provenance: {phrase}")
    print("V43_EXACT_THREE_ARMS_AND_15_MANDATORY_CONTROLS")
    print("V43_ALL_UNAPPROVED_PARAMETERS_UNSET_AND_ALL_AUTHORITIES_FALSE")
    print("V43_HISTORICAL_NEGATIVE_RESULTS_AND_PROVENANCE_PRESERVED")
if __name__=="__main__":
    main()
