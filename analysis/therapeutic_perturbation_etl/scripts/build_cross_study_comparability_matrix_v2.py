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
from collections import Counter
import os
import sys


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


PINNED_METADATA_SHA256 = {
    "gse335887_ref": "fd2c3fa5b517c81bbd158516dacb00416f1883a654c795e126916620f77f225f",
    "gse178317_lib": "8de1e7e737c8c42ec9a7feff0d6e198b4f09808f09b6238e8b9dfbe276774942",
    "gse301119_crispri": "ce96daa64413a238173b485a91037df02824e85bc071e715292aa800dee7abe8",
    "gse301119_crispra": "e13c3bb2741824139d5adb91b22ad725956078ede98f59cf74a5c1abe96e3397",
    "gse311359_identity": "1eeb4e40f14ec2ebe7472d7bb80769ae35bdb8df8ccbf4308493c8441eb363b5",
}
GSE293118_GIT_BLOB_SHA1 = "7cd6be560f211e0e053e98e8e834500232a185a8"
def authenticate_metadata(paths):
    # Complete validation before parsing any target lists; no self-declared root accepted.
    for role, expected in PINNED_METADATA_SHA256.items():
        if sha256_file(paths[role]) != expected:
            raise ValueError("STOP_AUTHENTICATED_METADATA_SHA_MISMATCH: "+role)
    raw = open(paths["gse293118_identity"],"rb").read()
    gitblob = hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\x00"+raw).hexdigest()
    if gitblob != GSE293118_GIT_BLOB_SHA1:
        raise ValueError("STOP_AUTHENTICATED_GSE293118_BLOB_MISMATCH")

