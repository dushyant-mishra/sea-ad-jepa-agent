#!/usr/bin/env python3
"""Committed producer for V77_REAL_ABUNDANCE_ENVELOPE_V1 (defect S141).

The frozen abundance envelope, which rejected every dynamic-range arm, was computed by an inline
script that was never committed: session transcript line 59147, 2026-10-06T17:53:35Z, the same
tool call that added abundance_stats() to build_v77_calibration_envelope.py. The transcript also
supports the freeze claim recorded in it: the Observer-V2 candidate code first appears at
18:21:58Z, about half an hour later.

This file is that computation, transcribed without change, so the envelope can be reproduced
from a committed head. It is POST-HOC PACKAGING of a computation that already ran; it does not
make the original run prospective, and it never overwrites the frozen file. Reproduction is
judged by verify_v77_reproduction.py, byte for byte.

Real TRAIN access is pathology-blind, TRAIN-only and read-only, through load_real, which
refuses pathology fields.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_v77_real_calibration as RC  # noqa: E402
import build_v77_calibration_envelope as ENV  # noqa: E402

FROZEN = HERE.parents[1] / "results" / "v77" / "V77_REAL_ABUNDANCE_ENVELOPE_V1.json"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, help="where to write the reproduced envelope")
    a = ap.parse_args()
    out = Path(a.out).resolve()
    if out == FROZEN.resolve():
        sys.exit("refusing: the frozen envelope is never overwritten; write the reproduction elsewhere")

    # ---- transcribed unchanged from the inline producer ----
    X, cls, don, src, dig = RC.load_real(RC.DEFAULT_CACHE)
    n, G = X.shape; lib = np.asarray(X.sum(1)).ravel()
    gdet = np.asarray((X > 0).sum(0)).ravel() / n
    keep = np.where(gdet > 0.05)[0]
    C = np.asarray(X[:, keep].todense())
    point = ENV.abundance_stats(C, lib[:, None])
    donors = np.unique(don); rng = np.random.default_rng(20261006); boots = []
    for b in range(24):
        pick = rng.choice(donors, size=len(donors), replace=True)
        idx = np.concatenate([np.where(don == d)[0] for d in pick])
        boots.append(ENV.abundance_stats(C[idx], lib[idx][:, None]))
    env = {}
    for k in point:
        v = np.array([bb[k] for bb in boots], float)
        env[k] = dict(point=point[k], boot_sd=float(v.std(ddof=1)),
                      accept_low=float(np.quantile(v, .05)), accept_high=float(np.quantile(v, .95)))
    rec = dict(schema="V77_REAL_ABUNDANCE_ENVELOPE_V1",
               frozen_before_any_observer_v2_candidate_was_evaluated=True,
               source=dict(cache=str(RC.DEFAULT_CACHE), n_shards=len(dig), shard_digests=dig,
                           pathology_blind=True, train_only=True, read_only=True),
               gene_universe=dict(detection_floor=0.05, genes_kept=int(len(keep)),
                                  note="the SAME filtering used for the frozen topology envelope"),
               resampling=dict(unit="donor", n_donors=int(len(donors)), n_bootstrap=24, seed=20261006),
               ACCEPTANCE_ENVELOPES=env)
    # ---- end of transcription; the original wrote with newline="\n" and no trailing newline ----
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="\n") as fh:
        fh.write(json.dumps(rec, indent=2))
    for k, v in env.items():
        print("%-38s %10.4f %9.4f %10.4f %10.4f" % (k, v["point"], v["boot_sd"],
                                                     v["accept_low"], v["accept_high"]))


if __name__ == "__main__":
    main()
