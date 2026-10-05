#!/usr/bin/env python3
"""Acquire and inventory the CRISPRbrain data commons, and measure its overlap
with the FULL104 molecular address space.

CRISPRbrain (crisprbrain.org, Kampmann lab UCSF with NIH CARD) hosts functional
genomics screens in differentiated human cell types.  It is reachable through a
published Python client (`pip install crisprbrain`), so acquisition is scripted
rather than scraped.

Two kinds of screen matter differently to this project:

  * **Transcriptomic screens** (Screen Type RNA-Seq or Single-cell) report, for
    each perturbed target gene, a differential expression profile across the
    transcriptome.  That is the same quantity the rest of this collection
    measures, and is directly usable as intervention-response benchmark data.

  * **Simple screens** report a single phenotype score per gene (survival,
    phagocytosis, antibody staining).  That is a different prediction target and
    is inventoried here but not treated as intervention-response data.

The overlap measurement exists because the benchmark is only held out if it is
disjoint from training.  Note the asymmetry between axes: study and donor
overlap must be ZERO, whereas gene-space overlap must be HIGH, because a model
cannot be asked to predict the response of a gene absent from its feature space.
Genes outside the space are out of scope, not failures.

This producer downloads and records.  It computes no intervention effect and
makes no claim about model performance.
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
import os
import sys

TRANSCRIPTOMIC_TYPES = ("RNA-Seq", "Single-cell")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_full104_symbols(registry_csv):
    """Symbols and Ensembl IDs of the FULL104 molecular address space."""
    import pandas as pd
    reg = pd.read_csv(registry_csv,
                      usecols=["molecular_address_id", "symbol",
                               "contributing_source_families"])
    fams = sorted({s for v in reg.contributing_source_families.dropna().unique()
                   for s in str(v).split("|")})
    return (set(reg.symbol.dropna().astype(str)),
            set(reg.molecular_address_id.dropna().astype(str)),
            len(reg), fams)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--full104-registry", default=None,
                    help="stage81a2r molecular address registry CSV; if omitted "
                         "the overlap section is recorded as NOT_CHECKED")
    a = ap.parse_args()
    os.makedirs(a.out_dir, exist_ok=True)

    import crisprbrain
    client = crisprbrain.Client()
    screens = client.screens
    print("CRISPRbrain screens: %d" % len(screens))

    catalog = {n: s.metadata for n, s in screens.items()}
    cat_path = os.path.join(a.out_dir, "crisprbrain_catalog_v1.json")
    with open(cat_path, "w") as fh:
        json.dump(catalog, fh, indent=2, sort_keys=True)

    receipt = {
        "schema": "CRISPRBRAIN_ACQUISITION_V1",
        "source": "https://crisprbrain.org",
        "client": "crisprbrain (PyPI)",
        "screens_total": len(screens),
        "catalog_sha256": sha256_file(cat_path),
        "by_screen_type": dict(collections.Counter(
            m.get("Screen Type") for m in catalog.values())),
        "by_cell_type": dict(collections.Counter(
            m.get("Cell Type") for m in catalog.values())),
        "by_lab": dict(collections.Counter(
            m.get("Lab (Institution)") for m in catalog.values())),
        "transcriptomic_screens": [],
        "simple_screens": sorted(
            n for n, m in catalog.items()
            if m.get("Screen Type") not in TRANSCRIPTOMIC_TYPES),
        "jepa_prediction_used": False,
        "simulated_erasure_used": False,
        "therapeutic_ranking": False,
    }

    tx_dir = os.path.join(a.out_dir, "transcriptomic")
    os.makedirs(tx_dir, exist_ok=True)

    all_targets, per_screen_targets = set(), {}
    for name in sorted(screens):
        meta = catalog[name]
        if meta.get("Screen Type") not in TRANSCRIPTOMIC_TYPES:
            continue
        df = screens[name].to_data_frame()
        safe = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in name)
        out = os.path.join(tx_dir, safe + ".csv")
        df.to_csv(out, index=False)

        targets = sorted(set(df["name"].astype(str))) if "name" in df else []
        per_screen_targets[name] = set(targets)
        all_targets |= set(targets)

        # target engagement: the perturbed gene measured on itself
        eng = None
        if {"Gene", "name", "Log2FC"} <= set(df.columns):
            self_rows = df[df["Gene"].astype(str) == df["name"].astype(str)]
            if len(self_rows):
                eng = {
                    "targets_with_self_row": int(len(self_rows)),
                    "knocked_down_log2fc_lt_0": int((self_rows["Log2FC"] < 0).sum()),
                    "median_self_log2fc": round(float(self_rows["Log2FC"].median()), 4),
                }
                if "FDR" in self_rows:
                    eng["self_row_fdr_lt_0.05"] = int((self_rows["FDR"] < 0.05).sum())

        rec = {
            "screen": name,
            "screen_type": meta.get("Screen Type"),
            "cell_type": meta.get("Cell Type"),
            "crispr_mode": meta.get("CRISPR Mode"),
            "screen_method": meta.get("Screen Method"),
            "reference": meta.get("Reference"),
            "rows": int(len(df)),
            "targets": len(targets),
            "measured_features": int(df["Gene"].nunique()) if "Gene" in df else None,
            "target_engagement": eng,
            "csv_sha256": sha256_file(out),
        }
        receipt["transcriptomic_screens"].append(rec)
        print("  %-44s rows=%-9d targets=%-4d" % (name, len(df), len(targets)))

    receipt["distinct_targets_across_transcriptomic_screens"] = len(all_targets)

    # ---- overlap with the FULL104 training feature space --------------------
    if a.full104_registry and os.path.exists(a.full104_registry):
        syms, ensg, n_addr, fams = load_full104_symbols(a.full104_registry)
        inside = all_targets & syms
        overlap = {
            "full104_registry_sha256": sha256_file(a.full104_registry),
            "full104_addresses": n_addr,
            "full104_source_families": fams,
            "note": ("gene-space intersection must be HIGH: a model cannot be "
                     "asked about a gene outside its feature space.  Study and "
                     "donor overlap, which must be ZERO, are separate axes and "
                     "are NOT checked by this producer."),
            "targets_in_full104_symbol_space": len(inside),
            "targets_total": len(all_targets),
            "targets_outside": sorted(all_targets - syms),
            "per_screen": {},
        }
        for n, t in per_screen_targets.items():
            overlap["per_screen"][n] = {
                "targets": len(t),
                "in_full104": len(t & syms),
            }
        receipt["full104_gene_space_overlap"] = overlap
        print("\nFULL104 gene-space overlap: %d / %d targets"
              % (len(inside), len(all_targets)))
        print("  outside: %s" % ", ".join(sorted(all_targets - syms)) or "(none)")
    else:
        receipt["full104_gene_space_overlap"] = "NOT_CHECKED"
        receipt["full104_donor_and_study_overlap"] = "NOT_CHECKED"
        print("\nFULL104 overlap: NOT_CHECKED (no registry supplied)")

    # These axes are not computable here and are recorded honestly as such.
    receipt.setdefault("full104_donor_and_study_overlap", "NOT_CHECKED")
    receipt["full104_cell_barcode_overlap"] = "NOT_CHECKED"

    rp = os.path.join(a.out_dir, "crisprbrain_acquisition_receipt_v1.json")
    with open(rp, "w") as fh:
        json.dump(receipt, fh, indent=2)
    print("\nwrote %s\nwrote %s" % (cat_path, rp))
    return 0


if __name__ == "__main__":
    sys.exit(main())
