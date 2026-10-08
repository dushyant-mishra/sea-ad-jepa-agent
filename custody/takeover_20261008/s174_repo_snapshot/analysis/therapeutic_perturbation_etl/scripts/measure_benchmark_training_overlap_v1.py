#!/usr/bin/env python3
"""Measure the perturbation benchmark against the FULL104 training corpus.

The benchmark is only held out if it is disjoint from training, and it is only
answerable if the model was given the means to learn the genes it is asked
about.  Those two requirements pull in opposite directions, so the axes here are
deliberately not symmetric:

  study / accession      must be ZERO   direct contamination
  donor / cell line      must be ZERO   a shared line is a shared genome
  cell barcode           must be ZERO   non-zero means a run was ingested twice
  gene / feature space   must be HIGH   a model cannot predict the response of a
                                        gene absent from its feature space
  expression support     must be HIGH   the axis symbol membership hides: a gene
                                        can sit in the address space and still
                                        never have been seen to vary

The last axis is the one this producer exists for.  `donor_addr_nnz` in the
FULL104 pass1 artifact is a 104 x 41,238 matrix of per-donor counts of cells in
which each address is detected, so "was this gene observed, and how widely" is a
measurement rather than an assumption.

A guardrail, stated because it is easy to violate without noticing: exclusions
from the benchmark must rest on training-side criteria declared in advance — a
gene is not expressed, or has no variance — and never on whether the model
performs well on that gene.  Trimming a benchmark until the model looks good
destroys the evidence the benchmark exists to produce.  This producer therefore
reports coverage and never filters anything.

Axes this producer cannot compute are written as NOT_CHECKED, never as zero.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import sys

import numpy as np
import pandas as pd


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def summarize(symbols, sym2idx, coreset, donors_det, cells_tot, n_donors):
    """Coverage of one target set against the training corpus.  No filtering."""
    present = [(s, sym2idx[s]) for s in symbols if s in sym2idx]
    absent = sorted(set(symbols) - {s for s, _ in present})
    if not present:
        return {"targets": len(symbols), "in_address_space": 0,
                "absent_symbols": absent}
    idx = [i for _, i in present]
    dd = np.array([donors_det[i] for i in idx])
    ct = np.array([cells_tot[i] for i in idx])
    unobserved = sorted(s for (s, i) in present if cells_tot[i] == 0)
    return {
        "targets": len(symbols),
        "in_address_space": len(present),
        "absent_symbols": absent,
        "in_common_core": int(sum(1 for i in idx if i in coreset)),
        "detected_in_all_donors": int((dd == n_donors).sum()),
        "detected_in_at_least_100_donors": int((dd >= 100).sum()),
        "detected_in_zero_donors": int((dd == 0).sum()),
        "unobserved_symbols": unobserved,
        "median_donors_detected": float(np.median(dd)),
        "min_donors_detected": int(dd.min()),
        "median_cells_expressing": float(np.median(ct)),
        "min_cells_expressing": int(ct.min()),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pass1-npz", required=True,
                    help="FULL104 pass1 with core and donor_addr_nnz")
    ap.add_argument("--registry", required=True,
                    help="stage81a2r molecular address registry CSV")
    ap.add_argument("--gse178317-library", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--include-crisprbrain", action="store_true",
                    help="also measure CRISPRbrain targets (requires network)")
    a = ap.parse_args()
    os.makedirs(a.out_dir, exist_ok=True)

    z = np.load(a.pass1_npz, allow_pickle=True)
    for req in ("core", "donor_addr_nnz"):
        if req not in z.files:
            raise SystemExit("pass1 artifact lacks %r; refusing to guess" % req)
    core = z["core"]
    dan = z["donor_addr_nnz"]
    n_donors, n_addr = dan.shape
    coreset = set(core.tolist())
    donors_det = (dan > 0).sum(axis=0)
    cells_tot = dan.sum(axis=0)

    reg = pd.read_csv(a.registry,
                      usecols=["molecular_address_index", "symbol",
                               "contributing_source_families"])
    if len(reg) != n_addr:
        raise SystemExit("registry rows %d != pass1 addresses %d"
                         % (len(reg), n_addr))
    sym2idx = dict(zip(reg.symbol.astype(str), reg.molecular_address_index))
    families = sorted({s for v in reg.contributing_source_families.dropna().unique()
                       for s in str(v).split("|")})

    receipt = {
        "schema": "BENCHMARK_TRAINING_OVERLAP_V1",
        "training_corpus": {
            "pass1_npz": os.path.basename(a.pass1_npz),
            "pass1_sha256": sha256_file(a.pass1_npz),
            "registry_sha256": sha256_file(a.registry),
            "donors": int(n_donors),
            "addresses": int(n_addr),
            "common_core_addresses": int(len(core)),
            "source_families": families,
        },
        "axis_semantics": {
            "study_accession": "must be ZERO",
            "donor_cell_line": "must be ZERO",
            "cell_barcode": "must be ZERO",
            "gene_feature_space": "must be HIGH",
            "expression_support": "must be HIGH",
        },
        "study_accession_overlap": {
            "training_source_families": families,
            "benchmark_accessions": [
                "GSE301119", "GSE311359", "GSE293118", "GSE254205",
                "GSE241858", "GSE240609", "GSE178317", "GSE175721"],
            "intersection": [],
            "basis": ("training families are HVS, NPH52 and SEA-AD; no benchmark "
                      "accession appears among them"),
        },
        "donor_cell_line_overlap": "NOT_CHECKED",
        "cell_barcode_overlap": "NOT_CHECKED",
        "target_sets": {},
        "filtering_applied": "none; this producer reports coverage only",
        "jepa_prediction_used": False,
        "simulated_erasure_used": False,
        "therapeutic_ranking": False,
    }

    lib = {r["target_gene"].strip()
           for r in csv.DictReader(open(a.gse178317_library))}
    lib.discard("NTC")
    receipt["target_sets"]["GSE178317"] = summarize(
        sorted(lib), sym2idx, coreset, donors_det, cells_tot, n_donors)

    if a.include_crisprbrain:
        import crisprbrain
        client = crisprbrain.Client()
        groups = {}
        for n, s in client.screens.items():
            if s.metadata.get("Screen Type") not in ("RNA-Seq", "Single-cell"):
                continue
            t = set(s.to_data_frame()["name"].astype(str))
            groups.setdefault("CRISPRbrain_all", set()).update(t)
            key = ("CRISPRbrain_microglia" if "icroglia" in n
                   else "CRISPRbrain_neuron" if "Neuron" in n
                   else "CRISPRbrain_other")
            groups.setdefault(key, set()).update(t)
        for k, t in groups.items():
            receipt["target_sets"][k] = summarize(
                sorted(t), sym2idx, coreset, donors_det, cells_tot, n_donors)

    out = os.path.join(a.out_dir, "benchmark_training_overlap_receipt_v1.json")
    with open(out, "w") as fh:
        json.dump(receipt, fh, indent=2)

    print("=== FULL104 training corpus ===")
    tc = receipt["training_corpus"]
    print("  donors %d   addresses %s   common core %s   families %s"
          % (tc["donors"], f"{tc['addresses']:,}",
             f"{tc['common_core_addresses']:,}", ",".join(tc["source_families"])))
    for name, r in receipt["target_sets"].items():
        if "median_donors_detected" not in r:
            continue
        print("\n%s  (n=%d)" % (name, r["targets"]))
        print("  in address space   %d   in common core %d"
              % (r["in_address_space"], r["in_common_core"]))
        print("  detected in 0 donors %d   median donors %.0f/%d"
              % (r["detected_in_zero_donors"], r["median_donors_detected"], n_donors))
        print("  median cells expressing %s   min %s"
              % (f"{r['median_cells_expressing']:,.0f}",
                 f"{r['min_cells_expressing']:,}"))
        if r["absent_symbols"]:
            print("  absent from address space: %s" % ", ".join(r["absent_symbols"]))
    print("\nwrote %s" % out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
