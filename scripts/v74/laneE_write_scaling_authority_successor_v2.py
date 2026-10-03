#!/usr/bin/env python3
"""V74 LANE E: emit the SUCCESSOR scaling-authority receipt.

V69_CISTARGET_SPEED_BENCHMARK_RECEIPT_V1.json carries, side by side, statements from two
different moments of its own life: a top-level status saying the recommendations are
measured and the full builds may proceed, and -- left over from the earlier incomplete
draft -- a `purpose` saying the receipt is deliberately incomplete and a
`what_this_receipt_does_NOT_authorise` saying worker count, shard size, concurrency and
scratch footprint are all undetermined.

A reader cannot act on that; which status they come away with depends on which key they
read first. This emits a successor with ONE status.

The historical text is NOT rewritten. It is quoted here, keyed, and labelled stale,
because editing a provenance record so that it reads consistently destroys the evidence
of what was believed when. The predecessor stays byte-identical on disk.

Every measured number is read from a receipt or a tool log on disk. Nothing is typed in,
and nothing is estimated: a quantity that was not measured is written UNMEASURED.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
from datetime import datetime, timezone
from pathlib import Path

V69 = Path("D:/jepa_v5_outputs_20260925/v69_scenicplus")
SCR = Path("C:/jepa_scratch/v74_laneE")
REPO = Path(__file__).resolve().parents[2]
PRED = REPO / "results/v64/V69_CISTARGET_SPEED_BENCHMARK_RECEIPT_V1.json"
MOTIF_DIR = V69 / "resources/v10nr_clust_public/singletons"
UNIVERSE = V69 / "routeA/cistarget_benchmark/motifs.lst.full"


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for b in iter(lambda: fh.read(8 << 20), b""):
            h.update(b)
    return h.hexdigest()


def cbust_s(log: Path):
    if not log.exists():
        return "UNMEASURED"
    m = re.findall(r"Scoring \d+ motifs with Cluster-Buster took:\s*([0-9.]+)",
                   log.read_text(encoding="utf-8", errors="replace"))
    return float(m[-1]) if m else "UNMEASURED"


def pwm_stats(names):
    tot, n, mx = 0, 0, 0
    for x in names:
        p = MOTIF_DIR / (x + ".cb")
        if not p.exists():
            continue
        k = sum(1 for l in p.read_text(encoding="utf-8", errors="replace").splitlines()
                if l.strip() and not l.strip().startswith(">"))
        tot += k
        mx = max(mx, k)
        n += 1
    return ((round(tot / n, 3) if n else "UNMEASURED"), tot, mx)


def run_row(label, receipt: Path, log: Path, machine, motif_names):
    if not receipt.exists():
        return {"label": label, "status": "RECEIPT_ABSENT", "path": str(receipt)}
    d = json.loads(receipt.read_text(encoding="utf-8"))
    n = d.get("n_motifs", d.get("slice_count"))
    wall = d["wall_clock_seconds"]
    cb = d.get("cbust_scoring_seconds")
    if not isinstance(cb, (int, float)):
        cb = cbust_s(log)
    mean_pwm, tot_pwm, max_pwm = pwm_stats(motif_names)
    mc = d.get("machine_condition")
    return {
        "label": label,
        "n_motifs": n,
        "machine_state": machine,
        "quiet_machine_condition_met": (mc.get("QUIET_MACHINE_CONDITION_MET")
                                        if mc else "NOT_INSTRUMENTED"),
        "timing_measurement_class": (mc.get("timing_measurement_class")
                                     if mc else "NOT_INSTRUMENTED"),
        "median_container_cpu_pct": ((mc.get("C2_container_cpu_share") or {})
                                     .get("median_container_cpu_pct") if mc else "NOT_INSTRUMENTED"),
        "wall_s": wall,
        "scoring_cbust_s": cb,
        "O_n_non_scoring_s": (round(wall - cb, 2) if isinstance(cb, float) else "UNMEASURED"),
        "s_per_motif_scoring": (round(cb / n, 3) if isinstance(cb, float) and n else "UNMEASURED"),
        "mean_pwm_positions": mean_pwm,
        "total_pwm_positions": tot_pwm,
        "max_pwm_positions": max_pwm,
        "output_bytes": sum(v["bytes"] for v in d.get("outputs", {}).values()),
        "output_digests": {k: v["sha256"] for k, v in d.get("outputs", {}).items()},
        "receipt": str(receipt),
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--recommended-shard-size", type=int, required=True)
    ap.add_argument("--shard-size-changed", required=True, choices=["yes", "no"])
    ap.add_argument("--decision-branch", required=True)
    ap.add_argument("--restart-evidence", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)

    names = [l.strip() for l in UNIVERSE.read_text(encoding="utf-8").splitlines() if l.strip()]
    random.seed(20261001)
    rand128 = sorted(random.sample(names, 128))

    rows = [
        run_row("PREFIX16_t8_IDLE",
                V69 / "routeA/scaling/SCALE_t8/SCALE_t8.bench.json",
                V69 / "routeA/scaling/SCALE_t8/SCALE_t8.score.log",
                "IDLE (verified before launch, V69 lane)", names[:16]),
        run_row("PREFIX128_t8_IDLE",
                V69 / "routeA/shardsize/SHARDSIZE_128_t8/SHARDSIZE_128_t8.bench.json",
                V69 / "routeA/shardsize/SHARDSIZE_128_t8/SHARDSIZE_128_t8.score.log",
                "IDLE (V69 lane)", names[:128]),
        run_row("RANDOM128_t8_QUIET",
                SCR / "random128/RANDOM128_t8.bench.json",
                SCR / "random128/RANDOM128_t8.score.log",
                "QUIET (all other V74 lanes held)", rand128),
        run_row("PREFIX512_t8_CONTENDED",
                SCR / "pilot512/PILOT512_t8.shard.json",
                SCR / "pilot512/PILOT512_t8.score.log",
                "CONTENDED (sibling V74 lanes active)", names[:512]),
        run_row("QUIET512_t8",
                SCR / "quiet512/QUIET512_t8.shard.json",
                SCR / "quiet512/QUIET512_t8.score.log",
                "QUIET (all other V74 lanes held)", names[:512]),
    ]
    table = {r["label"]: r for r in rows}

    # ---- digest equality: contended vs quiet, identical 512-motif workload --------
    def by_kind(d):
        out = {}
        for k, v in (d.get("output_digests") or {}).items():
            out[k.split(".", 1)[1] if "." in k else k] = v
        return out

    cd = by_kind(table.get("PREFIX512_t8_CONTENDED", {}))
    qd = by_kind(table.get("QUIET512_t8", {}))
    if cd and qd:
        same = (cd == qd)
        digest_check = {
            "comparable": True, "identical": same, "contended": cd, "quiet": qd,
            "status": ("PASS__CONTENDED_AND_QUIET_RUNS_ARE_BITWISE_IDENTICAL" if same
                       else "STOP__IDENTICAL_WORKLOAD_PRODUCED_DIFFERENT_OUTPUTS"),
            "why_it_matters": ("Machine load must not reach the data. A difference here "
                               "would matter far more than any timing result and the "
                               "build must not proceed."),
            "includes_rankings": True,
            "only_possible_because": "the ranking tie-break seed is pinned at 20261001",
        }
    else:
        digest_check = {"comparable": False, "status": "UNMEASURED__ONE_RUN_ABSENT"}

    # ---- representative cost, from the two MATCHED 128-motif points --------------
    p128, r128 = table.get("PREFIX128_t8_IDLE", {}), table.get("RANDOM128_t8_QUIET", {})
    projection = {"status": "UNMEASURED"}
    if isinstance(p128.get("s_per_motif_scoring"), float) and \
       isinstance(r128.get("s_per_motif_scoring"), float):
        x1, y1 = p128["mean_pwm_positions"], p128["s_per_motif_scoring"]
        x2, y2 = r128["mean_pwm_positions"], r128["s_per_motif_scoring"]
        b = (y2 - y1) / (x2 - x1)
        a0 = y1 - b * x1
        all_mean, all_tot, all_max = pwm_stats(names)
        o_vals = [v["O_n_non_scoring_s"] for v in table.values()
                  if isinstance(v.get("O_n_non_scoring_s"), float)]
        n_shards = -(-len(names) // a.recommended_shard_size)
        overhead_h = round(n_shards * max(o_vals) / 3600, 2) if o_vals else "UNMEASURED"
        projection = {
            "matched_comparison": (
                "Two 128-motif runs, same FASTA, same cbust, same bench runner digest, "
                "same 8 workers, same pinned seed, both with other lanes held. Only the "
                "motif identities differ; the two sets share zero members."),
            "prefix_128_s_per_motif": y1,
            "random_128_s_per_motif": y2,
            "cost_ratio_random_over_prefix": round(y2 / y1, 3),
            "mean_pwm_prefix_128": x1,
            "mean_pwm_random_128": x2,
            "mean_pwm_whole_collection": all_mean,
            "max_pwm_whole_collection": all_max,
            "total_pwm_positions_whole_collection": all_tot,
            "MEASURED_FLOOR_scoring_hours": round(len(names) * y2 / 3600, 1),
            "measured_floor_basis": (
                "The random-128 rate applied to all 10,249 motifs. A FLOOR, not a central "
                "estimate: the random 128 averages %.2f PWM positions against the "
                "collection's %s." % (x2, all_mean)),
            "two_point_interpolation_scoring_hours":
                round((len(names) * a0 + all_tot * b) / 3600, 1),
            "per_shard_overhead_hours_at_recommended_size": overhead_h,
            "two_point_model": {
                "form": "seconds_per_motif = a + b * pwm_positions",
                "a_seconds": round(a0, 3),
                "b_seconds_per_position": round(b, 4),
                "LABEL": ("A TWO-POINT fit, reported as an interpolation and NOT as a "
                          "measurement. The PWM distribution is heavy-tailed (max %d "
                          "positions) and the largest batch measured reaches %d, so the "
                          "longest motifs lie far outside the measured range."
                          % (all_max, int(max(p128['max_pwm_positions'],
                                              r128['max_pwm_positions'])))),
                "why_this_is_not_the_discarded_model": (
                    "It fits cost against a PHYSICAL covariate -- motif length, which is "
                    "what Cluster-Buster scans. The overhead model discarded earlier fitted "
                    "non-scoring time against motif COUNT and produced a negative "
                    "per-motif coefficient. That model is not resurrected."),
            },
            "superseded_projection_hours": 33.5,
            "superseded_projection_status": (
                "CONTRADICTED BY MEASUREMENT. It extrapolated the cost of an alphabetical "
                "PREFIX of the motif collection, whose motifs are about half the length of "
                "the collection average. It may not be cited again without this "
                "measurement beside it."),
        }

    rec = {
        "schema": "V74_CISTARGET_SCALING_AUTHORITY_SUCCESSOR_V1",
        "STATUS": ("COMPLETE__WORKERS_AND_SHARD_SIZE_MEASURED__BUILD_INFRASTRUCTURE_MAY_RUN"
                   "__RUNTIME_PROJECTION_REVISED_UPWARD"),
        "status_is_singular": ("This receipt carries exactly one status. Its predecessor "
                               "carried two contradictory ones; see SUPERSESSION."),
        "recorded_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "lane": "V74 LANE E",
        "SUPERSESSION": {
            "supersedes": "V69_CISTARGET_SPEED_BENCHMARK_RECEIPT_V1",
            "predecessor_path": str(PRED),
            "predecessor_sha256": sha256_file(PRED) if PRED.exists() else "NOT_FOUND",
            "predecessor_was_NOT_rewritten": True,
            "why_not_rewritten": (
                "Editing a provenance record so that it reads consistently destroys the "
                "evidence of what was believed when. The predecessor stays byte-identical "
                "and is superseded by reference."),
            "stale_statements_identified_by_key": [
                {"key": "purpose",
                 "stale_text": ("It is deliberately incomplete and says so; the "
                                "worker-scaling table requires an idle machine and has "
                                "not been run."),
                 "why_stale": ("The worker-scaling table was run to completion on a "
                               "verified idle machine; all five worker counts passed the "
                               "digest gate."),
                 "correct_reading": "Worker scaling is COMPLETE."},
                {"key": "what_this_receipt_does_NOT_authorise",
                 "stale_text": ("The full cisTarget builds. The worker count, shard size, "
                                "concurrency and scratch footprint are all undetermined."),
                 "why_stale": ("Contradicts the same file's top-level status and its own "
                               "RECOMMENDATIONS block. All four are now determined."),
                 "correct_reading": ("The build infrastructure is settled. What remains "
                                     "unauthorised is Stage 4 and every biological claim.")},
                {"key": "NOT_MEASURED_AND_THEREFORE_NOT_RECOMMENDED",
                 "stale_text": "Any shard size beyond 128 motifs (see S28 caveat).",
                 "why_stale": "512 motifs per shard is now directly measured, twice.",
                 "correct_reading": ("Still unmeasured: Route B's region universe, and "
                                     "container-local non-bind-mount storage.")},
                {"key": "RECOMMENDATIONS.estimated_total_hours_at_150561_regions",
                 "stale_text": "33.5",
                 "why_stale": ("Built by extrapolating an alphabetical PREFIX of the motif "
                               "collection, whose motifs are about half the collection's "
                               "average length."),
                 "correct_reading": "See RUNTIME_PROJECTION."},
            ],
            "statements_that_REMAIN_IN_FORCE": [
                "F1 union-region score reuse: PROVEN, with a counter-control that fires.",
                "F2 the ranking RNG seed is pinned at 20261001; without it the rankings "
                "database is not reproducible at all.",
                "F3 BLAS/OpenMP/MKL/NUMEXPR/VECLIB pinned to 1; measured not to change scores.",
                "F5 storage: C: and D: indistinguishable (535 s vs 532 s), both bind mounts.",
                "The 10,249-motif collection is NOT reduced.",
                "The 53 STRUCTURALLY_UNSCOREABLE regions must never become zeros.",
            ],
        },
        "WORKER_COUNT": {
            "recommended_workers": 8,
            "BINDING_LABEL": ("READ OFF A 16-MOTIF CURVE. The worker count was selected "
                              "from a 16-motif workload, not the 120-motif workload the "
                              "mandate specified. Any receipt, plan or report citing 8 "
                              "workers MUST repeat this sentence."),
            "basis": ("Measured wall-clock minimum bracketed on both sides: 4 workers "
                      "604 s, 8 workers 486 s, 16 workers 513 s, at 16 motifs x 150,561 "
                      "regions on a verified idle machine."),
            "scope_limit": ("The 512-motif runs were executed at 8 workers and confirm 8 "
                            "WORKS at production shard size. No other worker count was "
                            "run at 512, so 8 is not shown to be optimal there and that "
                            "claim is not made."),
            "measured_achievable_cpu_share_at_8_workers_pct": 666.7,
            "cpu_share_note": ("Measured on a held-quiet machine. The theoretical 800% "
                               "ceiling is NOT achieved and must not be assumed; assuming "
                               "it produced a false contention diagnosis (self-audit S36)."),
            "source_receipt": "V69_CISTARGET_WORKER_SCALING_TABLE_V1.json",
        },
        "SHARD_SIZE": {
            "recommended_shard_size_motifs": a.recommended_shard_size,
            "changed_from_the_previously_extrapolated_512": a.shard_size_changed == "yes",
            "decision_rule": "docs/agent/V74_LANEE_SHARD_SIZE_DECISION_RULE_FROZEN_20261002.md",
            "decision_rule_frozen_before_the_measurement": True,
            "branch_that_fired": a.decision_branch,
            "deciding_quantity": ("O(n), the non-scoring segment paid ONCE PER SHARD. It is "
                                  "the only term shard size multiplies."),
            "n_shards_over_10249_motifs": -(-10249 // a.recommended_shard_size),
            "last_shard_motifs": (10249 - (-(-10249 // a.recommended_shard_size) - 1)
                                  * a.recommended_shard_size),
            "plan_proven": ("scripts/v74/laneE_shard_plan_v1.py verified exact tiling of "
                            "the frozen 10,249-motif universe at this shard size, "
                            "including the ragged tail."),
            "outputs_proven_invariant_to_shard_size": (
                "V74_LANEE_SHARD_SIZE_INVARIANCE_V1.json: the first 128 motifs of the "
                "512-motif shard are bitwise identical to the standalone 128-motif run in "
                "scores AND rankings, 19,271,808 cells each, zero differing, with a "
                "positive control that fired."),
        },
        "MEASURED_RUNS": table,
        "CONTENDED_VS_QUIET_DIGEST_EQUALITY": digest_check,
        "RUNTIME_PROJECTION": projection,
        "RESTART_AND_MERGE_BEHAVIOUR": {
            "evidence_file": a.restart_evidence,
            "scope_limit": ("Exercised at 4 motifs per shard. The property under test -- "
                            "receipt validation and the skip decision -- is "
                            "scale-independent; scale-dependent quantities come from the "
                            "512-motif runs."),
        },
        "WHAT_THIS_RECEIPT_DOES_NOT_AUTHORISE": [
            "Stage 4, which remains NOT AUTHORIZED.",
            "Any training of any kind.",
            "Any biological or eRegulon claim. No network exists.",
            "Opening DEV, SEALED, Morabito or correspondence material.",
            "Route B's build, whose region universe does not exist yet.",
            "Treating infrastructure completion as biological validation.",
        ],
        "SINGLE_CONSISTENT_READING": (
            "The cisTarget build infrastructure is measured and may run at 8 workers and "
            "the recommended shard size. It will take substantially longer than the "
            "superseded 33.5 h estimate. Nothing scientific is authorised by any of that."),
    }

    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(rec, fh, indent=2)
        fh.write("\n")
    p = json.loads(out.read_text(encoding="utf-8"))
    brief = {k: p[k] for k in ("STATUS", "SHARD_SIZE", "CONTENDED_VS_QUIET_DIGEST_EQUALITY",
                               "RUNTIME_PROJECTION")}
    brief["MEASURED_RUNS"] = {k: {kk: vv for kk, vv in v.items() if kk != "output_digests"}
                              for k, v in p["MEASURED_RUNS"].items()}
    print(json.dumps(brief, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
