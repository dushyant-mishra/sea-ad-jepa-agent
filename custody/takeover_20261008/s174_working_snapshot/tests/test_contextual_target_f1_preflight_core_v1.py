from types import SimpleNamespace
import unittest
import json
import tempfile
from pathlib import Path

import numpy as np
import torch

from scripts.v4.contextual_target_f1_preflight_core_v1 import evidence_mask, lean_query_local, validate_authority_file, validate_fixture_binding, validate_runtime_facts, validate_encoder_architecture, validate_semantic_root


class RecordingEncoder:
    def __init__(self):
        self.views = []

    def __call__(self, *, gene_ids, expression, measurement_mask, hidden_target_mask, view):
        self.views.append(view)
        width = 3
        states = torch.arange(expression.shape[0] * expression.shape[1] * width, dtype=torch.float32).reshape(expression.shape[0], expression.shape[1], width)
        return SimpleNamespace(gene_states=states)


class PreflightCoreTests(unittest.TestCase):
    def test_authority_and_fixture_tampering_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "authority.bin"; path.write_bytes(b"good")
            import hashlib
            expected = hashlib.sha256(b"good").hexdigest()
            validate_authority_file(path, expected)
            path.write_bytes(b"bad")
            with self.assertRaises(RuntimeError): validate_authority_file(path, expected)
        fixture = {"selected": [{"x": 1}]}
        from scripts.v4.contextual_target_f1_preflight_core_v1 import canonical_json_sha
        fixture["membership_root_sha256"] = canonical_json_sha(fixture["selected"])
        validate_fixture_binding(fixture)
        fixture["selected"][0]["x"] = 2
        with self.assertRaises(RuntimeError): validate_fixture_binding(fixture)
        plan = {"reader_rows": [{"cell": "a"}]}
        from scripts.v4.contextual_target_f1_preflight_core_v1 import canonical_json_sha
        plan["reader_plan_root_sha256"] = canonical_json_sha(plan)
        validate_semantic_root(plan, "reader_plan_root_sha256")
        plan["reader_rows"][0]["cell"] = "b"
        with self.assertRaises(RuntimeError): validate_semantic_root(plan, "reader_plan_root_sha256")

    def test_wsl_cuda_environment_fails_closed(self):
        base = {"is_wsl": True, "canonical_mount": "/mnt/d/Jepa project", "cuda_available": True, "cuda_device_count": 1, "nvidia_smi_ok": True, "source_hashes_match": True}
        self.assertTrue(validate_runtime_facts(base))
        for field in ("is_wsl", "cuda_available"):
            with self.assertRaises(RuntimeError): validate_runtime_facts({**base, field: False})
        with self.assertRaises(RuntimeError): validate_runtime_facts({**base, "canonical_mount": "/tmp/copy"})
        with self.assertRaises(RuntimeError): validate_runtime_facts({**base, "canonical_mount": "/mnt/d/Jepa project-copy"})

    def test_architecture_is_explicitly_41238(self):
        from scripts.v4.contextual_target_f1_preflight_core_v1 import F1_ARCHITECTURE
        self.assertEqual(F1_ARCHITECTURE["vocabulary_size"], 41238)
        self.assertNotEqual(F1_ARCHITECTURE["vocabulary_size"], 4096)
        good = SimpleNamespace(
            tokenizer=SimpleNamespace(vocabulary_size=41238, width=160, gene_identity=SimpleNamespace(embedding_dim=48)),
            blocks=[SimpleNamespace(attention=SimpleNamespace(heads=4)) for _ in range(6)],
            gradient_checkpointing=False, training=False,
        )
        self.assertTrue(validate_encoder_architecture(good))
        good.tokenizer.vocabulary_size = 4096
        with self.assertRaises(RuntimeError):
            validate_encoder_architecture(good)
    def test_teacher_role_uses_reviewed_student_encoder_view(self):
        encoder = RecordingEncoder()
        expression = torch.tensor([[0.0, 1.0, 2.0, 3.0]], dtype=torch.float32)
        state = torch.tensor([[1, 1, 1, 0]], dtype=torch.uint8)
        evidence = torch.tensor([[True, False, True, False]])
        query = torch.tensor([1], dtype=torch.long)

        lean_query_local(encoder, expression, state, evidence, query, "teacher")

        self.assertEqual(encoder.views, ["student"])

    def test_evidence_masks_are_nested_and_always_withhold_query(self):
        state = np.asarray([1, 1, 0, 2, 1, 1, 1, 0, 1], dtype=np.uint8)
        query = 1
        masks = [evidence_mask(state, "row#1", query, level) for level in (20, 40, 60, 80, 100)]
        self.assertTrue(all(not mask[query] for mask in masks))
        self.assertTrue(all(np.all(left <= right) for left, right in zip(masks, masks[1:])))
        self.assertTrue(np.array_equal(np.flatnonzero(masks[-1]), np.asarray([0, 4, 5, 6, 8])))


if __name__ == "__main__":
    unittest.main()
