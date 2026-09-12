#!/usr/bin/env python3
"""Transport calibration at the REAL dataset geometry, not an invented one.

An earlier study answered this question in a regime I chose -- 12 genes, 3 signal
genes, unit noise -- and its numbers were about that toy. The pipeline is
developed around this dataset, so the simulation has to be too.

Geometry taken from the committed V20 artifacts and the open age/sex authority,
not assumed:

    features                28,061 molecular addresses
    decision-mask features  24,482  (T0_TARGET_DECISION_MASK_U8.bin)
    discovery donors        28
    development donors      46
    immune cells            20,804
    ridge grid              17 values, -6.0 to +2.0 step 0.5
    V20 selection           index 16 of 17 -- the grid boundary
    age                     65 to 100, mean 88.04, sd 8.36   (n = 46)
    sex                     31 female / 15 male

The ratio that matters: p/n is about 875 here against 0.43 in the toy. Ridge in
that regime behaves nothing like the toy, and a first probe already shows the
frozen learner selecting maximum regularization even on pure noise -- so the
earlier attenuation and calibration numbers cannot be carried over at all.

`fit_t0_target` costs about 3.1 s per fit at the real width, so a 28-fold nested
replicate costs roughly 87 s. This module provides a dual-form fast path and
**verifies it against the frozen learner** before using it, rather than assuming
equivalence.

Synthetic outcomes only. No AT8 value is read. Expression is simulated; the real
expression stores stay closed. Only donor-level age/sex, published fit shapes and
counts are taken from the repository.
"""

from __future__ import annotations

import argparse
import csv
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
import t0_v21_transport_estimand_v1 as T  # noqa: E402

REPO = HERE.parent.parent
AGE_SEX = REPO / "outputs/t0_age_sex_20260908/T0_AGE_SEX_REGISTRY.csv"
DECISION_MASK = (REPO / "outputs/t0_discovery_stage_20260909/target"
                 / "T0_TARGET_DECISION_MASK_U8.bin")

N_DISCOVERY = 28
N_DEVELOPMENT = 46
ALPHA = 0.025


def real_cohort() -> dict[str, Any]:
    """Donor-level age and sex from the open authority. No pathology is read."""
    rows = list(csv.DictReader(AGE_SEX.open(encoding="utf-8")))
    age = np.array([float(r["age"]) for r in rows], dtype=np.float64)
    sex = np.array([1.0 if r["sex"].strip().lower() == "female" else 0.0
                    for r in rows], dtype=np.float64)
    return {"age": age, "sex": sex, "n": len(rows),
            "minority_fraction": float(min(sex.mean(), 1 - sex.mean()))}


def real_feature_width() -> dict[str, int]:
    """Feature counts from the committed V20 target package, by shape only."""
    mask = np.fromfile(DECISION_MASK, dtype=np.uint8)
    return {"features_total": int(mask.size),
            "features_decision": int(mask.sum())}


# --------------------------------------------------------------------------
# generative model at the real width
# --------------------------------------------------------------------------

def simulate_expression(n: int, g: int, rng, *, factors: int,
                        factor_strength: float = 3.0) -> np.ndarray:
    """Factor-structured pseudobulk.

    Real pseudobulk is far from independent across genes: a handful of programmes
    dominate. Independent genes would make ridge behave quite differently, so the
    factor count is an explicit, swept assumption rather than a hidden one.
    """
    loadings = rng.normal(size=(factors, g))
    scores = rng.normal(size=(n, factors)) * factor_strength
    return scores @ loadings / math.sqrt(g) + rng.normal(size=(n, g))


def outcome_with_rho(x, z, direction, rho_true, rng):
    signal = x @ direction
    s_r = T.residualize(signal, z)
    sd = float(np.std(s_r, ddof=1))
    if sd <= 0:
        raise RuntimeError("degenerate signal")
    b = 0.0 if rho_true == 0 else (rho_true / math.sqrt(1 - rho_true ** 2)) / sd
    return z @ np.array([1.0, 0.02, 0.0005, 0.3]) + b * signal + rng.normal(size=len(z))


# --------------------------------------------------------------------------
# fast dual-form path, verified against the frozen learner
# --------------------------------------------------------------------------

def _dual_scores(x_train, y_train, x_held, exponent):
    """Ridge prediction via the dual form, matching the frozen trace scaling."""
    gram = x_train @ x_train.T
    n = len(y_train)
    scale = float(np.trace(x_train.T @ x_train) / n) if x_train.shape[1] < 4000 \
        else float(np.sum(x_train * x_train) / n)
    lam = (10.0 ** float(exponent)) * scale
    alpha = np.linalg.solve(gram + lam * np.eye(n), y_train)
    return (x_held @ x_train.T) @ alpha


