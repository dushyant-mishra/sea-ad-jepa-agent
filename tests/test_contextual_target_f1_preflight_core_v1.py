from types import SimpleNamespace
import unittest

import numpy as np
import torch

from scripts.v4.contextual_target_f1_preflight_core_v1 import evidence_mask, lean_query_local


class RecordingEncoder:
    def __init__(self):
        self.views = []

    def __call__(self, *, gene_ids, expression, measurement_mask, hidden_target_mask, view):
        self.views.append(view)
        width = 3
        states = torch.arange(expression.shape[0] * expression.shape[1] * width, dtype=torch.float32).reshape(expression.shape[0], expression.shape[1], width)
        return SimpleNamespace(gene_states=states)


class PreflightCoreTests(unittest.TestCase):
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
