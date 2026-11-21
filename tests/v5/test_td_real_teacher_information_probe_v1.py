from __future__ import annotations

import math

import pytest

import scripts.v5.td_real_teacher_information_probe_v1 as G


def _fixture_teacher_private(n_donors: int = 8):
    donor_ids, student_x, teacher_x, y = [], [], [], []
    pattern = [-1.0, -0.3, 0.3, 1.0]
    for d in range(n_donors):
        for value in pattern:
            donor_ids.append(f"D{d:02d}")
            student_x.append([0.0])
            teacher_x.append([value])
            y.append([value])
    return donor_ids, student_x, teacher_x, y


def _fixture_no_private(n_donors: int = 8):
    donor_ids, student_x, teacher_x, y = [], [], [], []
    pattern = [-1.0, -0.3, 0.3, 1.0]
    for d in range(n_donors):
        for value in pattern:
            donor_ids.append(f"D{d:02d}")
            student_x.append([value])
            teacher_x.append([value])
            y.append([value])
    return donor_ids, student_x, teacher_x, y


def test_lambda_family_is_exact_closed_25_value_power_of_two_grid():
    assert G.LAMBDAS == tuple(2.0 ** k for k in range(-12, 13))
    assert len(G.LAMBDAS) == 25


def test_donor_balanced_mse_gives_each_donor_equal_weight():
    donor_ids = ["A", "A", "A", "B"]
    y_true = [[0.0], [0.0], [0.0], [0.0]]
    y_pred = [[1.0], [1.0], [1.0], [3.0]]
    out = G.donor_balanced_mse(donor_ids, y_true, y_pred)
    assert out["donor_mse"] == {"A": 1.0, "B": 9.0}
    assert out["mean_donor_mse"] == 5.0


def test_training_only_standardization_maps_constant_columns_to_zero():
    fit = G.fit_standardizer([[2.0], [2.0], [2.0]])
    assert fit["mean"] == [2.0]
    assert fit["scale"] == [1.0]
    assert G.apply_standardizer([[2.0], [100.0]], fit) == [[0.0], [98.0]]


def test_zero_variance_required_target_is_not_estimable():
    donor_ids = ["A", "A", "B", "B", "C", "C"]
    x = [[0.0], [1.0], [0.0], [1.0], [0.0], [1.0]]
    y = [[1.0]] * 6
    out = G.nested_donor_probe(donor_ids, x, y)
    assert out["status"] == "NOT_ESTIMABLE_ZERO_VARIANCE_TARGET"


def test_teacher_private_known_truth_world_passes_at_exact_sign_resolution():
    donor_ids, student_x, teacher_x, y = _fixture_teacher_private(8)
    out = G.compare_teacher_student(donor_ids=donor_ids, student_x=student_x, teacher_x=teacher_x, y=y, alpha=0.01)
    assert out["status"] == "PASS"
    assert len(out["donor_deltas"]) == 8
    assert all(row["delta"] > 0.0 for row in out["donor_deltas"])
    assert out["sign_test"]["n_positive_donors"] == 8
    assert out["sign_test"]["resolution_estimable"] is True


def test_no_private_signal_world_does_not_false_pass():
    donor_ids, student_x, teacher_x, y = _fixture_no_private(8)
    out = G.compare_teacher_student(donor_ids=donor_ids, student_x=student_x, teacher_x=teacher_x, y=y, alpha=0.01)
    assert out["status"] in {"FAIL", "NOT_ESTIMABLE"}
    assert all(math.isclose(row["delta"], 0.0, abs_tol=1e-12) for row in out["donor_deltas"])


def test_underpowered_positive_world_is_not_estimable_not_fail():
    donor_ids, student_x, teacher_x, y = _fixture_teacher_private(7)
    out = G.compare_teacher_student(donor_ids=donor_ids, student_x=student_x, teacher_x=teacher_x, y=y, alpha=0.01)
    assert out["status"] == "NOT_ESTIMABLE"
    assert out["sign_test"]["resolution_estimable"] is False


def test_teacher_and_student_get_identical_search_rights_but_select_independently():
    donor_ids, student_x, teacher_x, y = _fixture_teacher_private(8)
    out = G.compare_teacher_student(donor_ids=donor_ids, student_x=student_x, teacher_x=teacher_x, y=y, alpha=0.01)
    for arm in ("student", "teacher"):
        assert out["arms"][arm]["lambda_family"] == list(G.LAMBDAS)
        assert out["arms"][arm]["outer_donors"] == sorted(set(donor_ids))
        assert all(record["selected_lambda"] in G.LAMBDAS for record in out["arms"][arm]["outer_results"])


def test_known_truth_qualification_requires_positive_negative_and_underpowered_worlds():
    out = G.qualify_known_truth_probe(alpha=0.01)
    assert out["status"] == "PASS_KNOWN_TRUTH_G6_PROBE_QUALIFICATION"
    assert out["worlds"]["TEACHER_PRIVATE_SIGNAL_PRESENT"] == "PASS"
    assert out["worlds"]["NO_TEACHER_PRIVATE_SIGNAL"] in {"FAIL", "NOT_ESTIMABLE"}
    assert out["worlds"]["UNDERPOWERED_TEACHER_PRIVATE_SIGNAL"] == "NOT_ESTIMABLE"
    assert out["human_fail_semantics_qualified"] is True
    assert out["authority"] == {"value_read_authorized": False, "real_tournament_authorized": False, "target_selection_authorized": False, "representation_selection_authorized": False, "td60_authorized": False, "stage4_authorized": False, "training_authorized": False}


def test_boolean_or_nonfinite_inputs_fail_closed():
    with pytest.raises(G.TeacherInformationProbeError):
        G.fit_standardizer([[True]])
    with pytest.raises(G.TeacherInformationProbeError):
        G.fit_standardizer([[float("nan")]])
