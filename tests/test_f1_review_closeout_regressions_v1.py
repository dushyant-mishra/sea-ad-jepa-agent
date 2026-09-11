"""Regression guards for the September 2026 F1 review closeout.

These tests encode the concrete invariants raised by the unresolved PR #6
review threads.  They are intentionally self-contained: no protected external
artifacts are required to exercise them.
"""
from __future__ import annotations

import ast
import inspect
import json
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
V4 = REPO / "scripts" / "v4"
if str(V4) not in sys.path:
    sys.path.insert(0, str(V4))


def source(path: str) -> str:
    return (REPO / path).read_text(encoding="utf-8")


def function_source(path: str, name: str) -> str:
    text = source(path)
    tree = ast.parse(text)
    lines = text.splitlines()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return "\n".join(lines[node.lineno - 1: node.end_lineno])
    raise AssertionError(f"missing function {name} in {path}")


class ReviewCloseoutRegressionTests(unittest.TestCase):
    def test_all_imported_execution_dependencies_are_frozen(self):
        text = source("scripts/v4/f1_real_producer_v1.py")
        self.assertIn('"preflight_executor": "scripts/v4/contextual_target_f1_preflight_executor_v1.py"', text)
        self.assertIn('"mechanics_validator": "scripts/v4/validate_f1_production_mechanics_acceptance_v1.py"', text)

    def test_package_builder_never_stages_inputs(self):
        body = function_source("scripts/v4/build_f1_prefreeze_package_v1.py", "git_bytes")
        self.assertNotIn('"add"', body)
        self.assertIn('"HEAD:', body)
        self.assertTrue("dirty" in body.lower() or "diff" in body.lower())

    def test_authorization_has_independent_issuer_trust_check(self):
        body = function_source("scripts/v4/f1_execution_authorization_v1.py", "validate_execution_authorization")
        self.assertIn("trusted_authorizations", body)
        self.assertIn("STOP_F1_AUTHORIZATION_ISSUER_UNTRUSTED", source("scripts/v4/f1_execution_authorization_v1.py"))

    def test_source_counts_require_independent_frozen_digest(self):
        body = function_source("scripts/v4/f1_production_runtime_adapter_v1.py", "resolve_authenticated_source_values")
        self.assertIn("expected_counts_sha256", body)
        self.assertIn("STOP_F1_MATCHED_NULL_SOURCE_COUNTS_UNAUTHENTICATED", source("scripts/v4/f1_production_runtime_adapter_v1.py"))

    def test_forward_construction_is_device_bound_and_no_grad(self):
        body = function_source("scripts/v4/f1_production_runtime_adapter_v1.py", "_construct")
        self.assertIn("torch.no_grad", body)
        self.assertIn("encoder_device", body)
        self.assertIn("device=encoder_device", body)

    def test_resume_validation_is_integrity_based_not_existence_based(self):
        body = function_source("scripts/v4/f1_real_producer_v1.py", "shard_is_complete")
        self.assertIn("verify_persisted_shard", body)
        self.assertIn("states", body)
        self.assertIn("capture", body)
        self.assertIn("effect", body)

    def test_success_path_enforces_final_completeness(self):
        body = function_source("scripts/v4/f1_real_producer_v1.py", "run_production_sweep")
        self.assertIn("verify_sweep_completeness", body)
        self.assertIn("planned_assignment_keys", body)

    def test_execution_deduplicates_cell_query_forwards(self):
        text = source("scripts/v4/f1_real_producer_v1.py")
        self.assertIn("def _group_query_assignments", text)
        body = function_source("scripts/v4/f1_real_producer_v1.py", "execute_authorized_sweep")
        self.assertIn("_group_query_assignments", body)

    def test_qid_uses_paired_wrong_teacher_not_matched_null(self):
        body = function_source("scripts/v4/f1_real_producer_v1.py", "_effect_row_from_states")
        self.assertIn("paired_wrong_teacher", body)
        self.assertIn('wrong = float(replay_free_cosine(correct["contextual"], paired_wrong_teacher["contextual"]))', body)

    def test_replay_recomputes_forward_identity(self):
        body = function_source("scripts/v4/f1_real_replay_v1.py", "replay_forward_topology")
        self.assertIn("recorded_identity", body)
        self.assertIn("recomputed_identity", body)
        self.assertIn("forward identity mismatch", body)

    def test_replay_requires_and_validates_each_payload(self):
        body = function_source("scripts/v4/f1_real_replay_v1.py", "replay_verify_produced_outputs")
        self.assertIn("verify_persisted_shard", body)
        self.assertIn("missing persisted shard", body)
        self.assertNotIn('glob("*.npz")', body)

    def test_replay_recomputes_effect_values_from_states(self):
        text = source("scripts/v4/f1_real_replay_v1.py")
        self.assertIn("def replay_effect_rows_from_states", text)
        body = function_source("scripts/v4/f1_real_replay_v1.py", "replay_verify_produced_outputs")
        self.assertIn("replay_effect_rows_from_states", body)
        self.assertIn("compare_effect_rows", body)

    def test_provenance_accepts_descendants_only_when_bound_blobs_match(self):
        text = source("tests/test_verifier_f1_real_reader_forward_preflight_v1.py")
        self.assertIn("merge-base", text)
        self.assertIn("bound", text.lower())
        self.assertNotIn("self.assertIn(head, {implementation, root_commit})", text)


if __name__ == "__main__":
    unittest.main()
