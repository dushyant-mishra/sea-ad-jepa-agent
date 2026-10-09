from __future__ import annotations

import sys
from pathlib import Path

import torch

PROJECT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT / "src"))

from sea_ad_jepa.v4 import GeneSetMechanicsEncoder, derive_visibility_masks


def encoder() -> GeneSetMechanicsEncoder:
    torch.manual_seed(8102)
    model = GeneSetMechanicsEncoder()
    model.eval()
    return model


def test_visibility_truth_table_and_measured_zero_validity() -> None:
    measurement = torch.tensor([[True, True, True, False]])
    context = torch.tensor([[False, False, True, False]])
    masks = derive_visibility_masks(measurement, context)
    assert masks.student_valid.tolist() == [[True, True, False, False]]
    assert masks.target_valid.tolist() == [[True, True, True, False]]


def test_context_mask_cannot_apply_to_unmeasured_gene() -> None:
    try:
        derive_visibility_masks(torch.tensor([[True, False]]), torch.tensor([[False, True]]))
    except ValueError as exc:
        assert "only genuinely measured genes" in str(exc)
    else:
        raise AssertionError("unmeasured gene entered context masking")


def test_unmeasured_expression_cannot_change_student_or_target_and_gets_zero_attention() -> None:
    model = encoder()
    gene_ids = torch.tensor([[2, 8, 15]])
    measurement = torch.tensor([[True, True, False]])
    context = torch.zeros_like(measurement)
    baseline = torch.tensor([[0.5, 2.0, 0.0]])
    for view in ("student", "target"):
        reference = model(gene_ids, baseline, measurement, context, view)
        _, attention = model(
            gene_ids, baseline, measurement, context, view, return_attention=True
        )
        assert torch.count_nonzero(attention[..., 2]) == 0
        for excluded_value in (10.0, 1000.0):
            changed = baseline.clone()
            changed[0, 2] = excluded_value
            result = model(gene_ids, changed, measurement, context, view)
            torch.testing.assert_close(result, reference, rtol=0.0, atol=0.0)


def test_context_hidden_gene_is_excluded_from_student_but_visible_to_target() -> None:
    model = encoder()
    gene_ids = torch.tensor([[4, 10, 21]])
    measurement = torch.ones_like(gene_ids, dtype=torch.bool)
    context = torch.tensor([[False, True, False]])
    baseline = torch.tensor([[0.5, 0.0, 1.0]])
    changed = baseline.clone()
    changed[0, 1] = 100.0
    student = model(gene_ids, baseline, measurement, context, "student")
    _, student_attention = model(
        gene_ids, baseline, measurement, context, "student", return_attention=True
    )
    changed_student = model(gene_ids, changed, measurement, context, "student")
    torch.testing.assert_close(changed_student, student, rtol=0.0, atol=0.0)
    assert torch.count_nonzero(student_attention[..., 1]) == 0
    target = model(gene_ids, baseline, measurement, context, "target")
    _, target_attention = model(
        gene_ids, baseline, measurement, context, "target", return_attention=True
    )
    changed_target = model(gene_ids, changed, measurement, context, "target")
    assert torch.all(target_attention[..., 1] > 0)
    assert float((changed_target - target).abs().max()) > 1e-6


def test_measured_zero_participates_while_unmeasured_gene_does_not() -> None:
    model = encoder()
    gene_ids = torch.tensor([[12, 12]])
    expression = torch.tensor([[0.0, 999.0]])
    measurement = torch.tensor([[True, False]])
    context = torch.zeros_like(measurement)
    _, attention = model(
        gene_ids, expression, measurement, context, "student", return_attention=True
    )
    assert torch.all(attention[..., 0] == 1)
    assert torch.count_nonzero(attention[..., 1]) == 0