def verify_fast_path_against_frozen(rng, *, g: int, tolerance: float = 1e-8
                                    ) -> dict[str, Any]:
    """The reconstruction must match the authority before it is used."""
    _, learner = v21._frozen()
    cohort = real_cohort()
    n = N_DISCOVERY
    x = simulate_expression(n, g, rng, factors=8)
    y = rng.normal(size=n)
    ids = ["D%02d" % i for i in range(n)]
    fit = learner.fit_t0_target(x, y, cohort["age"][:n], cohort["sex"][:n], ids)
    exponent = float(fit["selected_multiplier_exponent"])

    held = 0
    train = np.arange(n) != held
    mine = float(_dual_scores(x[train], y[train], x[held:held + 1], exponent)[0])
    primal = float(x[held] @ np.linalg.solve(
        x[train].T @ x[train]
        + (10.0 ** exponent) * float(np.sum(x[train] * x[train]) / (n - 1))
        * np.eye(g), x[train].T @ y[train]))
    return {"selected_exponent_on_noise": exponent,
            "dual": mine, "primal": primal,
            "relative_difference": abs(mine - primal) / max(abs(primal), 1e-12),
            "agree": abs(mine - primal) <= tolerance * max(abs(primal), 1.0)}


def nested_oof(x, y, z, *, exponent):
    n = len(y)
    out = np.empty(n)
    for held in range(n):
        train = np.arange(n) != held
        out[held] = _dual_scores(x[train], y[train], x[held:held + 1],
                                 exponent)[0]
    return out


def split_oof(x, y, *, n_train, exponent):
    train = np.arange(n_train)
    evaluate = np.arange(n_train, len(y))
    return _dual_scores(x[train], y[train], x[evaluate], exponent), evaluate


def null_calibration(*, replicates, g, factors, exponent, seed, n_train=None):
    """Null distribution of rho-hat at the real width."""
    rng = np.random.default_rng(seed)
    cohort = real_cohort()
    _, learner = v21._frozen()
    age, sex = cohort["age"][:N_DISCOVERY], cohort["sex"][:N_DISCOVERY]
    z, _ = learner.nuisance_design(age, sex)

    rhos, n_eval = [], N_DISCOVERY
    for _ in range(replicates):
        x = simulate_expression(N_DISCOVERY, g, rng, factors=factors)
        y = outcome_with_rho(x, z, np.zeros(g), 0.0, rng)
        if n_train is None:
            s = nested_oof(x, y, z, exponent=exponent)
            rhos.append(T.partial_correlation(y=y, nuisance=z, score=s))
        else:
            s, ev = split_oof(x, y, n_train=n_train, exponent=exponent)
            n_eval = len(ev)
            rhos.append(T.partial_correlation(y=y[ev], nuisance=z[ev], score=s))

    rho = np.asarray(rhos)
    df = n_eval - T.NUISANCE_COLUMNS - 1
    t = np.array([T.implied_t(r, n_eval) for r in rho])
    nominal = math.sqrt(df / (df - 2.0)) if df > 2 else float("nan")
    crit = float(stats.t.isf(ALPHA, df))
    return {"construction": "held_out_split" if n_train else "leave_one_out",
            "features": g, "factors": factors, "ridge_exponent": exponent,
            "n_evaluate": n_eval, "df": df, "replicates": replicates,
            "rho_sd": float(rho.std(ddof=1)),
            "implied_t_sd_ratio": float(t.std(ddof=1) / nominal),
            "null_rejection": float(np.mean(t >= crit)),
            "nominal_alpha": ALPHA}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--replicates", type=int, default=300)
    ap.add_argument("--features", type=int, default=24482)
    ap.add_argument("--seed", type=int, default=20260912)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    cohort = real_cohort()
    width = real_feature_width()
    report: dict[str, Any] = {"geometry": {**width, **{
        "n_discovery": N_DISCOVERY, "n_development": N_DEVELOPMENT,
        "age_mean": float(cohort["age"].mean()),
        "age_sd": float(cohort["age"].std(ddof=1)),
        "age_min": float(cohort["age"].min()),
        "age_max": float(cohort["age"].max()),
        "minority_sex_fraction": cohort["minority_fraction"],
        "p_confirmation12_inestimable":
            float(stats.binom.cdf(1, 12, cohort["minority_fraction"]))}},
        "arms": {}}
    print("REAL GEOMETRY: %d features (%d decision), n=%d/%d, minority sex %.3f"
          % (width["features_total"], width["features_decision"],
             N_DISCOVERY, N_DEVELOPMENT, cohort["minority_fraction"]))

    rng = np.random.default_rng(args.seed)
    check = verify_fast_path_against_frozen(rng, g=min(args.features, 3000))
    report["fast_path_verification"] = check
    print("fast path vs primal ridge: rel diff %.2e  agree=%s  "
          "(frozen learner selected exponent %.1f on pure noise)"
          % (check["relative_difference"], check["agree"],
             check["selected_exponent_on_noise"]))
    if not check["agree"]:
        print("STOP: fast path does not reproduce the primal fit")
        return 1

    for label, kw in (
            ("loo_boundary_ridge", dict(exponent=2.0, n_train=None)),
            ("loo_mid_ridge", dict(exponent=0.0, n_train=None)),
            ("split16_boundary_ridge", dict(exponent=2.0, n_train=16)),
    ):
        for factors in (8, 40):
            r = null_calibration(replicates=args.replicates, g=args.features,
                                 factors=factors, seed=args.seed + 1, **kw)
            report["arms"]["%s_f%d" % (label, factors)] = r
            print("  %-24s factors=%-3d  implied_t_sd_ratio=%.3f  "
                  "null_rejection=%.4f (nominal %.4f)"
                  % (label, factors, r["implied_t_sd_ratio"],
                     r["null_rejection"], ALPHA))

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print("written: %s" % args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
