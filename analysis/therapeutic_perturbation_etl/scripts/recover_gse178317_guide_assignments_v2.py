#!/usr/bin/env python3
"""GSE178317 per-cell sgRNA assignment, v2: two stages and a background model.

v1 recovered the guide reads correctly and then assigned only 10 of 58,302
cells.  The read layer was not at fault: 174,012,015 of 221,434,278 spots
carried a library guide, 54,950 cells held at least one guide UMI, and all 81
guides appeared in every lane.  The calling rule was at fault.  It required the
top guide to hold 70 percent of a cell's guide UMIs, which is the wrong question
for this assay: these are sgRNA *enrichment* libraries built by hemi-nested PCR,
which amplifies ambient guide transcripts along with real ones, so a typical
cell carries about 354 guide UMIs spread across the whole 81-guide library and
nothing approaches a 70 percent share.  That rule was imported from GSE311359,
where direct guide capture gives much lower per-cell guide depth and it is
appropriate.

v2 changes two things.

**Stage separation.**  `--stage count` streams SRA once and persists the
cell x guide UMI matrix.  `--stage call` reads that matrix and assigns.  v1
conflated them, so testing any calling rule cost a 47 minute re-stream of the
whole archive.  A calling rule that cannot be re-run cannot be checked.

**A background model instead of a within-cell share.**  The GEO record states
the authors used demuxEM together with the z-score cutoff of Tian et al. 2019.
The distinction that matters is not the number but the question asked:

    within-cell share   "does guide g lead inside cell c?"
                        defeated by a uniform ambient background
    across-cell outlier "is guide g's level in cell c extreme compared with
                        what guide g looks like in cells that lack it?"
                        robust to a uniform ambient background

Because any one guide is carried by roughly one percent of cells, that guide's
distribution across all cells is dominated by ambient, and a robust centre and
spread estimate the background directly from the data.

Two differently motivated statistics are computed and agreement is required,
mirroring the authors' use of two methods:

  A. robust z-score of the cell fraction f = x / T against a median/MAD
     background fitted per guide;
  B. Poisson tail probability of x against an ambient expectation T * p_g,
     where p_g is guide g's share of all guide UMIs in the experiment.

A cell is assigned only when exactly one guide passes both, so multiplets and
ambiguous cells are reported unassigned rather than resolved by a tie-break.

Every threshold below is declared before the calling stage is run, and a
sensitivity grid is reported so the operating point's influence is visible.
Nothing here is tuned against the authors' published count of assigned cells.
"""

from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import json
import os
import subprocess
import sys
import time

import numpy as np

# ---------------------------------------------------------------------------
# Read layer.  Unchanged from v1, which was verified correct.
# ---------------------------------------------------------------------------
LEN_I7, LEN_CB_UMI, LEN_BIO = 8, 28, 91
SPOT_LEN = LEN_I7 + LEN_CB_UMI + LEN_BIO
LEN_CB = 16
SCAFFOLD = "GTTTAAGAGCTAAGCTGG"
ANCHOR5P = "CCACCTTGTT"
PROTOSPACER_LEN = 20

LANES = [
    {"lane": "L1", "srr": "SRR14828091", "gex_gsm": "GSM5387652",
     "gex_h5": "GSM5387652_iTF_Microglia_10X_Lane1_filtered_feature_bc_matrix.h5"},
    {"lane": "L2", "srr": "SRR14828092", "gex_gsm": "GSM5387653",
     "gex_h5": "GSM5387653_iTF_Microglia_10X_Lane2_filtered_feature_bc_matrix.h5"},
    {"lane": "L3", "srr": "SRR14828093", "gex_gsm": "GSM5387654",
     "gex_h5": "GSM5387654_iTF_Microglia_10X_Lane3_filtered_feature_bc_matrix.h5"},
    {"lane": "L4", "srr": "SRR14828094", "gex_gsm": "GSM5387655",
     "gex_h5": "GSM5387655_iTF_Microglia_10X_Lane4_filtered_feature_bc_matrix.h5"},
]

