#!/usr/bin/env python3
"""GSE293118 (HMC3 noncoding CRISPRi) ETL and measured intervention effects.

Assay-specific by design. This is NOT the GSE301119 schema: GSE293118 is a
10x MEX triplet plus a separate per-cell protospacer-call file under a *different*
GSM accession, and its guide library mixes gene targets with noncoding regulatory
elements.

Joins that are verified rather than assumed
-------------------------------------------
* the protospacer calls (GSM8876720) and the expression matrix (GSM8876719) carry
  different accessions, so the barcode join is checked for containment and
  orphans before use;
* the feature file mixes ``Gene Expression`` and ``CRISPR Guide Capture`` rows;
  only the 36,601 gene rows enter expression pseudobulk.

Perturbation identity
---------------------
84 targets across four classes. Only ``gene`` targets have a same-named measured
feature, so **target engagement is defined only for those**. Noncoding variants
and deletions would need a nominated cis-target, which this script refuses to
invent; they are carried with engagement recorded as unavailable.

Multiplicity
------------
Cells receive 1..6+ guides. Single-perturbation effects use singly-assigned cells
only; the multiplet fraction is reported rather than silently collapsed.

No JEPA prediction, no simulated erasure, no therapeutic ranking.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

N_GENE_FEATURES = 36_601
N_GUIDE_FEATURES = 269
N_FEATURES_TOTAL = 36_870
N_BARCODES = 96_639


def target_of(guide: str) -> str:
    m = re.match(r"^(.*?)(?:_(\d+))$", guide)
    return m.group(1) if m else guide


def classify(target: str, measured_symbols: set[str]) -> str:
    if target.startswith("non-targeting"):
        return "non_targeting_control"
    if re.fullmatch(r"del\d+", target):
        return "noncoding_deletion"
    if re.match(r"^rs\d+", target):
        return "noncoding_variant"
    return "gene" if target in measured_symbols else "gene_symbol_unmatched"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--extracted-dir", type=Path, required=True)
    ap.add_argument("--feature-reference", type=Path, required=True)
    ap.add_argument("--out-dir", type=Path, required=True)
    args = ap.parse_args()
    E, out = args.extracted_dir, args.out_dir
    out.mkdir(parents=True, exist_ok=True)

    # ---- features -----------------------------------------------------------
    feats = [l.split("\t") for l in
             gzip.open(E / "GSM8876719_features.tsv.gz", "rt").read().splitlines()]
    if len(feats) != N_FEATURES_TOTAL:
        raise SystemExit(f"feature count {len(feats)} != {N_FEATURES_TOTAL}")
    kinds = [f[2] for f in feats]
    gene_rows = np.array([i for i, k in enumerate(kinds) if k == "Gene Expression"], dtype=np.int64)
    guide_rows = [i for i, k in enumerate(kinds) if k == "CRISPR Guide Capture"]
    if gene_rows.size != N_GENE_FEATURES or len(guide_rows) != N_GUIDE_FEATURES:
        raise SystemExit("feature-type census drifted")
    gene_symbols = [feats[i][1] for i in gene_rows]
    measured = set(gene_symbols)
    # position in the compacted gene-only matrix, -1 for guide rows
    gene_pos = np.full(N_FEATURES_TOTAL, -1, dtype=np.int64)
    gene_pos[gene_rows] = np.arange(gene_rows.size, dtype=np.int64)

    # ---- barcodes -----------------------------------------------------------
    barcodes = gzip.open(E / "GSM8876719_barcodes.tsv.gz", "rt").read().split()
    if len(barcodes) != N_BARCODES or len(set(barcodes)) != N_BARCODES:
        raise SystemExit("barcode census drifted or contains duplicates")
    bc_index = {b: i for i, b in enumerate(barcodes)}

    # ---- guide library and perturbation identity ----------------------------
    ref = list(csv.DictReader(gzip.open(args.feature_reference, "rt")))
    identity = []
    for r in ref:
        g = r["id"]
        t = target_of(g)
        identity.append({"guide_id": g, "target_id": t,
                         "target_class": classify(t, measured),
                         "target_gene_measured": t in measured})
    ident_by_guide = {r["guide_id"]: r for r in identity}

    # ---- protospacer calls: verified join ----------------------------------
    calls = list(csv.DictReader(gzip.open(E / "GSM8876720_protospacer_calls_per_cell.csv.gz", "rt")))
    call_bc = {r["cell_barcode"] for r in calls}
    orphans = call_bc - set(barcodes)
    if orphans:
        raise SystemExit(f"{len(orphans)} protospacer barcodes absent from the matrix")
    multiplicity = Counter(int(r["num_features"]) for r in calls)
    single = [r for r in calls if int(r["num_features"]) == 1]
    unknown = {r["feature_call"] for r in single} - set(ident_by_guide)
    if unknown:
        raise SystemExit(f"protospacer calls reference unknown guides: {sorted(unknown)[:5]}")

    # cell -> guide, singly assigned only
    cell_guide = {bc_index[r["cell_barcode"]]: r["feature_call"] for r in single}
    guides = sorted({g for g in cell_guide.values()})
    gidx = {g: i for i, g in enumerate(guides)}
    col_group = np.full(N_BARCODES, -1, dtype=np.int64)
    for c, g in cell_guide.items():
        col_group[c] = gidx[g]

    print(f"cells total {N_BARCODES:,} | protospacer-called {len(calls):,} | "
          f"singly assigned {len(single):,} | guides observed {len(guides)}", flush=True)

    # ---- stream the MEX matrix; accumulate guide x gene pseudobulk ----------
    PB = np.zeros((len(guides), N_GENE_FEATURES), dtype=np.float64)
    cell_counts = np.zeros(N_BARCODES, dtype=np.int64)
    n = 0
    with gzip.open(E / "GSM8876719_matrix.mtx.gz", "rt") as fh:
        line = fh.readline()
        if not line.startswith("%%MatrixMarket"):
            raise SystemExit("not a MatrixMarket file")
        line = fh.readline()
        while line.startswith("%"):
            line = fh.readline()
        nr, nc, nnz = (int(x) for x in line.split())
        if nr != N_FEATURES_TOTAL or nc != N_BARCODES:
            raise SystemExit(f"matrix dims {nr}x{nc} unexpected")
        for line in fh:
            a, b, v = line.split()
            r = int(a) - 1
            c = int(b) - 1
            val = int(v)
            if val < 0:
                raise SystemExit("negative count in the matrix")
            cell_counts[c] += val
            gp = gene_pos[r]
            if gp >= 0:
                g = col_group[c]
                if g >= 0:
                    PB[g, gp] += val
            n += 1
            if n % 50_000_000 == 0:
                print(f"  {n:,}/{nnz:,} entries", flush=True)
    if n != nnz:
        raise SystemExit(f"read {n} entries, header declared {nnz}")
    print(f"matrix entries read: {n:,}", flush=True)

    # ---- guide-level table --------------------------------------------------
    n_cells_per_guide = Counter(cell_guide.values())
    gmeta = []
    for g in guides:
        idr = ident_by_guide[g]
        gmeta.append({"study": "GSE293118", "assay_object": "HMC3_noncoding_CRISPRi",
                      "guide_id": g, "target_id": idr["target_id"],
                      "target_class": idr["target_class"],
                      "n_cells": n_cells_per_guide[g],
                      "total_counts": int(PB[gidx[g]].sum())})
    with (out / "GSE293118_guide_meta.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(gmeta[0]))
        w.writeheader(); w.writerows(gmeta)

    # CPM then log2(cpm+1) on the guide pseudobulk
    tot = np.maximum(PB.sum(axis=1, keepdims=True), 1.0)
    lg = np.log2(PB / tot * 1e6 + 1.0)

    nt = [gidx[g] for g in guides if ident_by_guide[g]["target_class"] == "non_targeting_control"]
    if not nt:
        raise SystemExit("no non-targeting control guides observed")
    nt_mean = lg[nt].mean(axis=0)
    print(f"non-targeting control guides used as reference: {len(nt)}", flush=True)

    sym_pos = {s: i for i, s in enumerate(gene_symbols)}
    by_target = defaultdict(list)
    for g in guides:
        if ident_by_guide[g]["target_class"] != "non_targeting_control":
            by_target[ident_by_guide[g]["target_id"]].append(gidx[g])

    eff = []
    for t, idxs in sorted(by_target.items()):
        cls = ident_by_guide[guides[idxs[0]]]["target_class"]
        p = sym_pos.get(t)
        per_guide = None if p is None else (lg[idxs, p] - nt_mean[p])
        eff.append({
            "study": "GSE293118", "assay_object": "HMC3_noncoding_CRISPRi",
            "target_id": t, "target_class": cls,
            "engagement_measurable": p is not None,
            "engagement_unavailable_reason": "" if p is not None else
                ("noncoding target has no same-named measured feature; a nominated "
                 "cis-target is required and is not invented here"),
            "n_guides": len(idxs),
            "n_cells": int(sum(n_cells_per_guide[guides[i]] for i in idxs)),
            "n_nt_guides": len(nt),
            "n_nt_cells": int(sum(n_cells_per_guide[guides[i]] for i in nt)),
            "target_log2fc_mean": "" if p is None else float(per_guide.mean()),
            "target_log2fc_sd": "" if p is None or len(idxs) < 2 else float(per_guide.std(ddof=1)),
            "target_log2fc_se": "" if p is None or len(idxs) < 2
                                else float(per_guide.std(ddof=1) / np.sqrt(len(idxs))),
        })
    with (out / "GSE293118_target_engagement.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(eff[0]))
        w.writeheader(); w.writerows(eff)

    np.savez_compressed(out / "GSE293118_guide_logcpm.npz",
                        guides=np.array(guides, dtype=object),
                        gene_symbols=np.array(gene_symbols, dtype=object),
                        logcpm=lg.astype(np.float32))

    summary = {
        "schema": "GSE293118_NONCODING_CRISPRI_INTERVENTION_EFFECTS_V1",
        "study": "GSE293118", "system": "HMC3 microglial cell line",
        "modality": "noncoding CRISPRi",
        "cells_total": N_BARCODES,
        "cells_protospacer_called": len(calls),
        "cells_singly_assigned": len(single),
        "multiplet_fraction_of_called": round(1 - len(single) / len(calls), 4),
        "guide_multiplicity_histogram": {str(k): v for k, v in sorted(multiplicity.items())},
        "protospacer_barcodes_subset_of_matrix": True,
        "orphan_protospacer_barcodes": 0,
        "gene_features": int(gene_rows.size),
        "guide_features": len(guide_rows),
        "guides_in_library": len(ref),
        "guides_observed_in_singly_assigned_cells": len(guides),
        "targets_by_class": dict(Counter(r["target_class"] for r in identity.__iter__())),
        "non_targeting_control_guides_observed": len(nt),
        "targets_with_measurable_engagement": sum(1 for e in eff if e["engagement_measurable"]),
        "targets_without_measurable_engagement": sum(1 for e in eff if not e["engagement_measurable"]),
        "matrix_entries_read": n,
        "jepa_prediction_used": False,
        "simulated_erasure_used": False,
        "therapeutic_ranking": False,
    }
    (out / "GSE293118_etl_summary.json").write_text(json.dumps(summary, indent=2) + "\n",
                                                    encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items()
                      if k not in ("guide_multiplicity_histogram", "targets_by_class")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
