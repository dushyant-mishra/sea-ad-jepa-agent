#!/usr/bin/env python3
"""Qualify serial-vs-parallel equivalence for the repaired Stage-4 K-curve runner.

This is the last execution-scheduling gate before the corrected 100-draw curve may run.
The SAME scientific draw identities are executed twice: first serially, then in parallel.
The second pass deliberately reuses the same JEPA_SYNTHETIC_RUN_ID namespaces after the
first pass has completed. A scheduling-only change is qualified only if every per-draw
result JSON is byte-identical.

No real Stage-4 substrate is read. No correspondence value is computed on real data.
"""
from __future__ import annotations

import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nihcard_exact_supplement_builder_v1 as B
import run_stage4_g2_sensitivity_curve_v1 as R

OUT = "results/v64/phase_b_design/V73_STAGE4_KCURVE_SERIAL_PARALLEL_EQUIVALENCE_V1.json"
SMOKE_SPECS = (
    (5, 0, 800000),
    (5, 1, 801000),
    (200, 0, 800000),
    (200, 1, 801000),
)
DONORS = 60
PARALLEL_WORKERS = 2


def execute_serial():
    out = {}
    for K, draw, seed in SMOKE_SPECS:
        d = R.one_draw(K, DONORS, seed, draw)
        if not d.get("ok"):
            raise RuntimeError("serial draw failed K=%s draw=%s: %s" %
                               (K, draw, d.get("err")))
        out[(K, draw)] = d
    return out


def execute_parallel():
    out = {}
    with ThreadPoolExecutor(max_workers=PARALLEL_WORKERS) as pool:
        futs = {
            pool.submit(R.one_draw, K, DONORS, seed, draw): (K, draw)
            for K, draw, seed in SMOKE_SPECS
        }
        for fut in as_completed(futs):
            key = futs[fut]
            d = fut.result()
            if not d.get("ok"):
                raise RuntimeError("parallel draw failed K=%s draw=%s: %s" %
                                   (key[0], key[1], d.get("err")))
            out[key] = d
    return out


def main() -> int:
    t0 = time.time()
    serial = execute_serial()
    serial_snapshot = {
        k: dict(result_sha256=v["result_sha256"],
                run_id=v["run_id"],
                seed_base=v["seed_base"],
                partition_semantics=v["partition_semantics"],
                realised_occupied_factors=v["realised_occupied_factors"])
        for k, v in serial.items()
    }

    parallel = execute_parallel()
    rows = []
    all_equal = True
    for K, draw, seed in SMOKE_SPECS:
        s = serial_snapshot[(K, draw)]
        p = parallel[(K, draw)]
        equal = (
            s["result_sha256"] == p["result_sha256"]
            and s["run_id"] == p["run_id"] == R.run_id_for(K, draw, seed)
            and s["seed_base"] == p["seed_base"] == seed
            and p["partition_semantics"] == "EXACT_K_OCCUPIED_BALANCED_BLOCKS"
            and p["realised_occupied_factors"] == K
        )
        all_equal &= equal
        rows.append(dict(
            K=K, draw_index=draw, seed_base=seed,
            run_id=s["run_id"],
            serial_result_sha256=s["result_sha256"],
            parallel_result_sha256=p["result_sha256"],
            byte_identical=bool(s["result_sha256"] == p["result_sha256"]),
            identity_equal=bool(s["run_id"] == p["run_id"]),
            holds=bool(equal),
        ))

    out = dict(
        schema="V73_STAGE4_KCURVE_SERIAL_PARALLEL_EQUIVALENCE_V1",
        date="2026-10-02",
        status="PASS" if all_equal else "FAIL",
        purpose="prove scheduling-only parallelism cannot change a repaired K-curve draw",
        smoke_specs=[dict(K=K, draw_index=d, seed_base=s)
                     for K, d, s in SMOKE_SPECS],
        donors=DONORS,
        serial_workers=1,
        parallel_workers=PARALLEL_WORKERS,
        identity_rule="seed and run id depend only on (K, draw_index); worker number, completion order, PID and wall clock are excluded",
        comparison="byte-identical per-draw Stage4 result JSON SHA-256",
        rows=rows,
        all_draws_byte_identical=bool(all_equal),
        runner_sha256=B.sha_file(os.path.abspath(
            "scripts/v64/run_stage4_g2_sensitivity_curve_v1.py")),
        builder_sha256=B.sha_file(os.path.abspath(
            "scripts/v64/build_stage4_synthetic_worlds_v1.py")),
        executor_sha256=B.sha_file(os.path.abspath(
            "scripts/v64/stage4_executor_v1.py")),
        wall_clock_seconds=round(time.time() - t0, 1),
        real_substrate_read=False,
        computed_real_correspondence_values=0,
    )
    with open(OUT, "w", newline="\n") as fh:
        json.dump(out, fh, indent=2)
    print("%s: %d/%d per-draw serial/parallel digests identical" %
          (out["status"], sum(r["holds"] for r in rows), len(rows)))
    print("receipt sha256 " + B.sha_file(OUT))
    return 0 if all_equal else 1


if __name__ == "__main__":
    raise SystemExit(main())
