from __future__ import annotations

from pathlib import Path

import pytest
import torch

from sea_ad_jepa.v4.teacher_student_relational_target_v2 import (
    CURRENT_FROZEN_TRAINING_EVIDENCE_LEVEL,
    EVIDENCE_LEVELS,
    CollapseCalibration,
    cosine_distance_matrix,
    effective_rank,
    enforce_collapse_calibration,
    enumerate_within_group_triplets,
    fine_matched_null_permutation,
    geometry_health,
    hidden_fraction_for_evidence,
    relational_batch_contract,
    scale_free_triplet_order_loss,
)

ROOT = Path(__file__).resolve().parents[1]


def _states() -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    torch.manual_seed(7)
    teacher = torch.randn(8, 160)
    student = teacher.clone().requires_grad_(True)
    groups = torch.tensor([0, 0, 0, 0, 1, 1, 1, 1], dtype=torch.int64)
    return teacher, student, groups


def test_target_is_scale_free_order_not_absolute_geometry_match() -> None:
    teacher, student, groups = _states()
    report = scale_free_triplet_order_loss(teacher, student, groups)
    assert report["triplet_count"].item() == 24
    assert report["order_agreement"].item() == pytest.approx(1.0)
    assert 0.0 < report["loss"].item() < 1.0
    report["loss"].backward()
    assert student.grad is not None and torch.isfinite(student.grad).all()


def test_positive_per_cell_rescaling_cannot_game_cosine_order_target() -> None:
    teacher, student, groups = _states()
    baseline = scale_free_triplet_order_loss(teacher, student, groups)
    scales_t = torch.linspace(0.2, 3.0, len(teacher))[:, None]
    scales_s = torch.linspace(3.0, 0.2, len(student))[:, None]
    rescaled = scale_free_triplet_order_loss(
        teacher * scales_t, student.detach() * scales_s, groups
    )
    assert rescaled["loss"].item() == pytest.approx(
        baseline["loss"].item(), abs=1e-6
    )
    assert rescaled["order_agreement"].item() == pytest.approx(1.0)


def test_reversing_a_teacher_relation_increases_loss_and_reduces_agreement() -> None:
    teacher, student, groups = _states()
    baseline = scale_free_triplet_order_loss(teacher, student, groups)
    changed = student.detach().clone()
    changed[0] = -changed[0]
    altered = scale_free_triplet_order_loss(teacher, changed, groups)
    assert altered["loss"].item() > baseline["loss"].item()
    assert altered["order_agreement"].item() < 1.0


def test_student_ties_are_penalized_not_silently_zero_loss() -> None:
    teacher, _, groups = _states()
    tied = torch.ones_like(teacher, requires_grad=True)
    report = scale_free_triplet_order_loss(teacher, tied, groups)
    assert (
        report["student_tie_count_on_teacher_resolved"].item()
        == report["teacher_resolved_count"].item()
    )
    assert report["loss"].item() == pytest.approx(1.0, abs=1e-6)


def test_zero_norm_cell_state_fails_closed() -> None:
    teacher, student, groups = _states()
    teacher[0].zero_()
    with pytest.raises(ValueError, match="zero-norm"):
        scale_free_triplet_order_loss(teacher, student, groups)


def test_triplets_never_cross_group_and_external_triplets_are_validated() -> None:
    teacher, student, groups = _states()
    triplets = enumerate_within_group_triplets(groups)
    assert torch.all(groups[triplets[:, 0]] == groups[triplets[:, 1]])
    assert torch.all(groups[triplets[:, 0]] == groups[triplets[:, 2]])

    bad = torch.tensor([[0, 1, 4]], dtype=torch.int64)
    with pytest.raises(ValueError, match="crosses relational group"):
        scale_free_triplet_order_loss(
            teacher, student, groups, frozen_triplets=bad
        )


def test_module_has_no_implicit_nearest_half_or_locality_selector() -> None:
    text = (
        ROOT / "src/sea_ad_jepa/v4/teacher_student_relational_target_v2.py"
    ).read_text()
    assert "nearest-half" not in text.lower()
    assert "selector_fraction" not in text
    assert "locality_fraction" not in text


def test_relational_target_is_not_active_in_current_production_update() -> None:
    runtime = (ROOT / "src/sea_ad_jepa/v4/teacher_student_runtime.py").read_text()
    assert "teacher_student_relational_target_v2" not in runtime
    assert "scale_free_triplet_order_loss" not in runtime


def test_health_and_external_collapse_calibration_remain_separate() -> None:
    teacher, student, groups = _states()
    teacher_health = geometry_health(teacher, groups)
    student_health = geometry_health(student, groups)
    calibration = CollapseCalibration(0.95, 0.95, 0.95)
    ratios = enforce_collapse_calibration(
        teacher_health, student_health, calibration
    )
    assert all(v == pytest.approx(1.0, abs=1e-6) for v in ratios.values())
    assert float(effective_rank(torch.ones(8, 160))) == 0.0


def test_fine_matched_null_is_within_stratum_and_deranged() -> None:
    strata = torch.tensor([0, 0, 0, 1, 1, 1], dtype=torch.int64)
    perm = fine_matched_null_permutation(strata, seed=19)
    assert not bool((perm == torch.arange(len(perm))).any())
    assert torch.equal(strata[perm], strata)


def test_evidence_schedule_and_group_geometry_require_external_values() -> None:
    assert EVIDENCE_LEVELS == (20, 40, 60, 80, 100)
    assert CURRENT_FROZEN_TRAINING_EVIDENCE_LEVEL == 60
    assert [hidden_fraction_for_evidence(x) for x in EVIDENCE_LEVELS] == pytest.approx(
        [0.8, 0.6, 0.4, 0.2, 0.0]
    )

    donors: list[str] = []
    operators: list[str] = []
    for group in range(8):
        donors.extend([f"d{group}"] * 16)
        operators.extend([f"o{group}"] * 16)
    report = relational_batch_contract(
        donors, operators, group_size=16, groups_per_batch=8
    )
    assert report["cells"] == 128
    with pytest.raises(TypeError):
        relational_batch_contract(donors, operators)  # type: ignore[call-arg]


def test_cosine_distance_is_symmetric_zero_diagonal() -> None:
    teacher, _, _ = _states()
    distance = cosine_distance_matrix(teacher)
    assert torch.allclose(distance, distance.T, atol=1e-7)
    assert torch.allclose(
        torch.diag(distance), torch.zeros(len(teacher)), atol=1e-6
    )
