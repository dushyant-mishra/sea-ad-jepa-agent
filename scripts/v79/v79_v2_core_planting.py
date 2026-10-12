#!/usr/bin/env python3
"""Pure deterministic planting/design primitives for V79 V2_CORE worlds.

No file-writing entrypoint lives here. These functions consume frozen authorities
and return in-memory design/truth arrays only.
"""
from __future__ import annotations

import numpy as np


def _seed(root: int, *spawn_key: int) -> int:
    ss = np.random.SeedSequence(entropy=int(root), spawn_key=tuple(int(x) for x in spawn_key))
    return int(ss.generate_state(1, dtype=np.uint32)[0])


def build_base_design(authority: dict[str, np.ndarray], *, donors_per_source: tuple[int, ...], root: int) -> dict[str, np.ndarray]:
    """Build the prospectively frozen crossed BASE design."""
    src0 = np.asarray(authority["src"], dtype=np.int64)
    donor0 = np.asarray(authority["donor"], dtype=np.int64)
    cls0 = np.asarray(authority["cls"], dtype=np.int64)
    op0 = np.asarray(authority["op"], dtype=np.int64)
    log0 = np.asarray(authority["log_lib"], dtype=np.float64)
    sources = np.sort(np.unique(src0))
    if len(donors_per_source) != len(sources):
        raise SystemExit("STOP: donors_per_source length does not match source count")
    for d in np.unique(donor0):
        if len(np.unique(src0[donor0 == d])) != 1:
            raise SystemExit("STOP: authority donor spans sources")
    for o in np.unique(op0):
        if len(np.unique(src0[op0 == o])) != 1:
            raise SystemExit("STOP: authority operator spans sources")

    rng = np.random.default_rng(_seed(root, 100, 0, 0))
    class_levels, class_counts = np.unique(cls0, return_counts=True)
    class_p = class_counts.astype(float) / class_counts.sum()
    pooled_log = log0.copy()

    out_src: list[int] = []
    out_donor: list[int] = []
    out_cls: list[int] = []
    out_op: list[int] = []
    out_log: list[float] = []
    next_donor = 0
    for s, n_new in zip(sources, donors_per_source):
        source_donors = np.unique(donor0[src0 == s])
        donor_counts = np.asarray([(donor0 == d).sum() for d in source_donors], dtype=np.int64)
        source_ops = np.unique(op0[src0 == s])
        if len(source_donors) == 0 or len(source_ops) == 0:
            raise SystemExit("STOP: empty source support in authority")
        sampled_counts = rng.choice(donor_counts, size=int(n_new), replace=True)
        for n_cell in sampled_counts:
            n = int(n_cell)
            out_src.extend([int(s)] * n)
            out_donor.extend([next_donor] * n)
            out_cls.extend(rng.choice(class_levels, size=n, replace=True, p=class_p).astype(int).tolist())
            out_log.extend(rng.choice(pooled_log, size=n, replace=True).astype(float).tolist())
            out_op.extend(rng.choice(source_ops, size=n, replace=True).astype(int).tolist())
            next_donor += 1
    return {
        "src": np.asarray(out_src, dtype=np.int64),
        "donor": np.asarray(out_donor, dtype=np.int64),
        "cls": np.asarray(out_cls, dtype=np.int64),
        "op": np.asarray(out_op, dtype=np.int64),
        "log_lib": np.asarray(out_log, dtype=np.float64),
    }


def latin_hypercube_empirical(values: np.ndarray, *, G: int, world_index: int, quantity_index: int,
                               root: int, p_lo: float = 0.05, p_hi: float = 0.95) -> tuple[np.ndarray, np.ndarray]:
    """Frozen p5-p95 empirical LHS with permutation per quantity and jitter per gene."""
    vals = np.asarray(values, dtype=float)
    vals = vals[np.isfinite(vals)]
    if len(vals) == 0 or not (0 <= p_lo < p_hi <= 1):
        raise SystemExit("STOP: invalid LHS empirical support")
    perm_rng = np.random.default_rng(_seed(root, world_index, 9999, 50 + int(quantity_index)))
    perm = perm_rng.permutation(int(G))
    levels = np.empty(int(G), dtype=float)
    for g in range(int(G)):
        jitter = np.random.default_rng(_seed(root, world_index, g, 10)).uniform()
        levels[g] = p_lo + (p_hi - p_lo) * (perm[g] + jitter) / float(G)
    return np.quantile(vals, levels, method="linear"), levels


