#!/usr/bin/env python3
"""End-to-end qualification: four synthetic worlds through the REAL executor entrypoint.

WHAT MAKES THIS DIFFERENT FROM THE EARLIER SUITE. The earlier synthetic suite called the
executor's mathematical helpers directly. This one launches `stage4_executor_v1.py
--synthetic-world <NAME>` as a subprocess and lets it do everything a real run would do:
resolve the shards, join metacells to donors, unpack the availability bitmaps, apply the
eligibility funnel, compute the frozen statistic, build the 14-term basis, cross-fit the
ridge by promoter, pair the arms, aggregate under all three weightings, bootstrap over
donors and write the result file. The only difference from a real run is the bytes.

HOW IT IS SCORED. Each world's prediction was written into its WORLD_MANIFEST.json when
the world was BUILT, before the pipeline could run against it. This harness reads the
prediction back out of the manifest rather than restating it, so the comparison is against
something recorded in advance. Where a numeric threshold is needed and the manifest gives
only a direction, the threshold is labelled POST_HOC in the receipt. A post-hoc threshold
that pretends to be prospective is worse than no threshold.

NOT EVERY WORLD IS SUPPOSED TO PASS. HIDDEN_CONFOUND is built to defeat the method, and
the correct outcome is that it does. It is scored as a LIMIT, and the limit is reported as
part of what a real Stage-4 number will mean.

No real substrate, no raw matrix and no protected outcome is read.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nihcard_exact_supplement_builder_v1 as B                      # noqa: E402

EXEC = "scripts/v64/stage4_executor_v1.py"
ROOT = "D:/jepa_v5_outputs_20260925/v64_stage4_synthetic"
OUT = os.path.join(ROOT, "_results")
WORLDS = ("BIOLOGY_POSITIVE", "TRUE_NULL", "MEASURED_TECHNICAL", "HIDDEN_CONFOUND")
PRIMARY = "GENE_BALANCED"
FINDINGS = []


def rec(section, name, expectation, observed, verdict):
    FINDINGS.append(dict(section=section, check=name, expectation=expectation,
                         observed=observed, verdict=verdict))
    print("  [%s] %-4s %-52s %s" % (section, verdict, name, observed))


def run_world(world):
    r = subprocess.run([sys.executable, EXEC, "--synthetic-world", world],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit("world %s failed to run:\n%s" % (world, r.stdout + r.stderr))
    p = os.path.join(OUT, "V64_STAGE4_RESULT_%s.json" % world)
    return json.load(open(p)), B.sha_file(p)


def main() -> int:
    results, digests = {}, {}
    print("running four synthetic worlds through the real executor entrypoint ...")
    for w in WORLDS:
        results[w], digests[w] = run_world(w)
    print("")

    # ------------------------------------------------- 1 the four decisive worlds
    for w in WORLDS:
        R = results[w]
        man = R["world_manifest"]
        pred = man["planted_truth"]["expect"]
        adj = R["ADJUSTED"][PRIMARY]
        raw = R["RAW_UNADJUSTED_GENE_BALANCED"]
        d, lcb, rawd = adj["delta"], adj["lcb95"], raw["delta"]
        obs = "delta=%+.4f lcb95=%+.4f raw=%+.4f" % (d, lcb, rawd)

        if w == "BIOLOGY_POSITIVE":
            ok = d > 0 and lcb > 0
            rec("worlds", "BIOLOGY_POSITIVE: planted biology is recovered",
                pred, obs, "PASS" if ok else "FAIL")
        elif w == "TRUE_NULL":
            ok = lcb <= 0
            rec("worlds", "TRUE_NULL: nothing planted, nothing claimed",
                pred, obs, "PASS" if ok else "FAIL")
        elif w == "MEASURED_TECHNICAL":
            removed = 1.0 - abs(d) / abs(rawd) if rawd else float("nan")
            ok = abs(d) < abs(rawd)
            rec("worlds", "MEASURED_TECHNICAL: the adjustment acts on depth",
                pred, obs + " removed=%.1f%%" % (100 * removed),
                "PASS" if ok else "FAIL")
            # the part that matters more than the headline
            residual_significant = lcb > 0
            rec("worlds",
                "MEASURED_TECHNICAL: residue after adjustment still excludes zero",
                "a purely technical world should ideally end with LCB95 <= 0",
                "lcb95=%+.4f -> %s" % (lcb, "YES, residue is significant"
                                       if residual_significant else "no"),
                "LIMIT" if residual_significant else "PASS")
        elif w == "HIDDEN_CONFOUND":
            fooled = lcb > 0
            ref = results["BIOLOGY_POSITIVE"]["ADJUSTED"][PRIMARY]["delta"]
            rec("worlds", "HIDDEN_CONFOUND: the method cannot see it",
                pred, obs + " = %.0f%% of the genuine-biology delta" % (100 * d / ref),
                "LIMIT" if fooled else "PASS")

    # ------------------------------------------- 2 the vectorised statistic is honest
    for w in WORLDS:
        cc = results[w]["_scalar_crosscheck"]
        rec("pipeline", "%s: fast statistic agrees with the qualified scalar one" % w,
            "all sampled cells agree in value and in status",
            "%d/%d values, %d/%d statuses, worst diff %.2e"
            % (cc["values_agreeing"], cc["sampled"], cc["statuses_agreeing"],
               cc["sampled"], cc["worst_absolute_difference"]),
            "PASS" if cc["agrees"] else "FAIL")

    # ------------------------------------------------------- 3 missingness semantics
    R = results["BIOLOGY_POSITIVE"]
    f = R["funnel"]
    planted = R["world_manifest"]["planted_missingness"]
    rec("missingness", "every planted missingness class appears in the funnel",
        "structurally unmeasured, measured-zero coverage and zero variance are "
        "separate counts and none is a zero value",
        "unmeasured->%d insufficient, %d rna-zero-coverage, %d atac-zero-coverage, "
        "%d rna-zero-variance, %d atac-zero-variance"
        % (f["MISSING_INSUFFICIENT_METACELLS"], f["MISSING_RNA_ZERO_COVERAGE"],
           f["MISSING_ATAC_ZERO_COVERAGE"], f["MISSING_RNA_ZERO_VARIANCE"],
           f["MISSING_ATAC_ZERO_VARIANCE"]),
        "PASS" if (f["MISSING_RNA_ZERO_COVERAGE"] > 0
                   and f["MISSING_ATAC_ZERO_VARIANCE"] + f["MISSING_RNA_ZERO_VARIANCE"] > 0
                   and f["MISSING_INSUFFICIENT_METACELLS"] > 0) else "FAIL")
    rec("missingness", "a missing cell is never carried as a numeric zero",
        "the funnel sums to donors x pairs and MEASURED excludes every missing class",
        "funnel total=%d, measured=%d" % (sum(f.values()), f["MEASURED"]),
        "PASS" if sum(f.values()) == R["eligibility"]["donors_eligible"]
        * R["eligibility"]["pairs_total"] else "FAIL")

    # ------------------------------------------------------------- 4 the funnel
    e = R["eligibility"]
    rec("funnel", "donor eligibility drops exactly the donors it should",
        "donors below 100 microglia or 4 metacells are dropped and named",
        "%d of %d donors eligible; %d dropped with reasons"
        % (e["donors_eligible"], e["donors_total"], e["donors_dropped"]),
        "PASS" if e["donors_dropped"] > 0 and e["donors_eligible"]
        == R["world_manifest"]["geometry"]["eligible_donors"] else "FAIL")

    # ------------------------------------------------------------ 5 weightings
    R1 = results["BIOLOGY_POSITIVE"]
    allw = R1["ADJUSTED"]
    rec("weighting", "all three weightings are computed and the primary is fixed",
        "GENE_BALANCED primary, PROMOTER_EQUAL companion, EDGE_EQUAL sensitivity; "
        "never chosen by which is largest",
        "primary=%s %+.4f | companion %+.4f | sensitivity %+.4f"
        % (R1["primary_weighting"], allw["GENE_BALANCED"]["delta"],
           allw["PROMOTER_EQUAL"]["delta"], allw["EDGE_EQUAL"]["delta"]),
        "PASS" if (len(allw) == 3 and R1["primary_weighting"] == PRIMARY) else "FAIL")

    # ------------------------------------------------------------- 6 Control B
    rec("controlB", "Control B is labelled null-and-calibration-only",
        "it appears only as a calibration arm and never as the primary contrast",
        "role=%s delta=%+.4f over %d edges"
        % (R1["CONTROL_A_VS_CONTROL_B"]["role"],
           R1["CONTROL_A_VS_CONTROL_B"]["delta"],
           R1["CONTROL_A_VS_CONTROL_B"]["edges"]),
        "PASS" if R1["CONTROL_A_VS_CONTROL_B"]["role"] == "NULL_AND_CALIBRATION_ONLY"
        else "FAIL")
    rec("controlB", "control-versus-control is near zero in the biology world",
        "an anti-false-green arm: two controls should not differ",
        "%+.4f against a linked-vs-control delta of %+.4f"
        % (R1["CONTROL_A_VS_CONTROL_B"]["delta"], allw[PRIMARY]["delta"]),
        "PASS" if abs(R1["CONTROL_A_VS_CONTROL_B"]["delta"])
        < 0.1 * abs(allw[PRIMARY]["delta"]) else "FAIL")

    # ------------------------------------------------------- 7 bootstrap reproducibility
    again, _ = run_world("BIOLOGY_POSITIVE")
    same = again["ADJUSTED"] == R1["ADJUSTED"]
    rec("bootstrap", "the same seed reproduces the interval exactly",
        "4000 replicates, seed 20260929, donors as the only resampling unit",
        "identical=%s (%d replicates)" % (same, R1["bootstrap"]["replicates"]),
        "PASS" if same else "FAIL")

    # ---------------------------------------------- 8 corrupted worlds must stop
    bad_root = os.path.join(ROOT, "_corrupt")
    src = os.path.join(ROOT, "TRUE_NULL")

    def corrupt(name, fn):
        dst = os.path.join(bad_root, name)
        if os.path.exists(dst):
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
        fn(dst)
        # Re-bind the manifest to the corrupted bytes. Without this every corruption test
        # trips the digest gate first and the SEMANTIC gate it claims to test is never
        # reached -- a check that passes for the wrong reason.
        mp = os.path.join(dst, "WORLD_MANIFEST.json")
        man = json.load(open(mp))
        for fname in list(man["digests"]):
            fp = os.path.join(dst, fname)
            if os.path.exists(fp):
                man["digests"][fname] = B.sha_file(fp)
        with open(mp, "w", newline=chr(10)) as fh:
            json.dump(man, fh, indent=2)
        # the executor only accepts the four fixed world names, so the corrupted copy is
        # swapped into a real world slot inside a scratch directory and run from there
        live = os.path.join(ROOT, "TRUE_NULL")
        keep = os.path.join(bad_root, "_keep_" + name)
        shutil.move(live, keep)
        shutil.move(dst, live)
        try:
            r = subprocess.run([sys.executable, EXEC, "--synthetic-world", "TRUE_NULL"],
                               capture_output=True, text=True)
            msg = [l for l in (r.stdout + r.stderr).splitlines()
                   if "Stop" in l or "STOP" in l]
            return r.returncode, (msg[-1][:140] if msg else
                                  (r.stdout + r.stderr).strip()[-140:])
        finally:
            shutil.move(live, dst)
            shutil.move(keep, live)
            shutil.rmtree(dst, ignore_errors=True)

    def break_pair_mapping(d):
        import numpy as _np
        p = os.path.join(d, "PHASE_B_SUBSTRATE_s00.npz")
        z = dict(_np.load(p, allow_pickle=True))
        z["pair_gene"] = _np.array(["NO_SUCH_GENE"] * len(z["pair_gene"]), dtype="<U15")
        _np.savez(p, **z)

    code, msg = corrupt("pairmap", break_pair_mapping)
    rec("corruption", "a corrupted gene mapping stops the run",
        "fail closed, not a silently wrong number", "exit=%d | %s" % (code, msg),
        "PASS" if code != 0 else "FAIL")

    def transpose_availability(d):
        import numpy as _np
        p = os.path.join(d, "PHASE_B_T3_T4_AVAILABILITY.npz")
        z = dict(_np.load(p, allow_pickle=True))
        z["t3_shape"] = z["t3_shape"][::-1].copy()
        _np.savez(p, **z)

    code, msg = corrupt("axes", transpose_availability)
    rec("corruption", "a transposed availability axis stops the run",
        "fail closed", "exit=%d | %s" % (code, msg), "PASS" if code != 0 else "FAIL")

    def tamper_without_updating_manifest(d):
        import numpy as _np
        p = os.path.join(d, "PHASE_B_SUBSTRATE_s01.npz")
        z = dict(_np.load(p, allow_pickle=True))
        z["t3_value"] = z["t3_value"] * 1.0001
        _np.savez(p, **z)

    dst = os.path.join(bad_root, "nodigest")
    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    tamper_without_updating_manifest(dst)
    live = os.path.join(ROOT, "TRUE_NULL")
    keep = os.path.join(bad_root, "_keep_nodigest")
    shutil.move(live, keep)
    shutil.move(dst, live)
    try:
        r = subprocess.run([sys.executable, EXEC, "--synthetic-world", "TRUE_NULL"],
                           capture_output=True, text=True)
        m = [l for l in (r.stdout + r.stderr).splitlines() if "STOP" in l]
        code, msg = r.returncode, (m[-1][:140] if m else "")
    finally:
        shutil.move(live, dst)
        shutil.move(keep, live)
        shutil.rmtree(dst, ignore_errors=True)
    rec("corruption", "edited bytes whose manifest was NOT updated stop on the digest",
        "fail closed", "exit=%d | %s" % (code, msg),
        "PASS" if code != 0 and "manifest digest" in msg else "FAIL")
    shutil.rmtree(bad_root, ignore_errors=True)

    # ------------------------------------- 9 synthetic mode cannot reach real bytes
    r = subprocess.run([sys.executable, EXEC, "--synthetic-world",
                        "../v64_phase_b"], capture_output=True, text=True)
    rec("firewall", "synthetic mode refuses a path-shaped world name",
        "the world list is fixed, so a traversal is not even expressible",
        "exit=%d" % r.returncode, "PASS" if r.returncode != 0 else "FAIL")

    real_shard = "D:/jepa_v5_outputs_20260925/v64_phase_b/PHASE_B_SUBSTRATE_s00.npz"
    dst = os.path.join(ROOT, "TRUE_NULL")
    keep = os.path.join(ROOT, "_keep_real")
    if os.path.exists(keep):
        shutil.rmtree(keep)
    shutil.copytree(dst, keep)
    try:
        man = json.load(open(os.path.join(dst, "WORLD_MANIFEST.json")))
        man["digests"]["PHASE_B_SUBSTRATE_s00.npz"] = B.sha_file(real_shard)
        with open(os.path.join(dst, "WORLD_MANIFEST.json"), "w", newline="\n") as fh:
            json.dump(man, fh, indent=2)
        shutil.copy2(real_shard, os.path.join(dst, "PHASE_B_SUBSTRATE_s00.npz"))
        r = subprocess.run([sys.executable, EXEC, "--synthetic-world", "TRUE_NULL"],
                           capture_output=True, text=True)
        txt = r.stdout + r.stderr
        refused = r.returncode != 0 and "REAL measurement bytes" in txt
        rec("firewall", "synthetic mode refuses real measurement bytes placed inside it",
            "even with a matching manifest digest, a real input is refused",
            "exit=%d refused_by_name=%s" % (r.returncode, refused),
            "PASS" if refused else "FAIL")
    finally:
        shutil.rmtree(dst)
        shutil.move(keep, dst)

    # ------------------------------------------------------------------ receipt
    verdicts = [f["verdict"] for f in FINDINGS]
    failed = [f for f in FINDINGS if f["verdict"] == "FAIL"]
    limits = [f for f in FINDINGS if f["verdict"] == "LIMIT"]
    summary = {w: dict(
        adjusted_delta=results[w]["ADJUSTED"][PRIMARY]["delta"],
        lcb95=results[w]["ADJUSTED"][PRIMARY]["lcb95"],
        raw_delta=results[w]["RAW_UNADJUSTED_GENE_BALANCED"]["delta"],
        control_vs_control=results[w]["CONTROL_A_VS_CONTROL_B"]["delta"],
        result_sha256=digests[w],
        prediction_recorded_before_the_run=results[w]["world_manifest"]
        ["planted_truth"]["expect"]) for w in WORLDS}

    out = dict(
        schema="V64_STAGE4_END_TO_END_WORLDS_V1", date="2026-10-01",
        what_this_qualifies="the whole orchestration, through the real entrypoint, not "
                            "the mathematical helpers in isolation",
        scale="reduced: 60 eligible donors, 11 metacells each, 200 edges. The real "
              "substrate is 282 donors, 3,231 metacells and 13,175 edges. Ratios are "
              "matched; absolute size is not, and nothing here qualifies real-scale "
              "runtime or memory.",
        thresholds_note="directional predictions come from each world manifest, written "
                        "when the world was built. Any numeric cut used to score them is "
                        "POST_HOC and is marked as such.",
        worlds=summary,
        n_checks=len(FINDINGS), n_pass=verdicts.count("PASS"),
        n_fail=len(failed), n_limit=len(limits),
        KNOWN_INTERPRETATION_LIMITS=[
            dict(limit="an unmeasured factor that varies BETWEEN metacells of the same "
                       "donor and loads on both modalities is indistinguishable from "
                       "biology under the frozen design",
                 evidence="HIDDEN_CONFOUND reaches delta %+.4f with LCB95 %+.4f, which "
                          "is %.0f%% of the genuine-biology world"
                          % (summary["HIDDEN_CONFOUND"]["adjusted_delta"],
                             summary["HIDDEN_CONFOUND"]["lcb95"],
                             100 * summary["HIDDEN_CONFOUND"]["adjusted_delta"]
                             / summary["BIOLOGY_POSITIVE"]["adjusted_delta"]),
                 what_bounds_it="only rna_depth_sensitivity and atac_depth_sensitivity "
                                "in the frozen 14-term basis. A cross-modal technical "
                                "factor orthogonal to depth survives untouched.",
                 consequence="a positive Stage-4 result is evidence of cross-modal "
                             "co-variation within donors, NOT by itself evidence of "
                             "regulatory causation."),
            dict(limit="the nuisance adjustment removes most, but not all, of a purely "
                       "technical depth effect",
                 evidence="MEASURED_TECHNICAL raw %+.4f -> adjusted %+.4f, and the "
                          "adjusted LCB95 is %+.4f"
                          % (summary["MEASURED_TECHNICAL"]["raw_delta"],
                             summary["MEASURED_TECHNICAL"]["adjusted_delta"],
                             summary["MEASURED_TECHNICAL"]["lcb95"]),
                 consequence="LCB95 > 0 alone does not establish that a real result is "
                             "non-technical. The size of the effect must be read against "
                             "this residue, not against zero.")],
        checks=FINDINGS,
        producer_sha256=B.sha_file(os.path.abspath(__file__)),
        executor_sha256=B.sha_file(EXEC),
        real_substrate_read=False, raw_matrix_opened=False,
        status="PASS" if not failed else "FAIL")
    p = "results/v64/phase_b_design/V64_STAGE4_END_TO_END_WORLDS_V1.json"
    with open(p, "w", newline="\n") as fh:
        json.dump(out, fh, indent=2)
    print("")
    print("%d checks: %d PASS, %d LIMIT (expected), %d FAIL -> %s"
          % (len(FINDINGS), verdicts.count("PASS"), len(limits), len(failed),
             out["status"]))
    print("receipt sha256 " + B.sha_file(p))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
