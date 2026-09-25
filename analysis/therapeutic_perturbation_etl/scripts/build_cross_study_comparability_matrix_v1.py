#!/usr/bin/env python3
"""Study-by-study comparability matrix, built from authenticated identity sources.

Shared target identities are recomputed from each study's own authenticated
guide/target source, never inherited from a catalogue or a prior document:

  GSE335887   deposited feature reference (feature_type == CRISPR Guide Capture)
  GSE178317   Supplementary Table 5 sgRNA library
  GSE301119   guide x donor pseudobulk metadata, per modality
  GSE311359   perturbation identity table, nominated genes only
  GSE293118   target engagement table

A **nominated** cis gene is never counted as an equivalent direct intervention.
GSE311359's MAF label and GSE293118's unmatched noncoding elements are nominated
or unassigned, not authenticated direct gene perturbations, and they are reported
in their own column so a reader cannot mistake one for the other.

The matrix reports what each study is, not what it proves. A shared gene symbol
is not experimental comparability: cell model, protocol, differentiation age,
control design and readout all differ, and those columns exist so that a shared
symbol cannot silently license pooling.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import os
import sys


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def load_targets(paths):
    """Authenticated DIRECT gene-intervention targets, per study."""
    t = {}
    rows = [r for r in csv.DictReader(gzip.open(paths["gse335887_ref"], "rt"))
            if r["feature_type"] == "CRISPR Guide Capture"]
    t["GSE335887"] = {r["target_gene_name"] for r in rows} - {"Non-Targeting"}

    t["GSE178317"] = {r["target_gene"] for r in
                      csv.DictReader(open(paths["gse178317_lib"]))} - {"NTC"}

    per_mod = {}
    for mod in ("CRISPRi", "CRISPRa"):
        rows = [r for r in csv.DictReader(open(paths["gse301119_%s" % mod.lower()]))
                if r["crispr"] == "Perturbed"]
        per_mod[mod] = {r["Gene_Targeted"] for r in rows}
    t["GSE301119"] = per_mod["CRISPRi"] | per_mod["CRISPRa"]
    t["_gse301119_per_modality"] = per_mod
    return t


def load_nominated(paths):
    """Nominated cis genes - NOT direct interventions."""
    rows = list(csv.DictReader(open(paths["gse311359_identity"])))
    return {"GSE311359": {r["nominated_gene"] for r in rows if r["nominated_gene"]}}


STUDIES = [
    # study, intervention, cell model, protocol/time, biological units, controls,
    # assay/readout, outcome exposure, limitation
    ("GSE178317", "CRISPRi (dCas9-KRAB), CROP-seq pMK1334", "iTF-MG, WTC11-class iPSC microglia",
     "six-TF doxycycline induction, Day 8", "1 pooled prep across 4 capture wells",
     "non-targeting guides, same wells", "scRNA + sgRNA enrichment library",
     "INSPECTED_DEVELOPMENT", "capture wells are not biological replicates; no biological error bar"),
    ("GSE335887", "CRISPRi, CROP-seq pMK1334", "iTF-MG and iMG, WTC11",
     "six-TF induction vs cytokine-directed; Day 12 per series",
     "one parental line WTC11; independent preparation census unverified",
     "5 non-targeting guides", "scRNA + CITE-seq 180-antibody panel + sgRNA",
     "UNOPENED_RESERVED", "protocol and differentiation age change together; not separately identifiable"),
    ("GSE301119", "CRISPRi and CRISPRa, separate strata", "primary human macrophages",
     "primary cells, donor-derived", "2 independent donors",
     "donor-matched non-targeting guides", "scRNA, guide x donor pseudobulk",
     "INSPECTED_DEVELOPMENT", "n=2 donors; CRISPRa HEXA guide variance not estimable; modalities do not share a feature space"),
    ("GSE311359", "CRISPRi, cis-regulatory elements and TSS", "iPSC-derived microglia",
     "7 samples", "7 samples; guide-level independence pending ID-keyed rebuild",
     "17 non-targeting guides", "scRNA + guide capture in one matrix",
     "INSPECTED_DEVELOPMENT", "BIN1 invalid pending ID-keyed V2; nominated genes are not direct interventions"),
    ("GSE293118", "CRISPRi, genes and noncoding elements", "HMC3 immortalized line",
     "single timepoint", "immortalized line; no donor axis",
     "non-targeting guides", "scRNA + guide capture",
     "INSPECTED_DEVELOPMENT", "6 direct targets only; 77 elements lack authenticated cis-target assignment; single-guide SYVN1"),
    ("GSE254205", "drug (GNE-317) + fibrillar amyloid-beta", "APOE4/4 iPSC microglia",
     "one model, one timepoint", "9 bulk samples, 3 per condition",
     "untreated (NT) arm", "bulk RNA-seq (STAR ReadsPerGene)",
     "INSPECTED_DEVELOPMENT_BULK_ONLY", "not a genetic intervention; drug response is not disease rescue; 3 assays unopened"),
    ("GSE240609", "genotype contrast (APOE3 vs APOE3ch x WT vs PSEN1)",
     "CD11b-purified microglia after neuron coculture", "post-coculture recovery",
     "1 sample per 2x2 design cell", "none; genotype contrast only", "bulk RNA-seq",
     "UNOPENED_RESERVED", "one sample per design cell forbids biological SE; not cell-autonomous"),
    ("GSE241858", "genotype (TREM2 R47H) x cytokine context", "iPSC microglia",
     "untreated / LPS / IFN-gamma", "2 independent clones per genotype",
     "untreated arm within clone", "bulk RNA-seq",
     "INSPECTED_DEVELOPMENT", "not a CRISPR study; clone is the unit; CTRL_A:LPS unbalanced"),
    ("GSE175721", "CRISPRi (intended)", "microglia-containing cortical organoids",
     "2 samples", "NOT ESTABLISHED - no per-cell guide assignment",
     "unknown", "scRNA only; no guide enrichment library",
     "UNOPENED_RESERVED", "STOP: depositor-described cell-to-guide table never deposited"),
]

HEADER = ["study", "intervention", "cell_model", "protocol_and_time",
          "biological_units", "controls", "assay_readout",
          "response_outcome_exposure", "limitation"]


def main():
    raise SystemExit(
        "STOP_COMPARABILITY_MATRIX_V1_SUPERSEDED: this producer hard-codes "
        "outcome exposure and recorded GSE240609 as UNOPENED_RESERVED while the "
        "same PR physically executed its four-sample contrasts and reported "
        "38,090 rows. It also wrote a chosen GSE335887 differentiation age where "
        "sources disagree, merged computed counts with unbound curator "
        "assertions in one table, digested its inputs only after reading them, "
        "and would overwrite a previous receipt. Use "
        "build_cross_study_comparability_matrix_v2.py, which reads exposure from "
        "CURATOR_ASSERTION_REGISTRY_V2.json. Retained for provenance only."
    )
    ap = argparse.ArgumentParser()
    ap.add_argument("--gse335887-ref", required=True)
    ap.add_argument("--gse178317-lib", required=True)
    ap.add_argument("--gse301119-crispri", required=True)
    ap.add_argument("--gse301119-crispra", required=True)
    ap.add_argument("--gse311359-identity", required=True)
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args()
    os.makedirs(a.out_dir, exist_ok=True)

    paths = {
        "gse335887_ref": a.gse335887_ref,
        "gse178317_lib": a.gse178317_lib,
        "gse301119_crispri": a.gse301119_crispri,
        "gse301119_crispra": a.gse301119_crispra,
        "gse311359_identity": a.gse311359_identity,
    }
    direct = load_targets(paths)
    nominated = load_nominated(paths)
    per_mod = direct.pop("_gse301119_per_modality")

    keys = ["GSE178317", "GSE335887", "GSE301119"]
    shared = {}
    for i, x in enumerate(keys):
        for y in keys[i + 1:]:
            shared["%s|%s" % (x, y)] = sorted(direct[x] & direct[y])
    # nominated-only relationships, kept in their own namespace
    nom_shared = {}
    for x in keys:
        nom_shared["%s|GSE311359_NOMINATED" % x] = sorted(
            direct[x] & nominated["GSE311359"])

    csv_path = os.path.join(a.out_dir, "CROSS_STUDY_COMPARABILITY_MATRIX_V1.csv")
    with open(csv_path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(HEADER + ["authenticated_direct_targets"])
        for row in STUDIES:
            n = len(direct.get(row[0], [])) if row[0] in direct else ""
            w.writerow(list(row) + [n])

    receipt = {
        "schema": "CROSS_STUDY_COMPARABILITY_MATRIX_V1",
        "shared_identities_recomputed_from_source": True,
        "authenticated_direct_target_counts": {k: len(v) for k, v in direct.items()},
        "gse301119_per_modality": {
            "CRISPRi": len(per_mod["CRISPRi"]),
            "CRISPRa": len(per_mod["CRISPRa"]),
            "union": len(per_mod["CRISPRi"] | per_mod["CRISPRa"]),
            "intersection": len(per_mod["CRISPRi"] & per_mod["CRISPRa"]),
            "crispri_only": sorted(per_mod["CRISPRi"] - per_mod["CRISPRa"]),
            "crispra_only": sorted(per_mod["CRISPRa"] - per_mod["CRISPRi"]),
            "note": ("the two modalities do NOT target identical gene sets, so a "
                     "paired CRISPRi/CRISPRa comparison is possible only on the "
                     "intersection"),
        },
        "shared_direct_targets": shared,
        "shared_with_nominated_only": nom_shared,
        "nominated_is_not_direct": (
            "a nominated cis gene is an assertion about which gene an element "
            "may regulate; it is not an authenticated direct gene intervention "
            "and must never be counted as a shared target"),
        "pooling_warning": (
            "a shared gene symbol is not experimental comparability: cell model, "
            "protocol, differentiation age, control design and readout all "
            "differ across these studies"),
        "source_digests": {k: sha256_file(v) for k, v in paths.items()},
        "matrix_csv_sha256": None,
        "jepa_prediction_used": False,
        "training_authorized": False,
        "therapeutic_ranking": False,
    }
    receipt["matrix_csv_sha256"] = sha256_file(csv_path)
    rp = os.path.join(a.out_dir, "CROSS_STUDY_COMPARABILITY_RECEIPT_V1.json")
    with open(rp, "w") as fh:
        json.dump(receipt, fh, indent=2)

    print("=== authenticated direct-intervention target counts ===")
    for k, v in direct.items():
        print("  %-12s %d" % (k, len(v)))
    print("\n=== shared DIRECT targets (recomputed from source) ===")
    for k, v in shared.items():
        print("  %-26s %2d  %s" % (k, len(v), v if v else "(none)"))
    print("\n=== shared with NOMINATED-only labels (not interventions) ===")
    for k, v in nom_shared.items():
        print("  %-38s %2d  %s" % (k, len(v), v if v else "(none)"))
    pm = receipt["gse301119_per_modality"]
    print("\n=== GSE301119 modality target sets ===")
    print("  CRISPRi %d | CRISPRa %d | union %d | intersection %d"
          % (pm["CRISPRi"], pm["CRISPRa"], pm["union"], pm["intersection"]))
    print("  CRISPRi-only %s | CRISPRa-only %s"
          % (pm["crispri_only"], pm["crispra_only"]))
    print("\nwrote %s\nwrote %s" % (csv_path, rp))
    return 0


if __name__ == "__main__":
    sys.exit(main())