# ---------------------------------------------------------------------------
# Calling layer.  DECLARED BEFORE THE CALLING STAGE IS RUN.
#
# Z_THRESHOLD: a robust z of 5 is a stringent outlier criterion.  The rationale
#   is external to this dataset: about 4.7 million cell-by-guide cells are
#   tested (roughly 58,000 x 81), so a per-test level near 1e-8 is needed to
#   expect fewer than one false call family-wide, and on a Gaussian background
#   that is z of about 5.7.  Five is the round value just below it and the
#   Poisson agreement requirement tightens it further.  It is NOT set from the
#   authors' published count of assigned cells.
# POISSON_ALPHA: Bonferroni-corrected across all cell-by-guide tests.
# MIN_ASSIGNED_UMI: a floor so that no assignment rests on a trivial count.
# ---------------------------------------------------------------------------
Z_THRESHOLD = 5.0
POISSON_ALPHA = 0.01
MIN_ASSIGNED_UMI = 5
MIN_CELL_TOTAL_UMI = 10          # cells below this carry too little to judge

SENSITIVITY_Z = [3.0, 4.0, 5.0, 6.0, 8.0, 10.0]

# ---------------------------------------------------------------------------
# Usability verdict.  v1 exited 0 and wrote a file while assigning 10 of 58,302
# cells.  Its only guard was "refuse to write if there are no rows at all",
# which catches a literal zero and waves through a result that is empty in
# every way that matters.  A producer whose output cannot support the analysis
# it feeds must say so itself rather than rely on a reader noticing the number
# is small.
#
# The floor is derived from the downstream requirement, not from any published
# count of assigned cells: build_gse178317_intervention_effects_v1.py needs at
# least 10 cells per (lane, target) pseudobulk and at least 3 lanes before it
# reports a spread, so a target needs roughly 30 to 40 cells to contribute, and
# the study only earns a place in the collection if most of its targets do.
#
# Stated plainly because it bears on how much this pre-declaration is worth: a
# bounded smoke run over 0.27% of the reads had already been executed when these
# numbers were fixed, and it assigned 4,223 cells across 38 targets.  So the
# expectation was that the full run clears this bar comfortably.  The bar is set
# by what the analysis needs, but it was not set in ignorance of the data.
# ---------------------------------------------------------------------------
MIN_CELLS_PER_USABLE_TARGET = 40      # ~10 cells x 4 lanes
MIN_USABLE_TARGETS = 30               # of the 39 non-control targets
MIN_CELLS_PER_PAIRED_LANE = 10           # matched target and NTC within lane
MIN_PAIRED_LANES = 3                    # downstream spread needs >=3 lanes


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_library(path):
    lib = {}
    with open(path, newline="") as fh:
        for row in csv.DictReader(fh):
            ps = row["protospacer"].strip().upper()
            if len(ps) != PROTOSPACER_LEN or set(ps) - set("ACGT") or ps in lib:
                raise SystemExit("bad or duplicate protospacer: %r" % (row,))
            lib[ps] = (row["target_gene"].strip(), row["sgrna_name"].strip())
    if not lib:
        raise SystemExit("empty sgRNA library")
    return lib


def load_called_cells(h5_path):
    import h5py
    with h5py.File(h5_path, "r") as f:
        raw = [b.decode() for b in f["matrix"]["barcodes"][:]]
    cells = set(b.split("-")[0] for b in raw)
    if len(cells) != len(raw):
        raise SystemExit("barcode suffix collision in %s" % h5_path)
    return cells