def load_targets(paths):
    """Authenticated DIRECT gene-intervention targets, per study."""
    t = {}
    rows = [r for r in csv.DictReader(gzip.open(paths["gse335887_ref"], "rt"))
            if r["feature_type"] == "CRISPR Guide Capture"]
    ids=[r["id"] for r in rows]
    seqs=[r["sequence"] for r in rows]
    target_counts=Counter(r["target_gene_name"] for r in rows)
    if (len(rows)!=65 or len(set(ids))!=65 or len(set(seqs))!=65
        or target_counts.pop("Non-Targeting",0)!=5
        or len(target_counts)!=30 or set(target_counts.values())!={2}
        or any(not r["target_gene_id"] for r in rows if r["target_gene_name"]!="Non-Targeting")):
        raise ValueError("STOP_GSE335887_GUIDE_REFERENCE_INTEGRITY")
    t["GSE335887"] = set(target_counts)

    t["GSE178317"] = {r["target_gene"] for r in
                      csv.DictReader(open(paths["gse178317_lib"]))} - {"NTC"}

    per_mod = {}
    for mod in ("CRISPRi", "CRISPRa"):
        with open(paths["gse301119_%s" % mod.lower()],newline="",encoding="utf-8") as fh:
            full=list(csv.DictReader(fh))
        if not full or {r["donor"] for r in full}!={"D1","D2"}:
            raise ValueError("STOP_GSE301119_DONOR_CENSUS: "+mod)
        seen=set();guide_map={};control={"D1":0,"D2":0}
        for row in full:
            donor=row["donor"];gid=row["guide_identity"]
            if not gid or row["guide_donor"]!=gid+"||"+donor:
                raise ValueError("STOP_GSE301119_GUIDE_DONOR_JOIN: "+mod)
            key=row["guide_donor"]
            if key in seen:raise ValueError("STOP_GSE301119_DUPLICATE_GUIDE_DONOR: "+mod)
            seen.add(key)
            try:n=int(row["n_cells"])
            except ValueError:raise ValueError("STOP_GSE301119_INVALID_CELL_COUNT: "+mod)
            if n<=0:raise ValueError("STOP_GSE301119_NONPOSITIVE_CELL_COUNT: "+mod)
            role=row["crispr"];target=row["Gene_Targeted"]
            if role=="NT":control[donor]+=n
            elif role!="Perturbed" or not target:raise ValueError("STOP_GSE301119_INVALID_ROLE_TARGET: "+mod)
            if gid in guide_map and guide_map[gid]!=(target,role):
                raise ValueError("STOP_GSE301119_GUIDE_TARGET_DRIFT: "+mod)
            guide_map[gid]=(target,role)
        if not all(control.values()):raise ValueError("STOP_GSE301119_MISSING_DONOR_MATCHED_CONTROL: "+mod)
        rows=[r for r in full if r["crispr"]=="Perturbed"]
        targets={r["Gene_Targeted"] for r in rows}
        if len(targets)!=206 or any({r["donor"] for r in rows if r["Gene_Targeted"]==tg}!={"D1","D2"} for tg in targets):
            raise ValueError("STOP_GSE301119_TARGET_DONOR_COVERAGE: "+mod)
        per_mod[mod]=targets
    t["GSE301119"] = per_mod["CRISPRi"] | per_mod["CRISPRa"]
    hmc = list(csv.DictReader(open(paths["gse293118_identity"])))
    direct = {r["target_id"] for r in hmc if r["target_class"]=="gene"}
    if len(direct)!=6: raise ValueError("STOP_GSE293118_DIRECT_TARGET_CENSUS")
    t["GSE293118"] = direct
    if len(per_mod["CRISPRi"])!=206 or len(per_mod["CRISPRa"])!=206:
        raise ValueError("STOP_GSE301119_MODALITY_CENSUS")
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
     "six-TF Day12 vs cytokine-directed Day28, both WTC11",
     "one parental line WTC11; 30 authentic guided targets, ARID5B unauthenticated",
     "5 non-targeting guides", "scRNA + CITE-seq 180-antibody panel + sgRNA",
     "UNOPENED_RESERVED", "protocol and differentiation age change together; not separately identifiable"),
    ("GSE301119", "CRISPRi and CRISPRa, separate strata", "primary human macrophages",
     "primary cells, donor-derived", "2 independent donors",
     "donor-matched non-targeting guides", "scRNA, guide x donor pseudobulk",
     "INSPECTED_DEVELOPMENT", "n=2 donors; CRISPRa HEXA guide variance not estimable; modalities do not share a feature space"),
    ("GSE311359", "CRISPRi, cis-regulatory elements and TSS", "iPSC-derived microglia",
     "7 samples", "7 samples; guide-level independence pending ID-keyed rebuild",
     "17 non-targeting guides", "scRNA + guide capture in one matrix",
     "INSPECTED_DEVELOPMENT", "BIN1 source feature IDs resolved; V1 effect invalid pending ID-keyed V2; nominated genes are not direct interventions"),
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
     "EFFECTS_EXECUTED_LEDGER_REVIEW_REQUIRED", "one sample per design cell forbids biological SE; not cell-autonomous"),
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
    ap = argparse.ArgumentParser()
    ap.add_argument("--gse335887-ref", required=True)
    ap.add_argument("--gse178317-lib", required=True)
    ap.add_argument("--gse301119-crispri", required=True)
    ap.add_argument("--gse301119-crispra", required=True)
    ap.add_argument("--gse311359-identity", required=True)
    ap.add_argument("--gse293118-identity", required=True)
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args()
    if os.path.isdir(a.out_dir) and os.listdir(a.out_dir):
        raise SystemExit("STOP_COMPARABILITY_V2_OUTPUT_ALREADY_EXISTS")

    paths = {
        "gse335887_ref": a.gse335887_ref,
        "gse178317_lib": a.gse178317_lib,
        "gse301119_crispri": a.gse301119_crispri,
        "gse301119_crispra": a.gse301119_crispra,
        "gse311359_identity": a.gse311359_identity,
        "gse293118_identity": a.gse293118_identity,
    }
    authenticate_metadata(paths)
    os.makedirs(a.out_dir,exist_ok=True)
    direct = load_targets(paths)
    nominated = load_nominated(paths)
    per_mod = direct.pop("_gse301119_per_modality")

    keys = ["GSE178317", "GSE335887", "GSE301119", "GSE293118"]
    shared = {}
    for i, x in enumerate(keys):
        for y in keys[i + 1:]:
            shared["%s|%s" % (x, y)] = sorted(direct[x] & direct[y])
    # nominated-only relationships, kept in their own namespace
    nom_shared = {}
    for x in keys:
        nom_shared["%s|GSE311359_NOMINATED" % x] = sorted(
            direct[x] & nominated["GSE311359"])

    csv_path = os.path.join(a.out_dir, "CROSS_STUDY_COMPARABILITY_MATRIX_V2.csv")
    with open(csv_path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(HEADER + ["authenticated_direct_targets"])
        for row in STUDIES:
            n = len(direct.get(row[0], [])) if row[0] in direct else ""
            w.writerow(list(row) + [n])

    receipt = {
        "schema": "CROSS_STUDY_COMPARABILITY_MATRIX_V2",
        "physical_metadata_sources_preflight_sha_authenticated": True,
        "descriptive_study_columns": "HUMAN_AUTHORED_ASSERTIONS_NOT_HASH_AUTHENTICATED",
        "code_test_authority": False,
        "independent_biological_replication": False,
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
        "target_join": "EXACT_LITERAL_TARGET_LABELS_ONLY_NO_ALIAS_OR_INTERVENTION_EQUIVALENCE",
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
    rp = os.path.join(a.out_dir, "CROSS_STUDY_COMPARABILITY_RECEIPT_V2.json")
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
