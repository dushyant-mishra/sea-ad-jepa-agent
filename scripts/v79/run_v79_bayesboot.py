#!/usr/bin/env python3
"""V79 Phase D1: nested donor-then-cell Bayesian bootstrap of the corrected reference geometry.

Each draw reweights the 4,726 corrected TRAIN cells (donor masses ~ Dirichlet(1), then cell shares within donor
~ Dirichlet(1)) and recomputes every reference statistic exactly as the corrected builders define them
(v79_geometry: both layers, T5 with raw labels and the 200-cell floor, abundance, depth). Genes, HVGs and
libraries are fixed from the full data, as in the historical donor bootstrap.

  worker  computes draws i with i % workers == worker (seeds from (seed, i), so the split does not change any
          draw); worker 0 also computes the full-data point (uniform weights)
  merge   checks every draw is present exactly once; per statistic: posterior quantiles, the full-data point,
          the resampling shift (posterior median - point) and the historical with-replacement band from the
          corrected envelopes (S159 is measured, not repaired)

Gated like every real-data runner: custody, recovery and benchmark must pass first. Output is internal.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import v79_data as DA  # noqa: E402
import v79_firewall as FW  # noqa: E402
import v79_geometry as GE  # noqa: E402

ROOT = HERE.parents[1]
CACHE = "D:/Jepa project/data/cache/s174_rebuilt_real_train_v1"
BRIDGE = ROOT / "results/v78/V78_S174_SHARD_OPERATOR_BRIDGE_V1.json"
REPLAY = ROOT / "results/v77/s174_replay"
ENVELOPES = {"expression_cp10k_log1p": "V77_REAL_CALIBRATION_ENVELOPE_V1.json",
             "detection_binary": "V77_REAL_DETECTION_ENVELOPE_V1.json",
             "abundance": "V77_REAL_ABUNDANCE_ENVELOPE_V1.json"}


def flatten(d: dict, prefix: str = "") -> dict:
    out = {}
    for k, v in d.items():
        key = f"{prefix}.{k}" if prefix else str(k)
        if isinstance(v, dict):
            out.update(flatten(v, key))
        elif isinstance(v, (int, float, np.floating, np.integer)) and not isinstance(v, bool):
            out[key] = float(v)
    return out


def load_prep():
    X, design = GE.load_builder_ordered(DA.local_path(CACHE), DA.local_path(BRIDGE))
    prep = GE.prepare(X, design["raw_class"], source_library=design["source_library"])
    return prep, design


def worker(a) -> None:
    import run_v79_inference as INF                      # reuse the real-data gate
    INF.preconditions()
    prep, design = load_prep()
    donors = design["donor_id"]
    keys = design["row"].astype(str)                     # internal only: stable cell order within donor
    out = dict(worker=a.worker, workers=a.workers, seed=a.seed, draws={}, point=None)
    t0 = time.time()
    if a.worker == 0:
        out["point"] = flatten(GE.geometry(prep, np.full(prep["n_cells"], 1.0 / prep["n_cells"])))
    for i in range(a.draws):
        if i % a.workers != a.worker:
            continue
        rng = np.random.default_rng([a.seed, i])
        w = GE.nested_dirichlet_weights(donors, rng, cell_keys=[f"{s}|{r}" for s, r in zip(design["stem"], keys)])
        out["draws"][str(i)] = flatten(GE.geometry(prep, w))
    out["seconds"] = time.time() - t0
    path = Path(a.out_dir) / f"d1_part_{a.worker:02d}_of_{a.workers:02d}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline=chr(10)) as fh:
        fh.write(json.dumps(out) + chr(10))
    print("worker", a.worker, "draws", len(out["draws"]), "seconds", round(out["seconds"]))


def merge(a) -> None:
    parts = sorted(Path(a.out_dir).glob("d1_part_*.json"))
    draws, point = {}, None
    for p in parts:
        r = json.loads(p.read_text(encoding="utf-8"))
        for k, v in r["draws"].items():
            if k in draws:
                raise SystemExit(f"draw {k} appears twice")
            draws[k] = v
        point = r["point"] or point
    missing = sorted(set(map(str, range(a.draws))) - set(draws))
    if missing or point is None:
        raise SystemExit(f"incomplete: {len(missing)} draws missing, point present: {point is not None}")
    stats = sorted(point)
    env = {}
    for layer, name in ENVELOPES.items():
        e = json.loads((REPLAY / name).read_text(encoding="utf-8"))["ACCEPTANCE_ENVELOPES"]
        for k, v in e.items():
            env[f"{layer}.{k}"] = v
    rows = {}
    for s in stats:
        x = np.array([draws[str(i)][s] for i in range(a.draws) if s in draws[str(i)]], dtype=np.float64)
        x = x[np.isfinite(x)]
        if len(x) == 0:
            continue
        q = np.quantile(x, [0.05, 0.25, 0.5, 0.75, 0.95])
        row = dict(point=point[s], q05=q[0], q25=q[1], median=q[2], q75=q[3], q95=q[4], mean=float(x.mean()),
                   sd=float(x.std(ddof=1)), n=int(len(x)), resampling_shift=float(q[2] - point[s]),
                   point_inside_bb90=bool(q[0] <= point[s] <= q[4]))
        if s in env:
            h = env[s]
            row.update(historical_point=h["point"], historical_band=[h["accept_low"], h["accept_high"]],
                       historical_point_inside_own_band=bool(h["accept_low"] <= h["point"] <= h["accept_high"]),
                       historical_band_width=h["accept_high"] - h["accept_low"], bb90_width=float(q[4] - q[0]))
        rows[s] = {k: (float(v) if isinstance(v, (np.floating, float)) else v) for k, v in row.items()}
    rec = dict(schema="V79_PHASE_D1_INTERNAL_V1", status="INTERNAL__NOT_SYNTHETIC_CONSUMABLE", draws=a.draws,
               seed=a.seed, parts=[p.name for p in parts],
               method=("nested Bayesian bootstrap: donor Dirichlet(1) x within-donor cell Dirichlet(1); genes, HVGs "
                       "and libraries fixed from the full data; statistics exactly as the corrected builders"),
               statistics=rows, lane=FW.LANE_TERMINAL)
    out = Path(a.out_dir) / "V79_PHASE_D1_INTERNAL_V1.json"
    with open(out, "w", encoding="utf-8", newline=chr(10)) as fh:
        fh.write(json.dumps(rec, indent=1) + chr(10))
    print("merged", a.draws, "draws;", len(rows), "statistics")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["worker", "merge"])
    ap.add_argument("--draws", type=int, default=1000)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--worker", type=int, default=0)
    ap.add_argument("--seed", type=int, default=20261009)
    ap.add_argument("--out-dir", default=str(ROOT / "results/v79/internal/d1"))
    a = ap.parse_args()
    worker(a) if a.mode == "worker" else merge(a)


if __name__ == "__main__":
    main()