def calibration_magnitudes(cal: dict) -> dict:
    """Reproduce the contract-builder calibration pools byte-semantically."""
    rows = cal["per_gene"]

    def vals(part: str, key: str, all_sources: bool = False, absolute: bool = False) -> np.ndarray:
        out: list[float] = []
        for r in rows:
            if part not in r or (all_sources and not r["all_sources_measured"]) or key not in r[part]:
                continue
            v = r[part][key]
            if isinstance(v, list):
                out.extend(abs(float(x)) if absolute else float(x) for x in v)
            else:
                out.append(abs(float(v)) if absolute else float(v))
        return np.asarray(out, dtype=float)

    m: dict[str, dict[str, np.ndarray]] = {}
    for part, P in (("det", "detection"), ("pos", "positive")):
        m[P] = {
            "depth1": vals(part, "depth"),
            "depth2": vals(part, "depth2"),
            "abs_class": vals(part, "cls", absolute=True),
            "abs_source": vals(part, "src", all_sources=True, absolute=True),
            "donor_sd": vals(part, "donor_sd"),
        }
        if part == "pos":
            m[P]["intercept"] = vals(part, "intercept", all_sources=True)
            m[P]["sigma"] = vals(part, "sigma")
    m["detection"]["prevalence"] = np.asarray([float(r["prevalence"]) for r in rows], dtype=float)
    return m


def _contrast_coefficients(magnitudes: np.ndarray, *, world_index: int, root: int, sign_offset: int) -> tuple[np.ndarray, np.ndarray]:
    """Give the two normalized-Helmert contrast coordinates independent seeded signs."""
    G = len(magnitudes)
    signs = np.empty((G, 2), dtype=np.int8)
    for g in range(G):
        rng = np.random.default_rng(_seed(root, world_index, g, 11))
        draws = rng.choice(np.array([-1, 1], dtype=np.int8), size=4, replace=True)
        signs[g] = draws[sign_offset:sign_offset + 2]
    return magnitudes[:, None] * signs.astype(float), signs


def build_q00_planting(cal: dict, payload: dict, *, world_index: int, G: int) -> dict:
    """Build Q00-style per-gene magnitudes from the masked development calibration."""
    mags = calibration_magnitudes(cal)
    root = int(payload["seeds"]["root"])
    qid = {
        "det_prevalence": 0, "det_depth1": 1, "det_depth2": 2, "det_abs_class_0": 3,
        "det_abs_class_1": 4, "det_abs_source_0": 5, "det_abs_source_1": 6, "det_donor_sd": 7,
        "pos_intercept": 8, "pos_depth1": 9, "pos_depth2": 10, "pos_abs_class_0": 11,
        "pos_abs_class_1": 12, "pos_abs_source_0": 13, "pos_abs_source_1": 14,
        "pos_donor_sd": 15, "pos_sigma": 16,
    }
    levels: dict[str, np.ndarray] = {}

    def lhs(part: str, key: str, name: str, idx: int | None = None) -> np.ndarray:
        qi = qid[name if idx is None else f"{name}_{idx}"]
        x, lev = latin_hypercube_empirical(mags[part][key], G=G, world_index=world_index,
                                           quantity_index=qi, root=root)
        levels[name if idx is None else f"{name}_{idx}"] = lev
        return x

    det_class_mags = np.column_stack([lhs("detection", "abs_class", "det_abs_class", j) for j in range(2)])
    det_source_mags = np.column_stack([lhs("detection", "abs_source", "det_abs_source", j) for j in range(2)])
    pos_class_mags = np.column_stack([lhs("positive", "abs_class", "pos_abs_class", j) for j in range(2)])
    pos_source_mags = np.column_stack([lhs("positive", "abs_source", "pos_abs_source", j) for j in range(2)])
    det_cls = np.empty_like(det_class_mags)
    det_src = np.empty_like(det_source_mags)
    pos_cls = np.empty_like(pos_class_mags)
    pos_src = np.empty_like(pos_source_mags)
    sign_rec = np.empty((G, 4), dtype=np.int8)
    for g in range(G):
        rng = np.random.default_rng(_seed(root, world_index, g, 11))
        sign_rec[g] = rng.choice(np.array([-1, 1], dtype=np.int8), size=4, replace=True)
        det_cls[g] = det_class_mags[g] * sign_rec[g, :2]
        det_src[g] = det_source_mags[g] * sign_rec[g, 2:]
        pos_cls[g] = pos_class_mags[g] * sign_rec[g, :2]
        pos_src[g] = pos_source_mags[g] * sign_rec[g, 2:]

    det_prev = lhs("detection", "prevalence", "det_prevalence")
    return {
        "detection": {
            "prevalence": det_prev,
            "depth1": lhs("detection", "depth1", "det_depth1"),
            "depth2": lhs("detection", "depth2", "det_depth2"),
            "class_contrasts": det_cls,
            "source_contrasts": det_src,
            "donor_sd": lhs("detection", "donor_sd", "det_donor_sd"),
        },
        "positive": {
            "intercept": lhs("positive", "intercept", "pos_intercept"),
            "depth1": lhs("positive", "depth1", "pos_depth1"),
            "depth2": lhs("positive", "depth2", "pos_depth2"),
            "class_contrasts": pos_cls,
            "source_contrasts": pos_src,
            "donor_sd": lhs("positive", "donor_sd", "pos_donor_sd"),
            "sigma": lhs("positive", "sigma", "pos_sigma"),
        },
        "lhs_levels": levels,
        "contrast_signs": sign_rec,
    }


