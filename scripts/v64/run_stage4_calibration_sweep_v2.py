#!/usr/bin/env python3
"""How often does the COMPLETE five-gate Stage-4 decision return a pass, per world?

Executes the design frozen in V64_STAGE4_CALIBRATION_PRECOMMIT_V2.json, which was written
and committed before any draw below was made and is bound here by SHA-256. Nothing in this
file chooses a world, a donor count, a draw count or an interpretation.

The V1 sweep measured G1 alone against a fixture whose control arm was drawn at random.
This measures all five gates against a fixture that builds its controls the way the frozen
contract does, and it carries BIOLOGY_POSITIVE as a positive control, because a gate set
that rejects everything would otherwise look like safety.

Every draw is rebuilt to disk and run through the real executor entrypoint. The world
builder fails closed on any violation of the frozen matching rule, so a draw that reaches
the executor is one whose arms satisfy the construction.

No real substrate is read. No correspondence value is computed on real data.
"""
from __future__ import annotations

import json
import math
import os
import subprocess
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nihcard_exact_supplement_builder_v1 as B                      # noqa: E402
import build_stage4_synthetic_worlds_v1 as BW                        # noqa: E402

EXEC = "scripts/v64/stage4_executor_v1.py"
BUILDER = "scripts/v64/build_stage4_synthetic_worlds_v1.py"
PRECOMMIT = "results/v64/phase_b_design/V64_STAGE4_CALIBRATION_PRECOMMIT_V2.json"
OUT = os.path.join(BW.ROOT, "_results")
GATES = ("G1_PRIMARY_LCB95_ABOVE_ZERO",
         "G2_CONTROL_VS_CONTROL_NOT_DISTINGUISHABLE_FROM_ZERO",
         "G3_COVARIATE_BALANCE", "G4_SUPPORT_CONCENTRATION", "G5_FUNNEL_RECONCILES")


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 1.0)
    p, d = k / n, 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def one_draw(world, donors, seed_base):
    b = subprocess.run([sys.executable, BUILDER, "--only", world, "--donors",
                        str(donors), "--seed-base", str(seed_base)],
                       capture_output=True, text=True)
    if b.returncode != 0:
        txt = b.stdout + b.stderr
        if "violates the frozen control construction" in txt:
            # the pre-commitment says this is a fixture defect, not a result
            raise SystemExit("STOP: world build violated the frozen matching rule.\n"
                             "Repair the generator; do not exclude the draw.\n" + txt[-400:])
        return dict(ok=False, stage="build", err=txt[-300:])
    r = subprocess.run([sys.executable, EXEC, "--synthetic-world", world],
                       capture_output=True, text=True)
    if r.returncode != 0:
        return dict(ok=False, stage="run", err=(r.stdout + r.stderr)[-300:])
    R = json.load(open(os.path.join(OUT, "V64_STAGE4_RESULT_%s.json" % world)))
    g, a = R["FIVE_GATE_DECISION"], R["ADJUSTED"]["GENE_BALANCED"]
    return dict(ok=True, all_five=bool(g["ALL_FIVE_PASS"]),
                gates={k: bool(g[k]["passed"]) for k in GATES},
                delta=a["delta"], lcb95=a["lcb95"],
                worst_smd=g["G3_COVARIATE_BALANCE"]["worst_abs_smd"],
                worst_feature=g["G3_COVARIATE_BALANCE"]["worst_feature"],
                cvc=R["CONTROL_A_VS_CONTROL_B"]["delta"],
                trimmed=R["world_manifest"]["matching_audit"][
                    "edges_trimmed_no_admissible_control"])


