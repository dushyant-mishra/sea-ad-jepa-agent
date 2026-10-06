#!/usr/bin/env python3
"""Evaluate discrete sub-state candidates jointly against every frozen target.

No metric is optimised at the expense of the others: a candidate is judged on all of them at
once, and the family-level decision rests on whether ONE mechanism produces the major features
together.
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import v77_substate_generator as SS
import v77_background_candidates as CAND
import build_v77_calibration_envelope as ENV
import v77_address_universe as AU

ABUNDANCE = AU.AddressUniverse(seed=7302)
AB = ABUNDANCE.log_abundance.astype(np.float32)

TARGETS = ["median_abs_corr", "frac_abs_gt_0p3", "var_top10_pc", "mean_degree",
           "largest_community_frac", "transitivity", "substitute_frac",
           "frac_pos_gt_0p3", "frac_neg_lt_m0p3", "pos_over_neg_ratio", "mean_signed_corr"]


def geom(M, n_hvg=3000):
    return ENV.stats_from_logmatrix(M, np.argsort(-M.var(0))[:n_hvg], n_hvg)


def t5(M, cls, n_hvg=3000):
    sel = np.argsort(-M.var(0))[:n_hvg]
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
    return float(np.mean(wc) / pooled) if (wc and pooled > 0) else float("nan")


def cpm_log(c):
    lib = c.sum(1, keepdims=True)
    return np.log1p(c / np.where(lib > 0, lib, 1.0) * 1e4)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--cells", type=int, default=3000)
    ap.add_argument("--addresses", type=int, default=41238)
    ap.add_argument("--seed", type=int, default=20261006)
    ap.add_argument("--only", default=None)
    a = ap.parse_args()

    expr = json.loads(Path("results/v77/V77_REAL_CALIBRATION_ENVELOPE_V1.json").read_text())["ACCEPTANCE_ENVELOPES"]
    det = json.loads(Path("results/v77/V77_REAL_DETECTION_ENVELOPE_V1.json").read_text())["ACCEPTANCE_ENVELOPES"]
    T5_REAL = 1.012

    ids = list(SS.SUBSTATE_CANDIDATES) if not a.only else [c.strip() for c in a.only.split(",")]
    out = {}
    for cid in ids:
        cfg = SS.SUBSTATE_CANDIDATES[cid]
        gen = SS.SubStateGenerator(cfg, a.addresses, a.seed)
        g = gen.generate(a.cells, seed=a.seed)
        eta, cls = g["eta"], g["cls"]
        counts = CAND.observe_counts(eta + AB[None, :], a.seed)
        obs = geom(cpm_log(counts))
        detection = geom((counts > 0).astype(np.float64))
        lat = geom(eta)
        r = dict(note=cfg["note"], n_modules=g["n_modules"],
                 module_sizes_top10=sorted(g["module_sizes"], reverse=True)[:10],
                 latent=lat, observed=obs, detection=detection,
                 t5_observed=t5(cpm_log(counts), cls),
                 inside_expression={k: bool(expr[k]["accept_low"] <= obs[k] <= expr[k]["accept_high"])
                                    for k in TARGETS},
                 inside_detection={k: bool(det[k]["accept_low"] <= detection[k] <= det[k]["accept_high"])
                                   for k in TARGETS})
        r["n_expression_inside"] = sum(r["inside_expression"].values())
        r["n_detection_inside"] = sum(r["inside_detection"].values())
        out[cid] = r
        print("%-24s modules=%3d  expr %2d/11  det %2d/11  transitivity %.4f  T5 %.4f"
              % (cid, g["n_modules"], r["n_expression_inside"], r["n_detection_inside"],
                 obs["transitivity"], r["t5_observed"]))

    rec = dict(schema="V77_SUBSTATE_FAMILY_SEARCH_V1",
               smoke_scale=dict(cells=a.cells, addresses=a.addresses, seed=a.seed),
               t5_real=T5_REAL, candidates=out,
               headline_target=dict(statistic="transitivity", real=0.8871,
                                    envelope=[0.8752, 0.8928],
                                    factor_family_range=[0.515, 0.775]))
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(rec, indent=2) + "\n")

    print("\n%-24s %10s" % ("target", "real") + "".join("%13s" % c[:12] for c in ids))
    for k in TARGETS:
        row = "%-24s %10.4f" % (k, expr[k]["point"])
        for c in ids:
            v = out[c]["observed"][k]
            row += "%12.4f%s" % (v, "*" if out[c]["inside_expression"][k] else " ")
        print(row)
    print("%-24s %10.4f" % ("T5 within/pooled", T5_REAL)
          + "".join("%13.4f" % out[c]["t5_observed"] for c in ids))


if __name__ == "__main__":
    main()
