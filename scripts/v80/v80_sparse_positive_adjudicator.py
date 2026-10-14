from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

import numpy as np


_ALLOWED = {"COMPLETE", "NOT_ESTIMABLE", "NUMERICAL_FAILURE"}
_SELF_REPORTED_METRICS = {
    "detection_intercept_abs_error",
    "positive_location_abs_error",
    "donor_effect_rank_correlation",
    "heldout_detection_logloss_delta",
    "heldout_positive_logdensity_delta",
}
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
    detection_fixed_effect_estimates: tuple[float, ...] | None = None
    positive_location_estimate: float | None = None
    detection_donor_effect_estimates: tuple[float, ...] | None = None
    positive_donor_effect_estimates: tuple[float, ...] | None = None
    detection_probability: tuple[float, ...] | None = None
    positive_mu: tuple[float, ...] | None = None
    positive_sigma: float | None = None


def parse_fit_outcome(record: Mapping[str, object]) -> FitOutcome:
    forbidden = _SELF_REPORTED_METRICS.intersection(record)
    if forbidden:
        raise ValueError(f"estimator may not self-report controller metrics: {sorted(forbidden)}")
    fit_id = str(record.get("opaque_fit_id", ""))
    status = str(record.get("status", ""))
    if not fit_id:
        raise ValueError("opaque_fit_id is required")
    if status not in _ALLOWED:
        raise ValueError(f"invalid fit status: {status}")
    if status != "COMPLETE":
        return FitOutcome(opaque_fit_id=fit_id, status=status)

    required = (
        "detection_fixed_effect_estimates",
        "positive_location_estimate",
        "detection_donor_effect_estimates",
        "positive_donor_effect_estimates",
        "detection_probability",
        "positive_mu",
        "positive_sigma",
    )
    missing = [k for k in required if k not in record]
    if missing:
        raise ValueError(f"COMPLETE result missing estimates/predictions: {missing}")

    def vector(name: str) -> tuple[float, ...]:
        raw = record[name]
        if not isinstance(raw, (list, tuple)):
            raise ValueError(f"{name} must be a list")
        return tuple(float(x) for x in raw)

    return FitOutcome(
        opaque_fit_id=fit_id,
        status=status,
        detection_fixed_effect_estimates=vector("detection_fixed_effect_estimates"),
        positive_location_estimate=float(record["positive_location_estimate"]),
        detection_donor_effect_estimates=vector("detection_donor_effect_estimates"),
        positive_donor_effect_estimates=vector("positive_donor_effect_estimates"),
        detection_probability=vector("detection_probability"),
        positive_mu=vector("positive_mu"),
        positive_sigma=float(record["positive_sigma"]),
    )


def _rank_corr(a: np.ndarray, b: np.ndarray) -> float:
    if len(a) < 2 or len(a) != len(b):
        return float("nan")
    ra = np.argsort(np.argsort(a, kind="mergesort"), kind="mergesort").astype(float)
    rb = np.argsort(np.argsort(b, kind="mergesort"), kind="mergesort").astype(float)
    if ra.std() == 0 or rb.std() == 0:
        return float("nan")
    return float(np.corrcoef(ra, rb)[0, 1])


def _binary_logloss(y: np.ndarray, p: np.ndarray) -> float:
    p = np.clip(np.asarray(p, dtype=float), 1e-8, 1.0 - 1e-8)
    y = np.asarray(y, dtype=float)
    return float(np.mean(-(y * np.log(p) + (1.0 - y) * np.log1p(-p))))


def _normal_logpdf(x: np.ndarray, mu: np.ndarray | float, sigma: float) -> np.ndarray:
    sigma = float(sigma)
    if not np.isfinite(sigma) or sigma <= 0:
        return np.full(np.asarray(x).shape, np.nan)
    z = (np.asarray(x, dtype=float) - np.asarray(mu, dtype=float)) / sigma
    return -0.5 * z * z - np.log(sigma) - 0.5 * np.log(2.0 * np.pi)