def main() -> int:
    pc = json.load(open(PRECOMMIT))
    pc_sha = B.sha_file(PRECOMMIT)
    worlds, counts = pc["design"]["worlds"], pc["design"]["donor_counts"]
    n_draws = pc["design"]["draws_per_cell"]
    print("executing pre-committed design %s" % pc_sha[:16])
    print("  %d worlds x %d donor counts x %d draws = %d runs"
          % (len(worlds), len(counts), n_draws, len(worlds) * len(counts) * n_draws))

    cells, t0 = {}, time.time()
    for world in worlds:
        for donors in counts:
            key = "%s@%d" % (world, donors)
            ok, bad = [], []
            for i in range(n_draws):
                d = one_draw(world, donors, 700000 + 1000 * i)
                (ok if d["ok"] else bad).append(d)
                if (i + 1) % 10 == 0:
                    print("    %-30s %2d/%d (%.0f s)" % (key, i + 1, n_draws,
                                                         time.time() - t0), flush=True)
            k = sum(1 for d in ok if d["all_five"])
            lo, hi = wilson(k, n_draws)
            per_gate = {g: dict(passes=sum(1 for d in ok if d["gates"][g]),
                                rate=sum(1 for d in ok if d["gates"][g]) / n_draws)
                        for g in GATES}
            dl = np.array([d["delta"] for d in ok], float)
            smd = np.array([d["worst_smd"] for d in ok if d["worst_smd"] is not None],
                           float)
            feats = {}
            for d in ok:
                feats[d["worst_feature"]] = feats.get(d["worst_feature"], 0) + 1
            cells[key] = dict(
                world=world, donors_configured=donors,
                draws_attempted=n_draws, draws_succeeded=len(ok), draws_failed=len(bad),
                all_five_pass_count=k, all_five_pass_rate=k / n_draws,
                wilson95=[round(lo, 4), round(hi, 4)],
                resolution="UNRESOLVED" if (hi - lo) / 2 > 0.20 else "RESOLVED",
                per_gate_pass_rate=per_gate,
                delta_median=float(np.median(dl)) if dl.size else None,
                delta_range=[float(dl.min()), float(dl.max())] if dl.size else None,
                lcb95_median=float(np.median([d["lcb95"] for d in ok])) if ok else None,
                worst_smd_median=float(np.median(smd)) if smd.size else None,
                worst_smd_feature_counts=feats,
                max_abs_control_vs_control=float(np.max(np.abs([d["cvc"] for d in ok])))
                if ok else None,
                edges_trimmed_max=max([d["trimmed"] for d in ok]) if ok else None,
                failures=[d["err"] for d in bad][:3])
            print("  %-30s ALL_FIVE %2d/%d  rate=%.3f  Wilson [%.3f, %.3f]  %s"
                  % (key, k, n_draws, k / n_draws, lo, hi, cells[key]["resolution"]),
                  flush=True)
            print("      per gate: " + "  ".join("%s=%.2f" % (g[:2], per_gate[g]["rate"])
                                                 for g in GATES), flush=True)

    # ------------------------------------------------------ readings, fixed in advance
    readings = []
    for donors in counts:
        c = {w: cells["%s@%d" % (w, donors)] for w in worlds}
        nul = c["TRUE_NULL"]["all_five_pass_rate"]
        readings.append(dict(
            donors=donors,
            rates={w: c[w]["all_five_pass_rate"] for w in worlds},
            positive_control_works=bool(c["BIOLOGY_POSITIVE"]["all_five_pass_rate"] >= 0.5),
            true_null_at_or_below_nominal=bool(c["TRUE_NULL"]["wilson95"][0] <= 0.05),
            technical_above_null=bool(
                c["MEASURED_TECHNICAL"]["wilson95"][0] > c["TRUE_NULL"]["wilson95"][1]),
            hidden_above_null=bool(
                c["HIDDEN_CONFOUND"]["wilson95"][0] > c["TRUE_NULL"]["wilson95"][1]),
            hidden_delta_vs_biology=None if not c["HIDDEN_CONFOUND"]["delta_median"]
            else round(c["HIDDEN_CONFOUND"]["delta_median"]
                       / c["BIOLOGY_POSITIVE"]["delta_median"], 4)))
    scale = {}
    if len(counts) == 2:
        for w in worlds:
            a = cells["%s@%d" % (w, counts[0])]["all_five_pass_rate"]
            b = cells["%s@%d" % (w, counts[1])]["all_five_pass_rate"]
            scale[w] = dict(rate_at_60=a, rate_at_282=b,
                            direction="RISES" if b > a else "FALLS" if b < a
                            else "UNCHANGED",
                            reading="behaves like a bias: the bound tightens with n while "
                                    "the quantity does not" if b > a else
                                    "behaves like noise; the reduced-scale qualification "
                                    "was conservative" if b < a else "no change")

    print("")
    print("restoring the canonical worlds ...")
    subprocess.run([sys.executable, BUILDER, "--seed-base",
                    str(BW.CANONICAL_SEED_BASE)], capture_output=True, text=True)
    restored = {}
    for w in BW.WORLDS:
        m = json.load(open(os.path.join(BW.ROOT, w, "WORLD_MANIFEST.json")))
        restored[w] = dict(
            seed=m["seed"], eligible_donors=m["geometry"]["eligible_donors"],
            matching_ok=m["matching_audit"]["all_frozen_matching_rules_satisfied"],
            digests_match=all(B.sha_file(os.path.join(BW.ROOT, w, f)) == d
                              for f, d in m["digests"].items()))
    canonical_ok = all(v["digests_match"] and v["eligible_donors"] == 60
                       and v["matching_ok"] for v in restored.values())
    print("  canonical state restored and digest-verified: %s" % canonical_ok)

    out = dict(
        schema="V64_STAGE4_CALIBRATION_SWEEP_V2", date="2026-10-01",
        executes_precommitment=dict(path=PRECOMMIT, sha256=pc_sha),
        supersedes_sweep="V64_STAGE4_CALIBRATION_SWEEP_V1, whose fixture used an unmatched "
                         "control arm and whose rates do not characterise the frozen design",
        design_was_frozen_before_any_draw=True,
        thresholds_or_draw_counts_changed_after_seeing_results=False,
        cells=cells, readings=readings, scale_reading=scale,
        canonical_worlds_restored=restored, canonical_state_verified=canonical_ok,
        what_this_cannot_establish=pc["what_this_cannot_establish"],
        wall_clock_seconds=round(time.time() - t0, 1),
        real_substrate_read=False, computed_correspondence_values=0,
        producer_sha256=B.sha_file(os.path.abspath(__file__)),
        status="COMPLETE" if canonical_ok else "CANONICAL_RESTORE_FAILED")
    p = "results/v64/phase_b_design/V64_STAGE4_CALIBRATION_SWEEP_V2.json"
    with open(p, "w", newline="\n") as fh:
        json.dump(out, fh, indent=2)
    print("")
    for r in readings:
        print("  %d donors: " % r["donors"]
              + "  ".join("%s=%.3f" % (w[:4], r["rates"][w]) for w in worlds))
    print("receipt sha256 " + B.sha_file(p))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
