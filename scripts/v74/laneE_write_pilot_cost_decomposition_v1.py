#!/usr/bin/env python3
"""V74 LANE E: decompose the measured cisTarget cost into terms that are physical.

The 512-motif pilot came in at 7,222 s against an extrapolation of about 6,011 s. The
useful question is not "by how much" but "WHICH TERM". This answers that from the tool's
own phase timers and from the motif collection itself, not from a fitted model -- the
earlier fitted overhead model produced a negative per-motif coefficient and was rightly
discarded, so nothing here fits coefficients to wall-clock.

Three terms are separated:

  1. O(n), the non-scoring segment paid ONCE PER SHARD. This is what shard size
     multiplies, and it is therefore the only term the shard-size decision depends on.
     It is read from the tool's own per-phase timers, not inferred.

  2. The per-motif SCORING cost. This is paid for every motif regardless of how the
     motifs are grouped, so no shard size changes it. If it rose, shrinking shards
     cannot help and would add serial segments.

  3. MOTIF COMPOSITION. Cluster-Buster scan cost scales with motif length. Every
     benchmark in this project has used a PREFIX of an alphabetically sorted collection,
     and a prefix of a sorted list is not a random sample.

Usage: see the lane's handoff. All inputs are read from disk.
"""
from __future__ import annotations

import argparse
import json
import re
import statistics
import random
from datetime import datetime, timezone
from pathlib import Path

PHASE_PATTERNS = {
    "scoring_cbust_s": r"Scoring \d+ motifs with Cluster-Buster took:\s*([0-9.]+)",
    "write_db1_s": r"Writing cisTarget regions vs motifs scores db took:\s*([0-9.]+)",
    "write_db2_s": r"Writing cisTarget motifs vs regions scores db took:\s*([0-9.]+)",
    "create_rankings_s": r"Creating cisTarget rankings db from cisTarget scores db took:\s*([0-9.]+)",
    "write_rankings_s": r"Writing cisTarget motifs vs regions rankings db took:\s*([0-9.]+)",
}


def phases(log: Path) -> dict:
    if not log.exists():
        return {"status": "LOG_ABSENT", "path": str(log)}
    txt = log.read_text(encoding="utf-8", errors="replace")
    out = {}
    for k, pat in PHASE_PATTERNS.items():
        m = re.findall(pat, txt)
        out[k] = float(m[-1]) if m else "UNMEASURED"
    return out


def pwm_positions(cb: Path) -> int:
    n = 0
    for line in cb.read_text(encoding="utf-8", errors="replace").splitlines():
        s = line.strip()
        if s and not s.startswith(">"):
            n += 1
    return n


def describe(label, names, motif_dir: Path) -> dict:
    L = []
    for n in names:
        p = motif_dir / (n + ".cb")
        if p.exists():
            L.append(pwm_positions(p))
    if not L:
        return {"label": label, "status": "NO_MOTIF_FILES_FOUND"}
    return {
        "label": label,
        "n_motifs": len(L),
        "pwm_positions_mean": round(statistics.mean(L), 3),
        "pwm_positions_median": statistics.median(L),
        "pwm_positions_min": min(L),
        "pwm_positions_max": max(L),
        "pwm_positions_total": sum(L),
    }