# ---------------------------------------------------------------------------
# Stage 1: count
# ---------------------------------------------------------------------------
def stage_count(a):
    lib = load_library(a.library)
    guides = sorted({name for _, name in lib.values()})
    gidx = {g: i for i, g in enumerate(guides)}
    print("library: %d guides" % len(guides), flush=True)

    rows, lane_recs = [], []
    cell_ids, cell_lane = [], []
    counts_blocks = []

    for spec in LANES:
        h5 = os.path.join(a.gex_dir, spec["gex_h5"])
        cells = load_called_cells(h5)
        order = sorted(cells)
        cpos = {c: i for i, c in enumerate(order)}
        mat = np.zeros((len(order), len(guides)), dtype=np.int32)
        stat = collections.Counter()
        t0 = time.time()
        print("\n=== %s %s (%d called cells) ===" %
              (spec["lane"], spec["srr"], len(order)), flush=True)

        rng = ["-R", "1-%d" % a.max_spots] if a.max_spots else []
        dump = subprocess.Popen(
            [a.vdb_dump, spec["srr"]] + rng + ["-C", "READ", "-f", "tab"],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True,
            bufsize=1 << 20)
        triples = os.path.join(a.tmp_dir, "%s.triples" % spec["srr"])
        env = dict(os.environ, LC_ALL="C")
        srt = subprocess.Popen(
            ["sort", "-u", "-S", "2G", "-T", a.tmp_dir, "-o", triples],
            stdin=subprocess.PIPE, text=True, bufsize=1 << 20, env=env)
        w = srt.stdin.write

        for line in dump.stdout:
            s = line.rstrip("\n")
            if len(s) != SPOT_LEN:
                stat["spot_len_mismatch"] += 1
                continue
            stat["spots"] += 1
            cb = s[LEN_I7:LEN_I7 + LEN_CB]
            if cb not in cells:
                continue
            stat["reads_on_called_cells"] += 1
            bio = s[LEN_I7 + LEN_CB_UMI:]
            j = bio.find(SCAFFOLD)
            ps = bio[j - PROTOSPACER_LEN:j] if j >= PROTOSPACER_LEN else None
            if ps not in lib:
                i = bio.find(ANCHOR5P)
                cand = (bio[i + len(ANCHOR5P):i + len(ANCHOR5P) + PROTOSPACER_LEN]
                        if i >= 0 else None)
                ps = cand if cand in lib else None
            if ps in lib:
                stat["reads_with_guide"] += 1
                w("%s\t%s\t%s\n" % (cb, s[LEN_I7 + LEN_CB:LEN_I7 + LEN_CB_UMI],
                                    lib[ps][1]))
            else:
                stat["reads_no_guide_match"] += 1

        dump.stdout.close()
        if dump.wait() != 0:
            raise SystemExit("vdb-dump failed for %s" % spec["srr"])
        srt.stdin.close()
        if srt.wait() != 0:
            raise SystemExit("sort failed for %s" % spec["srr"])

        with open(triples) as fh:
            for line in fh:
                cb, _umi, g = line.rstrip("\n").split("\t")
                mat[cpos[cb], gidx[g]] += 1
                stat["guide_umis"] += 1
        os.remove(triples)

        counts_blocks.append(mat)
        cell_ids.extend("%s_%s" % (spec["lane"], c) for c in order)
        cell_lane.extend([spec["lane"]] * len(order))
        lane_recs.append({
            "lane": spec["lane"], "srr": spec["srr"], "gex_gsm": spec["gex_gsm"],
            "gex_h5_sha256": sha256_file(h5),
            "gex_called_cells": len(order),
            "spots_read": stat["spots"],
            "reads_on_called_cells": stat["reads_on_called_cells"],
            "reads_with_guide": stat["reads_with_guide"],
            "reads_no_guide_match": stat["reads_no_guide_match"],
            "guide_umis_after_dedup": stat["guide_umis"],
            "cells_with_any_guide_umi": int((mat.sum(axis=1) > 0).sum()),
            "distinct_guides_observed": int((mat.sum(axis=0) > 0).sum()),
            "elapsed_s": round(time.time() - t0, 1),
        })
        for k, v in lane_recs[-1].items():
            if k != "gex_h5_sha256":
                print("  %-30s %s" % (k, v))

    counts = np.vstack(counts_blocks)
    os.makedirs(a.out_dir, exist_ok=True)
    npz = os.path.join(a.out_dir, "gse178317_cell_guide_umi_counts_v2.npz")
    np.savez_compressed(
        npz,
        counts=counts,
        cell_ids=np.array(cell_ids, dtype=object),
        cell_lane=np.array(cell_lane, dtype=object),
        guides=np.array(guides, dtype=object),
        guide_target=np.array(
            [dict((n, t) for t, n in lib.values())[g] for g in guides],
            dtype=object),
    )
    with open(os.path.join(a.out_dir, "gse178317_count_stage_receipt_v2.json"),
              "w") as fh:
        json.dump({"schema": "GSE178317_GUIDE_COUNT_STAGE_V2",
                   "library_sha256": sha256_file(a.library),
                   "max_spots_per_lane": a.max_spots,
                   "lanes": lane_recs,
                   "matrix": {"cells": int(counts.shape[0]),
                              "guides": int(counts.shape[1]),
                              "total_umis": int(counts.sum()),
                              "npz_sha256": sha256_file(npz)}}, fh, indent=2)
    print("\nwrote %s  (%d cells x %d guides, %d UMIs)"
          % (npz, counts.shape[0], counts.shape[1], counts.sum()))
    return 0


