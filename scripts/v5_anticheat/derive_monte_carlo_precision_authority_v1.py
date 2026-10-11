#!/usr/bin/env python3
"""Prospective Monte Carlo precision authority for FULL104 dimension metrics.

Replicate counts are derived mechanically from a declared error budget using
Hoeffding's inequality for bounded endpoint statistics. Historical constants are
not consulted. This module does not read FULL104, choose any dimension, or
authorize training.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


def hoeffding_replicates(metric_lower: float, metric_upper: float, half_width: float, alpha: float) -> int:
    lower = float(metric_lower)
    upper = float(metric_upper)
    eps = float(half_width)
    delta = float(alpha)
    if not (math.isfinite(lower) and math.isfinite(upper) and upper > lower):
        raise ValueError("metric bounds must be finite with upper > lower")
    if not math.isfinite(eps) or eps <= 0:
        raise ValueError("half_width must be finite and positive")
    if not math.isfinite(delta) or not (0.0 < delta < 1.0):
        raise ValueError("alpha must satisfy 0 < alpha < 1")
    width = upper - lower
    # P(|mean-E mean| >= eps) <= 2 exp(-2 n eps^2 / width^2)
    return int(math.ceil((width * width * math.log(2.0 / delta)) / (2.0 * eps * eps)))


def derive_precision_authority(
    metric_lower: float,
    metric_upper: float,
    half_width: float,
    familywise_alpha: float,
    n_endpoints: int,
) -> dict[str, object]:
    endpoints = int(n_endpoints)
    if endpoints <= 0:
        raise ValueError("n_endpoints must be positive")
    fwa = float(familywise_alpha)
    if not math.isfinite(fwa) or not (0.0 < fwa < 1.0):
        raise ValueError("familywise_alpha must satisfy 0 < alpha < 1")
    per_endpoint_alpha = fwa / endpoints
    reps = hoeffding_replicates(metric_lower, metric_upper, half_width, per_endpoint_alpha)
    return {
        "schema": "V5_FULL104_MONTE_CARLO_PRECISION_AUTHORITY_V1",
        "method": "HOEFFDING_BOUNDED_MEAN__BONFERRONI_FAMILYWISE",
        "metric_bounds": [float(metric_lower), float(metric_upper)],
        "half_width": float(half_width),
        "familywise_alpha": fwa,
        "n_endpoints": endpoints,
        "per_endpoint_alpha": per_endpoint_alpha,
        "replicates": reps,
        "replicate_count_source": "PROSPECTIVE_ERROR_BUDGET__NOT_HISTORICAL_CONSTANT",
        "historical_replicate_constants_authorized": False,
        "dimension_selected": False,
        "training_authorized": False,
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--metric-lower", type=float, required=True)
    p.add_argument("--metric-upper", type=float, required=True)
    p.add_argument("--half-width", type=float, required=True)
    p.add_argument("--familywise-alpha", type=float, required=True)
    p.add_argument("--n-endpoints", type=int, required=True)
    p.add_argument("--out", required=True)
    a = p.parse_args()
    rec = derive_precision_authority(a.metric_lower, a.metric_upper, a.half_width, a.familywise_alpha, a.n_endpoints)
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rec, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(rec["replicates"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
