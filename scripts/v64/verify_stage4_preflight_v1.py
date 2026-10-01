#!/usr/bin/env python3
"""Stage-4 fail-closed preflight. Runs the gates; computes no correspondence value.

EXIT CODE SEMANTICS, AND WHY THEY CHANGED (S72). The previous version printed
"EXECUTION AUTHORITY: NOT_GRANTABLE" and then returned 0 whenever the design gates
passed. A caller writing the obvious thing --

    python verify_stage4_preflight_v1.py && python execute_stage4.py

-- would have proceeded straight into execution. A human-readable warning that the shell
cannot see is not a gate. The default mode is now EXECUTION, which returns nonzero while
any execution prerequisite is unsatisfied. A design-only audit is still available, but it
has to be asked for by name:

    --mode execution   (default)  nonzero unless design gates pass AND execution
                                  prerequisites are satisfied
    --mode design                 nonzero unless the design gates pass; says loudly that
                                  it is NOT an execution authorisation

THREE OTHER FAIL-OPEN REPAIRS.
  S73  a required binding that is DELETED from the contract used to give the walker less
       to walk while every remaining digest still matched, so an input could vanish
       unnoticed. Presence of every key in the frozen REQUIRED_BINDINGS manifest is now
       checked before any digest work.
  S74  the blob gate asked only whether a string looked like a hash, so forty zeros would
       have passed. Every repo-resident input's stored blob is now recomputed with
       git rev-parse and required to be equal.
  S75  the contract listed 14 gates while the verifier implemented 16. A verifier and its
       authority with separate rule sets is the thing this project exists to prevent, so
       G0 compares the two sets in both directions.

This script reads digests, contract fields and git metadata. It never reads a measured
value, never multiplies the two modalities, and never opens the RNA or ATAC matrices.

TRAINING=OFF. STAGE 4 NOT AUTHORISED.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nihcard_exact_supplement_builder_v1 as B      # noqa: E402

DIR = "results/v64/phase_b_design"
AUTH = os.path.join(DIR, "V64_STAGE4_EXECUTION_AUTHORITY_V1.json").replace("\\", "/")

IMPLEMENTED_GATES = [
    "G0_GATE_REGISTRY_AGREES", "G1a_REQUIRED_BINDINGS_PRESENT", "G1_INPUT_DIGESTS",
    "G1b_REPO_INPUTS_GIT_BLOB_IDENTITY", "G2_ESTIMATOR_UNMODIFIED",
    "G3_NO_MATRIX_REOPEN", "G4_PARTITION_NOT_REBUILT", "G5_WEIGHTING", "G6_BOOTSTRAP",
    "G7_NULL_DENOMINATOR", "G8_R3_LABEL", "G9_CONTROL_B_NULL_ONLY",
    "G10_ANTI_FALSE_GREEN", "G11_PROTECTED", "G12_NO_THRESHOLD_ON_EFFECT",
    "G13_FUNNEL", "G14_STRATA", "G15_PERMUTATION_COROBORATION",
]


def head_blob(path):
    r = subprocess.run(["git", "rev-parse", f"HEAD:{path}"], capture_output=True,
                       text=True)
    o = r.stdout.strip()
    return o if (r.returncode == 0 and len(o) == 40
                 and all(c in "0123456789abcdef" for c in o)) else None


def dig(c, dotted):
    cur = c
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


def run_gates(C):
    """Returns {gate_id: (passed, detail)}. Pure function of the contract handed in."""
    g = {}

    # G0 the contract's declared gate set must equal what this verifier implements (S75)
    declared = {x["id"] for x in C.get("FAIL_CLOSED_GATES", [])}
    impl = set(IMPLEMENTED_GATES)
    only_c, only_v = sorted(declared - impl), sorted(impl - declared)
    g["G0_GATE_REGISTRY_AGREES"] = (
        not only_c and not only_v,
        f"declared {len(declared)} / implemented {len(impl)}"
        + (f"; only-in-contract {only_c}; only-in-verifier {only_v}"
           if (only_c or only_v) else "; sets agree in both directions"))

    # G1a every required binding must EXIST before any digest work (S73)
    req = C.get("REQUIRED_BINDINGS", {})
    keys = req.get("keys", [])
    absent = [k for k in keys if dig(C, k) is None]
    shards = C.get("BOUND_PHASE_B_INPUTS", {}).get("substrate_shards", {})
    need_sh = req.get("substrate_shards_required", 0)
    sh_ok = len(shards) == need_sh
    g["G1a_REQUIRED_BINDINGS_PRESENT"] = (
        bool(keys) and not absent and sh_ok,
        f"{len(keys) - len(absent)}/{len(keys)} required bindings present, "
        f"{len(shards)}/{need_sh} shard slots filled"
        + (f"; ABSENT {absent}" if absent else ""))

    # G1 every bound input must exist and its digest must match (S68)
    mismatched, missing, checked = [], [], 0

    def walk(o, path=""):
        nonlocal checked
        if isinstance(o, dict):
            p_, s_ = o.get("path"), o.get("sha256")
            if isinstance(p_, str) and isinstance(s_, str) and len(s_) == 64:
                checked += 1
                if not os.path.exists(p_):
                    missing.append(p_)
                elif B.sha_file(p_) != s_:
                    mismatched.append(p_)
            for k, v in o.items():
                walk(v, f"{path}/{k}")
        elif isinstance(o, list):
            for i, v in enumerate(o):
                walk(v, f"{path}[{i}]")

    walk({k: C[k] for k in ("INHERITED_NOT_RESTATED", "BOUND_PHASE_B_INPUTS",
                            "ESTIMATOR_IMPORTED_UNMODIFIED") if k in C})
    ok = not mismatched and not missing and checked > 0
    g["G1_INPUT_DIGESTS"] = (
        ok, f"all {checked} bound inputs exist and their digests match" if ok
        else f"{checked} checked; {len(missing)} MISSING, {len(mismatched)} mismatched")

    # G1b repo-resident blobs must EQUAL the live HEAD blob, not merely look like one (S74)
    wrong, nblob, repo_n = [], [], 0

    def walk_blob(o):
        nonlocal repo_n
        if isinstance(o, dict):
            if isinstance(o.get("path"), str) and "git_blob" in o and o.get(
                    "repo_resident"):
                repo_n += 1
                stored, live = o["git_blob"], head_blob(o["path"])
                if live is None:
                    nblob.append(o["path"])
                elif stored != live:
                    wrong.append((o["path"], stored, live))
            for v in o.values():
                walk_blob(v)
        elif isinstance(o, list):
            for v in o:
                walk_blob(v)

    walk_blob({k: C[k] for k in ("INHERITED_NOT_RESTATED", "BOUND_PHASE_B_INPUTS",
                                 "ESTIMATOR_IMPORTED_UNMODIFIED") if k in C})
    g["G1b_REPO_INPUTS_GIT_BLOB_IDENTITY"] = (
        not wrong and not nblob and repo_n > 0,
        f"all {repo_n} repo-resident blobs equal git rev-parse HEAD:<path>"
        if not wrong and not nblob else
        f"{repo_n} checked; {len(wrong)} WRONG blob, {len(nblob)} unresolvable")

    e = C.get("ESTIMATOR_IMPORTED_UNMODIFIED", {})
    ok = bool(e) and os.path.exists(e.get("path", "")) and B.sha_file(
        e["path"]) == e["sha256"]
    g["G2_ESTIMATOR_UNMODIFIED"] = (ok, f"estimator sha256 "
                                        f"{'matches' if ok else 'DIFFERS or absent'}")

    forb = C.get("WHAT_STAGE_4_MAY_NOT_READ", [])
    g["G3_NO_MATRIX_REOPEN"] = (any("h5ad" in x or "matrices" in x for x in forb),
                                "matrix reopening is declared forbidden")

    sub = C.get("BOUND_PHASE_B_INPUTS", {}).get("substrate_shards", {})
    g["G4_PARTITION_NOT_REBUILT"] = (
        len(sub) == 8 and all(len(v["sha256"]) == 64 for v in sub.values()),
        f"{len(sub)} shards bound by digest; the metacell assignment lives inside them")

    w = C["METHOD_LOCKS"]["weighting_hierarchy"]
    g["G5_WEIGHTING"] = (
        w["PRIMARY"] == "GENE_BALANCED" and w["MANDATORY_COMPANION"] == "PROMOTER_EQUAL"
        and w["PREDECLARED_SENSITIVITY"] == "EDGE_EQUAL",
        f"primary {w['PRIMARY']}, companion {w['MANDATORY_COMPANION']}, "
        f"sensitivity {w['PREDECLARED_SENSITIVITY']}")

    u = C["METHOD_LOCKS"]["uncertainty"]
    g["G6_BOOTSTRAP"] = (u["replicates"] == 4000 and u["seed"] == 20260929
                         and "DONOR" in u["method"].upper(),
                         f"{u['method']}, {u['replicates']} reps, seed {u['seed']}")

    n = C["NULL_AND_STRATA_LOCKS"]
    g["G7_NULL_DENOMINATOR"] = (
        n["randomized_null_denominator"] == 10654
        and n["excluded_structurally_forced"] == 158
        and n["excluded_partially_forced"] == 200
        and n["not_evaluable_B_unavailable"] == 2163,
        f"denominator {n['randomized_null_denominator']}, excluded "
        f"{n['excluded_structurally_forced']} forced + "
        f"{n['excluded_partially_forced']} partially forced")

    g["G8_R3_LABEL"] = (
        n["R3_required_label"] == "CONDITIONAL_ON_REALISED_LARGE_ARM"
        and "pooling" in n["R3_pooling_forbidden"].lower(),
        "R3 quantities must carry the conditional label and may not be pooled with R1/R2")

    g["G9_CONTROL_B_NULL_ONLY"] = ("NULL AND CALIBRATION ONLY" in n["control_B_role"],
                                   "CONTROL_B restricted to null and calibration")

    s = C["SUCCESS_CRITERION_FROZEN_BEFORE_ANY_RESULT"]
    afg = s["anti_false_green"]
    cvc = next((a for a in afg if a["name"] == "CONTROL_VS_CONTROL_NULL"), None)
    g["G10_ANTI_FALSE_GREEN"] = (bool(cvc and "STOP" in cvc.get("if_it_fails", "")),
                                 f"{len(afg)} controls; control-vs-control failure is a STOP")

    gov = C["governance"]
    g["G11_PROTECTED"] = (
        gov["training"] == "OFF" and gov["stage_4"] == "NOT_AUTHORISED"
        and gov["td60"] == "BLOCKED" and gov["Morabito"] == "PROTECTED"
        and gov["correspondence_opened"] is False,
        "training off, Morabito protected, TD60 blocked, correspondence unopened")

    # S76. The first version tested `"no_minimum_effect" in json.dumps(...)`, but that
    # substring is the FIELD NAME, which survives any change to the value: replacing the
    # block with "a minimum of 0.010 is imposed" still left the key present, so the gate
    # passed on its own violation. A gate that matches its own key cannot fail. It now
    # tests the rule's content inside that block, requiring each of the three statements
    # that together constitute the rule.
    nm = json.dumps(s.get("no_minimum_effect_size", {})).lower()
    needs = ["no defensible minimum effect can be derived",
             "reported without a threshold",
             "not the success definition"]
    have = [n for n in needs if n in nm]
    g["G12_NO_THRESHOLD_ON_EFFECT"] = (
        len(have) == len(needs),
        f"{len(have)}/{len(needs)} required statements present in the "
        f"no-minimum-effect block"
        + ("; effect reported without a threshold, p<0.05 alone explicitly not success"
           if len(have) == len(needs)
           else f"; MISSING {[n for n in needs if n not in nm]}"))

    g["G13_FUNNEL"] = (any("20,709" in x or "20709" in x
                           for x in s["PASS_requires_all_of"]),
                       "funnel reconciliation to 20,709 is a PASS requirement")

    g["G14_STRATA"] = ("violation" in n["no_silent_pooling"].lower(),
                       "pooling without the per-stratum breakdown is a violation")

    cor = C.get("CORROBORATIVE_PROVENANCE_NOT_A_STAGE4_INPUT", {})
    perm = cor.get("pairing_permutation")
    if not perm:
        g["G15_PERMUTATION_COROBORATION"] = (False, "permutation binding absent")
    elif not os.path.exists(perm["path"]):
        g["G15_PERMUTATION_COROBORATION"] = (False, f"missing: {perm['path']}")
    else:
        import numpy as _np
        fsha = hashlib.sha256(open(perm["path"], "rb").read()).hexdigest()
        csha = hashlib.sha256(_np.load(perm["path"]).tobytes()).hexdigest()
        okc, okf = csha == perm["array_content_sha256"], fsha == perm["npy_file_sha256"]
        g["G15_PERMUTATION_COROBORATION"] = (
            okc and okf,
            f"array-content {'matches' if okc else 'DIFFERS'}, "
            f"npy-file {'matches' if okf else 'DIFFERS'}; corroborative only")
    return g


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["execution", "design"], default="execution",
                    help="execution (default) fails while any execution prerequisite is "
                         "unsatisfied; design checks the design gates only")
    a = ap.parse_args()

    C = json.load(open(AUTH))
    g = run_gates(C)
    failed = [k for k, (ok, _) in g.items() if not ok]
    prereq = C.get("EXECUTION_PREREQUISITES_NOT_YET_SATISFIED", {})
    unsat = prereq.get("unsatisfied_prerequisites", [])
    grantable = (not failed) and (not unsat)

    for k in IMPLEMENTED_GATES:
        if k in g:
            ok, detail = g[k]
            print(f"  {k:<36} {'PASS' if ok else 'FAIL'}  {detail}")

    rec = dict(
        schema="V64_STAGE4_PREFLIGHT_V1", date="2026-10-01", mode=a.mode,
        authority=dict(path=AUTH, sha256=B.sha_file(AUTH)),
        producer_sha256=B.sha_file(os.path.abspath(__file__)),
        gates={k: dict(passed=v[0], detail=v[1]) for k, v in g.items()},
        n_gates=len(g), failed_gates=failed,
        design_gates_status="PASS" if not failed else "FAIL",
        EXECUTION_AUTHORITY="GRANTABLE" if grantable else "NOT_GRANTABLE",
        unsatisfied_execution_prerequisites=unsat,
        why_not_grantable=prereq.get("S71") if unsat else None,
        g3_limit=prereq.get("G3_LIMIT_STATED_HONESTLY"),
        exit_code_semantics=dict(
            mode=a.mode,
            execution="nonzero while any design gate fails OR any execution prerequisite "
                      "is unsatisfied, so `preflight && execute` cannot proceed",
            design="nonzero while any design gate fails; explicitly NOT an execution "
                   "authorisation"),
        computed_no_correspondence_value=True,
        rna_matrix_opened=False, atac_matrix_opened=False,
        status=("PASS" if (not failed and (a.mode == "design" or grantable))
                else "FAIL"),
        governance=C["governance"])
    p = os.path.join(DIR, "V64_STAGE4_PREFLIGHT_V1.json").replace("\\", "/")
    with open(p, "w", newline="\n") as fh:
        json.dump(rec, fh, indent=2)

    print("")
    print(f"{len(g)-len(failed)}/{len(g)} DESIGN gates "
          f"{'PASS' if not failed else 'FAIL'}")
    print(f"EXECUTION AUTHORITY: {rec['EXECUTION_AUTHORITY']}"
          + (f" ({len(unsat)} prerequisites unsatisfied)" if unsat else ""))
    for u in unsat:
        print(f"  unsatisfied: {u}")
    print(f"mode={a.mode}  receipt sha256 {B.sha_file(p)}")

    if a.mode == "execution":
        if failed or unsat:
            print("EXIT NONZERO: execution must not proceed")
            return 1
        return 0
    if failed:
        return 1
    print("design mode: this is NOT an execution authorisation")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