def solve_detection_intercept(non_intercept: np.ndarray, measured: np.ndarray, *, target_prevalence: float) -> float:
    """Solve alpha so mean expit(alpha+eta) over measured cells hits target."""
    eta = np.asarray(non_intercept, dtype=float)
    mask = np.asarray(measured, dtype=bool)
    if eta.shape != mask.shape or not mask.any() or not (0.0 < target_prevalence < 1.0):
        raise SystemExit("STOP: invalid detection intercept calibration inputs")
    x = eta[mask]
    lo, hi = -40.0, 40.0
    for _ in range(120):
        mid = (lo + hi) / 2.0
        z = np.clip(mid + x, -40.0, 40.0)
        p = 1.0 / (1.0 + np.exp(-z))
        if float(p.mean()) < target_prevalence:
            lo = mid
        else:
            hi = mid
    return float((lo + hi) / 2.0)


def _center_within_source(x: np.ndarray, src_by_donor: np.ndarray) -> np.ndarray:
    out = np.asarray(x, dtype=float).copy()
    for s in np.unique(src_by_donor):
        m = src_by_donor == s
        out[m] -= out[m].mean(axis=0, keepdims=True)
    return out


def _build_donor_effects(src_by_donor: np.ndarray, donor_sd: np.ndarray, *, world_index: int,
                         part: str, root: int, factor_stream: int,
                         detection_stream: int, positive_stream: int) -> dict[str, np.ndarray]:
    src = np.asarray(src_by_donor, dtype=np.int64)
    sd = np.asarray(donor_sd, dtype=float)
    D, G = len(src), len(sd)
    if part not in ("detection", "positive"):
        raise ValueError("part must be detection or positive")
    f_rng = np.random.default_rng(_seed(root, world_index, 9999, factor_stream))
    factor = f_rng.normal(size=D)
    l_rng = np.random.default_rng(_seed(root, world_index, 9999, 4))
    loaded = np.sort(l_rng.choice(G, size=G // 2, replace=False))
    lam = np.zeros(G, dtype=float)
    lam[loaded] = 0.6
    stream = detection_stream if part == "detection" else positive_stream
    raw = np.empty((D, G), dtype=float)
    for g in range(G):
        e_rng = np.random.default_rng(_seed(root, world_index, g, stream))
        e = e_rng.normal(size=D)
        raw[:, g] = lam[g] * factor + np.sqrt(1.0 - lam[g] ** 2) * e
    raw = _center_within_source(raw, src)
    effects = raw * sd[None, :]
    return {
        "effects": effects,
        "lambda": lam,
        "shared_factor": _center_within_source(factor[:, None], src)[:, 0],
        "raw_centered": raw,
    }


def build_donor_effects(src_by_donor: np.ndarray, donor_sd: np.ndarray, *, world_index: int,
                        part: str, root: int) -> dict[str, np.ndarray]:
    """Plant TRAIN/same-donor effects with frozen streams 2 and 12/13."""
    return _build_donor_effects(src_by_donor, donor_sd, world_index=world_index, part=part, root=root,
                                factor_stream=2, detection_stream=12, positive_stream=13)


def build_new_donor_effects(src_by_donor: np.ndarray, donor_sd: np.ndarray, *, world_index: int,
                            part: str, root: int) -> dict[str, np.ndarray]:
    """Plant held-out new-donor effects with frozen streams 3 and 18/19.

    Factor-loading assignment remains stream 4, so the same seeded half of genes
    carries the shared donor factor while the factor realization and idiosyncratic
    donor effects are new.
    """
    return _build_donor_effects(src_by_donor, donor_sd, world_index=world_index, part=part, root=root,
                                factor_stream=3, detection_stream=18, positive_stream=19)