def sampler_summary(p: Path) -> dict:
    if not p.exists():
        return {"status": "ABSENT"}
    cpu, host, mem, ts = [], [], [], []
    for line in p.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        ts.append(d.get("utc"))
        c = d.get("container_cpu_pct", "")
        if isinstance(c, str) and c.endswith("%"):
            try:
                cpu.append(float(c[:-1]))
            except ValueError:
                pass
        h = d.get("host_cpu_load_pct", "")
        try:
            host.append(float(h))
        except (TypeError, ValueError):
            pass
        m = d.get("container_mem", "")
        if "MiB /" in m:
            mem.append(float(m.split("MiB")[0]))
        elif "GiB /" in m:
            mem.append(float(m.split("GiB")[0]) * 1024)
    return {
        "n_samples": len(ts),
        "first_sample_utc": ts[0] if ts else None,
        "last_sample_utc": ts[-1] if ts else None,
        "cadence_note": ("The sampler's sleep is 15 s but each sample costs two docker "
                         "stats calls and a CIM query, so the realised cadence is longer. "
                         "The realised cadence is reported, not the sleep value."),
        "container_cpu_pct_mean": round(statistics.mean(cpu), 1) if cpu else "UNMEASURED",
        "container_cpu_pct_max": max(cpu) if cpu else "UNMEASURED",
        "host_cpu_load_pct_mean": round(statistics.mean(host), 1) if host else "UNMEASURED",
        "host_cpu_load_pct_min": min(host) if host else "UNMEASURED",
        "host_cpu_load_pct_max": max(host) if host else "UNMEASURED",
        "container_peak_mem_mib": round(max(mem), 1) if mem else "UNMEASURED",
        "peak_memory_is_a_SAMPLED_peak": ("Sampled, not a true high-water mark. The "
                                          "container was run with --rm so no cgroup "
                                          "max_usage could be read after exit."),
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--random128-bench", default=None,
                    help="bench json of the random-128 composition run, if it exists")
    a = ap.parse_args(argv)

    V69 = Path("D:/jepa_v5_outputs_20260925/v69_scenicplus")
    SCR = Path("C:/jepa_scratch/v74_laneE")
    motif_dir = V69 / "resources/v10nr_clust_public/singletons"
    universe = V69 / "routeA/cistarget_benchmark/motifs.lst.full"
    names = [l.strip() for l in universe.read_text(encoding="utf-8").splitlines() if l.strip()]

    runs = {
        "PREFIX16_t8_IDLE": {
            "n_motifs": 16, "wall_s": 486, "machine": "IDLE",
            "log": V69 / "routeA/scaling/SCALE_t8/SCALE_t8.score.log"},
        "PREFIX128_t8_IDLE": {
            "n_motifs": 128, "wall_s": 1694, "machine": "IDLE",
            "log": V69 / "routeA/shardsize/SHARDSIZE_128_t8/SHARDSIZE_128_t8.score.log"},
        "PREFIX512_t8_CONTENDED": {
            "n_motifs": 512, "wall_s": 7222, "machine": "CONTENDED",
            "log": SCR / "pilot512/PILOT512_t8.score.log"},
    }

    if a.random128_bench and Path(a.random128_bench).exists():
        b = json.loads(Path(a.random128_bench).read_text(encoding="utf-8"))
        runs["RANDOM128_t8_IDLE"] = {
            "n_motifs": b["n_motifs"], "wall_s": b["wall_clock_seconds"],
            "machine": "IDLE",
            "log": Path(a.random128_bench).with_suffix("").with_suffix("")
                   .parent / (b["run_id"] + ".score.log")}

    table = {}
    for k, v in runs.items():
        ph = phases(Path(v["log"]))
        sc = ph.get("scoring_cbust_s")
        non_scoring = (round(v["wall_s"] - sc, 2) if isinstance(sc, float) else "UNMEASURED")
        accounted = sum(x for kk, x in ph.items()
                        if kk != "scoring_cbust_s" and isinstance(x, float))
        table[k] = {
            "n_motifs": v["n_motifs"],
            "machine_state": v["machine"],
            "wall_s": v["wall_s"],
            "scoring_cbust_s": sc,
            "O_n_non_scoring_s": non_scoring,
            "phase_timers": {kk: vv for kk, vv in ph.items() if kk != "scoring_cbust_s"},
            "non_scoring_accounted_by_phase_timers_s": round(accounted, 2),
            "non_scoring_unaccounted_s": (round(non_scoring - accounted, 2)
                                          if isinstance(non_scoring, float) else "UNMEASURED"),
            "s_per_motif_scoring": (round(sc / v["n_motifs"], 3)
                                    if isinstance(sc, float) else "UNMEASURED"),
        }

    random.seed(20261001)
    composition = {
        "motif_dir": str(motif_dir),
        "frozen_universe": str(universe),
        "n_motifs_in_universe": len(names),
        "slices": [
            describe("PREFIX 1-16", names[:16], motif_dir),
            describe("PREFIX 1-128", names[:128], motif_dir),
            describe("PREFIX 129-512 (the 512-pilot's marginal motifs)", names[128:512], motif_dir),
            describe("PREFIX 1-512", names[:512], motif_dir),
            describe("RANDOM 128, seed 20261001", sorted(random.sample(names, 128)), motif_dir),
            describe("WHOLE COLLECTION 1-10249", names, motif_dir),
        ],
        "why_this_matters": (
            "Cluster-Buster scan cost scales with motif length. Every benchmark in this "
            "project has used a PREFIX of an alphabetically sorted collection, and a "
            "prefix of a sorted list is not a random sample."),
    }

    samplers = {
        "PREFIX512_t8_CONTENDED": sampler_summary(SCR / "logs/PILOT512_t8.resource_samples.jsonl"),
    }
    if "RANDOM128_t8_IDLE" in runs:
        samplers["RANDOM128_t8_IDLE"] = sampler_summary(
            SCR / "logs/RANDOM128_t8.resource_samples.jsonl")

    rec = {
        "schema": "V74_LANEE_CISTARGET_COST_DECOMPOSITION_V1",
        "recorded_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "question": "WHICH term of the cisTarget cost grows, and does shard size touch it?",
        "method_note": ("Phase timers are the tool's own, read from its logs. No "
                        "coefficients are fitted to wall clock. The earlier fitted "
                        "overhead model produced a negative per-motif term and was "
                        "discarded as falsified; it is not resurrected here."),
        "RUNS": table,
        "MOTIF_COMPOSITION": composition,
        "RESOURCE_SAMPLERS": samplers,
    }

    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(rec, fh, indent=2)
        fh.write("\n")
    persisted = json.loads(out.read_text(encoding="utf-8"))
    print(json.dumps({"RUNS": persisted["RUNS"],
                      "MOTIF_COMPOSITION": persisted["MOTIF_COMPOSITION"]["slices"]},
                     indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
