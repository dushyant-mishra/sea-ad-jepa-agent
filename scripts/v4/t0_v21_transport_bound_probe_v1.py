#!/usr/bin/env python3
"""Can the calibrated split estimand actually support a power guarantee?

The study established two things. The cross-fitted partial correlation is not
calibrated under the null, so it cannot carry an effect. The held-out-split
partial correlation *is* calibrated at a 16/12 split -- implied-null-t SD ratio
1.041, rejection 0.0267 against a nominal 0.025 -- so it is a legitimate estimate
of the frozen scorer's rho.

But its end-to-end projection was anti-conservative: 0.119 projected against
0.040 actual at rho_true = 0.30, and 0.195 against 0.080 at 0.50. A calibrated
estimand is not the same as a usable power guarantee, and this probe separates
the two candidate explanations and then asks the decisive question.

Explanation A -- projecting from a point estimate. Power is convex in rho in this
region, so averaging power over a noisy rho_hat exceeds the power at the true
rho. With only 12 evaluation donors, rho_hat is very noisy indeed.

Explanation B -- the parametric reference overstates the test that will actually
run. The frozen Freedman-Lane procedure at n = 12 carries mean HC3 leverage 5/12
= 0.417, and the statistic was separately measured to reach only ~0.83 of its
naive noncentrality there.

The decisive question, asked after both are corrected: with a one-sided lower
confidence bound on rho and power measured against the actual Freedman-Lane test,
is the projection conservative -- and if so, can the gate ever clear at n = 12?

Synthetic throughout. No AT8, no partition, no authority changed.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import t0_v21_selection_and_power_v1 as v21  # noqa: E402
import t0_v21_transport_estimand_v1 as T  # noqa: E402
import t0_v21_transport_estimand_study_v1 as S  # noqa: E402

ALPHA = 0.025
TARGET_POWER = 0.80
N_CONFIRMATION = 12


def rho_lower_bound(rho_hat: float, n_eval: int, *, conditioning: int = 4,
                    confidence: float = 0.95) -> float:
    """One-sided lower confidence bound on a partial correlation, Fisher z.

    For a partial correlation controlling `conditioning` variables, `atanh(rho)`
    is approximately normal with standard error `1 / sqrt(n - conditioning - 3)`.
    Nothing here is tuned: it is the standard interval, applied at the evaluation
    sample size the split actually leaves.
    """
    dof = n_eval - conditioning - 3
    if dof < 1:
        return -1.0
    z = math.atanh(max(-0.999999, min(0.999999, rho_hat)))
    se = 1.0 / math.sqrt(dof)
    critical = 1.6448536269514722 if confidence == 0.95 else 1.959963984540054
    return float(math.tanh(z - critical * se))


def run(*, replicates: int, n_train: int, rho_true: float, seed: int,
        n_permutations: int) -> dict[str, Any]:
    rng = np.random.default_rng(seed)
    n_eval = S.N_DISCOVERY - n_train
    point, lower, rejects = [], [], []
    for _ in range(replicates):
        _, _, z, scale = S.design(S.N_DISCOVERY, rng)
        x = S.expression(S.N_DISCOVERY, rng)
        y = S.outcome(x, z, scale, rho_true, rng)
        rho_hat, beta, _ = S.split_rho(x, y, z, n_train=n_train,
                                       inner_selection=False)
        rho_hat = max(-0.999, min(0.999, rho_hat))
        point.append(rho_hat)
        lower.append(rho_lower_bound(rho_hat, n_eval))
        hit = S.confirmation_rejects(beta, rng, n_permutations=n_permutations,
                                     rho_true=rho_true)
        if hit is not None:
            rejects.append(1.0 if hit else 0.0)

    point = np.asarray(point)
    lower = np.asarray(lower)
    rejects = np.asarray(rejects)

    def power_at(rho):
        rho = max(-0.999, min(0.999, float(rho)))
        if rho <= 0.0:
            return float(ALPHA)
        p = T.parametric_power(rho=rho, n=N_CONFIRMATION, alpha=ALPHA)
        return float(p["power"]) if p.get("estimable") else float("nan")

    projected_point = np.array([power_at(r) for r in point])
    projected_lower = np.array([power_at(r) for r in lower])
    actual = float(rejects.mean())
    se = math.sqrt(max(actual * (1 - actual), 0.0) / max(len(rejects), 1))

    return {
        "n_train": n_train, "n_evaluate": n_eval, "rho_true_signal": rho_true,
        "replicates": int(replicates),
        "mean_rho_hat": float(point.mean()),
        "sd_rho_hat": float(point.std(ddof=1)),
        "mean_rho_lower_95": float(lower.mean()),
        "fraction_lower_bound_positive": float(np.mean(lower > 0.0)),
        "mean_projected_power_from_point": float(projected_point.mean()),
        "mean_projected_power_from_lower_bound": float(projected_lower.mean()),
        "actual_rejection_rate": actual,
        "actual_rejection_se": se,
        "point_projection_conservative":
            bool(projected_point.mean() <= actual + 1.96 * se),
        "lower_bound_projection_conservative":
            bool(projected_lower.mean() <= actual + 1.96 * se),
        "fraction_lower_bound_clears_80":
            float(np.mean(projected_lower >= TARGET_POWER)),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--replicates", type=int, default=400)
    ap.add_argument("--permutations", type=int, default=199)
    ap.add_argument("--seed", type=int, default=20260912)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    needed = T.rho_for_power(target_power=TARGET_POWER, n=N_CONFIRMATION,
                             alpha=ALPHA)
    report: dict[str, Any] = {
        "alpha": ALPHA, "target_power": TARGET_POWER,
        "rho_required_for_80_percent_power_at_n12": needed,
        "arms": {},
    }
    print("rho required for %.0f%% power at n=12, alpha=%.3f: %.4f"
          % (100 * TARGET_POWER, ALPHA, needed))
    print("rho_hat needed so its 95%% lower bound reaches that, at n_eval=12: "
          "%.4f" % _invert_lower_bound(needed, 12))
    print("                                                   at n_eval=8:  "
          "%.4f" % _invert_lower_bound(needed, 8))

    for n_train in (16, 20):
        for rho_true in (0.30, 0.50, 0.70):
            r = run(replicates=args.replicates, n_train=n_train,
                    rho_true=rho_true, seed=args.seed,
                    n_permutations=args.permutations)
            report["arms"]["train%d_rho%.2f" % (n_train, rho_true)] = r
            print("  train=%d eval=%d rho_true=%.2f | rho_hat=%.3f(sd %.3f) "
                  "lower95=%.3f | proj_point=%.3f proj_lower=%.3f "
                  "actual=%.3f | point_cons=%s lower_cons=%s clears80=%.1f%%"
                  % (n_train, r["n_evaluate"], rho_true, r["mean_rho_hat"],
                     r["sd_rho_hat"], r["mean_rho_lower_95"],
                     r["mean_projected_power_from_point"],
                     r["mean_projected_power_from_lower_bound"],
                     r["actual_rejection_rate"],
                     r["point_projection_conservative"],
                     r["lower_bound_projection_conservative"],
                     100 * r["fraction_lower_bound_clears_80"]))

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print("written: %s" % args.out)
    return 0


def _invert_lower_bound(target_rho: float, n_eval: int) -> float:
    """What point estimate would be needed for the lower bound to reach target."""
    dof = n_eval - 4 - 3
    if dof < 1:
        return float("nan")
    return float(math.tanh(math.atanh(target_rho) + 1.6448536269514722
                           / math.sqrt(dof)))


if __name__ == "__main__":
    raise SystemExit(main())
