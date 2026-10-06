#!/usr/bin/env python3
"""V77 oracle v4: signed-projection successor, repairing defect S127.

GOVERNANCE-VISIBLE SUCCESSOR, not an in-place reinterpretation. v3 remains on disk and its
numbers remain readable; this file produces a separate, labelled measurement so the change of
instrument is auditable.

THE DEFECT (S127). v3 scores a planted module as an UNWEIGHTED CPM-log1p mean over its
addresses. Every planted module has mixed-sign loadings, built as sign(normal) * scale, so its
unweighted mean is a SYMMETRIC function of its driver and destroys the signal by construction.
Demonstrated on ATAC by binning accessibility by driver decile: module regions accessible
0.478 at the lowest decile, 0.174 in the middle, 0.515 at the highest, against a genome
baseline near 0.18. The effect arrived at full strength; the statistic averaged it away.

THE REPAIR. Project onto the planted loading sign vector instead of averaging:

    signed_score = (X_cpm_log1p[:, module] @ sign_vector) / len(module)

Using the sign vector is legitimate for an ORACLE: the oracle is already given module
MEMBERSHIP from truth, and the loading SIGN is the same class of information. The universal
label is unchanged and now explicitly includes sign knowledge.

ACCEPTANCE, as required by the review lane: the repair is acceptable ONLY if the intended
positive signal is restored AND the negative controls still reject. A statistic that lights up
on an off-twin is measuring something other than the planted component.

NO PASS THRESHOLD IS CHANGED BY THIS FILE. Every designed recoverability class and every
acceptance band is carried over from the frozen statistic document unmodified.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import numpy as np
from scipy import sparse

HERE = Path(__file__).resolve().parent
CEILING_LABEL = ("ORACLE_CEILING_UNDER_KNOWN_SUPPORT_AND_KNOWN_SIGN__UPPER_BOUND_"
                 "NOT_BLIND_ACHIEVABLE")
INSTRUMENT = "SIGNED_PROJECTION_ONTO_PLANTED_LOADING__S127_REPAIR"


def _load(name, fn):
    spec = importlib.util.spec_from_file_location(name, HERE / fn)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def signed_world(root: Path):
    """Load a world and build BOTH the v3 unweighted and the v4 signed design matrices."""
    import sys
    sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[0] / "v64"))
    ld = _load("v77_oracle_v2", "v77_measure_oracle_ceilings_v2.py")
    import build_v77_fullscale_rna_observer_v2 as OBS

    W = ld.load_v2_world(Path(root))
    man = W.observer_manifest
    seed = int(man["seed"])
    N = int(man["n_addresses"])
    sets = man["module_address_sets"]
    names = W.module_names

    # rebuild the CPM-log1p matrix once; the 41,238-address matrix is never densified
    odir = Path(root) / "observable_raw" / "FULLSCALE_V2_CANONICAL_sharded"
    Xs = []
    for s in man["shards"]:
        z = np.load(odir / s["file"], allow_pickle=False)
        X = sparse.csr_matrix((z["data"].astype(np.float64), z["indices"], z["indptr"]),
                              shape=(len(z["indptr"]) - 1, N))
        lib = np.asarray(X.sum(1)).ravel()
        X.data = np.log1p(X.data / np.repeat(np.maximum(lib, 1), np.diff(X.indptr)) * 1e4)
        Xs.append(X)
    X = sparse.vstack(Xs).tocsr()

    rows, cols, vals, signed_ok = [], [], [], []
    for j, nm in enumerate(names):
        g = np.asarray(sets[nm], dtype=np.int64)
        sv = OBS.module_sign_vector(seed, nm, g)
        if sv is None:
            sv = np.ones(len(g), dtype=np.float64)   # no own loading: fall back to the mean
            signed_ok.append(False)
        else:
            signed_ok.append(True)
        rows.extend(g.tolist()); cols.extend([j] * len(g))
        vals.extend((sv / len(g)).tolist())
    M = sparse.csr_matrix((vals, (rows, cols)), shape=(N, len(names)))
    W.signed_scores = (X @ M).toarray()
    W.signed_available = np.asarray(signed_ok)
    return W


def measure(root: Path) -> dict:
    v3 = _load("v77_oracle_v3", "v77_component_oracle_v3.py")
    W = signed_world(root)
    S_signed = W.signed_scores
    S_unw = W.module_scores
    names = W.module_names
    enabled = set(W.observer_manifest["enabled_components"])
    t = W.truth

    def block(S):
        out = {"default_reader": {}, "component_specific": {}}
        sp = v3.Split(W.n_cells)
        if "state_index" in t:
            st = t["state_index"].astype(np.int64)
            out["default_reader"]["B1"] = dict(mean_one_vs_rest_r2=float(np.mean(
                [sp.r2(S, (st == k).astype(np.float64)) for k in range(int(st.max()) + 1)])))
        if "z_donor" in t:
            v = [sp.r2(S, t["z_donor"][:, j].astype(np.float64)) for j in range(t["z_donor"].shape[1])]
            out["default_reader"]["B2"] = dict(mean_r2=float(np.mean(v)), per_dim_r2=v)
        if "rare_flags" in t:
            arms = []
            for j in range(t["rare_flags"].shape[1]):
                ap, base, npos = sp.average_precision(S, t["rare_flags"][:, j])
                arms.append(dict(arm=j, average_precision=ap, base_rate=base,
                                 n_positive_heldout=npos,
                                 lift=(ap / base if base > 0 else float("nan"))))
            out["default_reader"]["B3"] = dict(arms=arms)
        if "z_marker" in t:
            v = [sp.r2(S, t["z_marker"][:, j].astype(np.float64)) for j in range(t["z_marker"].shape[1])]
            out["default_reader"]["B5"] = dict(mean_r2=float(np.mean(v)), per_dim_r2=v)
        if "z_partial" in t:
            rung = [sp.r2(S, t["z_partial"][:, j].astype(np.float64))
                    for j in range(t["z_partial"].shape[1])]
            out["default_reader"]["B6"] = dict(
                rung_r2=rung, spread=float(max(rung) - min(rung)),
                monotone=bool(all(rung[i] <= rung[i + 1] + 0.03 for i in range(len(rung) - 1))))
        if "z_tf" in t:
            v = [sp.r2(S, t["z_tf"][:, j].astype(np.float64)) for j in range(t["z_tf"].shape[1])]
            out["default_reader"]["D1_tf_activity"] = dict(mean_r2=float(np.mean(v)), per_tf_r2=v)
        if "niche_score" in t:
            out["default_reader"]["E1"] = dict(niche_r2=sp.r2(S, t["niche_score"].astype(np.float64)))
        if "pert_id" in t:
            arms = []
            for i in (1, 2, 3, 4):
                ap, base, npos = sp.average_precision(S, (t["pert_id"] == i))
                arms.append(dict(pert_id=i, average_precision=ap, base_rate=base,
                                 n_positive_heldout=npos,
                                 lift=(ap / base if base > 0 else float("nan"))))
            out["default_reader"]["E2"] = dict(arms=arms, null_arm_lift=arms[-1]["lift"])
        # frozen component-specific statistics, thresholds untouched
        if "pseudotime" in t:
            out["component_specific"]["B4"] = v3.stat_B4_transient(W, S)
        if "c_state_a" in t:
            out["component_specific"]["C1"] = v3.stat_C1_interaction(W, S)
        if "z_gain" in t:
            out["component_specific"]["C2"] = v3.stat_C2_local_gain(W, S, names)
        if "z_bioqc" in t:
            out["component_specific"]["C3"] = v3.stat_C3_biology_x_operator(W)
        return out

    return dict(
        root=str(root), n_cells=W.n_cells, n_addresses=W.n_addresses,
        n_modules=len(names),
        modules_with_own_sign_vector=int(W.signed_available.sum()),
        modules_without=int((~W.signed_available).sum()),
        enabled_components=sorted(enabled),
        INSTRUMENT=INSTRUMENT, CEILING_LABEL=CEILING_LABEL,
        thresholds_changed=False,
        superseded_instrument="UNWEIGHTED_MODULE_MEAN__v77_component_oracle_v3",
        v4_signed=block(S_signed),
        v3_unweighted_for_comparison=block(S_unw))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    r = measure(Path(a.root))
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(r, indent=2) + "\n")
    cs = r["v4_signed"]["component_specific"]
    old = r["v3_unweighted_for_comparison"]["component_specific"]
    print(json.dumps({k: dict(v4_passes=cs[k].get("passes"), v3_passes=old[k].get("passes"))
                      for k in cs}, indent=2))


if __name__ == "__main__":
    main()
