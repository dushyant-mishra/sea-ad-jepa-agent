import copy
import unittest

from scripts.v4.validate_implementation_verifier_report_v1 import validate_report


def valid_report(verdict="PASS_IMPLEMENTATION_VERIFIER"):
    return {
        "schema": "jepa-implementation-verifier-report-v1", "gate": "fixture",
        "base_commit": "a" * 40, "implementation_commit": "b" * 40,
        "verifier_agent_identity": "independent-verifier", "controlling_contracts": ["contract.md"],
        "authority_hashes": {"contract.md": "c" * 64}, "changed_files": ["production.py"],
        "conclusion_bearing_symbols": ["production.endpoint"],
        "requirement_matrix": [{
            "requirement_id": "R1", "contract_source": "contract.md", "contract_text_or_formula": "A=cos(c,t)-cos(n,t)",
            "production_file": "production.py", "production_symbol": "endpoint", "production_lines_or_blob_sha": "d" * 64,
            "independent_check_method": "separate literal NumPy calculation", "independent_reference_file_or_inline_method": "verifier_test.py",
            "adversarial_test": "sign-flip", "mutation_attack": "M01_SIGN_FLIP", "applicable_mutations": ["M01_SIGN_FLIP"],
            "mutations_executed": ["M01_SIGN_FLIP"], "mutations_detected": ["M01_SIGN_FLIP"], "mutations_not_detected": [],
            "mutation_detected": True, "verdict": "PASS", "notes": "bounded synthetic"
        }],
        "independent_reference_summary": "derived from contract without production imports",
        "independent_reference_uses_production_helper": False,
        "verifier_tests": ["test_verifier_r1"], "mutation_tests": ["M01_SIGN_FLIP"],
        "production_tests_observed": ["test_production"], "coverage_complete": True,
        "independence_confirmed": True, "verifier_verdict": verdict,
        "stop_reason": None if verdict == "PASS_IMPLEMENTATION_VERIFIER" else "documented stop",
        "timestamp": "2026-09-03T00:00:00Z"
    }


class GovernanceValidatorTests(unittest.TestCase):
    def test_complete_pass_accepted(self): self.assertEqual(validate_report(valid_report())["verdict"], "PASS_IMPLEMENTATION_VERIFIER")
    def test_empty_matrix_rejected(self):
        r=valid_report(); r["requirement_matrix"]=[]
        with self.assertRaises(ValueError): validate_report(r)
    def test_missing_independent_reference_rejected(self):
        r=valid_report(); r["requirement_matrix"][0]["independent_check_method"]=""
        with self.assertRaises(ValueError): validate_report(r)
    def test_production_helper_as_reference_rejected(self):
        r=valid_report(); r["independent_reference_uses_production_helper"]=True
        with self.assertRaises(ValueError): validate_report(r)
    def test_zero_mutations_rejected(self):
        r=valid_report(); r["requirement_matrix"][0]["applicable_mutations"]=[]
        with self.assertRaises(ValueError): validate_report(r)
    def test_surviving_mutation_rejects_pass(self):
        r=valid_report(); q=r["requirement_matrix"][0]; q["mutations_not_detected"]=["M01_SIGN_FLIP"]; q["mutations_detected"]=[]; q["mutation_detected"]=False
        with self.assertRaises(ValueError): validate_report(r)
    def test_false_coverage_and_independence_reject_pass(self):
        for key in ("coverage_complete","independence_confirmed"):
            r=valid_report(); r[key]=False
            with self.assertRaises(ValueError): validate_report(r)
    def test_caller_pass_cannot_override_failure(self):
        r=valid_report(); r["requirement_matrix"][0]["verdict"]="STOP"
        with self.assertRaises(ValueError): validate_report(r)
    def test_valid_stop_preserved(self): self.assertEqual(validate_report(valid_report("STOP_IMPLEMENTATION_VERIFIER_TEST_FAILURE"))["verdict"], "STOP_IMPLEMENTATION_VERIFIER_TEST_FAILURE")
    def test_malformed_boolean_rejected(self):
        r=valid_report(); r["coverage_complete"]="true"
        with self.assertRaises(ValueError): validate_report(r)
    def test_empty_changed_or_symbols_rejected(self):
        for key in ("changed_files","conclusion_bearing_symbols"):
            r=valid_report(); r[key]=[]
            with self.assertRaises(ValueError): validate_report(r)


if __name__ == "__main__": unittest.main()
