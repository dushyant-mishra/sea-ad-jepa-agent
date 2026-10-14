"""Follow-up probes: small-donor permutation null with positive refit margin; float rank scan;
projector small-angle numeric floor and its effect on the module's own known-truth world."""
from __future__ import annotations

import json
import math
from fractions import Fraction

import numpy as np

import scripts.v5.td_real_geometry_recurrence_engine_v1 as G
import probe_geometry_engine as P

out = {}

# 1. 3-cell donors, refit margin 0.01: identity permutation forces q_alpha <= observed
rng = np.random.default_rng(21)
train, held = P.world(rng, cells=40, noise=0.01)
rows = P.pipeline(train, [(a[:3], b[:3]) for a, b in held], np.random.default_rng(9))
res = P.adjudicate(rows, ["SRC"], P.ref(rows, 0.01, 0.2))
out["three_cell_donors_refit_0.01"] = {
    "status": res["status"],
    "null_defeat": res["source_details"]["SRC"]["null_defeat_status"],
    "distinct_null_values": sorted({len(set(np.round(r["null_displacements"], 12))) for r in rows}),
    "adverse_bound_equals_observed": all(abs(d["adverse_null_bound"] - d["observed_displacement"]) < 1e-12
                                          for d in res["source_details"]["SRC"]["donors"]),
}

# 2. float rank scan: engine ceil(alpha*n) vs exact rational ceil
bad = {}
for alpha in (0.01, 0.005, 0.01 / 3, 0.0025, 0.05, 0.07):
    hits = []
    for n in range(G.adverse_null_minimum_draws(alpha), 20001):
        eng = max(1, int(math.ceil(float(alpha) * n)))
        exact = max(1, math.ceil(Fraction(alpha) * n)) if alpha != 0.01 / 3 else max(1, math.ceil(Fraction(1, 300) * n))
        if alpha in (0.01, 0.005, 0.0025, 0.05, 0.07):
            exact = max(1, math.ceil(Fraction(str(alpha)) * n))
        if eng != exact:
            hits.append(n)
    bad[str(alpha)] = {"n_mismatches_up_to_20000": len(hits), "first": hits[:8]}
out["float_rank_scan"] = bad
out["min_draws"] = {str(a): G.adverse_null_minimum_draws(a) for a in (0.01, 0.01 / 3, 0.005, 0.07)}

# 3. projector small-angle floor on generic bases; module's own known-truth tolerance is 1e-10
floors = []
for s in range(50):
    r = np.random.default_rng(s)
    A = r.normal(size=(20, 4))
    q, rr = np.linalg.qr(r.normal(size=(4, 4)))
    floors.append(G.projector_rms_displacement(A, A @ q))
out["projector_identical_subspace_floor"] = {"min": min(floors), "median": float(np.median(floors)), "max": max(floors),
                                             "fraction_above_1e-10": float(np.mean(np.array(floors) > 1e-10))}
# true small angle 1e-9 rad: cos-based formula
A = np.eye(5)[:, :2]
B = A.copy(); B[2, 0] = 1e-9
out["projector_true_angle_1e-9"] = G.projector_rms_displacement(A, B)

print(json.dumps(out, indent=1, default=str))
with open(__file__.replace("probe_followup.py", "probe_followup_results.json"), "w") as fh:
    json.dump(out, fh, indent=1, default=str)