# ---------------------------------------------------------------------------
# Stage 2: call
# ---------------------------------------------------------------------------
def robust_z(counts, totals):
    """Per-guide robust z of the cell fraction against a median/MAD background.

    Any one guide is carried by a small minority of cells, so its distribution
    across all cells is dominated by ambient and the median/MAD estimate the
    background rather than the signal.
    """
    frac = counts / np.maximum(totals, 1)[:, None]
    med = np.median(frac, axis=0)
    mad = np.median(np.abs(frac - med), axis=0)
    sigma = 1.4826 * mad
    degenerate = sigma <= 0
    if degenerate.any():                      # fall back to SD, then mark unusable
        sd = frac.std(axis=0)
        sigma = np.where(degenerate, sd, sigma)
    unusable = sigma <= 0
    safe = np.where(unusable, 1.0, sigma)
    z = (frac - med) / safe
    z[:, unusable] = -np.inf
    return z, unusable


def poisson_sf_log(k, lam):
    """log P(X >= k) for X ~ Poisson(lam), elementwise, k >= 1."""
    from scipy.stats import poisson
    return poisson.logsf(k - 1, lam)



def assess_lane_usable_assignments(rows, lanes):
    """Assess downstream lane-paired support, NOT identity or biological truth.

    A pooled count can pass when every target cell is in L1 and all controls
    are in L2. Require >=10 target AND NTC cells in each of >=3 matching lanes.
    These development thresholds were fixed after an inspected smoke run.
    """
    lanes = tuple(lanes)
    if len(lanes) < MIN_PAIRED_LANES or len(set(lanes)) != len(lanes):
        raise ValueError("expected lane identities missing or duplicated")
    per_lane, totals = collections.Counter(), collections.Counter()
    for row in rows:
        lane, target = row["lane"], row["target_gene"]
        if lane not in lanes or not target:
            raise ValueError("unknown lane or missing target identity")
        per_lane[(lane, target)] += 1
        totals[target] += 1
    ntc_by_lane = {lane: per_lane[(lane, "NTC")] for lane in lanes}
    ntc_supported_lanes = [
        lane for lane in lanes
        if ntc_by_lane[lane] >= MIN_CELLS_PER_PAIRED_LANE
    ]
    target_support = {}
    for target in sorted(g for g in totals if g != "NTC"):
        paired = [
            lane for lane in lanes
            if per_lane[(lane, target)] >= MIN_CELLS_PER_PAIRED_LANE
            and ntc_by_lane[lane] >= MIN_CELLS_PER_PAIRED_LANE
        ]
        target_support[target] = {
            "assigned_cells": totals[target],
            "cells_by_lane": {lane: per_lane[(lane, target)] for lane in lanes},
            "paired_lanes": paired,
            "lane_support_sufficient": (
                totals[target] >= MIN_CELLS_PER_USABLE_TARGET
                and len(paired) >= MIN_PAIRED_LANES
            ),
        }
    usable = [g for g, d in target_support.items()
              if d["lane_support_sufficient"]]
    ntc_ok = (totals["NTC"] >= MIN_CELLS_PER_USABLE_TARGET
              and len(ntc_supported_lanes) >= MIN_PAIRED_LANES)
    reasons = []
    if len(usable) < MIN_USABLE_TARGETS:
        reasons.append(
            "only %d targets have >=%d cells and >=%d lanes with >=%d "
            "target and >=%d same-lane NTC cells (need %d targets)"
            % (len(usable), MIN_CELLS_PER_USABLE_TARGET, MIN_PAIRED_LANES,
               MIN_CELLS_PER_PAIRED_LANE, MIN_CELLS_PER_PAIRED_LANE,
               MIN_USABLE_TARGETS)
        )
    if not ntc_ok:
        reasons.append(
            "NTC has %d cells across %d sufficiently populated lanes; "
            "need >=%d total and >=%d lanes with >=%d cells"
            % (totals["NTC"], len(ntc_supported_lanes),
               MIN_CELLS_PER_USABLE_TARGET, MIN_PAIRED_LANES,
               MIN_CELLS_PER_PAIRED_LANE)
        )
    return {
        "support_pass": not reasons,
        "usable_targets": usable,
        "ntc_cells": totals["NTC"],
        "ntc_by_lane": ntc_by_lane,
        "ntc_supported_lanes": ntc_supported_lanes,
        "target_support": target_support,
        "failure_reasons": reasons,
    }


