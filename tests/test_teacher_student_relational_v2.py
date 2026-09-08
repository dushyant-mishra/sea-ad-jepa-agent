from __future__ import annotations

import pytest
import torch

from sea_ad_jepa.v4.prospective_relational_teacher_student_v2 import (
    CURRENT_FROZEN_TRAINING_EVIDENCE_LEVEL,
    EVIDENCE_LEVELS,
    RELATIONAL_BATCH_SIZE,
    RELATIONAL_GROUPS_PER_BATCH,
    RELATIONAL_GROUP_SIZE,
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


def test_v2_identity_geometry_is_zero_loss_and_student_is_differentiable() -> None:
    teacher, student, groups = _states()
    report = relational_geometry_loss(teacher, student, groups)
    assert report["pair_count"].item() == 12
    assert float(report["loss"].detach()) == pytest.approx(0.0, abs=1e-7)
    report["loss"].backward()
    assert student.grad is not None and torch.isfinite(student.grad).all()
    assert teacher.grad is None


def test_v2_relational_loss_detects_within_group_geometry_change() -> None:
    teacher, student, groups = _states()
    with torch.no_grad():
        student[0] *= -4.0
    assert float(relational_geometry_loss(teacher, student, groups)["loss"].detach()) > 0.0


def test_v2_cross_group_translation_cannot_enter_loss() -> None:
    teacher, student, groups = _states()
    baseline = relational_geometry_loss(teacher, student, groups)
    changed = student.detach().clone()
    changed[4:] += 1000.0
    translated = relational_geometry_loss(teacher, changed, groups)
    assert float(translated["loss"].detach()) == pytest.approx(float(baseline["loss"].detach()), abs=1e-6)


def test_v2_rejects_fully_collapsed_teacher() -> None:
    teacher = torch.ones(8, 160)
    student = torch.ones(8, 160)
    groups = torch.tensor([0, 0, 0, 0, 1, 1, 1, 1], dtype=torch.int64)
    with pytest.raises(ValueError, match="zero norm|zero pairwise spread"):
        relational_geometry_loss(teacher, student, groups)


def test_v2_rejects_one_collapsed_teacher_group_even_if_other_groups_are_rich() -> None:
    torch.manual_seed(4)
    teacher = torch.cat([torch.ones(4, 160), torch.randn(4, 160)], dim=0)
    student = teacher.clone()
    groups = torch.tensor([0, 0, 0, 0, 1, 1, 1, 1], dtype=torch.int64)
    with pytest.raises(ValueError, match="zero norm|zero pairwise spread"):
        relational_geometry_loss(teacher, student, groups)


def test_v2_rejects_zero_centered_vector_where_angle_is_undefined() -> None:
    torch.manual_seed(9)
    local = torch.randn(3, 160)
    fourth = local.mean(dim=0, keepdim=True)
    teacher = torch.cat([local, fourth], dim=0)
    student = teacher.clone()
    groups = torch.zeros(4, dtype=torch.int64)
    with pytest.raises(ValueError, match="angle is undefined"):
        relational_geometry_loss(teacher, student, groups)


def test_v2_health_is_per_group_and_no_pooled_rescue_is_possible() -> None:
    torch.manual_seed(2)
    teacher = torch.cat([torch.ones(4, 160)] + [torch.randn(4, 160) for _ in range(7)])
    student = teacher.clone()
    groups = torch.repeat_interleave(torch.arange(8, dtype=torch.int64), 4)
    th = geometry_health(teacher, groups)
    sh = geometry_health(student, groups)
    assert set(th) == set(range(8))
    assert float(th[0]["variance"]) == 0.0
    calibration = CollapseCalibration(0.9, 0.9, 0.9)
    with pytest.raises(RuntimeError, match="group=0"):
        enforce_collapse_calibration(th, sh, calibration)


def test_v2_healthy_groups_pass_teacher_relative_collapse_ratios() -> None:
    teacher, student, groups = _states()
    ratios = enforce_collapse_calibration(
        geometry_health(teacher, groups),
        geometry_health(student, groups),
        CollapseCalibration(0.95, 0.95, 0.95),
    )
    assert set(ratios) == {0, 1}
    assert all(value == pytest.approx(1.0, abs=1e-6) for group in ratios.values() for value in group.values())


def test_v2_one_student_group_below_calibration_cannot_be_rescued() -> None:
    torch.manual_seed(11)
    teacher = torch.randn(8, 160)
    student = teacher.clone()
    student[:4] *= 0.01
    groups = torch.tensor([0, 0, 0, 0, 1, 1, 1, 1], dtype=torch.int64)
    with pytest.raises(RuntimeError, match="group=0.*variance"):
        enforce_collapse_calibration(
            geometry_health(teacher, groups),
            geometry_health(student, groups),
            CollapseCalibration(0.95, 0.95, 0.95),
        )


def test_v2_fine_matched_null_is_within_stratum_and_has_no_fixed_points() -> None:
    strata = torch.tensor([0, 0, 0, 1, 1, 1], dtype=torch.int64)
    perm = fine_matched_null_permutation(strata, seed=19)
    assert not bool((perm == torch.arange(len(perm))).any())
    assert torch.equal(strata[perm], strata)
    assert torch.equal(perm, fine_matched_null_permutation(strata, seed=19))


def test_v2_fine_matched_null_rejects_singleton_stratum() -> None:
    with pytest.raises(ValueError, match="fewer than 2"):
        fine_matched_null_permutation(torch.tensor([0, 0, 1], dtype=torch.int64), seed=19)


def test_v2_neighborhood_overlap_is_one_for_identical_geometry() -> None:
    teacher, student, groups = _states()
    assert float(neighborhood_overlap(teacher, student, groups, k=2)) == pytest.approx(1.0)


def test_v2_evidence_schedule_is_exact_and_fractional_values_do_not_coerce() -> None:
    assert EVIDENCE_LEVELS == (20, 40, 60, 80, 100)
    assert CURRENT_FROZEN_TRAINING_EVIDENCE_LEVEL == 60
    assert [hidden_fraction_for_evidence(x) for x in EVIDENCE_LEVELS] == pytest.approx([0.8, 0.6, 0.4, 0.2, 0.0])
    with pytest.raises(ValueError):
        hidden_fraction_for_evidence(50)
    with pytest.raises(TypeError):
        hidden_fraction_for_evidence(20.9)
    with pytest.raises(TypeError):
        hidden_fraction_for_evidence(True)


def _exact_batch() -> tuple[list[str], list[str]]:
    donors: list[str] = []
    operators: list[str] = []
    for group in range(RELATIONAL_GROUPS_PER_BATCH):
        donors.extend([f"d{group}"] * RELATIONAL_GROUP_SIZE)
        operators.extend([f"o{group}"] * RELATIONAL_GROUP_SIZE)
    return donors, operators


def test_v2_batch_contract_is_unconditionally_exact_8_by_16() -> None:
    donors, operators = _exact_batch()
    report = relational_batch_contract(donors, operators)
    assert RELATIONAL_BATCH_SIZE == 128
    assert report == {
        "cells": 128,
        "groups": 8,
        "cells_per_group": 16,
        "grouping": "canonical_donor_id x operator_id",
    }
    bad = donors.copy()
    bad[0] = "other"
    with pytest.raises(RuntimeError):
        relational_batch_contract(bad, operators)


def test_v2_batch_contract_has_no_4_by_32_override_route() -> None:
    donors: list[str] = []
    operators: list[str] = []
    for group in range(4):
        donors.extend([f"d{group}"] * 32)
        operators.extend([f"o{group}"] * 32)
    with pytest.raises(RuntimeError, match="expected 8"):
        relational_batch_contract(donors, operators)
    with pytest.raises(TypeError):
        relational_batch_contract(donors, operators, group_size=32, groups_per_batch=4)


def test_v2_batch_contract_rejects_missing_identity_strings() -> None:
    donors, operators = _exact_batch()
    donors[0] = ""
    with pytest.raises(ValueError, match="donor identity"):
        relational_batch_contract(donors, operators)


def test_v2_requires_160d_finite_states_and_integer_group_ids_in_health() -> None:
    states = torch.randn(4, 159)
    groups = torch.zeros(4, dtype=torch.int64)
    with pytest.raises(ValueError, match="160-D"):
        geometry_health(states, groups)
    with pytest.raises(ValueError, match="integer tensor dtype"):
        geometry_health(torch.randn(4, 160), groups.float())


def test_v2_effective_rank_zero_for_complete_collapse() -> None:
    assert float(effective_rank(torch.ones(8, 160))) == 0.0


def test_v2_is_not_imported_or_called_by_active_production_runtime() -> None:
    from pathlib import Path
    runtime = Path("src/sea_ad_jepa/v4/teacher_student_runtime.py").read_text(encoding="utf-8")
    assert "prospective_relational_teacher_student_v2" not in runtime
    assert "relational_geometry_loss" not in runtime
