#!/usr/bin/env python3
"""Pure in-memory observation generation for V79 V2_CORE synthetic worlds.

No disk emission, fitting or benchmark code lives here.
"""
from __future__ import annotations

import numpy as np


def _seed(root: int, world_index: int, gene_index: int, stream: int) -> int:
    ss = np.random.SeedSequence(entropy=int(root), spawn_key=(int(world_index), int(gene_index), int(stream)))
    return int(ss.generate_state(1, dtype=np.uint32)[0])


def normalized_helmert(k: int) -> np.ndarray:
    """Return k x (k-1) orthonormal Helmert contrasts with column sums zero."""
    if k < 2:
        raise ValueError("k must be >=2")
    H = np.zeros((k, k - 1), dtype=np.float64)
    for j in range(k - 1):
        den = np.sqrt((j + 1) * (j + 2))
        H[:j + 1, j] = 1.0 / den
        H[j + 1, j] = -(j + 1) / den
    return H


def depth_basis(log_lib: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    x = np.asarray(log_lib, dtype=np.float64)
    sd = float(x.std(ddof=0))
    if not np.isfinite(sd) or sd <= 0:
        raise SystemExit("STOP: log-library SD must be positive")
    z = (x - float(x.mean())) / sd
    return z, z * z - 1.0


def linear_predictor(design: dict[str, np.ndarray], part: dict, *, operator_offsets: np.ndarray | None = None) -> np.ndarray:
    z, q = depth_basis(design["log_lib"])
    cls = np.asarray(design["cls"], dtype=np.int64)
    src = np.asarray(design["src"], dtype=np.int64)
    donor = np.asarray(design["donor"], dtype=np.int64)
    op = np.asarray(design["op"], dtype=np.int64)
    G = len(np.asarray(part["intercept"]))
    Hc = normalized_helmert(len(np.unique(cls)))
    Hs = normalized_helmert(len(np.unique(src)))
    if np.min(cls) < 0 or np.max(cls) >= Hc.shape[0] or np.min(src) < 0 or np.max(src) >= Hs.shape[0]:
        raise SystemExit("STOP: class/source must be contiguous integer codes")
    eta = np.asarray(part["intercept"], dtype=float)[None, :].copy()
    eta = np.broadcast_to(eta, (len(z), G)).copy()
    eta += z[:, None] * np.asarray(part["depth1"], dtype=float)[None, :]
    eta += q[:, None] * np.asarray(part["depth2"], dtype=float)[None, :]
    eta += Hc[cls] @ np.asarray(part["class_contrasts"], dtype=float).T
    eta += Hs[src] @ np.asarray(part["source_contrasts"], dtype=float).T
    donor_eff = np.asarray(part["donor_effects"], dtype=float)
    if np.max(donor) >= donor_eff.shape[0]:
        raise SystemExit("STOP: donor effects do not cover design donors")
    eta += donor_eff[donor]
    if operator_offsets is not None:
        oo = np.asarray(operator_offsets, dtype=float)
        if oo.ndim != 2 or oo.shape[1] != G or np.max(op) >= oo.shape[0]:
            raise SystemExit("STOP: operator-offset shape mismatch")
        eta += oo[op]
    return eta


def _noise_matrix(n: int, G: int, *, root: int, world_index: int, stream: int, normal: bool) -> np.ndarray:
    out = np.empty((n, G), dtype=np.float64)
    for g in range(G):
        rng = np.random.default_rng(_seed(root, world_index, g, stream))
        out[:, g] = rng.normal(size=n) if normal else rng.uniform(size=n)
    return out


def generate_observation(design: dict[str, np.ndarray], truth: dict, support: np.ndarray, *, world_index: int,
                         root: int, poison: float = -1.0, replicate: str = "train",
                         pairing_parent_world: int | None = None,
                         operator_offsets_detection: np.ndarray | None = None,
                         operator_offsets_positive: np.ndarray | None = None) -> dict[str, np.ndarray]:
    """Generate measured Bernoulli + continuous lognormal observations.

    For Q11 paired counterfactuals, pairing_parent_world fixes all base-noise streams
    to Q10 while operator offsets alter only the linear predictors.
    """
    support = np.asarray(support, dtype=bool)
    n = len(np.asarray(design["src"]))
    G = support.shape[1]
    if support.shape[0] != n:
        raise SystemExit("STOP: support/design cell count mismatch")
    det = truth["detection"]; pos = truth["positive"]
    eta = linear_predictor(design, det, operator_offsets=operator_offsets_detection)
    mu = linear_predictor(design, pos, operator_offsets=operator_offsets_positive)
    if eta.shape != support.shape or mu.shape != support.shape:
        raise SystemExit("STOP: truth/design/support gene shape mismatch")

    if replicate == "train":
        det_stream, pos_stream = 14, 15
    elif replicate == "same_donor":
        det_stream, pos_stream = 16, 17
    else:
        raise ValueError("replicate must be train or same_donor")
    base_world = int(pairing_parent_world) if pairing_parent_world is not None else int(world_index)
    u = _noise_matrix(n, G, root=root, world_index=base_world, stream=det_stream, normal=False)
    eps = _noise_matrix(n, G, root=root, world_index=base_world, stream=pos_stream, normal=True)
    p = 1.0 / (1.0 + np.exp(-np.clip(eta, -40.0, 40.0)))
    detected = (u < p) & support
    sigma = np.asarray(pos["sigma"], dtype=float)
    if sigma.shape != (G,) or np.any(sigma <= 0):
        raise SystemExit("STOP: positive sigma must be positive per gene")
    positive = np.exp(mu + eps * sigma[None, :])
    observed = np.zeros((n, G), dtype=np.float64)
    observed[detected] = positive[detected]
    observed[~support] = float(poison)
    # Keep positive latent draws available for deterministic audit; scientific scoring
    # uses them only where detection is true and support is measured.
    return {
        "eta_detection": eta,
        "mu_positive": mu,
        "prob_detection": p,
        "base_uniform": u,
        "base_normal": eps,
        "detected": detected,
        "positive_value": positive,
        "observed": observed,
        "support": support.copy(),
    }
