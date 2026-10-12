#!/usr/bin/env python3
"""Truth-blind held-out predictive summaries for V79 V2_CORE qualification fits.

These metrics are descriptive/non-gating. They consume only blinded design/support and
same/new-donor observations plus the final active posterior lineage. Oracle truth is
never available on this surface.
"""
from __future__ import annotations

import math
from typing import Mapping

import numpy as np

import v79_v2_core_fit_model as M


class FitPredictiveRefused(RuntimeError):
    pass


def _refuse(msg: str):
    raise FitPredictiveRefused(f"REFUSED V2_CORE heldout predictive: {msg}")


def select_posterior_draws(samples_by_chain: Mapping[str, np.ndarray], *, stored_draws: int = 200) -> dict[str, np.ndarray]:
    if not isinstance(samples_by_chain, Mapping) or not samples_by_chain:
        _refuse("posterior sample mapping required")
    flattened = {}
    n_total = None
    for name, value in samples_by_chain.items():
        a = np.asarray(value, dtype=float)
        if a.ndim < 2 or a.shape[0] < 1 or a.shape[1] < 1 or np.any(~np.isfinite(a)):
            _refuse(f"invalid chain/draw array for {name}")
        flat = a.reshape((-1,) + a.shape[2:])
        if n_total is None:
            n_total = flat.shape[0]
        elif flat.shape[0] != n_total:
            _refuse("posterior sites have inconsistent chain/draw counts")
        flattened[str(name)] = flat
    if not isinstance(stored_draws, int) or stored_draws <= 0 or n_total is None or n_total < stored_draws:
        _refuse("insufficient posterior draws for frozen heldout projection")
    idx = np.linspace(0, n_total - 1, stored_draws, dtype=np.int64)
    return {k: np.asarray(v[idx]) for k, v in flattened.items()}


def _require_sites(samples: Mapping[str, np.ndarray], part: str) -> None:
    required = {"alpha", "class_contrasts", "source_contrasts", "donor_sd", "donor_raw"}
    required |= {"beta_depth1", "beta_depth2"} if part == "detection" else {"gamma_depth1", "gamma_depth2", "sigma"}
    if set(samples) != required:
        _refuse(f"posterior site set differs for {part}: extra={sorted(set(samples)-required)}, missing={sorted(required-set(samples))}")


def _posterior_fixed_eta(samples: Mapping[str, np.ndarray], prepared: Mapping[str, np.ndarray], part: str) -> np.ndarray:
    _require_sites(samples, part)
    n_draws = len(np.asarray(samples["alpha"]))
    n_cells = len(np.asarray(prepared["z"]))
    alpha = np.asarray(samples["alpha"], dtype=float).reshape(n_draws, 1)
    b1 = np.asarray(samples["beta_depth1" if part == "detection" else "gamma_depth1"], dtype=float).reshape(n_draws, 1)
    b2 = np.asarray(samples["beta_depth2" if part == "detection" else "gamma_depth2"], dtype=float).reshape(n_draws, 1)
    cc = np.asarray(samples["class_contrasts"], dtype=float)
    sc = np.asarray(samples["source_contrasts"], dtype=float)
    if cc.shape != (n_draws, 2) or sc.shape != (n_draws, 2):
        _refuse("class/source posterior contrast shape differs")
    z = np.asarray(prepared["z"], dtype=float).reshape(1, n_cells)
    q = np.asarray(prepared["q"], dtype=float).reshape(1, n_cells)
    class_rows = np.asarray(prepared["class_rows"], dtype=float)
    source_rows = np.asarray(prepared["source_rows"], dtype=float)
    eta = alpha + b1 * z + b2 * q
    eta = eta + cc @ class_rows.T + sc @ source_rows.T
    return np.asarray(eta, dtype=float)