def stage_call(a):
    z = np.load(a.counts_npz, allow_pickle=True)
    counts = z["counts"].astype(np.float64)
    cell_ids = list(z["cell_ids"])
    cell_lane = list(z["cell_lane"])
    guides = list(z["guides"])
    guide_target = list(z["guide_target"])
    n_cells, n_guides = counts.shape
    totals = counts.sum(axis=1)
    print("matrix: %d cells x %d guides, %d UMIs"
          % (n_cells, n_guides, int(counts.sum())))
    print("  median guide UMIs per cell: %.0f" % np.median(totals[totals > 0]))

    judged = totals >= MIN_CELL_TOTAL_UMI
    print("  cells with >= %d guide UMIs: %d" % (MIN_CELL_TOTAL_UMI, judged.sum()))

    zsc, unusable = robust_z(counts, totals)
    if unusable.any():
        print("  guides with degenerate background (z unusable): %d"
              % int(unusable.sum()))

    # ambient expectation: guide share of all guide UMIs, scaled by cell depth
    p_ambient = counts.sum(axis=0) / max(counts.sum(), 1.0)
    lam = np.outer(totals, p_ambient)
    n_tests = int(judged.sum()) * n_guides
    log_alpha = np.log(POISSON_ALPHA / max(n_tests, 1))
    with np.errstate(divide="ignore", invalid="ignore"):
        logsf = poisson_sf_log(np.maximum(counts, 1), np.maximum(lam, 1e-12))
    pois_pass = (logsf < log_alpha) & (counts > 0)

    def assign(z_thr):
        zpass = (zsc >= z_thr) & (counts >= MIN_ASSIGNED_UMI)
        both = zpass & pois_pass
        both[~judged, :] = False
        n_pass = both.sum(axis=1)
        single = n_pass == 1
        idx = np.full(n_cells, -1, dtype=np.int64)
        if single.any():
            idx[single] = both[single].argmax(axis=1)
        return idx, n_pass, single

    sens = {}
    for zt in SENSITIVITY_Z:
        i, npass, single = assign(zt)
        sens["z>=%.1f" % zt] = {
            "assigned": int(single.sum()),
            "multiplet_gt1_guide": int((npass > 1).sum()),
            "no_guide_passed": int((npass == 0).sum()),
        }
    idx, n_pass, single = assign(Z_THRESHOLD)

    rows = []
    for c in np.nonzero(single)[0]:
        g = int(idx[c])
        rows.append({
            "cell_id": cell_ids[c],
            "lane": cell_lane[c],
            "cell_barcode": cell_ids[c].split("_", 1)[1],
            "sgrna_name": guides[g],
            "target_gene": guide_target[g],
            "is_non_targeting": guide_target[g] == "NTC",
            "guide_umi": int(counts[c, g]),
            "cell_total_guide_umi": int(totals[c]),
            "guide_fraction": round(float(counts[c, g] / max(totals[c], 1)), 4),
            "robust_z": round(float(zsc[c, g]), 2),
        })

    os.makedirs(a.out_dir, exist_ok=True)
    out_csv = os.path.join(a.out_dir, "gse178317_cell_guide_assignments_v2.csv")
    if rows:
        with open(out_csv, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            w.writeheader(); w.writerows(rows)

    by_gene = collections.Counter(r["target_gene"] for r in rows)
    vals = sorted(by_gene.values())

    # An overall n>=40 is insufficient: a target needs target and control
    # pseudobulks in >=3 of the EXACT same sequencing lanes.
    support = assess_lane_usable_assignments(
        rows, [spec["lane"] for spec in LANES]
    )
    usable = support["usable_targets"]
    verdict_pass = support["support_pass"]
    reasons = support["failure_reasons"]

    receipt = {
        "schema": "GSE178317_GUIDE_ASSIGNMENT_V2",
        "development_status": "THRESHOLDS_FIXED_AFTER_BOUNDED_SMOKE_RUN",
        "prospective_confirmation_eligible": False,
        "verdict_scope": "DEVELOPMENT_USABILITY_ONLY",
        "verdict": "PASS_LANE_SUPPORT_ONLY" if verdict_pass else "FAIL_LANE_SUPPORT",
        "qualification_scope": "DEVELOPMENT_POST_SMOKE_NOT_GUIDE_IDENTITY_VALIDATION",
        "guide_identity_independently_verified": False,
        "biological_replication_verified": False,
        "verdict_basis": {
            "min_cells_per_usable_target": MIN_CELLS_PER_USABLE_TARGET,
            "min_usable_targets": MIN_USABLE_TARGETS,
            "usable_targets": len(usable),
            "ntc_cells_sufficient": bool(support["ntc_cells"] >= MIN_CELLS_PER_USABLE_TARGET
                                          and len(support["ntc_supported_lanes"]) >= MIN_PAIRED_LANES),
            "min_paired_lanes": MIN_PAIRED_LANES,
            "min_target_and_ntc_cells_per_lane": MIN_CELLS_PER_PAIRED_LANE,
            "ntc_cells_by_lane": support["ntc_by_lane"],
            "ntc_supported_lanes": support["ntc_supported_lanes"],
            "target_lane_support": support["target_support"],
            "failure_reasons": reasons,
            "note": ("development thresholds reflect downstream lane-paired "
                     "pseudobulk needs but were frozen AFTER an inspected smoke "
                     "run; this is not prospective confirmation or guide "
                     "identity validation"),
        },
        "counts_npz_sha256": sha256_file(a.counts_npz),
        "method": ("agreement of a per-guide robust z-score on cell fraction "
                   "with a Poisson test against an ambient expectation; a cell "
                   "is assigned only if exactly one guide passes both"),
        "declared_before_calling": {
            "z_threshold": Z_THRESHOLD,
            "poisson_alpha_family_wise": POISSON_ALPHA,
            "poisson_tests": n_tests,
            "min_assigned_umi": MIN_ASSIGNED_UMI,
            "min_cell_total_umi": MIN_CELL_TOTAL_UMI,
            "rationale": ("z of 5 is motivated by the number of tests rather "
                          "than a published assignment count; however a bounded "
                          "smoke run had already been inspected, so this is "
                          "development-calibrated, not prospective"),
        },
        "cells_total": n_cells,
        "cells_judged": int(judged.sum()),
        "cells_assigned": len(rows),
        "assignment_rate_of_called_cells": round(len(rows) / n_cells, 4),
        "cells_multiplet": int((n_pass > 1).sum()),
        "cells_no_guide_passed": int((n_pass == 0).sum()),
        "targets_represented": len([g for g in by_gene if g != "NTC"]),
        "ntc_cells": by_gene.get("NTC", 0),
        "cells_per_target_min": vals[0] if vals else 0,
        "cells_per_target_median": vals[len(vals) // 2] if vals else 0,
        "cells_per_target_max": vals[-1] if vals else 0,
        "cells_per_target": dict(sorted(by_gene.items())),
        "sensitivity": sens,
        "assignments_csv_sha256": sha256_file(out_csv) if rows else None,
        "jepa_prediction_used": False,
        "simulated_erasure_used": False,
        "therapeutic_ranking": False,
    }
    with open(os.path.join(a.out_dir, "gse178317_guide_assignment_receipt_v2.json"),
              "w") as fh:
        json.dump(receipt, fh, indent=2)

    print("\n=== VERDICT: %s ===" % receipt["verdict"])
    for r in reasons:
        print("  FAIL: %s" % r)
    print("  usable targets (>= %d cells and matched lanes): %d of %d required"
          % (MIN_CELLS_PER_USABLE_TARGET, len(usable), MIN_USABLE_TARGETS))

    print("\n=== assignment at the declared operating point (z >= %.1f) ===" % Z_THRESHOLD)
    for k in ("cells_total", "cells_judged", "cells_assigned", "cells_multiplet",
              "cells_no_guide_passed", "targets_represented", "ntc_cells",
              "cells_per_target_min", "cells_per_target_median",
              "cells_per_target_max"):
        print("  %-28s %s" % (k, receipt[k]))
    print("\n=== sensitivity (declared grid) ===")
    for k, v in sens.items():
        print("  %-10s assigned=%-7d multiplet=%-7d none=%d"
              % (k, v["assigned"], v["multiplet_gt1_guide"], v["no_guide_passed"]))
    print("\nwrote %s" % out_csv)
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", required=True, choices=["count", "call"])
    ap.add_argument("--library")
    ap.add_argument("--gex-dir")
    ap.add_argument("--counts-npz")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--vdb-dump", default="vdb-dump")
    ap.add_argument("--tmp-dir")
    ap.add_argument("--max-spots", type=int, default=None)
    a = ap.parse_args()
    if a.stage == "count":
        for req in ("library", "gex_dir", "tmp_dir"):
            if not getattr(a, req):
                raise SystemExit("--stage count requires --%s" % req.replace("_", "-"))
        os.makedirs(a.tmp_dir, exist_ok=True)
        return stage_count(a)
    if not a.counts_npz:
        raise SystemExit("--stage call requires --counts-npz")
    return stage_call(a)


if __name__ == "__main__":
    sys.exit(main())
