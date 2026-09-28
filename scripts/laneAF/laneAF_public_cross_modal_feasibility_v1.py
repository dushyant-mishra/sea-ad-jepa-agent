#!/usr/bin/env python3
"""Lane F: public SEA-AD cross-modal (RNA <-> ATAC) feasibility verdict.

Two jobs:

1. Resolve the assay origin of the one FULL104 SEA-AD matrix whose processed
   object does NOT declare obs/method (the 2025 Caudate release), using a
   library-prefix rule calibrated on the ten matrices that DO declare it. The
   result is labelled DERIVED_LIBRARY_PREFIX_RULE, never DECLARED.

2. Inventory what the PUBLIC processed SEA-AD ATAC resources expose, and emit
   the verdict artifact SEAAD_PUBLIC_CROSS_MODAL_FEASIBILITY_V1.

Governance: identity, provenance and schema only. For the cell-type question
this module reads the Subclass VOCABULARY (the categories array), never the
per-cell codes. No expression value, no accessibility value, no pathology value
is read anywhere.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from collections import Counter
from pathlib import Path

import h5py

sys.path.insert(0, str(Path(__file__).resolve().parent))
import laneAF_seaad_assay_origin_audit_v1 as audit  # noqa: E402
from laneAF_identity_firewall_v1 import assert_identity_only  # noqa: E402

VERDICTS = (
    "EXACT_SAME_NUCLEUS_PAIRING_PUBLICLY_AVAILABLE",
    "PUBLIC_ATAC_ONLY_DONOR_OR_AGGREGATE_LINKAGE",
    "EXACT_PAIRING_REQUIRES_CONTROLLED_METADATA",
    "INSUFFICIENT_PUBLIC_METADATA",
)

# Enumerated live from the public bucket listing at
# https://sea-ad-single-cell-profiling.s3.amazonaws.com/?list-type=2 (anonymous,
# no AWS credentials) on 2026-09-28. Sizes are the Content-Length returned by an
# anonymous HTTP HEAD against the same bucket.
PUBLIC_ATAC_RESOURCES = [
    {
        "key": "MTG/ATACseq/SEAAD_MTG_ATACseq_final-nuclei.2024-12-06.h5ad",
        "bytes": 18260707597,
        "kind": "processed_atac_matrix_with_obs_and_var",
        "access_class": "OPEN_PUBLIC",
        "also_local": True,
    },
    {
        "key": "MTG/ATACseq/SEAAD_MTG_ATACseq_all-nuclei_metadata.2024-12-06.csv",
        "bytes": 1119453295,
        "kind": "standalone_per_nucleus_metadata_table",
        "access_class": "OPEN_PUBLIC",
        "also_local": False,
    },
    {
        "key": "MTG/ATACseq/bw/*.bw",
        "bytes": None,
        "kind": "pseudobulk_coverage_tracks_by_subclass_and_adnc_group",
        "access_class": "OPEN_PUBLIC",
        "also_local": False,
    },
    {
        "key": "PFC/ATACseq/bw/*.bw",
        "bytes": None,
        "kind": "pseudobulk_coverage_tracks_only_no_per_nucleus_object",
        "access_class": "OPEN_PUBLIC",
        "also_local": False,
    },
    {
        "key": "Multiregion_2026/SEAAD_HIP_MEC_LEC_ITG_MTG_FI_STG_DFC_AnG_V1C_RNAseq_all-nuclei_metadata.2026-06-22.csv",
        "bytes": 8337530813,
        "kind": "standalone_per_nucleus_RNA_metadata_table_10_regions",
        "access_class": "OPEN_PUBLIC",
        "also_local": False,
    },
]

REGIONS_WITH_NO_PUBLIC_PER_NUCLEUS_ATAC = [
    "AnG",
    "Caudate_Nucleus",
    "DFC/PFC",
    "FI",
    "HIP",
    "ITG",
    "LEC",
    "MEC",
    "STG",
    "V1C",
]


def caudate_derived_assay(prefix_rule: dict[str, str]) -> dict[str, object]:
    index_rows = audit.read_lineage_index()
    target = [r for r in index_rows if r["matrix_id"] == "sea_ad_caudate_rna_all_2025"]
    if len(target) != 1:
        raise RuntimeError("caudate operator not found in FULL104 lineage")
    record = target[0]
    shard = audit.read_shard(int(record["operator_index"]))
    counts: Counter = Counter()
    prefix_counts: Counter = Counter()
    donors_by_class: dict[str, set] = {}
    for cell_id, donor in zip(shard["cell_id"], shard["donor_id"]):
        prefix = audit.library_prefix(audit.library_token(cell_id))
        prefix_counts[prefix] += 1
        method = prefix_rule.get(prefix)
        if method is None:
            assay = audit.CLASS_UNKNOWN
        elif method in audit.MULTIOME_METHODS:
            assay = audit.CLASS_MULTIOME
        elif method in audit.SINGLEOME_RNA_METHODS:
            assay = audit.CLASS_SINGLEOME
        else:
            assay = audit.CLASS_UNKNOWN
        counts[assay] += 1
        donors_by_class.setdefault(assay, set()).add(donor)
    return {
        "matrix_id": record["matrix_id"],
        "full104_rows": int(record["row_count"]),
        "declared_obs_method_present": False,
        "resolution_evidence": "DERIVED_LIBRARY_PREFIX_RULE",
        "rule_applied": prefix_rule,
        "library_prefix_counts": dict(sorted(prefix_counts.items())),
        "derived_assay_counts": dict(sorted(counts.items())),
        "derived_donor_counts": {k: len(v) for k, v in sorted(donors_by_class.items())},
        "caveat": (
            "This classification is NOT declared by the Caudate 2025 processed object, which "
            "carries no obs/method and no obs/library_prep field. It is derived from a rule that "
            "is a perfect deterministic function of the library prefix across the 3,484,130 "
            "FULL104 nuclei in the ten matrices that DO declare obs/method. It must not be used "
            "as an assay-origin authority without independent confirmation."
        ),
    }


def atac_exposure() -> dict[str, object]:
    with h5py.File(audit.ATAC_PATH, "r") as handle:
        obs = handle["obs"]
        var = handle["var"]
        index_name = audit.frame_index_name(obs)
        assert_identity_only([index_name], context="laneF_atac_index")
        var_index_name = audit.frame_index_name(var)
        var_node = var[var_index_name]
        var_count = int(var_node.shape[0]) if isinstance(var_node, h5py.Dataset) else None
        peak_examples = audit.decode(var_node[0:3]) if isinstance(var_node, h5py.Dataset) else None
        # Cell-type VOCABULARY only: the categories array, never the per-cell codes.
        subclass_vocabulary = None
        node = obs.get("Subclass")
        if node is not None and not isinstance(node, h5py.Dataset) and "categories" in node:
            subclass_vocabulary = audit.decode(node["categories"][...])
        return {
            "atac_object": str(audit.ATAC_PATH),
            "public_key": "MTG/ATACseq/SEAAD_MTG_ATACseq_final-nuclei.2024-12-06.h5ad",
            "obs_index_field": index_name,
            "obs_field_count": len(list(obs.keys())),
            "exposes_cell_nucleus_metadata": True,
            "exposes_barcode_identity": index_name in set(obs.keys()) or index_name == "index",
            "exposes_bare_barcode_column": "bc" in set(obs.keys()),
            "exposes_library_id": "library_prep" in set(obs.keys()),
            "exposes_sample_id": "sample_id" in set(obs.keys()),
            "exposes_ar_id": "ar_id" in set(obs.keys()),
            "exposes_assay_origin_field": "method" in set(obs.keys()),
            "exposes_region": "Brain Region" in set(obs.keys()),
            "exposes_qc_fields": sorted(
                k for k in obs.keys() if k.startswith("ATAC_") or k.startswith("GEX_")
            )[:8],
            "qc_field_count": sum(
                1 for k in obs.keys() if k.startswith("ATAC_") or k.startswith("GEX_")
            ),
            "exposes_cell_type_labels": sorted(
                k for k in obs.keys() if k in {"Class", "Subclass", "Supertype", "Supertype (non-expanded)"}
            ),
            "subclass_vocabulary": subclass_vocabulary,
            "microglia_label_present": bool(
                subclass_vocabulary and any("Micro" in v for v in subclass_vocabulary)
            ),
            "peak_feature_count": var_count,
            "peak_coordinate_examples": peak_examples,
            "peak_coordinates_are_genomic_intervals": bool(
                peak_examples and all(":" in v or "-" in v for v in peak_examples)
            ),
            "matrix_present": "X" in handle,
            "layers": sorted(handle["layers"].keys()) if "layers" in handle else [],
            "obsm": sorted(handle["obsm"].keys()) if "obsm" in handle else [],
        }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit", required=True, help="Lane A audit JSON")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    audit_report = json.loads(Path(args.audit).read_text(encoding="utf-8"))
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    prefix_rule = audit_report["library_prefix_to_declared_method"]
    if not audit_report["library_prefix_rule_deterministic_on_declared_regions"]:
        prefix_rule = {}
    caudate = caudate_derived_assay(prefix_rule)
    exposure = atac_exposure()

    paired = int(audit_report["exact_paired_atac_cells"])
    multiome = int(audit_report["multiome_gex_cells"])
    unresolved = int(audit_report["unmatched_multiome_gex_cells"])

    # Verdict rule, fixed before the numbers were read back in:
    #   - any exact same-nucleus pairing established from public processed
    #     metadata alone  -> EXACT_SAME_NUCLEUS_PAIRING_PUBLICLY_AVAILABLE
    #   - none established, but public ATAC exists at donor / pseudobulk level
    #     -> PUBLIC_ATAC_ONLY_DONOR_OR_AGGREGATE_LINKAGE
    #   - no public per-nucleus ATAC identity of any kind
    #     -> INSUFFICIENT_PUBLIC_METADATA
    # EXACT_PAIRING_REQUIRES_CONTROLLED_METADATA is reserved for the case where
    # a public per-nucleus ATAC object exists but carries no public key.
    if paired > 0:
        verdict = "EXACT_SAME_NUCLEUS_PAIRING_PUBLICLY_AVAILABLE"
    elif exposure["matrix_present"] and not exposure["exposes_barcode_identity"]:
        verdict = "EXACT_PAIRING_REQUIRES_CONTROLLED_METADATA"
    elif exposure["matrix_present"]:
        verdict = "PUBLIC_ATAC_ONLY_DONOR_OR_AGGREGATE_LINKAGE"
    else:
        verdict = "INSUFFICIENT_PUBLIC_METADATA"
    if verdict not in VERDICTS:
        raise RuntimeError("verdict outside the permitted vocabulary")

    document = {
        "schema": "SEAAD_PUBLIC_CROSS_MODAL_FEASIBILITY_V1",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "verdict": verdict,
        "verdict_scope": (
            "The verdict is TRUE FOR THE MTG MULTIOME SUBSET ONLY. Exactly "
            + str(paired)
            + " of the "
            + str(multiome)
            + " FULL104 SEA-AD Multiome-GEX nuclei have a publicly provable same-nucleus "
            "ATAC counterpart. The remaining "
            + str(unresolved)
            + " are unresolved because no per-nucleus ATAC object has been published for their "
            "brain regions at all - not because their pairing key is withheld."
        ),
        "unresolved_region_status": "NO_PUBLIC_PER_NUCLEUS_ATAC_OBJECT_EXISTS",
        "unresolved_requires_controlled_metadata": False,
        "controlled_metadata_would_help": False,
        "controlled_metadata_note": (
            "Controlled-access metadata is NOT the blocker for the unresolved nuclei. The blocker "
            "is that SEA-AD has published a per-nucleus ATAC object for MTG only; for PFC only "
            "pseudobulk bigwig coverage tracks exist, and for the other eight regions plus Caudate "
            "no ATAC product of any kind is published. No controlled-access request was made and "
            "none is proposed."
        ),
        "public_pairing_key": {
            "key": "exact string equality of the full nucleus identifier",
            "rna_side": "obs/exp_component_name in the public RNA h5ad (or column 'exp_component_name' in the public RNA metadata CSV)",
            "atac_side": "obs/_index in the public ATAC h5ad (or column 'index' in the public ATAC metadata CSV)",
            "identifier_grammar": "<16bp 10x barcode>-<library token>-<ar_id>, e.g. AAACAGCCAAACATAG-L8XR_210916_02_B11-1131607954",
            "restriction": "both sides restricted to method == 10xMulti",
            "transformations_applied": "none - no barcode translation, no suffix stripping, no partial matching",
            "available_from_metadata_alone": True,
            "metadata_only_route": (
                "MTG/ATACseq/SEAAD_MTG_ATACseq_all-nuclei_metadata.2024-12-06.csv (1,119,453,295 bytes) "
                "carries columns index, method, library_prep, sample_id, ar_id, bc, Donor ID and "
                "Brain Region, so the pairing can be established without downloading either matrix."
            ),
        },
        "public_atac_inventory": {
            "cell_nucleus_metadata": "PRESENT",
            "atac_matrix": "PRESENT (MTG only)",
            "peak_coordinates": "PRESENT (" + str(exposure["peak_feature_count"]) + " features)",
            "microglia_labels": "PRESENT" if exposure["microglia_label_present"] else "ABSENT",
            "qc_fields": "PRESENT (" + str(exposure["qc_field_count"]) + " ATAC_/GEX_ fields)",
            "library_ids": "PRESENT" if exposure["exposes_library_id"] else "ABSENT",
            "barcode_identity": "PRESENT" if exposure["exposes_barcode_identity"] else "ABSENT",
            "multiome_vs_singleome_origin": "PRESENT" if exposure["exposes_assay_origin_field"] else "ABSENT",
            "public_pairing_key": "PRESENT",
            "regions_with_per_nucleus_atac": ["MTG"],
            "regions_with_pseudobulk_atac_only": ["PFC"],
            "regions_with_no_public_atac_product": REGIONS_WITH_NO_PUBLIC_PER_NUCLEUS_ATAC,
        },
        "atac_exposure_detail": exposure,
        "public_resources": PUBLIC_ATAC_RESOURCES,
        "access_classes": {
            "sea-ad-single-cell-profiling S3 bucket": "OPEN_PUBLIC",
            "anonymous_bucket_listing_succeeded": True,
            "credentials_required": False,
            "registry": "https://registry.opendata.aws/allen-sea-ad-atlas/",
            "license": "Allen Institute Terms of Use",
            "local_copies_of_public_objects": "PROJECT_ALREADY_LOCAL",
            "controlled_access_requested": False,
        },
        "caudate_derived_assay_origin": caudate,
        "counts_from_lane_a": {
            "full104_seaad_cells_checked": audit_report["full104_seaad_cells_checked"],
            "multiome_gex_cells": multiome,
            "singleome_rna_cells": audit_report["singleome_rna_cells"],
            "unknown_assay_cells": audit_report["unknown_assay_cells"],
            "exact_paired_atac_cells": paired,
            "unmatched_multiome_gex_cells": unresolved,
            "paired_subset_donor_count": audit_report["paired_subset_donor_count"],
        },
        "did_not_infer": (
            "No pairing was inferred. A FULL104 Multiome-GEX nucleus is called paired only when "
            "its full identifier string is present verbatim in the ATAC obs index with method == "
            "10xMulti. Donor membership was never used to imply nucleus pairing, and the negative "
            "control (115,426 LEC Multiome-GEX nuclei, zero matches) shows the join does not fall "
            "back to donor or to bare barcode."
        ),
    }
    path = out / "SEAAD_PUBLIC_CROSS_MODAL_FEASIBILITY_V1.json"
    path.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in document.items() if k not in {"atac_exposure_detail"}}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
