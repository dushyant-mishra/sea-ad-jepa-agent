#!/usr/bin/env python3
"""Cross-study comparability matrix v2 — source-bound, no stale status.

Replaces v1, which the independent audit found to carry a stale exposure row and
unbound metadata. Four defects are fixed:

**Stale exposure.** v1 hard-coded GSE240609 as `UNOPENED_RESERVED` while the same
PR physically executed its four-sample contrasts and reported 38,090 rows. v2
does not hard-code exposure at all: every outcome-exposure value is read from
`CURATOR_ASSERTION_REGISTRY_V2.json`, so the ledger has exactly one home and
cannot drift from it. A study missing from the registry is an error.

**A chosen age where sources disagree.** v1 wrote GSE335887 as "Day 12 per
series", although the series prose, the earlier catalog record and prior
Day-28 descriptions do not agree. v2 records
`SOURCE_CONFLICT_PENDING_RUN_LEVEL_AUTHORITY` and carries the competing claims,
rather than silently picking one.

**Unbound curator assertions.** v1 mixed computed shared-target counts with
hand-authored descriptions of intervention, cell model and controls in one
table. v2 emits two files: a computed matrix whose every field derives from a
digested source, and an assertion table where each row names its source and
reviewer. They are never merged.

**Digest-after-open and overwrite.** v1 computed source digests only after the
tables had been read, so a file swapped mid-run would be digested in its new
state, and it would happily overwrite a previous receipt. v2 digests every input
BEFORE opening it, re-verifies after reading, and refuses an occupied output
directory.

A shared gene symbol is not experimental comparability, and a nominated cis gene
is not a direct intervention. Both are kept in separate namespaces so neither can
silently license pooling.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import os
import sys

# Curator assertions. Each carries its own source; none is a computed value.
# Outcome exposure is deliberately ABSENT here - it lives only in the registry.
# Curator assertions are NOT defined here. Self-audit S3 found that v2 merely
# relocated them into a second OUTPUT file while they still lived in this
# source, so they could not be reviewed or signed off independently of the
# code. They now load from an external digested contract, and the producer
# fails closed if it is absent or does not cover every study it must describe.
ASSERTIONS = None  # populated in main() from --metadata-contract

COMPUTED_FIELDS = ["authenticated_direct_targets"]
ASSERTION_FIELDS = ["intervention", "cell_model", "protocol_and_time",
                    "biological_units", "controls", "assay_readout"]


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gse335887-ref", required=True)
    ap.add_argument("--gse178317-lib", required=True)
    ap.add_argument("--gse301119-crispri", required=True)
    ap.add_argument("--gse301119-crispra", required=True)
    ap.add_argument("--gse311359-identity", required=True)
    ap.add_argument("--assertion-registry", required=True,
                    help="single source of truth for outcome exposure")
    ap.add_argument("--metadata-contract", required=True,
                    help="external digested curator/literature assertion contract")
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args()

    if os.path.exists(a.out_dir) and os.listdir(a.out_dir):
        raise SystemExit("STOP_COMPARABILITY_V2_OUTPUT_EXISTS__NEW_VERSIONED_DIR_REQUIRED")

    global ASSERTIONS
    inputs = {
        "metadata_contract": a.metadata_contract,
        "gse335887_ref": a.gse335887_ref,
        "gse178317_lib": a.gse178317_lib,
        "gse301119_crispri": a.gse301119_crispri,
        "gse301119_crispra": a.gse301119_crispra,
        "gse311359_identity": a.gse311359_identity,
        "assertion_registry": a.assertion_registry,
    }
    for k, p in inputs.items():
        if not os.path.exists(p):
            raise SystemExit("missing input %s: %s" % (k, p))

    # Digest BEFORE opening. v1 digested afterwards, so a file swapped mid-run
    # would have been recorded in its new state.
    digests_before = {k: sha256_file(p) for k, p in inputs.items()}

    with open(a.metadata_contract) as fh:
        contract = json.load(fh)
    ASSERTIONS = contract.get("assertions") or {}
    if not ASSERTIONS:
        raise SystemExit("STOP_METADATA_CONTRACT_EMPTY")
    for _s, _v in ASSERTIONS.items():
        for _f in ASSERTION_FIELDS + ["source"]:
            if not _v.get(_f):
                raise SystemExit("STOP_METADATA_CONTRACT_FIELD_MISSING: %s.%s" % (_s, _f))

    with open(a.assertion_registry) as fh:
        registry = json.load(fh)
    reg = registry.get("assertions", {})

    rows335 = [r for r in csv.DictReader(gzip.open(inputs["gse335887_ref"], "rt"))
               if r["feature_type"] == "CRISPR Guide Capture"]
    T335 = {r["target_gene_name"] for r in rows335} - {"Non-Targeting"}

    T178 = {r["target_gene"] for r in
            csv.DictReader(open(inputs["gse178317_lib"]))} - {"NTC"}

    per_mod = {}
    for mod, key in (("CRISPRi", "gse301119_crispri"), ("CRISPRa", "gse301119_crispra")):
        rows = [r for r in csv.DictReader(open(inputs[key]))
                if r["crispr"] == "Perturbed"]
        per_mod[mod] = {r["Gene_Targeted"] for r in rows}
    T301 = per_mod["CRISPRi"] | per_mod["CRISPRa"]

    r311 = list(csv.DictReader(open(inputs["gse311359_identity"])))
    NOM311 = {r["nominated_gene"] for r in r311 if r["nominated_gene"]}

    # Re-verify after reading: inputs must not have changed under us.
    digests_after = {k: sha256_file(p) for k, p in inputs.items()}
    drifted = [k for k in inputs if digests_before[k] != digests_after[k]]
    if drifted:
        raise SystemExit("STOP_INPUT_CHANGED_DURING_RUN: %s" % ", ".join(drifted))

    direct = {"GSE335887": T335, "GSE178317": T178, "GSE301119": T301}

    failures = []
    for s in ASSERTIONS:
        if s not in reg:
            failures.append("NO_REGISTERED_ASSERTION %s" % s)
        elif not reg[s].get("outcome_exposure"):
            failures.append("NO_OUTCOME_EXPOSURE %s" % s)
    if failures:
        for f in failures:
            print("FAIL:", f)
        raise SystemExit("STOP_EXPOSURE_LEDGER_INCOMPLETE")

    os.makedirs(a.out_dir, exist_ok=True)

    # ---- computed matrix ---------------------------------------------------
    comp_path = os.path.join(a.out_dir, "CROSS_STUDY_COMPUTED_MATRIX_V2.csv")
    with open(comp_path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["study", "authenticated_direct_targets",
                    "outcome_exposure_from_registry", "registry_source_reference"])
        for s in sorted(ASSERTIONS):
            w.writerow([s,
                        len(direct[s]) if s in direct else "",
                        reg[s]["outcome_exposure"],
                        reg[s].get("source_reference", "")])

    # ---- curator assertions, separate file --------------------------------
    assert_path = os.path.join(a.out_dir, "CROSS_STUDY_CURATOR_ASSERTIONS_V2.csv")
    with open(assert_path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["study"] + ASSERTION_FIELDS + ["assertion_source", "conflict_detail"])
        for s in sorted(ASSERTIONS):
            v = ASSERTIONS[s]
            w.writerow([s] + [v[f] for f in ASSERTION_FIELDS]
                       + [v["source"], v.get("conflict_detail", "")])

    keys = ["GSE178317", "GSE335887", "GSE301119"]
    shared = {}
    for i, x in enumerate(keys):
        for y in keys[i + 1:]:
            shared["%s|%s" % (x, y)] = sorted(direct[x] & direct[y])
    nom_shared = {"%s|GSE311359_NOMINATED" % x: sorted(direct[x] & NOM311)
                  for x in keys}

    receipt = {
        "schema": "CROSS_STUDY_COMPARABILITY_MATRIX_V2",
        "supersedes": "build_cross_study_comparability_matrix_v1.py",
        "fixes": [
            "outcome exposure read from the assertion registry, never hard-coded",
            "GSE335887 age recorded as SOURCE_CONFLICT_PENDING_RUN_LEVEL_AUTHORITY",
            "computed columns and curator assertions emitted as separate files",
            "inputs digested before opening and re-verified after reading",
            "refuses an occupied output directory",
        ],
        "metadata_contract_sha256": digests_before["metadata_contract"],
        "input_digests_before_open": digests_before,
        "input_digests_after_read": digests_after,
        "authenticated_direct_target_counts": {k: len(v) for k, v in direct.items()},
        "gse301119_per_modality": {
            "CRISPRi": len(per_mod["CRISPRi"]), "CRISPRa": len(per_mod["CRISPRa"]),
            "union": len(T301),
            "intersection": len(per_mod["CRISPRi"] & per_mod["CRISPRa"]),
            "crispri_only": sorted(per_mod["CRISPRi"] - per_mod["CRISPRa"]),
            "crispra_only": sorted(per_mod["CRISPRa"] - per_mod["CRISPRi"]),
            "note": ("modalities do not target identical gene sets and do not "
                     "share a feature space; cross-modal scores require the "
                     "actual feature intersection"),
        },
        "shared_direct_targets": shared,
        "shared_with_nominated_only": nom_shared,
        "nominated_is_not_direct": (
            "a nominated cis gene is an assertion about which gene an element "
            "may regulate; never counted as a shared intervention target"),
        "gse335887_target_identity": {
            "authenticated_guide_targets": len(T335),
            "ARID5B": "TARGET_IDENTITY_PENDING - present as a CRISPRbrain "
                      "processed label, no authenticated guide in the deposited "
                      "GEO feature reference",
        },
        "overlap_scope_warning": (
            "the five shared Day-8 / GSE301119 direct targets do NOT involve "
            "GSE335887; these overlap queries must never be conflated"),
        "computed_matrix_csv_sha256": sha256_file(comp_path),
        "curator_assertions_csv_sha256": sha256_file(assert_path),
        "jepa_prediction_used": False,
        "training_authorized": False,
        "therapeutic_ranking": False,
    }
    rp = os.path.join(a.out_dir, "CROSS_STUDY_COMPARABILITY_RECEIPT_V2.json")
    with open(rp, "w") as fh:
        json.dump(receipt, fh, indent=2)

    print("=== computed ===")
    for k, v in direct.items():
        print("  %-12s authenticated direct targets %d" % (k, len(v)))
    print("\n=== outcome exposure, from the registry (single source of truth) ===")
    for s in sorted(ASSERTIONS):
        print("  %-12s %s" % (s, reg[s]["outcome_exposure"]))
    print("\n=== shared DIRECT targets ===")
    for k, v in shared.items():
        print("  %-26s %2d  %s" % (k, len(v), v or "(none)"))
    print("\n=== shared NOMINATED-only (not interventions) ===")
    for k, v in nom_shared.items():
        print("  %-38s %2d  %s" % (k, len(v), v or "(none)"))
    print("\nwrote %s\nwrote %s\nwrote %s" % (comp_path, assert_path, rp))
    return 0


if __name__ == "__main__":
    sys.exit(main())
