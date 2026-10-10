#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
import math
from pathlib import Path
from typing import Any

import numpy as np

BLOCK_KEYS = (
    ("A", "HVS"),
    ("A", "NPH52"),
    ("A", "SEA_AD"),
    ("B", "HVS"),
    ("C", "HVS"),
    ("C", "NPH52"),
    ("C", "SEA_AD"),
)
STAGE_INDEX = np.array([0, 0, 0, 1, 2, 2, 2], dtype=np.int64)
SOURCE_INDEX = np.array([0, 1, 2, 0, 0, 1, 2], dtype=np.int64)
PARAMETER_NAMES = ("mu_A", "mu_B", "mu_C", "beta_HVS", "beta_NPH52", "log_tau_source", "log_sigma")
SCENARIOS = {
    "S0": np.array([0.20, -0.20, 0.00, 0.05, -0.20, 0.20, 0.05], dtype=np.float64),
    "S1": np.array([2.00, -0.10, 0.10, 2.10, 1.90, 0.10, -0.10], dtype=np.float64),
    "S3": np.array([2.00, -2.00, 2.00, 2.05, 1.80, -2.20, 2.10], dtype=np.float64),
    "S4": np.array([1.80, 2.00, 2.20, 2.05, 2.10, 1.90, 2.00], dtype=np.float64),
}
PRIOR_REGIMES = {
    "skeptical": {"k_mu": 0.5, "k_source": 0.5, "k_sigma": 0.5},
    "reference": {"k_mu": 1.0, "k_source": 1.0, "k_sigma": 1.0},
    "diffuse": {"k_mu": 2.0, "k_source": 2.0, "k_sigma": 2.0},
}
CHAIN_SEEDS = (2026100901, 2026100902, 2026100903, 2026100904)
DF = 4.0
DEFAULT_DRAWS = 12000
DEFAULT_BURN = 4000
DEFAULT_THIN = 4


def unpack(theta: np.ndarray) -> dict[str, Any]:
    theta = np.asarray(theta, dtype=np.float64)
    if theta.shape != (7,):
        raise ValueError(f"theta must have shape (7,), got {theta.shape}")
    mu = theta[:3]
    b0, b1 = float(theta[3]), float(theta[4])
    beta = np.array([b0, b1, -b0 - b1], dtype=np.float64)
    return {
        "mu": mu,
        "beta": beta,
        "tau_source": float(np.exp(theta[5])),
        "sigma": float(np.exp(theta[6])),
    }


def _log_normal(x: np.ndarray, scale: float) -> float:
    x = np.asarray(x, dtype=np.float64)
    return float(-0.5 * np.sum((x / scale) ** 2) - x.size * math.log(scale) - 0.5 * x.size * math.log(2.0 * math.pi))


def _log_half_normal_positive(x: float, scale: float) -> float:
    if not (x > 0.0 and math.isfinite(x)):
        return -math.inf
    return math.log(math.sqrt(2.0 / math.pi)) - math.log(scale) - 0.5 * (x / scale) ** 2


def _log_centered_source_prior(beta: np.ndarray, tau: float) -> float:
    if not (tau > 0.0 and math.isfinite(tau)):
        return -math.inf
    b0, b1, b2 = map(float, beta)
    if abs(b0 + b1 + b2) > 1e-10:
        return -math.inf
    # Density on the 2-D zero-sum plane induced by three iid N(0,tau^2)
    # effects conditioned on their sum being zero.
    quad = (b0 * b0 + b1 * b1 + b0 * b1) / (tau * tau)
    return -math.log(2.0 * math.pi) - 2.0 * math.log(tau) + 0.5 * math.log(3.0) - quad


def _log_student_t(y: float, loc: float, scale: float, df: float = DF) -> float:
    if not (scale > 0.0 and math.isfinite(scale)):
        return -math.inf
    z = (y - loc) / scale
    return (
        math.lgamma((df + 1.0) / 2.0)
        - math.lgamma(df / 2.0)
        - 0.5 * math.log(df * math.pi)
        - math.log(scale)
        - 0.5 * (df + 1.0) * math.log1p((z * z) / df)
    )


