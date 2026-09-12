#!/usr/bin/env python3
"""Does the frozen-score partial correlation transport from n=28 to n=12?

Tests the five predictions set out in `t0_v21_transport_estimand_v1.py`. The
estimand and its derivation were fixed before these arms were written, so each
arm tests a prediction rather than fitting one.

  T1  null calibration of `rho_hat` from out-of-fold scores;
  T2  attenuation -- does `rho_hat` overstate the frozen scorer's true `rho`?
  T3  end to end -- is projected power at n=12 no greater than the actual
      rejection rate of the frozen confirmatory test on fresh cohorts?
  T4  sensitivity to ridge selection, leverage profile, donor heterogeneity;
  T5  negative controls -- deliberately violate the transport condition and
      require the projection to visibly fail.

Everything is synthetic. No AT8, no partition, no real cohort, no authority is
changed by running this.
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
import t0_v21_transport_estimand_v1 as T  # noqa: E402

N_DISCOVERY = 28
N_CONFIRMATION = 12
N_GENES = 12
N_SIGNAL_GENES = 3
ALPHA = 0.025
POPULATION_SAMPLE = 6000
INNER_GRID = (-4.0, -2.0, 0.0, 2.0, 4.0)


# --------------------------------------------------------------------------
# generative model
# --------------------------------------------------------------------------

def design(n: int, rng, *, heterogeneous: bool = False):
    age = np.linspace(66.0, 94.0, n) + rng.normal(scale=0.5, size=n)
    sex = np.array([float(i % 2) for i in range(n)])
    _, learner = v21._frozen()
    z, _ = learner.nuisance_design(age, sex)
    scale = (1.0 + 0.8 * rng.random(n)) if heterogeneous else np.ones(n)
    return age, sex, z, scale


def expression(n: int, rng, *, shift: float = 0.0, heavy: bool = False):
    if heavy:
        x = rng.standard_t(3, size=(n, N_GENES)) / math.sqrt(3.0)
    else:
        x = rng.normal(size=(n, N_GENES))
    return x + shift


def outcome(x, z, scale, rho_true, rng):
    """`y` with a prescribed population partial correlation against the signal."""
    signal = x[:, :N_SIGNAL_GENES].mean(axis=1)
    s_r = T.residualize(signal, z)
    sd = float(np.std(s_r, ddof=1))
    if sd <= 0.0 or rho_true >= 1.0:
        raise RuntimeError("degenerate signal")
    b = 0.0 if rho_true == 0.0 else (rho_true / math.sqrt(1 - rho_true ** 2)) / sd
    noise = rng.normal(size=len(z)) * scale
    nuisance_part = z @ np.array([1.0, 0.02, 0.0005, 0.3])
    return nuisance_part + b * signal + noise


def _ridge(x, y, exponent):
    gram = x.T @ x
    lam = (10.0 ** float(exponent)) * float(np.trace(gram) / len(x))
    return np.linalg.solve(gram + lam * np.eye(x.shape[1]), x.T @ y)


def _inner_loo_exponent(x, y):
    best, best_loss = None, None
    for e in INNER_GRID:
        total = 0.0
        for held in range(len(y)):
            keep = np.arange(len(y)) != held
            total += float((y[held] - x[held] @ _ridge(x[keep], y[keep], e)) ** 2)
        if best_loss is None or total < best_loss or (
                total == best_loss and e < best):
            best, best_loss = e, total
    return best


def nested_oof_scores(x, y, *, inner_selection: bool):
    """The 28-fold nested procedure: one out-of-fold score per donor."""
    n = len(y)
    scores = np.empty(n, dtype=np.float64)
    for held in range(n):
        keep = np.arange(n) != held
        e = _inner_loo_exponent(x[keep], y[keep]) if inner_selection else 0.0
        scores[held] = float(x[held] @ _ridge(x[keep], y[keep], e))
    return scores


def split_rho(x, y, z, *, n_train: int, inner_selection: bool):
    """Train on a prospectively fixed subset; estimate rho only on the rest.

    The evaluation donors' outcomes enter nothing that produces the score, so
    conditional on the training split the predictor is fixed and the ordinary
    fixed-predictor theory holds exactly. This is the same situation the
    confirmation cohort is in.
    """
    train = np.arange(n_train)
    evaluate = np.arange(n_train, len(y))
    e = _inner_loo_exponent(x[train], y[train]) if inner_selection else 0.0
    beta = _ridge(x[train], y[train], e)
    score = x[evaluate] @ beta
    rho = T.partial_correlation(y=y[evaluate], nuisance=z[evaluate],
                                score=score)
    return rho, beta, len(evaluate)


def arm_t1_split(replicates, seed, *, inner_selection, n_train):
    """Null calibration of the held-out-split rho."""
    rng = np.random.default_rng(seed)
    rhos = []
    for _ in range(replicates):
        age, sex, z, scale = design(N_DISCOVERY, rng)
        x = expression(N_DISCOVERY, rng)
        y = outcome(x, z, scale, 0.0, rng)
        rho, _, n_eval = split_rho(x, y, z, n_train=n_train,
                                   inner_selection=inner_selection)
        rhos.append(rho)
    rho = np.asarray(rhos)
    n_eval = N_DISCOVERY - n_train
    t_from_rho = np.array([T.implied_t(r, n_eval) for r in rho])
    df = n_eval - T.NUISANCE_COLUMNS - 1
    nominal_sd = math.sqrt(df / (df - 2.0)) if df > 2 else float("nan")
    crit = float(stats.t.isf(ALPHA, df))
    return {
        "construction": "held_out_split", "n_train": n_train,
        "n_evaluate": n_eval, "evaluation_df": df,
        "inner_ridge_selection": inner_selection,
        "replicates": int(replicates),
        "rho_mean": float(rho.mean()), "rho_sd": float(rho.std(ddof=1)),
        "implied_t_sd": float(t_from_rho.std(ddof=1)),
        "nominal_t_sd": nominal_sd,
        "implied_t_sd_ratio": float(t_from_rho.std(ddof=1) / nominal_sd),
        "implied_t_rejection": float(np.mean(t_from_rho >= crit)),
        "nominal_alpha": ALPHA,
    }


def arm_t3_split(replicates, seed, *, inner_selection, rho_true, n_train,
                 n_permutations, **kw):
    """End to end for the split construction."""
    rng = np.random.default_rng(seed)
    projected, rejected, rho_hats = [], [], []
    for _ in range(replicates):
        age, sex, z, scale = design(N_DISCOVERY, rng,
                                    heterogeneous=kw.get("heterogeneous", False))
        x = expression(N_DISCOVERY, rng, heavy=kw.get("heavy", False))
        y = outcome(x, z, scale, rho_true, rng)
        rho_hat, beta, _ = split_rho(x, y, z, n_train=n_train,
                                     inner_selection=inner_selection)
        rho_hat = max(-0.999, min(0.999, rho_hat))
        rho_hats.append(rho_hat)
        power = T.parametric_power(rho=rho_hat, n=N_CONFIRMATION, alpha=ALPHA)
        if not power.get("estimable"):
            continue
        hit = confirmation_rejects(beta, rng, n_permutations=n_permutations,
                                   rho_true=rho_true, **kw)
        if hit is None:
            continue
        projected.append(power["power"])
        rejected.append(1.0 if hit else 0.0)
    projected, rejected = np.asarray(projected), np.asarray(rejected)
    n = len(rejected)
    se = math.sqrt(max(rejected.mean() * (1 - rejected.mean()), 0.0) / max(n, 1))
    return {
        "construction": "held_out_split", "n_train": n_train,
        "rho_true_signal": rho_true, "inner_ridge_selection": inner_selection,
        "usable_replicates": n,
        "mean_rho_hat": float(np.mean(rho_hats)),
        "mean_projected_power": float(projected.mean()),
        "actual_rejection_rate": float(rejected.mean()),
        "actual_rejection_se": se,
        "projection_minus_actual": float(projected.mean() - rejected.mean()),
        "projection_is_conservative":
            bool(projected.mean() <= rejected.mean() + 1.96 * se),
        **{k: v for k, v in kw.items()},
    }


def frozen_scorer(x, y, *, inner_selection: bool):
    e = _inner_loo_exponent(x, y) if inner_selection else 0.0
    return _ridge(x, y, e)


def population_rho(beta, rng, *, shift=0.0, heavy=False, heterogeneous=False,
                   rho_true=0.3):
    """The frozen scorer's true partial correlation, on a large fresh sample."""
    age, sex, z, scale = design(POPULATION_SAMPLE, rng,
                                heterogeneous=heterogeneous)
    x = expression(POPULATION_SAMPLE, rng, shift=shift, heavy=heavy)
    y = outcome(x, z, scale, rho_true, rng)
    return T.partial_correlation(y=y, nuisance=z, score=x @ beta)