def _fit_input_index(fit_payload: Mapping[str, object]) -> dict[str, tuple[Mapping[str, object], int]]:
    worlds = fit_payload.get("worlds")
    if not isinstance(worlds, list):
        raise ValueError("fit payload requires worlds list")
    out: dict[str, tuple[Mapping[str, object], int]] = {}
    for world in worlds:
        fit_ids = world.get("opaque_fit_ids")
        if not isinstance(fit_ids, list):
            raise ValueError("fit world missing opaque_fit_ids")
        for gene, fit_id in enumerate(fit_ids):
            key = str(fit_id)
            if key in out:
                raise ValueError("duplicate fit id in fit transport")
            out[key] = (world, gene)
    return out


def _controller_metrics(
    truth: Mapping[str, object],
    fit_world: Mapping[str, object],
    gene: int,
    outcome: FitOutcome,
) -> dict[str, float]:
    fixed = np.asarray(outcome.detection_fixed_effect_estimates, dtype=float)
    true_fixed = np.asarray(truth["latent_detection_fixed_effects"], dtype=float)
    donor_est = np.asarray(outcome.detection_donor_effect_estimates, dtype=float)
    true_donor = np.asarray(truth["latent_detection_donor_effect"], dtype=float)
    positive_donor_est = np.asarray(outcome.positive_donor_effect_estimates, dtype=float)
    p = np.asarray(outcome.detection_probability, dtype=float)
    positive_mu = np.asarray(outcome.positive_mu, dtype=float)
    donor_id = np.asarray(fit_world["donor_id"], dtype=int)
    split = np.asarray(fit_world["split"], dtype=str)
    support = np.asarray(fit_world["support"], dtype=bool)[:, gene]
    detected = np.asarray(fit_world["detected"], dtype=bool)[:, gene]
    positive_value = np.asarray(fit_world["positive_value"], dtype=float)[:, gene]

    n_cells = len(donor_id)
    n_donors = int(donor_id.max()) + 1
    arrays = (fixed, true_fixed, donor_est, true_donor, positive_donor_est, p, positive_mu)
    if fixed.shape != (4,) or true_fixed.shape != (4,):
        raise ValueError("COMPLETE fixed-effect vector must have four coefficients")
    if donor_est.shape != (n_donors,) or true_donor.shape != (n_donors,) or positive_donor_est.shape != (n_donors,):
        raise ValueError("COMPLETE donor-effect vectors have wrong length")
    if p.shape != (n_cells,) or positive_mu.shape != (n_cells,):
        raise ValueError("COMPLETE prediction vectors have wrong length")
    if any(not np.all(np.isfinite(x)) for x in arrays):
        raise ValueError("COMPLETE estimates/predictions must be finite")
    if not (np.all(p >= 0.0) and np.all(p <= 1.0)):
        raise ValueError("detection probabilities must lie in [0,1]")
    if outcome.positive_location_estimate is None or not np.isfinite(outcome.positive_location_estimate):
        raise ValueError("positive_location_estimate must be finite")
    if outcome.positive_sigma is None or not np.isfinite(outcome.positive_sigma) or outcome.positive_sigma <= 0:
        raise ValueError("positive_sigma must be finite and positive")

    train = (split == "train") & support
    test = (split == "test") & support
    if not train.any() or not test.any():
        raise ValueError("estimable fit lacks train/test measured support")
    y_train = detected[train]
    y_test = detected[test]
    baseline_p = float(np.clip(y_train.mean(), 1e-8, 1.0 - 1e-8))
    detection_delta = _binary_logloss(y_test, p[test]) - _binary_logloss(y_test, np.full(y_test.shape, baseline_p))

    train_pos = train & detected
    test_pos = test & detected
    if not train_pos.any() or not test_pos.any():
        raise ValueError("estimable positive component lacks train/test positive observations")
    log_train = np.log(positive_value[train_pos])
    log_test = np.log(positive_value[test_pos])
    baseline_mu = float(log_train.mean())
    baseline_sigma = max(float(log_train.std(ddof=0)), 1e-6)
    baseline_ld = float(_normal_logpdf(log_test, baseline_mu, baseline_sigma).mean())
    estimator_ld = float(_normal_logpdf(log_test, positive_mu[test_pos], float(outcome.positive_sigma)).mean())
    positive_density_delta = baseline_ld - estimator_ld

    return {
        "detection_intercept_abs_error": float(abs(fixed[0] - true_fixed[0])),
        "positive_location_abs_error": float(abs(float(outcome.positive_location_estimate) - float(truth["latent_positive_location"]))),
        "donor_effect_rank_correlation": _rank_corr(donor_est, true_donor),
        "heldout_detection_logloss_delta": float(detection_delta),
        "heldout_positive_logdensity_delta": float(positive_density_delta),
    }


