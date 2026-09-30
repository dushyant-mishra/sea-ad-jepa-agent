#!/usr/bin/env python3
"""Deterministic synthetic smoke for the V64 privileged-information boundary.

This is a software/architecture fixture only. It does not authorize training and
does not estimate biological recoverability.

It demonstrates three required semantics:
1) an RNA-derived shared privileged factor is recoverable from RNA;
2) an independent privileged-private factor is not;
3) forcing both into one compulsory target obscures the recoverability boundary.

A second fixture rotates the shared coordinates and verifies that recoverability
is preserved at subspace level.
"""
from __future__ import annotations

import json
import numpy as np


def mean_multivariate_r2(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    y_true = np.asarray(y_true, dtype=np.float64)
    y_pred = np.asarray(y_pred, dtype=np.float64)
    if y_true.shape != y_pred.shape or y_true.ndim != 2:
        raise ValueError("y_true/y_pred must have the same 2-D shape")
    ss_res = np.square(y_true - y_pred).sum(axis=0)
    centered = y_true - y_true.mean(axis=0, keepdims=True)
    ss_tot = np.square(centered).sum(axis=0)
    good = ss_tot > 0
    if not bool(good.any()):
        raise ValueError("all target dimensions have zero variance")
    return float(np.mean(1.0 - ss_res[good] / ss_tot[good]))


def fit_linear(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    if x.ndim != 2 or y.ndim != 2 or len(x) != len(y):
        raise ValueError("x/y must be aligned 2-D arrays")
    x1 = np.column_stack([np.ones(len(x)), x])
    coef, *_ = np.linalg.lstsq(x1, y, rcond=None)
    return coef


def predict_linear(x: np.ndarray, coef: np.ndarray) -> np.ndarray:
    x = np.asarray(x, dtype=np.float64)
    return np.column_stack([np.ones(len(x)), x]) @ coef


def subspace_cosines(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    a = np.asarray(a, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    if a.shape != b.shape or a.ndim != 2:
        raise ValueError("a/b must have equal 2-D shape")
    a = a - a.mean(axis=0, keepdims=True)
    b = b - b.mean(axis=0, keepdims=True)
    qa, _ = np.linalg.qr(a)
    qb, _ = np.linalg.qr(b)
    return np.linalg.svd(qa.T @ qb, compute_uv=False)


def run_smoke() -> dict[str, object]:
    rng = np.random.default_rng(20260930)
    n_train, n_test, p = 2400, 1200, 10
    shared_dim = private_dim = 4

    x_train = rng.normal(size=(n_train, p))
    x_test = rng.normal(size=(n_test, p))
    w = rng.normal(size=(p, shared_dim))

    shared_train = x_train @ w + 0.03 * rng.normal(size=(n_train, shared_dim))
    shared_test = x_test @ w + 0.03 * rng.normal(size=(n_test, shared_dim))
    private_train = rng.normal(size=(n_train, private_dim))
    private_test = rng.normal(size=(n_test, private_dim))

    # Equalize each target coordinate's TRAIN scale so full-state R2 cannot hide
    # private failure behind an arbitrary variance imbalance.
    shared_scale = shared_train.std(axis=0, ddof=1)
    private_scale = private_train.std(axis=0, ddof=1)
    shared_train = shared_train / shared_scale
    shared_test = shared_test / shared_scale
    private_train = private_train / private_scale
    private_test = private_test / private_scale

    full_train = np.column_stack([shared_train, private_train])
    full_test = np.column_stack([shared_test, private_test])

    shared_hat = predict_linear(x_test, fit_linear(x_train, shared_train))
    private_hat = predict_linear(x_test, fit_linear(x_train, private_train))
    full_hat = predict_linear(x_test, fit_linear(x_train, full_train))

    main = {
        "shared_mean_r2": mean_multivariate_r2(shared_test, shared_hat),
        "private_mean_r2": mean_multivariate_r2(private_test, private_hat),
        "forced_full_state_mean_r2": mean_multivariate_r2(full_test, full_hat),
    }

    rng2 = np.random.default_rng(930)
    n_train2, n_test2, p2, k2 = 1800, 900, 12, 4
    x_train2 = rng2.normal(size=(n_train2, p2))
    x_test2 = rng2.normal(size=(n_test2, p2))
    w2 = rng2.normal(size=(p2, k2))
    z_train = x_train2 @ w2 + 0.02 * rng2.normal(size=(n_train2, k2))
    z_test = x_test2 @ w2 + 0.02 * rng2.normal(size=(n_test2, k2))
    q, _ = np.linalg.qr(rng2.normal(size=(k2, k2)))
    z_train = z_train @ q
    z_test = z_test @ q
    z_hat = predict_linear(x_test2, fit_linear(x_train2, z_train))
    c = subspace_cosines(z_test, z_hat)

    out = {
        "schema": "V64_PRIVILEGED_INFORMATION_ARCHITECTURE_SMOKE_V1",
        "status": "SYNTHETIC_SOFTWARE_SMOKE_ONLY",
        "main": main,
        "rotation_aware": {
            "mean_principal_angle_cosine": float(c.mean()),
            "minimum_principal_angle_cosine": float(c.min()),
        },
        "pass": bool(
            main["shared_mean_r2"] > 0.98
            and main["private_mean_r2"] < 0.05
            and main["forced_full_state_mean_r2"] < main["shared_mean_r2"] - 0.20
            and main["forced_full_state_mean_r2"] > main["private_mean_r2"] + 0.20
            and float(c.min()) > 0.99
        ),
        "training_authorized": False,
    }
    return out


def main() -> int:
    out = run_smoke()
    print(json.dumps(out, sort_keys=True, indent=2))
    return 0 if out["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
