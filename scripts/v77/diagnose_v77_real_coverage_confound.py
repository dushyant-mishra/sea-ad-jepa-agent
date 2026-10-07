#!/usr/bin/env python3
"""How much of the frozen REAL detection topology is produced by cohort coverage alone? (S149)

THE CONCERN. The real TRAIN cohort mixes cells measured on different address coverage. A gene
that one cohort's assay does not cover is zero in every cell of that cohort. If many envelope
genes share that structural zero, their detection patterns become correlated through cohort
membership alone, and the real envelope (fraction |corr| > 0.3, transitivity, degree, largest
community) would partly measure measurement coverage rather than biology. The synthetic
calibration experiments applied no structural support at all, so they were asked to reproduce,
through planted biology, whatever part of the real topology coverage creates.

WHAT THIS MEASURES, on the real envelope's OWN 3,000 genes (expression-variance selection, as
frozen), so every number is comparable with the frozen detection envelope:

  A  all cells, as frozen. Must reproduce the frozen point estimate, or nothing below is trusted.
  N  COVERAGE-ONLY NULL. Each cell keeps its own coverage stratum; each gene keeps its real
     detection rate within that stratum; within a stratum every gene is drawn independently.
     The null has the real marginals and the real structural zeros and NO biological dependence.
     Whatever topology it shows is produced by coverage and composition alone.
  S  each coverage stratum separately, where structural zeros are shared by every cell.
  G  all cells, restricted to envelope genes covered by all three cohorts.

A cell's coverage stratum is inferred from its own detections only (the smallest cohort
coverage containing all of them). No label, metadata or pathology field enters.

Real TRAIN access is pathology-blind, TRAIN-only and read-only, through load_real.
DIAGNOSTIC ONLY: no frozen envelope is changed, and no threshold is set from these numbers.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_v77_real_calibration as RC  # noqa: E402
import build_v77_calibration_envelope as ENV  # noqa: E402
import build_v77_topology_calibration as TC  # noqa: E402
import v77_address_universe as AU  # noqa: E402

EXECUTOR_FILES = ("diagnose_v77_real_coverage_confound.py", "build_v77_real_calibration.py",
                  "build_v77_calibration_envelope.py", "build_v77_topology_calibration.py",
                  "v77_address_universe.py")
STRATUM_ORDER = ("HVS", "NPH52", "SEA_AD")   # smallest coverage first
N_HVG = 3000
SEED = 20261006


def _git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True, cwd=HERE).stdout.strip()


def _require_committed_executors():
    head = _git("rev-parse", "HEAD")
    for f in EXECUTOR_FILES:
        rel = f"scripts/v77/{f}"
        if subprocess.run(["git", "ls-files", "--error-unmatch", rel], capture_output=True,
                          cwd=HERE.parents[1]).returncode != 0:
            sys.exit(f"refusing: {rel} is not tracked; a receipt must describe committed code")
        if subprocess.run(["git", "diff", "--quiet", "HEAD", "--", rel],
                          cwd=HERE.parents[1]).returncode != 0:
            sys.exit(f"refusing: {rel} differs from HEAD {head[:8]}")
    return head


def _stats(det, sel):
    s = ENV.stats_from_logmatrix(det.astype(np.float64), sel, N_HVG)
    keys = ("frac_abs_gt_0p3", "median_abs_corr", "transitivity", "mean_degree",
            "largest_community_frac", "pos_over_neg_ratio")
    return {k: float(s[k]) for k in keys}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--cache", default=str(RC.DEFAULT_CACHE),
                    help="real TRAIN cache; the default is the original (S174-affected) cache")
    ap.add_argument("--inputs-dir", default=str(HERE.parents[1] / "results" / "v77"),
                    help="where the detection envelope this run is checked against lives")
    a = ap.parse_args()
    head = _require_committed_executors()

    X, cls, don, src, dig = RC.load_real(Path(a.cache))
    X = X.tocsr(); n = X.shape[0]
    lib = np.asarray(X.sum(1)).ravel()
    gdet = np.asarray((X > 0).sum(0)).ravel() / n
    keep = np.where(gdet > 0.05)[0]
    _C, _hvg, _Ld, sel = TC.hvg_correlation(X, lib, keep, N_HVG)     # the frozen gene choice
    det = (np.asarray(X[:, keep].todense()) > 0)                       # cells x 19,569 bool
    uni = AU.AddressUniverse(7302)
    cov = {f: uni.source_support[AU.SOURCE_FAMILIES.index(f)][keep] for f in STRATUM_ORDER}

    # stratum = smallest cohort coverage containing every detection of the cell
    fits = {f: ~(det & ~cov[f][None, :]).any(1) for f in STRATUM_ORDER}
    stratum = np.full(n, "NONE", dtype=object)
    for f in reversed(STRATUM_ORDER):
        stratum[fits[f]] = f
    counts = {f: int((stratum == f).sum()) for f in (*STRATUM_ORDER, "NONE")}

    A = _stats(det, sel)

    rng = np.random.default_rng(SEED)
    null = np.zeros_like(det)
    for f in STRATUM_ORDER:
        m = stratum == f
        if m.any():
            p = det[m].mean(0)
            null[m] = rng.random((int(m.sum()), det.shape[1])) < p[None, :]
    N = _stats(null, sel)

    S = {}
    for f in STRATUM_ORDER:
        m = stratum == f
        if m.sum() >= 200:
            S[f] = dict(n_cells=int(m.sum()), **_stats(det[m], sel))

    all3 = cov["HVS"] & cov["NPH52"] & cov["SEA_AD"]
    sel_all3 = np.array([j for j in sel if all3[j]])
    G = dict(n_genes=int(len(sel_all3)),
             **{k: v for k, v in ENV.stats_from_logmatrix(det.astype(np.float64), sel_all3,
                                                          len(sel_all3)).items()
                if k in ("frac_abs_gt_0p3", "median_abs_corr", "transitivity", "mean_degree",
                         "largest_community_frac", "pos_over_neg_ratio")})

    frozen = json.loads((Path(a.inputs_dir) /
                         "V77_REAL_DETECTION_ENVELOPE_V1.json").read_text())["ACCEPTANCE_ENVELOPES"]
    reproduces = all(abs(A[k] - frozen[k]["point"]) < 1e-9 for k in A if k in frozen)

    rec = dict(
        schema="V77_REAL_COVERAGE_CONFOUND_DIAGNOSTIC_V1",
        claim_class="V77_SYNTHETIC_WORLD_QUALIFICATION",
        status="DIAGNOSTIC_ONLY__NO_ENVELOPE_CHANGED__NO_THRESHOLD_SET",
        question="how much of the frozen real detection topology does cohort coverage alone produce?",
        source=dict(cache=str(a.cache), n_shards=len(dig), shard_digests=dig,
                    pathology_blind=True, train_only=True, read_only=True),
        envelope_genes=dict(rule="frozen: expression-variance selection on TRAIN_PREVALENCE05_19569",
                            n=int(len(sel))),
        coverage_strata=dict(
            rule="smallest cohort coverage containing every detection of the cell",
            cells=counts,
            universe_genes_outside_coverage={f: int((~cov[f]).sum()) for f in STRATUM_ORDER},
            envelope_genes_outside_coverage={f: int((~cov[f][sel]).sum()) for f in STRATUM_ORDER}),
        A_all_cells_as_frozen=A,
        A_reproduces_frozen_point_estimate=reproduces,
        N_coverage_only_null=N,
        N_construction=("per-stratum real per-gene detection rates, independent draws within a "
                        f"stratum, seed {SEED}; real marginals and structural zeros, no dependence"),
        S_within_single_coverage_stratum=S,
        G_all_cells_genes_covered_by_all_three_cohorts=G,
        frozen_detection_envelope_points={k: frozen[k]["point"] for k in A if k in frozen},
        command=(f"python scripts/v77/diagnose_v77_real_coverage_confound.py --out {a.out} --cache {a.cache} "
                 f"--inputs-dir {a.inputs_dir}"),
        source_commit=head,
        provenance_status="CLEAN_COMMITTED_HEAD__EXECUTORS_TRACKED_AND_UNMODIFIED",
        executor_sha256={f: hashlib.sha256((HERE / f).read_bytes()).hexdigest() for f in EXECUTOR_FILES},
        no_training_performed=True)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    with open(a.out, "w", newline="\n") as fh:
        fh.write(json.dumps(rec, indent=2) + "\n")
    print("cells by coverage stratum:", counts, "| A reproduces frozen:", reproduces)
    print("%-36s %8s %8s %8s %8s" % ("", "frac>.3", "trans", "degree", "largest"))
    rows = [("A all cells (frozen)", A), ("N coverage-only null", N)]
    rows += [(f"S within {f} ({v['n_cells']} cells)", v) for f, v in S.items()]
    rows += [(f"G all-cohort genes ({G['n_genes']})", G)]
    for name, r in rows:
        print("%-36s %8.4f %8.4f %8.1f %8.4f" % (name, r["frac_abs_gt_0p3"], r["transitivity"],
                                                r["mean_degree"], r["largest_community_frac"]))


if __name__ == "__main__":
    main()
