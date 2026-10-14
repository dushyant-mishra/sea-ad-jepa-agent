from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

import numpy as np


_ALLOWED = {"COMPLETE", "NOT_ESTIMABLE", "NUMERICAL_FAILURE"}
_THRESHOLDS = {
    "detection_intercept_abs_error": ("max", 0.35),
    "positive_location_abs_error": ("max", 0.30),
    "donor_effect_rank_correlation": ("min", 0.45),
    "heldout_detection_logloss_delta": ("max", 0.02),
    "heldout_positive_logdensity_delta": ("max", 0.05),
}


@dataclass(frozen=True)
class FitOutcome:
    opaque_fit_id: str
    status: str
    finite: bool | None
    detection_intercept_abs_error: float | None
    positive_location_abs_error: float | None
    donor_effect_rank_correlation: float | None
    heldout_detection_logloss_delta: float | None
    heldout_positive_logdensity_delta: float | None


def parse_fit_outcome(record: Mapping[str, object]) -> FitOutcome:
    fit_id = str(record.get("opaque_fit_id", ""))
    status = str(record.get("status", ""))
    if not fit_id:
        raise ValueError("opaque_fit_id is required")
    if status not in _ALLOWED:
        raise ValueError(f"invalid fit status: {status}")

    def maybe_float(name: str) -> float | None:
        value = record.get(name)
        return None if value is None else float(value)

    finite = record.get("finite")
    finite_value = None if finite is None else bool(finite)
    return FitOutcome(
        opaque_fit_id=fit_id,
        status=status,
        finite=finite_value,
        detection_intercept_abs_error=maybe_float("detection_intercept_abs_error"),
        positive_location_abs_error=maybe_float("positive_location_abs_error"),
        donor_effect_rank_correlation=maybe_float("donor_effect_rank_correlation"),
        heldout_detection_logloss_delta=maybe_float("heldout_detection_logloss_delta"),
        heldout_positive_logdensity_delta=maybe_float("heldout_positive_logdensity_delta"),
    )


def _recovery_failures(outcomes: Sequence[FitOutcome]) -> list[dict[str, object]]:
    failures: list[dict[str, object]] = []
    if not outcomes:
        return failures
    for field, (direction, threshold) in _THRESHOLDS.items():
        values = [getattr(o, field) for o in outcomes]
        if any(v is None or not np.isfinite(v) for v in values):
            failures.append({"reason": "RECOVERY_GATE", "metric": field, "detail": "MISSING_OR_NONFINITE"})
            continue
        median = float(np.median(np.asarray(values, dtype=float)))
        bad = median > threshold if direction == "max" else median < threshold
        if bad:
            failures.append({
                "reason": "RECOVERY_GATE",
                "metric": field,
                "median": median,
                "threshold": threshold,
                "direction": direction,
            })
    return failures


def adjudicate_sparse_positive(
    controller_payload: Mapping[str, object],
    estimator_results: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    controller_fits = controller_payload.get("fits")
    if not isinstance(controller_fits, list):
        raise ValueError("controller payload requires fits list")
    truth = {str(x["opaque_fit_id"]): str(x["estimability_truth"]) for x in controller_fits}
    parsed = [parse_fit_outcome(x) for x in estimator_results]
    result_map = {x.opaque_fit_id: x for x in parsed}
    if len(result_map) != len(parsed):
        raise ValueError("duplicate estimator result fit id")

    failures: list[dict[str, object]] = []
    complete_estimable: list[FitOutcome] = []

    for fit_id, estimability in truth.items():
        outcome = result_map.get(fit_id)
        if outcome is None:
            failures.append({"opaque_fit_id": fit_id, "reason": "MISSING_RESULT"})
            continue
        if outcome.status == "NUMERICAL_FAILURE":
            failures.append({"opaque_fit_id": fit_id, "reason": "NUMERICAL_FAILURE"})
            continue
        if estimability == "ESTIMABLE":
            if outcome.status == "NOT_ESTIMABLE":
                failures.append({"opaque_fit_id": fit_id, "reason": "FALSE_ABSTENTION"})
                continue
            if outcome.status != "COMPLETE":
                failures.append({"opaque_fit_id": fit_id, "reason": "INVALID_STATUS_FOR_ESTIMABLE"})
                continue
            if outcome.finite is not True:
                failures.append({"opaque_fit_id": fit_id, "reason": "NONFINITE_COMPLETE"})
                continue
            complete_estimable.append(outcome)
        elif estimability == "NOT_ESTIMABLE_BY_CONSTRUCTION":
            if outcome.status == "COMPLETE":
                failures.append({"opaque_fit_id": fit_id, "reason": "FALSE_CERTAINTY"})
            elif outcome.status != "NOT_ESTIMABLE":
                failures.append({"opaque_fit_id": fit_id, "reason": "INVALID_STATUS_FOR_NONESTIMABLE"})
        else:
            raise ValueError(f"unknown controller estimability truth: {estimability}")

    failures.extend(_recovery_failures(complete_estimable))
    unexpected = sorted(set(result_map) - set(truth))
    for fit_id in unexpected:
        failures.append({"opaque_fit_id": fit_id, "reason": "UNEXPECTED_RESULT"})

    return {
        "schema": "V80_SPARSE_POSITIVE_ADJUDICATION_V1",
        "status": "PASS" if not failures else "FAIL",
        "n_expected": len(truth),
        "n_results": len(parsed),
        "failures": failures,
        "aggregate_rescue_authorized": False,
    }