def confirmation_rejects(beta, rng, *, n_permutations, shift=0.0, heavy=False,
                         heterogeneous=False, rho_true=0.3):
    """One frozen confirmatory test on a fresh 12-donor cohort."""
    inference = v21._frozen_inference()
    age, sex, z, scale = design(N_CONFIRMATION, rng,
                                heterogeneous=heterogeneous)
    x = expression(N_CONFIRMATION, rng, shift=shift, heavy=heavy)
    y = outcome(x, z, scale, rho_true, rng)
    score = x @ beta
    perms = v21.frozen_permutations(N_CONFIRMATION, n_permutations,
                                    int(rng.integers(1, 2 ** 31)))
    result = inference.safe_studentized_fl(y, z, score, perms)
    if not result.get("estimable"):
        return None
    return float(result["p_upper"]) <= ALPHA


# --------------------------------------------------------------------------
# arms
# --------------------------------------------------------------------------

def arm_t1(replicates, seed, *, inner_selection):
    """Null calibration: is `rho_hat` from overlapping folds well behaved?"""
    rng = np.random.default_rng(seed)
    rhos, hc3 = [], []
    for _ in range(replicates):
        age, sex, z, scale = design(N_DISCOVERY, rng)
        x = expression(N_DISCOVERY, rng)
        y = outcome(x, z, scale, 0.0, rng)
        s = nested_oof_scores(x, y, inner_selection=inner_selection)
        rhos.append(T.partial_correlation(y=y, nuisance=z, score=s))
        eff = v21.oof_effect(y=y, age=age, sex=sex, oof_scores=s)
        if eff.get("estimable"):
            hc3.append(float(eff["t_observed"]))
    rho = np.asarray(rhos)
    t_from_rho = np.array([T.implied_t(r, N_DISCOVERY) for r in rho])
    df = N_DISCOVERY - T.NUISANCE_COLUMNS - 1
    nominal_sd = math.sqrt(df / (df - 2.0))
    crit = float(stats.t.isf(ALPHA, df))
    hc3 = np.asarray(hc3)
    return {
        "inner_ridge_selection": inner_selection, "replicates": int(replicates),
        "rho_mean": float(rho.mean()), "rho_sd": float(rho.std(ddof=1)),
        "implied_t_sd": float(t_from_rho.std(ddof=1)),
        "nominal_t_sd": nominal_sd,
        "implied_t_sd_ratio": float(t_from_rho.std(ddof=1) / nominal_sd),
        "implied_t_rejection": float(np.mean(t_from_rho >= crit)),
        "hc3_t_sd_ratio": float(hc3.std(ddof=1) / nominal_sd),
        "hc3_t_rejection": float(np.mean(hc3 >= crit)),
        "nominal_alpha": ALPHA,
    }


