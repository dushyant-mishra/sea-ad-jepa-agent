"""Outcome-blind matched diagnostic probe for real-TD G6.

This module qualifies a finite multi-output ridge diagnostic for teacher-vs-
student evidence. It does not define a biological target and does not authorize
human real-TD execution. A real target object must already be frozen elsewhere.
"""
from __future__ import annotations

import math
from collections.abc import Sequence

import numpy as np

from scripts.v5 import td_target_tournament_precision as P


class TeacherInformationProbeError(ValueError):
    pass


LAMBDAS = tuple(2.0 ** k for k in range(-12, 13))
NO_AUTHORITY = {
    "value_read_authorized": False,
    "real_tournament_authorized": False,
    "target_selection_authorized": False,
    "representation_selection_authorized": False,
    "td60_authorized": False,
    "stage4_authorized": False,
    "training_authorized": False,
}


def _matrix(value, label: str) -> np.ndarray:
    try:
        arr = np.asarray(value, dtype=object)
    except Exception as exc:  # pragma: no cover - numpy defensive path
        raise TeacherInformationProbeError(f"{label} must be matrix-like") from exc
    if arr.ndim != 2 or arr.shape[0] == 0 or arr.shape[1] == 0:
        raise TeacherInformationProbeError(f"{label} must be a nonempty 2D matrix")
    out = np.empty(arr.shape, dtype=float)
    for index, raw in np.ndenumerate(arr):
        if isinstance(raw, bool) or not isinstance(raw, (int, float, np.integer, np.floating)):
            raise TeacherInformationProbeError(f"{label} must contain finite numeric values")
        number = float(raw)
        if not math.isfinite(number):
            raise TeacherInformationProbeError(f"{label} must contain finite numeric values")
        out[index] = number
    return out


def _donors(value, n_rows: int) -> list[str]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence) or len(value) != n_rows:
        raise TeacherInformationProbeError("donor_ids must match matrix rows")
    donors: list[str] = []
    for donor in value:
        if not isinstance(donor, str) or not donor or donor != donor.strip() or "\0" in donor:
            raise TeacherInformationProbeError("donor_ids must be nonempty trimmed NUL-free strings")
        donors.append(donor)
    return donors


def fit_standardizer(x) -> dict:
    arr = _matrix(x, "x")
    mean = arr.mean(axis=0)
    scale = arr.std(axis=0, ddof=0)
    scale = np.where(scale == 0.0, 1.0, scale)
    return {"mean": mean.tolist(), "scale": scale.tolist(), "n_features": int(arr.shape[1])}


def apply_standardizer(x, fit: dict) -> list[list[float]]:
    arr = _matrix(x, "x")
    if not isinstance(fit, dict) or set(fit) != {"mean", "scale", "n_features"}:
        raise TeacherInformationProbeError("invalid standardizer")
    mean = np.asarray(fit["mean"], dtype=float)
    scale = np.asarray(fit["scale"], dtype=float)
    if arr.shape[1] != int(fit["n_features"]) or mean.shape != scale.shape or mean.shape[0] != arr.shape[1]:
        raise TeacherInformationProbeError("standardizer feature shape mismatch")
    return ((arr - mean) / scale).tolist()


def donor_balanced_mse(donor_ids, y_true, y_pred) -> dict:
    yt = _matrix(y_true, "y_true")
    yp = _matrix(y_pred, "y_pred")
    if yt.shape != yp.shape:
        raise TeacherInformationProbeError("y_true and y_pred must have identical shape")
    donors = _donors(donor_ids, yt.shape[0])
    donor_mse: dict[str, float] = {}
    for donor in sorted(set(donors)):
        idx = [i for i, value in enumerate(donors) if value == donor]
        residual = yt[idx] - yp[idx]
        donor_mse[donor] = float(np.mean(residual * residual))
    return {
        "donor_mse": donor_mse,
        "mean_donor_mse": float(np.mean(list(donor_mse.values()))),
    }


def _target_fit(y_train: np.ndarray) -> tuple[np.ndarray, np.ndarray] | None:
    mean = y_train.mean(axis=0)
    scale = y_train.std(axis=0, ddof=0)
    if np.any(scale == 0.0):
        return None
    return mean, scale


