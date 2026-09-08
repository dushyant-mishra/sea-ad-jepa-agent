from __future__ import annotations

import pytest
import torch

from sea_ad_jepa.v4.teacher_student_relational import (
    CURRENT_FROZEN_TRAINING_EVIDENCE_LEVEL,
    EVIDENCE_LEVELS,
    CollapseCalibration,
    effective_rank,
    enforce_collapse_calibration,
    fine_matched_null_permutation,
    geometry_health,
    hidden_fraction_for_evidence,
    neighborhood_overlap,
    relational_batch_contract,
    relational_geometry_loss,
)


def _states() -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    torch.manual_seed(7)
    teacher = torch.randn(8, 160)
    student = teacher.clone().requires_grad_(True)
    groups = torch.tensor([0, 0, 0, 0, 1, 1, 1, 1], dtype=torch.int64)
    return teacher, student, groups


def test_relational_representation_is_direct_cell_state_and_identity_geometry_is_zero_loss() -> None:
    teacher, student, groups = _states()
    report = relational_geometry_loss(teacher, student, groups)
    assert report["pair_count"].item() == 12
    assert float(report["loss"]) == pytest.approx(0.0, abs=1e-7)
    report["loss"].backward()
    assert student.grad is not None
    assert torch.isfinite(student.grad).all()


def test_relational_loss_detects_geometry_change() -> None:
    teacher, student, groups = _states()
    with torch.no_grad():
        student[0] = student[0] * -4.0
    report = relational_geometry_loss(teacher, student, groups)
    assert float(report["loss"]) > 0.0


def test_relational_pairs_never_cross_donor_operator_group() -> None:
    teacher, student, groups = _states()
    baseline = relational_geometry_loss(teacher, student, groups)
    changed = student.detach().clone()
    # Translate the second group as a whole. Group centering makes the relational
    # loss invariant to cross-group location; there are no cross-group pairs.
    changed[4:] += 1000.0
    translated = relational_geometry_loss(teacher, changed, groups)
    assert float(translated["loss"]) == pytest.approx(float(baseline["loss"]), abs=1e-6)


def test_collapsed_teacher_geometry_is_rejected() -> None:
    teacher = torch.ones(8, 160)
    student = torch.ones(8, 160)
    groups = torch.tensor([0, 0, 0, 0, 1, 1, 1, 1], dtype=torch.int64)
    with pytest.raises(ValueError, match="zero pairwise spread"):
        relational_geometry_loss(teacher, student, groups)


def test_health_reports_variance_spread_and_effective_rank() -> None:
    teacher, _, groups = _states()
    health = geometry_health(teacher, groups)
    assert float(health["variance"]) > 0
    assert float(health["pairwise_spread"]) > 0
    assert float(health["effective_rank"]) > 1


def test_collapse_thresholds_have_no_implicit_defaults() -> None:
    teacher, student, groups = _states()
    teacher_health = geometry_health(teacher, groups)
    student_health = geometry_health(student, groups)
    calibration = CollapseCalibration(
        min_variance_ratio=0.95,
        min_spread_ratio=0.95,
        min_effective_rank_ratio=0.95,
    )
    ratios = enforce_collapse_calibration(teacher_health, student_health, calibration)
    assert all(value == pytest.approx(1.0, abs=1e-6) for value in ratios.values())

    collapsed = student.detach().clone() * 0.01
    collapsed_health = geometry_health(collapsed, groups)
    with pytest.raises(RuntimeError, match="variance"):
        enforce_collapse_calibration(teacher_health, collapsed_health, calibration)


def test_fine_matched_null_is_within_stratum_and_has_no_fixed_points() -> None:
    strata = torch.tensor([0, 0, 0, 1, 1, 1], dtype=torch.int64)
    perm = fine_matched_null_permutation(strata, seed=19)
    assert not bool((perm == torch.arange(len(perm))).any())
    assert torch.equal(strata[perm], strata)


def test_fine_matched_null_rejects_singleton_stratum() -> None:
    strata = torch.tensor([0, 0, 1], dtype=torch.int64)
    with pytest.raises(ValueError, match="fewer than 2"):
        fine_matched_null_permutation(strata, seed=19)


def test_neighborhood_overlap_is_one_for_identical_geometry() -> None:
    teacher, student, groups = _states()
    assert float(neighborhood_overlap(teacher, student, groups, k=2)) == pytest.approx(1.0)


def test_evidence_schedule_is_exact_and_100_percent_is_not_a_hidden_target_training_dose() -> None:
    assert EVIDENCE_LEVELS == (20, 40, 60, 80, 100)
    assert CURRENT_FROZEN_TRAINING_EVIDENCE_LEVEL == 60
    assert [hidden_fraction_for_evidence(x) for x in EVIDENCE_LEVELS] == pytest.approx(
        [0.8, 0.6, 0.4, 0.2, 0.0]
    )
    with pytest.raises(ValueError):
        hidden_fraction_for_evidence(50)


def test_relational_batch_contract_requires_exact_8_by_16_geometry() -> None:
    donors = []
    operators = []
    for group in range(8):
        donors.extend([f"d{group}"] * 16)
        operators.extend([f"o{group}"] * 16)
    report = relational_batch_contract(donors, operators)
    assert report["cells"] == 128
    assert report["groups"] == 8
    assert report["cells_per_group"] == 16

    bad = donors.copy()
    bad[0] = "other"
    with pytest.raises(RuntimeError):
        relational_batch_contract(bad, operators)


def test_effective_rank_zero_for_complete_collapse() -> None:
    assert float(effective_rank(torch.ones(8, 160))) == 0.0