def log_posterior(theta: np.ndarray, y: np.ndarray, prior: dict[str, float]) -> float:
    theta = np.asarray(theta, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    if theta.shape != (7,) or y.shape != (7,):
        raise ValueError("theta and y must both match the frozen seven-block geometry")
    if not np.all(np.isfinite(theta)) or not np.all(np.isfinite(y)):
        return -math.inf
    if theta[5] < -20.0 or theta[5] > 20.0 or theta[6] < -20.0 or theta[6] > 20.0:
        return -math.inf
    state = unpack(theta)
    mu = state["mu"]
    beta = state["beta"]
    tau = state["tau_source"]
    sigma = state["sigma"]
    lp = _log_normal(mu, float(prior["k_mu"]))
    lp += _log_centered_source_prior(beta, tau)
    lp += _log_half_normal_positive(tau, float(prior["k_source"])) + theta[5]
    lp += _log_half_normal_positive(sigma, float(prior["k_sigma"])) + theta[6]
    for i in range(7):
        loc = float(mu[STAGE_INDEX[i]] + beta[SOURCE_INDEX[i]])
        lp += _log_student_t(float(y[i]), loc, sigma)
    return float(lp)


def run_chain(
    y: np.ndarray,
    prior: dict[str, float],
    seed: int,
    draws: int = DEFAULT_DRAWS,
    burn: int = DEFAULT_BURN,
    thin: int = DEFAULT_THIN,
) -> dict[str, Any]:
    if not (0 <= burn < draws and thin >= 1):
        raise ValueError("require 0 <= burn < draws and thin >= 1")
    rng = np.random.default_rng(seed)
    theta = np.zeros(7, dtype=np.float64)
    current = log_posterior(theta, y, prior)
    if not math.isfinite(current):
        raise RuntimeError("non-finite initial log posterior")
    base = np.array([0.35, 0.35, 0.35, 0.30, 0.30, 0.20, 0.20], dtype=np.float64)
    multiplier = 1.0
    window_accept = 0
    window_total = 0
    post_accept = 0
    post_total = 0
    kept: list[np.ndarray] = []
    for it in range(draws):
        proposal = theta + rng.normal(0.0, base * multiplier)
        proposed = log_posterior(proposal, y, prior)
        accepted = False
        if math.isfinite(proposed) and math.log(rng.random()) < min(0.0, proposed - current):
            theta = proposal
            current = proposed
            accepted = True
        if it < burn:
            window_total += 1
            window_accept += int(accepted)
            if (it + 1) % 100 == 0:
                rate = window_accept / max(window_total, 1)
                if rate < 0.20:
                    multiplier *= 0.80
                elif rate > 0.50:
                    multiplier *= 1.25
                multiplier = float(np.clip(multiplier, 0.05, 20.0))
                window_accept = 0
                window_total = 0
        else:
            post_total += 1
            post_accept += int(accepted)
            if (it - burn) % thin == 0:
                kept.append(theta.copy())
    samples = np.asarray(kept, dtype=np.float64)
    expected = len(range(burn, draws, thin))
    if samples.shape != (expected, 7):
        raise RuntimeError(f"unexpected retained sample shape {samples.shape}, expected {(expected, 7)}")
    return {
        "samples": samples,
        "acceptance": post_accept / max(post_total, 1),
        "proposal_multiplier": multiplier,
        "final_log_posterior": current,
    }


def _autocorr_1d(x: np.ndarray) -> np.ndarray:
    x = np.asarray(x, dtype=np.float64)
    x = x - x.mean()
    n = x.size
    if n < 2:
        return np.ones(1)
    fft_n = 1 << (2 * n - 1).bit_length()
    f = np.fft.rfft(x, fft_n)
    acov = np.fft.irfft(f * np.conjugate(f), fft_n)[:n]
    acov /= np.arange(n, 0, -1)
    if acov[0] <= 0 or not np.isfinite(acov[0]):
        return np.concatenate(([1.0], np.zeros(n - 1)))
    return acov / acov[0]


def _ess(chains: np.ndarray) -> float:
    m, n = chains.shape
    rhos = np.vstack([_autocorr_1d(chains[j]) for j in range(m)]).mean(axis=0)
    s = 0.0
    t = 1
    while t + 1 < n:
        pair = float(rhos[t] + rhos[t + 1])
        if not math.isfinite(pair) or pair < 0.0:
            break
        s += pair
        t += 2
    return float(min(m * n, (m * n) / max(1.0 + 2.0 * s, 1e-12)))


def chain_diagnostics(chains: np.ndarray) -> dict[str, list[float]]:
    chains = np.asarray(chains, dtype=np.float64)
    if chains.ndim != 3 or chains.shape[0] < 2 or chains.shape[1] < 4:
        raise ValueError("chains must have shape (>=2, >=4, parameters)")
    m, n, p = chains.shape
    half = n // 2
    split = np.concatenate([chains[:, :half, :], chains[:, -half:, :]], axis=0)
    sm, sn, _ = split.shape
    rhats: list[float] = []
    ess: list[float] = []
    for j in range(p):
        x = split[:, :, j]
        chain_means = x.mean(axis=1)
        within_vars = x.var(axis=1, ddof=1)
        W = float(within_vars.mean())
        B = float(sn * chain_means.var(ddof=1))
        if W <= 0.0:
            rhat = 1.0 if B <= 0.0 else math.inf
        else:
            var_hat = ((sn - 1.0) / sn) * W + B / sn
            rhat = math.sqrt(max(var_hat / W, 0.0))
        rhats.append(float(rhat))
        ess.append(_ess(chains[:, :, j]))
    return {"split_rhat": rhats, "ess": ess}


def posterior_summary(chains: np.ndarray, predictive_seed: int) -> dict[str, Any]:
    chains = np.asarray(chains, dtype=np.float64)
    flat = chains.reshape(-1, chains.shape[-1])
    mu = flat[:, :3]
    tau = np.exp(flat[:, 5])
    sigma = np.exp(flat[:, 6])
    rng = np.random.default_rng(predictive_seed)
    stage: dict[str, dict[str, float]] = {}
    for j, name in enumerate(("A", "B", "C")):
        beta_new = rng.normal(0.0, tau)
        eps = rng.standard_t(df=DF, size=flat.shape[0]) * sigma
        pred = mu[:, j] + beta_new + eps
        q05, med, q95 = np.quantile(mu[:, j], [0.05, 0.5, 0.95])
        stage[name] = {
            "p_mu_gt_zero": float(np.mean(mu[:, j] > 0.0)),
            "median": float(med),
            "q05": float(q05),
            "q95": float(q95),
            "p_pred_gt_zero": float(np.mean(pred > 0.0)),
        }
    tq05, tmed, tq95 = np.quantile(tau, [0.05, 0.5, 0.95])
    sq05, smed, sq95 = np.quantile(sigma, [0.05, 0.5, 0.95])
    return {
        "stage": stage,
        "tau_source": {"q05": float(tq05), "median": float(tmed), "q95": float(tq95)},
        "sigma": {"q05": float(sq05), "median": float(smed), "q95": float(sq95)},
    }


def evaluate_scientific_criteria(summaries: dict[str, dict[str, dict[str, float]]], duplicate_rejected: bool) -> dict[str, bool]:
    c0 = all(0.35 <= summaries["S0"][s]["p_mu_gt_zero"] <= 0.65 for s in "ABC") and all(
        summaries["S0"][s]["p_pred_gt_zero"] <= 0.75 for s in "ABC"
    )
    c1 = all(
        summaries["S1"][s]["p_mu_gt_zero"] < 0.90 and summaries["S1"][s]["p_pred_gt_zero"] < 0.80
        for s in ("A", "C")
    )
    c3 = all(
        summaries["S3"][s]["p_pred_gt_zero"] < 0.85
        and (
            summaries["S3"][s]["q05"] <= 0.0 <= summaries["S3"][s]["q95"]
            or summaries["S3"][s]["p_mu_gt_zero"] < 0.95
        )
        for s in ("A", "C")
    )
    c4 = all(
        summaries["S4"][s]["p_mu_gt_zero"] > 0.95 and summaries["S4"][s]["p_pred_gt_zero"] > 0.85
        for s in ("A", "C")
    )
    return {
        "C0_null_calibration": bool(c0),
        "C1_one_source_resistance": bool(c1),
        "C2_duplicate_resistance": bool(duplicate_rejected),
        "C3_sign_flip_heterogeneity": bool(c3),
        "C4_shared_positive_recovery": bool(c4),
    }


def duplicate_attack_rejected() -> bool:
    sibling = Path(__file__).with_name("build_td_bayesian_historical_ledger.py")
    spec = importlib.util.spec_from_file_location("td_bayes_ledger_for_calibration", sibling)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load ledger builder for duplicate calibration")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    row = module.decorate_dependencies(
        {"stage": "TD57B", "source": "HVS", "panel": 0, "split": 0, "half": 0, "margin": 0.0, "model_eligible": True}
    )
    try:
        module.aggregate_stage_source_blocks([row] + [dict(row) for _ in range(20)])
    except ValueError as e:
        return "duplicate case identity" in str(e)
    return False


