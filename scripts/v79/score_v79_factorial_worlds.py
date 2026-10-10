from __future__ import annotations

from typing import Any, Callable, Mapping
import importlib

import numpy as np
from scipy import sparse

from .build_v79_factorial_worlds import FactorialWorlds, WorldArm

CANONICAL_THRESHOLD = 0.30
SENSITIVITY_THRESHOLDS = (0.10, 0.20, 0.30, 0.40)


def _default_legacy_score():
    mod = importlib.import_module("scripts.v77.v77_matched_scoring")
    return mod.score_matched


def _default_localization_backend():
    return importlib.import_module("scripts.v79.v79_detection_localization")


def _dense_if_needed(x):
    return x.toarray() if sparse.issparse(x) else np.asarray(x)


def _build_base_strata(loc, broad_class: np.ndarray, depth: np.ndarray) -> np.ndarray:
    broad = np.asarray(broad_class).astype(str)
    depth = np.asarray(depth, dtype=float)
    out = np.empty(len(broad), dtype=object)
    for cls in np.unique(broad):
        ix = np.flatnonzero(broad == cls)
        bins = loc.quantile_depth_bins(depth[ix])
        if bins.get("supported"):
            labels = np.asarray(bins["labels"], dtype=int)
            for pos, b in zip(ix, labels):
                out[pos] = f"class={cls}|depth={int(b)}"
        else:
            for pos in ix:
                out[pos] = f"class={cls}|depth=UNSUPPORTED"
    return out.astype(str)


def score_world(world: WorldArm, universe: np.ndarray, *,
                legacy_score_fn: Callable | None = None,
                localization_backend=None, n_hvg: int = 3000) -> dict[str, Any]:
    legacy = legacy_score_fn or _default_legacy_score()
    loc = localization_backend or _default_localization_backend()
    counts = world.observed.counts
    universe = np.asarray(universe, dtype=np.int64)
    broad = np.asarray(world.latent.broad_class)

    legacy_result = legacy(_dense_if_needed(counts), universe, broad, n_hvg=int(n_hvg))
    l02 = loc.build_l0_l2(counts, universe, broad, n_hvg=int(n_hvg), retain_stratum_corr=True)
    sel = np.asarray(l02["selection"]["selected_positions"], dtype=np.int64)
    sub_det = (sparse.csr_matrix(counts)[:, universe] > 0).astype(float)
    H = np.asarray(sub_det[:, sel].todense())
    depth = np.asarray(sub_det.sum(1)).ravel()
    base = _build_base_strata(loc, broad, depth)
    regime = np.asarray(world.observed.regime_labels).astype(str)
    l3 = loc.localize_operator_source(H, base, regime, regime, retain_stratum_corr=True)
    # Synthetic observation regimes are deliberately crossed with biology, so donor
    # localization may lawfully pool across observation regime while preserving the
    # same class+depth support floor. This is a synthetic causal view, not a relabeling
    # of the real-data nested L4 object.
    donor_base = base
    l4 = loc.localize_donor(H, donor_base, np.asarray(world.latent.donor), retain_stratum_corr=True)
    l4["synthetic_donor_view"] = "BALANCED_CROSS_SOURCE_BY_DESIGN"

    return {
        "arm": world.name,
        "biology_kind": world.biology_kind,
        "observer_kind": world.observer_kind,
        "observation_family": world.observation_family,
        "legacy": legacy_result,
        "selection": l02["selection"],
        "localization": {
            "L0": l02["L0"],
            "L1": l02["L1"],
            "L2": l02["L2"],
            "L3": l3,
            "L4": l4,
        },
        "thresholds": {
            "canonical": CANONICAL_THRESHOLD,
            "sensitivity": list(SENSITIVITY_THRESHOLDS),
        },
    }


def _latent_distance(a: WorldArm, b: WorldArm) -> float:
    xa = np.asarray(a.latent.latent_abundance, dtype=float)
    xb = np.asarray(b.latent.latent_abundance, dtype=float)
    if xa.shape != xb.shape:
        raise ValueError("counterfactual latent shapes must match")
    denom = float(np.mean(np.abs(xa)) + np.mean(np.abs(xb)) + 1e-12)
    return float(np.mean(np.abs(xa - xb)) / denom)


def _observed_distance(a: WorldArm, b: WorldArm) -> float:
    xa = sparse.csr_matrix(a.observed.counts, dtype=float)
    xb = sparse.csr_matrix(b.observed.counts, dtype=float)
    if xa.shape != xb.shape:
        raise ValueError("counterfactual observed shapes must match")
    diff = xa - xb
    numerator = float(np.abs(diff.data).sum())
    denom = float(np.abs(xa.data).sum() + np.abs(xb.data).sum() + 1e-12)
    return numerator / denom


def _counterfactual_score(pair: tuple[WorldArm, WorldArm]) -> dict[str, float]:
    a, b = pair
    return {
        "latent_distance": _latent_distance(a, b),
        "observed_distance": _observed_distance(a, b),
    }


def score_factorial_tournament(worlds: FactorialWorlds, universe: np.ndarray, *,
                               legacy_score_fn: Callable | None = None,
                               localization_backend=None, n_hvg: int = 3000) -> dict[str, Any]:
    per_arm = {
        name: score_world(
            arm, universe, legacy_score_fn=legacy_score_fn,
            localization_backend=localization_backend, n_hvg=n_hvg,
        )
        for name, arm in worlds.arms.items()
    }
    return {
        "endpoint_version": worlds.manifest.endpoint_version,
        "per_arm": per_arm,
        "counterfactuals": {
            "C_OBS": _counterfactual_score(worlds.c_obs),
            "C_BIO": _counterfactual_score(worlds.c_bio),
        },
    }


def compare_factorial_mechanisms(evidence: Mapping[str, Mapping[str, Any]]) -> str:
    for arm in ("H1", "H2", "H3"):
        if arm not in evidence:
            raise ValueError("causal endpoint evidence requires H1/H2/H3")
    needed = {
        "H1": {"biology_endpoint_pass", "observer_endpoint_pass", "joint_adequate"},
        "H2": {"biology_endpoint_pass", "observer_endpoint_pass", "joint_adequate"},
        "H3": {"joint_adequate"},
    }
    for arm, keys in needed.items():
        if not keys.issubset(evidence[arm]):
            raise ValueError("causal endpoint evidence is required; aggregate distance alone is insufficient")

    h1 = evidence["H1"]
    h2 = evidence["H2"]
    h3 = evidence["H3"]
    if bool(h1["joint_adequate"]):
        return "BIOLOGY_ONLY_SUFFICIENT"
    if bool(h2["joint_adequate"]):
        return "OBSERVER_ONLY_SUFFICIENT"
    if bool(h1["biology_endpoint_pass"]) and bool(h2["observer_endpoint_pass"]):
        return "BOTH_AND_INTERACTION" if bool(h3["joint_adequate"]) else "COUPLING_FALSIFIED"
    if bool(h1["biology_endpoint_pass"]) and not bool(h2["observer_endpoint_pass"]):
        return "BIOLOGY_NECESSARY"
    if bool(h2["observer_endpoint_pass"]) and not bool(h1["biology_endpoint_pass"]):
        return "OBSERVER_NECESSARY"
    return "FAMILY_UNRESOLVED"
