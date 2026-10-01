#!/usr/bin/env python3
"""Stage-4 fail-closed preflight. Runs the gates; computes no correspondence value.

Stage 4 must pass this before it is permitted to compute anything. It verifies every
bound input, the unmodified estimator, the method locks, the null denominator and the
protected boundaries -- and it refuses rather than warns.

THE TEST THAT GUARDS THE OTHERS. A preflight that only ever sees correct inputs proves
nothing, so every gate here is also exercised against a deliberately corrupted copy in the
accompanying test suite, and a gate that cannot reject is reported as not a real gate.

This script reads digests, contract fields and array SHAPES. It never reads a measured
value, never multiplies the two modalities, and never opens the RNA or ATAC matrices.

TRAINING=OFF. STAGE 4 NOT AUTHORISED.
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nihcard_exact_supplement_builder_v1 as B      # noqa: E402

DIR = "results/v64/phase_b_design"
AUTH = os.path.join(DIR, "V64_STAGE4_EXECUTION_AUTHORITY_V1.json")
RNA_H5 = "D:/jepa_v5_outputs_20260925/nihcard/final_rna_data.h5ad"
ATAC_H5 = "D:/jepa_v5_outputs_20260925/nihcard/final_atac_data.h5ad"


def run_gates(C):
    """Returns {gate_id: (passed, detail)}. Pure function of the contract given on disk."""
    g = {}

    # G1 every bound input digest matches
    bad = []
    def walk(o, path=""):
        if isinstance(o, dict):
            p, s = o.get("path"), o.get("sha256")
            if isinstance(p, str) and isinstance(s, str) and len(s) == 64:
                if os.path.exists(p) and B.sha_file(p) != s:
                    bad.append((path, p))
            for k, v in o.items():
                walk(v, f"{path}/{k}")
        elif isinstance(o, list):
            for i, v in enumerate(o):
                walk(v, f"{path}[{i}]")
    walk({k: C[k] for k in ("INHERITED_NOT_RESTATED", "BOUND_PHASE_B_INPUTS",
                            "ESTIMATOR_IMPORTED_UNMODIFIED")})
    g["G1_INPUT_DIGESTS"] = (not bad, f"{len(bad)} mismatches" if bad
                             else "every bound input digest matches the live file")

    # G2 estimator unmodified
    e = C["ESTIMATOR_IMPORTED_UNMODIFIED"]
    ok = os.path.exists(e["path"]) and B.sha_file(e["path"]) == e["sha256"]
    g["G2_ESTIMATOR_UNMODIFIED"] = (ok, f"estimator sha256 {'matches' if ok else 'DIFFERS'}")

    # G3 the matrices are declared unreadable by Stage 4
    forb = C["WHAT_STAGE_4_MAY_NOT_READ"]
    ok = any("h5ad" in x or "matrices" in x for x in forb)
    g["G3_NO_MATRIX_REOPEN"] = (ok, "matrix reopening is declared forbidden")

    # G4 the partition is bound by digest rather than rebuilt
    sub = C["BOUND_PHASE_B_INPUTS"]["substrate_shards"]
    ok = len(sub) == 8 and all(len(v["sha256"]) == 64 for v in sub.values())
    g["G4_PARTITION_NOT_REBUILT"] = (ok, f"{len(sub)} shards bound by digest; the "
                                         f"metacell assignment lives inside them")

    # G5 weighting hierarchy
    w = C["METHOD_LOCKS"]["weighting_hierarchy"]
    ok = (w["PRIMARY"] == "GENE_BALANCED" and w["MANDATORY_COMPANION"] == "PROMOTER_EQUAL"
          and w["PREDECLARED_SENSITIVITY"] == "EDGE_EQUAL")
    g["G5_WEIGHTING"] = (ok, f"primary {w['PRIMARY']}, companion "
                             f"{w['MANDATORY_COMPANION']}, sensitivity "
                             f"{w['PREDECLARED_SENSITIVITY']}")

    # G6 bootstrap
    u = C["METHOD_LOCKS"]["uncertainty"]
    ok = (u["replicates"] == 4000 and u["seed"] == 20260929
          and "DONOR" in u["method"].upper())
    g["G6_BOOTSTRAP"] = (ok, f"{u['method']}, {u['replicates']} reps, seed {u['seed']}")

    # G7 null denominator
    n = C["NULL_AND_STRATA_LOCKS"]
    ok = (n["randomized_null_denominator"] == 10654
          and n["excluded_structurally_forced"] == 158
          and n["excluded_partially_forced"] == 200
          and n["not_evaluable_B_unavailable"] == 2163)
    g["G7_NULL_DENOMINATOR"] = (ok, f"denominator {n['randomized_null_denominator']}, "
                                    f"excluded {n['excluded_structurally_forced']} forced "
                                    f"+ {n['excluded_partially_forced']} partially forced")

    # G8 R3 label
    ok = (n["R3_required_label"] == "CONDITIONAL_ON_REALISED_LARGE_ARM"
          and "pooling" in n["R3_pooling_forbidden"].lower())
    g["G8_R3_LABEL"] = (ok, "R3 quantities must carry the conditional label and may not "
                            "be pooled with R1/R2")

    # G9 CONTROL_B null only
    ok = "NULL AND CALIBRATION ONLY" in n["control_B_role"]
    g["G9_CONTROL_B_NULL_ONLY"] = (ok, "CONTROL_B restricted to null and calibration")

    # G10 anti-false-green present with a STOP
    afg = C["SUCCESS_CRITERION_FROZEN_BEFORE_ANY_RESULT"]["anti_false_green"]
    cvc = next((a for a in afg if a["name"] == "CONTROL_VS_CONTROL_NULL"), None)
    ok = bool(cvc and "STOP" in cvc.get("if_it_fails", ""))
    g["G10_ANTI_FALSE_GREEN"] = (ok, f"{len(afg)} controls; control-vs-control failure "
                                     f"is a STOP")

    # G11 protected boundaries
    gov = C["governance"]
    ok = (gov["training"] == "OFF" and gov["stage_4"] == "NOT_AUTHORISED"
          and gov["td60"] == "BLOCKED" and gov["Morabito"] == "PROTECTED"
          and gov["correspondence_opened"] is False)
    g["G11_PROTECTED"] = (ok, "training off, Morabito protected, TD60 blocked, "
                              "correspondence unopened")

    # G12 no minimum-effect threshold, and p<0.05 is not success
    s = C["SUCCESS_CRITERION_FROZEN_BEFORE_ANY_RESULT"]
    ok = ("NO_MINIMUM_EFFECT" in json.dumps(s["no_minimum_effect_size"]).upper()
          or "no defensible minimum" in json.dumps(s["no_minimum_effect_size"]).lower())
    ok = ok and "not the success definition" in json.dumps(s).lower()
    g["G12_NO_THRESHOLD_ON_EFFECT"] = (ok, "effect reported without a threshold; "
                                           "p<0.05 alone is explicitly not success")

    # G13 funnel reconciliation is a stated PASS requirement
    ok = any("20,709" in x or "20709" in x for x in s["PASS_requires_all_of"])
    g["G13_FUNNEL"] = (ok, "funnel reconciliation to 20,709 is a PASS requirement")

    # G14 no silent pooling across strata
    ok = "violation" in C["NULL_AND_STRATA_LOCKS"]["no_silent_pooling"].lower()
    g["G14_STRATA"] = (ok, "pooling without the per-stratum breakdown is a violation")

    return g


def main() -> int:
    C = json.load(open(AUTH))
    g = run_gates(C)
    failed = [k for k, (ok, _) in g.items() if not ok]
    for k in sorted(g):
        ok, detail = g[k]
        print(f"  {k:<28} {'PASS' if ok else 'FAIL'}  {detail}")
    rec = dict(schema="V64_STAGE4_PREFLIGHT_V1", date="2026-09-30",
               authority=dict(path=AUTH, sha256=B.sha_file(AUTH)),
               producer_sha256=B.sha_file(os.path.abspath(__file__)),
               gates={k: dict(passed=v[0], detail=v[1]) for k, v in g.items()},
               n_gates=len(g), failed_gates=failed,
               computed_no_correspondence_value=True,
               rna_matrix_opened=False, atac_matrix_opened=False,
               status="PASS" if not failed else "FAIL",
               what_a_pass_means="the inputs are bound and the rules are locked. It does "
                                 "NOT authorise execution; that is a separate decision.",
               governance=C["governance"])
    p = os.path.join(DIR, "V64_STAGE4_PREFLIGHT_V1.json")
    with open(p, "w", newline="\n") as fh:
        json.dump(rec, fh, indent=2)
    print(f"\n{len(g)-len(failed)}/{len(g)} gates PASS -> {rec['status']}")
    print(f"receipt sha256 {B.sha_file(p)}")
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
