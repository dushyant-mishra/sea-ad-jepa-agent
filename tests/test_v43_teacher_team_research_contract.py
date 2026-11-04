"""Mutation controls for V43 design-only comparison; no data access or training."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/agent/verify_v43_teacher_team_research_contract.py"
spec = importlib.util.spec_from_file_location("v43_contract", SCRIPT)
v43 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v43)
BASE = json.loads((ROOT / "docs/agent/JEPA_V43_TEAM_ARCHITECTURE_COMPARISON_CONTRACT_20260926.json").read_text())

class DesignContractRedTeam(unittest.TestCase):
    def test_authorized_original_fixture_stays_research_only(self):
        v43.verify(copy.deepcopy(BASE))

    def fail_mutation(self, mutation, fragment):
        modified = copy.deepcopy(BASE)
        mutation(modified)
        with self.assertRaisesRegex(ValueError, fragment):
            v43.verify(modified)

    def test_train_flag(self):
        self.fail_mutation(lambda x: x["authority"].update(training_authorized=True), "training_authorized")

    def test_execution_flag(self):
        self.fail_mutation(lambda x: x["authority"].update(execution_authorized=True), "execution_authorized")

    def test_n1_flag(self):
        self.fail_mutation(lambda x: x["authority"].update(audit_b_n1_opened=True), "audit_b_n1_opened")

    def test_protected_outcomes(self):
        self.fail_mutation(lambda x: x["authority"].update(protected_full104_outcomes_opened=True), "protected_full104_outcomes_opened")

    def test_selected_teacher_target(self):
        self.fail_mutation(lambda x: x["authority"].update(scientific_target_selected=True), "scientific_target_selected")

    def test_architecture_selection(self):
        self.fail_mutation(lambda x: x["authority"].update(architecture_selected=True), "architecture_selected")

    def test_historical_mask_rate_spillover(self):
        self.fail_mutation(lambda x: x.update(masking_budgets="0.40"), "masking_budgets")

    def test_historical_model_width_spillover(self):
        self.fail_mutation(lambda x: x.update(model_capacities_and_compute="160"), "model_capacities_and_compute")

    def test_fake_current_physical_execution(self):
        self.fail_mutation(lambda x: x.update(physically_executed_current_v5=True), "invented physical execution")

    def test_unmeasured_gene_as_zero(self):
        self.fail_mutation(lambda x: x["validity_rules"].update(unmeasured_gene_is_zero=True), "unmeasured is not zero")

    def test_rare_missing_support_forced_to_predict(self):
        self.fail_mutation(lambda x: x["validity_rules"].update(rare_head_missing_support_abstains=False), "rare_head_missing_support_abstains")

    def test_rare_cells_counted_as_replicated_donors(self):
        self.fail_mutation(lambda x: x["validity_rules"].update(rare_donors_independent_unit=False), "rare_donors_independent_unit")

    def test_teacher_disagreement_suppressed(self):
        self.fail_mutation(lambda x: x["validity_rules"].update(diagnostic_teacher_disagreement_retained=False), "diagnostic_teacher_disagreement_retained")

    def test_teacher_update_before_student_step(self):
        self.fail_mutation(lambda x: x["validity_rules"].update(teacher_weights_update_only_post_verified_optimizer=False), "teacher_weights_update_only_post_verified_optimizer")

    def test_omit_rare_control(self):
        self.fail_mutation(lambda x: x["mandatory_controls"].remove("RARE_DONOR_RECURRENCE"), "exact control list")

    def test_duplicate_control_as_false_coverage(self):
        def mutate(x):
            x["mandatory_controls"].remove("RARE_DONOR_RECURRENCE")
            x["mandatory_controls"].append("QUERY_EXCHANGEABILITY")
        self.fail_mutation(mutate, "exact control list")

    def test_remove_capacity_control(self):
        self.fail_mutation(lambda x: x["mandatory_controls"].remove("CAPACITY_AND_COMPUTE_MATCHED_SINGLE_TEACHER"), "exact control list")

    def test_remove_q_denominator_leakage_control(self):
        self.fail_mutation(lambda x: x["mandatory_controls"].remove("FULL_LIBRARY_DENOMINATOR_LEAKAGE_EXPECTED_FAIL"), "exact control list")

    def test_remove_independent_test_execution_evidence(self):
        self.fail_mutation(lambda x: x["mandatory_controls"].remove("ORIGINAL_EXECUTED_TEST_EVIDENCE"), "exact control list")

    def test_rewrite_single_teacher_as_multi_teacher(self):
        self.fail_mutation(lambda x: x["arms"][0]["teacher"].append("UNAPPROVED_TEACHER"), "arm geometry")

    def test_erase_historical_stage71_negative(self):
        self.fail_mutation(lambda x: x["historical_roles"].update(stage71_real_vs_random_graph_lock_failed=False), "historical false authority")

    def test_change_common_core_support(self):
        self.fail_mutation(lambda x: x["historical_roles"].update(common_core_addresses=41238), "historical support")

    def test_allow_student_q_derivative_leakage(self):
        self.fail_mutation(lambda x: x.update(student_query_scalar_policy="EXCLUDE_TOKEN_AFTER_FULL_LIBRARY_NORMALIZATION"), "student q firewall")

    def test_invent_teacher_q_policy(self):
        self.fail_mutation(lambda x: x.update(teacher_query_scalar_policy="ALWAYS_EXCLUDE_Q"), "teacher_query_scalar_policy")

if __name__ == "__main__":
    unittest.main()
