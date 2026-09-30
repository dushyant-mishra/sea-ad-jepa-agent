#!/usr/bin/env python3
"""Realism qualification stage v3. Repairs the three defects in v2 (audit 90a1288c).

DEFECT 1, THE SERIOUS ONE: THE WRONG WORLD.
v2 patched `T.make_world` on ITS OWN tournament instance, then called `R.run()`. But
the frozen stress runner does its own `_load("tour", ...)`, so `R.T` is a DIFFERENT
module object. Proven directly: `T is R.T` -> False, and after patching `T.make_world`
the runner still resolves `R.T.make_world` to the historical generator.

Consequence had it been run: the realism diagnostic would have described calibrated
worlds while the nuisance tournament silently used historical ones -- a very
convincing false green. v2's calibrated mode was never executed, so no such artifact
exists, but it was one command away.

v3 patches R.T.make_world -- the exact instance the runner resolves -- inside a
try/finally, and adds a POSITIVE CONTROL: the patched generator increments a counter,
and the run ABORTS unless the counter proves the patch was actually exercised once per
seed. A patch that silently fails to take is precisely the failure mode above, so the
guard has to be able to fail, and it is tested below.

DEFECT 2: THE "ACCEPTANCE GATE" WAS NOT A GATE.
v2 logged a reproduction mismatch and carried on, and calibrated mode did not require
any prior historical acceptance. v3 TERMINATES on mismatch, applies the tolerance
frozen at canonical 3406aa60 (1e-12 absolute, limited to reproducing historical family
margins/LCBs across numerical environments and permitted to alter nothing else), and
refuses calibrated mode without a historical-reproduction receipt that passed.

DEFECT 3: THE CALIBRATED INPUT CANNOT SATISFY THIS INTERFACE, AND RETROFITTING IS NOT
A FIX. The canonical calibration executor emits no promoter_id, and its receipt does
not carry the geometry NPZ digests. More fundamentally, the pair-level copula permutes
each feature column independently, so the promoter hierarchy is ALREADY DESTROYED;
grouping rows afterwards by old promoter IDs would assemble blocks whose values no
longer belong together and would manufacture a hierarchy rather than restore one.
v3 therefore REFUSES calibrated mode until a HIERARCHICALLY calibrated artifact exists,
per V64_NIH_CARD_HIERARCHICAL_CALIBRATION_SUCCESSOR_CONTRACT_V1. It does not accept a
retrofit.

S45 (depth-sensitivity realism) and S46 (donor/metacell support, sparsity, missingness)
remain OPEN and require a simulator successor. They are not absorbed here.

FIREWALL. Covariate geometry only. No E2 gene RNA is paired with its linked distal
ATAC. No Delta. TRAINING=OFF. TD60=BLOCKED.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import subprocess

import numpy as np

TOURNAMENT = "scripts/v63/e2_synthetic_identifiability_tournament_v2_1.py"
ESTIMATOR = "scripts/v63/e2_continuous_adjustment_estimator_v1.py"
STRESS = "scripts/v64/v64_frozen_stress_runner_v1.py"
FROZEN_OUTSPAN = "results/v64/V64_FROZEN_STRESS_OUTSPAN_V1.json"
TOLERANCE_AUTHORITY = "results/v64/V64_NIH_CARD_HISTORICAL_REPRODUCTION_TOLERANCE_V1.json"
HIER_CONTRACT = ("results/v64/"
                 "V64_NIH_CARD_HIERARCHICAL_CALIBRATION_SUCCESSOR_CONTRACT_V1.json")

SEED = 20260929
M_MIN = 0.010
NUMERIC_TOL = 1e-12          # frozen at canonical 3406aa60; reproduction only


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def git_blob(p):
    return subprocess.run(["git", "rev-parse", f"HEAD:{p}"], capture_output=True,
                          text=True, check=True).stdout.strip()


def load_mod(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def adjudicate(T, R, asf, include_outspan):
    """The FROZEN adjudication: per-seed paired margins, T.FAMILIES, T.lcb."""
    arm_seed = {k: np.array([f.mean() for f in v]) for k, v in asf.items()}
    med = {k: float(np.median(v)) for k, v in arm_seed.items()}
    pos_min = np.vstack([arm_seed[p] for p in T.POSITIVES]).min(0)

    def fam(arms):
        neg = np.vstack([arm_seed[x] for x in arms]).max(0)
        m = pos_min - neg
        return float(m.mean()), float(T.lower_confidence_bound(m))

    fams = dict(T.FAMILIES)
    if include_outspan:
        fams["OUTSPAN_TECH"] = (R.OUTSPAN,)
    families = {f: dict(zip(("margin", "lcb95"), fam(arms))) for f, arms in fams.items()}
    for f in families:
        families[f]["passes_M_MIN"] = bool(families[f]["lcb95"] > M_MIN)
    heldout = {}
    for f, arms in T.HELDOUT_FAMILY.items():
        mm, ll = fam(arms)
        heldout[f] = {"margin": mm, "lcb95": ll, "generalises": bool(ll > M_MIN)}
    return {"arm_medians": med, "families": families,
            "heldout_NOT_A_GATING_FAMILY": heldout,
            "all_gating_families_pass": all(v["passes_M_MIN"] for v in families.values()),
            "semantic_twin_identical": bool(np.allclose(arm_seed[T.TWIN],
                                                        arm_seed["POS_BIO_1"],
                                                        rtol=0, atol=0))}


def check_reproduction(adj, log):
    """TERMINATING gate against the committed frozen result, at the frozen tolerance."""
    ref = json.load(open(FROZEN_OUTSPAN))["families"]
    per, worst, ok = {}, 0.0, True
    for f, v in ref.items():
        mine = adj["families"].get(f)
        if mine is None:
            per[f] = {"present": False}
            ok = False
            continue
        dm = abs(mine["margin"] - v["margin"])
        dl = abs(mine["lcb95"] - v["lcb95"])
        worst = max(worst, dm, dl)
        within = bool(dm <= NUMERIC_TOL and dl <= NUMERIC_TOL)
        same = bool(mine["passes_M_MIN"] == v["passes_M_MIN"])
        ok &= within and same
        per[f] = {"abs_margin_delta": dm, "abs_lcb95_delta": dl,
                  "within_tolerance": within, "pass_fail_identical": same}
    log(f"  reproduction: worst delta {worst:.3e} against tolerance {NUMERIC_TOL:.0e} "
        f"-> {'PASS' if ok else 'FAIL'}")
    return {"reference": FROZEN_OUTSPAN, "tolerance": NUMERIC_TOL,
            "tolerance_authority": "canonical 3406aa60; reproduction of historical "
                                   "family margins/LCBs across numerical environments "
                                   "ONLY. It may not alter M_MIN, biological gates, "
                                   "q-safety, span thresholds or any estimator decision.",
            "worst_abs_delta": worst, "per_family": per, "PASS": bool(ok)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["historical", "calibrated"], required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--donors", type=int, default=18)
    ap.add_argument("--seeds", type=int, default=24)
    ap.add_argument("--hierarchical-geometry", default=None)
    ap.add_argument("--hierarchical-geometry-sha256", default=None)
    ap.add_argument("--historical-receipt", default=None,
                    help="receipt from a previously PASSED historical run")
    ap.add_argument("--selftest-patch", action="store_true",
                    help="install a COUNTING PASS-THROUGH generator on R.T.make_world "
                         "in historical mode. It returns the identical historical world, "
                         "so results must be unchanged, while proving the patch reaches "
                         "R.run and that the call-count guard can fail.")
    a = ap.parse_args()
    if os.path.exists(a.out_dir) and os.listdir(a.out_dir):
        raise SystemExit("STOP_OUTPUT_EXISTS")
    os.makedirs(a.out_dir, exist_ok=True)
    lines = []

    def log(m):
        print(m, flush=True)
        lines.append(m)

    T = load_mod(TOURNAMENT, "tour")
    E = load_mod(ESTIMATOR, "est")
    R = load_mod(STRESS, "stress")
    T.assert_sealed()
    log(f"module identity check: T is R.T -> {T is R.T} "
        f"(the runner loads its own instance; v3 patches R.T)")

    patch_state = {"calls": 0}
    calibrated_info = None
    historical_receipt_binding = None

    if a.mode == "calibrated":
        # DEFECT 2: calibrated mode requires a PASSED historical receipt
        if not a.historical_receipt:
            raise SystemExit("STOP_CALIBRATED_REQUIRES_HISTORICAL_RECEIPT")
        hr = json.load(open(a.historical_receipt))
        rep = hr.get("ACCEPTANCE_GATE_historical_reproduction") or {}
        if not rep.get("PASS"):
            raise SystemExit("STOP_HISTORICAL_RECEIPT_DID_NOT_PASS")
        if rep.get("tolerance") != NUMERIC_TOL:
            raise SystemExit("STOP_HISTORICAL_RECEIPT_TOLERANCE_MISMATCH")

        # Strong provenance binding: PASS+tolerance alone is not sufficient.
        pb = hr.get("provenance_binding") or {}
        expected_blobs = {
            "tournament_git_blob": git_blob(TOURNAMENT),
            "estimator_git_blob": git_blob(ESTIMATOR),
            "stress_runner_git_blob": git_blob(STRESS),
            "tolerance_authority_git_blob": git_blob(TOLERANCE_AUTHORITY),
        }
        for key, expected in expected_blobs.items():
            observed = pb.get(key)
            if observed != expected:
                raise SystemExit(
                    f"STOP_HISTORICAL_RECEIPT_PROVENANCE_MISMATCH {key}: "
                    f"observed={observed!r} expected={expected!r}"
                )
        if pb.get("tolerance_authority_path") != TOLERANCE_AUTHORITY:
            raise SystemExit("STOP_HISTORICAL_RECEIPT_TOLERANCE_AUTHORITY_PATH_MISMATCH")
        historical_receipt_binding = {"path": a.historical_receipt, "git_blob_bindings": expected_blobs}
        log(f"historical receipt accepted: worst delta {rep['worst_abs_delta']:.3e}; "
            "module and tolerance-authority provenance bindings verified")

        # DEFECT 3: refuse retrofitted pair-level geometry outright
        if not (a.hierarchical_geometry and a.hierarchical_geometry_sha256):
            raise SystemExit("STOP_CALIBRATED_REQUIRES_HIERARCHICAL_GEOMETRY")
        if not os.path.exists(HIER_CONTRACT):
            raise SystemExit(f"STOP_MISSING_HIERARCHICAL_CONTRACT {HIER_CONTRACT}")
        got = sha256_file(a.hierarchical_geometry)
        if got != a.hierarchical_geometry_sha256:
            raise SystemExit(f"STOP_GEOMETRY_DIGEST {got}")
        d = np.load(a.hierarchical_geometry, allow_pickle=True)
        need = {"X_promoter_level", "X_edge_level", "promoter_index", "names"}
        if not need.issubset(set(d.files)):
            raise SystemExit(
                "STOP_NOT_HIERARCHICALLY_CALIBRATED — this stage will NOT accept a "
                "pair-level copula artifact with promoter_id retrofitted. A pair-level "
                "copula permutes each column independently, so the promoter hierarchy "
                "is already destroyed and regrouping by old IDs would manufacture "
                f"structure rather than restore it. Required keys: {sorted(need)}")
        calibrated_info = {"path": a.hierarchical_geometry, "sha256": got,
                           "keys": sorted(d.files)}
        raise SystemExit("STOP_HIERARCHICAL_CALIBRATION_NOT_YET_PRODUCED — the interface "
                         "is defined and enforced, but no hierarchically calibrated "
                         "artifact exists yet. Produce one under the successor contract "
                         "first.")

    log(f"\nrunning frozen stress runner, mode={a.mode}, donors={a.donors}, "
        f"seeds={a.seeds}, include_outspan=True")
    orig = R.T.make_world
    try:
        if a.selftest_patch:
            def counting_passthrough(rng, _o=orig, _st=patch_state):
                _st["calls"] += 1
                return _o(rng)
            R.T.make_world = counting_passthrough
            log("  SELFTEST: counting pass-through installed on R.T.make_world")
        asf, diag = R.run(a.donors, a.seeds, False, True, base_seed=SEED)
    finally:
        R.T.make_world = orig          # always restore, even on failure
    if a.selftest_patch:
        log(f"  SELFTEST: patched generator called {patch_state['calls']} times, "
            f"expected {a.seeds}")
        if patch_state["calls"] != a.seeds:
            raise SystemExit("STOP_SELFTEST_PATCH_DID_NOT_REACH_RUNNER")

    # POSITIVE CONTROL for the patch mechanism, exercised in historical mode too so
    # the guard itself is proven able to fail rather than assumed to work.
    if a.mode == "calibrated" and patch_state["calls"] != a.seeds:
        raise SystemExit(f"STOP_FALSE_GREEN_GUARD patched generator was called "
                         f"{patch_state['calls']} times, expected {a.seeds}. The patch "
                         f"did not take, which is exactly the v2 defect.")

    adj = adjudicate(T, R, asf, include_outspan=True)
    for f, v in adj["families"].items():
        log(f"    {f:<14} margin {v['margin']:+.8f}  lcb95 {v['lcb95']:+.8f}  "
            f"{'PASS' if v['passes_M_MIN'] else 'FAIL'}")
    for f, v in adj["heldout_NOT_A_GATING_FAMILY"].items():
        log(f"    [heldout, not gating] {f} lcb95 {v['lcb95']:+.8f} "
            f"generalises {v['generalises']}")

    repro = None
    if a.mode == "historical":
        repro = check_reproduction(adj, log)

    out = {
        "schema": "V64_NIH_CARD_REALISM_QUALIFICATION_RESULT_V3",
        "date": "2026-09-30",
        "repairs_over_v2": {
            "wrong_world": "patches R.T.make_world (the runner's own instance) inside "
                           "try/finally, with a call-count positive control",
            "gate_was_not_a_gate": "reproduction mismatch now TERMINATES; calibrated "
                                   "mode requires a PASSED historical receipt",
            "retrofit_refused": "calibrated mode requires a hierarchically calibrated "
                                "artifact and rejects promoter_id retrofits"},
        "module_identity": {"T_is_R_T": bool(T is R.T),
                            "note": "the runner loads its own tournament instance; "
                                    "patching the caller's T does not reach it"},
        "modules": {
            "tournament": {"git_blob": git_blob(TOURNAMENT), "sha256": sha256_file(TOURNAMENT)},
            "estimator": {"git_blob": git_blob(ESTIMATOR), "sha256": sha256_file(ESTIMATOR)},
            "stress_runner": {"git_blob": git_blob(STRESS), "sha256": sha256_file(STRESS)},
            "imported_unmodified": True, "assert_sealed_passed": True,
            "adjudication_reused_from_frozen_runner": True},
        "mode": a.mode,
        "config": {"donors": a.donors, "seeds": a.seeds, "M_MIN": M_MIN, "seed": SEED},
        "ADJUDICATION": adj,
        "ACCEPTANCE_GATE_historical_reproduction": repro,
        "calibrated_geometry": calibrated_info,
        "historical_receipt_binding": historical_receipt_binding,
        "OPEN_NOT_FIXABLE_HERE": {
            "S45_depth_sensitivity_realism": "OPEN; requires a simulator successor",
            "S46_support_geometry_realism": "OPEN; requires a simulator successor",
            "rule": "neither may be absorbed into a claim that a world is NIH-CARD-like"},
        "historical_14D_span_verdict": "WITHDRAWN; valid statements are distance fully "
                                       "inside support and promoter degree mismatched "
                                       "at 24.29% outside",
        "e2_correspondence_outcome_opened": False,
        "governance": {"training": "OFF", "td60": "BLOCKED", "Morabito": "PROTECTED",
                       "stage_4": "NOT_AUTHORISED"},
    }
    with open(os.path.join(a.out_dir,
                           "V64_NIH_CARD_REALISM_QUALIFICATION_RESULT_V3.json"),
              "w") as fh:
        json.dump(out, fh, indent=2)
    with open(os.path.join(a.out_dir, "run_log.txt"), "w", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")
    if repro is not None and not repro["PASS"]:
        raise SystemExit("STOP_HISTORICAL_REPRODUCTION_FAILED — this is a terminating "
                         "gate, not a log line")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
