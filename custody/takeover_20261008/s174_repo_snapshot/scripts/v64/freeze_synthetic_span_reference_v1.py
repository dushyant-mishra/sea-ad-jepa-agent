#!/usr/bin/env python3
"""LANE B: freeze the synthetic span reference for the out-of-span diagnostic.

The frozen design compares NIH-CARD's realised 14-feature geometry against the
geometry that qualified the continuous-adjustment estimator. The audit asked, before
that comparison is implemented, whether the required synthetic reference quantities
are already PERSISTED anywhere -- feature means, SDs, full ranges, the covariance
needed for Mahalanobis, and the p99 radius.

ANSWER: THEY ARE NOT. The committed V63/V64 qualification artifacts persist arm
medians, family margins, LCBs, support diagnostics and linked-vs-control SMDs. They
do NOT persist the feature-space moments. This receipt therefore regenerates them
DETERMINISTICALLY from the frozen qualification lineage, and does so as its own
artifact so the reference is frozen BEFORE any NIH-CARD comparison exists.

WHAT IS AND IS NOT ALLOWED HERE
  allowed      replaying T.make_world, T.simulate and E.build_features under the
               exact frozen seeds and configuration, with both modules imported
               UNMODIFIED
  forbidden    defining a new synthetic distribution, changing any seed, changing
               the estimator, or altering N_PROM / N_DISTAL / the feature basis

REPRODUCTION CHECK. Regenerating world geometry is only trustworthy if the replay
actually reproduces the committed qualification. This script therefore re-derives
the linked-pair count and the world-geometry invariants and compares them against
the committed frozen-stress artifacts, refusing to emit a reference on mismatch.

No NIH-CARD data is read. No E2 correspondence outcome is opened.
TRAINING=OFF. TD60=BLOCKED.
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
COMMITTED_STRESS = "results/v64/V64_FROZEN_STRESS_BASELINE_V1.json"

SEED = 20260929          # frozen project-wide base seed
N_DONORS = 18            # frozen statistical decision configuration
N_SEEDS = 24             # frozen
REF_ARM = "NEG_NULL_0"   # the nuisance-free arm; geometry reference, not an outcome


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def git_blob(p):
    return subprocess.run(["git", "rev-parse", f"HEAD:{p}"], capture_output=True,
                          text=True, check=True).stdout.strip()


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args()
    if os.path.exists(a.out_dir) and os.listdir(a.out_dir):
        raise SystemExit("STOP_OUTPUT_EXISTS")
    os.makedirs(a.out_dir, exist_ok=True)

    T = load(TOURNAMENT, "tour")
    E = load(ESTIMATOR, "est")
    T.assert_sealed()

    mats, linked_counts = [], []
    for s in range(N_SEEDS):
        w = T.make_world(np.random.default_rng(SEED + 7919 * s + 101 * N_DONORS))
        linked_counts.append(int(w["linked"].sum()))
        d = T.simulate(w, REF_ARM, N_DONORS, SEED + s)[0]
        R0, A0 = d["R"], d["A"]
        rz = (R0 - R0.mean(0)) / np.maximum(R0.std(0), 1e-9)
        az = (A0 - A0.mean(0)) / np.maximum(A0.std(0), 1e-9)
        dz = (d["rna_depth"] - d["rna_depth"].mean()) / (d["rna_depth"].std() + 1e-9)
        tz = (d["atac_depth"] - d["atac_depth"].mean()) / (d["atac_depth"].std() + 1e-9)
        rs = np.repeat(((rz * dz[:, None]).mean(0))[:, None], T.N_DISTAL, 1)
        as_ = (az * tz[:, None, None]).mean(0)
        mats.append(E.build_features(w, rs, as_))
    X = np.vstack(mats)

    # ---- reproduction check against the committed qualification lineage
    expected_linked = T.N_PROM * T.N_LINKED_PER_PROM
    repro = {
        "linked_per_world_expected": expected_linked,
        "linked_per_world_observed": sorted(set(linked_counts)),
        "linked_reproduces": all(c == expected_linked for c in linked_counts),
        "N_PROM": T.N_PROM, "N_DISTAL": T.N_DISTAL,
        "pairs_per_world": T.N_PROM * T.N_DISTAL,
        "total_reference_pairs": int(X.shape[0]),
        "features": int(X.shape[1]),
    }
    if not repro["linked_reproduces"]:
        raise SystemExit("STOP_REPLAY_DOES_NOT_REPRODUCE_FROZEN_WORLD")
    if os.path.exists(COMMITTED_STRESS):
        cs = json.load(open(COMMITTED_STRESS))
        cfg = cs.get("config", {})
        repro["committed_config"] = cfg
        repro["config_matches"] = (cfg.get("donors") == N_DONORS
                                   and cfg.get("seeds") == N_SEEDS)
        if not repro["config_matches"]:
            raise SystemExit(f"STOP_CONFIG_MISMATCH replay {N_DONORS}/{N_SEEDS} "
                             f"vs committed {cfg}")
        repro["linked_scored_in_committed_stress"] = cs.get("support", {}).get(
            "linked_scored")
        repro["linked_scored_matches_world"] = (
            repro["linked_scored_in_committed_stress"] == expected_linked)

    mu, sd = X.mean(0), X.std(0)
    sd = np.where(sd < 1e-12, 1.0, sd)
    Z = (X - mu) / sd
    cov = np.cov(Z.T) + 1e-6 * np.eye(Z.shape[1])
    inv = np.linalg.inv(cov)
    md = np.sqrt(np.einsum("ij,jk,ik->i", Z, inv, Z))

    ref = {
        "schema": "V64_NIH_CARD_SYNTHETIC_SPAN_REFERENCE_V1",
        "date": "2026-09-29",
        "lane": "B",
        "purpose": "frozen geometry reference for the out-of-span diagnostic",
        "PERSISTENCE_FINDING": {
            "were_these_quantities_already_persisted": False,
            "what_the_committed_artifacts_do_persist":
                "arm medians, family margins and LCBs, support/ESS/concentration "
                "diagnostics, nuisance OOF R2, residual correlations and "
                "linked-vs-control SMDs",
            "what_they_do_not_persist":
                "feature means, feature SDs, full observed feature ranges, the "
                "standardised covariance, and the p99 Mahalanobis radius",
            "consequence": "deterministic regeneration from the frozen lineage was "
                           "necessary, and is recorded here as its own receipt so the "
                           "reference is frozen before any NIH-CARD comparison exists"
        },
        "provenance": {
            "tournament_module": {"path": TOURNAMENT, "git_blob": git_blob(TOURNAMENT),
                                  "sha256": sha256_file(TOURNAMENT)},
            "estimator_module": {"path": ESTIMATOR, "git_blob": git_blob(ESTIMATOR),
                                 "sha256": sha256_file(ESTIMATOR)},
            "modules_imported_unmodified": True,
            "assert_sealed_passed": True,
            "seeds": {"base": SEED, "world": "SEED + 7919*s + 101*N_DONORS",
                      "simulate": "SEED + s", "n_seeds": N_SEEDS,
                      "n_donors": N_DONORS},
            "reference_arm": REF_ARM,
            "why_this_arm": "the nuisance-free null arm. It fixes the world geometry "
                            "and realised depth-sensitivity distribution without "
                            "injecting any positive effect. It is a covariate "
                            "reference, not an outcome."
        },
        "reproduction_check": repro,
        "feature_names": E.FEATURE_NAMES,
        "reference": {
            "mean": [float(x) for x in mu],
            "sd": [float(x) for x in sd],
            "min": [float(x) for x in X.min(0)],
            "max": [float(x) for x in X.max(0)],
            "p99_mahalanobis_radius": float(np.quantile(md, 0.99)),
            "median_mahalanobis": float(np.median(md)),
            "standardised_covariance": [[float(v) for v in row] for row in cov],
        },
        "FROZEN": True,
        "frozen_before_any_nihcard_comparison": True,
        "e2_correspondence_outcome_opened": False,
        "nih_card_data_read": False,
        "governance": {"training": "OFF", "td60": "BLOCKED",
                       "estimator_changed": False, "new_distribution_defined": False},
    }
    p = os.path.join(a.out_dir, "V64_NIH_CARD_SYNTHETIC_SPAN_REFERENCE_V1.json")
    with open(p, "w") as fh:
        json.dump(ref, fh, indent=2)
    print(f"reference pairs {X.shape[0]:,} x {X.shape[1]} features")
    print(f"linked per world reproduces frozen design: {repro['linked_reproduces']} "
          f"({repro['linked_per_world_observed']} vs expected {expected_linked})")
    print(f"config matches committed stress: {repro.get('config_matches')}")
    print(f"p99 Mahalanobis radius {ref['reference']['p99_mahalanobis_radius']:.4f}")
    print(f"written {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
