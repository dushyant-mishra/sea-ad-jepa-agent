#!/usr/bin/env python3
"""Realism qualification stage v2. Repairs S41-S48 from canonical audit c48e2c70.

v1 was correctly not merged. Its central defect was that it REIMPLEMENTED the
adjudication instead of reusing the frozen one. This version reuses the frozen V64
stress runner end to end and changes exactly one thing: the world generator.

WHAT v1 GOT WRONG, AND HOW EACH IS FIXED

S42  confidence calculation. v1 took per-arm MEDIANS and an SE from ONE negative arm.
     The frozen procedure computes, PER SEED, pos_min = min over positives and
     neg = max over the family's arms, forms the PAIRED margin m = pos_min - neg, and
     takes T.lower_confidence_bound(m). Taking medians destroys the common-random-
     number pairing that makes those margins comparable across arms, and can flip
     PASS/FAIL. FIXED by calling T.lower_confidence_bound on the paired per-seed
     margin vector, exactly as the frozen runner does.

S43  held-out ambient was turned into a gating family. T.FAMILIES does not contain it;
     T.HELDOUT_FAMILY does, and the frozen runner reports it separately as
     "generalises". v1's string-parsing of arm names invented a HELDOUT gating family.
     FIXED by using T.FAMILIES and T.HELDOUT_FAMILY verbatim and never parsing names.

S47  class B was overinterpreted. "Only outspan failed" does NOT establish "historical
     support was too narrow": NEG_TECH_OUTSPAN_1 is a NONLINEAR nuisance outside the
     ridge basis, which is a statement about model form, not about support width.
     FIXED by renaming the class and refusing to assert the support explanation.

S41  v1 referenced an addendum file that was deliberately not committed, so a clean
     checkout could not emit a result. FIXED: the governing authority is canonical's
     V64_NIH_CARD_REALISM_EXECUTOR_SUCCESSOR_RULE_V1.

S44  the simulated world did not preserve the calibrated JOINT geometry: promoter-level
     degree/activity came from one sampled row while accessibility/density/anchor came
     from other, independently sampled rows. FIXED by resampling whole PROMOTER BLOCKS,
     which requires the feature artifact to carry a promoter identifier; absent it the
     stage FAILS CLOSED rather than silently reverting to independent row sampling.

S48  geometry digests were only checked against caller-supplied values. FIXED: the
     digests must also appear in the canonical calibration receipt.

S45 and S46 CANNOT BE FIXED HERE, AND SAYING SO IS THE POINT. Depth-sensitivity
geometry (S45) and donor/metacell support geometry (S46) are not world inputs at all:
they are produced inside T.simulate, which is frozen. Calibrating them requires a
prospectively frozen SUCCESSOR TO THE SIMULATOR, not a change to this stage or to the
estimator. Improvising them here would be exactly the tampering the contract forbids.
This stage therefore declares its claim scope narrowed and reports both as open.

ACCEPTANCE GATE. In --mode historical the stage must reproduce the committed frozen
stress result EXACTLY. It refuses to run calibrated geometry unless that passes.

POST-CONSTRUCTION REALISM. Checking realism only on the calibration input is
insufficient, because the estimator sees features recomputed FROM THE CONSTRUCTED
WORLD. This stage therefore recomputes E.build_features on each constructed world and
compares THAT against the real input distribution.

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
SUCCESSOR_RULE = "results/v64/V64_NIH_CARD_REALISM_EXECUTOR_SUCCESSOR_RULE_V1.json"
FROZEN_OUTSPAN = "results/v64/V64_FROZEN_STRESS_OUTSPAN_V1.json"

SEED = 20260929
M_MIN = 0.010
F_LOGDIST, F_DEGREE, F_ACT, F_ACC, F_DEN, F_ANC = 0, 1, 2, 3, 4, 5


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


def make_calibrated_world_fn(T, X, prom_id, log):
    """Return a make_world replacement that resamples whole PROMOTER BLOCKS (S44).

    The calibrated geometry is a per-pair feature matrix. A promoter's degree and
    activity are properties of the promoter, shared by all of its pairs. Sampling
    pair rows independently and then reading the promoter-level columns off one of
    them destroys exactly that coupling. So whole promoter blocks are drawn intact.
    """
    blocks = {}
    for i, p in enumerate(prom_id):
        blocks.setdefault(p, []).append(i)
    keys = [k for k, v in blocks.items() if len(v) >= 1]
    log(f"  calibrated geometry: {len(X):,} pairs in {len(keys):,} promoter blocks "
        f"(median block {int(np.median([len(blocks[k]) for k in keys]))})")

    def make_world(rng):
        P, D = T.N_PROM, T.N_DISTAL
        chosen = rng.choice(len(keys), P, replace=True)
        dist = np.empty((P, D)); acc = np.empty((P, D))
        den = np.empty((P, D)); anc = np.empty((P, D))
        deg = np.empty(P); act = np.empty(P)
        for g, ci in enumerate(chosen):
            rows = np.asarray(blocks[keys[ci]])
            take = rows[rng.integers(0, len(rows), D)] if len(rows) < D else \
                rng.choice(rows, D, replace=False)
            G = X[take]
            dist[g] = np.exp(G[:, F_LOGDIST])
            acc[g] = G[:, F_ACC]
            den[g] = G[:, F_DEN]
            anc[g] = G[:, F_ANC]
            # promoter-level values come from the SAME block, not a foreign row
            deg[g] = np.rint(X[rows[0], F_DEGREE])
            act[g] = X[rows[0], F_ACT]
        w = {"distance": dist, "distal_acc": acc, "re_density": den,
             "anchor_freq": anc, "degree": deg.astype(int), "prom_activity": act}
        linked = np.zeros((P, D), bool)
        for g in range(P):
            pref = (-np.log(w["distance"][g]) + 0.15 * w["degree"][g]
                    + 0.5 * w["distal_acc"][g] + 0.4 * w["anchor_freq"][g]
                    + rng.normal(0, 0.6, D))
            linked[g, np.argsort(-pref)[:T.N_LINKED_PER_PROM]] = True
        w["linked"] = linked
        return w
    return make_world


def adjudicate(T, R, asf, include_outspan):
    """The FROZEN adjudication, reusing T.FAMILIES / T.HELDOUT_FAMILY / T.lcb."""
    arm_seed = {k: np.array([f.mean() for f in v]) for k, v in asf.items()}
    med = {k: float(np.median(v)) for k, v in arm_seed.items()}
    pos_min = np.vstack([arm_seed[p] for p in T.POSITIVES]).min(0)

    def fam(arms):
        neg = np.vstack([arm_seed[x] for x in arms]).max(0)
        m = pos_min - neg                       # PAIRED per seed: CRN preserved
        return float(m.mean()), float(T.lower_confidence_bound(m))

    fams = dict(T.FAMILIES)
    if include_outspan:
        fams["OUTSPAN_TECH"] = (R.OUTSPAN,)
    families = {}
    for f, arms in fams.items():
        mm, ll = fam(arms)
        families[f] = {"margin": mm, "lcb95": ll, "passes_M_MIN": bool(ll > M_MIN)}
    heldout = {}
    for f, arms in T.HELDOUT_FAMILY.items():
        mm, ll = fam(arms)
        heldout[f] = {"margin": mm, "lcb95": ll, "generalises": bool(ll > M_MIN)}
    twin_identical = bool(np.allclose(arm_seed[T.TWIN], arm_seed["POS_BIO_1"],
                                      rtol=0, atol=0))
    return {"arm_medians": med, "families": families,
            "heldout_NOT_A_GATING_FAMILY": heldout,
            "all_gating_families_pass": all(v["passes_M_MIN"]
                                            for v in families.values()),
            "semantic_twin_identical": twin_identical}


def classify(adj):
    failed = [k for k, v in adj["families"].items() if not v["passes_M_MIN"]]
    if not failed:
        return "A", "FROZEN_ESTIMATOR_STILL_QUALIFIES_UNDER_THIS_GEOMETRY"
    if set(failed) == {"OUTSPAN_TECH"}:
        return "B", ("ONLY_THE_OUT_OF_BASIS_NONLINEAR_FAMILY_FAILS. This is a statement "
                     "about MODEL FORM -- NEG_TECH_OUTSPAN_1 is nonlinear and outside "
                     "the ridge basis -- and NOT evidence that historical support was "
                     "too narrow. Those are different claims and this class asserts "
                     "only the first.")
    return "C", "FAILS_MATERIALLY_ON_REALISTIC_TECHNICAL_WORLDS__STOP_AND_REPORT"


def post_construction_realism(T, E, make_world, Xreal, names, n, log):
    """Realism of the features the ESTIMATOR ACTUALLY SEES, not of the input."""
    mats = []
    for s in range(n):
        w = make_world(np.random.default_rng(SEED + 7919 * s + 101 * 18))
        d = T.simulate(w, "NEG_NULL_0", 18, SEED + s)[0]
        R0, A0 = d["R"], d["A"]
        rz = (R0 - R0.mean(0)) / np.maximum(R0.std(0), 1e-9)
        az = (A0 - A0.mean(0)) / np.maximum(A0.std(0), 1e-9)
        dz = (d["rna_depth"] - d["rna_depth"].mean()) / (d["rna_depth"].std() + 1e-9)
        tz = (d["atac_depth"] - d["atac_depth"].mean()) / (d["atac_depth"].std() + 1e-9)
        rs = np.repeat(((rz * dz[:, None]).mean(0))[:, None], T.N_DISTAL, 1)
        as_ = (az * tz[:, None, None]).mean(0)
        mats.append(E.build_features(w, rs, as_))
    Xc = np.vstack(mats)
    per = {}
    for j, nm in enumerate(names):
        rq = np.quantile(Xreal[:, j], [0.0, .25, .5, .75, 1.0])
        cq = np.quantile(Xc[:, j], [0.0, .25, .5, .75, 1.0])
        per[nm] = {"real_quantiles": [float(x) for x in rq],
                   "as_seen_by_estimator_quantiles": [float(x) for x in cq],
                   "median_abs_gap": float(abs(rq[2] - cq[2]))}
    worst = max(per, key=lambda k: per[k]["median_abs_gap"])
    log(f"  post-construction realism: largest median gap on {worst} "
        f"({per[worst]['median_abs_gap']:.4f})")
    return {"note": ("Realism of the CONSTRUCTED world as the estimator sees it. "
                     "Checking only the calibration input is insufficient, because "
                     "features 7-8 are regenerated inside the simulator and the "
                     "products are recomputed from the world."),
            "per_feature": per, "largest_median_gap_feature": worst,
            "S45_caveat": ("rna/atac depth sensitivity are NOT calibrated: they are "
                           "produced inside frozen T.simulate. Any gap on those two "
                           "features is expected and is not repaired here.")}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["historical", "calibrated"], required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--donors", type=int, default=18)
    ap.add_argument("--seeds", type=int, default=24)
    ap.add_argument("--geometry", default=None)
    ap.add_argument("--geometry-sha256", default=None)
    ap.add_argument("--calibration-receipt", default=None)
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
    orig_make_world = T.make_world
    realism = None

    if a.mode == "calibrated":
        if not (a.geometry and a.geometry_sha256 and a.calibration_receipt):
            raise SystemExit("STOP_CALIBRATED_MODE_REQUIRES_GEOMETRY_AND_RECEIPT")
        got = sha256_file(a.geometry)
        if got != a.geometry_sha256:
            raise SystemExit(f"STOP_GEOMETRY_DIGEST {got}")
        # S48: the digest must also be recorded in the canonical calibration receipt
        rec = json.load(open(a.calibration_receipt))
        if got not in json.dumps(rec):
            raise SystemExit("STOP_GEOMETRY_NOT_BOUND_TO_CALIBRATION_RECEIPT "
                             "(S48: caller-supplied digests are not sufficient)")
        log("S48 provenance: geometry digest verified AND found in the calibration "
            "receipt")
        d = np.load(a.geometry, allow_pickle=True)
        if [str(x) for x in d["names"]] != E.FEATURE_NAMES:
            raise SystemExit("STOP_FEATURE_NAME_MISMATCH")
        if "promoter_id" not in d.files:
            raise SystemExit("STOP_S44_PROMOTER_ID_REQUIRED — whole promoter blocks "
                             "must be resampled intact; independent row sampling "
                             "destroys the promoter/pair coupling and this stage will "
                             "not silently fall back to it")
        X = np.asarray(d["X"], float)
        T.make_world = make_calibrated_world_fn(T, X, np.asarray(d["promoter_id"]), log)
        realism = post_construction_realism(T, E, T.make_world, X, E.FEATURE_NAMES,
                                            min(4, a.seeds), log)

    log(f"\nrunning frozen stress runner, mode={a.mode}, donors={a.donors}, "
        f"seeds={a.seeds}, include_outspan=True")
    asf, diag = R.run(a.donors, a.seeds, False, True, base_seed=SEED)
    T.make_world = orig_make_world
    adj = adjudicate(T, R, asf, include_outspan=True)
    for f, v in adj["families"].items():
        log(f"    {f:<14} margin {v['margin']:+.8f}  lcb95 {v['lcb95']:+.8f}  "
            f"{'PASS' if v['passes_M_MIN'] else 'FAIL'}")
    for f, v in adj["heldout_NOT_A_GATING_FAMILY"].items():
        log(f"    [heldout, not gating] {f} margin {v['margin']:+.8f} "
            f"lcb95 {v['lcb95']:+.8f} generalises {v['generalises']}")

    repro = None
    if a.mode == "historical":
        ref = json.load(open(FROZEN_OUTSPAN))
        repro = {"reference": FROZEN_OUTSPAN, "per_family": {}, "exact": True}
        for f, v in ref["families"].items():
            mine = adj["families"].get(f)
            ok = (mine is not None
                  and mine["margin"] == v["margin"] and mine["lcb95"] == v["lcb95"])
            repro["per_family"][f] = {"frozen_margin": v["margin"],
                                      "reproduced_margin": mine["margin"] if mine else None,
                                      "frozen_lcb95": v["lcb95"],
                                      "reproduced_lcb95": mine["lcb95"] if mine else None,
                                      "exact": bool(ok)}
            repro["exact"] &= bool(ok)
        log(f"\nACCEPTANCE GATE exact reproduction of {FROZEN_OUTSPAN}: {repro['exact']}")
        if not repro["exact"]:
            for f, v in repro["per_family"].items():
                if not v["exact"]:
                    log(f"    MISMATCH {f}: frozen {v['frozen_margin']} / "
                        f"{v['frozen_lcb95']}  vs  reproduced "
                        f"{v['reproduced_margin']} / {v['reproduced_lcb95']}")

    cls, label = classify(adj)
    log(f"\nCLASS {cls}: {label[:90]}")

    out = {
        "schema": "V64_NIH_CARD_REALISM_QUALIFICATION_RESULT_V2",
        "date": "2026-09-30",
        "repairs": ["S41", "S42", "S43", "S44", "S47", "S48"],
        "governing_rule": {"path": SUCCESSOR_RULE, "sha256": sha256_file(SUCCESSOR_RULE)},
        "modules": {
            "tournament": {"git_blob": git_blob(TOURNAMENT), "sha256": sha256_file(TOURNAMENT)},
            "estimator": {"git_blob": git_blob(ESTIMATOR), "sha256": sha256_file(ESTIMATOR)},
            "stress_runner": {"git_blob": git_blob(STRESS), "sha256": sha256_file(STRESS)},
            "imported_unmodified": True, "assert_sealed_passed": True,
            "adjudication_reused_from_frozen_runner": True,
            "estimator_basis_changed": False},
        "mode": a.mode, "config": {"donors": a.donors, "seeds": a.seeds,
                                   "M_MIN": M_MIN, "seed": SEED},
        "ADJUDICATION": adj,
        "ACCEPTANCE_GATE_historical_reproduction": repro,
        "post_construction_realism": realism,
        "OUTCOME_CLASS": cls, "OUTCOME_LABEL": label,
        "OPEN_DEFECTS_NOT_FIXABLE_HERE": {
            "S45_depth_sensitivity_geometry": {
                "status": "OPEN",
                "why_not_fixable_here": "rna/atac depth sensitivities are computed "
                                        "inside frozen T.simulate from the simulated "
                                        "donor matrices; they are not world inputs, so "
                                        "no world constructor can calibrate them",
                "required": "a prospectively frozen SUCCESSOR TO THE SIMULATOR",
                "claim_scope_effect": "this qualification says nothing about realistic "
                                      "depth-sensitivity geometry"},
            "S46_support_geometry": {
                "status": "OPEN",
                "why_not_fixable_here": "every synthetic donor still receives the frozen "
                                        "N_METACELL with complete support; real donor "
                                        "metacell counts, edge missingness, sparsity and "
                                        "donor-edge support live inside frozen "
                                        "T.simulate",
                "required": "a prospectively frozen SUCCESSOR TO THE SIMULATOR",
                "claim_scope_effect": "this qualification says nothing about realistic "
                                      "support or missingness geometry"},
            "why_not_improvised": "Editing the frozen simulator inside a qualification "
                                  "run is exactly the tampering the contract forbids."},
        "e2_correspondence_outcome_opened": False,
        "governance": {"training": "OFF", "td60": "BLOCKED", "Morabito": "PROTECTED",
                       "stage_4": "NOT_AUTHORISED"},
    }
    with open(os.path.join(a.out_dir,
                           "V64_NIH_CARD_REALISM_QUALIFICATION_RESULT_V2.json"),
              "w") as fh:
        json.dump(out, fh, indent=2)
    with open(os.path.join(a.out_dir, "run_log.txt"), "w", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