def run_scenario(y: np.ndarray, prior_name: str, draws: int, burn: int, thin: int) -> dict[str, Any]:
    prior = PRIOR_REGIMES[prior_name]
    chain_results = [run_chain(y, prior, seed, draws=draws, burn=burn, thin=thin) for seed in CHAIN_SEEDS]
    chains = np.stack([r["samples"] for r in chain_results], axis=0)
    diag = chain_diagnostics(chains)
    predictive_seed = 2026100990 + (0 if prior_name == "skeptical" else 10 if prior_name == "reference" else 20)
    summary = posterior_summary(chains, predictive_seed=predictive_seed)
    return {
        "summary": summary,
        "diagnostics": diag,
        "acceptance": [float(r["acceptance"]) for r in chain_results],
        "proposal_multiplier": [float(r["proposal_multiplier"]) for r in chain_results],
    }


def sampler_quality_ok(result: dict[str, Any]) -> bool:
    acceptance = result["acceptance"]
    diag = result["diagnostics"]
    return (
        all(0.10 <= x <= 0.70 for x in acceptance)
        and max(diag["split_rhat"]) <= 1.10
        and min(diag["ess"][:3]) >= 200.0
    )


def run_calibration(draws: int = DEFAULT_DRAWS, burn: int = DEFAULT_BURN, thin: int = DEFAULT_THIN) -> dict[str, Any]:
    duplicate_rejected = duplicate_attack_rejected()
    runs: dict[str, dict[str, Any]] = {}
    any_sampler_failure = False
    criteria_by_prior: dict[str, dict[str, bool]] = {}
    for prior_name in ("skeptical", "reference", "diffuse"):
        runs[prior_name] = {}
        summaries: dict[str, dict[str, dict[str, float]]] = {}
        for scenario_name in ("S0", "S1", "S3", "S4"):
            result = run_scenario(SCENARIOS[scenario_name], prior_name, draws, burn, thin)
            runs[prior_name][scenario_name] = result
            summaries[scenario_name] = result["summary"]["stage"]
            if not sampler_quality_ok(result):
                any_sampler_failure = True
        criteria_by_prior[prior_name] = evaluate_scientific_criteria(summaries, duplicate_rejected)
    criterion_names = list(criteria_by_prior["reference"].keys())
    prior_agreement = {
        name: len({criteria_by_prior[p][name] for p in criteria_by_prior}) == 1 for name in criterion_names
    }
    if any_sampler_failure:
        terminal = "SAMPLER_NOT_ESTIMABLE"
    elif not all(prior_agreement.values()):
        terminal = "PRIOR_SENSITIVE"
    elif all(criteria_by_prior["reference"].values()):
        terminal = "PASS_TD_BAYESIAN_SYNTHETIC_CALIBRATION__HISTORICAL_FIT_STILL_NOT_AUTHORIZED"
    else:
        terminal = "FAIL_TD_BAYESIAN_SYNTHETIC_CALIBRATION"
    return {
        "schema": "JEPA_TD_BAYESIAN_SYNTHETIC_CALIBRATION_V1",
        "terminal": terminal,
        "historical_values_used": False,
        "historical_verdict_labels_used": False,
        "corrected_replay_ingested": False,
        "historical_fit_authorized": False,
        "target_ranking_allowed": False,
        "duplicate_attack_rejected": duplicate_rejected,
        "criteria_by_prior": criteria_by_prior,
        "prior_agreement": prior_agreement,
        "runs": runs,
        "sampler": {"chains": 4, "seeds": list(CHAIN_SEEDS), "draws": draws, "burn": burn, "thin": thin},
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    result = run_calibration()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"terminal": result["terminal"], "out": str(args.out)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
