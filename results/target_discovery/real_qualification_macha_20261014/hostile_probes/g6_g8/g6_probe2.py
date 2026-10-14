"""Follow-up G6 probes: near-constant column blowup, unit-dependent verdict flip, negative-world false PASS.

Usage: python -B g6_probe2.py <worktree_root>
"""
from __future__ import annotations

import json
import sys
from concurrent.futures import ProcessPoolExecutor

import numpy as np

sys.path.insert(0, sys.argv[1])
import scripts.v5.td_real_teacher_information_probe_v1 as G  # noqa: E402

sys.path.insert(0, __file__.rsplit("\\", 1)[0].rsplit("/", 1)[0])
from g6_probe import world  # noqa: E402

OUT: dict = {}


def neg(args):
    seed, kind = args
    rng = np.random.default_rng(seed)
    donors, sx, tx, y = [], [], [], []
    for d in range(8):
        for _ in range(30):
            s = rng.normal()
            donors.append(f"D{d:02d}")
            sx.append([s])
            if kind == "noise_cols":
                tx.append([s] + list(rng.normal(size=3)))
            else:  # redundant noisy copy of student information
                tx.append([s, s + 0.05 * rng.normal()])
            y.append([s + rng.normal(), rng.normal()])
    out = G.compare_teacher_student(donor_ids=donors, student_x=sx, teacher_x=tx, y=y)
    return kind, out["status"]


def flip(seed):
    res = {}
    for ys in ((1.0, 1.0), (1000.0, 1.0), (1.0, 1000.0)):
        dd, ssx, ttx, yy = world(seed, b=0.6, y_scale=ys)
        res[str(ys)] = G.compare_teacher_student(donor_ids=dd, student_x=ssx, teacher_x=ttx, y=yy)["status"]
    return seed, res


def main():
    # near-constant column: constant 0.1 in all donors except the held-out one
    rng = np.random.default_rng(3)
    donors, x_exact, x_float, y = [], [], [], []
    for d in range(8):
        for _ in range(30):
            s = rng.normal()
            donors.append(f"D{d:02d}")
            x_exact.append([s, 0.0 if d < 7 else 1.0])
            x_float.append([s, 0.1 if d < 7 else 0.2])  # same information content as x_exact (affine image)
            y.append([s + rng.normal()])
    re = G.nested_donor_probe(donors, x_exact, y)
    rf = G.nested_donor_probe(donors, x_float, y)
    OUT["near_const_heldout_D07_mse_exact_vs_float"] = [re["donor_mse"]["D07"], rf["donor_mse"]["D07"]]
    OUT["near_const_other_donors_max_abs_diff"] = max(abs(re["donor_mse"][d] - rf["donor_mse"][d]) for d in re["donor_mse"] if d != "D07")
    fit = G.fit_standardizer([r for r, d in zip(x_float, donors) if d != "D07"])
    OUT["near_const_train_scale_col2"] = fit["scale"][1]
    OUT["near_const_heldout_standardized_col2"] = G.apply_standardizer([[0.0, 0.2]], fit)[0][1]

    with ProcessPoolExecutor(max_workers=8) as ex:
        flips = list(ex.map(flip, range(2000, 2016)))
        negs = list(ex.map(neg, [(s, k) for k in ("noise_cols", "redundant_copy") for s in range(3000, 3024)]))
    OUT["unit_rescale_status_by_seed"] = {s: r for s, r in flips if len(set(r.values())) > 1}
    OUT["unit_rescale_n_seeds_verdict_changes"] = sum(len(set(r.values())) > 1 for _, r in flips)
    counts: dict = {}
    for k, st in negs:
        counts.setdefault(k, {}).setdefault(st, 0)
        counts[k][st] += 1
    OUT["negative_world_status_counts_24_seeds"] = counts
    print(json.dumps(OUT, indent=1, default=str))


if __name__ == "__main__":
    main()