def _ridge_predict(
    x_train: np.ndarray,
    y_train: np.ndarray,
    x_test: np.ndarray,
    *,
    lam: float,
) -> np.ndarray | None:
    xfit = fit_standardizer(x_train.tolist())
    xtr = np.asarray(apply_standardizer(x_train.tolist(), xfit), dtype=float)
    xte = np.asarray(apply_standardizer(x_test.tolist(), xfit), dtype=float)
    yfit = _target_fit(y_train)
    if yfit is None:
        return None
    y_mean, y_scale = yfit
    ytr = (y_train - y_mean) / y_scale
    n = xtr.shape[0]
    gram = (xtr.T @ xtr) / float(n)
    rhs = (xtr.T @ ytr) / float(n)
    system = gram + float(lam) * np.eye(xtr.shape[1], dtype=float)
    beta = np.linalg.solve(system, rhs)
    pred_std = xte @ beta
    return pred_std * y_scale + y_mean


def _rows_for_donors(donors: list[str], selected: set[str]) -> list[int]:
    return [i for i, donor in enumerate(donors) if donor in selected]


def _choose_lambda(
    donors: list[str],
    x: np.ndarray,
    y: np.ndarray,
    training_donors: list[str],
) -> float | None:
    scores: list[tuple[float, float]] = []
    training_set = set(training_donors)
    for lam in LAMBDAS:
        inner_losses: list[float] = []
        valid = True
        for held in training_donors:
            inner_train_donors = training_set - {held}
            train_idx = _rows_for_donors(donors, inner_train_donors)
            test_idx = _rows_for_donors(donors, {held})
            pred = _ridge_predict(x[train_idx], y[train_idx], x[test_idx], lam=lam)
            if pred is None:
                valid = False
                break
            inner_losses.append(
                donor_balanced_mse(
                    [donors[i] for i in test_idx],
                    y[test_idx].tolist(),
                    pred.tolist(),
                )["mean_donor_mse"]
            )
        if valid and inner_losses:
            scores.append((float(np.mean(inner_losses)), float(lam)))
    if not scores:
        return None
    # Lower inner donor-balanced loss wins. Exact ties prefer larger lambda.
    scores.sort(key=lambda item: (item[0], -item[1]))
    return scores[0][1]


def nested_donor_probe(donor_ids, x, y) -> dict:
    x_arr = _matrix(x, "x")
    y_arr = _matrix(y, "y")
    if x_arr.shape[0] != y_arr.shape[0]:
        raise TeacherInformationProbeError("x and y row counts must match")
    donors = _donors(donor_ids, x_arr.shape[0])
    outer_donors = sorted(set(donors))
    if len(outer_donors) < 3:
        return {
            "status": "NOT_ESTIMABLE_DONOR_SPLITS",
            "lambda_family": list(LAMBDAS),
            "outer_donors": outer_donors,
            "outer_results": [],
        }

    outer_results: list[dict] = []
    all_donors = set(outer_donors)
    for held in outer_donors:
        train_donors = sorted(all_donors - {held})
        train_idx = _rows_for_donors(donors, set(train_donors))
        test_idx = _rows_for_donors(donors, {held})
        if _target_fit(y_arr[train_idx]) is None:
            return {
                "status": "NOT_ESTIMABLE_ZERO_VARIANCE_TARGET",
                "lambda_family": list(LAMBDAS),
                "outer_donors": outer_donors,
                "outer_results": outer_results,
            }
        selected = _choose_lambda(donors, x_arr, y_arr, train_donors)
        if selected is None:
            return {
                "status": "NOT_ESTIMABLE_INNER_SELECTION",
                "lambda_family": list(LAMBDAS),
                "outer_donors": outer_donors,
                "outer_results": outer_results,
            }
        pred = _ridge_predict(x_arr[train_idx], y_arr[train_idx], x_arr[test_idx], lam=selected)
        if pred is None:
            return {
                "status": "NOT_ESTIMABLE_ZERO_VARIANCE_TARGET",
                "lambda_family": list(LAMBDAS),
                "outer_donors": outer_donors,
                "outer_results": outer_results,
            }
        loss = donor_balanced_mse(
            [donors[i] for i in test_idx],
            y_arr[test_idx].tolist(),
            pred.tolist(),
        )["mean_donor_mse"]
        outer_results.append(
            {"donor_id": held, "selected_lambda": selected, "outer_mse": float(loss)}
        )

    return {
        "status": "PASS_PROBE_EXECUTION",
        "lambda_family": list(LAMBDAS),
        "outer_donors": outer_donors,
        "outer_results": outer_results,
        "donor_mse": {row["donor_id"]: row["outer_mse"] for row in outer_results},
    }


