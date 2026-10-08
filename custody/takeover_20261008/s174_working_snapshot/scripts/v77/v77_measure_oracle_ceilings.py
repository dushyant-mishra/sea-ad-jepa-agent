#!/usr/bin/env python3
"""Measure the oracle recoverability ceiling of every planted component in a V77 world.

This runs BEFORE any JEPA sees the world, as the Phase 4 governing rule requires: a component
whose MEASURED class contradicts its DESIGNED class is a construction failure, to be repaired
or withdrawn, never reinterpreted.

All readouts are linear probes on CPM-log1p counts with a held-out split. A linear probe is
an honest reference, not a claim that the best possible reader is linear; where a component is
designed to be invisible to a linear global readout (C1, C2) the probe reports BOTH the plain
linear number and the structured contrast that is supposed to expose it.
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))


def load_world(root: Path):
    T = root / "hidden_truth"
    O = root / "observable_raw" / "FULL104_like_sharded"
    acc = {}
    for f in sorted(T.glob("TRUTH_*.npz")):
        z = np.load(f, allow_pickle=False)
        for k in z.files:
            if k != "cell_id":
                acc.setdefault(k, []).append(z[k])
    truth = {k: np.concatenate(v, 0) for k, v in acc.items()}
    cnt, avail = [], []
    for f in sorted(O.glob("RNA_*.npz")):
        z = np.load(f, allow_pickle=False)
        cnt.append(z["counts"].T); avail.append(z["availability"].T)
    cnt = np.concatenate(cnt, 0).astype(np.float64)
    avail = np.concatenate(avail, 0).astype(np.float64)
    tm = json.loads((T / "TRUTH_MANIFEST.json").read_text())
    return truth, cnt, avail, tm


def cpm_log(X):
    s = X.sum(1, keepdims=True); s = np.where(s > 0, s, 1.0)
    return np.log1p(X / s * 1e4)


class Probe:
    def __init__(self, X, n, seed=20261005):
        rng = np.random.default_rng(seed)
        p = rng.permutation(n)
        self.tr, self.te = p[: n // 2], p[n // 2:]
        self.X1 = np.c_[np.ones(len(X)), X]

    def fit_predict(self, y, X1=None):
        X1 = self.X1 if X1 is None else X1
        B, *_ = np.linalg.lstsq(X1[self.tr], y[self.tr], rcond=None)
        return X1[self.te] @ B

    def r2(self, y, X1=None):
        p = self.fit_predict(y, X1)
        yt = y[self.te]
        ss = ((yt - p) ** 2).sum(); tt = ((yt - yt.mean()) ** 2).sum()
        return float(1 - ss / tt) if tt > 0 else float("nan")

    def ap(self, y, X1=None):
        """average precision of a held-out linear score against a binary label."""
        p = self.fit_predict(y.astype(np.float64), X1)
        yt = y[self.te].astype(bool)
        if yt.sum() == 0:
            return float("nan"), 0.0, 0
        o = np.argsort(-p)
        hits = yt[o].cumsum()
        prec = hits / np.arange(1, len(o) + 1)
        return float(prec[yt[o]].mean()), float(yt.mean()), int(yt.sum())


def main():
    ap_ = argparse.ArgumentParser()
    ap_.add_argument("--root", required=True)
    ap_.add_argument("--out", required=True)
    a = ap_.parse_args()
    root = Path(a.root)
    truth, cnt, avail, tm = load_world(root)
    om = root / "observable_raw" / "FULL104_like_sharded" / "FULL104_SHARDED_MANIFEST.json"
    obs_manifest = json.loads(om.read_text()) if om.exists() else {}
    n = len(truth["global_cell_index"])
    enabled = set(tm["enabled_components"])
    X = cpm_log(cnt)
    P = Probe(X, n)
    R = {"n_cells": n, "enabled_components": sorted(enabled), "components": {}}

    def put(cid, designed, measured, verdict, detail=None):
        R["components"][cid] = dict(designed_class=designed, measured=measured,
                                    verdict=verdict, detail=detail)

    # ---- World A base, for continuity with the locked ceilings
    base = {}
    for blk in ["z_global", "z_query", "z_reg_shared", "z_reg_private"]:
        base[blk] = float(np.mean([P.r2(truth[blk][:, j]) for j in range(truth[blk].shape[1])]))
    R["world_A_base_ceilings_in_this_world"] = base

    if "B1" in enabled:
        st = truth["state_index"].astype(np.int64)
        accs = []
        for k in range(int(st.max()) + 1):
            accs.append(P.r2((st == k).astype(np.float64)))
        m = float(np.mean(accs))
        put("B1", "RECOVERABLE 0.55-0.75", {"mean_one_vs_rest_R2": m},
            "PASS" if m >= 0.35 else "BELOW_DESIGN")
    if "B2" in enabled:
        v = [P.r2(truth["z_donor"][:, j]) for j in range(truth["z_donor"].shape[1])]
        m = float(np.mean(v))
        put("B2", "RECOVERABLE_AT_DONOR_LEVEL 0.40-0.65 at cell level",
            {"per_dim_R2": v, "mean_R2": m}, "PASS" if m >= 0.25 else "BELOW_DESIGN")
    if "B3" in enabled:
        from build_v77_extended_truth import RARE_PREVALENCE, RARE_RECOVERABLE
        arms = []
        for j in range(truth["rare_flags"].shape[1]):
            apv, baserate, npos = P.ap(truth["rare_flags"][:, j])
            lift = (apv / baserate) if (baserate > 0 and apv == apv) else float("nan")
            arms.append(dict(arm=j, designed_prevalence=RARE_PREVALENCE[j],
                             designed_recoverable=bool(RARE_RECOVERABLE[j]),
                             n_positive_heldout=npos, base_rate=baserate,
                             average_precision=apv, lift_over_base_rate=lift))
        ok = all((x["lift_over_base_rate"] > 3) == x["designed_recoverable"]
                 for x in arms if x["n_positive_heldout"] >= 5)
        put("B3", "MIXED: arms 0,1 RECOVERABLE; arms 2,3 NON_RECOVERABLE",
            {"arms": arms}, "PASS" if ok else "CHECK",
            "arms with fewer than 5 held-out positives are underpowered and excluded from the verdict")
    if "B4" in enabled:
        band = np.exp(-((truth["pseudotime"].astype(np.float64) - 0.5) / 0.15) ** 2)
        put("B4", "PARTIALLY_RECOVERABLE 0.25-0.45",
            {"pseudotime_R2": P.r2(truth["pseudotime"].astype(np.float64)),
             "transient_band_R2": P.r2(band)}, "REPORTED")
    if "B5" in enabled:
        v = [P.r2(truth["z_marker"][:, j]) for j in range(truth["z_marker"].shape[1])]
        put("B5", "RECOVERABLE_BUT_LOW_WEIGHT 0.30-0.60",
            {"per_dim_R2": v, "mean_R2": float(np.mean(v))},
            "PASS" if np.mean(v) >= 0.20 else "BELOW_DESIGN")
    if "B6" in enabled:
        fr = tm.get("b6_high_pool_fraction") or np.linspace(0, 1, truth["z_partial"].shape[1]).tolist()
        rung = [P.r2(truth["z_partial"][:, j]) for j in range(truth["z_partial"].shape[1])]
        monotone = all(rung[i] <= rung[i + 1] + 0.03 for i in range(len(rung) - 1))
        spread = float(max(rung) - min(rung))
        put("B6", "GRADED_PARTIAL ladder approx 0.05/0.15/0.30/0.45/0.60",
            {"high_pool_fraction": fr, "rung_R2": rung, "spread": spread,
             "monotone_increasing": bool(monotone)},
            "PASS" if (monotone and spread > 0.15) else "CHECK",
            "this is the component World A entirely lacks: a continuum between recoverable and not")
    if "C1" in enabled:
        A = truth["c_state_a"].astype(np.float64); B = truth["c_state_b"].astype(np.float64)
        AB = (A * B)
        full = P.r2(AB)
        pA = P.fit_predict(A); pB = P.fit_predict(B)
        Xadd = np.c_[np.ones(len(P.te)), pA, pB]
        Badd, *_ = np.linalg.lstsq(Xadd, AB[P.te], rcond=None)
        pred = Xadd @ Badd
        ss = ((AB[P.te] - pred) ** 2).sum(); tt = ((AB[P.te] - AB[P.te].mean()) ** 2).sum()
        additive_only = float(1 - ss / tt)
        put("C1", "RECOVERABLE_ONLY_BY_A_NONLINEAR_READER",
            {"interaction_R2_from_full_RNA": full,
             "interaction_R2_from_additive_state_summary_only": additive_only,
             "gap_attributable_to_the_interaction_module": full - additive_only},
            "PASS" if (full - additive_only) > 0.05 else "CHECK",
            "the gap is the signal an additive state representation cannot supply")
    if "C2" in enabled:
        g = truth["z_gain"].astype(np.float64)
        plain = P.r2(g)
        # ORACLE readout: an oracle ceiling is allowed to use ground truth, and here it must.
        # The effect is a multiplicative gain on ONE module's loading, so it is only visible in
        # the ratio of that module's score to the drive it modulates. Conditioning on the known
        # module is what makes this an oracle rather than fitting the test to the simulator.
        mg = (obs_manifest or {}).get("c2_local_module_genes")
        if mg:
            ms = X[:, np.asarray(mg, dtype=np.int64)].mean(1)
            drive = truth["z_global"][:, 0].astype(np.float64)
            dsafe = np.where(np.abs(drive) < 0.25, np.sign(drive + 1e-9) * 0.25, drive)
            feats = np.c_[ms, drive, ms * drive, ms / dsafe]
            cond = P.r2(g, np.c_[np.ones(len(feats)), feats])
        else:
            cond = float("nan")
        put("C2", "RECOVERABLE_ONLY_BY_CONDITIONING_ON_THE_MODULE",
            {"global_linear_readout_R2": plain, "module_conditional_readout_R2": cond,
             "gap": cond - plain},
            "PASS" if (cond - plain) > 0.05 else "CHECK",
            "a genuinely local effect must be weak globally and strong when conditioned on its module")
    if "C3" in enabled:
        depth = cnt.sum(1).astype(np.float64); na = avail.sum(1).astype(np.float64)
        q = truth["z_bioqc"].astype(np.float64)
        cs = [float(abs(np.corrcoef(q, depth)[0, 1])), float(abs(np.corrcoef(q, na)[0, 1]))]
        put("C3", "CONFOUNDED_BY_DESIGN",
            {"abs_corr_z_bioqc_vs_total_counts": cs[0],
             "abs_corr_z_bioqc_vs_n_available": cs[1],
             "world_A_reference_max_abs_corr": 0.008637},
            "PASS" if max(cs) > 0.05 else "CHECK",
            "World A measures <=0.009; a materially larger value means the operator now depends on biology")
    if "D1" in enabled:
        v = [P.r2(truth["z_tf"][:, j]) for j in range(truth["z_tf"].shape[1])]
        put("D1", "RECOVERABLE_AS_A_GRAPH",
            {"per_tf_activity_R2": v, "mean_R2": float(np.mean(v))},
            "PASS" if np.mean(v) >= 0.15 else "BELOW_DESIGN",
            "graph precision/recall is evaluated in the multiome lane; this is TF activity readout only")
    if "E1" in enabled:
        put("E1", "RECOVERABLE_SPATIAL_FIELD",
            {"niche_score_R2": P.r2(truth["niche_score"].astype(np.float64)),
             "compartment_mean_one_vs_rest_R2": float(np.mean(
                 [P.r2((truth["compartment"] == k).astype(np.float64))
                  for k in range(int(truth["compartment"].max()) + 1)]))},
            "REPORTED")
    if "E2" in enabled:
        from build_v77_extended_truth import PERTURBATIONS
        arms = []
        for arm in PERTURBATIONS:
            i = arm["pert_id"]
            if i == 0:
                continue
            y = (truth["pert_id"] == i).astype(np.float64)
            apv, br, npos = P.ap(y)
            arms.append(dict(pert_id=i, name=arm["name"], kind=arm["kind"],
                             average_precision=apv, base_rate=br, n_positive_heldout=npos,
                             lift=(apv / br if br > 0 else float("nan"))))
        null_arm = [x for x in arms if x["kind"] == "null"][0]
        real = [x for x in arms if x["kind"] != "null"]
        ok = null_arm["lift"] < 1.5 and all(x["lift"] > 1.5 for x in real)
        put("E2", "REAL_ARMS_DETECTABLE, NULL_ARM_MUST_NOT_BE",
            {"arms": arms, "null_arm_lift": null_arm["lift"]},
            "PASS" if ok else "CHECK",
            "the null arm is the false-positive control: it is assigned and dosed but has no effect")

    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(R, indent=2) + "\n")
    print(json.dumps({k: dict(verdict=v["verdict"], designed=v["designed_class"])
                      for k, v in R["components"].items()}, indent=2))
    print("\nworld A base ceilings in this world:", json.dumps(base, indent=2))


if __name__ == "__main__":
    main()
