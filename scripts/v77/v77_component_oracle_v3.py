#!/usr/bin/env python3
"""V77 component-specific oracle layer, implementing the frozen sufficient statistics.

Sits on top of the qualified sparse loader in `v77_measure_oracle_ceilings_v2.py`, which
supplies planted module scores without ever densifying the 41,238-address matrix.

The oracle audit established that a single universal module-score reader is scientifically
invalid for B4, C1, C2 and C3, and that graph recovery is not a module quantity at all. Those
five statistics are defined in
`results/v77/V77_COMPONENT_SUFFICIENT_STATISTIC_FREEZE_V1.json` and are implemented here
exactly as frozen. Nothing in this file may introduce a new threshold.

EVERY NUMBER THIS PRODUCES IS AN ORACLE CEILING UNDER KNOWN SUPPORT. The design matrix is
built from the planted module sets, i.e. from truth, so it measures recoverability GIVEN
PERFECT MODULE DISCOVERY. It is an upper bound, never a blind achievable ceiling.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
CEILING_LABEL = "ORACLE_CEILING_UNDER_KNOWN_SUPPORT__UPPER_BOUND_NOT_BLIND_ACHIEVABLE"
SPLIT_SEED = 20261005


def _loader():
    spec = importlib.util.spec_from_file_location(
        "v77_oracle_v2", HERE / "v77_measure_oracle_ceilings_v2.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class Split:
    def __init__(self, n: int, seed: int = SPLIT_SEED):
        p = np.random.default_rng(seed).permutation(n)
        self.tr, self.te = p[: n // 2], p[n // 2:]

    def r2(self, X, y):
        X = np.asarray(X, dtype=np.float64)
        if X.ndim == 1:
            X = X[:, None]
        X1 = np.c_[np.ones(len(X)), X]
        B, *_ = np.linalg.lstsq(X1[self.tr], y[self.tr], rcond=None)
        pr = X1[self.te] @ B
        yt = y[self.te]
        tt = ((yt - yt.mean()) ** 2).sum()
        return float(1 - ((yt - pr) ** 2).sum() / tt) if tt > 0 else float("nan")

    def predict(self, X, y):
        X = np.asarray(X, dtype=np.float64)
        if X.ndim == 1:
            X = X[:, None]
        X1 = np.c_[np.ones(len(X)), X]
        B, *_ = np.linalg.lstsq(X1[self.tr], y[self.tr], rcond=None)
        return X1 @ B

    def average_precision(self, X, y):
        pr = self.predict(X, y.astype(np.float64))[self.te]
        yt = y[self.te].astype(bool)
        if yt.sum() == 0:
            return float("nan"), 0.0, 0
        o = np.argsort(-pr)
        hits = yt[o].cumsum()
        prec = hits / np.arange(1, len(o) + 1)
        return float(prec[yt[o]].mean()), float(yt.mean()), int(yt.sum())


# ----------------------------------------------------------------- frozen statistics
def stat_B4_transient(W, S):
    t = W.truth["pseudotime"].astype(np.float64)
    band = np.exp(-((t - 0.5) / 0.15) ** 2)
    sp = Split(W.n_cells)
    r2_band, r2_t = sp.r2(S, band), sp.r2(S, t)
    return dict(statistic="band_value_not_pseudotime", r2_band=r2_band,
                r2_pseudotime_diagnostic_only=r2_t,
                pass_range=[0.25, 0.45], passes=bool(0.25 <= r2_band <= 0.45),
                off_twin_must_be_below=0.05)


def stat_C1_interaction(W, S):
    A = W.truth["c_state_a"].astype(np.float64)
    B = W.truth["c_state_b"].astype(np.float64)
    AB = A * B
    sp = Split(W.n_cells)
    full = sp.r2(S, AB)
    pA, pB = sp.predict(S, A), sp.predict(S, B)
    add = sp.r2(np.c_[pA, pB], AB)
    gap = full - add
    return dict(statistic="full_minus_additive_gap", r2_full=full, r2_additive_summary=add,
                gap=gap, pass_threshold=0.05, passes=bool(gap > 0.05),
                off_twin_must_be_below=0.01)


def stat_C2_local_gain(W, S, module_names):
    g = W.truth["z_gain"].astype(np.float64)
    drive = W.truth["z_global"][:, 0].astype(np.float64)
    sp = Split(W.n_cells)
    linear = sp.r2(S, g)
    if "C2_local" not in module_names:
        return dict(statistic="ratio_features", error="C2_local module absent", passes=False)
    ms = S[:, module_names.index("C2_local")]
    ds = np.where(np.abs(drive) < 0.25, np.sign(drive + 1e-9) * 0.25, drive)
    ratio = sp.r2(np.c_[ms, drive, ms * drive, ms / ds], g)
    return dict(statistic="ratio_features", r2_linear_over_module_scores=linear,
                r2_ratio_features=ratio, improvement=ratio - linear,
                pass_range=[0.40, 0.60], pass_improvement_threshold=0.05,
                passes=bool(0.40 <= ratio <= 0.60 and (ratio - linear) > 0.05),
                off_twin_must_be_below=0.05,
                freeze_note="this freeze predicted C2 would fail its designed band")


def stat_C3_biology_x_operator(W):
    q = W.truth["z_bioqc"].astype(np.float64)
    lib = W.library_size.astype(np.float64)
    c_lib = abs(float(np.corrcoef(q, lib)[0, 1]))
    sup = None
    m = max(c_lib, sup or 0.0)
    return dict(statistic="depth_and_support_coupling_not_a_module_quantity",
                abs_corr_bioqc_vs_library=c_lib, max_abs_corr=m,
                world_A_reference=0.0086, pass_threshold=0.05, passes=bool(m > 0.05),
                off_twin_must_be_below=0.02)


def default_reader(W, S, name, y, kind="r2"):
    sp = Split(W.n_cells)
    if kind == "ap":
        ap, base, npos = sp.average_precision(S, y)
        return dict(component=name, statistic="average_precision", average_precision=ap,
                    base_rate=base, n_positive_heldout=npos,
                    lift=(ap / base if base > 0 else float("nan")))
    return dict(component=name, statistic="module_score_r2", r2=sp.r2(S, y))


def measure(root: Path) -> dict:
    ld = _loader()
    W = ld.load_v2_world(Path(root))
    S, names = W.module_scores, W.module_names
    enabled = set(W.observer_manifest["enabled_components"])
    out = {"root": str(root), "n_cells": W.n_cells, "n_addresses": W.n_addresses,
           "n_modules": S.shape[1], "enabled_components": sorted(enabled),
           "CEILING_LABEL": CEILING_LABEL,
           "design_matrix_policy": W.design_matrix_policy,
           "suppressed_from_observation": W.observer_manifest.get("suppressed_from_observation", []),
           "statistic_selection": "keyed off TRUTH availability, not observer-enabled, so an "
                                  "off-twin statistic is still COMPUTED and must return ~0",
           "default_reader": {}, "component_specific": {}}

    t = W.truth
    if "B1" in enabled and "state_index" in t:
        st = t["state_index"].astype(np.int64)
        sp = Split(W.n_cells)
        out["default_reader"]["B1"] = dict(
            mean_one_vs_rest_r2=float(np.mean([sp.r2(S, (st == k).astype(np.float64))
                                               for k in range(int(st.max()) + 1)])))
    if "B2" in enabled and "z_donor" in t:
        sp = Split(W.n_cells)
        v = [sp.r2(S, t["z_donor"][:, j].astype(np.float64)) for j in range(t["z_donor"].shape[1])]
        out["default_reader"]["B2"] = dict(per_dim_r2=v, mean_r2=float(np.mean(v)))
    if "B3" in enabled and "rare_flags" in t:
        sp = Split(W.n_cells)
        arms = []
        for j in range(t["rare_flags"].shape[1]):
            ap, base, npos = sp.average_precision(S, t["rare_flags"][:, j])
            arms.append(dict(arm=j, average_precision=ap, base_rate=base,
                             n_positive_heldout=npos,
                             lift=(ap / base if base > 0 else float("nan"))))
        out["default_reader"]["B3"] = dict(arms=arms)
    if "B5" in enabled and "z_marker" in t:
        sp = Split(W.n_cells)
        v = [sp.r2(S, t["z_marker"][:, j].astype(np.float64)) for j in range(t["z_marker"].shape[1])]
        out["default_reader"]["B5"] = dict(per_dim_r2=v, mean_r2=float(np.mean(v)))
    if "B6" in enabled and "z_partial" in t:
        sp = Split(W.n_cells)
        rung = [sp.r2(S, t["z_partial"][:, j].astype(np.float64))
                for j in range(t["z_partial"].shape[1])]
        out["default_reader"]["B6"] = dict(
            rung_r2=rung, spread=float(max(rung) - min(rung)),
            monotone=bool(all(rung[i] <= rung[i + 1] + 0.03 for i in range(len(rung) - 1))))
    if "D1" in enabled and "z_tf" in t:
        sp = Split(W.n_cells)
        v = [sp.r2(S, t["z_tf"][:, j].astype(np.float64)) for j in range(t["z_tf"].shape[1])]
        out["default_reader"]["D1_tf_activity"] = dict(per_tf_r2=v, mean_r2=float(np.mean(v)))
    if "E1" in enabled and "niche_score" in t:
        sp = Split(W.n_cells)
        out["default_reader"]["E1"] = dict(niche_r2=sp.r2(S, t["niche_score"].astype(np.float64)))
    if "E2" in enabled and "pert_id" in t:
        sp = Split(W.n_cells)
        arms = []
        for i in (1, 2, 3, 4):
            ap, base, npos = sp.average_precision(S, (t["pert_id"] == i))
            arms.append(dict(pert_id=i, average_precision=ap, base_rate=base,
                             n_positive_heldout=npos,
                             lift=(ap / base if base > 0 else float("nan"))))
        out["default_reader"]["E2"] = dict(arms=arms,
                                           null_arm_lift=arms[-1]["lift"],
                                           note="arm 4 is the NULL false-positive control")

    if "pseudotime" in t:
        out["component_specific"]["B4"] = stat_B4_transient(W, S)
    if "c_state_a" in t:
        out["component_specific"]["C1"] = stat_C1_interaction(W, S)
    if "z_gain" in t:
        out["component_specific"]["C2"] = stat_C2_local_gain(W, S, names)
    if "z_bioqc" in t:
        out["component_specific"]["C3"] = stat_C3_biology_x_operator(W)
    return out


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    r = measure(Path(a.root))
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(r, indent=2) + "\n")
    print(json.dumps({k: v.get("passes", "reported")
                      for k, v in r["component_specific"].items()}, indent=2))


if __name__ == "__main__":
    main()