def compare_teacher_student(*, donor_ids, student_x, teacher_x, y, alpha: float = 0.01) -> dict:
    if isinstance(alpha, bool) or not isinstance(alpha, (int, float)) or not math.isfinite(float(alpha)) or not (0.0 < float(alpha) < 1.0):
        raise TeacherInformationProbeError("alpha must lie in (0,1)")
    alpha = float(alpha)
    student = nested_donor_probe(donor_ids, student_x, y)
    teacher = nested_donor_probe(donor_ids, teacher_x, y)
    if student["status"] != "PASS_PROBE_EXECUTION" or teacher["status"] != "PASS_PROBE_EXECUTION":
        return {
            "status": "NOT_ESTIMABLE",
            "arms": {"student": student, "teacher": teacher},
            "donor_deltas": [],
            "sign_test": None,
            "claim_boundary": "FINITE_LINEAR_DIAGNOSTIC_ONLY__NO_INFORMATION_THEORETIC_ABSENCE_CLAIM",
            "authority": dict(NO_AUTHORITY),
        }
    donors = sorted(set(student["donor_mse"]) & set(teacher["donor_mse"]))
    deltas = [
        {
            "donor_id": donor,
            "delta": float(student["donor_mse"][donor] - teacher["donor_mse"][donor]),
        }
        for donor in donors
    ]
    sign = P.sign_recurrence_gate(deltas, alpha)
    if not sign["resolution_estimable"]:
        status = "NOT_ESTIMABLE"
    elif sign["pass"]:
        status = "PASS"
    else:
        status = "FAIL"
    return {
        "status": status,
        "arms": {"student": student, "teacher": teacher},
        "donor_deltas": deltas,
        "sign_test": sign,
        "claim_boundary": "FINITE_LINEAR_DIAGNOSTIC_ONLY__NO_INFORMATION_THEORETIC_ABSENCE_CLAIM",
        "authority": dict(NO_AUTHORITY),
    }


def _known_truth_fixture(*, n_donors: int, private: bool):
    donor_ids: list[str] = []
    student_x: list[list[float]] = []
    teacher_x: list[list[float]] = []
    y: list[list[float]] = []
    pattern = (-1.0, -0.3, 0.3, 1.0)
    for donor_index in range(n_donors):
        donor = f"D{donor_index:02d}"
        for value in pattern:
            donor_ids.append(donor)
            student_x.append([0.0 if private else value])
            teacher_x.append([value])
            y.append([value])
    return donor_ids, student_x, teacher_x, y


def qualify_known_truth_probe(*, alpha: float = 0.01) -> dict:
    positive = _known_truth_fixture(n_donors=8, private=True)
    negative = _known_truth_fixture(n_donors=8, private=False)
    underpowered = _known_truth_fixture(n_donors=7, private=True)
    positive_result = compare_teacher_student(
        donor_ids=positive[0], student_x=positive[1], teacher_x=positive[2], y=positive[3], alpha=alpha
    )
    negative_result = compare_teacher_student(
        donor_ids=negative[0], student_x=negative[1], teacher_x=negative[2], y=negative[3], alpha=alpha
    )
    underpowered_result = compare_teacher_student(
        donor_ids=underpowered[0], student_x=underpowered[1], teacher_x=underpowered[2], y=underpowered[3], alpha=alpha
    )
    worlds = {
        "TEACHER_PRIVATE_SIGNAL_PRESENT": positive_result["status"],
        "NO_TEACHER_PRIVATE_SIGNAL": negative_result["status"],
        "UNDERPOWERED_TEACHER_PRIVATE_SIGNAL": underpowered_result["status"],
    }
    passed = (
        worlds["TEACHER_PRIVATE_SIGNAL_PRESENT"] == "PASS"
        and worlds["NO_TEACHER_PRIVATE_SIGNAL"] in {"FAIL", "NOT_ESTIMABLE"}
        and worlds["UNDERPOWERED_TEACHER_PRIVATE_SIGNAL"] == "NOT_ESTIMABLE"
    )
    return {
        "schema": "JEPA_TD_REAL_G6_TEACHER_INFORMATION_PROBE_QUALIFICATION_V1",
        "status": (
            "PASS_KNOWN_TRUTH_G6_PROBE_QUALIFICATION"
            if passed
            else "FAIL_KNOWN_TRUTH_G6_PROBE_QUALIFICATION"
        ),
        "worlds": worlds,
        "human_fail_semantics_qualified": bool(passed),
        "probe_scope": "MATCHED_MULTI_OUTPUT_RIDGE_OPERATIONAL_DIAGNOSTIC",
        "authority": dict(NO_AUTHORITY),
    }