def _same_donor_eta(samples: Mapping[str, np.ndarray], prepared: Mapping[str, np.ndarray], part: str) -> np.ndarray:
    eta = _posterior_fixed_eta(samples, prepared, part)
    donor_raw = np.asarray(samples["donor_raw"], dtype=float)
    donor_sd = np.asarray(samples["donor_sd"], dtype=float).reshape(-1)
    rows = np.asarray(prepared["donor_rows"], dtype=float)
    if donor_raw.ndim != 2 or donor_raw.shape[0] != eta.shape[0] or donor_raw.shape[1] != rows.shape[1]:
        _refuse("donor posterior/design shape differs")
    if donor_sd.shape != (eta.shape[0],):
        _refuse("donor SD posterior shape differs")
    if rows.shape[1]:
        eta = eta + (donor_raw * donor_sd[:, None]) @ rows.T
    return eta


def _gh_nodes_weights(nodes: int) -> tuple[np.ndarray, np.ndarray]:
    if nodes != 40:
        _refuse("new-donor heldout prediction requires exactly 40 Gauss-Hermite nodes")
    x, w = np.polynomial.hermite.hermgauss(nodes)
    return np.asarray(x, dtype=float), np.asarray(w / math.sqrt(math.pi), dtype=float)


def _new_donor_sd_scale(samples: Mapping[str, np.ndarray], prepared: Mapping[str, np.ndarray]) -> np.ndarray:
    sd = np.asarray(samples["donor_sd"], dtype=float).reshape(-1)
    rows = np.asarray(prepared["donor_rows"], dtype=float)
    row_norm = np.sqrt(np.sum(rows * rows, axis=1)) if rows.shape[1] else np.zeros(rows.shape[0], dtype=float)
    return sd[:, None] * row_norm[None, :]


def _sigmoid(x: np.ndarray) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    out = np.empty_like(x)
    pos = x >= 0
    out[pos] = 1.0 / (1.0 + np.exp(-x[pos]))
    ex = np.exp(x[~pos])
    out[~pos] = ex / (1.0 + ex)
    return out


def _calibration_table(prob: np.ndarray, y: np.ndarray, *, bins: int) -> list[dict]:
    if bins != 10:
        _refuse("detection calibration requires exactly 10 fixed bins")
    p = np.asarray(prob, dtype=float).reshape(-1)
    y = np.asarray(y, dtype=int).reshape(-1)
    if p.size != y.size or p.size == 0 or np.any((p < 0) | (p > 1)) or np.any((y != 0) & (y != 1)):
        _refuse("invalid calibration inputs")
    idx = np.minimum((p * bins).astype(int), bins - 1)
    rows = []
    for b in range(bins):
        m = idx == b
        n = int(np.sum(m))
        rows.append({
            "bin_index": b,
            "lower": b / bins,
            "upper": (b + 1) / bins,
            "n": n,
            "mean_predicted": None if n == 0 else float(np.mean(p[m])),
            "observed_rate": None if n == 0 else float(np.mean(y[m])),
        })
    return rows


def detection_heldout_metrics(samples_by_chain: Mapping[str, np.ndarray], *, design: Mapping[str, np.ndarray], detected: np.ndarray,
                               measured_mask: np.ndarray, new_donor: bool, posterior_draws: int = 200,
                               calibration_bins: int = 10, gh_nodes: int = 40) -> dict:
    samples = select_posterior_draws(samples_by_chain, stored_draws=posterior_draws)
    prepared = M.prepare_design(design)
    mask = np.asarray(measured_mask, dtype=bool).reshape(-1)
    y_all = np.asarray(detected, dtype=int).reshape(-1)
    if len(mask) != len(prepared["z"]) or len(y_all) != len(mask) or not np.any(mask):
        _refuse("unaligned/empty detection heldout mask")
    y = y_all[mask]
    if np.any((y != 0) & (y != 1)):
        _refuse("detection heldout observations must be binary")
    if new_donor:
        eta = _posterior_fixed_eta(samples, prepared, "detection")[:, mask]
        scale = _new_donor_sd_scale(samples, prepared)[:, mask]
        nodes, weights = _gh_nodes_weights(gh_nodes)
        acc = np.zeros_like(eta)
        for node, weight in zip(nodes, weights):
            acc += weight * _sigmoid(eta + math.sqrt(2.0) * scale * node)
        p = np.mean(acc, axis=0)
        mode = "new_donor"
        gh = gh_nodes
    else:
        eta = _same_donor_eta(samples, prepared, "detection")[:, mask]
        p = np.mean(_sigmoid(eta), axis=0)
        mode = "same_donor"
        gh = None
    eps = np.finfo(float).eps
    pc = np.clip(p, eps, 1.0 - eps)
    log_loss = -np.mean(y * np.log(pc) + (1 - y) * np.log1p(-pc))
    return {
        "schema": "V79_V2_CORE_DETECTION_HELDOUT_V1",
        "replicate_mode": mode,
        "posterior_draws": int(posterior_draws),
        "gauss_hermite_nodes": gh,
        "n_measured": int(y.size),
        "mean_log_loss": float(log_loss),
        "predicted_prevalence": float(np.mean(p)),
        "observed_prevalence": float(np.mean(y)),
        "calibration_bins": _calibration_table(p, y, bins=calibration_bins),
    }


