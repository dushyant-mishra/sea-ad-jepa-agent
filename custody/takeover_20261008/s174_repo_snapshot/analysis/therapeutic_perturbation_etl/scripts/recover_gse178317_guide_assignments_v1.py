#!/usr/bin/env python3
"""Recover per-cell sgRNA assignments for GSE178317 from the raw SRA reads.

GSE178317 is the Kampmann CRISPRi/a iPSC-microglia CROP-seq experiment.  Its
GEO deposit carries gene-expression matrices and sgRNA-enrichment matrices, but
the sgRNA-enrichment libraries were processed against the plain transcriptome
reference, so the deposited matrices contain no guide features at all and the
guide-to-cell assignment is absent from the processed deposit.  That assignment
is nevertheless recoverable, because two things survive elsewhere:

  1. The sgRNA library.  Supplementary Table 5 of Draeger et al. 2022
     (Nat Neurosci, PMID 35953545) lists all 81 sgRNAs with 20 nt protospacers.

  2. The raw reads.  SRA stores 127 bases per spot for the enrichment runs:
     an 8 nt i7 index, the 28 nt cell barcode + UMI, and the 91 nt guide read.
     The barcode read is flagged TECHNICAL, which is why the ENA-derived FASTQ
     serves only 91 bases and appears to lack barcodes.  vdb-dump returns it.

This producer streams each lane from SRA, extracts (cell barcode, UMI, guide),
restricts to barcodes that Cell Ranger called as cells in the matching
gene-expression lane, deduplicates by UMI, and assigns a single guide per cell
under a dominance rule declared below before any result was inspected.

No value here is synthetic, historical or placeholder.  Every count is measured
from the archived reads.  Cells that do not satisfy the dominance rule are
reported as unassigned; they are never imputed.
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

# ---------------------------------------------------------------------------
# Declared constants.  Fixed before any assignment result was examined.
# ---------------------------------------------------------------------------

# Spot layout, verified with: vdb-dump <SRR> -R 1 -C READ_LEN,READ_TYPE
#   READ_LEN: 8, 28, 91   READ_TYPE: TECHNICAL, TECHNICAL, BIOLOGICAL
LEN_I7, LEN_CB_UMI, LEN_BIO = 8, 28, 91
SPOT_LEN = LEN_I7 + LEN_CB_UMI + LEN_BIO
LEN_CB, LEN_UMI = 16, 12                      # 10x Chromium 3-prime v3

# Vector context flanking the protospacer, read directly off the archived reads
# and consistent with the enrichment primers in Supplementary Table 10.
SCAFFOLD = "GTTTAAGAGCTAAGCTGG"               # Chen-optimized sgRNA scaffold, 3-prime
ANCHOR5P = "CCACCTTGTT"                       # vector sequence, 5-prime
PROTOSPACER_LEN = 20

# Guide-calling rule.  Identical to the rule already applied to GSE311359 in
# this collection, so the two Perturb-seq studies are called the same way.
# A cell is assigned iff its top guide has at least MIN_TOP_UMI deduplicated
# UMIs AND that guide holds at least MIN_DOMINANCE of the cell guide UMIs.
MIN_TOP_UMI = 5
MIN_DOMINANCE = 0.70

# Reported alongside the primary call purely to show sensitivity.  These do not
# select the operating point; MIN_TOP_UMI / MIN_DOMINANCE above do.
SENSITIVITY_GRID = [(3, 0.70), (5, 0.70), (5, 0.80), (10, 0.70), (10, 0.90)]

# Lane wiring.  Pairing of expression lane to enrichment lane was established
# empirically by barcode containment (diagonal 12-25x off-diagonal) and agrees
# with the deposited filename numbering.
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


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_library(path):
    """protospacer -> (target_gene, sgrna_name).  Fails closed on any anomaly."""
    lib = {}
    with open(path, newline="") as fh:
        for row in csv.DictReader(fh):
            ps = row["protospacer"].strip().upper()
            if len(ps) != PROTOSPACER_LEN:
                raise SystemExit("protospacer not %d nt: %r" % (PROTOSPACER_LEN, row))
            if set(ps) - set("ACGT"):
                raise SystemExit("non-ACGT protospacer: %r" % (row,))
            if ps in lib:
                raise SystemExit("duplicate protospacer %s: %r" % (ps, row))
            lib[ps] = (row["target_gene"].strip(), row["sgrna_name"].strip())
    if not lib:
        raise SystemExit("empty sgRNA library")
    return lib


def load_called_cells(h5_path):
    """16 nt barcodes Cell Ranger called as cells in the expression lane."""
    import h5py
    with h5py.File(h5_path, "r") as f:
        raw = [b.decode() for b in f["matrix"]["barcodes"][:]]
    cells = set(b.split("-")[0] for b in raw)
    if len(cells) != len(raw):
        raise SystemExit("barcode suffix collision in %s" % h5_path)
    return cells


def extract_lane(srr, lib, cells, vdb_dump, tmp_dir, max_spots):
    """Stream one lane; return (per-(cell,guide) UMI counts, read statistics).

    Deduplication is delegated to `sort -u` over (cell, umi, guide) triples so
    that memory stays bounded regardless of lane depth.
    """
    stat = collections.Counter()
    rng = ["-R", "1-%d" % max_spots] if max_spots else []
    dump = subprocess.Popen(
        [vdb_dump, srr] + rng + ["-C", "READ", "-f", "tab"],
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, bufsize=1 << 20)

    triples = os.path.join(tmp_dir, "%s.triples" % srr)
    env = dict(os.environ, LC_ALL="C")
    srt = subprocess.Popen(["sort", "-u", "-S", "2G", "-T", tmp_dir, "-o", triples],
                           stdin=subprocess.PIPE, text=True, bufsize=1 << 20, env=env)

    w = srt.stdin.write
    for line in dump.stdout:
        s = line.rstrip("\n")
        if len(s) != SPOT_LEN:
            stat["spot_len_mismatch"] += 1
            continue
        stat["spots"] += 1
        cb = s[LEN_I7:LEN_I7 + LEN_CB]
        if cb not in cells:                       # ambient / uncalled droplet
            stat["barcode_not_a_called_cell"] += 1
            continue
        stat["barcode_is_called_cell"] += 1
        bio = s[LEN_I7 + LEN_CB_UMI:]
        j = bio.find(SCAFFOLD)
        ps = bio[j - PROTOSPACER_LEN:j] if j >= PROTOSPACER_LEN else None
        how = "scaffold3p"
        if ps not in lib:
            i = bio.find(ANCHOR5P)
            cand = (bio[i + len(ANCHOR5P):i + len(ANCHOR5P) + PROTOSPACER_LEN]
                    if i >= 0 else None)
            if cand in lib:
                ps, how = cand, "anchor5p"
        if ps in lib:
            stat["guide_read"] += 1
            stat["by_" + how] += 1
            umi = s[LEN_I7 + LEN_CB:LEN_I7 + LEN_CB_UMI]
            w("%s\t%s\t%s\n" % (cb, umi, lib[ps][1]))
        else:
            stat["no_guide_match"] += 1

    dump.stdout.close()
    if dump.wait() != 0:
        raise SystemExit("vdb-dump failed for %s" % srr)
    srt.stdin.close()
    if srt.wait() != 0:
        raise SystemExit("sort failed for %s" % srr)

    counts = collections.Counter()
    with open(triples) as fh:
        for line in fh:
            cb, _umi, g = line.rstrip("\n").split("\t")
            counts[(cb, g)] += 1
            stat["umi_dedup"] += 1
    os.remove(triples)
    return counts, stat


def call_guides(counts, min_umi, min_dom):
    """Apply the dominance rule.  Returns cell -> (guide, top_umi, total, frac)."""
    per_cell = collections.defaultdict(dict)
    for (cb, g), n in counts.items():
        per_cell[cb][g] = n
    out = {}
    for cb, gs in per_cell.items():
        total = sum(gs.values())
        g, top = max(gs.items(), key=lambda kv: kv[1])
        frac = top / total
        if top >= min_umi and frac >= min_dom:
            out[cb] = (g, top, total, frac)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--library", required=True, help="Suppl. Table 5 CSV")
    ap.add_argument("--gex-dir", required=True, help="dir of deposited GEX .h5")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--vdb-dump", default="vdb-dump")
    ap.add_argument("--tmp-dir", required=True)
    ap.add_argument("--max-spots", type=int, default=None,
                    help="bound spots per lane (smoke test only; omit for full run)")
    a = ap.parse_args()

    os.makedirs(a.out_dir, exist_ok=True)
    os.makedirs(a.tmp_dir, exist_ok=True)

    lib = load_library(a.library)
    guide_to_gene = dict((name, gene) for gene, name in lib.values())
    n_targets = len(set(g for g, _ in lib.values()))
    print("sgRNA library: %d guides, %d targets (incl NTC)" % (len(lib), n_targets),
          flush=True)

    receipt = {
        "schema": "GSE178317_GUIDE_ASSIGNMENT_RECOVERY_V1",
        "study": "GSE178317",
        "system": "iPSC-derived microglia (iTF-Microglia), CROP-seq CRISPRi",
        "guide_identity_source": {
            "why_not_in_geo": ("deposited sgRNA-enrichment matrices were processed "
                               "against the plain transcriptome reference, so they "
                               "carry 33538 Gene Expression features and no guides"),
            "library_table": "Draeger et al. 2022 Nat Neurosci Supplementary Table 5",
            "library_sha256": sha256_file(a.library),
            "reads": "SRA (barcode read is flagged TECHNICAL; ENA FASTQ omits it)",
        },
        "declared_before_inspection": {
            "min_top_guide_umi": MIN_TOP_UMI,
            "min_dominance_fraction": MIN_DOMINANCE,
            "rule_shared_with": "GSE311359 in this collection",
        },
        "max_spots_per_lane": a.max_spots,
        "lanes": [],
        "jepa_prediction_used": False,
        "simulated_erasure_used": False,
        "therapeutic_ranking": False,
    }

    rows = []
    for spec in LANES:
        h5 = os.path.join(a.gex_dir, spec["gex_h5"])
        cells = load_called_cells(h5)
        t0 = time.time()
        print("\n=== %s %s -> %s (%d called cells) ===" %
              (spec["lane"], spec["srr"], spec["gex_gsm"], len(cells)), flush=True)
        counts, stat = extract_lane(spec["srr"], lib, cells, a.vdb_dump,
                                    a.tmp_dir, a.max_spots)
        called = call_guides(counts, MIN_TOP_UMI, MIN_DOMINANCE)

        sens = {}
        for mu, md in SENSITIVITY_GRID:
            sens["umi>=%d,dom>=%.2f" % (mu, md)] = len(call_guides(counts, mu, md))

        cells_with_any = len(set(cb for cb, _ in counts))
        lane_rec = {
            "lane": spec["lane"], "srr": spec["srr"], "gex_gsm": spec["gex_gsm"],
            "gex_h5_sha256": sha256_file(h5),
            "gex_called_cells": len(cells),
            "spots_read": stat["spots"],
            "reads_on_called_cells": stat["barcode_is_called_cell"],
            "reads_with_guide": stat["guide_read"],
            "reads_no_guide_match": stat["no_guide_match"],
            "guide_umis_after_dedup": stat["umi_dedup"],
            "cells_with_any_guide_umi": cells_with_any,
            "cells_assigned": len(called),
            "assignment_rate_of_called_cells": round(len(called) / len(cells), 4),
            "distinct_guides_observed": len(set(g for _, g in counts)),
            "sensitivity_cells_assigned": sens,
            "elapsed_s": round(time.time() - t0, 1),
        }
        receipt["lanes"].append(lane_rec)
        for k, v in lane_rec.items():
            if k not in ("sensitivity_cells_assigned", "gex_h5_sha256"):
                print("  %-36s %s" % (k, v))

        for cb in sorted(called):
            g, top, total, frac = called[cb]
            rows.append({
                "lane": spec["lane"], "gex_gsm": spec["gex_gsm"],
                "cell_barcode": cb,
                "cell_id": "%s_%s" % (spec["lane"], cb),
                "sgrna_name": g,
                "target_gene": guide_to_gene[g],
                "is_non_targeting": guide_to_gene[g] == "NTC",
                "top_guide_umi": top,
                "total_guide_umi": total,
                "dominance_fraction": round(frac, 4),
            })

    if not rows:
        raise SystemExit("no cells assigned; refusing to write an empty result")

    out_csv = os.path.join(a.out_dir, "gse178317_cell_guide_assignments_v1.csv")
    with open(out_csv, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    by_gene = collections.Counter(r["target_gene"] for r in rows)
    vals = sorted(by_gene.values())
    receipt["totals"] = {
        "cells_assigned": len(rows),
        "gex_called_cells": sum(l["gex_called_cells"] for l in receipt["lanes"]),
        "targets_represented": len([g for g in by_gene if g != "NTC"]),
        "ntc_cells": by_gene.get("NTC", 0),
        "cells_per_target_min": vals[0],
        "cells_per_target_median": vals[len(vals) // 2],
        "cells_per_target_max": vals[-1],
    }
    receipt["cells_per_target"] = dict(sorted(by_gene.items()))
    receipt["assignments_csv_sha256"] = sha256_file(out_csv)

    out_json = os.path.join(a.out_dir, "gse178317_guide_assignment_receipt_v1.json")
    with open(out_json, "w") as fh:
        json.dump(receipt, fh, indent=2)

    print("\n=== TOTALS ===")
    for k, v in receipt["totals"].items():
        print("  %-28s %s" % (k, v))
    print("\nwrote %s" % out_csv)
    print("wrote %s" % out_json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