def arm_t2(replicates, seed, *, inner_selection, rho_true, **kw):
    """Attenuation: does the out-of-fold rho overstate the frozen scorer's rho?"""
    rng = np.random.default_rng(seed)
    oof, frozen = [], []
    for _ in range(replicates):
        age, sex, z, scale = design(N_DISCOVERY, rng,
                                    heterogeneous=kw.get("heterogeneous", False))
        x = expression(N_DISCOVERY, rng, heavy=kw.get("heavy", False))
        y = outcome(x, z, scale, rho_true, rng)
        s = nested_oof_scores(x, y, inner_selection=inner_selection)
        oof.append(T.partial_correlation(y=y, nuisance=z, score=s))
        beta = frozen_scorer(x, y, inner_selection=inner_selection)
        frozen.append(population_rho(beta, rng, rho_true=rho_true, **kw))
    oof, frozen = np.asarray(oof), np.asarray(frozen)
    return {
        "rho_true_signal": rho_true, "inner_ridge_selection": inner_selection,
        "replicates": int(replicates),
        "mean_rho_oof": float(oof.mean()),
        "mean_rho_frozen_population": float(frozen.mean()),
        "mean_ratio_oof_over_frozen": float(np.mean(oof / np.maximum(frozen, 1e-9))),
        "fraction_oof_exceeds_frozen": float(np.mean(oof > frozen)),
        "conservative": bool(oof.mean() <= frozen.mean()),
        **{k: v for k, v in kw.items()},
    }