def _normal_logpdf(y: np.ndarray, mu: np.ndarray, sigma: np.ndarray) -> np.ndarray:
    return -0.5 * math.log(2.0 * math.pi) - np.log(sigma) - 0.5 * ((y - mu) / sigma) ** 2


def _logmeanexp(log_values: np.ndarray, axis: int) -> np.ndarray:
    a = np.asarray(log_values, dtype=float)
    m = np.max(a, axis=axis, keepdims=True)
    return np.squeeze(m, axis=axis) + np.log(np.mean(np.exp(a - m), axis=axis))


def positive_heldout_metrics(samples_by_chain: Mapping[str, np.ndarray], *, design: Mapping[str, np.ndarray], observed: np.ndarray,
                              positive_mask: np.ndarray, new_donor: bool, posterior_draws: int = 200,
                              gh_nodes: int = 40) -> dict:
    samples = select_posterior_draws(samples_by_chain, stored_draws=posterior_draws)
    prepared = M.prepare_design(design)
    mask = np.asarray(positive_mask, dtype=bool).reshape(-1)
    obs = np.asarray(observed, dtype=float).reshape(-1)
    if len(mask) != len(prepared["z"]) or len(obs) != len(mask) or not np.any(mask):
        _refuse("unaligned/empty positive heldout mask")
    if np.any(~np.isfinite(obs[mask])) or np.any(obs[mask] <= 0):
        _refuse("positive heldout observations must be finite and >0")
    y = np.log(obs[mask])[None, :]
    sigma = np.asarray(samples["sigma"], dtype=float).reshape(-1, 1)
    if np.any(~np.isfinite(sigma)) or np.any(sigma <= 0):
        _refuse("positive posterior sigma must be finite and >0")
    if new_donor:
        fixed = _posterior_fixed_eta(samples, prepared, "positive")[:, mask]
        scale = _new_donor_sd_scale(samples, prepared)[:, mask]
        nodes, weights = _gh_nodes_weights(gh_nodes)
        # Integrate density over the new donor random effect for each posterior draw.
        density = np.zeros_like(fixed)
        for node, weight in zip(nodes, weights):
            mu = fixed + math.sqrt(2.0) * scale * node
            density += weight * np.exp(_normal_logpdf(y, mu, sigma))
        density = np.maximum(density, np.finfo(float).tiny)
        cell_lpd = _logmeanexp(np.log(density), axis=0)
        mode = "new_donor"
        gh = gh_nodes
    else:
        mu = _same_donor_eta(samples, prepared, "positive")[:, mask]
        log_density = _normal_logpdf(y, mu, sigma)
        cell_lpd = _logmeanexp(log_density, axis=0)
        mode = "same_donor"
        gh = None
    return {
        "schema": "V79_V2_CORE_POSITIVE_HELDOUT_V1",
        "replicate_mode": mode,
        "posterior_draws": int(posterior_draws),
        "gauss_hermite_nodes": gh,
        "n_positive": int(np.sum(mask)),
        "mean_lpd": float(np.mean(cell_lpd)),
    }
