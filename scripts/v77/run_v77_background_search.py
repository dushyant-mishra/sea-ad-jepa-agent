#!/usr/bin/env python3
"""Measure every background candidate against the frozen envelopes, at smoke scale.

Reports LATENT geometry (eta itself) and OBSERVED geometry (after the observation model)
separately, because the observation process is already known to destroy roughly half the
covariance and a candidate must not compensate by making latent biology absurdly correlated.

Every candidate is recorded including failures. Nothing here changes a frozen target.
"""
from __future__ import annotations
import argparse, json, sys, time
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import v77_background_candidates as CAND
import build_v77_calibration_envelope as ENV
import build_v77_topology_calibration as TC
import v77_address_universe as AU

ABUNDANCE = AU.AddressUniverse(seed=7302).log_abundance.astype('float32')

TARGETS = ["median_abs_corr", "frac_abs_gt_0p3", "var_top10_pc", "mean_degree",
           "largest_community_frac", "transitivity", "substitute_frac",
           "frac_pos_gt_0p3", "frac_neg_lt_m0p3", "pos_over_neg_ratio", "mean_signed_corr"]


def geometry(M, n_hvg, cls=None):
    """Dependence geometry of a cell-by-feature matrix, plus T5 if classes are given."""
    v = M.var(0)
    sel = np.argsort(-v)[:n_hvg]
    stats = ENV.stats_from_logmatrix(M, sel, n_hvg)
    if cls is not None:
        H = M[:, sel]; H = (H - H.mean(0)) / (H.std(0) + 1e-9)
        C = (H.T @ H) / len(H)
        pooled = float(np.quantile(np.abs(C[~np.eye(len(C), dtype=bool)]), .5))
        wc = []
        for c in np.unique(cls):
            m = cls == c
            if m.sum() < 150:
                continue
            Hc = M[m][:, sel]; Hc = (Hc - Hc.mean(0)) / (Hc.std(0) + 1e-9)
            Cc = (Hc.T @ Hc) / m.sum()
            wc.append(float(np.quantile(np.abs(Cc[~np.eye(len(Cc), dtype=bool)]), .5)))
        stats["t5_within_over_pooled"] = float(np.mean(wc) / pooled) if (wc and pooled > 0) else float("nan")
    return stats


def cpm_log(counts):
    lib = counts.sum(1, keepdims=True)
    lib = np.where(lib > 0, lib, 1.0)
    return np.log1p(counts / lib * 1e4)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--envelope", default="results/v77/V77_REAL_CALIBRATION_ENVELOPE_V1.json")
    ap.add_argument("--out", required=True)
    ap.add_argument("--cells", type=int, default=4000)
    ap.add_argument("--addresses", type=int, default=41238)
    ap.add_argument("--n-hvg", type=int, default=3000)
    ap.add_argument("--seed", type=int, default=20261006)
    ap.add_argument("--only", default=None, help="comma-separated candidate ids")
    a = ap.parse_args()

    env = json.loads(Path(a.envelope).read_text())
    E = env["ACCEPTANCE_ENVELOPES"]
    t5_env = 1.012   # from the topology calibration; guard, not a tuned target

    ids = list(CAND.CANDIDATES) if not a.only else [c.strip() for c in a.only.split(",")]
    results = {}
    for cid in ids:
        cfg = CAND.CANDIDATES[cid]
        t0 = time.time()
        eta, cls, nfac = CAND.build_eta(cfg, a.cells, a.addresses, a.seed)
        lat = geometry(eta, a.n_hvg, cls)
        # The abundance prior is LOAD-BEARING and must be present, exactly as in the real
        # observer. Without it every address is equivalent, detection is near-binary and
        # censoring at zero destroys the negative correlation tail entirely. An earlier
        # version of this harness omitted it and therefore measured a different object.
        counts = CAND.observe_counts(eta + ABUNDANCE[None, :], a.seed)
        obs = geometry(cpm_log(counts), a.n_hvg, cls)
        inside = {k: bool(E[k]["accept_low"] <= obs[k] <= E[k]["accept_high"]) for k in TARGETS}
        n_in = sum(inside.values())
        results[cid] = dict(
            note=cfg["note"], n_factors=int(nfac), seconds=round(time.time() - t0, 1),
            latent=lat, observed=obs, inside_envelope=inside,
            n_targets_inside=n_in, n_targets=len(TARGETS),
            t5_observed=obs.get("t5_within_over_pooled"),
            verdict=("ACCEPT" if n_in == len(TARGETS) else "REJECT"))
        print("%-30s factors=%5d  inside %2d/%2d  %s" % (cid, nfac, n_in, len(TARGETS),
                                                         results[cid]["verdict"]))

    rec = dict(schema="V77_BACKGROUND_CANDIDATE_SEARCH_V1",
               envelope_source=dict(path=a.envelope, schema=env["schema"]),
               smoke_scale=dict(cells=a.cells, addresses=a.addresses, n_hvg=a.n_hvg, seed=a.seed),
               t5_real_reference=t5_env,
               acceptance_rule=("a candidate must land inside the donor-resampled 5th-to-95th "
                                "percentile envelope on EVERY target individually; improvement "
                                "alone is not acceptance"),
               candidates=results,
               failed_candidates_preserved=True)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(rec, indent=2) + "\n")

    print("\n%-26s %10s" % ("target", "real") + "".join("%14s" % c[:13] for c in ids))
    for k in TARGETS:
        row = "%-26s %10.4f" % (k, E[k]["point"])
        for c in ids:
            v = results[c]["observed"][k]
            row += "%13.4f%s" % (v, "*" if results[c]["inside_envelope"][k] else " ")
        print(row)
    print("%-26s %10.4f" % ("t5_within_over_pooled", t5_env)
          + "".join("%13.4f " % results[c]["observed"].get("t5_within_over_pooled", float("nan")) for c in ids))
    print("\n* = inside the donor-resampled envelope")


if __name__ == "__main__":
    main()
