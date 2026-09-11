#!/usr/bin/env python3
"""Negative control: is the assembled HC3 `t` a valid scale under cross-fitting?

External review asked the decisive question about the V21 power gate. The gate
transports an effect as `delta = t / sqrt(n)`, where `t` comes from one HC3
regression across 28 out-of-fold predictions. But the predictor in that
regression is itself produced by 28 overlapping outcome-trained folds: folds `i`
and `j` share 26 of their 27 training donors, so `score_i` is a function of `y_j`
for every `j != i`. A permutation-valid p-value would not by itself establish
that the HC3 standard error is a valid scale for the underlying effect.

So this measures it rather than arguing about it. Under a strict null -- expression
generated independently of the outcome -- the whole nested procedure is run many
times and the distribution of the assembled HC3 `t` is compared against the
nominal `t` distribution at df = 23. If the procedure's null distribution is
wider than nominal, the HC3 standard error understates the procedure's own
variability, `t / sqrt(n)` overstates the effect, and the gate would be
anti-conservative.

A second arm runs a known non-null effect and asks whether `t / sqrt(n)` recovers
the underlying signal-to-noise it is supposed to transport.

Diagnostic only. No AT8 value, no partition, no real cohort: every array here is
synthetic. Nothing in this module changes a gate, a threshold or an authority.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np
from scipy import stats

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import t0_v21_selection_and_power_v1 as v21  # noqa: E402

N_DONORS = v21.V21_DISCOVERY_DONORS
N_GENES = 12
INNER_GRID = (-4.0, -2.0, 0.0, 2.0, 4.0)


def _ridge(x: np.ndarray, y: np.ndarray, exponent: float) -> np.ndarray:
    gram = x.T @ x
    scale = float(np.trace(gram) / len(x))
    lam = (10.0 ** float(exponent)) * scale
    return np.linalg.solve(gram + lam * np.eye(x.shape[1]), x.T @ y)


def _inner_loo_loss(x: np.ndarray, y: np.ndarray, exponent: float) -> float:
    total = 0.0
    for held in range(len(y)):
        keep = np.arange(len(y)) != held
        coef = _ridge(x[keep], y[keep], exponent)
        total += float((y[held] - x[held] @ coef) ** 2)
    return total / len(y)


def nested_statistic(x: np.ndarray, y: np.ndarray, age: np.ndarray,
                     sex: np.ndarray, *, inner_selection: bool) -> float | None:
    """One realisation of the full 28-fold nested procedure's assembled `t`."""

    def train_fold(train_idx):
        xt, yt = x[train_idx], y[train_idx]
        exponent = (min(INNER_GRID, key=lambda e: (_inner_loo_loss(xt, yt, e), e))
                    if inner_selection else 0.0)
        return _ridge(xt, yt, exponent)

    folds = v21.outer_lodo_oof(
        n_donors=len(y), train_fold=train_fold,
        predict_held_out=lambda coef, i: float(x[i] @ coef),
        expected_n_donors=len(y))
    effect = v21.oof_effect(y=y, age=age, sex=sex,
                            oof_scores=folds["oof_predictions"])
    return float(effect["t_observed"]) if effect.get("estimable") else None


def run(*, n_replicates: int, signal_to_noise: float, seed: int,
        inner_selection: bool) -> dict[str, Any]:
    rng = np.random.default_rng(seed)
    age = np.linspace(66.0, 94.0, N_DONORS)
    sex = np.array([float(i % 2) for i in range(N_DONORS)])

    statistics: list[float] = []
    for _ in range(n_replicates):
        x = rng.normal(size=(N_DONORS, N_GENES))
        # Under the null the outcome is generated independently of expression.
        signal = x[:, :3].mean(axis=1)
        y = signal_to_noise * signal + rng.normal(size=N_DONORS)
        t = nested_statistic(x, y, age, sex, inner_selection=inner_selection)
        if t is not None:
            statistics.append(t)

    values = np.asarray(statistics, dtype=np.float64)
    df = N_DONORS - v21.P_FULL
    critical = float(stats.t.isf(v21.ALPHA, df))
    rejection = float(np.mean(values >= critical))
    nominal_sd = math.sqrt(df / (df - 2.0))       # SD of a t with df > 2
    return {
        "n_replicates": int(n_replicates),
        "usable": int(values.size),
        "signal_to_noise": float(signal_to_noise),
        "inner_ridge_selection": bool(inner_selection),
        "residual_df": df,
        "observed_mean_t": float(values.mean()),
        "observed_sd_t": float(values.std(ddof=1)),
        "nominal_sd_t": nominal_sd,
        "sd_ratio_observed_over_nominal": float(values.std(ddof=1) / nominal_sd),
        "one_sided_critical_t": critical,
        "rejection_rate_at_alpha": rejection,
        "nominal_alpha": v21.ALPHA,
        "rejection_rate_over_nominal": rejection / v21.ALPHA,
        "implied_delta": float(values.mean() / math.sqrt(N_DONORS)),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--replicates", type=int, default=300)
    ap.add_argument("--seed", type=int, default=20260911)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    report: dict[str, Any] = {
        "question": "Is the assembled HC3 t a valid scale for effect transport "
                    "when the predictor is produced by overlapping "
                    "outcome-trained folds?",
        "arms": {},
    }
    for label, snr, inner in (
            ("null_fixed_ridge", 0.0, False),
            ("null_inner_selection", 0.0, True),
            ("effect_fixed_ridge", 0.6, False),
    ):
        report["arms"][label] = run(n_replicates=args.replicates,
                                    signal_to_noise=snr, seed=args.seed,
                                    inner_selection=inner)
        arm = report["arms"][label]
        print("%-22s sd_ratio=%.3f  rejection=%.4f (nominal %.4f, x%.2f)"
              % (label, arm["sd_ratio_observed_over_nominal"],
                 arm["rejection_rate_at_alpha"], arm["nominal_alpha"],
                 arm["rejection_rate_over_nominal"]))

    null_arms = [report["arms"][k] for k in
                 ("null_fixed_ridge", "null_inner_selection")]
    worst = max(a["rejection_rate_over_nominal"] for a in null_arms)
    report["verdict"] = (
        "HC3_T_NULL_INFLATED" if worst > 1.5 else
        "HC3_T_NULL_APPROXIMATELY_NOMINAL")
    report["worst_null_rejection_over_nominal"] = worst
    print("\nverdict: %s (worst null rejection is %.2fx nominal)"
          % (report["verdict"], worst))

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print("written: %s" % args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