def arm_t3(replicates, seed, *, inner_selection, rho_true, n_permutations,
           **kw):
    """End to end: projected power at n=12 against actual rejection rate."""
    rng = np.random.default_rng(seed)
    projected, rejected = [], []
    for _ in range(replicates):
        age, sex, z, scale = design(N_DISCOVERY, rng,
                                    heterogeneous=kw.get("heterogeneous", False))
        x = expression(N_DISCOVERY, rng, heavy=kw.get("heavy", False))
        y = outcome(x, z, scale, rho_true, rng)
        s = nested_oof_scores(x, y, inner_selection=inner_selection)
        rho_hat = T.partial_correlation(y=y, nuisance=z, score=s)
        rho_hat = max(-0.999, min(0.999, rho_hat))
        power = T.parametric_power(rho=rho_hat, n=N_CONFIRMATION, alpha=ALPHA)
        if not power.get("estimable"):
            continue
        beta = frozen_scorer(x, y, inner_selection=inner_selection)
        hit = confirmation_rejects(beta, rng, n_permutations=n_permutations,
                                   rho_true=rho_true, **kw)
        if hit is None:
            continue
        projected.append(power["power"])
        rejected.append(1.0 if hit else 0.0)
    projected, rejected = np.asarray(projected), np.asarray(rejected)
    n = len(rejected)
    se = math.sqrt(max(rejected.mean() * (1 - rejected.mean()), 0.0) / max(n, 1))
    return {
        "rho_true_signal": rho_true, "inner_ridge_selection": inner_selection,
        "usable_replicates": n,
        "mean_projected_power": float(projected.mean()),
        "actual_rejection_rate": float(rejected.mean()),
        "actual_rejection_se": se,
        "projection_minus_actual": float(projected.mean() - rejected.mean()),
        "projection_is_conservative":
            bool(projected.mean() <= rejected.mean() + 1.96 * se),
        **{k: v for k, v in kw.items()},
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--replicates", type=int, default=400)
    ap.add_argument("--sensitivity-replicates", type=int, default=120)
    ap.add_argument("--permutations", type=int, default=199)
    ap.add_argument("--seed", type=int, default=20260911)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    report: dict[str, Any] = {"estimand": T.ESTIMAND_NAME, "alpha": ALPHA,
                              "n_discovery": N_DISCOVERY,
                              "n_confirmation": N_CONFIRMATION, "arms": {}}

    print("T1 null calibration")
    for label, sel in (("fixed_ridge", False), ("inner_selection", True)):
        r = arm_t1(args.replicates if not sel else args.sensitivity_replicates,
                   args.seed, inner_selection=sel)
        report["arms"]["T1_null_" + label] = r
        print("  %-16s rho_sd=%.4f implied_t_sd_ratio=%.3f rej=%.4f | "
              "hc3_t_sd_ratio=%.3f rej=%.4f"
              % (label, r["rho_sd"], r["implied_t_sd_ratio"],
                 r["implied_t_rejection"], r["hc3_t_sd_ratio"],
                 r["hc3_t_rejection"]))

    print("T2 attenuation")
    for rho_true in (0.30, 0.50):
        r = arm_t2(args.sensitivity_replicates, args.seed + 1,
                   inner_selection=False, rho_true=rho_true)
        report["arms"]["T2_rho%.2f" % rho_true] = r
        print("  rho_true=%.2f  oof=%.4f  frozen=%.4f  oof>frozen in %.1f%%  "
              "conservative=%s"
              % (rho_true, r["mean_rho_oof"], r["mean_rho_frozen_population"],
                 100 * r["fraction_oof_exceeds_frozen"], r["conservative"]))

    print("T3 end-to-end transport")
    for rho_true in (0.30, 0.50):
        r = arm_t3(args.sensitivity_replicates, args.seed + 2,
                   inner_selection=False, rho_true=rho_true,
                   n_permutations=args.permutations)
        report["arms"]["T3_rho%.2f" % rho_true] = r
        print("  rho_true=%.2f  projected=%.3f  actual=%.3f (se %.3f)  "
              "conservative=%s"
              % (rho_true, r["mean_projected_power"], r["actual_rejection_rate"],
                 r["actual_rejection_se"], r["projection_is_conservative"]))

    print("T4 sensitivity")
    for label, kw in (("inner_selection", {"inner_selection": True}),
                      ("heavy_leverage", {"inner_selection": False,
                                          "heavy": True}),
                      ("donor_heterogeneity", {"inner_selection": False,
                                               "heterogeneous": True})):
        r = arm_t3(args.sensitivity_replicates, args.seed + 3, rho_true=0.40,
                   n_permutations=args.permutations, **kw)
        report["arms"]["T4_" + label] = r
        print("  %-20s projected=%.3f actual=%.3f conservative=%s"
              % (label, r["mean_projected_power"], r["actual_rejection_rate"],
                 r["projection_is_conservative"]))

    print("T6 held-out-split candidate: null calibration")
    for n_train in (16, 20):
        for sel in (False, True):
            r = arm_t1_split(args.replicates if not sel
                             else args.sensitivity_replicates,
                             args.seed + 5, inner_selection=sel,
                             n_train=n_train)
            report["arms"]["T6_split_train%d_%s"
                           % (n_train, "sel" if sel else "fixed")] = r
            print("  train=%d eval=%d sel=%-5s implied_t_sd_ratio=%.3f "
                  "rej=%.4f (nominal %.4f)"
                  % (n_train, r["n_evaluate"], str(sel),
                     r["implied_t_sd_ratio"], r["implied_t_rejection"], ALPHA))

    print("T7 held-out-split candidate: end to end")
    for rho_true in (0.30, 0.50):
        r = arm_t3_split(args.sensitivity_replicates, args.seed + 6,
                         inner_selection=False, rho_true=rho_true, n_train=16,
                         n_permutations=args.permutations)
        report["arms"]["T7_split_rho%.2f" % rho_true] = r
        print("  rho_true=%.2f rho_hat=%.3f projected=%.3f actual=%.3f "
              "(se %.3f) conservative=%s"
              % (rho_true, r["mean_rho_hat"], r["mean_projected_power"],
                 r["actual_rejection_rate"], r["actual_rejection_se"],
                 r["projection_is_conservative"]))

    print("T5 negative control: confirmation drawn from a shifted population")
    r = arm_t3(args.sensitivity_replicates, args.seed + 4, inner_selection=False,
               rho_true=0.40, n_permutations=args.permutations, shift=1.5)
    report["arms"]["T5_distribution_shift"] = r
    print("  shifted   projected=%.3f actual=%.3f conservative=%s"
          % (r["mean_projected_power"], r["actual_rejection_rate"],
             r["projection_is_conservative"]))

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print("written: %s" % args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