def _recovery_failures(metrics: Sequence[Mapping[str, float]]) -> list[dict[str, object]]:
    failures: list[dict[str, object]] = []
    if not metrics:
        return failures
    for field, (direction, threshold) in _THRESHOLDS.items():
        values = np.asarray([m[field] for m in metrics], dtype=float)
        if not np.all(np.isfinite(values)):
            failures.append({"reason": "RECOVERY_GATE", "metric": field, "detail": "NONFINITE_CONTROLLER_METRIC"})
            continue
        median = float(np.median(values))
        bad = median > threshold if direction == "max" else median < threshold
        if bad:
            failures.append({"reason": "RECOVERY_GATE", "metric": field, "median": median, "threshold": threshold, "direction": direction})
    return failures


def adjudicate_sparse_positive(
    controller_payload: Mapping[str, object],
    fit_payload: Mapping[str, object],
    estimator_results: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    controller_fits = controller_payload.get("fits")
    if not isinstance(controller_fits, list):
        raise ValueError("controller payload requires fits list")
    truth = {str(x["opaque_fit_id"]): x for x in controller_fits}
    fit_index = _fit_input_index(fit_payload)
    parsed = [parse_fit_outcome(x) for x in estimator_results]
    result_map = {x.opaque_fit_id: x for x in parsed}
    if len(result_map) != len(parsed):
        raise ValueError("duplicate estimator result fit id")

    failures: list[dict[str, object]] = []
    recovery_metrics: list[dict[str, float]] = []
    for fit_id, truth_record in truth.items():
        outcome = result_map.get(fit_id)
        if outcome is None:
            failures.append({"opaque_fit_id": fit_id, "reason": "MISSING_RESULT"})
            continue
        if fit_id not in fit_index:
            raise ValueError("controller fit missing from fit transport")
        estimability = str(truth_record["estimability_truth"])
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
            fit_world, gene = fit_index[fit_id]
            try:
                recovery_metrics.append(_controller_metrics(truth_record, fit_world, gene, outcome))
            except ValueError as exc:
                failures.append({"opaque_fit_id": fit_id, "reason": "INVALID_COMPLETE_OUTPUT", "detail": str(exc)})
        elif estimability == "NOT_ESTIMABLE_BY_CONSTRUCTION":
            if outcome.status == "COMPLETE":
                failures.append({"opaque_fit_id": fit_id, "reason": "FALSE_CERTAINTY", "construction_reason": truth_record.get("nonestimability_reason")})
            elif outcome.status != "NOT_ESTIMABLE":
                failures.append({"opaque_fit_id": fit_id, "reason": "INVALID_STATUS_FOR_NONESTIMABLE"})
        else:
            raise ValueError(f"unknown controller estimability truth: {estimability}")

    failures.extend(_recovery_failures(recovery_metrics))
    for fit_id in sorted(set(result_map) - set(truth)):
        failures.append({"opaque_fit_id": fit_id, "reason": "UNEXPECTED_RESULT"})

    return {
        "schema": "V80_SPARSE_POSITIVE_ADJUDICATION_V2",
        "status": "PASS" if not failures else "FAIL",
        "n_expected": len(truth),
        "n_results": len(parsed),
        "n_controller_scored_complete": len(recovery_metrics),
        "failures": failures,
        "aggregate_rescue_authorized": False,
        "metrics_computed_by_controller": True,
    }
